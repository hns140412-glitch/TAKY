#!/usr/bin/env python3
"""TAKY v3 candidate: ChatGPT -> Drive mailbox -> deterministic receipt.
NO MODEL INVOCATION. Future adapter must reuse governed TAKY2 wrapper and
separately verify provider session identity, user consent and quota.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, subprocess, uuid
from datetime import datetime, timezone

ROOT=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON")
MAILBOX=ROOT/"01_INBOX"/"TAKY_BRIDGE_V3_CANDIDATE"
CURRENT=ROOT/"02_CURRENT"/"TAKY_CONVERSATION_RESUME.json"
ALLOWED={
    "TAKY":pathlib.Path(r"D:\Git PWA\TAKY"),
    "TAKY2":pathlib.Path(r"D:\Git PWA\TAKY-2.0-ORCH")
}
CAPS={
    "CLAUDE":{"skills":".claude/skills","settings":".claude/settings.json",
              "mcp":"TAKY/.mcp.json or global Claude settings"},
    "CODEX":{"skills":".agents/skills","settings":"AGENTS.md and user config.toml",
             "mcp":"Codex user config.toml"}
}
SCHEMA="TAKY_ANTIGRAVITY_BRIDGE_V3_CANDIDATE"
ACTIONS={"ECHO","REPO_INFO","CAPABILITY_ATTEST","CLAUDE","CODEX"}
def timestamp():
    return datetime.now(timezone.utc).isoformat()
def digest(content):
    return hashlib.sha256(content).hexdigest()
def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def write_new(file,obj):
    file.parent.mkdir(parents=True,exist_ok=True)
    tmp=file.with_name(file.name+"."+uuid.uuid4().hex+".tmp")
    tmp.write_bytes(json.dumps(obj,ensure_ascii=False,indent=2).encode("utf-8"))
    if file.exists():
        tmp.unlink(missing_ok=True)
        raise FileExistsError(str(file))
    os.replace(tmp,file)
def load(file):
    return json.loads(file.read_text(encoding="utf-8-sig"))
def run_git(repo,*args):
    output=subprocess.run(["git","-C",str(repo),*args],capture_output=True,text=True,timeout=12)
    if output.returncode:
        raise RuntimeError("GIT_QUERY_FAILED:"+" ".join(args))
    return output.stdout.strip()
def snap(repo):
    return {
        "repo":str(repo),
        "head":run_git(repo,"rev-parse","HEAD"),
        "branch":run_git(repo,"branch","--show-current"),
        "dirty_file_count":len(run_git(repo,"status","--porcelain=v1","-uno").splitlines())
    }
def current():
    if not CURRENT.is_file():
        return {"state":"UNRESOLVED","path":str(CURRENT),"sha256":None}
    raw=CURRENT.read_bytes()
    return {"state":"DERIVED_SNAPSHOT_PRESENT_NOT_CANONICAL","path":str(CURRENT),
            "sha256":digest(raw),"bytes":len(raw)}
def attest(repo):
    result={}
    for agent,cap in CAPS.items():
        folder=repo/cap["skills"]
        skills=[]
        if folder.is_dir():
            for item in sorted(folder.iterdir()):
                f=item/"SKILL.md"
                if item.is_dir() and f.is_file():
                    raw=f.read_bytes()
                    skills.append({"skill":item.name,"sha256":digest(raw),
                                   "link_target":str(item.resolve()) if item.is_symlink() else None})
        result[agent]={"skills_available_on_disk":len(skills),"skills":skills,
                       "live_invocation_attested":False,"mcp_runtime_attested":False,
                       "mcp_configuration_source":cap["mcp"]}
    return result
def stage(args):
    if args.actor not in ACTIONS or args.project not in ALLOWED:
        raise ValueError("ACTOR_OR_PROJECT_NOT_ALLOWED")
    if not args.intent or len(args.intent)>2000:
        raise ValueError("INTENT_REQUIRED_MAX_2000")
    repo=ALLOWED[args.project]
    req={
        "schema":SCHEMA,"task_id":uuid.uuid4().hex,"created_utc":timestamp(),
        "actor":args.actor,"project":args.project,"intent":args.intent,
        "source":"CHATGPT_GENERAL_CHAT_REMOTE_COMMAND",
        "requested_mode":"READ_ONLY","repo_state":snap(repo),
        "context":current(),"session_binding":"NATIVE_PANEL_UNVERIFIED",
        "cost":"NO_MODEL_CALL_IN_CANDIDATE","consent":"MODEL_CALL_NOT_AUTHORIZED_BY_THIS_FILE",
        "forbidden_actions":["PUSH","MERGE","DEPLOY","DELETE","PAID_API","CANONICAL_WRITE"]
    }
    req["payload_sha256"]=digest(canonical(req))
    write_new(MAILBOX/"requests"/(req["task_id"]+".json"),req)
    return {"status":"STAGED","task_id":req["task_id"],"request_hash":req["payload_sha256"]}
def validate(req):
    if req.get("schema")!=SCHEMA or not re.fullmatch("[0-9a-f]{32}",str(req.get("task_id",""))):
        return "MALFORMED_REQUEST"
    h=req.get("payload_sha256")
    packet={k:v for k,v in req.items() if k!="payload_sha256"}
    if h!=digest(canonical(packet)):
        return "REQUEST_HASH_MISMATCH"
    if req.get("project") not in ALLOWED or req.get("actor") not in ACTIONS:
        return "EXECUTOR_OR_PROJECT_UNTRUSTED"
    if req.get("requested_mode")!="READ_ONLY":
        return "EFFECT_SCOPE_FORBIDDEN"
    return None
def process(req):
    reason=validate(req)
    actor=req.get("actor","UNKNOWN")
    rid=req.get("task_id","UNKNOWN")
    result={"schema":SCHEMA,"task_id":rid,"actor":actor,"processed_utc":timestamp(),
            "request_hash":req.get("payload_sha256"),"provider_invoked":False,
            "native_panel_session_confirmed":False,"canonical_modified":False}
    if reason:
        result.update(status="HOLD",error=reason)
    else:
        repo=ALLOWED[req["project"]]
        current_repo=snap(repo)
        if current_repo["head"]!=req["repo_state"].get("head"):
            result.update(status="HOLD",error="HEAD_CHANGED_RESTAGE")
        elif current_repo["branch"]!=req["repo_state"].get("branch"):
            result.update(status="HOLD",error="BRANCH_CHANGED_RESTAGE")
        elif current_repo["dirty_file_count"]!=req["repo_state"].get("dirty_file_count"):
            result.update(status="HOLD",error="WORKTREE_CHANGED_RESTAGE")
        elif current()["sha256"]!=req.get("context",{}).get("sha256"):
            result.update(status="HOLD",error="CONTEXT_CHANGED_RESTAGE")
        elif actor=="ECHO":
            result.update(status="PASS",data={"ack":req["intent"]})
        elif actor=="REPO_INFO":
            result.update(status="PASS",data=current_repo)
        elif actor=="CAPABILITY_ATTEST":
            result.update(status="PASS",data={"repo":current_repo,
                "skills":attest(repo),"context_snapshot":current()})
        elif actor in ("CLAUDE","CODEX"):
            result.update(status="PREPARED_NOT_EXECUTED",data={
                "requested_executor":actor,"repo":current_repo,
                "context":current(),"capabilities":attest(repo)[actor],
                "session_binding":"NATIVE_PANEL_UNVERIFIED",
                "next_gate":"VERIFY_SESSION_IDENTITY_AND_USER_APPROVAL_AND_COST_THEN_CALL_GOVERNED_EXECUTOR",
                "provider_cli_call":"NOT_PERFORMED"})
        else:
            result.update(status="HOLD",error="UNSUPPORTED")
    result["receipt_sha256"]=digest(canonical(result))
    return result
def worker_once():
    seen=0
    for f in sorted((MAILBOX/"requests").glob("*.json")):
        if not re.fullmatch(r"[0-9a-f]{32}\.json",f.name):
            continue
        destination=MAILBOX/"responses"/f.name
        if destination.exists():
            continue
        try:
            receipt=process(load(f))
        except Exception as exc:
            receipt={"schema":SCHEMA,"status":"HOLD","task_id":f.stem,
                     "error":"WORKER_EXCEPTION:"+type(exc).__name__,"provider_invoked":False}
            receipt["receipt_sha256"]=digest(canonical(receipt))
        write_new(destination,receipt)
        seen+=1
    return {"status":"WORKER_ONCE","new_receipts":seen}
def poll(taskid):
    if not re.fullmatch("[0-9a-f]{32}",taskid):
        raise ValueError("BAD_TASK_ID")
    target=MAILBOX/"responses"/(taskid+".json")
    if not target.exists():
        return {"status":"PENDING","task_id":taskid}
    data=load(target)
    expected=data.get("receipt_sha256")
    observed=digest(canonical({k:v for k,v in data.items() if k!="receipt_sha256"}))
    if expected!=observed or data.get("task_id")!=taskid:
        return {"status":"HOLD","task_id":taskid,"error":"RECEIPT_INTEGRITY_MISMATCH"}
    return data
def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["stage","worker-once","poll","status"])
    p.add_argument("--actor",default="CAPABILITY_ATTEST")
    p.add_argument("--project",default="TAKY2")
    p.add_argument("--intent",default="Verify common TAKY context and capabilities")
    p.add_argument("--id",default="")
    a=p.parse_args()
    if a.mode=="stage":r=stage(a)
    elif a.mode=="worker-once":r=worker_once()
    elif a.mode=="poll":r=poll(a.id)
    else:r={"schema":SCHEMA,"mailbox_present":MAILBOX.is_dir(),
            "project_present":{key:v.is_dir() for key,v in ALLOWED.items()},
            "context":current(),"session_native_panel":"UNVERIFIED",
            "supported_actions":sorted(ACTIONS),"provider_invocations_enabled":False}
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
