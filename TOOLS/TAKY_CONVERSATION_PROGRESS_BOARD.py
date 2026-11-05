#!/usr/bin/env python3
"""Evidence-grounded progress console for TAKY's EXISTING Workbench.

Reads existing CHAT/TOPIC projection, October relay + orchestration receipts,
project current, AI assignments and prepared task titles. Does not alter inputs,
CURRENT, code repositories, deployment, or misrepresent native chat coverage.
Local derived JSON and self-contained HTML only. Rerunnable / content readback.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import html
import json
import os
import re
import subprocess
from pathlib import Path
from datetime import datetime,timezone
from TAKY_CONVERSATION_VIEW_READBACK import guarded_write

ROOT=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
CONTROL=ROOT/"00_CONTROL"
OUT=CONTROL/"TAKY_CONVERSATION_PROGRESS_INDEX.json"
HTML=CONTROL/"TAKY_CONVERSATION_PROGRESS_BOARD.html"
PORTFOLIO_REL=Path("01_BACKLOG_AND_ADOPTION")/"70_EXECUTION_QUEUE"/"TASK_REGISTER.json"
INPUTS={"projects":CONTROL/"PROJECT_REGISTRY.json",
        "assignments":CONTROL/"AI_WORK_ASSIGNMENTS.json",
        "september":CONTROL/"CONVERSATION_TOPIC_OVERVIEW.json",
        "october":CONTROL/"OCTOBER_CONVERSATION_EVIDENCE_INDEX.json",
        "oct_native":CONTROL/"CONVERSATION_2026_10_ONWARD_TOPIC_INDEX.json"}
SAFE_STATUSES={"OPEN","IN_PROGRESS","REVIEW","USER_APPROVAL_REQUIRED",
               "APPROVED","PROMOTION_READY","PROMOTED","BLOCKED"}
def sha(b:bytes):return hashlib.sha256(b).hexdigest()
def read(p:Path):return json.loads(p.read_text(encoding="utf-8-sig"))
def ref_summary(paths:list[str])->list[dict]:
    out=[]
    for p in paths:
        try:
            q=Path(p)
            present=q.is_file()
            out.append({"path":str(p),"exists":present,
                        "size":q.stat().st_size if present else None})
        except (OSError,ValueError):
            out.append({"path":str(p),"exists":False,"size":None})
    return out
def inspect_repo(repo_path:str)->dict:
    """Read-only git signals. A commit is NOT proof of current-task completion."""
    path=Path(repo_path)
    if not path.is_dir():
        return {"probe":"SOURCE_PATH_NOT_FOUND","commit":None,"branch":None,
                "head_date":None,"tracked_changes":None,
                "meaning":"REPO_PATH_MISSING_NOT_PROJECT_ABANDONED"}
    try:
        cmd=["git","-C",str(path)]
        def call(args):
            r=subprocess.run(cmd+args,capture_output=True,text=True,encoding="utf-8",
                             errors="replace",timeout=6,check=False,
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if r.returncode!=0:raise RuntimeError("GIT_READ_FAILED")
            return r.stdout.strip()
        commit=call(["log","-1","--format=%H|%cI|%s"]).split("|",2)
        if len(commit)!=3:raise ValueError("GIT_COMMIT_FORMAT")
        branch=call(["rev-parse","--abbrev-ref","HEAD"])
        changed=call(["status","--porcelain","-uno"])
        return {"probe":"READ_ONLY_GIT_METADATA","commit":commit[0],
                "head_date":commit[1],"commit_subject":commit[2][:160],
                "branch":branch,"tracked_changes":len(changed.splitlines()) if changed else 0,
                "meaning":"GIT_ACTIVITY_ONLY_NOT_PROJECT_QA_OR_USER_APPROVAL"}
    except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired):
        return {"probe":"GIT_PROBE_UNAVAILABLE","commit":None,"branch":None,
                "head_date":None,"tracked_changes":None,
                "meaning":"SOURCE_REPO_STATE_NOT_VERIFIED"}

def load_portfolio(path:Path)->dict:
    """Read-only portfolio registry (a DIFFERENT registry from AI assignments).
    Fail closed: missing/corrupt/empty/duplicate ids raise, never a silent 0."""
    try:
        raw=path.read_bytes()
        doc=json.loads(raw.decode("utf-8-sig"))
    except (OSError,ValueError) as e:
        raise ValueError("PORTFOLIO_REGISTRY_UNREADABLE") from e
    tasks=doc.get("tasks") if isinstance(doc,dict) else None
    if not isinstance(tasks,list) or not tasks:raise ValueError("PORTFOLIO_REGISTRY_INVALID")
    ids=[t.get("id") if isinstance(t,dict) else None for t in tasks]
    if any(not isinstance(x,str) or not x for x in ids) or len(set(ids))!=len(ids):
        raise ValueError("PORTFOLIO_REGISTRY_INVALID_IDS")
    return {"path":str(path),"sha256":sha(raw),"ids":set(ids),"count":len(ids),
            "statuses":dict(sorted(collections.Counter(
                str(t.get("status") or "UNKNOWN") for t in tasks).items()))}
def load_task(a:dict)->dict:
    # Titles are extracted from own registered input artifact, not generated from
    # conversation guesses. Never embed raw task file bytes in the viewer.
    result={"title":None,"prepared_state":None,"title_source":None}
    for source in a.get("input_refs",[]):
        try:
            p=Path(source)
            if not p.is_file() or p.suffix.lower()!=".json":continue
            task=read(p)
            if task.get("id")!=a.get("task_id"):continue
            s=task.get("task")
            if isinstance(s,str) and s.strip():
                result={"title":s.strip()[:350],"prepared_state":task.get("state"),
                        "title_source":str(p)}
                return result
        except (OSError,ValueError,json.JSONDecodeError):continue
    return result
def derive(inputs:dict, currents:dict, task_titles:dict|None=None, repo_metadata=None, source_manifest=None, portfolio=None):
    projects=inputs["projects"]["projects"]
    assignments=inputs["assignments"]["tasks"]
    sep=inputs["september"]
    octo=inputs["october"]
    native=inputs["oct_native"]
    if not isinstance(projects,dict) or not isinstance(assignments,list):
        raise ValueError("INVALID_WORKBENCH_INPUT")
    if octo.get("account_wide_chat_coverage_verified") is not False:
        raise ValueError("OCTOBER_NATIVE_COVERAGE_UNVERIFIED")
    if native.get("account_wide_coverage_verified") is True:raise ValueError("INVALID_FULL_COVERAGE")
    if sep.get("archive_source_count")!=25:raise ValueError("HISTORICAL_SOURCE_SCOPE_DRIFT")
    aid=[t.get("work_id") for t in assignments]
    if len(set(aid))!=len(aid) or any(not x for x in aid):raise ValueError("DUPLICATE_OR_MISSING_WORK_ID")
    by_work=collections.defaultdict(list)
    for receipt in octo["records"]:
        if receipt.get("source")!="TAKY_CHAT_ORCH_V1":continue
        key=receipt.get("work_id")
        if key and receipt.get("work_id_evidence")=="EXPLICIT_WORK_ID":
            by_work[key].append(receipt)
    by_project=collections.defaultdict(list)
    rows=[]
    for a in assignments:
        work_id=a["work_id"]
        proj=next((k for k,v in projects.items()
                   if str(v.get("source_repo","")).casefold().replace("\\","/").rstrip("/")
                   ==str(a.get("project","")).casefold().replace("\\","/").rstrip("/")),None)
        receipts=sorted(by_work.get(work_id,[]),key=lambda r:(str(r.get("when") or ""),r.get("record_id","")))
        status=str(a.get("status") or "UNKNOWN")
        if status not in SAFE_STATUSES:status="UNRECOGNIZED:"+status
        prep=(task_titles or {}).get(work_id) or load_task(a)
        evidence=ref_summary(a.get("evidence_refs") or [])
        outputs=ref_summary(a.get("output_refs") or [])
        real_statuses=[str(r.get("reported_status") or "UNKNOWN") for r in receipts]
        flags=[]
        flags.append("INDEPENDENT_EXECUTION_VERIFICATION_MISSING")
        if a.get("execution_verified") is True:flags.append("REGISTRY_VERIFICATION_CLAIM_REQUIRES_PROOF")
        if a.get("reviewer") in ("UNASSIGNED",None,""):flags.append("REVIEWER_UNASSIGNED")
        if not outputs:flags.append("NO_OUTPUT_REGISTERED")
        if not receipts:flags.append("NO_OCTOBER_RECEIPT_LINKED")
        if status=="BLOCKED":flags.append("REGISTRY_BLOCKED")
        if any(x in ("ERROR","FAILED","HOLD","OUTCOME_UNKNOWN","COMPLETE_UNVERIFIED",
                     "APPLIED_UNVERIFIED","PREPARED_NOT_EXECUTED") for x in real_statuses):
            flags.append("NON_SUCCESS_OR_UNVERIFIED_RECEIPT_PRESENT")
        if not proj:flags.append("PROJECT_REPO_NOT_IN_REGISTRY")
        row={"work_id":work_id,"project":proj or "UNREGISTERED_PROJECT",
             "task_id":a.get("task_id"),"portfolio_task_id":a.get("portfolio_task_id"),
             "title":prep.get("title") or "작업명 원문 미확보",
             "title_source":prep.get("title_source"),
             "prepared_state":prep.get("prepared_state"),
             "registry_status":status,"executor":a.get("executor") or "UNASSIGNED",
             "reviewer":a.get("reviewer") or "UNASSIGNED",
             "output_refs":outputs,"evidence_refs":evidence,
             "input_refs":ref_summary(a.get("input_refs") or []),
             "receipts":[{"when":r.get("when"),"reported_status":r.get("reported_status"),
                          "record_id":r.get("record_id"),"source_ref":r.get("source_ref"),
                          "action":r.get("action"),"model_called":r.get("model_called")}
                         for r in receipts],
             "receipt_count":len(receipts),
             "latest_receipt":receipts[-1].get("reported_status") if receipts else None,
             "last_observed":receipts[-1].get("when") if receipts else None,
             "execution_verified":False,
             "registry_verification_claim":a.get("execution_verified") is True,
             "verification_status":"INDEPENDENT_RUNTIME_QA_NOT_ATTESTED",
             "chat_source_link":"NOT_PROVEN", "issues":flags,
             "state_basis":"REGISTRY_PLUS_RECEIPT_CLAIMS_NOT_INDEPENDENT_COMPLETION"}
        rows.append(row);by_project[row["project"]].append(row)
    historical=collections.defaultdict(list)
    topics={t["topic_id"]:t for t in sep["topics"]}
    for c in sep["chats"]:
        for topic_id in c.get("topics",[]):
            topic=topics.get(topic_id)
            if topic and topic.get("project"):
                historical[topic["project"]].append({"chat_id":c["chat_id"],
                    "title":" · ".join(c.get("titles") or []),"topic":topic.get("name"),
                    "messages":c.get("messages"),"original_urls":c.get("source_urls") or [],
                    "source_scope":"HISTORICAL_2026_09_CANDIDATE"})
    for k in historical:
        seen=set();historical[k]=[r for r in historical[k]
            if not ((r["chat_id"],r["topic"]) in seen or seen.add((r["chat_id"],r["topic"])))]

    relay_by_project=collections.defaultdict(list)
    for r in octo["records"]:
        if r.get("source")!="AI_SHARED_CHAT_LOG_2026-10":continue
        for t in r.get("topic_candidates",[]):
            relay_by_project[t["project"]].append({"when":r.get("when"),"event_id":r.get("event_id"),
                 "task_id":r.get("task_id"),"reported_status":r.get("reported_status"),
                 "kind":r.get("event_kind"),"source_ref":r.get("source_ref"),
                 "source_scope":"OCTOBER_RELAY_TOPIC_CANDIDATE_NOT_NATIVE_CHAT"})

    projects_out=[];alerts=[]
    for k,v in projects.items():
        curr=currents.get(k) or {}
        tasks=by_project[k]
        # A PROJECT_CURRENT may explicitly name its own work ID without an
        # AI assignment. Preserve this as an evidenced but UNREGISTERED link;
        # never fabricate a TAKY-CHAT ID or create an assignment from it.
        declared_id=curr.get("current_work_id")
        if not isinstance(declared_id,str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{3,90}",declared_id) or curr.get("project")!=k:
            declared_id=None
        registered_ids_for_project={t["work_id"] for t in tasks}
        # Portfolio registry is a separate registry from AI assignments.
        # portfolio=None (older callers) keeps the original two-state logic.
        in_portfolio=(declared_id in portfolio["ids"]) if portfolio and declared_id else None
        ai_assigned=declared_id in registered_ids_for_project if declared_id else None
        if declared_id in registered_ids_for_project:reg_state="CURRENT_DECLARED_REGISTERED"
        elif declared_id and in_portfolio:reg_state="CURRENT_DECLARED_PORTFOLIO_REGISTERED_NOT_AI_ASSIGNED"
        elif declared_id:reg_state="CURRENT_DECLARED_UNREGISTERED"
        else:reg_state="NO_CURRENT_WORK_ID"
        current_work_link={
            "id":declared_id,
            "source":"PROJECT_CURRENT_EXPLICIT_FIELD" if declared_id else "NOT_DECLARED",
            "registration":reg_state,
            "portfolio_registered":in_portfolio if portfolio else "UNKNOWN",
            "ai_assigned":ai_assigned,
            "registration_note":"portfolio registered; not AI-assigned; outcome not independently verified"
                           if reg_state=="CURRENT_DECLARED_PORTFOLIO_REGISTERED_NOT_AI_ASSIGNED" else None,
            "outcome_verified":False,
            "scope":str(curr.get("result_scope") or "")[:180] if declared_id else None,
            "pending_gate_count":len(curr.get("pending_gates") or [])
                                 if isinstance(curr.get("pending_gates"),list) else 0,
            "declared_output_count":len(curr.get("output_refs") or [])
                                 if isinstance(curr.get("output_refs"),list) else 0,
        }
        statuses=dict(sorted(collections.Counter(t["registry_status"] for t in tasks).items()))
        important=(sum(t["registry_status"]=="BLOCKED" for t in tasks),
                   sum(t["registry_status"]=="REVIEW" for t in tasks),
                   sum(t["registry_status"]=="OPEN" for t in tasks))
        registered=v.get("status","UNKNOWN")
        current=curr.get("status","MISSING")
        repo=(repo_metadata or {}).get(k) or {"probe":"NOT_CHECKED"}
        # Local source changes are evidence of unregistered WIP, NOT evidence
        # of a finished task, a verified deployment, or CURRENT promotion.
        tracked=repo.get("tracked_changes")
        has_local_wip=(repo.get("probe")=="READ_ONLY_GIT_METADATA"
                       and isinstance(tracked,int) and tracked>0)
        if important[0]:signal="BLOCKED_TASK_RECORDED"
        elif important[1]:signal="REVIEW_TASK_RECORDED"
        elif important[2]:signal="OPEN_TASK_RECORDED"
        elif has_local_wip:signal="LOCAL_TRACKED_WIP_OBSERVED_NOT_TASK_COMPLETION"
        elif repo.get("probe")=="READ_ONLY_GIT_METADATA":signal="REPO_COMMIT_OBSERVED_NOT_COMPLETION"
        else:signal="NO_VERIFIED_PROGRESS_SIGNAL"
        issues=[]
        if (registered=="IDLE" or current=="IDLE") and tasks:
            issues.append("IDLE_REGISTRY_WITH_REGISTERED_WORK_RECHECK")
        if not tasks:issues.append("NO_PROJECT_BOUND_WORK_IN_AI_ASSIGNMENTS")
        if reg_state=="CURRENT_DECLARED_PORTFOLIO_REGISTERED_NOT_AI_ASSIGNED":
            issues.append("CURRENT_WORK_PORTFOLIO_REGISTERED_NOT_AI_ASSIGNED")
        if reg_state=="CURRENT_DECLARED_UNREGISTERED":
            issues.append("CURRENT_WORK_NOT_IN_AI_ASSIGNMENTS")
            alerts.append({"type":"EXPLICIT_PROJECT_CURRENT_WORK_NOT_REGISTERED",
                "project":k,"work_id":declared_id,
                "reason":"EXACT_PROJECT_CURRENT_ID_ABSENT_FROM_PORTFOLIO_AND_AI_ASSIGNMENTS"
                         if portfolio else "EXACT_PROJECT_CURRENT_ID_WITHOUT_MATCHING_AI_ASSIGNMENT",
                "action":"RECONCILE_EXISTING_WORK_CONTRACT_NO_AUTOMATIC_REGISTRATION"})
        if has_local_wip and not tasks:
            issues.append("LOCAL_CODE_WIP_WITHOUT_REGISTERED_AI_WORK")
        if has_local_wip and (registered=="IDLE" or current=="IDLE"):
            issues.append("REGISTRY_IDLE_WITH_LOCAL_CODE_WIP")
        if k not in currents:issues.append("PROJECT_CURRENT_MISSING")
        if tasks and not any(t["execution_verified"] for t in tasks):
            issues.append("NO_VERIFIED_TASK_COMPLETION")
        recency=max([t["last_observed"] for t in tasks if t["last_observed"]],default=None)
        if has_local_wip and not tasks:
            alerts.append({"type":"PROJECT_LOCAL_WIP_UNBOUND_TO_AI_WORK",
                "project":k,"reason":"TRACKED_GIT_CHANGE_BUT_NO_REGISTERED_AI_TASK",
                "action":"RECOVER_SOURCE_BOUND_TASK_LINK_NO_COMPLETION_INFERENCE"})
        if issues and "IDLE_REGISTRY_WITH_REGISTERED_WORK_RECHECK" in issues:
            alerts.append({"type":"PROJECT_STATUS_DRIFT_CANDIDATE",
                "project":k,"work_ids":[t["work_id"] for t in tasks],
                "reason":"IDLE_REGISTERED_WITH_WORK_EVIDENCE",
                "action":"CHECK_PROJECT_CURRENT_AND_EXECUTION_RUNTIME_BEFORE_CHANGING_STATE"})
        projects_out.append({"project":k,"registry_status":registered,"current_status":current,
            "repo_evidence":repo,
            "current_work_id":curr.get("current_work_id"),"source_repo":v.get("source_repo"),
            "workbench_ref":v.get("workbench_path"),"progress_signal":signal,
            "local_activity":{"tracked_wip_observed":has_local_wip,
                              "tracked_changed_files":tracked if has_local_wip else 0,
                              "untracked_files_coverage":"NOT_COUNTED",
                              "execution_verified":False,
                              "meaning":"LOCAL_CODE_ACTIVITY_NOT_COMPLETED_TASK"},
            "work_registration_gap":bool(has_local_wip and not tasks),
            "current_work_link":current_work_link,
            "work_count":len(tasks),"work_statuses":statuses,
            "work_ids":[t["work_id"] for t in tasks],
            "historical_chats":historical[k],"relay_events":relay_by_project[k],
            "last_observed_work_receipt":recency,
            "flags":issues,"progress_percent":None,
            "authority":"WORKBENCH_READ_ONLY_DERIVED_NOT_PROJECT_CANONICAL"})
    registered_ids=set(aid)
    links=[p["current_work_link"] for p in projects_out if p["current_work_link"]["id"]]
    outside=sorted(set(by_work)-registered_ids)
    for w in outside:alerts.append({"type":"WORK_ID_NOT_IN_AI_ASSIGNMENTS",
        "work_id":w,"receipt_count":len(by_work[w]),"reason":"EXPLICIT_RECEIPT_WORK_ID_NOT_REGISTERED"})
    for w in rows:
        if w["registry_status"]=="BLOCKED":alerts.append({"type":"WORK_BLOCKED_IN_REGISTRY","work_id":w["work_id"],"project":w["project"]})
        if "NON_SUCCESS_OR_UNVERIFIED_RECEIPT_PRESENT" in w["issues"]:
            alerts.append({"type":"RECEIPT_CONTAINS_NON_SUCCESS_OR_UNVERIFIED_STATUS",
                           "work_id":w["work_id"],"project":w["project"]})
    for seq in octo.get("relay_duplicate_sequence_numbers",[]):
        alerts.append({"type":"DUPLICATE_RELAY_SEQUENCE","sequence":seq})
    return {"schema":"TAKY_CONVERSATION_PROGRESS_PROJECTION_V1",
        "authority":"DERIVED_VIEW_ONLY_NOT_CURRENT_OR_ACCEPTANCE",
        "source_scope":{"historical_archive":"25_2026_09_SHARED_CHATS",
                        "oct_native_chat_count":len(native.get("chats") or []),
                        "oct_native_source_limit":"ONLY_USER_PROVIDED_EXPORTS",
                        "oct_relay_evidence":octo.get("log_entries"),
                        "oct_execution_receipts":octo.get("execution_receipts"),
                        "chatgpt_account_total":"NOT_VERIFIED",
                        "portfolio_task_count":portfolio["count"] if portfolio else "NOT_CHECKED"},
        "counts":{"projects":len(projects_out),"registered_ai_work":len(rows),
                 "blocked":sum(x["registry_status"]=="BLOCKED" for x in rows),
                 "review":sum(x["registry_status"]=="REVIEW" for x in rows),
                 "open":sum(x["registry_status"]=="OPEN" for x in rows),
                 "independently_verified_completion":sum(x["execution_verified"] for x in rows),
                 "unregistered_work_ids_in_receipts":len(outside),
                 "status_review_alerts":len(alerts),
                 "projects_with_local_tracked_wip":
                    sum(p["local_activity"]["tracked_wip_observed"] for p in projects_out),
                 "projects_with_unbound_local_tracked_wip":
                    sum(p["work_registration_gap"] for p in projects_out),
                 "portfolio_tasks":portfolio["count"] if portfolio else None,
                 "ai_assignments":len(rows),
                 "project_current_in_portfolio":
                    sum(l["portfolio_registered"] is True for l in links) if portfolio else None,
                 "global_missing_current_work":
                    sum(l["registration"]=="CURRENT_DECLARED_UNREGISTERED" for l in links) if portfolio else None,
                 "current_not_ai_assigned":sum(l["ai_assigned"] is False for l in links),
                 "projects_with_explicit_current_unregistered_work":
                    sum(p["current_work_link"]["registration"] ==
                        "CURRENT_DECLARED_UNREGISTERED" for p in projects_out)},
        "projects":projects_out,"work_items":rows,
        "unregistered_receipt_work_ids":outside,
        "alerts":alerts,
        "portfolio_registry":({k:portfolio[k] for k in ("path","sha256","count","statuses")}
                              if portfolio else None),
        "source_manifest":source_manifest or [],
        "verified_claims_excluded":["SUCCESS_FROM_PASS","PERCENT_FROM_FILE_COUNT",
                                   "GENERAL_CHAT_FROM_RELAY","PROJECT_IDLE_MEANS_NO_WORK"],
        "safe_to_publish_to_public_app":False,
        "no_git_push_or_deployment":True}
def write_if_changed(path:Path,text:str):
    if path.exists() and path.read_text(encoding="utf-8")==text:return False
    tmp=path.with_name(path.name+".progress-tmp")
    try:
        tmp.write_text(text,encoding="utf-8")
        try:
            os.replace(tmp,path)
        except PermissionError:
            # Windows sometimes denies rename-over-open while permitting an
            # in-place update. Use the established SHA-backed rollback guard.
            rollback=CONTROL/"CHAT_INGEST"/"REVIEW"/"_rollback_previous_derived"
            rollback.mkdir(exist_ok=True,parents=True)
            guarded_write(path,text.encode("utf-8"),rollback/path.name)
    finally:
        tmp.unlink(missing_ok=True)
    if path.read_text(encoding="utf-8")!=text:raise RuntimeError("READBACK_MISMATCH")
    return True

def build_page(data:dict):
    # Embed safe bounded metadata as JSON; DOM rendering uses textContent only.
    payload=json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    return r'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TAKY 작업·대화 통합 진행 관제</title>
<style>
:root{color-scheme:dark;--bg:#081320;--paper:#102239;--line:#29435f;--soft:#a7bad0;--text:#e9f1fb;--accent:#79b8ff;--note:#f1c795}
*{box-sizing:border-box}body{background:var(--bg);color:var(--text);font:14px/1.55 system-ui,-apple-system,"Malgun Gothic",sans-serif;margin:0}
main{max-width:1250px;margin:auto;padding:21px}h1{margin:0;font-size:24px;letter-spacing:-.8px}h2{font-size:18px;margin:25px 0 10px}h3{font-size:16px;margin:0 0 5px}
small,.muted{color:var(--soft)}.intro{color:var(--soft);margin:5px 0 20px}.notice{border-left:3px solid var(--note);padding:12px 15px;background:#192b41;border-radius:6px}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}.metric{background:#132b44;border:1px solid var(--line);border-radius:12px;padding:13px}.metric strong{display:block;font-size:24px}
.bar{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}.tab,.chip,button,select,input{font:inherit}.tab,.chip,button{border:1px solid #3b5879;background:#182e48;color:var(--text);border-radius:10px;padding:9px 12px;cursor:pointer}
.tab[aria-selected="true"],.chip[aria-pressed="true"]{background:#244d71;border-color:var(--accent)}
input,select{background:#0c1f34;color:var(--text);border:1px solid #45617f;border-radius:9px;padding:12px;min-height:43px}
.controls{display:flex;gap:9px;flex-wrap:wrap;margin:15px 0}.controls input{flex:1;min-width:205px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(265px,1fr));gap:12px}
.card{border:1px solid var(--line);background:var(--paper);padding:15px;border-radius:14px;overflow-wrap:anywhere}
.card button.choose{display:block;width:100%;text-align:left;border:0;background:transparent;padding:0;color:var(--text)}
.card .heading{display:flex;justify-content:space-between;gap:10px;align-items:start}.card p{margin:7px 0}.key{font:12px ui-monospace,Consolas,monospace;color:#aac5e6}
.label{color:var(--soft);font-size:12px}.pill{border:1px solid #405b79;border-radius:20px;padding:3px 8px;font-size:11px;white-space:nowrap}
.alert{border-left:3px solid #d0aa75}.active-card{outline:2px solid var(--accent)}
.panels{margin:16px 0}.panel{background:#0e2034;border:1px solid #2f4c68;border-radius:12px;padding:15px}
.kv{display:grid;grid-template-columns:minmax(100px,160px) 1fr;gap:5px 12px;margin:10px 0}.kv dt{color:var(--soft)}.kv dd{margin:0}
code{font:12px ui-monospace,Consolas,monospace;overflow-wrap:anywhere;color:#bcd8f1}
details{margin:12px 0;border-top:1px solid var(--line);padding-top:9px}summary{cursor:pointer;color:#acd3fb}
.list-row{border-bottom:1px solid var(--line);padding:10px 0}.list-row:last-child{border-bottom:0}
a{color:#9ed0ff;text-decoration:underline}a:hover{text-decoration:none}
.count{color:var(--soft);margin:5px 0 16px}[hidden]{display:none!important}
@media(max-width:600px){main{padding:13px}.controls>*{width:100%}.kv{grid-template-columns:1fr}}
</style></head><body><main>
<header><h1>TAKY / 통합 진행 관제</h1>
<p class="intro">프로젝트 · 대화 주제 · AI 담당 작업 · 실행 증거 · 충돌 검토</p>
<div class="notice">이 화면은 워크벤치 원자료의 조회 결과입니다. 10월 ChatGPT 일반 대화 원문은 아직 연결되지 않았습니다. 등록 상태·영수증·실제 검증을 혼동하지 않으며, 진행률 %를 추정하지 않습니다.</div></header>
<div id="metrics" class="metrics"></div>
<div class="bar" role="tablist" aria-label="관제 보기">
<button class="tab" data-tab="projects" role="tab" aria-selected="true">프로젝트</button>
<button class="tab" data-tab="work" role="tab" aria-selected="false">AI 작업·진행</button>
<button class="tab" data-tab="alerts" role="tab" aria-selected="false">중복·충돌 검토</button>
<button class="tab" data-tab="source" role="tab" aria-selected="false">자료 범위</button>
</div>
<div class="controls"><input id="search" aria-label="프로젝트 및 작업 검색" placeholder="프로젝트 · 작업명 · WORK_ID 검색">
<select id="status" aria-label="작업 상태"><option value="">모든 상태</option><option value="OPEN">OPEN</option><option value="REVIEW">REVIEW</option><option value="BLOCKED">BLOCKED</option><option value="IN_PROGRESS">IN_PROGRESS</option></select>
<button id="reset">필터 초기화</button></div>
<p id="count" class="count" aria-live="polite"></p>
<div id="projects"></div><div id="work" hidden></div><div id="alerts" hidden></div><div id="source" hidden></div>
<footer class="intro">실제 원문·CURRENT 수정 없음 · 로컬 전용 · 계정 전체 대화 검수 완료 주장 아님</footer>
<p><a href="TAKY_CONVERSATION_UNIFIED_VIEW.html">대화·주제별 원문 관제로 이동</a></p>
</main><script id="source-data" type="application/json">__DATA__</script><script>
"use strict";
const db=JSON.parse(document.getElementById("source-data").textContent), $=id=>document.getElementById(id);
let tab="projects", chosen="", query="", status="";
const text=(s)=>document.createTextNode(String(s??""));
function el(tag,cls,content){const e=document.createElement(tag);if(cls)e.className=cls;if(content!==undefined)e.append(text(content));return e}
function node(parent,child){parent.append(child);return child}
function attrs(e,o){for(const [k,v] of Object.entries(o))e.setAttribute(k,v);return e}
function row(parent,k,v){const dt=node(parent,el("dt","",k));node(parent,el("dd","",v==null?"확인되지 않음":v));return dt}
function details(parent,label,items,render){const d=node(parent,el("details"));node(d,el("summary","",label));const inner=node(d,el("div"));for(const item of items)render(inner,item);return d}
function metric(label,value){const e=node($("metrics"),el("div","metric"));node(e,el("small","",label));node(e,el("strong","",value))}
function addLink(parent,label,url){if(!/^https:\/\/(drive|docs)\.google\.com\//.test(url))return;const a=node(parent,el("a","",label));a.href=url;a.target="_blank";a.rel="noopener noreferrer"}
function chooseProject(k){chosen=chosen===k?"":k;tab="work";$("search").value="";query="";render()}
function projectCard(container,p){const e=node(container,el("article","card"+(chosen===p.project?" active-card":"")));
const b=node(e,el("button","choose"));const h=node(b,el("div","heading"));node(h,el("h3","",p.project));node(h,el("span","pill",
 p.work_count>0?"AI 작업 등록됨":
 p.local_activity?.tracked_wip_observed?"로컬 코드 변경 감지":
 p.progress_signal==="REPO_COMMIT_OBSERVED_NOT_COMPLETION"?"Git 커밋 기록만":"진행 미확인"));
node(e,el("p","label","등록 상태 "+p.registry_status+" / CURRENT "+p.current_status));
node(e,el("p","","등록된 AI 작업 "+p.work_count+"건 · 9월 주제 연관 대화 "+p.historical_chats.length+"건 · 10월 AI 전달 후보 "+p.relay_events.length+"건"));
if(p.current_work_link?.id){
 node(e,el("p","key","프로젝트 CURRENT 작업: "+p.current_work_link.id));
 node(e,el("p","muted",p.current_work_link.registration==="CURRENT_DECLARED_UNREGISTERED"
   ?(p.current_work_link.portfolio_registered==="UNKNOWN"
     ?"명시적 작업 ID 확보 · AI 작업 등록부 미연결 · 포트폴리오 미확인 · 완료 아님"
     :"명시적 작업 ID 확보 · 포트폴리오·AI 작업 등록부 모두 미연결 · 완료 아님")
   :p.current_work_link.registration==="CURRENT_DECLARED_PORTFOLIO_REGISTERED_NOT_AI_ASSIGNED"
   ?"포트폴리오 등록됨 · AI 미배정 · 결과 독립 검증 안 됨"
   :"명시적 작업 ID · AI 작업 등록부와 일치 · 완료 아님"));
 if(p.current_work_link.scope)node(e,el("p","muted","CURRENT 산출 범위: "+p.current_work_link.scope));
 node(e,el("p","muted","CURRENT 기재 산출물 "+p.current_work_link.declared_output_count+"건 · 미해결 게이트 "+p.current_work_link.pending_gate_count+"건"));
}
if(p.repo_evidence.probe==="READ_ONLY_GIT_METADATA"){
 node(e,el("p","muted","Git 최근 커밋: "+(p.repo_evidence.head_date||"")+" · 변경 추적 파일 "+p.repo_evidence.tracked_changes+"개 (실제 완료 의미 아님)"));
}else node(e,el("p","muted","코드 저장소 확인: "+p.repo_evidence.probe));
if(p.flags.length)node(e,el("p","muted","재검토: "+p.flags.map(x=>({IDLE_REGISTRY_WITH_REGISTERED_WORK_RECHECK:"IDLE와 작업기록 불일치",NO_PROJECT_BOUND_WORK_IN_AI_ASSIGNMENTS:"프로젝트 연결 AI 작업 없음",LOCAL_CODE_WIP_WITHOUT_REGISTERED_AI_WORK:"로컬 코드 변경이 AI 작업 등록부에 연결되지 않음",REGISTRY_IDLE_WITH_LOCAL_CODE_WIP:"IDLE 표시와 로컬 변경 흔적 불일치",CURRENT_WORK_NOT_IN_AI_ASSIGNMENTS:"CURRENT 작업 ID가 포트폴리오·AI 작업 등록부에 없음",CURRENT_WORK_PORTFOLIO_REGISTERED_NOT_AI_ASSIGNED:"포트폴리오 등록됨 · AI 미배정",NO_VERIFIED_TASK_COMPLETION:"검증 완료 작업 없음",PROJECT_CURRENT_MISSING:"CURRENT 파일 없음"}[x]||x)).join(" · ")));
b.onclick=()=>chooseProject(p.project);
details(e,"9월 원문 대화와 연결 후보",(p.historical_chats||[]).slice(0,30),(area,x)=>{
 const a=node(area,el("p","list-row",x.title+" — "+x.topic+" ("+x.messages+"건)"));
 for(const [i,url] of (x.original_urls||[]).entries())addLink(a,"원문 "+(i+1),url)
});
details(e,"10월 AI 인계 기록",(p.relay_events||[]).slice(0,50),(area,x)=>{
 node(area,el("p","list-row",(x.when||"일시 미확인")+" · "+(x.event_id||"")+" · "+(x.reported_status||"")))
});
}
function currentWorkCard(container,p){const c=p.current_work_link||{};if(c.registration!=="CURRENT_DECLARED_UNREGISTERED")return;
const e=node(container,el("article","card alert"));
node(e,el("h3","","PROJECT CURRENT / 포트폴리오·AI 작업 모두 미등록"));
node(e,el("p","key",c.id));
node(e,el("p","muted",p.project+" · 프로젝트 CURRENT의 명시적 ID, AI 실행·승인·완료 아님"));
if(c.scope)node(e,el("p","",c.scope));
node(e,el("p","muted","CURRENT 기재 산출물 "+c.declared_output_count+"건 · 미해결 게이트 "+c.pending_gate_count+"건"));
node(e,el("p","label","후속: 동일 작업 계약 확인 후 기존 AI 작업 등록부에 정확 연결. 새 WORK_ID 임의 생성 금지"));
}
function workCard(container,w){const e=node(container,el("article","card"));const h=node(e,el("div","heading"));node(h,el("h3","",w.title));node(h,el("span","pill",w.registry_status));
node(e,el("p","label",w.project+" / "+w.executor+" / 검토자 "+w.reviewer));
node(e,el("p","key",w.work_id));
node(e,el("p","","실행 증거 "+w.receipt_count+"건 · 등록 산출물 "+w.output_refs.length+"건 · 증거 참조 "+w.evidence_refs.length+"건"));
node(e,el("p","muted","가장 최근 영수증: "+(w.latest_receipt||"없음")+" / "+(w.last_observed||"날짜 미확인")));
const kv=node(e,el("dl","kv"));row(kv,"실제 검증",w.execution_verified?"등록부에 검증 표시 있음":"확인되지 않음");
row(kv,"준비 단계",w.prepared_state||"원본 작업지시 미확보");row(kv,"대화 원문 연결","미확인");
if(w.issues.length)node(e,el("p","muted","검토 사항: "+w.issues.join(" · ")));
details(e,"실행 영수증 이력 "+w.receipts.length+"건",w.receipts,(area,x)=>{
 node(area,el("div","list-row",(x.when||"일시 미확인")+" / "+(x.action||"")+" / "+(x.reported_status||"상태 미확인")))
});
details(e,"등록된 산출물·증거 파일",[...w.output_refs.map(x=>({...x,role:"산출물"})),...w.evidence_refs.map(x=>({...x,role:"증거"}))],(area,x)=>{
 node(area,el("div","list-row",x.role+" · "+(x.exists?"파일 존재":"파일 미확인")+" · "+x.path))
});}
function alertCard(container,a){const e=node(container,el("article","card alert"));node(e,el("h3","",a.type));node(e,el("p","",a.project||a.work_id||("seq "+(a.sequence??""))));node(e,el("p","muted",a.reason||"관련 원문과 실행 기록을 비교 검토해야 합니다"))}
function render(){query=$("search").value.trim().toLocaleLowerCase();status=$("status").value;
for(const b of document.querySelectorAll("[data-tab]"))b.setAttribute("aria-selected",String(b.dataset.tab===tab));
for(const id of ["projects","work","alerts","source"]){$(id).hidden=id!==tab;$(id).replaceChildren()}
let count=0;
if(tab==="projects"){const grid=node($("projects"),el("div","grid"));for(const p of db.projects){
 const match=!query||[p.project,p.progress_signal,p.registry_status,p.current_status].join(" ").toLocaleLowerCase().includes(query);
 const sm=!status||p.work_statuses[status]>0;if(!match||!sm)continue;projectCard(grid,p);count++}}
else if(tab==="work"){const grid=node($("work"),el("div","grid"));for(const w of db.work_items){
 const match=!query||[w.title,w.work_id,w.project,w.executor,w.registry_status].join(" ").toLocaleLowerCase().includes(query);
 if((chosen&&w.project!==chosen)||!match||(status&&w.registry_status!==status))continue;workCard(grid,w);count++}
 if(!status)for(const p of db.projects){const c=p.current_work_link||{};
 if(c.registration!=="CURRENT_DECLARED_UNREGISTERED"||(chosen&&p.project!==chosen))continue;
 if(query&&![c.id,p.project,c.scope].join(" ").toLocaleLowerCase().includes(query))continue;
 currentWorkCard(grid,p);count++}
 if(chosen){const b=node($("work"),el("button","",chosen+" 프로젝트 필터 해제"));b.onclick=()=>{chosen="";render()}}}
else if(tab==="alerts"){for(const a of db.alerts){if(query&&!JSON.stringify(a).toLocaleLowerCase().includes(query))continue;alertCard($("alerts"),a);count++}}
else {const f=db.source_scope;const v=node($("source"),el("div","panel"));for(const [k,x] of Object.entries(f))node(v,el("p","",k+" : "+x));
node(v,el("p","muted","프로젝트 진행률은 계산하지 않습니다. ChatGPT 10월 전체 대화 원문 미확보 및 TASK→CHAT 직접 연결 미검증 상태입니다."));
details(v,"입력 원자료 SHA256",db.source_manifest,(area,x)=>node(area,el("p","key",x.path+" / "+x.sha256)));count=1}
$("count").textContent=(chosen&&tab==="work"?chosen+" · ":"")+count+"개 항목 표시"+(tab==="projects"?" (프로젝트를 선택하면 관련 AI 작업으로 이동)":"")}
document.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>{tab=b.dataset.tab;chosen="";render()})
for(const [k,v] of [["프로젝트",db.counts.projects],["등록된 AI 작업",db.counts.registered_ai_work],["검토 대기",db.counts.review],["로컬 변경 미연결",db.counts.projects_with_unbound_local_tracked_wip||0],["CURRENT 작업 전체 미등록",db.counts.projects_with_explicit_current_unregistered_work||0],["포트폴리오 작업",db.counts.portfolio_tasks??"미확인"],["CURRENT 포트폴리오 등록",db.counts.project_current_in_portfolio??"미확인"],["CURRENT AI 미배정",db.counts.current_not_ai_assigned||0],["차단 기록",db.counts.blocked],["독립 검증 표시",db.counts.independently_verified_completion],["10월 원문 대화",db.source_scope.oct_native_chat_count]])metric(k,v);
$("search").addEventListener("input",render);$("status").addEventListener("change",render);
$("reset").onclick=()=>{query="";chosen="";status="";$("search").value="";$("status").value="";render()};
render();
</script></body></html>'''.replace("__DATA__",payload)
def run(root=ROOT,control=CONTROL,output=OUT,page=HTML):
    inp={name:read(control/p.name) for name,p in INPUTS.items()}
    reg=inp["projects"]["projects"]
    currents={}
    for key,val in reg.items():
        path=root/str(val.get("workbench_path",""))/"PROJECT_CURRENT.json"
        if path.is_file():currents[key]=read(path)
    manifest=[{"path":str(control/p.name),"sha256":sha((control/p.name).read_bytes())} for p in INPUTS.values()]
    portfolio=load_portfolio(root/PORTFOLIO_REL)
    manifest.append({"path":portfolio["path"],"sha256":portfolio["sha256"]})
    titles={}
    for t in inp["assignments"]["tasks"]:
        titles[t["work_id"]]=load_task(t)
        ref=titles[t["work_id"]].get("title_source")
        if ref:manifest.append({"path":ref,"sha256":sha(Path(ref).read_bytes())})
    for k,val in reg.items():
        path=root/str(val.get("workbench_path",""))/"PROJECT_CURRENT.json"
        if path.is_file():manifest.append({"path":str(path),"sha256":sha(path.read_bytes())})
    repo_meta={k:inspect_repo(str(v.get("source_repo") or "")) for k,v in reg.items()}
    data=derive(inp,currents,task_titles=titles,repo_metadata=repo_meta,source_manifest=manifest,portfolio=portfolio)
    output_text=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
    html_text=build_page(data)
    changed_data=write_if_changed(output,output_text)
    changed_page=write_if_changed(page,html_text)
    if read(output)["counts"]!=data["counts"] or page.read_text(encoding="utf-8")!=html_text:
        raise RuntimeError("PROGRESS_READBACK_FAILED")
    return {"progress_index":str(output),"viewer":str(page),
            "counts":data["counts"],"oct_chat_count":data["source_scope"]["oct_native_chat_count"],
            "changed_index":changed_data,"changed_viewer":changed_page,
            "readback":"PASS","deployment":False}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=OUT)
    parser.add_argument("--viewer",type=Path,default=HTML)
    args=parser.parse_args()
    print(json.dumps(run(output=args.output,page=args.viewer),ensure_ascii=False))
