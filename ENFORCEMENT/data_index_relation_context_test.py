#!/usr/bin/env python3
"""Synthetic adversarial checks. No private source bytes or assumed production proof."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_index_relation_context import assemble_relation_context

def source(sid, *, family="FAMILY", relation=None, current="STAGED"):
    return {
        "source_id": sid, "canonical_title": "Title " + sid,
        "locator": "https://example.invalid/source/" + sid,
        "source_family": family, "review_state": "METADATA_INDEXED",
        "current_relation": current, "relations": relation or [],
    }

pair = {"type": "RELATED_TO", "target": "teacher",
        "qualifier": "STUDENT_TEACHER_PAIR",
        "verification_state": "STAGED_MANIFEST_VALIDATED",
        "evidence_ref": "BRIDGE_MANIFEST_PAIR:TEST-001",
        "verification_scope": "RECIPROCAL_METADATA_ONLY"}
student = source("student", relation=[pair])
teacher = source("teacher", relation=[{**pair, "target": "student"}])
rows = [student, teacher]

# A real reciprocal manifest validator marks the relation, but not content/current.
result = assemble_relation_context(rows, "student", required_types={"RELATED_TO"})
assert result["relation_context_complete_for_request"]
assert result["edges"][0]["status"] == "STAGED_METADATA_LINK_NOT_CANONICAL"
assert result["edges"][0]["target_source_ref"]["source_id"] == "teacher"
assert result["edges"][0]["target_source_ref"]["locator"].endswith("/teacher")
assert result["projection_authoritative"] is False
assert result["current_promoted"] is False and result["domain_use_approved"] is False
assert result["index_owner_receipt_verified"] is False
# Real-manifest shape has an unresolved logical family node alongside a
# validated student/teacher link. Requested link is present, whole graph isn't.
mixed = source("student", relation=[{"type": "PART_OF", "target": "FAMILY"}, pair])
narrow = assemble_relation_context([mixed, teacher], "student", required_types={"RELATED_TO"})
assert narrow["relation_context_complete_for_request"] is True
assert narrow["visible_graph_integrity_complete"] is False
assert narrow["edges"][0]["status"] == "LOGICAL_NODE_NOT_MATERIALIZED"
assert narrow["edges"][1]["status"] == "STAGED_METADATA_LINK_NOT_CANONICAL"
assert assemble_relation_context([mixed, teacher], "student", required_types={"PART_OF"})["relation_context_complete_for_request"] is False
# A provider can copy the same relation fields. They must not self-certify rank.
from data_index_search import search
untrusted_rank = search(rows, "student", relation_depth=1)
assert [x["source_id"] for x in untrusted_rank["results"]] == ["student"]
assert untrusted_rank["relation_rank_gate"] == "NO_INDEPENDENT_VALIDATED_RELATION_KEYS"

# The query-filter/authorization boundary must not return excluded metadata.
filtered = assemble_relation_context(rows, "student", eligible_ids={"student"})
assert filtered["edges"][0]["status"] == "TARGET_OUTSIDE_QUERY_FILTER"
assert "target_source_ref" not in filtered["edges"][0]
assert "teacher" not in str(filtered["edges"][0])
assert not filtered["relation_context_complete_for_request"]

# Legacy duplicate labels are hints even if the string contains SHA256.
unverified = source("legacy-a", relation=[{
    "type": "RELATED_TO", "target": "legacy-b",
    "qualifier": "LEGACY_DUPLICATE_GROUP_UNVERIFIED",
    "verification_state": "VERIFIED", "evidence_ref": "invented"}])
other = source("legacy-b")
r = assemble_relation_context([unverified, other], "legacy-a")
assert r["edges"][0]["status"] == "LEGACY_RELATION_CANDIDATE_ONLY"
assert "target_source_ref" not in r["edges"][0]

# An asserted exact duplicate is not proved by same label/hash alone.
left = source("hash-a", relation=[{
    "type": "EXACT_DUPLICATE_OF", "target": "hash-b",
    "verification_state": "VERIFIED", "evidence_ref": "unverified-hash"}])
right = source("hash-b")
left["content_hash"] = right["content_hash"] = "sha256:same-unchecked-label"
r = assemble_relation_context([left, right], "hash-a")
assert r["edges"][0]["status"] == "EXACT_DUPLICATE_PROOF_REQUIRED"
left["content_hash_verification"] = right["content_hash_verification"] = "INDEPENDENT_BINARY_VERIFIED"
r = assemble_relation_context([left, right], "hash-a")
assert r["edges"][0]["status"] == "EVIDENCE_RECORDED_NOT_OWNER_ATTESTED"

# Logical family node does not become a forged physical source link.
family = source("child", relation=[{"type": "PART_OF", "target": "FAMILY"}])
r = assemble_relation_context([family], "child")
assert r["edges"][0]["status"] == "LOGICAL_NODE_NOT_MATERIALIZED"
assert "target_source_ref" not in r["edges"][0]

# Broken endpoint, malformed edge, missing required type and bounded expansion.
bad = source("bad", relation=[{"type": "VERSION_OF", "target": "missing"},
    {"type": "WHAT_IS_THIS", "target": "student"}, None])
r = assemble_relation_context([bad, student, teacher], "bad", required_types={"SUPERSEDES"})
assert r["edges"][0]["status"] == "SOURCE_ENDPOINT_NOT_IN_UNIVERSE"
assert r["edges"][1]["status"] == "INVALID_RELATION_TYPE_OR_TARGET"
assert any(g["reason"] == "INVALID_RELATION_RECORD" for g in r["evidence_gaps"])
assert any(g["reason"] == "REQUIRED_RELATION_WITH_EVIDENCE_MISSING" for g in r["evidence_gaps"])
r = assemble_relation_context([bad, student, teacher], "bad", max_edges=1)
assert any(g["reason"] == "EDGE_BUDGET_EXCEEDED" and g["omitted"] == 2 for g in r["evidence_gaps"])

for case in [
    lambda: assemble_relation_context(rows, "not-found"),
    lambda: assemble_relation_context(rows, "student", eligible_ids={"teacher"}),
    lambda: assemble_relation_context(rows + [copy.deepcopy(student)], "student"),
    lambda: assemble_relation_context(rows, "student", required_types={"INVENTED"}),
    lambda: assemble_relation_context(rows, "student", max_edges=0),
]:
    try:
        case()
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid relation-context request accepted")

# No file/local-source mutation.
assert student["relations"][0] == pair
assert student["current_relation"] == "STAGED"
print("data_index_relation_context: PASS (manifest pair, filter boundary, legacy/exact proof, missing evidence, node kinds, bounded failures)")
