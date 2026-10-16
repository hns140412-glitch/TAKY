#!/usr/bin/env python3
"""TAKY opted-in, one-turn, detached-CLI diagnostic adapter.
This is NOT a native Antigravity panel transport. Default is prepare-only.
The existing V3 mailbox/worker remains unchanged.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, subprocess, sys, time
from datetime import datetime, timezone

import taky_antigravity_bridge_v3_candidate as bridge

BASE=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON")
OUT=BASE/"04_HISTORY"/"CLI_BRIDGE_RECEIPTS"
CLAIM_DIR=bridge.LOCAL_BRIDGE_DIR/"cli_one_time_claims"
CLAUDE=pathlib.Path.home()/".local"/"bin"/"claude.exe"
CODEX_SHIM=pathlib.Path(r"D:\Git PWA\TAKY\TOOLS\TAKY_CODEX_SHIM.ps1")

def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def receipt(taskid, data):
    OUT.mkdir(parents=True,exist_ok=True)
    f=OUT/(taskid+".json")
    if f.exists():raise RuntimeError("RECEIPT_EXISTS_NO_OVERWRITE")
    bridge.seal_receipt(data)
    bridge.write_new(f,data)
    return str(f)
def get_task(taskid):
    body=bridge.poll(taskid)
    if body.get("status")!="PREPARED_NOT_EXECUTED" or body.get("provider_invoked") is not False:
        raise RuntimeError("SIGNED_PROVIDER_TASK_NOT_PREPARED")
    req=bridge.load(bridge.MAILBOX/"requests"/(taskid+".json"))
    if bridge.validate(req):raise RuntimeError("INVALID_SIGNED_REQUEST")
    if body.get("request_hash")!=req["payload_sha256"]:raise RuntimeError("REQUEST_RECEIPT_MISMATCH")
    if req.get("actor") not in ("CLAUDE","CODEX"):raise RuntimeError("WRONG_PROVIDER")
    if req.get("context_delivery"):
        # A signed bundle being prepared is NOT evidence the model consumed it.
        # Block detached execution until provider-side receipt/ACK protocol exists.
        raise RuntimeError("CONTEXT_BOUND_PROVIDER_DELIVERY_NOT_IMPLEMENTED")
    repo=bridge.ALLOWED.get(req.get("project"))
    if not repo or bridge.snap(repo)!=req.get("repo_state"):
        raise RuntimeError("GIT_STATE_DRIFT")
    if bridge.current().get("sha256")!=req.get("context",{}).get("sha256"):
        raise RuntimeError("CONTEXT_DRIFT")
    return req,body,repo
def invoke(taskid, expected,execute):
    req,confirmation,repo=get_task(taskid)
    agent=req["actor"]
    if not re.fullmatch(r"TAKY_[A-Z]+_[A-F0-9]{8}_PASS",expected):
        raise ValueError("EXPECTED_TOKEN_FORMAT_INVALID")
    # Deterministic diagnostic prompt; no project file modifications.
    prompt=f"Read only. Do not use tools or inspect files. Reply with exactly this single token and no other text: {expected}"
    command=([str(CLAUDE),"-p",prompt,"--output-format","json","--no-session-persistence","--max-turns","1","--tools",""] if agent=="CLAUDE" else
        ["pwsh.exe","-NoProfile","-File",str(CODEX_SHIM),"exec","--sandbox","read-only","--cd",str(repo),"--json",prompt])
    state={"schema":"TAKY_CLI_DETACHED_EXECUTION_CANDIDATE_V1","task_id":taskid,
           "request_sha256":req["payload_sha256"],"agent":agent,
           "session_mode":"NEW_DETACHED_CLI_NOT_IDE_PANEL","native_panel_bound":False,
           "repo":str(repo),"head":req["repo_state"]["head"],
           "context_sha256":req["context"]["sha256"],"prompt_sha256":sha(prompt.encode()),
           "expected_token":expected,"model_turns_max":1,"tool_policy":"NO_TOOLS_REQUESTED / READ_ONLY_SANDBOX",
           "provider_authenticated_via_existing_subscription":"REQUIRES_LIVE_CHECK",
           "paid_api_environment_excluded":True,
           "created_utc":now(),"status":"PREPARED_NOT_EXECUTED",
           "model_called":False,"forbidden":["PUSH","MERGE","DEPLOY","REPO_WRITE","METERED_API"]}
    if not execute:return state
    if os.environ.get("TAKY_USER_EXPLICIT_AUTHORIZATION")!="1":
        raise RuntimeError("USER_EXECUTION_AUTHORIZATION_REQUIRED")
    if os.environ.get("TAKY_CLI_DETACHED_MODE")!="ACK_SEPARATE_SESSION":
        raise RuntimeError("DETACHED_SESSION_DISCLOSURE_REQUIRED")
    if not CLAUDE.is_file() or not CODEX_SHIM.is_file():raise RuntimeError("PROVIDER_ENTRYPOINT_MISSING")
    if (OUT/(taskid+".json")).exists():
        raise RuntimeError("FINAL_RECEIPT_EXISTS_NO_REPEAT")
    # Permanent local claim, created atomically before any provider subprocess starts.
    # Keep claims after failures/timeouts: a retry needs separate deliberate review/task ID.
    CLAIM_DIR.mkdir(parents=True,exist_ok=True)
    claim=CLAIM_DIR/(taskid+".json")
    claim_data=json.dumps({"task_id":taskid,"created_utc":now(),
                           "executor":agent,"session":"DETACHED_CLI",
                           "replay":"DENIED"},sort_keys=True).encode("utf-8")
    try:
        fd=os.open(claim,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        raise RuntimeError("TASK_ALREADY_CLAIMED_NO_REPEAT")
    with os.fdopen(fd,"wb") as handle:
        handle.write(claim_data)
    environ=os.environ.copy()
    for sensitive in ("ANTHROPIC_API_KEY","OPENAI_API_KEY","ANTHROPIC_BASE_URL","OPENAI_BASE_URL"):
        environ.pop(sensitive,None)
    environ["TAKY_USER_EXPLICIT_AUTHORIZATION"]="1"
    environ["TAKY_USER_INTENT"]="TAKY Antigravity general-chat to detached subscription CLI one-turn integration acceptance"
    state["model_called"]=True
    state["started_utc"]=now()
    t=time.monotonic()
    try:
        p=subprocess.run(command,cwd=repo,env=environ,capture_output=True,text=True,encoding="utf-8",
                         errors="replace",timeout=90,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        state["exit_code"]=p.returncode
        raw=p.stdout
        response=""
        if agent=="CLAUDE":
            try:
                envelope=json.loads(raw)
                response=str(envelope.get("result","")).strip()
                state["provider_session_id"]=str(envelope.get("session_id",""))[:128]
                state["reported_is_error"]=bool(envelope.get("is_error",True))
            except Exception:
                state["parse_error"]="CLAUDE_JSON_RESULT_UNREADABLE"
        else:
            # Structured Codex stdout, no echo of user prompt to shared receipts.
            events=[]
            for line in raw.splitlines():
                try:
                    ob=json.loads(line)
                    if isinstance(ob,dict):events.append(ob)
                except Exception:pass
            state["event_types"]=sorted(set(str(e.get("type","")) for e in events))[:20]
            msgs=[]
            for e in events:
                if e.get("type")=="item.completed":
                    item=e.get("item") or {}
                    if item.get("type")=="agent_message":msgs.append(str(item.get("text","")))
                if e.get("type")=="thread.started":state["provider_session_id"]=str(e.get("thread_id",""))[:128]
            response=(msgs[-1] if msgs else "").strip()
            state["codex_completed_event"]=any(e.get("type")=="turn.completed" for e in events)
        state["response_sha256"]=sha(response.encode())
        state["response_characters"]=len(response)
        state["verified_expected_reply"]=response==expected
        state["status"]="EXECUTED_E2E_REPLY_VERIFIED" if p.returncode==0 and response==expected else "EXECUTED_UNVERIFIED"
        state["stderr_sha256"]=sha(p.stderr.encode())
        state["stderr_line_count"]=len(p.stderr.splitlines())
    except subprocess.TimeoutExpired:
        state["status"]="TIMEOUT_HOLD"
        state["error"]="SINGLE_ATTEMPT_LIMIT_90_SECONDS"
    except Exception as e:
        state["status"]="ERROR_HOLD"
        state["error_class"]=type(e).__name__
    state["duration_seconds"]=round(time.monotonic()-t,2)
    state["finished_utc"]=now()
    state["receipt_path"]=receipt(taskid,state)
    return state
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--task-id",required=True)
    parser.add_argument("--expected",required=True)
    parser.add_argument("--execute",action="store_true")
    a=parser.parse_args()
    result=invoke(a.task_id,a.expected,a.execute)
    print(json.dumps({key:result.get(key) for key in
        ("task_id","agent","session_mode","status","model_called","exit_code",
         "verified_expected_reply","provider_session_id","duration_seconds","receipt_path")},
         ensure_ascii=False))
    return 0 if result["status"] in ("PREPARED_NOT_EXECUTED","EXECUTED_E2E_REPLY_VERIFIED") else 2
if __name__=="__main__":sys.exit(main())
