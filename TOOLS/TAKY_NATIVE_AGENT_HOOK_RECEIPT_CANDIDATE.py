#!/usr/bin/env python3
"""TAKY candidate native-agent hook receipt (NO PROMPT TEXT STORAGE).
Reads UserPromptSubmit input from stdin. Does not execute models, approve work,
write canonical CURRENT, or advance learner/agent read pointers.
"""
from __future__ import annotations
import hashlib,hmac,json,os,pathlib,re,sys
from datetime import datetime,timezone

TOOLS=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(TOOLS))
import taky_antigravity_bridge_v3_candidate as bridge

PROOF_DIR=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY\TAKY_AGENT_HOOK_RECEIPTS_CANDIDATE")
REPO=bridge.ALLOWED["TAKY2"]
TASK_ID_RX=re.compile(r"(?<![0-9a-f])(?:TAKY_TASK_ID\s*[:=]\s*)([0-9a-f]{32})(?![0-9a-f])",re.I)
def on_prompt(data, out_dir=PROOF_DIR):
    if data.get("hook_event_name")!="UserPromptSubmit":return {"state":"IGNORED_EVENT"}
    cwd=pathlib.Path(str(data.get("cwd",""))).resolve()
    if cwd!=REPO.resolve():return {"state":"IGNORED_OTHER_REPO"}
    prompt=str(data.get("prompt",""))
    m=TASK_ID_RX.search(prompt)
    if not m:return {"state":"IGNORED_NO_TASK_MARKER"}
    taskid=m.group(1).lower()
    req_path=bridge.MAILBOX/"requests"/(taskid+".json")
    if not req_path.is_file():return {"state":"IGNORED_UNKNOWN_TASK"}
    req=bridge.load(req_path)
    if bridge.validate(req) is not None:return {"state":"IGNORED_UNTRUSTED_TASK"}
    result=bridge.poll(taskid)
    if result.get("status")!="PREPARED_NOT_EXECUTED":
        return {"state":"IGNORED_NONPREPARED_TASK"}
    provider="CLAUDE" if str(data.get("source","")).lower()=="claude" else None
    # Provider identities in hook inputs are caller claims. Config-specific
    # caller identity must be supplied via project-installed argument.
    provider=str(data.get("_taky_installed_provider",""))
    if provider!=req.get("actor"):return {"state":"IGNORED_WRONG_PROVIDER"}
    sess=str(data.get("session_id",""))[:128]
    if not sess or len(sess)<8:return {"state":"IGNORED_NO_SESSION"}
    packet={
      "schema":"TAKY_NATIVE_HOOK_RECEIPT_CANDIDATE_V1",
      "event":"USER_PROMPT_SUBMITTED_HOOK_OBSERVED",
      "task_id":taskid,"provider":provider,
      "session_id_sha256":hashlib.sha256(sess.encode()).hexdigest(),
      "request_sha256":req["payload_sha256"],
      "hook_event_name":"UserPromptSubmit",
      "cwd":str(cwd),
      "source_input_untrusted":True,
      "actual_model_completed":False,
      "native_panel_binding_verified":False,
      "current_ack_cursor_advanced":False,
      "received_time_utc":datetime.now(timezone.utc).isoformat()
    }
    bridge.seal_receipt(packet)
    digest=hashlib.sha256((provider+sess+taskid).encode()).hexdigest()[:24]
    folder=pathlib.Path(out_dir)/provider
    file=folder/(taskid+"_"+digest+".json")
    if file.is_file():
        old=bridge.load(file)
        if old.get("request_sha256")!=packet["request_sha256"]:
            return {"state":"HOLD_EXISTING_RECEIPT_CONFLICT"}
        return {"state":"HOOK_RECEIPT_ALREADY_PRESENT"}
    bridge.write_new(file,packet)
    return {"state":"HOOK_SUBMIT_METADATA_SIGNED","task_id":taskid}
def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--provider",choices=["CLAUDE","CODEX"],required=True)
    args=parser.parse_args()
    try:
        raw=sys.stdin.read(250000)
        obj=json.loads(raw)
        if isinstance(obj,dict):
            obj["_taky_installed_provider"]=args.provider
            on_prompt(obj)
    except Exception:
        pass
    # Empty stdout is intentional: no prompt rewrite, no security override.
    return 0
if __name__=="__main__":
    sys.exit(main())
