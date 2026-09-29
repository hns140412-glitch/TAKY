#!/usr/bin/env python3
"""Adversarial offline assurance tests: no real source IDs, private content or API."""
import copy
import json

from data_index_lifecycle_assurance import audit_projected_universe, plan_incremental_impact


def record(sid, title, relations=None, **extra):
    return {
        "source_id": sid, "canonical_title": title, "locator": "https://example.invalid/" + sid,
        "source_family": "FAMILY", "relations": relations or [],
        "field_lineage": {"source_family": "SOURCE_V6_RECORDED",
                          "short_summary": "SOURCE_V6_CONTENT_REVIEWED"},
        **extra,
    }


pair = {"type": "RELATED_TO", "target": "teacher", "verification_state": "STAGED_MANIFEST_VALIDATED",
        "evidence_ref": "PAIR:synthetic"}
rows = [
    record("student", "Visual ID", [
        {"type": "PART_OF", "target": "FAMILY"},
        pair,
    ], short_summary="directly reviewed source material"),
    record("teacher", "visual id", [{"**": "noise", "type": "RELATED_TO", "target": "student",
                                     "verification_state": "STAGED_MANIFEST_VALIDATED",
                                     "evidence_ref": "PAIR:synthetic"}],
           field_lineage={"source_family": "UTILIZATION_V26_DERIVED_CANDIDATE",
                          "short_summary": "UNKNOWN_NOT_INFERRED"}),
]
before = copy.deepcopy(rows)
r = audit_projected_universe(rows, expected_source_ids={"student", "teacher"})
assert r["source_identity_conserved"] is True and r["source_count"] == 2
assert r["casefold_title_collision_groups_not_merged"] == 1
assert r["evidence_state_counts"]["family_source_recorded"] == 1
assert r["evidence_state_counts"]["family_derived_candidate"] == 1
assert r["evidence_state_counts"]["summary_source_reviewed"] == 1
assert r["evidence_state_counts"]["logical_family_or_package_unmaterialized"] == 1
assert r["evidence_state_counts"]["resolved_physical_edge"] == 2
assert r["evidence_state_counts"]["content_hash_unknown"] == 2
assert r["evidence_state_counts"]["privacy_scope_not_attested_in_projection"] == 2
assert not r["projection_authoritative"] and not r["index_owner_receipt_verified"]
assert not r["current_promoted"] and not r["domain_use_approved"]
assert (rows == before), "read-only projection mutated"

# The reconciliation oracle must compare exact source IDs, not just the count.
lost = audit_projected_universe(rows, expected_source_ids={"student", "missing"})
assert lost["missing_expected_count"] == 1 and lost["unexpected_count"] == 1
assert lost["source_identity_conserved"] is False
assert "student" not in json.dumps(lost) and "teacher" not in json.dumps(lost)

# Casefold title collisions are warnings; source identifiers remain case-sensitive.
case_ids = [record("Visual-ID", "One"), record("visual-id", "Two")]
assert audit_projected_universe(case_ids, expected_source_ids={"Visual-ID", "visual-id"})["source_identity_conserved"]
for invalid in ([rows[0], rows[0]], [record("", "invalid")], [None]):
    try:
        audit_projected_universe(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid identity accepted")

# No dangling endpoint can silently disappear during merge; family is logical,
# not a fabricated physical document.
broken = [record("A", "alpha", [{"type": "DERIVED_FROM", "target": "discarded-delta-id"}])]
report = audit_projected_universe(broken, expected_source_ids={"A"})
assert report["issue_counts"]["DANGLING_PHYSICAL_EDGE"] == 1
assert report["state"] == "STRUCTURAL_GAPS"

# A label or hash without independently verified source bytes is NOT binary proof.
dup = [
    record("A", "alpha", [{"type": "EXACT_DUPLICATE_OF", "target": "B",
                            "verification_state": "VERIFIED", "evidence_ref": "CLAIMED"}],
           content_hash="sha256:unchecked"),
    record("B", "beta", content_hash="sha256:unchecked"),
]
report = audit_projected_universe(dup)
assert report["issue_counts"]["EXACT_DUPLICATE_PROOF_MISSING"] == 1
assert report["evidence_state_counts"]["content_hash_not_independently_verified"] == 2

# Cyclic recorded supersession is invalid; a latest filename may never solve it.
version = [
    record("A", "rev-a", [{"type": "SUPERSEDES", "target": "B",
                          "verification_state": "VERIFIED", "evidence_ref": "synthetic-a"}]),
    record("B", "rev-b", [{"type": "SUPERSEDES", "target": "A",
                          "verification_state": "VERIFIED", "evidence_ref": "synthetic-b"}]),
]
assert audit_projected_universe(version)["issue_counts"]["RECORDED_SUPERSESSION_CYCLE"] == 1

# A -> dependent B -> dependent C: modifying A must invalidate all three.
lineage = [
    record("A", "raw"),
    record("B", "detail", [{"type": "DERIVED_FROM", "target": "A"}]),
    record("C", "search", [{"type": "EXTRACTED_FROM", "target": "B"}]),
    record("D", "related-only", [{"type": "RELATED_TO", "target": "A"}]),
]
events = [{"event_id": "evt-001", "source_id": "A", "change_type": "MODIFIED"}]
plan = plan_incremental_impact(lineage, events + copy.deepcopy(events),
                               start_cursor="cursor-start", end_cursor=None,
                               change_feed_exhausted=False)
assert plan["unique_event_count"] == 1
assert plan["dependency_impacted_count"] == 3
assert plan["related_review_only_count"] == 1
assert not plan["cursor_committed"] and not plan["current_promoted"] and not plan["raw_deleted"]
assert plan["source_identifiers_returned"] is False
assert '"source_id": "A"' not in json.dumps(plan) and "evt-001" not in json.dumps(plan)
assert plan["consumer_artifact_recheck_required"] and plan["detail_anchor_recheck_required"]
assert plan["end_cursor_present"] is False

# End-of-feed alone cannot self-approve pointer/cursor promotion.
end = plan_incremental_impact(lineage, events, start_cursor="start", end_cursor="end",
                              change_feed_exhausted=True)
assert end["end_cursor_present"] and end["change_feed_end_seen"] and not end["cursor_committed"]
revoked = plan_incremental_impact(lineage, [
    {"event_id": "evt-access", "source_id": "A", "change_type": "ACCESS_REVOKED"}],
    start_cursor="start", end_cursor="end", change_feed_exhausted=True)
assert revoked["authority_and_access_recheck_required"]
new = plan_incremental_impact(lineage, [
    {"event_id": "evt-new", "source_id": "brand-new", "change_type": "NEW"}],
    start_cursor="start", end_cursor="end", change_feed_exhausted=True)
assert new["changed_source_count"] == 1 and new["cursor_committed"] is False

for bad_events in (
    [{"event_id": "same", "source_id": "A", "change_type": "MODIFIED"},
     {"event_id": "same", "source_id": "B", "change_type": "MODIFIED"}],
    [{"event_id": "evt", "source_id": "unknown", "change_type": "MODIFIED"}],
    [{"event_id": "evt", "source_id": "A", "change_type": "PROMOTE_CURRENT"}],
):
    try:
        plan_incremental_impact(lineage, bad_events, start_cursor="start",
                                end_cursor=None, change_feed_exhausted=False)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid delta accepted")
try:
    plan_incremental_impact(lineage, events, start_cursor="start", end_cursor="end",
                            change_feed_exhausted=False, max_affected=2)
except ValueError as exc:
    assert "IMPACT_SCOPE_LIMIT_EXCEEDED" in str(exc)
else:
    raise AssertionError("impact cap ignored")
assert all(isinstance(x, dict) for x in lineage) and len(lineage) == 4
print("data_index_lifecycle_assurance: PASS (source set conservation, case identity, graph edges/cycles, lineage evidence, incremental impact and fail-closed negative gates)")
