#!/usr/bin/env python3
"""Offline regressions for the staged external source bridge. No corpus in GitHub."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from data_index_bridge import load_explicit_overlay, validate_and_project_bridge
from data_index_search import search

CURRENT_ID = "current-test-id"
INDEX = {"schema": "TAKY_DATA_UTILIZATION_INDEX_V26", "source_authority": {"source_index_id": "source-test-id"}, "source_entries": [{"source_id": "existing-1", "title": "기존 학습 자료", "source_family": "TEST", "mime_type": "application/pdf"}]}
POINTER = {"current_utilization_index": {"id": CURRENT_ID, "name": "DATA_UTILIZATION_INDEX_2026-09-25_V26.json"}, "source_authority": {"source_index": {"id": "source-test-id"}}, "current_status": {"total": 1}}
STUDENT, TEACHER, PAIR_ID = "test-student-001", "test-teacher-001", "WR-12-DIARY"

def entry(sid, role, other):
    return {"source_id": sid, "pair_id": PAIR_ID, "source_role": role, "canonical_title": f"일기 쓰기 {role}", "locator": f"https://drive.google.com/file/d/{sid}/view", "media_type": "application/pdf", "source_family": "ICE_STRUCTURED_WRITING_2024", "grade_band": "1_2", "genre": "experience_diary", "origin_type": "PRESERVED_CURATED_COPY", "authority_class": "OFFICIAL_LOCAL_EDUCATION_OFFICE_MATERIAL", "content_hash": None, "hash_state": "NOT_PROVIDED", "review_state": "FULL_PAGE_VISUAL_PARTIAL", "relations": [{"type": "RELATED_TO", "target": other, "qualifier": "STUDENT_TEACHER_PAIR"}]}

BRIDGE = {"schema": "TAKY_INDEX_INCREMENTAL_SOURCE_RELATION_BRIDGE_V1", "state": "STAGED_VERIFIED_DELTA_NON_PROMOTION", "authority_boundaries": {"current_utilization_index": CURRENT_ID, "current_pointer_modified": False, "cross_universe_relation_bridge_not_auto_add_to_679": True}, "source_family": {"family_id": "ICE_STRUCTURED_WRITING_2024", "original_official_listing": "https://example.invalid/original", "publisher": "인천광역시교육청"}, "source_entries": [entry(STUDENT, "student", TEACHER), entry(TEACHER, "teacher", STUDENT)], "pair_relations": [{"pair_id": PAIR_ID, "grade_band": "1_2", "genre": "experience_diary", "title": "겪은 일을 떠올려 일기 쓰기", "printed_standard_code": "2국03-04", "student_source_id": STUDENT, "teacher_source_id": TEACHER, "keywords": ["일기", "속마음"]}]}

def rejects(edit, phrase):
    candidate = copy.deepcopy(BRIDGE)
    edit(candidate)
    try:
        validate_and_project_bridge(candidate, CURRENT_ID)
    except ValueError as exc:
        assert phrase in str(exc), str(exc)
    else:
        raise AssertionError("bad bridge accepted")

items = validate_and_project_bridge(BRIDGE, CURRENT_ID)
assert len(items) == 2
assert items[0]["source_id"] == STUDENT and items[1]["source_id"] == TEACHER
assert items[0]["content_hash"] is None and items[0]["detail_available"] is False
assert items[0]["current_relation"] == "EXTERNAL_BRIDGE_STAGED"
assert "GRADE_1_2" in items[0]["domain_facets"]
r = search(items, STUDENT, limit=10)
assert r["results"][0]["source_id"] == STUDENT
# A staged metadata receipt is not an independent Indexing-owner rank receipt.
assert {v["source_id"] for v in r["results"]} == {STUDENT}
assert r["relation_rank_gate"] == "NO_INDEPENDENT_VALIDATED_RELATION_KEYS"
assert r["results"][0]["detail_escalation"]["stage"] == "RAW_REQUIRED"
# Bridge proof is metadata-scoped and must never become production/CURRENT authority.
from data_index_relation_context import assemble_relation_context
context = assemble_relation_context(items, STUDENT, required_types={"RELATED_TO"})
assert context["relation_context_complete_for_request"]
assert context["edges"][0]["status"] == "STAGED_METADATA_LINK_NOT_CANONICAL"
assert context["edges"][0]["target_source_ref"]["source_id"] == TEACHER
assert context["edges"][0]["target_source_ref"]["source_family_origin"] == "STAGED_MANIFEST_METADATA_NOT_CURRENT"
assert r["results"][0]["classification_provenance"]["source_family"] == "STAGED_MANIFEST_METADATA_NOT_CURRENT"
assert r["results"][0]["classification_provenance"]["short_summary"] == "STAGED_PAIR_METADATA_NOT_PDF_CONTENT_REVIEW"
assert context["current_promoted"] is False and context["domain_use_approved"] is False
assert not r["projection_authoritative"]
assert {v["source_id"] for v in search(items, "일기", filters={"domain": "GRADE_1_2"})["results"]} == {STUDENT, TEACHER}
rejects(lambda b: b["authority_boundaries"].update(current_utilization_index="historical-id"), "different CURRENT")
rejects(lambda b: b["authority_boundaries"].update(current_pointer_modified=True), "unapproved CURRENT")
rejects(lambda b: b["source_entries"][1].update(source_id=STUDENT), "duplicate/invalid")
rejects(lambda b: b["source_entries"][0].update(content_hash="made-up"), "hash")
rejects(lambda b: b["source_entries"][0].update(locator="https://example.invalid/wrong"), "locator")
rejects(lambda b: b["source_entries"][1].update(relations=[]), "reciprocal")
rejects(lambda b: b["pair_relations"][0].update(genre="opinion"), "metadata mismatch")

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    def dump(name, value):
        p = root/name
        p.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return p
    index, pointer, bridge = dump("index.json", INDEX), dump("current.json", POINTER), dump("bridge.json", BRIDGE)
    all_items, info = load_explicit_overlay(index, pointer, bridge)
    assert len(all_items) == 3 and info["current_corpus_count"] == 1 and info["external_bridge_count"] == 2
    assert len(INDEX["source_entries"]) == 1
    command = [sys.executable, str(ROOT/"data_index_bridge.py"), "--current-index", str(index), "--current-pointer", str(pointer), "--bridge", str(bridge), "--query", STUDENT, "--context-source-id", STUDENT]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["results"][0]["source_id"] == STUDENT and output["overlay_provenance"]["current_pointer_modified"] is False
    assert output["relation_context"]["edges"][0]["target_source_ref"]["source_id"] == TEACHER
    assert output["relation_context"]["index_owner_receipt_verified"] is False
    bad = copy.deepcopy(INDEX)
    bad["schema"] = "TAKY_DATA_UTILIZATION_INDEX_V25"
    dump("index.json", bad)
    try:
        load_explicit_overlay(index, pointer, bridge)
    except ValueError as exc:
        assert "CURRENT schema" in str(exc)
    else:
        raise AssertionError("historical index accepted")
    dump("index.json", INDEX)
    bad = copy.deepcopy(INDEX)
    bad["source_entries"].append({"source_id": STUDENT})
    bad["source_entries"][0] = {"source_id": STUDENT}
    bad_pointer = copy.deepcopy(POINTER)
    bad_pointer["current_status"]["total"] = 2
    dump("index.json", bad)
    dump("current.json", bad_pointer)
    try:
        load_explicit_overlay(index, pointer, bridge)
    except ValueError as exc:
        assert "duplicated" in str(exc)
    else:
        raise AssertionError("duplicated CURRENT accepted")

# Read-only multi-universe composition: Source V6 original + CURRENT V26 + 2
# staged writing originals + 4 link-only provider records.
from data_index_bridge import load_source_grounded_universe
from data_index_external_intake import SCHEMA as EXTERNAL_SCHEMA
source = {"schema": "TAKY_DATA_SOURCE_INDEX_V6", "entries": [{
    "source_id": "existing-1", "title": "기존 학습 자료",
    "mime_type": "application/pdf", "review_state": "CONTENT_REVIEWED",
    "url": "https://drive.google.com/file/d/existing-1/view",
    "content_summary": "원본 평가 기준과 피드백",
}]}
source_pointer = copy.deepcopy(POINTER)
source_pointer["source_authority"]["source_index"]["name"] = "DATA_SOURCE_INDEX_2026-09-25_V6.json"
def provider(i, kind):
    return {
        "schema": EXTERNAL_SCHEMA, "external_namespace": "PROVIDER_"+str(i),
        "provider_native_id": "native_"+str(i), "source_title": "독립 자료 "+str(i),
        "original_locator": "https://example.org/item/"+str(i),
        "source_kind": kind, "evidence_extent": "LISTING_METADATA",
        "rights_state": "UNKNOWN_REVIEW_REQUIRED", "privacy_class": "PUBLIC",
        "observed_at": "2026-09-29", "attribution": "Publisher metadata",
        "content_hash": None, "original_content_acquired": False, "current_promoted": False,
    }
external_manifest = {
    "schema": "TAKY_EXTERNAL_DISCOVERY_MANIFEST_V1", "state": "STAGED_LINK_ONLY_NOT_CURRENT",
    "authority": {"current_pointer_modified": False,
                  "external_original_content_acquired": False,
                  "corpus_addition_to_DATA_679": False},
    "sources": [provider(i,k) for i,k in enumerate([
        "OFFICIAL_STANDARD", "PUBLIC_API_LISTING", "OPEN_SOURCE_ISSUE", "COMMUNITY_DISCUSSION"])],
}
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    def save(name, payload):
        p = root/name
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return p
    source_path=save("source.json", source)
    current_path=save("current.json", INDEX)
    pointer_path=save("pointer.json", source_pointer)
    bridge_path=save("bridge.json", BRIDGE)
    external_path=save("external.json", external_manifest)
    rows, proof = load_source_grounded_universe(
        source_path,current_path,pointer_path,bridge_path,external_path)
    assert len(rows)==7 and len({v["source_id"] for v in rows})==7
    assert proof["data_current_count"]==1 and proof["writing_originals_staged_count"]==2
    assert proof["external_discovery_link_only_count"]==4
    assert proof["temporary_retrieval_candidate_count"]==7
    assert proof["data_current_pointer_modified"] is False
    assert rows[0]["origin_locator"].endswith("/existing-1/view")
    assert rows[0]["short_summary"] == "원본 평가 기준과 피드백"
    assert rows[3]["source_id"] == "EXTERNAL::PROVIDER_0::native_0"
    assert rows[3]["content_hash"] is None and not rows[3]["detail_available"]
    assert search(rows,"EXTERNAL::PROVIDER_0::native_0")["results"][0]["source_ref"]["locator"].endswith("/item/0")
    bad = copy.deepcopy(external_manifest)
    bad["authority"]["current_pointer_modified"] = True
    save("external.json",bad)
    try: load_source_grounded_universe(source_path,current_path,pointer_path,bridge_path,external_path)
    except ValueError as exc: assert "AUTHORITY_INVALID" in str(exc)
    else: raise AssertionError("external pointer promotion accepted")
    bad=copy.deepcopy(external_manifest)
    bad["sources"][0]["privacy_class"]="AUTHORIZED_PRIVATE"
    save("external.json",bad)
    try: load_source_grounded_universe(source_path,current_path,pointer_path,bridge_path,external_path)
    except ValueError as exc: assert "PRIVATE_SOURCE" in str(exc)
    else: raise AssertionError("private external source reached shared search")

# Optional selected-source evidence roundtrip retains a staged-only 1+2+4 scope.
from data_index_evidence_overlay import SCHEMA as EVIDENCE_SCHEMA, STATE as EVIDENCE_STATE, FACT_KIND
section_notes=[]
for source_row in external_manifest["sources"]:
    role=source_row["source_kind"]
    method,fact=FACT_KIND[role]
    section_notes.append({
        "source_id": "EXTERNAL::"+source_row["external_namespace"]+"::"+source_row["provider_native_id"],
        "original_locator": source_row["original_locator"], "source_kind": role,
        "inspection_method": method, "fact_status":fact, "section_ref":"Named original section",
        "evidence_summary":"Selected original page section directly reviewed for its stated content and limitations.",
        "limits":"Only this selected section observed; no whole document or full-text reuse claim.",
        "reviewed_at":"2026-09-29","content_hash":None,"full_content_acquired":False,
        "rights_verified":False,"reuse_scope":"SHORT_ORIGINAL_PARAPHRASE_ONLY",
        "detail_location_verified":"SECTION_LABEL_NOT_SPATIAL_BBOX",
    })
delta={
    "schema":EVIDENCE_SCHEMA,"state":EVIDENCE_STATE,
    "parent_manifest_document_id":"test-base-document",
    "authority":{"current_pointer_modified":False,"source_manifest_modified":False,
       "raw_full_content_acquired":False,"rights_for_full_text_reuse_verified":False,
       "source_hashes_verified":0},
    "entries":section_notes,
}
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    def put(name,data):
        p=root/name;p.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
        return p
    source_path=put("source.json",source)
    current_path=put("current.json",INDEX)
    pointer_path=put("pointer.json",source_pointer)
    bridge_path=put("bridge.json",BRIDGE)
    external_path=put("external.json",external_manifest)
    evidence_path=put("evidence.json",delta)
    records,meta=load_source_grounded_universe(source_path,current_path,pointer_path,
        bridge_path,external_path,evidence_path,"test-base-document")
    assert len(records)==7 and meta["external_evidence_receipt"]["notes_joined"]==4
    assert records[3]["short_summary"].startswith("Selected original page")
    assert records[3]["content_hash"] is None and records[3]["current_relation"]=="NO_CURRENT_PROMOTION"
    assert meta["data_current_pointer_modified"] is False
    bad=copy.deepcopy(delta);bad["entries"][0]["source_id"]="EXTERNAL::UNLISTED::anything"
    put("evidence.json",bad)
    try:load_source_grounded_universe(source_path,current_path,pointer_path,
         bridge_path,external_path,evidence_path,"test-base-document")
    except ValueError as exc:assert "UNKNOWN_OR_DUPLICATE_ID" in str(exc)
    else:raise AssertionError("Unknown evidence source ID accepted")
print("source_grounded_evidence: PASS (staged selected sections, no content/promotion, origin gate)")
print("source_grounded_universe: PASS (1 current + 2 staged PDF + 4 external link-only; negative gates)")

print("data_index_bridge: PASS (schema, identity, pair, provenance, stage, collision, CLI)")
