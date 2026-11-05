"""Reason Network same-machine bounded handoff for TAKY's existing local work.

Reason is transport only, never approval. Only CLN-002 and INT-001 read-only
diagnostics from the canonical registered portfolio are executable.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

TAKY=Path(r"D:\Git PWA\TAKY")
TOOLS=TAKY/"TOOLS"
WORKBENCH=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
RECEIPTS=WORKBENCH/"01_BACKLOG_AND_ADOPTION/80_EVIDENCE"
REASON=Path.home()/"AppData/Local/TAKY/reason_network_evaluation/bin/reason-network.exe"
sys.path.insert(0,str(TOOLS))
from TAKY_ORCHESTRATION_ADVANCE import evidence_signature, run_checks, read_json, DEFAULT_BOARD, LOCAL_EXECUTORS

SCHEMA="TAKY_REASON_GUIDED_WORK_V1"
ALLOWED=frozenset(LOCAL_EXECUTORS)
SESSION="taky-guided-work"

def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def classify_team_output(output):
    """Agent readiness is based on agent TYPE, not a CLI session NAME.

    A queued/busy shell named 'codex-review-queue' is not a live Codex agent.
    Reason is transport only and must never auto-authorize model execution.
    """
    found={"claude":0,"codex":0,"gemini":0,"cli":0}
    for line in output.splitlines():
        m=re.match(r"^\s{2}[^\s]+\s+(claude|codex|gemini|cli)\s+",line,re.I)
        if m:
            found[m.group(1).lower()]+=1
    return {
        "schema":"TAKY_REASON_EXECUTOR_CAPABILITY_V1",
        "reason_team_observed":output.startswith("team "),
        "session_types":found,
        "claude_code_live_session":found["claude"]>0,
        "codex_live_session":found["codex"]>0,
        "claude_codex_bilateral_route_ready":found["claude"]>0 and found["codex"]>0,
        "cli_queues_are_not_model_executors":True,
        "provider_call_performed":False,
        "model_execution_authorized":False,
        "approval_granted":False,
        "scope":"LIVE_SESSION_OBSERVATION_ONLY_NOT_FULL_ORCHESTRATION"}

def reason_capability():
    """Bounded local who-readback; no login, setup, network join, or APIs."""
    if not REASON.is_file():
        return {"schema":"TAKY_REASON_EXECUTOR_CAPABILITY_V1",
                "state":"HOLD_REASON_EXECUTABLE_MISSING",
                "model_execution_authorized":False}
    try:
        done=subprocess.run([str(REASON),"who"],
            cwd=Path.home(),capture_output=True,text=True,encoding="utf-8",
            errors="replace",timeout=10,check=False)
        if done.returncode!=0 or len(done.stdout)>16000:
            raise RuntimeError("REASON_WHO_NOT_VALID")
        value=classify_team_output(done.stdout)
        value["state"]=("LIVE_DUAL_AGENT_SESSIONS_VISIBLE_NOT_OWNERSHIP_VERIFIED"
            if value["claude_codex_bilateral_route_ready"]
            else "HOLD_LIVE_EXECUTOR_SESSIONS_NOT_VISIBLE")
        return value
    except (OSError,RuntimeError,subprocess.TimeoutExpired):
        return {"schema":"TAKY_REASON_EXECUTOR_CAPABILITY_V1",
                "state":"HOLD_REASON_WHO_UNAVAILABLE",
                "model_execution_authorized":False}

def prepare(task_id):
    if task_id not in ALLOWED:raise ValueError("REASON_WORK_ID_NOT_ALLOWLISTED")
    board=read_json(DEFAULT_BOARD)
    task=next((x for x in board["tasks"] if x.get("id")==task_id),None)
    if not task or task.get("status") in ("BLOCKED","REJECTED","VERIFIED") or task.get("approval_required") is True:
        raise ValueError("CANONICAL_WORK_NOT_ACTIVE")
    source,digest=evidence_signature(board,task_id)
    return {"schema":SCHEMA,"task_id":task_id,
            "task_contract_sha256":source["task_sha256"],
            "evidence_signature":digest,
            "role":"LOCAL_READ_ONLY_DIAGNOSTIC",
            "index_owner_approval":False,"auto_done":False,
            "model_calls_authorized":False,"external_actions_authorized":False}

def decode(out):
    match=re.search(r'<reason-message from="([^"]+)" agent="[^"]*" id="([A-Z0-9]+)">\s*(.*?)\s*</reason-message>',out,re.S)
    if not match:raise ValueError("NO_VERIFIED_REASON_MESSAGE_RECEIVED")
    sender,message_id,body=match.groups()
    if not sender.startswith("taky-local/") or len(message_id)>40:
        raise ValueError("REASON_LOCAL_SENDER_OR_MESSAGE_INVALID")
    message=json.loads(body)
    if not isinstance(message,dict) or set(message)!=set(prepare_keys):
        raise ValueError("REASON_WORK_SCHEMA_OR_EXTRA_ACTION_INVALID")
    if message.get("schema")!=SCHEMA or message.get("role")!="LOCAL_READ_ONLY_DIAGNOSTIC":
        raise ValueError("REASON_MESSAGE_CANNOT_AUTHORIZE_TOOLS")
    if message.get("index_owner_approval") is not False or message.get("auto_done") is not False:
        raise ValueError("REASON_MESSAGE_PRETENDS_APPROVAL")
    if message.get("model_calls_authorized") is not False or message.get("external_actions_authorized") is not False:
        raise ValueError("REASON_MESSAGE_COST_OR_EXTERNAL_ACTION_REJECTED")
    expected=prepare(message.get("task_id"))
    if message!=expected:
        raise ValueError("REASON_CANONICAL_WORK_CONTRACT_CHANGED")
    return sender,message_id,message

prepare_keys={"schema","task_id","task_contract_sha256","evidence_signature",
              "role","index_owner_approval","auto_done",
              "model_calls_authorized","external_actions_authorized"}

def consume(sender,message_id,work):
    dest=RECEIPTS/("TAKY_REASON_GUIDED_"+message_id+".json")
    if dest.exists():
        existing=read_json(dest)
        if (existing.get("schema")!="TAKY_REASON_GUIDED_RECEIPT_V1" or
            existing.get("message_id")!=message_id or existing.get("task_id")!=work["task_id"]):
            raise ValueError("REASON_MESSAGE_ID_REPLAY_CONFLICT")
        return {"state":"REPLAY_ALREADY_EVIDENCED_NOT_EXECUTED",
                "task_id":work["task_id"],"message_id":message_id,
                "receipt_sha256":hashfile(dest)}
    # Canonical admission and the actual execution code share the same
    # checked input signature, and run_checks verifies it again after work.
    result=run_checks(work["task_id"],DEFAULT_BOARD,RECEIPTS)
    filename=Path(result["evidence"]) if result.get("evidence") else None
    if not filename or not filename.is_file() or not filename.resolve().is_relative_to(RECEIPTS.resolve()):
        raise ValueError("REASON_LOCAL_WORK_EVIDENCE_MISSING")
    source=read_json(filename)
    if (source.get("schema")!="TAKY_LOCAL_WORK_SLICE_V1"
        or source.get("task_id")!=work["task_id"]
        or source.get("portfolio_done") is not False
        or source.get("no_model_calls") is not True
        or source.get("no_push_merge_deploy") is not True):
        raise ValueError("REASON_WORK_RESULT_NOT_SAFE")
    proof={"schema":"TAKY_REASON_GUIDED_RECEIPT_V1",
           "message_id":message_id,"sender":sender,"task_id":work["task_id"],
           "execution_mode":"EXISTING_TAKY_READ_ONLY_WORKER",
           "source_work_contract_sha256":work["task_contract_sha256"],
           "result_state":source["state"],"source_evidence_sha256":hashfile(filename),
           "source_evidence":str(filename),
           "human_verified_done":False,"work_authority_modified":False,
           "model_calls":0,"paid_api_calls":0,"push_merge_deploy":False,
           "observed_at":datetime.now(timezone.utc).isoformat()}
    with dest.open("x",encoding="utf-8") as f:
        json.dump(proof,f,ensure_ascii=False,indent=2)
    return {"state":"REASON_GUIDED_REAL_WORK_RECEIPT",
            "task_id":work["task_id"],"result":source["state"],
            "message_id":message_id,"receipt_sha256":hashfile(dest)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--prepare",choices=sorted(ALLOWED))
    parser.add_argument("--capability",action="store_true")
    parser.add_argument("--listen",action="store_true")
    parser.add_argument("--wait",type=int,default=25)
    args=parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(args.prepare),ensure_ascii=False,separators=(",",":")))
        return
    if args.capability:
        print(json.dumps(reason_capability(),ensure_ascii=False))
        return
    if not args.listen:raise ValueError("REASON_MODE_REQUIRED")
    if args.wait<1 or args.wait>90:raise ValueError("REASON_WAIT_OUT_OF_BOUNDS")
    if not REASON.is_file():raise ValueError("REASON_BINARY_MISSING")
    incoming=subprocess.run([str(REASON),"listen","--as",SESSION,"--wait",str(args.wait)],
         cwd=Path.home(),capture_output=True,text=True,encoding="utf-8",
         errors="replace",timeout=args.wait+20,check=False)
    if incoming.returncode!=0:raise RuntimeError("REASON_LISTEN_TRANSPORT_FAILED")
    if incoming.stdout.strip().startswith("No messages in"):
        print(json.dumps({"state":"REASON_QUEUE_IDLE","no_model_calls":True,
                          "no_owner_change":True},ensure_ascii=False))
        return
    sender,message_id,work=decode(incoming.stdout)
    result=consume(sender,message_id,work)
    # This notification is informational only; it cannot turn a HOLD into DONE.
    outgoing=f"TAKY_REASON_GUIDED_RESULT_V1 task={result['task_id']} message={message_id} state={result['state']} receipt_sha256={result['receipt_sha256']} done=false"
    # Do not rely on an ephemeral CLI terminal session; the established
    # local TAKY inbox is the reusable feedback route.
    sent=subprocess.run([str(REASON),"send","taky-local/takyinbox",outgoing],
         cwd=Path.home(),capture_output=True,text=True,encoding="utf-8",
         errors="replace",timeout=15,check=False)
    result["reason_return_message_accepted"]=sent.returncode==0 and (
       "delivered" in sent.stdout.lower() or "queued" in sent.stdout.lower())
    result["reason_return_message_live_received"]=sent.returncode==0 and "delivered" in sent.stdout.lower()
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":main()
