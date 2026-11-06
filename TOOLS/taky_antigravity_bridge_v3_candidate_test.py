#!/usr/bin/env python3
"""TAKY Bridge V3 isolated regression; no provider inference calls."""
import copy, importlib.util, json, tempfile
from pathlib import Path
from types import SimpleNamespace

code=Path(__file__).with_name("taky_antigravity_bridge_v3_candidate.py")
spec=importlib.util.spec_from_file_location("bridge_v3",code)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def pack(v):
    v["payload_sha256"]=b.digest(b.canonical({k:x for k,x in v.items() if k not in ("payload_sha256","payload_mac")}))
    v["payload_mac"]=b.mac(v["payload_sha256"])
    return v
with tempfile.TemporaryDirectory(prefix="TAKY_BRIDGE_V3_TEST_") as tmp:
    b.MAILBOX=Path(tmp)/"mailbox"
    b.HOST_KEY=Path(tmp)/"local_identity.bin"
    b.WORKER_LOCK=Path(tmp)/"worker.lock"
    def stage(actor):
        return b.stage(SimpleNamespace(actor=actor,project="TAKY2",intent="Verify protected TAKY bridge"))
    reqid=stage("CAPABILITY_ATTEST")["task_id"]
    inp=b.load(b.MAILBOX/"requests"/(reqid+".json"))
    assert b.validate(inp) is None
    result=b.process(inp)
    assert result["status"]=="PASS"
    assert result["data"]["skills"]["CLAUDE"]["skills_available_on_disk"]>=11
    assert result["data"]["skills"]["CODEX"]["skills_available_on_disk"]>=11
    assert result["data"]["skills"]["CLAUDE"]["project_mcp"]["state"]=="PROJECT_MCP_CONFIG_PRESENT_RUNTIME_UNVERIFIED"
    assert result["data"]["skills"]["CLAUDE"]["project_mcp"]["names"]==["chrome-devtools","playwright"]
    assert result["data"]["skills"]["CLAUDE"]["mcp_runtime_attested"] is False
    assert result["data"]["skills"]["CLAUDE"]["project_instructions_present"] is True
    assert result["data"]["skills"]["CODEX"]["project_instructions_present"] is True
    assert "node_repl" in result["data"]["skills"]["CODEX"]["project_mcp"]["names"]
    assert result["data"]["skills"]["CODEX"]["mcp_runtime_attested"] is False
    bad=copy.deepcopy(inp);bad["intent"]="changed but not rehashed"
    assert b.process(bad)["error"]=="REQUEST_HASH_MISMATCH"
    forged=copy.deepcopy(inp);forged["intent"]="changed with new SHA but old MAC"
    forged["payload_sha256"]=b.digest(b.canonical({k:x for k,x in forged.items() if k not in ("payload_sha256","payload_mac")}))
    assert b.process(forged)["error"]=="REQUEST_ORIGIN_NOT_ATTESTED"
    host=copy.deepcopy(inp);host["host_identity"]="wrong-machine";pack(host)
    assert b.process(host)["error"]=="WRONG_TARGET_PC"
    moved=copy.deepcopy(inp);moved["repo_state"]["head"]="bad-head";pack(moved)
    assert b.process(moved)["error"]=="HEAD_CHANGED_RESTAGE"
    branch=copy.deepcopy(inp);branch["repo_state"]["branch"]="other";pack(branch)
    assert b.process(branch)["error"]=="BRANCH_CHANGED_RESTAGE"
    context=copy.deepcopy(inp);context["context"]["sha256"]="bad-context";pack(context)
    assert b.process(context)["error"]=="CONTEXT_CHANGED_RESTAGE"
    changed=copy.deepcopy(inp);changed["repo_state"]["worktree_status_sha256"]="alternate-same-file-count";pack(changed)
    assert b.process(changed)["error"]=="WORKTREE_CHANGED_RESTAGE"
    b.WORKER_LOCK.parent.mkdir(parents=True,exist_ok=True)
    b.WORKER_LOCK.write_text("another worker",encoding="utf-8")
    assert b.worker_once()["status"]=="HOLD_WORKER_ALREADY_RUNNING"
    b.WORKER_LOCK.unlink()
    assert b.worker_once()["new_receipts"]==1
    assert b.worker_once()["new_receipts"]==0
    assert b.poll(reqid)["status"]=="PASS"
    receiptfile=b.MAILBOX/"responses"/(reqid+".json")
    original=receiptfile.read_bytes()
    modified=json.loads(original);modified["status"]="FORGED_PASS"
    receiptfile.write_text(json.dumps(modified),encoding="utf-8")
    assert b.poll(reqid)["error"]=="RECEIPT_INTEGRITY_MISMATCH"
    receiptfile.write_bytes(original)
    modified=json.loads(original);modified["status"]="FORGED_PASS"
    modified["receipt_sha256"]=b.digest(b.canonical({k:x for k,x in modified.items() if k not in ("receipt_sha256","receipt_mac")}))
    receiptfile.write_text(json.dumps(modified),encoding="utf-8")
    assert b.poll(reqid)["error"]=="RECEIPT_INTEGRITY_MISMATCH"
    receiptfile.write_bytes(original)
    actor=stage("CLAUDE")["task_id"]
    assert b.worker_once()["new_receipts"]==1
    answer=b.poll(actor)
    assert answer["status"]=="PREPARED_NOT_EXECUTED" and not answer["provider_invoked"]
    assert answer["data"]["session_binding"]=="NATIVE_PANEL_UNVERIFIED"
print("TAKY_BRIDGE_V3_REGRESSION_PASS 15_CASES_NO_MODEL_CALLS")
