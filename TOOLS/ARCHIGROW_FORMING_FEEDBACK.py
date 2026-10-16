#!/usr/bin/env python3
"""FORMING result -> classify feedback -> existing Mining Engine *index-first plan*.

This is a read-only, deterministic handoff to the existing
SOURCE-VAULT/MINING_DIRECTION_DISPATCHER.validate_request + Mining-V2
mining_source_directional_expansion.plan_followup. Never invokes the worker,
provider, network, model or live queue. Correctly routes real project-document
HOLDs to PROJECT_INPUT, not to repeated semantic mining.

Caller persists the SHA-bound returned result/request/plan in its own stage.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

VAULT=Path(r"D:\Git PWA\TAKY-SOURCE-VAULT")
MINING=Path(r"D:\Git PWA\TAKY\.local\TAKY_MINING_V2_SOURCE_CONSUMER_ISOLATED_20260929\ENFORCEMENT")
SCHEMA="TAKY_ARCHIGROW_FORMING_FEEDBACK_TO_MINING_PLAN_V1"
HEX=re.compile(r"^[0-9a-f]{64}$")

def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sha_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()
def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda:stream.read(2*1024*1024),b""):
            h.update(buf)
    return h.hexdigest()
def read(path:Path):
    result=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result,dict):
        raise ValueError("FORMING_FEEDBACK_OBJECT_REQUIRED")
    return result

def module(path:Path,name:str):
    if not path.is_file():
        raise ValueError("FORMING_FEEDBACK_MISSING_EXISTING_MINING_MODULE")
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def build(forming:dict, evidence_manifest_path:str|Path,
          collector_pointer_path:str|Path)->tuple[dict,dict|None]:
    """Return (feedback receipt, existing-Mining-compatible request candidate)."""
    if not isinstance(forming,dict) or forming.get("schema")!="TAKY_ARCHIGROW_REFERENCE_FORMING_RECEIPT_V1":
        raise ValueError("FEEDBACK_FORMING_RECEIPT_NOT_RECOGNIZED")
    if (forming.get("status")!="HOLD"
        or forming.get("failure_class")!="PROJECT_SOURCE_NOT_PROVIDED"
        or forming.get("actual_project_compliance_approved")!=0
        or forming.get("CURRENT_promotion") is not False
        or forming.get("LEARNING_promotion") is not False
        or forming.get("app_rule_applied") is not False):
        raise ValueError("FEEDBACK_CANNOT_APPLY_NONHOLD_OR_PROMOTED_FORMING")
    evidence_path=Path(evidence_manifest_path).resolve()
    pointer_path=Path(collector_pointer_path).resolve()
    if pointer_path != (VAULT/"data/pipeline_bridge/COLLECTOR_CANDIDATE_CURRENT.json").resolve():
        raise ValueError("FEEDBACK_LIVE_COLLECTOR_POINTER_PATH_NOT_ALLOWED")
    evidence=read(evidence_path)
    pointer=read(pointer_path)
    if (sha(evidence_path)!=forming.get("evidence_manifest_sha256")
        or pointer.get("batch_key")!=forming.get("source_batch_key")
        or evidence.get("archive_original_sha256")!=forming.get("raw_archive_sha256")
        or evidence.get("exact_citation_count")!=forming.get("candidate_question_count")):
        raise ValueError("FEEDBACK_STALE_OR_UNBOUND_SOURCE_FORMING")
    if (pointer.get("do_not_publish") is not True
        or pointer.get("full_pipeline_complete") is not False
        or evidence.get("CURRENT_promotion") is not False):
        raise ValueError("FEEDBACK_SOURCE_AUTHORITY_INVALID")
    raw_root=(VAULT/"reports/generations").resolve()
    index_file=Path(pointer["index_path"]).resolve()
    if not index_file.is_file() or not index_file.is_relative_to(raw_root):
        raise ValueError("FEEDBACK_INDEX_PATH_OUTSIDE_SOURCE_VAULT")
    index=read(index_file)
    if sha_bytes(canonical(index).encode("utf-8"))!=pointer["index_sha256"]:
        raise ValueError("FEEDBACK_INDEX_CHANGED")
    matches=[row for row in index.get("records",[])
             if row.get("source_id")==evidence.get("original_source_id")]
    if len(matches)!=1:
        raise ValueError("FEEDBACK_REFERENCE_SOURCE_NOT_INDEXED")
    record=matches[0]
    local_file=Path(record.get("raw_path","")).resolve()
    if (not local_file.is_file()
        or local_file.suffix.lower()!=".zip"
        or record.get("raw_sha256")!=forming["raw_archive_sha256"]
        or record.get("forming_authorized") is not False):
        raise ValueError("FEEDBACK_UNTRUSTED_RAW_SOURCE")
    if len(forming.get("candidates") or [])!=3:
        raise ValueError("FEEDBACK_EXPECTED_THREE_VERIFIED_HOLDS")
    lookup={x["rule_id"]:x for x in evidence["source_citations"]}
    tasks=[]
    for c in forming["candidates"]:
        original=lookup.get(c.get("id"))
        if (not original
            or c.get("status")!="HOLD_NO_PROJECT_SOURCE"
            or c.get("legal_or_project_conclusion")!="NOT_EVALUATED"
            or c.get("reference_quote_sha256")!=original.get("quote_SHA256")
            or c.get("reference_page")!=original.get("source_page_number")
            or c.get("review_question")!=original.get("review_question_candidate")
            or c.get("project_specific_documents_required")!=original.get("needed_real_project_documents")):
            raise ValueError("FEEDBACK_PROJECT_GAP_GROUNDING_FAILED")
        tasks.append({
            "candidate_id":c["id"],
            "kind":"PROJECT_SOURCE_GAP_NOT_MINING_FAILURE",
            "required_real_documents":c["project_specific_documents_required"],
            "review_question":c["review_question"],
            "next_route":"ARCHIGROW_PROJECT_DOCUMENT_ACQUISITION",
            "mining_queue_dispatch":False,
            "project_review_approved":False,
        })
    if {x["candidate_id"] for x in tasks}!={x["id"] for x in forming["candidates"]}:
        raise ValueError("FEEDBACK_DUPLICATE_PROJECT_GAP")
    need_semantic=forming.get("mining_stage")=="EXTRACTIVE_QUOTE_VERIFIED_ONLY_NOT_FULL_SEMANTIC_MINING"
    # The existing worker needs actual UTF-8 TEXT bytes. A ZIP-only request
    # passes RAW binding but fails semantic source_text(). Use the separately
    # SHA-verified, source-bound first two PDF pages, never fabricate text.
    seed_file=evidence_path.parent/"sourcebound_seed_pages_p1_p2.txt"
    seed_proof=seed_file.with_suffix(".source_receipt.json")
    seed=None
    if need_semantic:
        if not seed_file.is_file() or not seed_proof.is_file():
            raise ValueError("FEEDBACK_VERIFIED_LOCAL_SEED_TEXT_NOT_READY")
        seed_receipt=read(seed_proof)
        seed=seed_file.read_text(encoding="utf-8")
        if (seed_receipt.get("source_archive_sha256")!=forming["raw_archive_sha256"]
            or seed_receipt.get("source_member_sha256")!=evidence["pdf_member_sha256"]
            or seed_receipt.get("local_plaintext_sha256")!=sha(seed_file)
            or seed_receipt.get("local_plaintext_chars")!=len(seed)
            or not 50<=len(seed)<=17000
            or not all(x["source_quote"] in seed for x in evidence["source_citations"])):
            raise ValueError("FEEDBACK_SEED_TEXT_NOT_BOUND_TO_PRIMARY_PDF")
    request=None
    preplan=None
    request_status="NOT_NEEDED_SEMANTIC_ALREADY_VERIFIED"
    if need_semantic:
        direction=(
            "ARCHIGROW reference-checklist semantic depth: verify against independent "
            "current authoritative sources the relevance, limits and exceptions of "
            "reviewing permit conditions, site area consistency, and road layout. "
            "Contrast actual implementation and contrary evidence. This archived "
            "checklist is not itself a law; do not infer any project compliance."
        )
        stable=sha_bytes(canonical({
            "source_id":record["source_id"],
            "sha":record["raw_sha256"],
            "source_member":evidence["pdf_member_sha256"],
            "gap":"REFERENCE_SEMANTIC_DEPTH_NOT_VERIFIED_V1",
        }).encode("utf-8"))
        request={
            "schema":"TAKY_LOCAL_DIRECTION_MINING_REQUEST_V1",
            "request_id":stable[:20],
            "research_policy":{
                "stage":"SEED_MINING",  # live queue recognizes this stage; explicit no-paid gate blocks dispatch
                "max_directional_queries":4,
                "mode":"WORKBENCH_PREVIEW_AND_INDEX_FIRST_ONLY_NO_AUTORUN",
                "paid_calls_allowed":False,
            },
            "source":{
                "source_id":record["source_id"],
                "title":"Archi Grow reference checklist member, semantic-depth gap",
                "url":None,
                "local_file":str(local_file),
                "raw_state":"RAW_CAPTURED",
                "raw_artifacts":[{
                    "kind":"ORIGINAL_LOCAL_ZIP_RAW",
                    "path":str(local_file),
                    "sha256":record["raw_sha256"],
                    "size_bytes":local_file.stat().st_size
                },{
                    "kind":"RENDERED_TEXT",
                    "path":str(seed_file.resolve()),
                    "sha256":sha(seed_file),
                    "size_bytes":seed_file.stat().st_size,
                    "source_member_sha256":evidence["pdf_member_sha256"],
                    "source_scope":"EXACT_PDF_PAGES_1_AND_2_ONLY"
                }],
                "original_evidence":{
                    "state":"LOCAL_RAW_ARCHIVE_SHA_AND_PDF_MEMBER_QUOTED",
                    "pdf_member_path":evidence["origin_reference_name"],
                    "member_sha256":evidence["pdf_member_sha256"],
                    "full_document_semantic_mining_verified":False,
                },
                "intake_origin":"FORMING_DOMAIN_FEEDBACK_RESEARCH_CANDIDATE",
            },
            "direction":{
                "user_direction_exact":None,
                "combined_direction":direction,
                "direction_source":"FORMING_GAP_DERIVED_NOT_USER_EXACT",
                "derived_keywords":["permit conditions","site area consistency","road layout",
                                    "exceptions","independent primary source"],
                "analysis_level":"FEEDBACK_SHALLOW_DIRECTION_ONLY",
                "source_fact_claimed":False,
                "scope_hints":["ARCHIGROW","ARCHITECTURE_REFERENCE","NO_PROJECT_COMPLIANCE"]
            },
            "contract":{
                "feedback_is_source_fact":False,
                "research_candidate_only":True,
                "collector_forbidden":["INDEXING","LEARNING","CANONICAL_PROMOTION"],
                "raw_evidence_egress_allowed":False,
                "real_mining_completed":False,
            }
        }
        existing_dispatch=module(VAULT/"MINING_DIRECTION_DISPATCHER.py",
                                 "taky_actual_mining_direction_dispatcher")
        valid,errors=existing_dispatch.validate_request(request)
        if not valid or errors:
            raise ValueError("FEEDBACK_EXISTING_MINING_REQUEST_REJECTED:"+",".join(errors))
        # Actual queue recognizes SEED_MINING as costful, but the explicit
        # no-paid permission is denied before scheduler activation.
        live_queue=module(VAULT/"RUN_MINING_QUEUE_WORKER.py",
                          "actual_existing_mining_queue_gate")
        request_stage=request["research_policy"]["stage"]
        if request_stage not in live_queue.COSTFUL:
            raise ValueError("FEEDBACK_STAGE_NOT_IN_EXISTING_LIVE_MINING_QUEUE")
        # Immutable legacy queue does NOT enforce paid_calls_allowed. Instead
        # this candidate must never leave WORKBENCH runtime. A bare copy into
        # the live outbox would be eligible and might invoke Claude.
        admitted,why=live_queue.request_eligibility(request)
        if not admitted or why is not None:
            raise ValueError("FEEDBACK_EXISTING_LIVE_MINING_QUEUE_STAGE_NOT_RECOGNIZED")
        if (request["research_policy"].get("paid_calls_allowed") is not False
            or request["research_policy"].get("mode")!="WORKBENCH_PREVIEW_AND_INDEX_FIRST_ONLY_NO_AUTORUN"):
            raise ValueError("FEEDBACK_WORKBENCH_EXPLICIT_NO_PAID_SAFETY_GATE")
        if Path(evidence_path).resolve().is_relative_to((VAULT/"reports/mining_direction_outbox").resolve()):
            raise ValueError("FEEDBACK_EVIDENCE_MUST_NOT_BE_IN_LIVE_QUEUE")
        if not MINING.is_dir():
            raise ValueError("FEEDBACK_ORIGINAL_MINING_RUNTIME_MISSING")
        worker=module(MINING/"mining_direction_request_worker.py",
                      "existing_mining_source_text_preflight")
        worker_errors,worker_artifacts=worker.verify_request(request)
        bounded_text=worker.source_text(worker_artifacts)
        if (worker_errors or not bounded_text or
            bounded_text!=seed.strip() or
            not all(x["source_quote"] in bounded_text for x in evidence["source_citations"])):
            raise ValueError("FEEDBACK_EXISTING_WORKER_CANNOT_READ_VERIFIED_TEXT_SOURCE")
        # Consult the *actual current local candidate Index* before proposing
        # external discovery. Every item is explicitly held for review; no
        # index hit can be treated as verified evidence or company authority.
        safe_index_rows=[]
        for ix in index.get("records",[])[:100]:
            discovery=(ix.get("index_l1") or {}).get("discovery") or {}
            summary=discovery.get("short_summary")
            safe_index_rows.append({
                "source_id":ix["source_id"],
                "title":ix.get("title") or "",
                "short_summary":summary[:650] if isinstance(summary,str) else "",
                "authority_class":"REFERENCE_ONLY",
                "review_state":"REVIEW_REQUIRED",
                "index_state":"NONAUTHORITATIVE_RAW_CANDIDATE",
            })
        mining_parent=str(MINING)
        sys.path.insert(0,mining_parent)
        try:
            from mining_source_directional_expansion import plan_followup
            preplan=plan_followup({
                "source_id":record["source_id"],
                "title":request["source"]["title"],
                "source_direction":direction,
                "short_summary":None,
                "keywords":request["direction"]["derived_keywords"],
                "applicability_scope":request["direction"]["scope_hints"],
                "authority_ceiling":"NONAUTHORITATIVE_REFERENCE_ONLY",
            },index_rows=safe_index_rows,max_queries=4)
        finally:
            if sys.path and sys.path[0]==mining_parent:
                sys.path.pop(0)
        if preplan.get("state")!="READY_FOR_INDEX_FIRST_RESEARCH" or not preplan.get("plan"):
            raise ValueError("FEEDBACK_MINING_INDEX_FIRST_ORCHESTRATOR_REFUSED_PLAN")
        if len(preplan.get("directional_queries") or [])!=4:
            raise ValueError("FEEDBACK_BOUND_RESEARCH_QUERY_COUNT_CHANGED")
        request_status="EXISTING_MINING_INTAKE_AND_INDEX_FIRST_PLAN_VERIFIED_NOT_DISPATCHED"
    out={
        "schema":SCHEMA,
        "state":"PROJECT_GAPS_ROUTED_AND_SEMANTIC_GAP_PLANNED_WITH_EXISTING_MINER",
        "source_batch":pointer["batch_key"],
        "project_id":forming["project_id"],
        "source_raw_sha256":record["raw_sha256"],
        "source_pdf_member_sha256":evidence["pdf_member_sha256"],
        "source_forming_receipt_sha256":sha_bytes(canonical(forming).encode("utf-8")),
        "source_manifest_sha256":sha(evidence_path),
        "source_project_gap_count":len(tasks),
        "source_project_tasks":tasks,
        "misrouted_project_gaps_to_mining":0,
        "semantic_depth_gap_count":int(need_semantic),
        "semantic_candidate_state":request_status,
        "semantic_request_id":request["request_id"] if request else None,
        "existing_mining_dispatcher_schema_valid":bool(request),
        "existing_normal_queue_stage_recognized":bool(request),
        "existing_queue_original_unchanged":True,
        "existing_queue_native_stage_is_costful_and_would_accept_if_submitted":bool(request),
        "workbench_only_preview_not_submitted":True,
        "workbench_explicit_no_paid_gate_enforced":bool(request),
        "existing_queue_rejection_reason":None,
        "existing_semantic_worker_can_read_SHA_verified_text":bool(request),
        "existing_semantic_worker_text_input_sha256":sha(seed_file) if request else None,
        "existing_semantic_worker_text_input_chars":len(seed) if request else 0,
        "existing_mining_directional_query_count":len(preplan["directional_queries"]) if preplan else 0,
        "existing_mining_index_first_planning_performed":bool(preplan),
        "actual_local_index_rows_consulted":len(safe_index_rows) if preplan else 0,
        "actual_local_index_is_unverified_candidate_only":True,
        "existing_mining_index_first_trace":(preplan["plan"].get("index_first") or {}).get("counts") if preplan else None,
        "next_mining_stage":"AWAIT_APPROVED_BOUNDED_SEMANTIC_MINING" if request else "NONE",
        "live_queue_insertions":0,
        "live_worker_invocations":0,
        "actual_semantic_mining_completed":False,
        "planned_provider_execution_performed":False,
        "SOURCE_VAULT_mutations":False,
        "CURRENT_promotion":False,"LEARNING_promotion":False,
        "app_policy_applied":False,
        "model_calls":0,"paid_API_calls":0,"network_calls":0,
    }
    return out,request

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--forming",required=True)
    p.add_argument("--evidence",required=True)
    p.add_argument("--collector-pointer",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--candidate-out",required=True)
    a=p.parse_args()
    form=read(Path(a.forming))
    result,candidate=build(form,a.evidence,a.collector_pointer)
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if candidate:
        Path(a.candidate_out).write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["state"],"project":len(result["source_project_tasks"]),
                      "semantic_research_candidates":result["semantic_depth_gap_count"]},ensure_ascii=False))
