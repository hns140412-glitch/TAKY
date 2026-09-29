#!/usr/bin/env python3
"""No private corpus: synthetic INDEX -> MINING reverse-loop regressions."""
import copy
from data_index_gap_router import build_gap_proposal, deduplicate_proposals, validate_mining_return
BASE = {
    "scope_namespace": "DATA_TEST", "gap_kind": "ORIGINAL_MISSING", "source_refs": ["SRC-1"],
    "evidence_question": "Where is the primary original document?",
    "desired_evidence": "Primary original or official publication listing",
    "why_index_insufficient": "Only a derivative screenshot exists",
    "index_check": "CHECKED_INSUFFICIENT", "raw_access": "MISSING",
    "attempted_checks": ["SOURCE_CATALOG", "DETAIL_L2", "ORIGINAL_LOCATOR"],
    "minimum_authority": "PRIMARY_SOURCE_PREFERRED", "freshness_requirement": "PUBLICATION_DATE_AND_VERSION",
    "privacy_class": "PUBLIC", "rights_state": "UNKNOWN",
}

def test(g, expected):
    p = build_gap_proposal(g)
    assert p["route"] == expected, (g, p)
    assert p["state"] == "DRAFT_NOT_DISPATCHED" and not p["actions_performed"]
    assert p["indexing_resume"]["current_promotion"] == "REQUIRES_SEPARATE_APPROVAL"
    if expected != "MINING_REQUEST_DRAFT":
        assert p["mining_handoff"] is None
    return p

p = test(BASE, "MINING_REQUEST_DRAFT")
assert p["mining_handoff"]["evidence_gap"] == BASE["evidence_question"]
assert deduplicate_proposals([BASE, copy.deepcopy(BASE)])[0]["request_id"] == p["request_id"]
assert len(deduplicate_proposals([BASE, copy.deepcopy(BASE)])) == 1
for kind in ("VERSION_UNRESOLVED", "CONTRADICTORY_SOURCES", "COVERAGE_MISSING", "PRIMARY_PROVENANCE_MISSING", "RIGHTS_UNCLEAR"):
    test({**BASE, "gap_kind":kind, "raw_access":"ACCESSIBLE"}, "MINING_REQUEST_DRAFT")
for kind in ("DETAIL_ANCHOR_MISSING", "CLASSIFICATION_AMBIGUOUS", "DUPLICATE_PROOF_MISSING", "RETRIEVAL_LOW_RECALL"):
    test({**BASE, "gap_kind":kind, "raw_access":"ACCESSIBLE"}, "INDEXING_INTERNAL")
    test({**BASE, "gap_kind":kind, "raw_access":"NOT_CHECKED"}, "INDEXING_PRECHECK")
    test({**BASE, "gap_kind":kind, "raw_access":"DENIED"}, "MINING_REQUEST_DRAFT")
test({**BASE, "index_check":"NOT_CHECKED"}, "INDEXING_PRECHECK")
test({**BASE, "gap_kind":"DOMAIN_POLICY_QUESTION"}, "DOMAIN_CONSUMER")
assert test({**BASE, "privacy_class":"AUTHORIZED_PRIVATE"}, "MINING_REQUEST_DRAFT")["mining_handoff"]["search_constraints"]["privacy_constraint"] == "NO_EXTERNAL_ACCOUNT_DISCLOSURE"
assert test({**BASE, "privacy_class":"RESTRICTED"}, "MINING_REQUEST_DRAFT")["mining_handoff"]["search_constraints"]["privacy_constraint"] == "NO_EXTERNAL_ACCOUNT_DISCLOSURE"
test({**BASE, "gap_kind":"ACCESS_BLOCKED", "raw_access":"DENIED", "desired_evidence":"Authorized partial-frame/local-sync access"}, "MINING_REQUEST_DRAFT")
test({**BASE, "gap_kind":"RETRIEVAL_LOW_RECALL", "raw_access":"ACCESSIBLE"}, "INDEXING_INTERNAL")
receipt={"request_id":p["request_id"],"outcome":"LINK_ONLY","provider_native_id":"source-001","original_locator":"https://official.example/resource","observed_at":"2026-09-29","provenance_evidence":"primary listing attribution","access_status":"METADATA_ONLY"}
out=validate_mining_return(receipt,p)
assert out["state"]=="RETURNED_FOR_INDEX_VALIDATION_NOT_CANONICAL" and out["current_promotion"] is False
assert validate_mining_return({"request_id":p["request_id"],"outcome":"BLOCKED"},p)["indexing_next"] == "KEEP_EVIDENCE_GAP_OPEN"
for bad in ({**receipt,"request_id":"wrong"},{**receipt,"original_locator":""},{**receipt,"outcome":"VERIFIED_CURRENT"}):
    try: validate_mining_return(bad,p)
    except ValueError: pass
    else: raise AssertionError("bad mining return accepted")
for field in ("scope_namespace","gap_kind","evidence_question","why_index_insufficient","minimum_authority","freshness_requirement"):
    try: build_gap_proposal({**BASE,field:""})
    except ValueError: pass
    else: raise AssertionError("missing field accepted: "+field)
# A relationship miss reuses the same Index-first proposal path, not a new queue.
from data_index_gap_router import proposals_from_relation_context
relation_context = {
    "schema": "TAKY_INDEX_RELATION_CONTEXT_V1",
    "root_source_ref": {"source_id": "SRC-REL"},
    "evidence_gaps": [
        {"type": "RELATED_TO", "reason": "RELATION_EVIDENCE_MISSING"},
        {"type": "RELATED_TO", "reason": "TARGET_OUTSIDE_QUERY_FILTER"},
        {"type": "EXACT_DUPLICATE_OF", "reason": "EXACT_DUPLICATE_PROOF_REQUIRED"},
        {"type": "PART_OF", "reason": "LOGICAL_NODE_NOT_MATERIALIZED"},
        {"type": "VERSION_OF", "reason": "SOURCE_ENDPOINT_NOT_IN_UNIVERSE"},
        {"reason": "EDGE_BUDGET_EXCEEDED"},
    ],
}
q = proposals_from_relation_context(relation_context, scope_namespace="DATA_TEST",
                                    privacy_class="AUTHORIZED_PRIVATE")
assert len(q["proposals"]) == 4
assert {x["route"] for x in q["proposals"]} == {"INDEXING_PRECHECK"}
assert len(q["local_holds"]) == 2
assert q["local_holds"][0]["target_metadata_returned"] is False
assert not q["mining_requests_dispatched"] and not q["current_promoted"]
assert all(x["mining_handoff"] is None for x in q["proposals"])
active = proposals_from_relation_context(relation_context, scope_namespace="DATA_TEST",
                                         privacy_class="AUTHORIZED_PRIVATE", raw_access="ACCESSIBLE")
assert sum(x["route"] == "INDEXING_INTERNAL" for x in active["proposals"]) == 3
assert sum(x["route"] == "INDEXING_PRECHECK" for x in active["proposals"]) == 1
denied = proposals_from_relation_context(relation_context, scope_namespace="DATA_TEST",
                                         privacy_class="RESTRICTED", raw_access="DENIED")
assert sum(x["route"] == "MINING_REQUEST_DRAFT" for x in denied["proposals"]) == 3
assert all(x["mining_handoff"]["search_constraints"]["privacy_constraint"] == "NO_EXTERNAL_ACCOUNT_DISCLOSURE"
           for x in denied["proposals"] if x["route"] == "MINING_REQUEST_DRAFT")
assert all("SRC-REL" not in x["mining_handoff"]["evidence_gap"]
           for x in denied["proposals"] if x["route"] == "MINING_REQUEST_DRAFT")
assert len(proposals_from_relation_context({"schema":"TAKY_INDEX_RELATION_CONTEXT_V1",
    "root_source_ref":{"source_id":"SRC-REL"},"evidence_gaps":[]},
    scope_namespace="DATA_TEST",privacy_class="PUBLIC")["proposals"]) == 0
for invalid in [
    {**relation_context, "schema": "FORGED"},
    {**relation_context, "root_source_ref": {"source_id": ""}},
    {**relation_context, "evidence_gaps": [None]},
]:
    try:
        proposals_from_relation_context(invalid, scope_namespace="DATA_TEST",privacy_class="PUBLIC")
    except ValueError:
        pass
    else:
        raise AssertionError("Bad relation context accepted")
print("data_index_gap_router: PASS (relation context -> Index-first reversible drafts and filter holds)")

print("data_index_gap_router: PASS (routing, no auto mining, privacy, replay, returns, negative gates)")
