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
print("data_index_gap_router: PASS (routing, no auto mining, privacy, replay, returns, negative gates)")
