#!/usr/bin/env python3
"""Attest an immutable pre-signature CLI E2E receipt against signed V3 task.
Never overwrites the original. No inference call.
"""
import argparse, hashlib, json, pathlib
from datetime import datetime, timezone
import taky_antigravity_bridge_v3_candidate as bridge
import TAKY_CLI_DETACHED_E2E_CANDIDATE as cli

def sha(b):return hashlib.sha256(b).hexdigest()
def attest(taskid):
    original=cli.OUT/(taskid+".json")
    attestation=cli.OUT/(taskid+".attestation.json")
    if not original.is_file():raise RuntimeError("ORIGINAL_RECEIPT_MISSING")
    if attestation.exists():raise RuntimeError("ATTESTATION_EXISTS_NO_OVERWRITE")
    raw=original.read_bytes()
    legacy=json.loads(raw)
    request=bridge.load(bridge.MAILBOX/"requests"/(taskid+".json"))
    if bridge.validate(request) is not None:raise RuntimeError("REQUEST_SIGNATURE_INVALID")
    worker=bridge.poll(taskid)
    if worker["status"]!="PREPARED_NOT_EXECUTED" or worker["request_hash"]!=request["payload_sha256"]:
        raise RuntimeError("WORKER_RECEIPT_INVALID")
    if (legacy.get("task_id")!=taskid or legacy.get("request_sha256")!=request["payload_sha256"]
        or legacy.get("session_mode")!="NEW_DETACHED_CLI_NOT_IDE_PANEL"
        or legacy.get("status")!="EXECUTED_E2E_REPLY_VERIFIED"
        or legacy.get("agent")!=request["actor"] or legacy.get("exit_code")!=0):
        raise RuntimeError("CLAUDE_EXECUTION_RECEIPT_INVALID")
    expected=legacy["expected_token"]
    if sha(expected.encode())!=legacy["response_sha256"] or not legacy["verified_expected_reply"]:
        raise RuntimeError("CLAUDE_EXACT_RESPONSE_HASH_NOT_MATCHED")
    repo=bridge.ALLOWED[request["project"]]
    final=bridge.snap(repo)
    before=request["repo_state"]
    postcondition=(final==before)
    answer={"schema":"TAKY_CLI_E2E_ATTESTATION_V1","task_id":taskid,
        "validated_at":datetime.now(timezone.utc).isoformat(),
        "source_receipt_sha256":sha(raw),"request_sha256":request["payload_sha256"],
        "response_sha256":legacy["response_sha256"],"agent":legacy["agent"],
        "status":"E2E_RESPONSE_AND_REQUEST_BOUND_PASS",
        "repo_postcondition_unchanged":postcondition,
        "repo_postcondition":"PASS" if postcondition else "HOLD_STATE_CHANGED_SINCE_STAGE",
        "agent_session_native_panel":False,"extra_model_calls":0,"cost_route":"SUBSCRIPTION_CLI_ENV_KEYS_REMOVED",
        "raw_receipt_unchanged":True}
    bridge.seal_receipt(answer)
    bridge.write_new(attestation,answer)
    print(json.dumps({"status":answer["status"],"postcondition":answer["repo_postcondition"],
        "attestation":str(attestation),"source_sha256":answer["source_receipt_sha256"]},ensure_ascii=False))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",required=True)
    attest(ap.parse_args().task_id)
