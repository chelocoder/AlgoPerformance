import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from run import (CATALOG, VERSION, Deadline, budget_config, complete, consolidate, dump, export, ledger,
                 parse, plan_config, recover_sealed, register, sha, sizes)

BASE={"campaign":"synthetic-only","forks":2,"warmups":0,"measurements":1,"timeout_s":12,
      "global_timeout_s":120,"seeds":[42],"algorithms":[{"id":"array-index-read","sizes":{"values":[64]},"batch":1}]}


class CandidateTest(unittest.TestCase):
    def test_progressions_and_uniqueness(self):
        self.assertEqual(sizes(dict(start=10,step=5,count=3)),[10,15,20])
        self.assertEqual(sizes(dict(start=10,ratio=2,count=3)),[10,20,40])
        self.assertEqual(sizes(dict(values=[3,1])),[3,1])
        for spec in (dict(values=[1,1]),dict(start=1,step=0,count=2),dict(start=1,ratio=1,count=2)):
            with self.assertRaises(ValueError):
                sizes(spec)

    def test_catalog_and_selection(self):
        self.assertEqual(len(CATALOG),20)
        row,=plan_config(BASE)
        self.assertEqual((row["n"],row["seed"],row["mode"]),(64,42,"SINGLE"))
        with self.assertRaises(ValueError):
            plan_config(dict(BASE,seeds=[42,42]))

    def test_hierarchical_statistics_and_zeros(self):
        base=dict(algorithm="a",complexity="Θ(1)",n=4,mode="SINGLE",operations=1)
        rows=[dict(base,seed=seed,fork=fork,ns_per_operation=ns) for seed,fork,ns in
              [(42,1,0),(42,1,4),(42,2,10),(43,1,6)]]
        item,=consolidate(rows)
        self.assertEqual((item["representative_ns"],item["valid_measurements"],item["median_ns"],
                          item["zero_measurements"]),(6,4,5,1))

    def synthetic(self,folder):
        case,=plan_config(BASE)
        affinity="Affinity verified before warmup: pid=10 mask=0x1"
        (folder/"affinity-10.txt").write_text(affinity)
        fixture=dict(event="fixture",pid=10,input_sha256="synthetic",jdk="25.0.5.1")
        sample=dict(event="sample",phase="measurement",iteration=1,operations=1,elapsed_ns=0,
                    ns_per_operation=0,checksum=5,parameter=2)
        log="\n".join((affinity,json.dumps(fixture),json.dumps(sample)))
        proof=("synthetic",[(2,5,1)])
        return case,log,proof

    def test_validation_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            case,log,proof=self.synthetic(folder)
            self.assertEqual(parse(log,case,proof,folder)[1][0]["validation"],"valid_resolution_zero")
            for bad in (log.replace('"checksum": 5','"checksum": 8'),log+"\n"+log.splitlines()[-1]):
                with self.assertRaises(ValueError):parse(bad,case,proof,folder)

    def test_interruption_and_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            db=ledger(root/"test.sqlite")
            try:
                folder=root/"attempts"/"synthetic"
                folder.mkdir(parents=True)
                case,log,proof=self.synthetic(folder)
                (folder/"supervisor.log").write_bytes(log.encode())
                (folder/"attempt.json").write_text(json.dumps(dict(case=case,fork=1,jar_sha256="example")))
                pid,record=parse(log,case,proof,folder)
                sealed=folder/"validated.json"
                sealed.write_text(json.dumps(dict(pid=pid,record=record,raw_sha256=sha(log.encode()),exit_code=0)))
                with db:
                    db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?,?)",
                               ("synthetic",case["id"],1,"running",str(folder),None,None))
                recover_sealed(root,dict(cases=[case],jar_sha256="example"),db,{case["id"]:proof})
                self.assertEqual(complete(db,case["id"],1)[0],"synthetic")
                self.assertIsNone(complete(db,case["id"],2))
                with self.assertRaises(ValueError):
                    register(db,case["id"],1,"synthetic",sealed)
            finally:
                db.close()


    def test_per_algorithm_seed_overrides_and_nominal_seed(self):
        selected=[dict(BASE["algorithms"][0]),
                  dict(id="array-sum",sizes={"values":[64]},seeds=[7,9]),
                  dict(id="fibonacci-naive",sizes={"values":[10]})]
        plan=plan_config(dict(BASE,seeds=[3,5],algorithms=selected))
        self.assertEqual([case["seed"] for case in plan],[3,5,7,9,42])
        selected[-1]["seeds"]=[3]
        with self.assertRaises(ValueError):
            plan_config(dict(BASE,algorithms=selected))

    def test_budget_boundaries(self):
        budget=budget_config(dict(BASE,preparation_timeout_s=5,verification_timeout_s=11))
        self.assertEqual((budget["preparation_timeout_s"],budget["verification_timeout_s"]),(5,11))
        with self.assertRaises(ValueError):
            budget_config(dict(BASE,verification_timeout_s=0))
        with patch("run.time.monotonic",side_effect=[0,2,5]):
            deadline=Deadline(5,"synthetic")
            self.assertEqual(deadline.remaining(8),3)
            with self.assertRaises(TimeoutError):
                deadline.remaining()

    def test_atomic_interruption_before_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            result=folder/"validated.json"
            with patch.object(Path,"replace",side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    dump(result,{"scientific":False})
            self.assertFalse(result.exists())
            self.assertEqual(len(list(folder.glob("*.tmp"))),1)
            dump(result,{"scientific":False})
            with self.assertRaises(FileExistsError):
                dump(result,{"scientific":True})
            self.assertEqual(json.loads(result.read_bytes()),{"scientific":False})

    def test_missing_or_truncated_seal_leaves_fork_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            db=ledger(root/"test.sqlite")
            try:
                case,=plan_config(BASE)
                for attempt in ("no-seal","broken"):
                    folder=root/"attempts"/attempt
                    folder.mkdir(parents=True)
                    case,log,proof=self.synthetic(folder)
                    (folder/"supervisor.log").write_text(log)
                    if attempt=="broken":
                        (folder/"attempt.json").write_text("{}")
                        (folder/"validated.json").write_text("{")
                    with db:
                        db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?,?)",
                                   (attempt,case["id"],1,"running",str(folder),None,None))
                    recover_sealed(root,dict(cases=[case],jar_sha256="x"),db,{case["id"]:proof})
                    self.assertIsNone(complete(db,case["id"],1))
                    self.assertTrue((folder/"supervisor.log").is_file())
                self.assertEqual(db.execute("SELECT status FROM attempts").fetchall(),[("incomplete",),("incomplete",)])
            finally:
                db.close()

    def test_transaction_rollback_and_pending_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            db=ledger(root/"test.sqlite")
            try:
                folder=root/"attempts"/"first"
                folder.mkdir(parents=True)
                case,log,proof=self.synthetic(folder)
                (folder/"supervisor.log").write_bytes(log.encode())
                pid,record=parse(log,case,proof,folder)
                sealed=folder/"validated.json"
                dump(sealed,dict(pid=pid,record=record,raw_sha256=sha(log.encode()),exit_code=0))
                with db:
                    db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?,?)",
                               ("first",case["id"],1,"running",str(folder),None,None))
                    db.execute("CREATE TRIGGER synthetic_failure BEFORE INSERT ON completed "
                               "BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
                with self.assertRaises(sqlite3.IntegrityError):
                    register(db,case["id"],1,"first",sealed)
                self.assertEqual(db.execute("SELECT status FROM attempts").fetchone(),("running",))
                self.assertIsNone(complete(db,case["id"],1))
                with db:
                    db.execute("DROP TRIGGER synthetic_failure")
                register(db,case["id"],1,"first",sealed)
                plan=dict(campaign="synthetic-only",version=VERSION,config_sha256="example",jar_sha256="example",cases=[case])
                report=export(root,plan,db,"test")
                self.assertEqual((report["status"],report["completed_forks"],report["valid_measurements"]),
                                 ("partial",1,1))
                self.assertEqual(report["pending_cases"],[dict(case=case["id"],pending_forks=[2])])
                for filename,checksum in report["files"].items():
                    self.assertEqual(sha((root/filename).read_bytes()),checksum)
            finally:
                db.close()
