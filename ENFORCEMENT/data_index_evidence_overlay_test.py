#!/usr/bin/env python3
"""Synthetic evidence-note lineage/rights guards; no external source bytes in repo."""
from copy import deepcopy
from data_index_external_intake import SCHEMA as EXTERNAL, stage_external_candidates
from data_index_evidence_overlay import attach_selected_section_notes, SCHEMA, STATE, FACT_KIND

DOCUMENT_ID = "test-manifest-document"
def source(i,kind):
    return dict(schema=EXTERNAL,external_namespace="PROVIDER_"+str(i),
       provider_native_id="origin"+str(i),source_title="Source title "+str(i),
       original_locator="https://example.org/original/"+str(i),
       source_kind=kind,evidence_extent="LISTING_METADATA",
       rights_state="UNKNOWN_REVIEW_REQUIRED",privacy_class="PUBLIC",
       observed_at="2026-09-29",attribution="Original source publisher",
       content_hash=None,original_content_acquired=False,current_promoted=False)
base = dict(schema="TAKY_EXTERNAL_DISCOVERY_MANIFEST_V1", state="STAGED_LINK_ONLY_NOT_CURRENT",
    sources=[source(i,k) for i,k in enumerate(FACT_KIND)])
rows,_=stage_external_candidates(base["sources"])
def note(record):
    kind=record["intake_envelope"]["external_namespace"]
    source=next(x for x in base["sources"] if "EXTERNAL::"+x["external_namespace"]+"::"+x["provider_native_id"]==record["source_id"])
    method,status=FACT_KIND[source["source_kind"]]
    return dict(source_id=record["source_id"],original_locator=record["locator"],source_kind=source["source_kind"],
        inspection_method=method,fact_status=status,section_ref="The observed section",
        evidence_summary="Directly inspected part of this original source; this is a brief independent factual note, not full content.",
        limits="Only this chosen section was observed; not full source or complete issue verification.",
        reviewed_at="2026-09-29",content_hash=None,full_content_acquired=False,rights_verified=False,
        reuse_scope="SHORT_ORIGINAL_PARAPHRASE_ONLY",detail_location_verified="SECTION_LABEL_NOT_SPATIAL_BBOX")
evidence=dict(schema=SCHEMA,state=STATE,parent_manifest_document_id=DOCUMENT_ID,
    authority=dict(current_pointer_modified=False,source_manifest_modified=False,
        raw_full_content_acquired=False,rights_for_full_text_reuse_verified=False,source_hashes_verified=0),
    entries=[note(r) for r in rows])
before=deepcopy(rows),deepcopy(base),deepcopy(evidence)
out,receipt=attach_selected_section_notes(rows,base,evidence,DOCUMENT_ID)
assert (rows,base,evidence)==before
assert len(out)==4 and receipt["notes_joined"]==4
assert not receipt["current_promoted"] and not receipt["evidence_authenticated_cryptographically"]
assert all(r["short_summary"] and r["evidence_note"]["rights_verified"] is False for r in out)
assert all(r["current_relation"]=="NO_CURRENT_PROMOTION" and r["content_hash"] is None for r in out)
assert out[2]["evidence_note"]["fact_status"]=="ISSUE_AUTHOR_REPORTED_NOT_REPRODUCED"
assert out[3]["evidence_note"]["fact_status"]=="COMMUNITY_AUTHOR_REPORTED_NOT_GENERALIZED"

def rejects(modifier,expected):
    br,rr,ev=deepcopy(base),deepcopy(rows),deepcopy(evidence)
    modifier(br,rr,ev)
    try:attach_selected_section_notes(rr,br,ev,DOCUMENT_ID)
    except ValueError as exc:assert expected in str(exc),(expected,str(exc))
    else:raise AssertionError("unsupported evidence claim passed: "+expected)
rejects(lambda b,r,e:e.update(parent_manifest_document_id="other"),"PARENT_MANIFEST_MISMATCH")
rejects(lambda b,r,e:e["entries"][0].update(original_locator="https://another.example"),"ORIGIN_OR_ROLE_MISMATCH")
rejects(lambda b,r,e:e["entries"][0].update(source_kind="COMMUNITY_DISCUSSION"),"ORIGIN_OR_ROLE_MISMATCH")
rejects(lambda b,r,e:e["entries"][3].update(fact_status="OFFICIAL_STANDARD_SELECTED_SECTION"),"METHOD_OR_FACT_ROLE_INVALID")
rejects(lambda b,r,e:e["entries"][1].update(full_content_acquired=True),"CONTENT_OR_RIGHTS_OVERCLAIM")
rejects(lambda b,r,e:e["entries"][1].update(rights_verified=True),"CONTENT_OR_RIGHTS_OVERCLAIM")
rejects(lambda b,r,e:e["entries"][1].update(content_hash="invented"),"CONTENT_OR_RIGHTS_OVERCLAIM")
rejects(lambda b,r,e:e["entries"][1].update(section_ref=""),"EVIDENCE_SECTION_REF_REQUIRED")
rejects(lambda b,r,e:e["entries"].append(deepcopy(e["entries"][0])),"EVIDENCE_COVERAGE_MISMATCH")
rejects(lambda b,r,e:e["authority"].update(source_hashes_verified=True),"HASH_PROOF_NOT_ALLOWED")
rejects(lambda b,r,e:e["authority"].update(current_pointer_modified=True),"AUTHORITY_OVERCLAIM")
rejects(lambda b,r,e:r[0].update(short_summary="older"),"WOULD_OVERWRITE_EXISTING_SUMMARY")
rejects(lambda b,r,e:r[0]["intake_envelope"].update(privacy_class="RESTRICTED"),"PROJECTION_BOUNDARY_INVALID")
rejects(lambda b,r,e:r[0].update(locator="https://different.example"),"PROJECTION_BOUNDARY_INVALID")
print("data_index_evidence_overlay: PASS (4 original roles, non-promotion, 14 negative gates)")
