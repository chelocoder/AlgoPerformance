"""Materializa y ejecuta el piloto ampliado 05F sin reintentar casos."""
import argparse
import ctypes as ct
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import random
import subprocess
import time
from uuid import UUID

from run_affinity import PROBE, RAW, RUNNER, append, sha, verify_forks
from run_anchors import BALANCED
from windows_affinity import affinity, core_types, supervise

ROOT = Path("docs/examples/pilot-extended-05f")
GRID = Path("docs/examples/pilot-extended-01.json")
SPECS = {
    "array-sum": (1000, 10000000, 2100, 120, 10, "AverageTime", 200, "bounded-uniform-int"),
    "merge-sort": (1000, 1000000, 1800, 120, 100, "SingleShotTime", None, "bounded-uniform-int"),
    "insertion-sort-reverse": (100, 65536, 2700, 240, 100, "SingleShotTime", None,
                               "strictly-descending-distinct-keys"),
}
EXPECTED = [180, 540, 37800, 5400]

kernel = ct.WinDLL("kernel32", use_last_error=True)
power_api = ct.WinDLL("powrprof")
power_api.PowerGetActiveScheme.argtypes = [w.HANDLE, ct.POINTER(ct.c_void_p)]
power_api.PowerGetActiveScheme.restype = w.DWORD
kernel.LocalFree.argtypes = [ct.c_void_p]
kernel.LocalFree.restype = ct.c_void_p


def conditions():
    status = (ct.c_ubyte * 12)()
    if not kernel.GetSystemPowerStatus(ct.byref(status)) or status[0] != 1:
        raise RuntimeError("Alimentación de red ausente o no verificable.")
    ptr = ct.c_void_p()
    if power_api.PowerGetActiveScheme(None, ct.byref(ptr)) != 0:
        raise RuntimeError("No se pudo verificar el plan de energía.")
    try:
        scheme = str(UUID(bytes_le=ct.string_at(ptr, 16)))
    finally:
        kernel.LocalFree(ptr)
    if scheme != BALANCED:
        raise RuntimeError(f"Plan de energía distinto de Equilibrado: {scheme}")
    return {"ac_online": True, "battery_percent": int(status[2]), "power_scheme": scheme}


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write("\n")


def materialize(evidence):
    plan, grid = read(ROOT / "plan.json"), read(GRID)
    specs = list(SPECS)
    suite = plan["suite_id"]
    if (suite != "pilot-extended-01" or plan["pause_seconds"] != 5
            or plan["planning_seed"] == 42
            or [entry["algorithm"] for entry in plan["campaigns"]] != specs
            or [a["algorithm_id"] for a in grid["algorithms"]] != specs):
        raise ValueError("Plan experimental discrepante.")
    rng = random.Random(plan["planning_seed"])
    campaigns = []
    for entry, algorithm in zip(plan["campaigns"], grid["algorithms"]):
        name = entry["algorithm"]
        lo, hi, duration, case_timeout, warm, mode, window, distribution = SPECS[name]
        if (entry != dict(id=f"{suite}-{name}", algorithm=name, timeout_seconds=duration,
                         case_timeout_seconds=case_timeout, warmup_iterations=warm)
                or algorithm["input_distribution"] != distribution
                or algorithm["seeds"] != ["42"]):
            raise ValueError(f"Parámetros discrepantes: {name}")
        sizes = algorithm["sizes"]["values"]
        if sorted(set(sizes)) != sizes or len(sizes) != 60 or (sizes[0], sizes[-1]) != (lo, hi):
            raise ValueError(f"Malla discrepante: {name}")
        ordered = sizes.copy()
        rng.shuffle(ordered)
        jmh = dict(mode=mode, forks=3, warmup_iterations=warm,
                   measurement_iterations=10, batch_size=1)
        if window is not None:
            jmh.update(warmup_duration_ms=window, measurement_duration_ms=window)
        common = {"schema_version": 1, "threads": 1, "results_directory": "datasets/raw"}
        limits = dict(payload_budget_bytes=134217728, heap_max_mib=256, iteration_timeout_ms=10000)
        paths = []
        for n in ordered:
            raw_id = f"{entry['id']}-n{n}"
            path = evidence / "configs" / entry["id"] / f"{raw_id}.json"
            config = dict(**common, experiment_id=raw_id,
                          limits=dict(**limits, campaign_timeout_ms=case_timeout*1000),
                          algorithms=[dict(algorithm, sizes=dict(distribution="custom", values=[n]),
                                           jmh=jmh)])
            write(path, config)
            paths.append(path)
        campaigns.append(dict(entry, cases=[dict(position=i, n=n, raw_experiment_id=p.stem,
                                                  config=p.relative_to(evidence).as_posix(),
                                                  config_sha256=sha(p))
                                             for i, (n, p) in enumerate(zip(ordered, paths), 1)]))
    resolved = dict(plan, campaigns=campaigns, mask="0x1", plan_sha256=sha(ROOT / "plan.json"),
                    grid_sha256=sha(GRID))
    write(evidence / "resolved-plan.json", resolved)
    return resolved


def validate(evidence, plan, command):
    total = [0, 0, 0, 0]
    for campaign in plan["campaigns"]:
        for case in campaign["cases"]:
            config = evidence / case["config"]
            raw = subprocess.check_output([*command, RUNNER, "--dry-run", str(config)])
            dry = json.loads(raw)
            parsed, = dry["plan"]["cases"]
            jmh = parsed["jmh"]
            expected = read(config)["algorithms"][0]["jmh"]
            if (dry["case_count"] != 1 or dry["threads"] != 1
                    or parsed["seed"] != "42" or parsed["input_size"] != case["n"]
                    or parsed["algorithm_id"] != campaign["algorithm"]
                    or parsed["input_distribution"] != SPECS[campaign["algorithm"]][-1]
                    or {k: v for k, v in jmh.items() if v is not None} != expected
                    or dry["limits"] != read(config)["limits"]
                    or dry["plan"]["experiment_id"] != case["raw_experiment_id"]):
                raise ValueError(f"Dry-run discrepante: {config.name}")
            target = evidence / "dry-run" / f"{config.stem}.json"
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(raw)
            counters = [dry["case_count"], dry["plan"]["total_forks"],
                        dry["plan"]["total_warmup_iterations"], dry["plan"]["total_measurement_iterations"]]
            total = [a+b for a, b in zip(total, counters)]
    if total != EXPECTED:
        raise ValueError(f"Totales discrepantes: {total}")
    write(evidence / "dry-run-summary.json", dict(zip(
        ("cases", "forks", "warmups", "measurements"), total)))
    print(f"Dry-run confirmado: {total}", flush=True)


def execute(evidence, plan, command, jar):
    def check_environment():
        conditions()
        if affinity() != 0xfff:
            raise RuntimeError("Cambió la máscara base de Windows.")

    events = evidence / "events.jsonl"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("El repositorio debe estar limpio.")
    if any((RAW / case["raw_experiment_id"]).exists()
           for campaign in plan["campaigns"] for case in campaign["cases"]):
        raise RuntimeError("Ya existe evidencia de esta campaña. No se reanudará automáticamente.")
    classes = core_types()
    if classes != {i: int(i < 4) for i in range(12)}:
        raise RuntimeError(f"Topología discrepante: {classes}")
    check_environment()
    probe = evidence / "probe-p.log"
    with probe.open("x", encoding="utf-8") as log:
        result = supervise([command[0], "--enable-native-access=ALL-UNNAMED", *command[1:], PROBE],
                           0, 20, "p", check=check_environment, output=log)
    if result != 0:
        raise RuntimeError("Falló la sonda JVM.")
    verify_forks([probe], 1, 1)
    initial_jar_hash = sha(jar)
    append(events, "preflight", commit=commit, jar_sha256=initial_jar_hash, java=subprocess.check_output(
        [command[0], "-version"], stderr=subprocess.STDOUT, text=True),
        resolved_plan_sha256=sha(evidence/"resolved-plan.json"), topology=classes, power=conditions())
    for campaign in plan["campaigns"]:
        identity = {"campaign": campaign["id"], "algorithm": campaign["algorithm"]}
        deadline = time.monotonic() + campaign["timeout_seconds"]

        def remaining():
            check_environment()
            available = deadline - time.monotonic()
            if available <= 0:
                raise TimeoutError("Se agotó el presupuesto global de campaña.")
            return available

        append(events, "campaign_started", **identity)
        for case in campaign["cases"]:
            started = time.monotonic()
            fields = dict(**identity, position=case["position"], n=case["n"],
                          raw_experiment_id=case["raw_experiment_id"])
            try:
                timeout = min(campaign["case_timeout_seconds"], remaining())
                config = evidence / case["config"]
                if sha(config) != case["config_sha256"] or sha(jar) != initial_jar_hash:
                    raise RuntimeError("Cambió el JAR o la configuración.")
                append(events, "case_started", **fields, applied_timeout_s=timeout)
                with (evidence / f"{config.stem}.log").open("x", encoding="utf-8") as log:
                    result = supervise([*command, RUNNER, "--execute", str(config)],
                                       0, timeout, "p", check=remaining, output=log)
                if result != 0:
                    raise RuntimeError(f"El coordinador salió con código {result}.")
                attempt = RAW / config.stem / "case-000001/attempt-001"
                pids = verify_forks(sorted(attempt.glob("affinity-*.txt")), 1, 3)
                record, = read(attempt / "jmh.json")
                if list(map(len, record["primaryMetric"]["rawData"])) != [10] * 3:
                    raise RuntimeError("Matriz de puntuaciones incompleta.")
                append(events, "case_completed", **fields, fork_pids=pids,
                       duration_s=time.monotonic()-started)
                print(f"{campaign['id']} {case['position']:02d}/60 n={case['n']}", flush=True)
                if case["position"] < 60:
                    pause_started = time.monotonic()
                    append(events, "pause_started", **fields)
                    while (pause_left := plan["pause_seconds"] - (time.monotonic()-pause_started)) > 0:
                        time.sleep(min(1.0, remaining(), pause_left))
                    append(events, "pause_completed", **fields,
                           duration_s=time.monotonic()-pause_started)
                remaining()
            except (Exception, KeyboardInterrupt) as failure:
                append(events, "suite_interrupted", **fields, failure=str(failure),
                       failure_type=type(failure).__name__, elapsed_s=time.monotonic()-started)
                raise
        append(events, "campaign_completed", **identity)
    append(events, "suite_completed", power=conditions())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jar", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    args.evidence.mkdir(parents=True)
    plan = materialize(args.evidence)
    java = Path(os.environ["ALGOPERFORMANCE_JDK_HOME"]) / "bin/java.exe"
    command = [str(java), "-cp", str(args.jar.resolve())]
    validate(args.evidence, plan, command)
    if args.execute:
        execute(args.evidence, plan, command, args.jar)


if __name__ == "__main__":
    main()
