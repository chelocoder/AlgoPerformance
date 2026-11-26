"""Operación del instrumento v1.0.0-rc.2."""
import argparse
import csv
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import statistics
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".local/phase08r"
VERSION="1.0.0-rc.2"
JAR=OUT/f"AlgoPerformance-v{VERSION}.jar"
CATALOG=json.loads((Path(__file__).with_name("catalog.json")).read_bytes())
sys.path.insert(0,str(ROOT/"tools/experimental"))
from run_affinity import append
from run_extended_recovery import PowerMonitor, check_sleep, clocks, stay_awake, suspend_notifications
from windows_affinity import core_types, supervise

BALANCED="381b4222-f694-41f0-9685-ff5bb260df2e"
AFFINITY=re.compile(r"Affinity verified before warmup: pid=(\d+) mask=0x1")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path,value):
    """Publica sólo después de escribir y sincronizar un archivo hermano."""
    temporary=path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    # El directorio es de un intento UUID o está bajo el bloqueo del coordinador.
    if path.exists():
        raise FileExistsError(path)
    temporary.replace(path)


def budget_config(config):
    budgets={}
    for field,default,maximum in (
        ("preparation_timeout_s",60,3600),("preparation_case_timeout_s",10,300),
        ("verification_timeout_s",120,86400),("verification_case_timeout_s",30,3600),
        ("global_timeout_s",None,86400),("timeout_s",None,300),
    ):
        value=config.get(field,default)
        if type(value) is not int or not 1<=value<=maximum:
            raise ValueError(f"Límite inválido: {field}")
        budgets[field]=value
    return budgets


def validated_seeds(seeds):
    if not isinstance(seeds,list) or not seeds or any(
            type(seed) is not int or not -(1<<63)<=seed<1<<63 for seed in seeds
    ) or len(seeds)!=len(set(seeds)):
        raise ValueError("Semillas inválidas o duplicadas")
    return seeds


def sizes(spec):
    if set(spec)=={"values"}:
        values=spec["values"]
    elif set(spec) in ({"start","step","count"},{"start","ratio","count"}):
        start,count=spec["start"],spec["count"]
        if type(start) is not int or not 1<=start<=10_000_000 or type(count) is not int or not 1<=count<=1000:
            raise ValueError("Inicio o cantidad inválidos")
        values=[]
        value=start
        for _ in range(count):
            if not 1<=value<=10_000_000:
                raise ValueError("Malla fuera de límites")
            values.append(value)
            if "step" in spec:
                if type(spec["step"]) is not int or spec["step"]<=0:
                    raise ValueError("Paso inválido")
                value+=spec["step"]
            else:
                if type(spec["ratio"]) is not int or spec["ratio"]<=1:
                    raise ValueError("Razón entera inválida")
                value*=spec["ratio"]
    else:
        raise ValueError("Use lista, progresión aritmética o progresión geométrica")
    if not isinstance(values,list) or not values or len(values)>1000 or any(
            type(n) is not int or not 1<=n<=10_000_000 for n in values) or len(set(values))!=len(values):
        raise ValueError("Tamaños inválidos o duplicados")
    return values


def plan_config(config):
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}",config["campaign"]):
        raise ValueError("Identificador de campaña inválido")
    for name,low,high in (("forks",1,20),("warmups",0,1000),("measurements",1,100),
                          ("timeout_s",1,300),("global_timeout_s",1,86400)):
        if type(config[name]) is not int or not low<=config[name]<=high:
            raise ValueError(name)
    budget_config(config)
    default_seeds=validated_seeds(config.get("seeds",[42]))
    if len({row["id"] for row in config["algorithms"]})!=len(config["algorithms"]) or not config["algorithms"]:
        raise ValueError("Selección vacía o duplicada")
    cases=[]
    for item in config["algorithms"]:
        key=item["id"]
        info=CATALOG[key]
        nominal=key in ("fibonacci-naive","hanoi-traversal")
        seeds=validated_seeds(item.get("seeds",[42] if nominal else default_seeds))
        batch=item.get("batch",1)
        if type(batch) is not int or not 1<=batch<=1048576:
            raise ValueError("Lote inválido")
        if nominal and seeds!=[42]:
            raise ValueError(f"{key} sólo usa semilla nominal 42")
        for n in sizes(item["sizes"]):
            for seed in seeds:
                cases.append(dict(id=f"{key}-n{n}-s{seed}",algorithm=key,n=n,seed=seed,
                    complexity=info["complexity"],profile=info["perfil"],minimum=info["minimum"],maximum=info["maximum"],
                    mode="SINGLE" if batch==1 else "BATCH",warmups=config["warmups"],measurements=config["measurements"],
                    batch=batch,forks=config["forks"],timeout_s=config["timeout_s"]))
    if len(cases)*config["forks"]>20000:
        raise ValueError("Divida la campaña en bloques menores")
    return cases


def java():
    return (Path(os.environ["ALGOPERFORMANCE_JDK_HOME"])/"bin/java.exe").resolve(strict=True)


def args_for(case):
    return [str(case[key]) for key in ("algorithm","n","seed","minimum","maximum","mode","warmups","measurements","batch")]+["0"]


def command(case,action,directory=None):
    prefix=[str(java()),"-Xint","-Xmx256m","--enable-native-access=ALL-UNNAMED"]
    if directory:
        prefix.append(f"-Dalgoperformance.affinity.evidence={directory}")
    return [*prefix,"-jar",str(JAR),action,*args_for(case)]


def fixture_signature(case,timeout=10):
    cmd=command(case,"validate")
    return subprocess.check_output(cmd,text=True,timeout=timeout).strip().rsplit(":",1)[-1]


def expected(case,timeout=30):
    lines=subprocess.check_output(command(case,"expected"),text=True,timeout=timeout).splitlines()
    return lines[0],[tuple(map(int,line.split(","))) for line in lines[1:]]


def parse(log,case,expect,directory):
    pid=AFFINITY.findall(log)
    if len(pid)!=1 or AFFINITY.findall((directory/f"affinity-{pid[0]}.txt").read_text())!=pid:
        raise ValueError("Afinidad efectiva sin evidencia")
    original=[json.loads(line) for line in log.splitlines() if line.startswith("{")]
    if not original or original[0].get("event")!="fixture" or str(original[0]["pid"])!=pid[0] or original[0]["input_sha256"]!=expect[0]:
        raise ValueError("Entrada o JVM discrepantes")
    if not original[0]["jdk"].startswith("25."):
        raise ValueError("Versión Java discrepante")
    record=original[1:]
    schedule=[("warmup",i) for i in range(1,case["warmups"]+1)]+[
              ("measurement",i) for i in range(1,case["measurements"]+1)]
    if [(r["phase"],r["iteration"]) for r in record]!=schedule or len(expect[1])!=len(record):
        raise ValueError("Serie incompleta o duplicada")
    for item,(parameter,checksum,batch) in zip(record,expect[1]):
        elapsed=item["elapsed_ns"]
        if (item["event"]!="sample" or type(elapsed) is not int or elapsed<0 or
                item["operations"]!=batch or item["parameter"]!=parameter or item["checksum"]!=checksum or
                item["ns_per_operation"]!=elapsed/batch):
            raise ValueError("Resultado, tiempo o lote no conforme")
        item["validation"]="valid_resolution_zero" if elapsed==0 else "valid"
    return int(pid[0]),record


def ledger(path):
    connection=sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, case_id TEXT NOT NULL,
          fork INTEGER NOT NULL, status TEXT NOT NULL CHECK(status IN ('running','complete','incomplete')),
          location TEXT NOT NULL, code INTEGER, reason TEXT);
        CREATE TABLE IF NOT EXISTS completed(case_id TEXT NOT NULL, fork INTEGER NOT NULL,
          attempt TEXT NOT NULL UNIQUE REFERENCES attempts(id), sha TEXT NOT NULL, PRIMARY KEY(case_id, fork));
        CREATE UNIQUE INDEX IF NOT EXISTS one_running_fork ON attempts(case_id,fork) WHERE status='running';
        """)
        if connection.execute("PRAGMA quick_check").fetchone()!=("ok",):
            raise ValueError("Registro persistente corrupto")
        invalid=connection.execute("""
            SELECT 1 FROM attempts a LEFT JOIN completed c ON a.id=c.attempt
            WHERE (a.status='complete')!=(c.attempt IS NOT NULL)
               OR (c.attempt IS NOT NULL AND (a.case_id!=c.case_id OR a.fork!=c.fork OR a.code IS NOT 0))
            LIMIT 1
        """).fetchone()
        if invalid or connection.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Registro de completitud inconsistente")
    except BaseException:
        connection.close()
        raise
    return connection


def complete(db,case,fork):
    return db.execute("SELECT attempt,sha FROM completed WHERE case_id=? AND fork=?",(case,fork)).fetchone()


def register(db,case,fork,attempt,result,code=0):
    checksum=sha(result.read_bytes())
    if code!=0:
        raise ValueError("Un fork completo requiere código cero")
    with db:
        updated=db.execute(
            "UPDATE attempts SET status='complete',code=0,reason=NULL WHERE id=? AND case_id=? AND fork=? AND status='running'",
            (attempt,case,fork))
        if updated.rowcount!=1:
            raise ValueError("Transición de completitud inválida")
        db.execute("INSERT INTO completed VALUES(?,?,?,?)",
                   (case,fork,attempt,checksum))


def mark_incomplete(db,attempt,code,reason):
    with db:
        db.execute("UPDATE attempts SET status='incomplete',code=?,reason=? WHERE id=? AND status='running'",
                   (code,reason,attempt))


def recover_sealed(root,plan,db,checks):
    """Recupera sólo archivos validados que quedaron antes del commit SQLite."""
    by_id={case["id"]:case for case in plan["cases"]}
    for attempt,key,fork in db.execute("SELECT id,case_id,fork FROM attempts WHERE status='running'").fetchall():
        if complete(db,key,fork):
            raise ValueError("El intento pendiente colisiona con un fork completo")
        folder=root/"attempts"/attempt
        result=folder/"validated.json"
        if not result.is_file():
            mark_incomplete(db,attempt,None,"Interrupción antes de sellar el resultado")
            continue
        case=by_id[key]
        try:
            invocation=json.loads((folder/"attempt.json").read_bytes())
            raw=(folder/"supervisor.log").read_bytes()
            document=json.loads(result.read_bytes())
            pid,record=parse(raw.decode("utf-8",errors="replace"),case,checks[key],folder)
            if (invocation["case"]!=case or invocation["fork"]!=fork
                    or invocation["jar_sha256"]!=plan["jar_sha256"] or
                    document!={"pid":pid,"record":record,"raw_sha256":sha(raw),"exit_code":0}):
                raise ValueError("El sello no coincide con la evidencia")
        except (OSError,ValueError,KeyError,TypeError) as failure:
            mark_incomplete(db,attempt,None,f"Sello no recuperable: {failure}")
            continue
        register(db,key,fork,attempt,result)


ORIGINAL_FIELDS=("campaign","algorithm","complexity","n","seed","pid","fork","attempt","config_id",
                 "version","mode","profile","phase","iteration","operations","elapsed_ns","ns_per_operation",
                 "checksum","parameter","validation")
CONSOLIDATED_FIELDS=("algorithm","complexity","n","mode","operations","representative_ns","valid_measurements",
                     "sd_ns","median_ns","cv_pct","zero_measurements","seeds","forks")


def write_rows(path,records,fields):
    with path.open("x",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fields)
        writer.writeheader();writer.writerows(records)


def export(root,plan,db,stamp):
    original=[]
    aggregate=[]
    pending=[]
    completed=0
    expected_forks=sum(case["forks"] for case in plan["cases"])
    expected_measurements=sum(case["forks"]*case["measurements"] for case in plan["cases"])
    for case in plan["cases"]:
        group=[]
        missing=[]
        for fork in range(1,case["forks"]+1):
            item=complete(db,case["id"],fork)
            if item is None:
                missing.append(fork)
                continue
            completed+=1
            attempt,sha_expected=item
            src=root/"attempts"/attempt/"validated.json"
            if sha(src.read_bytes())!=sha_expected:
                raise ValueError(f"Resultado alterado: {attempt}")
            result=json.loads(src.read_bytes())
            raw_path=root/"attempts"/attempt/"supervisor.log"
            if sha(raw_path.read_bytes())!=result["raw_sha256"]:
                raise ValueError(f"Log original alterado: {attempt}")
            expected_schedule=[("warmup",index+1) for index in range(case["warmups"])]+[
                ("measurement",index+1) for index in range(case["measurements"])]
            if result.get("exit_code")!=0 or [(s["phase"],s["iteration"]) for s in result["record"]]!=expected_schedule:
                raise ValueError(f"Cobertura del sello discrepante: {attempt}")
            for sample in result["record"]:
                row=dict(campaign=plan["campaign"],algorithm=case["algorithm"],complexity=case["complexity"],
                         n=case["n"],seed=case["seed"],pid=result["pid"],fork=fork,attempt=attempt,
                         config_id=plan["config_sha256"],version=VERSION,mode=case["mode"],
                         profile=case["profile"],**{k:v for k,v in sample.items() if k!="event"})
                original.append(row)
                if sample["phase"]=="measurement":
                    group.append(row)
        aggregate.extend(group)
        if missing:
            pending.append({"case":case["id"],"pending_forks":missing})
    state="partial" if pending else "complete"
    label=f"{state}-{stamp}"
    originals=root/f"original-{label}.csv"
    consolidated=root/f"consolidated-{label}.csv"
    write_rows(originals,original,ORIGINAL_FIELDS)
    write_rows(consolidated,consolidate(aggregate),CONSOLIDATED_FIELDS)
    manifest=dict(campaign=plan["campaign"],version=plan["version"],status=state,
                  purpose=plan.get("purpose","technical_review"),classification="candidate_evidence",
                  configuration_sha256=plan["config_sha256"],artifact_sha256=plan["jar_sha256"],
                  expected_forks=expected_forks,completed_forks=completed,expected_measurements=expected_measurements,
                  valid_measurements=len(aggregate),warmup_intervals=len(original)-len(aggregate),pending_cases=pending,
                  files={path.name:sha(path.read_bytes()) for path in (originals,consolidated)})
    dump(root/f"export-{label}.json",manifest)
    return manifest


def consolidate(rows):
    groups={}
    for row in rows:
        key=(row["algorithm"],row["complexity"],row["n"],row["mode"],row["operations"])
        groups.setdefault(key,[]).append(row)
    output=[]
    for key,group in groups.items():
        by_seed={}
        scores=[]
        for row in group:
            value=row["ns_per_operation"]
            scores.append(value)
            by_seed.setdefault(row["seed"],{}).setdefault(row["fork"],[]).append(value)
        mean=statistics.mean(statistics.mean(statistics.mean(fork) for fork in forks.values())
                             for forks in by_seed.values())
        sd=statistics.stdev(scores) if len(scores)>1 else None
        flat_mean=statistics.mean(scores)
        output.append(dict(zip(("algorithm","complexity","n","mode","operations"),key),
                           representative_ns=mean,valid_measurements=len(scores),sd_ns=sd,
                           median_ns=statistics.median(scores),
                           cv_pct=100*sd/flat_mean if sd is not None and flat_mean>0 else None,
                           zero_measurements=scores.count(0),seeds=len(by_seed),
                           forks=sum(map(len,by_seed.values()))))
    return output


class Deadline:
    def __init__(self,seconds,phase):
        self.seconds=seconds
        self.phase=phase
        self.start=time.monotonic()

    def remaining(self,case_limit=None):
        remaining=self.seconds-(time.monotonic()-self.start)
        if remaining<=0:
            raise TimeoutError(f"Presupuesto de {self.phase} agotado")
        return min(remaining,case_limit) if case_limit is not None else remaining


@contextmanager
def measured_stage(events,name,limit,started=None):
    start=time.monotonic() if started is None else started
    status="failed"
    try:
        yield
        status="finished"
    finally:
        append(events,"stage_duration",stage=name,limit_s=limit,duration_s=time.monotonic()-start,status=status)


def run(config_path,action):
    preparation_started=time.monotonic()
    config_raw=config_path.read_bytes()
    config=json.loads(config_raw)
    budgets=budget_config(config)
    preparation=Deadline(budgets["preparation_timeout_s"],"preparación")
    cases=plan_config(config)
    version=subprocess.check_output([str(java()),"-Xint","-version"],text=True,stderr=subprocess.STDOUT,
                                    timeout=preparation.remaining(budgets["preparation_case_timeout_s"]))
    if "25." not in version or "interpreted mode" not in version:
        raise ValueError("Se necesita Java 25 en modo interpretado")
    plan=dict(campaign=config["campaign"],config_sha256=sha(config_raw),jar_sha256=sha(JAR.read_bytes()),
              version=VERSION,jdk=version,flags=["-Xint","-Xmx256m"],cases=cases,budgets=budgets,
              purpose=config.get("purpose","technical_review"))
    if action=="plan":
        for case in cases:
            case["fixture_sha256"]=fixture_signature(case,preparation.remaining(budgets["preparation_case_timeout_s"]))
        plan["preparation_duration_s"]=time.monotonic()-preparation_started
        print(json.dumps(plan,ensure_ascii=False,indent=2))
        return

    root=OUT/config["campaign"]
    root.mkdir(parents=False,exist_ok=action!="run")
    lock=root/"active.lock"
    with lock.open("x",encoding="utf-8") as mark:
        mark.write(f"{os.getpid()}\n")
    db=None
    try:
        config_out=root/"configuration.json"
        if action=="run":
            dump(config_out,plan)
        elif plan!=json.loads(config_out.read_bytes()):
            raise ValueError("Configuración o artefacto diferente del registrado")
        db=ledger(root/"ledger.sqlite")
        if action=="export":
            print(export(root,plan,db,uuid.uuid4().hex[:8]))
            return
        stamp=uuid.uuid4().hex[:8]
        events=root/"events.jsonl"
        with measured_stage(events,"preparation",preparation.seconds,preparation_started):
            if core_types().get(0)!=1:
                raise ValueError("CPU 0 no confirmado como P-core")
            valid={(case["id"],fork) for case in cases for fork in range(1,case["forks"]+1)}
            if set(db.execute("select case_id,fork from completed"))-valid:
                raise ValueError("Registro ajeno a la configuración")
            signatures={}
            for case in cases:
                if any(not complete(db,case["id"],fork) for fork in range(1,case["forks"]+1)):
                    signatures[case["id"]]=fixture_signature(case,preparation.remaining(budgets["preparation_case_timeout_s"]))
            preparation.remaining()
        with measured_stage(events,"functional_verification",budgets["verification_timeout_s"]):
            verification=Deadline(budgets["verification_timeout_s"],"verificación funcional")
            checks={}
            for case in cases:
                key=case["id"]
                if key in signatures:
                    proof=expected(case,verification.remaining(budgets["verification_case_timeout_s"]))
                    if proof[0]!=signatures[key]:
                        raise ValueError("Referencia y fixture no coinciden")
                    checks[key]=proof
            if action=="resume":
                recover_sealed(root,plan,db,checks)
            verification.remaining()
        append(events,"prepared",attempt=stamp,processes_pending=sum(
            not complete(db,case["id"],fork) for case in cases for fork in range(1,case["forks"]+1)))
        with measured_stage(events,"measurement",config["global_timeout_s"]), PowerMonitor() as power,suspend_notifications() as signals,stay_awake(events):
            started=clocks()
            end=time.monotonic()+config["global_timeout_s"]
            def check():
                check_sleep(started,clocks())
                state=power.check()
                if signals or not state["ac_online"] or state["power_scheme"].lower()!=BALANCED:
                    raise RuntimeError("Entorno experimental alterado")
                return state
            append(events,"campaign_started",environment=check(),affinity="0x1",unmonitored_activity=True)
            for case in cases:
                for fork in range(1,case["forks"]+1):
                    if complete(db,case["id"],fork):
                        continue
                    if (root/"STOP").exists():
                        append(events,"safe_stop",case=case["id"],fork=fork)
                        return
                    check()
                    first=time.monotonic()
                    timeout=min(case["timeout_s"],end-first)
                    if timeout<=0:
                        raise TimeoutError("Presupuesto global agotado")
                    attempt=uuid.uuid4().hex
                    folder=root/"attempts"/attempt
                    folder.mkdir(parents=True,exist_ok=False)
                    invocation=command(case,"measure",folder)
                    dump(folder/"attempt.json",dict(case=case,fork=fork,command=invocation,
                                                    jar_sha256=plan["jar_sha256"]))
                    with db:
                        db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?,?)",
                                   (attempt,case["id"],fork,"running",str(folder),None,None))
                    original=folder/"supervisor.log"
                    code=None
                    try:
                        with original.open("x",encoding="utf-8") as stream:
                            code=supervise(invocation,0,timeout,"p",check=check,output=stream)
                        if code:
                            raise RuntimeError(f"Salida JVM {code}")
                        pid,record=parse(original.read_text(encoding="utf-8",errors="replace"),case,checks[case["id"]],folder)
                        result=folder/"validated.json"
                        dump(result,dict(pid=pid,record=record,raw_sha256=sha(original.read_bytes()),exit_code=0))
                        register(db,case["id"],fork,attempt,result,code)
                    except BaseException as failure:
                        sealed=(folder/"validated.json").is_file()
                        if not sealed:
                            mark_incomplete(db,attempt,code,repr(failure))
                        append(events,"fork_pending_reconcile" if sealed else "fork_incomplete",
                               case=case["id"],fork=fork,attempt=attempt,error=repr(failure))
                        raise
                    append(events,"fork_completed",case=case["id"],fork=fork,pid=pid,attempt=attempt,
                           duration_s=time.monotonic()-first)
            append(events,"campaign_completed",environment=check())
        print(export(root,plan,db,stamp))
    finally:
        if db is not None:
            db.close()
        lock.unlink()


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("action",choices=("plan","run","resume","export"))
    cli.add_argument("config",type=Path)
    args=cli.parse_args()
    run(args.config,args.action)


if __name__=="__main__":
    main()
