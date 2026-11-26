"""Continuación 05F-R con vigilancia de energía fuera del hilo supervisor."""
from contextlib import contextmanager
import ctypes as ct
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

from run_extended import conditions, read, write
from run_affinity import PROBE, RAW, RUNNER, append, sha, verify_forks
from windows_affinity import affinity, core_types, supervise

JAR_HASH = "75daa09462afe89fae302e064e70caaef9a8e2065ae4b97f59dc61b7cf3639e6"
SIZES = [62387, 677, 944, 2356, 194, 1689, 527, 250, 230, 52941, 128, 348]
BASE = Path(".local/phase05f")
OUTPUT = Path(".local/phase05fr/run")
API = ct.WinDLL("kernel32", use_last_error=True)
API.SetThreadExecutionState.argtypes = [ct.c_ulong]
API.SetThreadExecutionState.restype = ct.c_ulong
API.GetTickCount64.restype = ct.c_ulonglong
API.QueryUnbiasedInterruptTime.argtypes = [ct.POINTER(ct.c_ulonglong)]
CONTINUOUS = 0x80000000
SYSTEM_REQUIRED = 1
POWER = ct.WinDLL("powrprof")
NOTIFY = ct.WINFUNCTYPE(ct.c_ulong, ct.c_void_p, ct.c_ulong, ct.c_void_p)


class Subscription(ct.Structure):
    _fields_ = [("callback", NOTIFY), ("context", ct.c_void_p)]


POWER.PowerRegisterSuspendResumeNotification.argtypes = [
    ct.c_ulong, ct.POINTER(Subscription), ct.POINTER(ct.c_void_p)]
POWER.PowerUnregisterSuspendResumeNotification.argtypes = [ct.c_void_p]


@contextmanager
def suspend_notifications():
    signals = []

    @NOTIFY
    def receive(_context, kind, _setting):
        if kind in (4, 7, 18):
            signals.append(kind)
        return 0

    handle = ct.c_void_p()
    registration = Subscription(receive, None)
    status = POWER.PowerRegisterSuspendResumeNotification(2, ct.byref(registration), ct.byref(handle))
    if status:
        raise ct.WinError(status)
    try:
        yield signals
    finally:
        status = POWER.PowerUnregisterSuspendResumeNotification(handle)
        if status:
            raise ct.WinError(status)


def clocks():
    active = ct.c_ulonglong()
    if not API.QueryUnbiasedInterruptTime(ct.byref(active)):
        raise ct.WinError(ct.get_last_error())
    return API.GetTickCount64()/1000, active.value/10_000_000


def elapsed(start, end):
    return tuple(b-a for a, b in zip(start, end))


def check_sleep(start, end):
    wall, active = elapsed(start, end)
    if wall-active >= 1:
        raise RuntimeError(f"Indicio de suspensión: pared={wall:.3f}s, sistema activo={active:.3f}s")


@contextmanager
def stay_awake(events):
    thread = threading.get_native_id()
    flags = CONTINUOUS | SYSTEM_REQUIRED
    previous = API.SetThreadExecutionState(flags)
    if not previous:
        raise RuntimeError("Falló SetThreadExecutionState al activar.")
    try:
        append(events, "sleep_prevention_enabled", thread_id=thread, flags=hex(flags),
               previous=hex(previous))
        yield
    finally:
        previous = API.SetThreadExecutionState(CONTINUOUS)
        append(events, "sleep_prevention_released", thread_id=thread, flags=hex(CONTINUOUS),
               previous=hex(previous), ok=bool(previous and previous & SYSTEM_REQUIRED))
        if not previous or not previous & SYSTEM_REQUIRED:
            raise RuntimeError("No se confirmó la liberación de la solicitud de energía.")


class PowerMonitor:
    def __init__(self, sample=conditions):
        self.sample = sample
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.last = None
        self.error = None
        self.thread = threading.Thread(target=self.poll, daemon=True)

    def poll(self):
        while not self.stop.is_set():
            try:
                self.last = (time.monotonic(), self.sample())
            except Exception as failure:
                self.error = failure
                self.ready.set()
                return
            self.ready.set()
            self.stop.wait(.5)

    def check(self):
        if self.error is not None:
            raise RuntimeError(str(self.error))
        if self.last is None or time.monotonic()-self.last[0] > 3:
            raise RuntimeError("La comprobación asíncrona de energía dejó de responder.")
        return self.last[1]

    def __enter__(self):
        self.thread.start()
        if not self.ready.wait(3):
            self.stop.set()
            raise RuntimeError("La comprobación inicial de energía excedió el plazo.")
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=1)


def launch(command, timeout, log, check):
    with log.open("x", encoding="utf-8") as output:
        code = supervise(command, 0, timeout, "p", check=check, output=output)
    if code != 0:
        raise RuntimeError(f"El coordinador salió con código {code}.")


def main():
    jar = next(Path("instrument/target").glob("*-benchmarks.jar")).resolve()
    if sha(jar) != JAR_HASH:
        raise RuntimeError("SHA-256 del JAR diferente del autorizado.")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Repositorio con cambios pendientes.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    source = BASE/"complete"/"execution"
    old_events = [json.loads(line) for line in (source/"events.jsonl").read_text().splitlines()]
    done = {e["position"] for e in old_events if e["event"] == "case_completed"
            and e["algorithm"] == "insertion-sort-reverse"}
    if done != set(range(1,49)) or sum(e["event"] == "case_completed" for e in old_events) != 168:
        raise RuntimeError("El punto de continuación difiere de lo autorizado.")
    prior_plan = read(source/"resolved-plan.json")
    insertion = prior_plan["campaigns"][-1]
    pending = insertion["cases"][48:]
    if [c["n"] for c in pending] != SIZES:
        raise RuntimeError("Orden distinto del autorizado.")
    OUTPUT.mkdir(parents=True)
    events = OUTPUT/"events.jsonl"
    java = Path(os.environ["ALGOPERFORMANCE_JDK_HOME"])/"bin/java.exe"
    cmd = [str(java), "-cp", str(jar)]
    entries = []
    totals = [0,0,0,0]
    for case in pending:
        original = source/case["config"]
        if sha(original) != case["config_sha256"]:
            raise RuntimeError("Cambió una configuración del plan original.")
        config = read(original)
        config["experiment_id"] += "-05fr"
        path = OUTPUT/"configs"/(config["experiment_id"]+".json")
        write(path, config)
        dry = json.loads(subprocess.check_output([*cmd, RUNNER, "--dry-run", str(path)], timeout=30))
        planned, = dry["plan"]["cases"]
        if (planned["input_size"] != case["n"] or planned["seed"] != "42"
                or planned["input_distribution"] != "strictly-descending-distinct-keys"
                or planned["algorithm_id"] != "insertion-sort-reverse" or dry["threads"] != 1
                or any(planned["jmh"][k] != v for k,v in dict(
                    mode="SingleShotTime", forks=3, warmup_iterations=100, measurement_iterations=10,
                    batch_size=1).items())
                or dry["limits"]["heap_max_mib"] != 256 or dry["limits"]["payload_budget_bytes"] != 134217728
                or (RAW/path.stem).exists()):
            raise RuntimeError(f"Dry-run discrepante: {path}")
        counters = [dry["case_count"], dry["plan"]["total_forks"],
                    dry["plan"]["total_warmup_iterations"], dry["plan"]["total_measurement_iterations"]]
        totals = [a+b for a,b in zip(totals,counters)]
        write(OUTPUT/"dry-run"/path.name, dry)
        entries.append(dict(case, raw_experiment_id=path.stem,
                            config=path.relative_to(OUTPUT).as_posix(), config_sha256=sha(path)))
    if totals != [12,36,3600,360]:
        raise RuntimeError(f"Totales de dry-run discrepantes: {totals}")
    write(OUTPUT/"dry-run-summary.json", dict(zip(("cases","forks","warmups","measurements"),totals)))
    plan = dict(prior_plan, campaigns=[dict(insertion, timeout_seconds=1200, cases=entries)])
    write(OUTPUT/"resolved-plan.json", plan)
    topology = core_types()
    if affinity() != 0xfff or topology != {i:int(i<4) for i in range(12)}:
        raise RuntimeError("Topología o máscara base discrepantes.")
    with stay_awake(events), suspend_notifications() as signals, PowerMonitor() as power:
        baseline = clocks()
        power.check()
        probe = OUTPUT/"probe-p.log"
        launch([cmd[0], "--enable-native-access=ALL-UNNAMED", *cmd[1:], PROBE], 20, probe, power.check)
        verify_forks([probe],1,1)
        append(events, "preflight", commit=commit, jar_sha256=JAR_HASH, topology=topology,
               power=power.check(), resolved_plan_sha256=sha(OUTPUT/"resolved-plan.json"),
               preceding_execution_sha256=sha(source/"events.jsonl"),
               java=subprocess.check_output([cmd[0],"-version"], stderr=subprocess.STDOUT,
                                            text=True,timeout=10))
        started = clocks()

        def check():
            if signals:
                raise RuntimeError(f"Windows notificó suspensión o reanudación: {signals}")
            now = clocks()
            check_sleep(baseline, now)
            if elapsed(started, now)[0] >= 1200:
                raise TimeoutError("Plazo global de 1200 s agotado.")
            power.check()

        identity = dict(campaign=insertion["id"], algorithm=insertion["algorithm"])
        append(events,"campaign_started", **identity)
        for case in entries:
            beginning = clocks()
            fields = dict(**identity, position=case["position"], n=case["n"],
                          raw_experiment_id=case["raw_experiment_id"])
            config = OUTPUT/case["config"]
            try:
                check()
                if sha(config) != case["config_sha256"] or sha(jar) != JAR_HASH:
                    raise RuntimeError("Cambió el JAR o la configuración.")
                timeout = min(240,1200-elapsed(started,clocks())[0])
                append(events,"case_started",**fields, applied_timeout_s=timeout,
                       wall_clock_s=beginning[0], active_system_clock_s=beginning[1])

                def check_case():
                    check()
                    if elapsed(beginning,clocks())[0] >= timeout:
                        raise TimeoutError("Plazo de pared por caso agotado.")

                launch([*cmd,RUNNER,"--execute",str(config)],timeout,OUTPUT/f"{config.stem}.log",check_case)
                check_case()
                attempt = RAW/config.stem/"case-000001/attempt-001"
                pids = verify_forks(sorted(attempt.glob("affinity-*.txt")),1,3)
                record, = read(attempt/"jmh.json")
                if list(map(len,record["primaryMetric"]["rawData"])) != [10]*3:
                    raise RuntimeError("Matriz de mediciones incompleta.")
                wall, active = elapsed(beginning,clocks())
                append(events,"case_completed",**fields, fork_pids=pids, duration_s=wall,
                       system_awake_s=active)
                print(f"{case['position']}/60 n={case['n']} completado ({wall:.2f}s)",flush=True)
                if case["position"] < 60:
                    start_pause = clocks()
                    append(events,"pause_started",**fields)
                    while (left := 5-elapsed(start_pause,clocks())[0]) > 0:
                        check()
                        time.sleep(min(.25,left))
                    append(events,"pause_completed",**fields,duration_s=elapsed(start_pause,clocks())[0])
            except (Exception,KeyboardInterrupt) as error:
                wall, active = elapsed(beginning,clocks())
                append(events,"suite_interrupted",**fields,failure=str(error),
                       elapsed_s=wall,system_awake_s=active)
                raise
        append(events,"campaign_completed",**identity)
        append(events,"suite_completed",power=power.check())


if __name__ == "__main__":
    main()
