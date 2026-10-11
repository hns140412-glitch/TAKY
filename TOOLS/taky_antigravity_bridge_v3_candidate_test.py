#!/usr/bin/env python3
"""TAKY Bridge V3 isolated regression; no provider inference calls."""
import copy, importlib.util, json, tempfile
from pathlib import Path
from types import SimpleNamespace

code=Path(__file__).with_name("taky_antigravity_bridge_v3_candidate.py")
spec=importlib.util.spec_from_file_location("bridge_v3",code)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def pack(v):
    v["payload_sha256"]=b.digest(b.canonical({k:x for k,x in v.items() if k!="payload_sha256"}))
    return v
with tempfile.TemporaryDirectory(prefix="TAKY_BRIDGE_V3_TEST_") as tmp:
    b.MAILBOX=Path(tmp)/"mailbox"
    def stage(actor):
        return b.stage(SimpleNamespace(actor=actor,project="TAKY2",intent="Verify protected TAKY bridge"))
    reqid=stage("CAPABILITY_ATTEST")["task_id"]
    inp=b.load(b.MAILBOX/"requests"/(reqid+".json"))
    assert b.validate(inp) is None
    result=b.process(inp)
    assert result["status"]=="PASS"
    assert result["data"]["skills"]["CLAUDE"]["skills_available_on_disk"]>=11
    assert result["data"]["skills"]["CODEX"]["skills_available_on_disk"]>=11
    bad=copy.deepcopy(inp);bad["intent"]="changed but not rehashed"
    assert b.process(bad)["error"]=="REQUEST_HASH_MISMATCH"
    moved=copy.deepcopy(inp);moved["repo_state"]["head"]="bad-head";pack(moved)
    assert b.process(moved)["error"]=="HEAD_CHANGED_RESTAGE"
    branch=copy.deepcopy(inp);branch["repo_state"]["branch"]="other";pack(branch)
    assert b.process(branch)["error"]=="BRANCH_CHANGED_RESTAGE"
    context=copy.deepcopy(inp);context["context"]["sha256"]="bad-context";pack(context)
    assert b.process(context)["error"]=="CONTEXT_CHANGED_RESTAGE"
    assert b.worker_once()["new_receipts"]==1
    assert b.worker_once()["new_receipts"]==0
    assert b.poll(reqid)["status"]=="PASS"
    receiptfile=b.MAILBOX/"responses"/(reqid+".json")
    original=receiptfile.read_bytes()
    modified=json.loads(original);modified["status"]="FORGED_PASS"
    receiptfile.write_text(json.dumps(modified),encoding="utf-8")
    assert b.poll(reqid)["error"]=="RECEIPT_INTEGRITY_MISMATCH"
    receiptfile.write_bytes(original)
    actor=stage("CLAUDE")["task_id"]
    assert b.worker_once()["new_receipts"]==1
    answer=b.poll(actor)
    assert answer["status"]=="PREPARED_NOT_EXECUTED" and not answer["provider_invoked"]
    assert answer["data"]["session_binding"]=="NATIVE_PANEL_UNVERIFIED"
print("TAKY_BRIDGE_V3_REGRESSION_PASS 10_CASES_NO_MODEL_CALLS")
