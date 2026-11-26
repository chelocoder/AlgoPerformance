import json, subprocess
from pathlib import Path
from run import CATALOG, OUT, expected, fixture_signature, plan_config
base=OUT
config=json.loads(Path("rc/examples/demo-expertos.json").read_bytes())
config.update(campaign="functional-catalog-only",forks=1,warmups=0,measurements=2)
config["algorithms"]=[dict(id=key,sizes=dict(values=[8])) for key in CATALOG]
items=[]
for row in plan_config(config):
    first,values=expected(row)
    second,repeated=expected(row)
    assert first==second==fixture_signature(row) and values==repeated and len(values)==2
    items.append(dict(algorithm=row["algorithm"],n=row["n"],seed=row["seed"],fixture_sha256=first,
                      expected=values,classification="functional-no-clock"))
(base/"catalog-functional.json").write_text(json.dumps(items,indent=2),encoding="utf-8")
print(f"{len(items)} núcleos con resultados funcionales reproducibles bajo Java 25 -Xint; no se midieron.")
