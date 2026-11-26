"""Valida y ejecuta el plan de tamaños ancla, sin reintentar casos fallidos."""
import argparse
import ctypes as ct
import json
import os
from pathlib import Path
import re
import subprocess
import time

from run_affinity import PROBE, RAW, RUNNER, append, launch, sha, verify_forks
from windows_affinity import affinity, core_types

PLAN = Path("docs/examples/pilot-extended-anchors-01")
SETTINGS = {
    "array-sum": ({1000, 100000, 10000000}, {5, 10}, "AverageTime", 200, "bounded-uniform-int"),
    "merge-sort": ({1000, 100000, 1000000}, {50, 100}, "SingleShotTime", None, "bounded-uniform-int"),
    "insertion-sort-reverse": ({100, 8192, 65536}, {30, 100}, "SingleShotTime", None,
                               "strictly-descending-distinct-keys"),
}
BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"


def power():
    status = (ct.c_ubyte * 12)()
    if not ct.windll.kernel32.GetSystemPowerStatus(ct.byref(status)) or status[0] != 1:
        raise RuntimeError("Se requiere alimentación de red verificada.")
    scheme = subprocess.check_output(["powercfg", "/getactivescheme"]).decode("ascii", "replace")
    if BALANCED not in scheme.lower():
        raise RuntimeError("Se requiere el plan Equilibrado.")
    return {"ac_online": True, "battery_percent": int(status[2]), "scheme": BALANCED}


def preflight(classpath, evidence):
    plan = json.loads((PLAN / "plan.json").read_bytes())
    ordered = []
    totals = [0, 0, 0, 0]
    for entry in plan["order"]:
        config = PLAN / entry["config"]
        raw = subprocess.check_output([*classpath, RUNNER, "--dry-run", str(config)])
        (evidence / f"{config.stem}-dry-run.json").write_bytes(raw)
        dry = json.loads(raw)
        case, = dry["plan"]["cases"]
        alg, n, jmh = (case[k] for k in ("algorithm_id", "input_size", "jmh"))
        sizes, budgets, mode, window, distribution = SETTINGS[alg]
        warm = jmh["warmup_iterations"]
        timeout = 240 if alg == "insertion-sort-reverse" and n == 65536 and warm == 100 else 120
        if (n not in sizes or warm not in budgets or case["seed"] != "42"
                or case["input_distribution"] != distribution or dry["threads"] != 1
                or dry["results_directory"] != "datasets/raw"
                or entry["hard_timeout_seconds"] != timeout
                or dry["limits"] != {"payload_budget_bytes": 134217728, "heap_max_mib": 256,
                                     "iteration_timeout_ms": 10000, "campaign_timeout_ms": timeout * 1000}
                or dry["plan"]["experiment_id"] != config.stem
                or [jmh[k] for k in ("mode", "forks", "measurement_iterations", "batch_size",
                                     "warmup_duration_ms", "measurement_duration_ms")]
                   != [mode, 3, 10, 1, window, window]):
            raise ValueError(f"Configuración discrepante: {config}")
        ordered.append((config, alg, n, warm, timeout))
        for i, value in enumerate([dry["case_count"], dry["plan"]["total_forks"],
                                   dry["plan"]["total_warmup_iterations"],
                                   dry["plan"]["total_measurement_iterations"]]):
            totals[i] += value
    expected = {(alg, n, w) for alg, spec in SETTINGS.items() for n in spec[0] for w in spec[1]}
    if (totals != [18, 54, 2655, 540] or {(a, n, w) for _, a, n, w, _ in ordered} != expected
            or any(a[1:3] != b[1:3] for a, b in zip(ordered, reversed(ordered)))
            or not 4 <= sum(w == max(SETTINGS[a][1]) for _, a, _, w, _ in ordered[:9]) <= 5
            or plan["pause_seconds_between_cases"] != 15):
        raise ValueError("Conteos, orden o pausa incorrectos.")
    return ordered, totals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jar", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    args.evidence.mkdir(parents=True)
    events = args.evidence / "events.jsonl"
    java = Path(os.environ["ALGOPERFORMANCE_JDK_HOME"]) / "bin/java.exe"
    classpath = [str(java), "-cp", str(args.jar.resolve())]
    ordered, totals = preflight(classpath, args.evidence)
    print(f"Validado: {totals}", flush=True)
    if not args.execute:
        return
    clean = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    if clean.strip() or any((RAW / config.stem).exists() for config, *_ in ordered):
        raise RuntimeError("Git tiene cambios o existe evidencia de un caso; no se ejecutará.")
    classes = core_types()
    if classes != {cpu: int(cpu < 4) for cpu in range(12)} or affinity() != 0xfff:
        raise RuntimeError(f"Topología inesperada: {classes}")
    conditions = power()
    probe = args.evidence / "probe-p.log"
    launch("p", 20, [str(java), "--enable-native-access=ALL-UNNAMED", *classpath[1:], PROBE], probe)
    verify_forks([probe], 1, 1)
    append(events, "preflight", commit=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                              text=True).strip(),
           jar_sha256=sha(args.jar), plan_sha256=sha(PLAN / "plan.json"),
           configs={config.name: sha(config) for config, *_ in ordered},
           topology=classes, power=conditions, mask="0x1", totals=totals)
    append(events, "campaign_started")
    for index, (config, alg, n, warm, timeout) in enumerate(ordered, 1):
        fields = dict(position=index, config=config.name, algorithm=alg, n=n, warmup=warm,
                      timeout_seconds=timeout)
        log = args.evidence / f"{config.stem}.log"
        try:
            power()
            start = time.monotonic()
            append(events, "case_started", **fields)
            launch("p", timeout, [*classpath, RUNNER, "--execute", str(config)], log)
            duration = time.monotonic() - start
            attempt = RAW / config.stem / "case-000001/attempt-001"
            pids = verify_forks(sorted(attempt.glob("affinity-*.txt")), 1, 3)
            record, = json.loads((attempt / "jmh.json").read_bytes())
            if list(map(len, record["primaryMetric"]["rawData"])) != [10] * 3:
                raise RuntimeError("Matriz de resultados incompleta.")
            memory = re.search(r"peak_job_commit_bytes=(\d+)", log.read_text(errors="replace"))
            append(events, "case_completed", **fields, duration_seconds=duration,
                   fork_pids=pids, peak_job_commit_bytes=int(memory[1]) if memory else None)
        except Exception as failure:
            append(events, "case_failed", **fields, error=str(failure))
            raise
        print(f"{index}/18 {config.stem}: {duration:.3f} s", flush=True)
        if index < len(ordered):
            start = time.monotonic()
            append(events, "pause_started", after_position=index)
            time.sleep(15)
            append(events, "pause_completed", after_position=index,
                   duration_seconds=time.monotonic() - start)
    append(events, "campaign_completed", power=power())


if __name__ == "__main__":
    main()
