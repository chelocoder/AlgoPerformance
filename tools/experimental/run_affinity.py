"""Ejecuta una sola vez el plan autorizado; conserva evidencia y se detiene al fallar."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime

from windows_affinity import affinity, core_types

PLAN = Path("docs/examples/pilot-affinity-01")
RAW = Path("datasets/raw")
MASKS = {"default": 0xfff, "p": 1, "e": 0x10}
RUNNER = "pe.algoperformance.instrument.runner.ExperimentMain"
PROBE = "pe.algoperformance.instrument.runner.WindowsAffinity"


def now():
    return datetime.now().astimezone().isoformat()


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def append(file, event, **fields):
    with file.open("a", encoding="utf-8") as stream:
        print(json.dumps({"event": event, "timestamp": now(), **fields}), file=stream)


def launch(core, timeout, command, log):
    selector = [] if core == "default" else ["--core", core]
    with log.open("wb") as output:
        subprocess.run([sys.executable, str(Path(__file__).with_name("windows_affinity.py")),
                        "--timeout-seconds", str(timeout), *selector, "--", *command],
                       stdout=output, stderr=subprocess.STDOUT, check=True)


def verify_forks(records, expected, count):
    pids = set()
    for record in records:
        content = record.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"Affinity verified before warmup: pid=(\d+) mask=0x([0-9a-f]+)", content)
        if not match or int(match[2], 16) != expected:
            raise RuntimeError(f"Registro de afinidad inválido en {record}")
        pids.add(int(match[1]))
    if len(pids) != count:
        raise RuntimeError(f"Conteo de JVM verificadas {len(pids)}, esperado {count}")
    return sorted(pids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jar", type=Path)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    java = Path(os.environ["ALGOPERFORMANCE_JDK_HOME"]) / "bin/java.exe"
    plan_path = PLAN / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    order = plan["order"]
    pause_seconds = plan["pause_seconds_between_cases"]
    configs = [PLAN / cell["config"] for cell in order]
    classes = core_types()
    if (affinity() != MASKS["default"] or set(classes) != set(range(12))
            or any(classes[cpu] != (1 if cpu < 4 else 0) for cpu in classes)):
        raise RuntimeError(f"Topología distinta de la aprobada: {classes}")
    if any((RAW / p.stem).exists() for p in configs):
        raise RuntimeError("Ya existe evidencia de al menos un caso; se requiere revisión.")
    if len(order) != 12 or len(set(configs)) != 12:
        raise RuntimeError("El plan debe contener 12 configuraciones distintas.")
    args.evidence.mkdir(parents=True)
    events = args.evidence / "events.jsonl"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    if dirty.strip():
        raise RuntimeError("Hay cambios en Git; se detuvo antes de las mediciones.")
    append(events, "preflight", git_commit=commit, jar_sha256=sha(args.jar),
           plan_sha256=sha(plan_path), hashes={p.name: sha(p) for p in configs},
           classes=classes, masks=MASKS, pause_seconds=pause_seconds)
    classpath = [str(java), "-cp", str(args.jar)]
    for core, mask in MASKS.items():
        probe = args.evidence / f"probe-{core}.log"
        launch(core, 20, [str(java), "--enable-native-access=ALL-UNNAMED", *classpath[1:], PROBE],
               probe)
        verify_forks([probe], mask, 1)
    for config in configs:
        dry_run = subprocess.check_output([*classpath, RUNNER, "--dry-run", str(config)])
        (args.evidence / f"{config.stem}-dry-run.json").write_bytes(dry_run)
        dry = json.loads(dry_run)
        case, = dry["plan"]["cases"]
        jmh = case["jmh"]
        index = configs.index(config)
        cell = order[index]
        if (case["seed"] != "42" or case["input_size"] != cell["n"] or dry["threads"] != 1
                or case["algorithm_id"] != "insertion-sort-reverse"
                or case["input_distribution"] != "strictly-descending-distinct-keys"
                or [jmh[key] for key in ("mode", "forks", "warmup_iterations",
                                         "measurement_iterations", "batch_size")]
                   != ["SingleShotTime", 3, 1000, 20, 1]):
            raise RuntimeError(f"Parámetros inesperados en {config}")
    append(events, "campaign_started")
    for index, (cell, config) in enumerate(zip(order, configs), 1):
        core = cell["affinity"]
        start = time.monotonic()
        append(events, "case_started", position=index, **cell)
        try:
            launch(core, plan["hard_timeout_seconds_per_case"],
                   [*classpath, RUNNER, "--execute", str(config)],
                   args.evidence / f"{config.stem}.log")
            result = RAW / config.stem / "case-000001/attempt-001"
            pids = verify_forks(sorted(result.glob("affinity-*.txt")), MASKS[core], 3)
            data, = json.loads((result / "jmh.json").read_bytes())
            scores = data["primaryMetric"]["rawData"]
            if list(map(len, scores)) != [20] * 3:
                raise RuntimeError(f"Matriz de mediciones incompleta en {config}")
        except Exception as error:
            append(events, "case_failed", duration_seconds=time.monotonic() - start,
                   error=str(error), **cell)
            raise
        append(events, "case_completed", duration_seconds=time.monotonic() - start,
               fork_pids=pids, **cell)
        print(f"{index}/12 {config.stem}: {time.monotonic() - start:.2f} s", flush=True)
        if index != len(order):
            started = time.monotonic()
            append(events, "pause_started", after_position=index)
            time.sleep(pause_seconds)
            append(events, "pause_completed", after_position=index,
                   duration_seconds=time.monotonic() - started)
    append(events, "campaign_completed")


if __name__ == "__main__":
    main()
