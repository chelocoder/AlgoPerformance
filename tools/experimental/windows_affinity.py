"""Supervisa un comando y sus descendientes dentro de un Job Object de Windows."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from struct import unpack_from

MASK = "ALGOPERFORMANCE_EXPECTED_AFFINITY"
kernel = c.WinDLL("kernel32", use_last_error=True)


def api(name, result, *arguments):
    function = getattr(kernel, name)
    function.restype = result
    function.argtypes = arguments
    return function


create_job = api("CreateJobObjectW", w.HANDLE, w.LPVOID, w.LPCWSTR)
configure_job = api("SetInformationJobObject", w.BOOL, w.HANDLE, c.c_int, w.LPVOID, w.DWORD)
query_job = api("QueryInformationJobObject", w.BOOL, w.HANDLE, c.c_int, w.LPVOID, w.DWORD, w.LPVOID)
assign_job = api("AssignProcessToJobObject", w.BOOL, w.HANDLE, w.HANDLE)
open_process = api("OpenProcess", w.HANDLE, w.DWORD, w.BOOL, w.DWORD)
close = api("CloseHandle", w.BOOL, w.HANDLE)
current = api("GetCurrentProcess", w.HANDLE)
get_mask = api("GetProcessAffinityMask", w.BOOL, w.HANDLE,
               c.POINTER(c.c_size_t), c.POINTER(c.c_size_t))
cpu_sets = api("GetSystemCpuSetInformation", w.BOOL, w.LPVOID, w.DWORD,
               c.POINTER(w.DWORD), w.HANDLE, w.DWORD)


class BasicLimits(c.Structure):
    _fields_ = [("process_time", c.c_longlong), ("job_time", c.c_longlong),
                ("flags", w.DWORD), ("min_working_set", c.c_size_t),
                ("max_working_set", c.c_size_t), ("active_processes", w.DWORD),
                ("affinity", c.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]


class ExtendedLimits(c.Structure):
    _fields_ = [("basic", BasicLimits), ("io_counters", c.c_ulonglong * 6),
                ("memory_limits_and_peaks", c.c_size_t * 4)]


def checked(value):
    if not value:
        raise c.WinError(c.get_last_error())
    return value


def affinity():
    process, system = c.c_size_t(), c.c_size_t()
    checked(get_mask(current(), c.byref(process), c.byref(system)))
    return process.value


def core_types():
    length = w.DWORD()
    if not cpu_sets(None, 0, c.byref(length), None, 0) and c.get_last_error() != 122:
        raise c.WinError(c.get_last_error())
    records = c.create_string_buffer(length.value)
    checked(cpu_sets(records, length.value, c.byref(length), None, 0))
    classes = {}
    offset = 0
    while offset < length.value:
        size, kind = unpack_from("<II", records, offset)
        if size < 8 or offset + size > length.value:
            raise RuntimeError("Registro de topología de Windows inválido.")
        if kind == 0:
            group, logical, _, _, _, efficiency = unpack_from("<HBBBBB", records, offset + 12)
            if group != 0:
                raise RuntimeError("El supervisor requiere un solo grupo de procesadores.")
            classes[logical] = efficiency
        offset += size
    return classes


def bootstrap(command):
    token = sys.stdin.readline()
    if token != "start\n":
        return 1
    expected = int(os.environ[MASK], 16)
    if affinity() != expected:
        raise RuntimeError("La máscara del lanzador no coincide con el tratamiento.")
    return subprocess.call(command, stdin=subprocess.DEVNULL)


def wait_for_child(child, deadline, check):
    if check is None:
        return child.wait(timeout=max(0, deadline - time.monotonic()))
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(child.args, 0)
        check()
        try:
            result = child.wait(timeout=min(0.25, remaining))
        except subprocess.TimeoutExpired:
            continue
        check()
        if time.monotonic() > deadline:
            raise subprocess.TimeoutExpired(child.args, 0)
        return result


def supervise(command, logical_cpu, timeout, treatment="default", *, check=None, output=None):
    deadline = time.monotonic() + timeout

    def phase(label):
        if output is not None:
            print(f"supervisor_phase={label} utc={datetime.now(timezone.utc).isoformat()} "
                  f"monotonic={time.monotonic():.6f}", file=output, flush=True)

    phase("setup")
    inherited = affinity()
    expected = inherited if logical_cpu is None else 1 << logical_cpu
    if inherited & expected != expected:
        raise ValueError("Procesador lógico fuera de la máscara heredada.")
    job = checked(create_job(None, None))
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if logical_cpu is not None:
            limits.basic.flags |= 0x10  # JOB_OBJECT_LIMIT_AFFINITY
            limits.basic.affinity = expected
        checked(configure_job(job, 9, c.byref(limits), c.sizeof(limits)))
        env = dict(os.environ)
        env[MASK] = f"{expected:x}"
        env["ALGOPERFORMANCE_AFFINITY_TREATMENT"] = treatment
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_bootstrap", *command],
                                 stdin=subprocess.PIPE, text=True, env=env, stdout=output,
                                 stderr=subprocess.STDOUT if output else None)
        try:
            # PROCESS_SET_QUOTA | PROCESS_TERMINATE. El comando espera hasta la asignación.
            handle = checked(open_process(0x0101, False, child.pid))
            try:
                checked(assign_job(job, handle))
            finally:
                close(handle)
            phase("assigned")
            if check is not None:
                check()
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(command, timeout)
            child.stdin.write("start\n")
            child.stdin.close()
            print(f"Windows Job: pid={child.pid} expected=0x{expected:x}", file=output, flush=True)
            phase("released")
            result = wait_for_child(child, deadline, check)
            phase("child_exited")
            if query_job(job, 9, c.byref(limits), c.sizeof(limits), None):
                print(f"peak_job_commit_bytes={limits.memory_limits_and_peaks[3]}", file=output, flush=True)
            return result
        finally:
            phase("close_job")
            checked(close(job))
            job = None
            if not child.stdin.closed:
                child.stdin.close()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)
            phase("cleanup_finished")
    finally:
        if job is not None:
            close(job)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", choices=("p", "e"))
    parser.add_argument("--topology", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    classes = core_types()
    if args.topology:
        print(f"Windows affinity=0x{affinity():x}; logical CPU -> efficiency class: {classes}")
        return 0
    if args.timeout_seconds <= 0 or len(args.command) < 2 or args.command[0] != "--":
        parser.error("Indique un plazo positivo y un comando después de --.")
    logical_cpu = None
    if args.core:
        distinct = sorted(set(classes.values()))
        if len(distinct) != 2:
            parser.error("Se requieren dos clases de eficiencia para seleccionar P o E.")
        requested = distinct[-1] if args.core == "p" else distinct[0]
        eligible = [cpu for cpu, value in classes.items()
                    if value == requested and affinity() & (1 << cpu)]
        if not eligible:
            parser.error("La máscara heredada excluye la clase seleccionada.")
        logical_cpu = min(eligible)
    try:
        return supervise(args.command[1:], logical_cpu, args.timeout_seconds, args.core or "default")
    except subprocess.TimeoutExpired:
        print("Plazo agotado. Se cerró el Job completo.", file=sys.stderr)
        return 124


if __name__ == "__main__":
    if sys.argv[1:2] == ["_bootstrap"]:
        raise SystemExit(bootstrap(sys.argv[2:]))
    raise SystemExit(main())
