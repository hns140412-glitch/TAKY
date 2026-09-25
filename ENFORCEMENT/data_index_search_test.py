import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "data_index_search.py"
sys.path.insert(0, str(ROOT))

from data_index_search import normalize_record, search

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
                "media_type": "application/pdf",
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

records = [normalize_record(r) for r in RECORDS]

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

# 6. duplicate-group compatibility hint does not become exact-duplicate identity
a = next(x for x in records if x["source_id"] == "SRC-003")
b = next(x for x in records if x["source_id"] == "SRC-004")
assert a["legacy_relation_hints"][0]["type"] == "LEGACY_DUPLICATE_GROUP"
assert b["legacy_relation_hints"][0]["type"] == "LEGACY_DUPLICATE_GROUP"
assert not any(x.get("type") == "EXACT_DUPLICATE_OF" for x in a["relations"])

# 7. relation expansion can surface linked indexed source
r = search(records, "서울 PHONICS 학생용", limit=10, relation_depth=1)
ids = [x["source_id"] for x in r["results"]]
assert "SRC-001" in ids and "SRC-002" in ids

# 8. search projection does not expose domain decision fields as core result data
r = search(records, "학습도구어")
payload = json.dumps(r, ensure_ascii=False)
assert "DIRECT_USE_READY" not in payload
assert "LE-F02" not in payload
assert "MAPPED_NOT_CONNECTED" not in payload

# 9. semantic channel is explicitly fallback, not embedding claim
assert r["semantic_mode"] == "TOKEN_COSINE_FALLBACK__NOT_EMBEDDING_SEMANTIC"
assert r["projection_authoritative"] is False

# 10. CLI smoke test against a V24-like container
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
    )
    assert cli.returncode == 0, (cli.stdout, cli.stderr)
    data = json.loads(cli.stdout)
    assert data["results"][0]["source_id"] == "SRC-001"

# 11. default family diversification caps same-family results at 3
family_records = [
    normalize_record(
        {
            "source_id": f"FAM-{i:02d}",
            "title": f"Architecture item {i}",
            "source_family": "ARCHITECTURE_WORK_SOURCE" if i < 5 else f"OTHER_FAMILY_{i}",
            "source_type": "REFERENCE",
            "authority_level": "REFERENCE_ONLY",
        }
    )
    for i in range(8)
]
r = search(family_records, "Architecture", limit=8, relation_depth=0)
families = [x["source_family"] for x in r["results"]]
assert families.count("ARCHITECTURE_WORK_SOURCE") <= 3
assert r["family_cap_applied"] is True
assert r["family_cap"] == 3

# 12. explicit family request lifts the default family cap
r = search(family_records, "ARCHITECTURE_WORK_SOURCE", limit=8, relation_depth=0)
families = [x["source_family"] for x in r["results"]]
assert families.count("ARCHITECTURE_WORK_SOURCE") == 5
assert r["family_cap_applied"] is False
assert r["family_cap"] is None

print("data_index_search: PASS")
