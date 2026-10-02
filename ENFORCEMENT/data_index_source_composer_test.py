#!/usr/bin/env python3
"""G1 source-grounded join regression. Fixtures only; Drive corpus stays outside GitHub."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from data_index_source_composer import compose_source_l1
from data_index_search import search

ID = "derived-current-test"
SOURCE = {"schema": "TAKY_DATA_SOURCE_INDEX_V6", "entries": [
    {"source_id": "SRC-1", "title": "학교 평가 참고", "mime_type": "application/pdf", "path": "DATA",
     "url": "https://drive.google.com/file/d/SRC-1/view", "size_bytes": 200,
     "review_state": "CONTENT_REVIEWED", "content_summary": "평가 기준과 피드백의 원문 자료",
     "source_family": "SOURCE_REVIEWED_FAMILY", "authority_level": "OFFICIAL"},
    {"source_id": "SRC-2", "title": "기록과 생각", "mime_type": "image/png", "path": "DATA/capture",
     "url": "https://drive.google.com/file/d/SRC-2/view", "review_state": "METADATA_INDEXED",
     "duplicate_group": "SHA256_BUT_NOT_VALIDATED"},
    {"source_id": "SRC-3", "title": "보류 자료", "mime_type": "video/mp4", "path": "DATA/capture",
     "url": "https://drive.google.com/file/d/SRC-3/view", "review_state": "PDF_TEXT_EMPTY_VISUAL_REVIEW_REQUIRED"}
]}
CURRENT = {"schema": "TAKY_DATA_UTILIZATION_INDEX_V26", "source_authority": {"source_index_id": "source-id-test"},
           "source_entries": [
               {"source_id": "SRC-1", "title": "학교 평가 참고", "mime_type": "application/pdf", "path": "DATA",
                "source_family": "SOURCE_REVIEWED_FAMILY", "value_statement": "ACTUAL_USE_POLICY_SHOULD_NOT_LEAK",
                "index_l1": {"identity": {"source_id": "SRC-1", "canonical_title": "학교 평가 참고",
                                          "locator": "DATA", "media_type": "application/pdf"},
                             "discovery": {"short_summary": "유틸리티 활용 해석, 원문 아님"}}},
               {"source_id": "SRC-2", "title": "기록과 생각", "mime_type": "image/png", "path": "DATA/capture",
                "source_family": "DERIVED_CANDIDATE", "value_statement": "SCORING_ADVICE"},
               {"source_id": "SRC-3", "title": "보류 자료", "mime_type": "video/mp4", "path": "DATA/capture"},
           ]}
POINTER = {"current_utilization_index": {"id": ID, "name": "DATA_UTILIZATION_INDEX_2026-09-25_V26.json"},
           "source_authority": {"source_index": {"id": "source-id-test", "name": "DATA_SOURCE_INDEX_2026-09-25_V6.json"}},
           "current_status": {"total": 3}}

def rejects(modify, expected):
    source, use, pointer = copy.deepcopy(SOURCE), copy.deepcopy(CURRENT), copy.deepcopy(POINTER)
    modify(source, use, pointer)
    try:
        compose_source_l1(source, use, pointer)
    except ValueError as exc:
        assert expected in str(exc), (expected, str(exc))
    else:
        raise AssertionError(f"expected rejection: {expected}")

source_copy, use_copy, pointer_copy = copy.deepcopy(SOURCE), copy.deepcopy(CURRENT), copy.deepcopy(POINTER)
records, receipt = compose_source_l1(SOURCE, CURRENT, POINTER)
assert len(records) == 3 and len({r["source_id"] for r in records}) == 3
assert receipt["original_locator_preserved"] == 3
assert receipt["source_content_reviewed_summary"] == 1
assert receipt["family_source_v6_recorded"] == 1 and receipt["family_utilization_v26_derived_candidate"] == 1
assert receipt["family_unknown"] == 1 and receipt["unknown_hash"] == 3
assert receipt["current_pointer_modified"] is False and receipt["detail_page_fetch_performed"] is False
assert (SOURCE, CURRENT, POINTER) == (source_copy, use_copy, pointer_copy)
for entry in records:
    assert entry["locator"].startswith("https://drive.google.com/file/d/" + entry["source_id"] + "/")
    assert entry["origin_locator"] == entry["locator"]
    assert entry["content_hash"] is None
assert records[0]["short_summary"] == "평가 기준과 피드백의 원문 자료"
assert records[1]["short_summary"] is None and records[2]["short_summary"] is None
assert records[0]["field_lineage"]["short_summary"] == "SOURCE_V6_CONTENT_REVIEWED"
assert records[1]["field_lineage"]["source_family"] == "UTILIZATION_V26_DERIVED_CANDIDATE"
assert records[2]["field_lineage"]["source_family"] == "UNKNOWN"
# Search must expose source-family lineage rather than silently presenting a
# V26-derived family as reviewed original-source evidence.
assert search(records, "SRC-1")["results"][0]["classification_provenance"]["source_family"] == "SOURCE_V6_RECORDED"
assert search(records, "SRC-2")["results"][0]["classification_provenance"]["source_family"] == "UTILIZATION_V26_DERIVED_CANDIDATE"
assert search(records, "SRC-3")["results"][0]["classification_provenance"]["source_family"] == "UNKNOWN"
assert search(records, "SRC-2")["results"][0]["classification_provenance"]["short_summary"] == "UNKNOWN_NOT_INFERRED"
assert records[1]["relation_candidates"]["duplicate_group"] == "SHA256_BUT_NOT_VALIDATED"
assert records[1]["relations"] == []
assert all(r["detail_available"] is False for r in records)
assert not search(records, "ACTUAL_USE_POLICY_SHOULD_NOT_LEAK")["results"]
assert not search(records, "SCORING_ADVICE")["results"]
assert search(records, "평가 기준과 피드백")["results"][0]["source_id"] == "SRC-1"
assert search(records, "SRC-2")["results"][0]["source_ref"]["locator"].endswith("/SRC-2/view")

rejects(lambda s,u,p: s["entries"].pop(), "SOURCE_IDS_DIFFER")
rejects(lambda s,u,p: s["entries"][1].update(source_id="SRC-1"), "SOURCE_SOURCE_ID_DUPLICATE")
rejects(lambda s,u,p: s["entries"][1].update(url="https://drive.google.com/file/d/SRC-1/view"), "SOURCE_LOCATOR_INVALID")
rejects(lambda s,u,p: s["entries"][0].update(title="다른 원본"), "SOURCE_IDENTITY_CONFLICT")
rejects(lambda s,u,p: u["source_entries"][0].update(mime_type="image/png"), "SOURCE_IDENTITY_CONFLICT")
rejects(lambda s,u,p: u["source_entries"][0].update(source_family="OTHER"), "SOURCE_FAMILY_CONFLICT")
rejects(lambda s,u,p: u["source_entries"][0]["index_l1"]["identity"].update(source_id="SRC-3"), "EMBEDDED_IDENTITY_CONFLICT")
rejects(lambda s,u,p: s.update(schema="TAKY_DATA_SOURCE_INDEX_V5"), "SOURCE_SCHEMA_DISAGREES")
rejects(lambda s,u,p: u["source_authority"].update(source_index_id="stale"), "CURRENT source authority")
rejects(lambda s,u,p: s["entries"][0].update(content_hash="sha256:a") or u["source_entries"][0]["index_l1"]["identity"].update(content_hash="sha256:b"), "CONTENT_HASH_CONFLICT")
with tempfile.TemporaryDirectory() as temp:
    d = Path(temp)
    for name, value in (("source.json", SOURCE), ("current.json", CURRENT), ("pointer.json", POINTER)):
        (d/name).write_text("\ufeff" + json.dumps(value, ensure_ascii=False), encoding="utf-8")
    cmd = [sys.executable, str(ROOT / "data_index_source_composer.py"),
           "--source-index", str(d/"source.json"), "--current-index", str(d/"current.json"),
           "--current-pointer", str(d/"pointer.json"), "--query", "SRC-1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["results"][0]["source_ref"]["locator"].endswith("/SRC-1/view")
    assert output["results"][0]["field_lineage"]["locator"] == "SOURCE_V6_PRESERVED_DRIVE_COPY"
    assert output["source_composition_receipt"]["projection_authoritative"] is False
print("data_index_source_composer: PASS (source grounding, boundary, 10 negative gates, CLI)")
