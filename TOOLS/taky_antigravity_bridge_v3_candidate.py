#!/usr/bin/env python3
"""TAKY v3 candidate: ChatGPT -> Drive mailbox -> deterministic receipt.
NO MODEL INVOCATION. Future adapter must reuse governed TAKY2 wrapper and
separately verify provider session identity, user consent and quota.
"""
from __future__ import annotations
import argparse, hashlib, hmac, json, os, pathlib, re, secrets, subprocess, tomllib, uuid
from datetime import datetime, timezone

ROOT=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON")
MAILBOX=ROOT/"01_INBOX"/"TAKY_BRIDGE_V3_CANDIDATE"
CURRENT=ROOT/"02_CURRENT"/"TAKY_CONVERSATION_RESUME.json"
DELTA_DELIVERIES=ROOT/"04_HISTORY"/"TAKY_CONTEXT_DELTA_CANDIDATE"/"deliveries"
LOCAL_BRIDGE_DIR=pathlib.Path(os.environ.get("LOCALAPPDATA",str(pathlib.Path.home()))) / "TAKY" / "bridge"
HOST_KEY=LOCAL_BRIDGE_DIR/"v3_candidate_host_key.bin"
WORKER_LOCK=LOCAL_BRIDGE_DIR/"v3_candidate_worker.lock"
ALLOWED={
    "TAKY":pathlib.Path(r"D:\Git PWA\TAKY"),
    "TAKY2":pathlib.Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")
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
def host_key():
    # Local single-user trust boundary; never put this key in the Drive mailbox.
    HOST_KEY.parent.mkdir(parents=True,exist_ok=True)
    if not HOST_KEY.exists():
        try:
            with os.fdopen(os.open(HOST_KEY,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"wb") as stream:
                stream.write(secrets.token_bytes(32))
        except FileExistsError:
            pass
    data=HOST_KEY.read_bytes()
    if len(data)!=32:
        raise RuntimeError("LOCAL_BRIDGE_KEY_INVALID_HOLD")
    return data
def mac(s):
    return hmac.new(host_key(),s.encode("ascii"),hashlib.sha256).hexdigest()
def host_identity():
    return hashlib.sha256(host_key()).hexdigest()[:20]
def seal_receipt(receipt):
    receipt["receipt_sha256"]=digest(canonical(receipt))
    receipt["receipt_mac"]=mac(receipt["receipt_sha256"])
    return receipt
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
    status=run_git(repo,"status","--porcelain=v1","--untracked-files=normal")
    return {
        "repo":str(repo),
        "head":run_git(repo,"rev-parse","HEAD"),
        "branch":run_git(repo,"branch","--show-current"),
        "dirty_file_count":len(status.splitlines()),
        "worktree_status_sha256":digest(status.encode("utf-8"))
    }
def current():
    if not CURRENT.is_file():
        return {"state":"UNRESOLVED","path":str(CURRENT),"sha256":None}
    raw=CURRENT.read_bytes()
    return {"state":"DERIVED_SNAPSHOT_PRESENT_NOT_CANONICAL","path":str(CURRENT),
            "sha256":digest(raw),"bytes":len(raw)}
def mcp_names(repo,agent):
    if agent=="CLAUDE":
        file=repo/".mcp.json"
        if not file.is_file():
            return {"state":"PROJECT_MCP_CONFIG_MISSING","names":[],"sha256":None}
        try:
            raw=file.read_bytes()
            names=sorted((json.loads(raw).get("mcpServers") or {}).keys())
            return {"state":"PROJECT_MCP_CONFIG_PRESENT_RUNTIME_UNVERIFIED",
                    "names":names,"sha256":digest(raw)}
        except (ValueError,TypeError,OSError):
            return {"state":"MCP_CONFIG_PARSE_HOLD","names":[],"sha256":None}
    file=pathlib.Path.home()/".codex"/"config.toml"
    if not file.is_file():
        return {"state":"USER_MCP_CONFIG_MISSING","names":[],"sha256":None}
    try:
        raw=file.read_bytes()
        names=sorted((tomllib.loads(raw.decode("utf-8-sig")).get("mcp_servers") or {}).keys())
        return {"state":"USER_MCP_CONFIG_PRESENT_RUNTIME_UNVERIFIED",
                "names":names,"sha256":digest(raw)}
    except (ValueError,TypeError,OSError):
        return {"state":"MCP_CONFIG_PARSE_HOLD","names":[],"sha256":None}
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
                    linked=item.is_symlink() or (hasattr(item,"is_junction") and item.is_junction())
                    skills.append({"skill":item.name,"sha256":digest(raw),
                                   "link_target":str(item.resolve()) if linked else None})
        instruction=repo/("CLAUDE.md" if agent=="CLAUDE" else "AGENTS.md")
        result[agent]={"skills_available_on_disk":len(skills),"skills":skills,
                       "project_instructions_present":instruction.is_file(),
                       "project_mcp":mcp_names(repo,agent),
                       "live_invocation_attested":False,"mcp_runtime_attested":False,
                       "mcp_configuration_source":cap["mcp"]}
    return result
def delivery_binding(actor,identifier):
    if actor not in ("CLAUDE","CODEX") or not re.fullmatch(r"[0-9a-f]{24}",str(identifier)):
        raise ValueError("INVALID_CONTEXT_DELIVERY_TARGET")
    f=DELTA_DELIVERIES/actor/(identifier+".json")
    if not f.is_file():
        raise ValueError("CONTEXT_DELIVERY_MISSING")
    raw=f.read_bytes()
    envelope=json.loads(raw)
    digest_value=envelope.get("receipt_sha256")
    payload={k:v for k,v in envelope.items() if k not in ("receipt_sha256","receipt_mac")}
    if (digest_value!=digest(canonical(payload)) or not hmac.compare_digest(
          str(envelope.get("receipt_mac") or ""),mac(digest_value or ""))):
        raise ValueError("CONTEXT_DELIVERY_SIGNATURE_INVALID")
    if (envelope.get("delivery_id")!=identifier or envelope.get("actor")!=actor
        or envelope.get("delivery_state")!="PENDING_RECEIVER_ACK"
        or envelope.get("current",{}).get("sha256")!=current().get("sha256")
        or not envelope.get("event_ids") or envelope.get("event_seq_end",0)<1):
        raise ValueError("CONTEXT_DELIVERY_STALE_OR_INCOMPLETE")
    return {"delivery_id":identifier,"sha256":digest(raw),
            "event_ids":envelope["event_ids"],"event_seq_end":envelope["event_seq_end"],
            "source_current_sha256":envelope["current"]["sha256"]}
def stage(args):
    if args.actor not in ACTIONS or args.project not in ALLOWED:
        raise ValueError("ACTOR_OR_PROJECT_NOT_ALLOWED")
    if not args.intent or len(args.intent)>2000:
        raise ValueError("INTENT_REQUIRED_MAX_2000")
    repo=ALLOWED[args.project]
    req={
        "schema":SCHEMA,"task_id":uuid.uuid4().hex,"created_utc":timestamp(),
        "actor":args.actor,"project":args.project,"intent":args.intent,
        "source":"CHATGPT_GENERAL_CHAT_REMOTE_COMMAND","host_identity":host_identity(),
        "requested_mode":"READ_ONLY","repo_state":snap(repo),
        "context":current(),"session_binding":"NATIVE_PANEL_UNVERIFIED",
        "cost":"NO_MODEL_CALL_IN_CANDIDATE","consent":"MODEL_CALL_NOT_AUTHORIZED_BY_THIS_FILE",
        "forbidden_actions":["PUSH","MERGE","DEPLOY","DELETE","PAID_API","CANONICAL_WRITE"]
    }
    delivery_id=getattr(args,"context_delivery_id","")
    if delivery_id:
        req["context_delivery"]=delivery_binding(args.actor,delivery_id)
    req["payload_sha256"]=digest(canonical(req))
    req["payload_mac"]=mac(req["payload_sha256"])
    write_new(MAILBOX/"requests"/(req["task_id"]+".json"),req)
    return {"status":"STAGED","task_id":req["task_id"],"request_hash":req["payload_sha256"]}
def validate(req):
    if req.get("schema")!=SCHEMA or not re.fullmatch("[0-9a-f]{32}",str(req.get("task_id",""))):
        return "MALFORMED_REQUEST"
    h=req.get("payload_sha256")
    packet={k:v for k,v in req.items() if k not in ("payload_sha256","payload_mac")}
    if h!=digest(canonical(packet)):
        return "REQUEST_HASH_MISMATCH"
    supplied=req.get("payload_mac") or ""
    if not hmac.compare_digest(str(supplied),mac(h)):
        return "REQUEST_ORIGIN_NOT_ATTESTED"
    if req.get("project") not in ALLOWED or req.get("actor") not in ACTIONS:
        return "EXECUTOR_OR_PROJECT_UNTRUSTED"
    if req.get("host_identity")!=host_identity():
        return "WRONG_TARGET_PC"
    if req.get("requested_mode")!="READ_ONLY":
        return "EFFECT_SCOPE_FORBIDDEN"
    if "context_delivery" in req:
        binding=req["context_delivery"]
        try:
            observed=delivery_binding(req["actor"],binding["delivery_id"])
        except (ValueError,KeyError,TypeError):
            return "CONTEXT_DELIVERY_NOT_TRUSTED"
        if binding!=observed:
            return "CONTEXT_DELIVERY_CHANGED"
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
        elif current_repo["worktree_status_sha256"]!=req["repo_state"].get("worktree_status_sha256"):
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
                "context_delivery_binding":req.get("context_delivery"),
                "session_binding":"NATIVE_PANEL_UNVERIFIED",
                "next_gate":"VERIFY_SESSION_IDENTITY_AND_USER_APPROVAL_AND_COST_THEN_CALL_GOVERNED_EXECUTOR",
                "provider_cli_call":"NOT_PERFORMED"})
        else:
            result.update(status="HOLD",error="UNSUPPORTED")
    return seal_receipt(result)
def _worker_once_unlocked():
    seen=0
    for f in sorted((MAILBOX/"requests").glob("*.json")):
        if not re.fullmatch(r"[0-9a-f]{32}\.json",f.name):
            continue
        destination=MAILBOX/"responses"/f.name
        if destination.exists():
            continue
        try:
            request=load(f)
            if request.get("host_identity")!=host_identity():
                continue
            receipt=process(request)
        except Exception as exc:
            receipt={"schema":SCHEMA,"status":"HOLD","task_id":f.stem,
                     "error":"WORKER_EXCEPTION:"+type(exc).__name__,"provider_invoked":False}
            seal_receipt(receipt)
        write_new(destination,receipt)
        seen+=1
    return {"status":"WORKER_ONCE","new_receipts":seen}
def worker_once():
    # Exclusive lock for this PC only; a stale lock requires inspection, not auto-overwrite.
    WORKER_LOCK.parent.mkdir(parents=True,exist_ok=True)
    try:
        fd=os.open(WORKER_LOCK,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        return {"status":"HOLD_WORKER_ALREADY_RUNNING","new_receipts":0}
    try:
        os.close(fd)
        return _worker_once_unlocked()
    finally:
        WORKER_LOCK.unlink(missing_ok=True)
def poll(taskid):
    if not re.fullmatch("[0-9a-f]{32}",taskid):
        raise ValueError("BAD_TASK_ID")
    target=MAILBOX/"responses"/(taskid+".json")
    if not target.exists():
        return {"status":"PENDING","task_id":taskid}
    data=load(target)
    expected=data.get("receipt_sha256")
    observed=digest(canonical({k:v for k,v in data.items() if k not in ("receipt_sha256","receipt_mac")}))
    signed=bool(expected) and hmac.compare_digest(str(data.get("receipt_mac") or ""),mac(expected))
    if expected!=observed or not signed or data.get("task_id")!=taskid:
        return {"status":"HOLD","task_id":taskid,"error":"RECEIPT_INTEGRITY_MISMATCH"}
    request_path=MAILBOX/"requests"/(taskid+".json")
    if not request_path.is_file():
        return {"status":"HOLD","task_id":taskid,"error":"REQUEST_MISSING_FOR_RECEIPT"}
    request=load(request_path)
    if validate(request) is not None or request["payload_sha256"]!=data.get("request_hash"):
        return {"status":"HOLD","task_id":taskid,"error":"REQUEST_RECEIPT_CHAIN_MISMATCH"}
    return data
def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["stage","worker-once","poll","status"])
    p.add_argument("--actor",default="CAPABILITY_ATTEST")
    p.add_argument("--project",default="TAKY2")
    p.add_argument("--intent",default="Verify common TAKY context and capabilities")
    p.add_argument("--id",default="")
    p.add_argument("--context-delivery-id",default="")
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
