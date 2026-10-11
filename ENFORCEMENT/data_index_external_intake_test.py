#!/usr/bin/env python3
"""Four-provider, link-only intake regression with negative gates."""
from copy import deepcopy
from data_index_external_intake import SCHEMA, project_external_candidate, stage_external_candidates
kinds = ["OFFICIAL_STANDARD", "PUBLIC_API_LISTING", "OPEN_SOURCE_ISSUE", "COMMUNITY_DISCUSSION"]
def fixture(i):
    return dict(schema=SCHEMA, external_namespace="PROVIDER_"+str(i), provider_native_id="origin"+str(i),
        source_title="Independent source", original_locator="https://example.org/item/"+str(i),
        source_kind=kinds[i], evidence_extent="LINK_ONLY", rights_state="UNKNOWN_REVIEW_REQUIRED",
        privacy_class="PUBLIC", observed_at="2026-09-29", attribution="Source owner",
        content_hash=None, original_content_acquired=False, current_promoted=False)
rows = [fixture(i) for i in range(4)]
original = deepcopy(rows)
staged, receipt = stage_external_candidates(rows)
assert len(staged) == 4 and len({x["source_id"] for x in staged}) == 4
assert receipt["current_pointer_modified"] is False and rows == original
assert all(x["content_hash"] is None and not x["detail_available"] for x in staged)
assert all(x["intake_envelope"]["current_promoted"] is False for x in staged)
duplicate = deepcopy(rows[0]); duplicate["provider_native_id"] = "another"
uncollapsed, report = stage_external_candidates([rows[0], duplicate])
assert len(uncollapsed) == 2 and len(report["same_locator_candidates"]) == 1
for key, value in (("content_hash", "unverified"), ("current_promoted", True), ("original_content_acquired", True),
                   ("original_locator", "http://invalid"), ("rights_state", "ASSERTED_OPEN")):
    bad = deepcopy(rows[0]); bad[key] = value
    try: project_external_candidate(bad)
    except ValueError: pass
    else: raise AssertionError("unsupported intake passed: "+key)
for entries in ([rows[0], rows[0]], [rows[0]]):
    existing = set() if len(entries) == 2 else {staged[0]["source_id"]}
    try: stage_external_candidates(entries, existing)
    except ValueError as e: assert "COLLISION" in str(e)
    else: raise AssertionError("duplicate provider ID accepted")
print("data_index_external_intake: PASS (4 provider types, metadata/rights/identity gates)")
