"""Single canonical Workbench task intake (before execution / verification).

Existing no-argument bootstrap remains unchanged. --intake only updates the
existing TASK_REGISTER, never creates a parallel queue or calls a model.
"""
from pathlib import Path
import json
import argparse
import hashlib
import os
import re
import sys
import tempfile

REGISTRY_ROOT = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
CANONICAL_BOARD = REGISTRY_ROOT / "01_BACKLOG_AND_ADOPTION" / "70_EXECUTION_QUEUE" / "TASK_REGISTER.json"
PROJECTS = REGISTRY_ROOT / "00_CONTROL" / "PROJECT_REGISTRY.json"


def _intake(args):
    path=CANONICAL_BOARD if not args.test_task_register else Path(args.test_task_register).resolve()
    if args.test_task_register:
        sandbox=Path(tempfile.gettempdir()).resolve()
        if path.name!="TASK_REGISTER.json" or sandbox not in path.parents:
            raise ValueError("TEST_REGISTRY_OUTSIDE_TEMP_BLOCKED")
    registry=json.loads(PROJECTS.read_text(encoding="utf-8-sig"))
    projects=registry.get("projects",{})
    if args.project not in projects:
        raise ValueError("WORK_PROJECT_NOT_REGISTERED")
    base=Path(projects[args.project]["source_repo"]).resolve(strict=True)
    if not (base/".git").exists():
        raise ValueError("WORK_PROJECT_SOURCE_REPO_UNAVAILABLE")
    if not args.title or len(args.title)>240 or any(ord(c)<32 for c in args.title):
        raise ValueError("WORK_TITLE_INVALID")
    if not re.fullmatch(r"[A-Z][A-Z0-9_-]{1,31}",args.category):
        raise ValueError("WORK_CATEGORY_INVALID")
    if args.request_key and not re.fullmatch(r"[A-Za-z0-9._:-]{8,150}",args.request_key):
        raise ValueError("WORK_REQUEST_KEY_INVALID")
    sources=[]
    for rel in args.source or []:
        if (not re.fullmatch(r"[\w .()/-]+",rel)
                or rel.startswith("/") or "\\" in rel
                or any(x in ("", ".", "..") for x in rel.split("/"))):
            raise ValueError("WORK_SOURCE_PATH_INVALID")
        item=(base/rel).resolve(strict=True)
        if (base not in item.parents or not item.is_file()
                or item.is_symlink() or len(sources)>=20 or item.stat().st_size>4_000_000):
            raise ValueError("WORK_SOURCE_OUTSIDE_REPO_OR_NOT_REGULAR")
        sources.append({"path":str(item),"sha256":hashlib.sha256(item.read_bytes()).hexdigest()})
    if len({x["path"] for x in sources})!=len(sources):
        raise ValueError("WORK_DUPLICATE_SOURCE")
    request_key=args.request_key or (args.project+":"+re.sub(r"\s+"," ",args.title.strip()).casefold())
    preimage=path.read_bytes()
    doc=json.loads(preimage.decode("utf-8-sig"))
    if doc.get("schema")!="TAKY_WORKBENCH_BACKLOG_V1" or not isinstance(doc.get("tasks"),list):
        raise ValueError("WORK_CANONICAL_BOARD_INVALID")
    tasks=doc["tasks"]
    ids=[x.get("id") for x in tasks]
    if len(ids)!=len(set(ids)):
        raise ValueError("WORK_DUPLICATE_EXISTING_ID_HOLD")

    if args.parent_work_id:
        if args.parent_work_id not in ids or args.parent_work_id==args.existing_id:
            raise ValueError("WORK_PARENT_ID_INVALID_OR_NOT_REGISTERED")

    if args.existing_id:
        matches=[x for x in tasks if x["id"]==args.existing_id]
        if len(matches)!=1:
            raise ValueError("WORK_EXISTING_ID_NOT_FOUND")
        row=matches[0]
        intake=row.get("intake",{})
        if intake and intake.get("project")!=args.project:
            raise ValueError("WORK_EXISTING_ID_PROJECT_CONFLICT")
        if not intake:
            # Older IDs were registered before project ownership metadata.
            # Do not let --existing-id attach a task from another application
            # just because the user supplied a valid-looking ID.
            current_file=REGISTRY_ROOT/"10_PROJECTS"/args.project/"PROJECT_CURRENT.json"
            current=json.loads(current_file.read_text(encoding="utf-8-sig"))
            repo_path=str(base).casefold().rstrip("\\") + "\\"
            owned=(current.get("current_work_id")==row["id"] or
                   any(isinstance(ref,str) and ref.casefold().startswith(repo_path)
                       for ref in row.get("evidence",[])))
            if not owned:
                raise ValueError("WORK_LEGACY_PROJECT_OWNERSHIP_UNVERIFIED")
        if row.get("status") in ("REJECTED","ADOPTED"):
            raise ValueError("WORK_EXISTING_ID_CLOSED")
        if args.parent_work_id and row.get("parent_work_id")!=args.parent_work_id:
            raise ValueError("WORK_EXISTING_PARENT_MISMATCH")
        status="EXISTING_WORK_ID_REUSED"
    else:
        key_matches=[x for x in tasks if
                     x.get("intake",{}).get("request_key")==request_key]
        if key_matches:
            row=key_matches[0]
            if (row.get("intake",{}).get("project")!=args.project or
                    row.get("title")!=args.title):
                raise ValueError("WORK_REQUEST_KEY_REUSED_FOR_DIFFERENT_TASK_HOLD")
            if args.parent_work_id and row.get("parent_work_id")!=args.parent_work_id:
                raise ValueError("WORK_EXISTING_PARENT_MISMATCH")
            status="EXISTING_WORK_ID_REUSED"
        else:
            exact=[x for x in tasks if
                   re.sub(r"\s+"," ",x.get("title","").strip()).casefold()==
                   re.sub(r"\s+"," ",args.title.strip()).casefold() and
                   (not x.get("intake") or x["intake"].get("project")==args.project)]
            if exact:
                raise ValueError("WORK_EXISTING_TITLE_AMBIGUOUS_REUSE_EXPLICIT_ID")
            prefix=re.sub(r"[^A-Z0-9-]","-",args.project.upper()).strip("-")
            nums=[int(x[len(prefix)+1:]) for x in ids if isinstance(x,str) and
                  re.fullmatch(re.escape(prefix)+r"-[0-9]{3,6}",x)]
            work_id=prefix+"-"+str(max(nums,default=0)+1).zfill(3)
            row={"id":work_id,"category":args.category,"title":args.title,
                 "priority":args.priority,"dependencies":[],
                 "phase":"INTAKE","status":"DISCOVERY","owner":"TAKY_ORCHESTRATOR",
                 "approval_required":False,"evidence":[],
                 "decision":"INTAKE_CLASSIFIED_NOT_EXECUTED",
                 "intake":{"project":args.project,"request_key":request_key},
                 "planned_source_bindings":[]}
            if args.parent_work_id:
                # Related work is classified under its parent at intake, but
                # grouping does NOT incorrectly require the parent to be DONE.
                row["parent_work_id"]=args.parent_work_id
            status="WORK_ID_ASSIGNED_AT_INTAKE"
            tasks.append(row)
    # Linking a known source is not an implementation, test, or DONE proof.
    if sources:
        existing={x["path"]:x for x in row.get("planned_source_bindings",[])}
        for src in sources:
            existing[src["path"]]=src
        row["planned_source_bindings"]=sorted(existing.values(),key=lambda x:x["path"])
        row.setdefault("intake",{"project":args.project,"request_key":request_key})
    changed=status=="WORK_ID_ASSIGNED_AT_INTAKE" or bool(sources)
    if changed and not args.dry_run:
        # Guarded single-writer update. No blind overwrite of a concurrently
        # replaced registry: the index is the only authority.
        import msvcrt
        lock=path.with_name("TASK_REGISTER.intake.lock")
        with lock.open("a+b") as handle:
            handle.seek(0)
            if not handle.read(1):
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_LOCK,1)
            try:
                fresh=json.loads(path.read_text(encoding="utf-8-sig"))
                # Do not silently override another writer. Rerun classification.
                original_ids=[x["id"] for x in fresh["tasks"]]
                if original_ids!=ids or len(fresh["tasks"])!=len(ids):
                    raise RuntimeError("WORK_REGISTRY_CONCURRENT_CHANGE_HOLD")
                # Ensure no concurrent source/approval/status edits.
                if path.read_bytes()!=preimage:
                    raise RuntimeError("WORK_REGISTRY_CHANGED_HOLD")
                data=(json.dumps(doc,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
                tmp=path.with_name(path.name+".work-intake.tmp")
                if tmp.exists():
                    raise RuntimeError("WORK_INTAKE_TEMP_COLLISION_HOLD")
                with tmp.open("xb") as f:
                    f.write(data);f.flush();os.fsync(f.fileno())
                os.replace(tmp,path)
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
        verify=json.loads(path.read_text(encoding="utf-8-sig"))
        if [x["id"] for x in verify["tasks"]].count(row["id"])!=1:
            raise RuntimeError("WORK_INTAKE_READBACK_FAILED")
    print(json.dumps({"work_id":row["id"],"status":status,
                      "classified_project":args.project,
                      "parent_work_id":row.get("parent_work_id"),
                      "task_state":row["status"],
                      "planned_source_bindings":len(row.get("planned_source_bindings",[])),
                      "implementation_verified":False,
                      "model_called":False,"done_issued":False,
                      "dry_run":args.dry_run},ensure_ascii=False))
    return 0


if "--intake" in sys.argv:
    parser=argparse.ArgumentParser(description="Assign/reuse Work ID BEFORE implementation")
    parser.add_argument("--intake",action="store_true")
    parser.add_argument("--project",required=True)
    parser.add_argument("--title",required=True)
    parser.add_argument("--category",default="INTEGRATION")
    parser.add_argument("--priority",choices=["P0","P1","P2"],default="P1")
    parser.add_argument("--request-key")
    parser.add_argument("--existing-id")
    parser.add_argument("--parent-work-id")
    parser.add_argument("--source",action="append")
    parser.add_argument("--test-task-register")
    parser.add_argument("--dry-run",action="store_true")
    sys.exit(_intake(parser.parse_args()))

from pathlib import Path
import json
root=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
base=root/"01_BACKLOG_AND_ADOPTION"
for folder in ["00_INBOX","10_POST_CLEANUP","20_MCP","30_SKILLS","40_TOOLS","50_INTEGRATION","60_DECISIONS","70_EXECUTION_QUEUE","80_EVIDENCE","90_DONE"]:
 (base/folder).mkdir(parents=True,exist_ok=True)
items=[
 ("CLN-001","POST_CLEANUP","Inventory duplicate folders, retired paths, live Git worktrees and external references","P0",["filesystem-inventory","path-registry"],"AFTER_CLEANUP"),
 ("CLN-002","POST_CLEANUP","Verify canonical CURRENT, owner and archived revisions without duplicates","P0",["CLN-001"],"AFTER_CLEANUP"),
 ("MCP-001","MCP","Audit connected MCP inventory and effective permissions; avoid installing redundant tools","P1",["CLN-001"],"ASSESS"),
 ("MCP-002","MCP","Verify Remote Desktop Commander paths, shell reliability and CPU limits","P0",["CLN-001"],"ASSESS"),
 ("MCP-003","MCP","Check Drive and GitHub connector access vs local source authority; minimize remote calls","P1",["MCP-001"],"ASSESS"),
 ("SKL-001","SKILLS","Catalog Claude and Codex skills; trigger rules, compatibility and necessity gate","P1",["CLN-001"],"ASSESS"),
 ("SKL-002","SKILLS","Evaluate Agent Reach and Graft only after directory cleanup; record exact utility and adoption decision","P2",["CLN-001"],"AFTER_CLEANUP"),
 ("INT-001","INTEGRATION","Connect WORK_ID task manifests with shared GPT Claude Codex handoffs","P0",["CLN-002"],"IMPLEMENT"),
 ("INT-002","INTEGRATION","Bind UI gallery to real approval evidence, Visual ID and app screen state","P0",["CLN-002"],"IMPLEMENT"),
 ("INT-003","INTEGRATION","Bind script, pronunciation, voice samples, approvals and runtime audio events","P0",["CLN-002"],"IMPLEMENT"),
 ("GATE-001","INTEGRATION","Enforce no GitHub push, Netlify deploy or paid API without explicit approval","P0",["INT-001"],"IMPLEMENT"),
 ("OPS-001","TOOLS","After cleanup, audit observer and local collector stage coverage and rate/CPU limits","P0",["CLN-001"],"ASSESS")
]
path=base/"70_EXECUTION_QUEUE"/"TASK_REGISTER.json"
if not path.exists():
 data={"schema":"TAKY_WORKBENCH_BACKLOG_V1","authority":"TAKY/CURRENT","tasks":[{"id":i,"category":c,"title":t,"priority":pr,"dependencies":dep,"phase":phase,"status":"NOT_STARTED","owner":"UNASSIGNED","approval_required":False,"evidence":[],"decision":"UNDECIDED"} for i,c,t,pr,dep,phase in items],"states":["NOT_STARTED","DISCOVERY","EVALUATION","READY","IMPLEMENTING","VERIFIED","ADOPTED","REJECTED","BLOCKED"]}
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
readme=base/"README.md"
readme.write_text("""# TAKY WORKBENCH - Adoption & Backlog (top level)
This is the single entry for after-cleanup adoption of MCP, skills, tools and pending work.
- 00_INBOX: untriaged suggestions (not yet accepted)
- 10_POST_CLEANUP: cleanup closing conditions and baseline
- 20_MCP / 30_SKILLS / 40_TOOLS: suitability evaluations, not auto installation
- 50_INTEGRATION: integration plans
- 60_DECISIONS: ACCEPT / HOLD / REJECT decisions, with provenance
- 70_EXECUTION_QUEUE/TASK_REGISTER.json: authoritative work queue within this workspace
- 80_EVIDENCE: verification results
- 90_DONE: closed-task references

Hard gates: necessity before call; no paid API, plugin install, GitHub push or Netlify deploy without user authorization. No MCP or skill is considered installed merely by being listed. Dependencies must be verified. After folder cleanup, promote only evidenced items; do not blindly install all candidates.
""",encoding="utf-8")
print(json.dumps({"path":str(base),"tasks":len(json.loads(path.read_text(encoding="utf-8"))["tasks"]),"folders":10},ensure_ascii=False))
