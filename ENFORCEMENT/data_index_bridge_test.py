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
assert {v["source_id"] for v in r["results"]} == {STUDENT, TEACHER}
assert r["results"][0]["detail_escalation"]["stage"] == "RAW_REQUIRED"
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
    command = [sys.executable, str(ROOT/"data_index_bridge.py"), "--current-index", str(index), "--current-pointer", str(pointer), "--bridge", str(bridge), "--query", STUDENT]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["results"][0]["source_id"] == STUDENT and output["overlay_provenance"]["current_pointer_modified"] is False
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
print("data_index_bridge: PASS (schema, identity, pair, provenance, stage, collision, CLI)")
