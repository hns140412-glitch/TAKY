#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from data_index_outcome_utility import aggregate_events
from data_index_search import materialize_legacy_relations, normalize_record, search

events=[
 {"stage":"OUTCOME","source_ref":"INDEX:SRC-A","payload":{"verified_target":True,"outcome":1}},
 {"stage":"OUTCOME","source_ref":"INDEX:SRC-A","payload":{"verified_target":True,"outcome":1}},
 {"stage":"OUTCOME","source_ref":"INDEX:SRC-B","payload":{"verified_target":True,"outcome":0}},
 {"stage":"GROWTH","source_ref":"INDEX:SRC-A","payload":{"verified_reuse":True}},
 {"stage":"OUTCOME","source_ref":"LEARNING_RECEIPT:PRIVATE","payload":{"verified_target":True,"outcome":1}},
]
u=aggregate_events(events)
assert u["SRC-A"]["verified_success"]==2
assert u["SRC-A"]["verified_reuse"]==1
assert u["SRC-B"]["verified_failure"]==1
assert "PRIVATE" not in u

records=materialize_legacy_relations([normalize_record(x) for x in [
 {"source_id":"SRC-A","title":"같은 제목","current_relation":"CURRENT_INDEX_ENTRY"},
 {"source_id":"SRC-B","title":"같은 제목","current_relation":"CURRENT_INDEX_ENTRY"},
]])
r=search(records,"같은 제목",relation_depth=0,outcome_utility_by_source=u)
assert r["results"][0]["source_id"]=="SRC-A"
assert r["results"][0]["ranking"]["outcome_utility"]>r["results"][1]["ranking"]["outcome_utility"]

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    lineage=td/"grow.jsonl"
    lineage.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in events)+"\n",encoding="utf-8")
    sidecar=td/"utility.json"
    p=subprocess.run([sys.executable,str(ROOT/"data_index_outcome_utility.py"),"--lineage",str(lineage),"--output",str(sidecar)],capture_output=True,text=True)
    assert p.returncode==0,(p.stdout,p.stderr)
    s=json.loads(sidecar.read_text(encoding="utf-8"))
    assert s["schema"]=="TAKY_DATA_INDEX_OUTCOME_UTILITY_V1"
    assert s["authoritative"] is False
    assert s["by_source_id"]["SRC-A"]["verified_success"]==2

print("data_index_outcome_utility: PASS")
