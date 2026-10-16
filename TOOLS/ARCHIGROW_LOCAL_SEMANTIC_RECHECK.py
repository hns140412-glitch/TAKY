#!/usr/bin/env python3
"""Read-only local *evidence relation* extraction, NOT LLM semantic mining.

Input: verified real original ZIP/PDF ArchiGrow FORMING output, page-1/2
verified UTF-8 text and source SHA receipt. Derive three narrow, auditable
relations supported by verbatim spans, and re-assess existing FORMING questions.
No legal conclusions, no new mined authority, no paid/model/network calls.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path

S="TAKY_ARCHIGROW_LOCAL_REFERENCE_RELATION_RECHECK_V1"
RULES={
 "CHECK_PERMIT_AND_COMMITTEE_CONDITIONS":{
   "support":["각종심의조건및허가조건반영여부","건축 도면 검토 사항"],
   "relation":"CHECK_PERMIT_CONDITIONS_AGAINST_DRAWINGS",
   "source_scope":"REFERENCE_CHECKLIST_SECTION_GENERAL",
   "required_comparison_inputs":["심의 의결서","허가조건","관련 설계도면"],
   "cross_check_type":"CONDITION_TO_DRAWING_REFLECTION"
 },
 "VERIFY_SITE_AREA_CONSISTENCY":{
   "support":["면적관련일치여부확인","대지면적:설계개요&면적표면적&공부상면적"],
   "relation":"COMPARE_SITE_AREA_AMONG_THREE_RECORDS",
   "source_scope":"REFERENCE_CHECKLIST_SECTION_OVERVIEW",
   "required_comparison_inputs":["설계개요의 대지면적","면적표의 대지면적","공부상 대지면적"],
   "cross_check_type":"THREE_WAY_NUMERIC_CONSISTENCY"
 },
 "VERIFY_ROAD_LOCATION_AND_WIDTH":{
   "support":["5 배치도","도로 위치 및 폭 확인"],
   "relation":"CHECK_ROAD_LOCATION_AND_WIDTH_ON_SITE_PLAN",
   "source_scope":"REFERENCE_CHECKLIST_SECTION_SITE_PLAN",
   "required_comparison_inputs":["배치도","도로 위치 확인 근거","도로 폭 확인 근거"],
   "cross_check_type":"GEOMETRY_AND_DOCUMENT_CROSS_CHECK"
 },
}

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(2*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()
def load(path:str|Path)->dict:
    p=Path(path)
    o=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(o,dict):raise ValueError("RECHECK_JSON_OBJECT_REQUIRED")
    return o

def evaluate(forming:dict, feedback:dict, evidence_path:str|Path,
             seed_path:str|Path, seed_receipt_path:str|Path)->tuple[dict,dict]:
    evfile=Path(evidence_path).resolve()
    seedfile=Path(seed_path).resolve()
    receiptfile=Path(seed_receipt_path).resolve()
    source=load(evfile)
    receipt=load(receiptfile)
    if (forming.get("schema")!="TAKY_ARCHIGROW_REFERENCE_FORMING_RECEIPT_V1"
        or forming.get("status")!="HOLD"
        or forming.get("actual_project_compliance_approved")!=0
        or forming.get("missing_project_evidence") is not True
        or forming.get("CURRENT_promotion") is not False
        or forming.get("LEARNING_promotion") is not False
        or forming.get("evidence_manifest_sha256")!=file_sha(evfile)
        or forming.get("raw_archive_sha256")!=source.get("archive_original_sha256")):
        raise ValueError("RECHECK_FORMING_SOURCE_NOT_VERIFIED_OR_PROMOTED")
    if (feedback.get("schema")!="TAKY_ARCHIGROW_FORMING_FEEDBACK_TO_MINING_PLAN_V1"
        or feedback.get("source_forming_receipt_sha256")!=sha(
             json.dumps(forming,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8"))
        or feedback.get("source_project_gap_count")!=len(RULES)
        or feedback.get("semantic_depth_gap_count")!=1
        or feedback.get("misrouted_project_gaps_to_mining")!=0
        or feedback.get("live_worker_invocations")!=0):
        raise ValueError("RECHECK_NOT_SAME_FORMING_FEEDBACK")
    if (receipt.get("schema")!="TAKY_BOUNDED_LOCAL_ORIGINAL_PDF_TEXT_SEED_V1"
        or receipt.get("source_archive_sha256")!=forming.get("raw_archive_sha256")
        or receipt.get("source_member_sha256")!=source.get("pdf_member_sha256")
        or receipt.get("pages")!=[1,2]
        or receipt.get("raw_source_egress_permitted") is not False
        or receipt.get("local_plaintext_file")!=str(seedfile)
        or receipt.get("local_plaintext_sha256")!=file_sha(seedfile)
        or receipt.get("local_plaintext_chars")!=len(seedfile.read_text(encoding="utf-8"))):
        raise ValueError("RECHECK_VERIFIED_SEED_PAGES_OR_SHA_CHANGED")
    text=seedfile.read_text(encoding="utf-8")
    if len(text)>17000 or len(text)<1000:
        raise ValueError("RECHECK_TEXT_INPUT_OUT_OF_BOUNDS")
    pages=text.split("\n\n",1)
    if len(pages)!=2:
        raise ValueError("RECHECK_PDF_PAGES_NOT_SEPARABLE")
    if set(RULES)!={x.get("id") for x in forming.get("candidates",[])}:
        raise ValueError("RECHECK_FORMING_RULESET_NOT_EXPLICITLY_SUPPORTED")
    citations={x["rule_id"]:x for x in source.get("source_citations",[])}
    if len(citations)!=len(RULES):raise ValueError("RECHECK_CITATION_SOURCE_COUNT")
    spans=[]
    reformed=[]
    for item in forming["candidates"]:
        rule_id=item["id"]; spec=RULES[rule_id];cite=citations[rule_id]
        page=cite["source_page_number"]
        if (page!=item.get("reference_page")
            or item.get("reference_quote")!=cite.get("source_quote")
            or item.get("reference_quote_sha256")!=cite.get("quote_SHA256")
            or item.get("status")!="HOLD_NO_PROJECT_SOURCE"
            or item.get("strategy_candidate_not_approved") is not True):
            raise ValueError("RECHECK_CITATION_NOT_SAME_FORMING_INPUT")
        full=pages[page-1]
        if sha(full.encode("utf-8"))!=cite.get("source_page_full_extracted_SHA256"):
            raise ValueError("RECHECK_SEED_PAGE_DIGEST_MISMATCH")
        source_spans=[]
        for fragment in spec["support"]:
            offset=full.find(fragment)
            if offset<0 or full.count(fragment)!=1:
                raise ValueError("RECHECK_UNGROUNDED_OR_AMBIGUOUS_SUPPORT_"+rule_id)
            source_spans.append({
                "exact_verbatim":fragment,
                "page":page,
                "offset_in_pdf_page":offset,
                "exact_utf8_sha256":sha(fragment.encode("utf-8")),
                "citation_method":"EXACT_SOURCE_TEXT_MATCH_NOT_MODEL_GUESS"
            })
        original_quote=cite["source_quote"]
        if original_quote not in full:
            raise ValueError("RECHECK_SOURCE_QUOTE_DOES_NOT_EXIST")
        rel={
            "rule_id":rule_id,
            "source_page":page,
            "source_reference_quote":original_quote,
            "source_quote_SHA256":cite["quote_SHA256"],
            "relationship_kind":spec["relation"],
            "relationship_is_extraction_interpretation":True,
            "source_scope":spec["source_scope"],
            "source_support_spans":source_spans,
            "relationship_comparison_mode":spec["cross_check_type"],
            "required_project_evidence":spec["required_comparison_inputs"],
            "official_legality_verified":False,
            "actual_drawings_checked":False,
            "real_project_data_present":False,
            "independent_source_corrob":False,
            "certainty_scope":"SOURCE_TEXT_ONLY_NOT_REAL_WORLD_FACT",
            "approved_for_learning_or_app":False
        }
        spans.append(rel)
        reformed.append({
            **item,
            "local_reference_relation":spec["relation"],
            "comparison_mode":spec["cross_check_type"],
            "required_project_evidence_detail":spec["required_comparison_inputs"],
            "local_source_relation_verification":"TWO_SOURCE_SPANS_EXACT_MATCH",
            "local_source_relation_model":"DETERMINISTIC_NO_LLM",
            "unresolved_requirement":"ACTUAL_PROJECT_DRAWING_AND_OFFICIAL_RULE_CHECK",
            "status":"HOLD_NO_PROJECT_SOURCE",
            "legal_or_project_conclusion":"NOT_EVALUATED",
            "strategy_candidate_not_approved":True,
        })
    mining_result={
        "schema":S,
        "status":"VERIFIED_LOCAL_SOURCE_RELATIONS_PARTIAL_NOT_FULL_AI_MINING",
        "input_forming_digest":sha(json.dumps(forming,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")),
        "input_forming_project_id":forming["project_id"],
        "source_evidence_manifest_sha256":file_sha(evfile),
        "source_archive_sha256":forming["raw_archive_sha256"],
        "source_member_sha256":source["pdf_member_sha256"],
        "source_pages_text_sha256":file_sha(seedfile),
        "source_page_sha256s":[sha(p.encode("utf-8")) for p in pages],
        "source_relation_count":len(spans),
        "verified_relation_set":spans,
        "stage":"LOCAL_DETERMINISTIC_RELATION_EXTRACTION",
        "model_inference_performed":False,
        "full_semantic_mining_completed":False,
        "official_source_cross_verified":False,
        "CURRENT_promotion":False,"LEARNING_promotion":False,
        "paid_api_calls":0,"model_calls":0,"network_calls":0,
    }
    forming_result={
        **forming,
        "schema":"TAKY_ARCHIGROW_REASSESSED_REFERENCE_FORMING_RECEIPT_V1",
        "status":"HOLD",
        "forming_stage":"PARTIAL_SOURCE_RELATIONS_VERIFIED_PROJECT_EVIDENCE_MISSING",
        "mining_stage":"LOCAL_DETERMINISTIC_RELATIONS_VERIFIED_DEEP_SEMANTIC_STILL_PENDING",
        "local_relation_evidence_sha256":sha(json.dumps(mining_result,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")),
        "relation_evidence_only":True,
        "candidate_question_count":len(reformed),
        "candidates":reformed,
        "project_document_gaps":len(reformed),
        "project_review_passed":0,
        "independent_authority_crosscheck_passed":0,
        "full_semantic_mining_completed":False,
        "CURRENT_promotion":False,"LEARNING_promotion":False,
        "app_rule_applied":False,
        "model_calls":0,"paid_api_calls":0,"network_calls":0
    }
    return mining_result,forming_result
