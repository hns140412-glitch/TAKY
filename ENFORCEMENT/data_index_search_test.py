import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "data_index_search.py"
sys.path.insert(0, str(ROOT))

from data_index_search import materialize_legacy_relations, normalize_record, search

RECORDS = [
    {
        "source_id": "SRC-001",
        "title": "서울 PHONICS 학생용",
        "mime_type": "application/pdf",
        "source_family": "SEOUL_PHONICS_STUDENT_BOOK",
        "source_type": "LOCAL_EDUCATION_AUTHORITY_STUDENT_WORKBOOK_PDF",
        "authority_level": "LOCAL_EDUCATION_AUTHORITY_PUBLISHED_MATERIAL",
        "temporal_group": "CAP-X",
        "consumers": ["LEARNING_ENGINE"],
        "index_l1": {
            "identity": {
                "source_id": "SRC-001",
                "canonical_title": "서울 PHONICS 학생용",
                "locator": "DATA/phonics.pdf",
                "media_type": "application/pdf",
                "content_hash": "sha256:test-phonics",
            },
            "provenance": {
                "origin_type": "LOCAL_EDUCATION_AUTHORITY_PUBLICATION",
                "origin_locator": "https://example.invalid/phonics",
                "publisher_or_account": "SEOUL_EDU",
            },
            "classification": {
                "source_family": "SEOUL_PHONICS_STUDENT_BOOK",
                "source_type": "LOCAL_EDUCATION_AUTHORITY_STUDENT_WORKBOOK_PDF",
                "domain_facets": ["EDUCATION", "ENGLISH", "PHONICS"],
                "authority_class": "LOCAL_EDUCATION_AUTHORITY_PUBLISHED_MATERIAL",
            },
            "discovery": {
                "short_summary": "초등 영어 파닉스 학생 워크북",
                "controlled_terms": ["서울 PHONICS", "phonics", "학생용"],
                "keywords": ["영어", "파닉스", "워크북"],
                "entities": ["서울특별시교육청"],
                "consumer_candidates": ["LEARNING_ENGINE"],
            },
            "state": {
                "index_state": "INDEXED",
                "detail_available": True,
                "review_state": "REVIEWED",
                "current_relation": "CURRENT_INDEX_ENTRY",
            },
            "relations": [{"type": "RELATED_TO", "target": "SRC-002"}],
        },
        "detail_l2": {"pdf": {"page_count": 57, "reviewed_pages": [1, 2, 30, 57], "anchors": ["cover", "practice page"]}},
    },
    {
        "source_id": "SRC-002",
        "title": "초등 학습도구어",
        "mime_type": "application/pdf",
        "source_family": "ELEMENTARY_TOOL_LANGUAGE",
        "source_type": "OFFICIAL_CURRICULUM_DERIVED_REFERENCE",
        "authority_level": "AUTHORITY_OR_OFFICIAL_CURRICULUM_DERIVED",
        "temporal_group": "CAP-X",
        "value_statement": "terminology normalization and tool-language consistency",
        "utilization_class": "DIRECT_USE_READY",
        "function_ids": ["LE-F02"],
        "runtime_connection_state": "MAPPED_NOT_CONNECTED",
    },
    {
        "source_id": "SRC-003",
        "title": "Runtime preview capture",
        "mime_type": "video/mp4",
        "source_family": "READY_SET_MOBILE_PREVIEW_RUNTIME_REFERENCE",
        "source_type": "HISTORICAL_RUNTIME_CAPTURE",
        "authority_level": "FIRST_PARTY_HISTORICAL_REFERENCE",
        "temporal_group": "CAP-X",
        "duplicate_group": "DUP-GROUP-1",
        "current_relation": "SUPERSEDED",
    },
    {
        "source_id": "SRC-004",
        "title": "Runtime preview capture copy",
        "mime_type": "video/mp4",
        "source_family": "READY_SET_MOBILE_PREVIEW_RUNTIME_REFERENCE",
        "source_type": "HISTORICAL_RUNTIME_CAPTURE",
        "authority_level": "FIRST_PARTY_HISTORICAL_REFERENCE",
        "temporal_group": "CAP-Y",
        "duplicate_group": "DUP-GROUP-1",
        "current_relation": "CURRENT_INDEX_ENTRY",
    },
]

records = materialize_legacy_relations([normalize_record(r) for r in RECORDS])

# 1. exact source_id
r = search(records, "SRC-001")
assert r["results"][0]["source_id"] == "SRC-001"
assert r["results"][0]["channels"]["exact"] is True

# 2. exact family lookup
r = search(records, "ELEMENTARY_TOOL_LANGUAGE")
assert r["results"][0]["source_id"] == "SRC-002"

# 3. lexical retrieval
r = search(records, "영어 파닉스")
assert r["results"][0]["source_id"] == "SRC-001"

# 4. structured filter before retrieval
r = search(records, "runtime", filters={"current": "CURRENT_INDEX_ENTRY"})
assert [x["source_id"] for x in r["results"]] == ["SRC-004"]

# 5. same temporal group does not merge families
same_temporal = [x for x in records if x["temporal_group"] == "CAP-X"]
assert {x["source_family"] for x in same_temporal} == {
    "SEOUL_PHONICS_STUDENT_BOOK",
    "ELEMENTARY_TOOL_LANGUAGE",
    "READY_SET_MOBILE_PREVIEW_RUNTIME_REFERENCE",
}

# 6. duplicate-group compatibility becomes a conservative source relation, not identity merge
a = next(x for x in records if x["source_id"] == "SRC-003")
b = next(x for x in records if x["source_id"] == "SRC-004")
assert a["legacy_relation_hints"][0]["type"] == "LEGACY_DUPLICATE_GROUP"
assert b["legacy_relation_hints"][0]["type"] == "LEGACY_DUPLICATE_GROUP"
assert any(x.get("type") == "NEAR_DUPLICATE_OF" and x.get("target") == "SRC-004" for x in a["relations"])
assert any(x.get("type") == "NEAR_DUPLICATE_OF" and x.get("target") == "SRC-003" for x in b["relations"])

# 7. relation expansion can surface linked indexed source
r = search(records, "서울 PHONICS 학생용", limit=10, relation_depth=1)
ids = [x["source_id"] for x in r["results"]]
assert "SRC-001" in ids and "SRC-002" in ids

# 8. sourceRef/provenance are surfaced without leaking domain decision metadata
r = search(records, "서울 PHONICS 학생용")
assert r["results"][0]["source_ref"]["source_id"] == "SRC-001"
assert r["results"][0]["source_ref"]["locator"] == "DATA/phonics.pdf"
assert r["results"][0]["provenance"]["origin_type"] == "LOCAL_EDUCATION_AUTHORITY_PUBLICATION"
assert r["results"][0]["provenance"]["publisher_or_account"] == "SEOUL_EDU"

# 9. search projection does not expose domain decision fields as core result data
r = search(records, "학습도구어")
payload = json.dumps(r, ensure_ascii=False)
assert "DIRECT_USE_READY" not in payload
assert "LE-F02" not in payload
assert "MAPPED_NOT_CONNECTED" not in payload

# 10. semantic channel is explicitly fallback, not embedding claim
assert r["semantic_mode"] == "TOKEN_COSINE_FALLBACK__NOT_EMBEDDING_SEMANTIC"
assert r["projection_authoritative"] is False

# 11. DETAIL_L2 is preferred and RAW is not required when anchors exist
r = search(records, "서울 PHONICS 학생용")
esc = r["results"][0]["detail_escalation"]
assert esc["stage"] == "DETAIL_L2"
assert esc["raw_required"] is False
assert "practice page" in esc["detail_l2"]["anchors"]
assert esc["detail_l2"]["reviewed_units"]["reviewed_pages"] == [1, 2, 30, 57]

# 12. missing DETAIL explicitly escalates to RAW
r = search(records, "학습도구어")
esc = r["results"][0]["detail_escalation"]
assert esc["stage"] == "RAW_REQUIRED"
assert esc["reason"] == "DETAIL_UNAVAILABLE"
assert esc["raw_required"] is True

# 13. authority-preserving outcome utility rerank
utility_records = materialize_legacy_relations([normalize_record(r) for r in [
    {
        "source_id":"UTIL-CURRENT-LOW",
        "title":"공통 전략 자료",
        "source_family":"UTILITY_TEST",
        "current_relation":"CURRENT_INDEX_ENTRY",
        "outcome_utility":{"verified_success":0,"verified_failure":3}
    },
    {
        "source_id":"UTIL-OLD-HIGH",
        "title":"공통 전략 자료",
        "source_family":"UTILITY_TEST",
        "current_relation":"SUPERSEDED",
        "outcome_utility":{"verified_success":9,"verified_failure":0}
    },
    {
        "source_id":"UTIL-CURRENT-HIGH",
        "title":"공통 전략 자료",
        "source_family":"UTILITY_TEST",
        "current_relation":"CURRENT_INDEX_ENTRY",
        "outcome_utility":{"verified_success":5,"verified_failure":0}
    }
]])
r = search(utility_records, "공통 전략 자료", relation_depth=0)
ids = [x["source_id"] for x in r["results"]]
assert ids[0] == "UTIL-CURRENT-HIGH"
assert ids[1] == "UTIL-CURRENT-LOW"
assert ids[2] == "UTIL-OLD-HIGH"
assert r["results"][0]["ranking"]["outcome_utility"] > r["results"][1]["ranking"]["outcome_utility"]
assert r["results"][0]["ranking"]["rule"] == "EXACT -> CURRENT -> OUTCOME_UTILITY -> RETRIEVAL_SCORE"

# 14. exact source-id authority outranks CURRENT and utility
r = search(utility_records, "UTIL-OLD-HIGH", relation_depth=0)
assert r["results"][0]["source_id"] == "UTIL-OLD-HIGH"
assert r["results"][0]["ranking"]["exact_authority_tier"] == 0

# 15. CLI smoke test against a V24-like container
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "index.json"
    p.write_text(json.dumps({"source_entries": RECORDS}, ensure_ascii=False), encoding="utf-8")
    cli = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--index",
            str(p),
            "--query",
            "파닉스",
            "--filter",
            "authority=LOCAL_EDUCATION_AUTHORITY_PUBLISHED_MATERIAL",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    assert cli.returncode == 0, (cli.stdout, cli.stderr)
    data = json.loads(cli.stdout)
    assert data["results"][0]["source_id"] == "SRC-001"

# 16. auto-discover outcome utility sidecar through environment override
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    p = tmp / "index.json"
    u = tmp / "utility.json"
    p.write_text(json.dumps({"source_entries": [
        {"source_id":"AUTO-A","title":"동일 제목","current_relation":"CURRENT_INDEX_ENTRY"},
        {"source_id":"AUTO-B","title":"동일 제목","current_relation":"CURRENT_INDEX_ENTRY"}
    ]}, ensure_ascii=False), encoding="utf-8")
    u.write_text(json.dumps({
        "schema":"TAKY_DATA_INDEX_OUTCOME_UTILITY_V1",
        "authoritative":False,
        "by_source_id":{
            "AUTO-A":{"verified_success":0,"verified_failure":2},
            "AUTO-B":{"verified_success":4,"verified_failure":0}
        }
    }, ensure_ascii=False), encoding="utf-8")
    env = os.environ.copy()
    env["TAKY_DATA_INDEX_OUTCOME_UTILITY"] = str(u)
    # Pin the child stdout codec; the parent decodes UTF-8 regardless of locale.
    env["PYTHONIOENCODING"] = "utf-8"
    cli = subprocess.run(
        [sys.executable, str(SCRIPT), "--index", str(p), "--query", "동일 제목", "--relation-depth", "0"],
        capture_output=True, text=True, encoding="utf-8", env=env
    )
    assert cli.returncode == 0, (cli.stdout, cli.stderr)
    data = json.loads(cli.stdout)
    assert data["results"][0]["source_id"] == "AUTO-B"
    assert data["outcome_utility_projection"]["applied"] is True
    assert data["outcome_utility_projection"]["auto_discovered"] is True
    assert data["outcome_utility_projection"]["authoritative"] is False

print("data_index_search: PASS")
