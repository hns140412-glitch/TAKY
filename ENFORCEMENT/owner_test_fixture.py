"""Synthetic independent-owner fixture only. No live source/credential or real receipt."""
from __future__ import annotations
import hashlib

FIELDS=("source_id","source_ref","index_version","locator","content_hash")
def make_row(source_id,canonical_title,*,authorization_class="READY_WITH_GUARDS",
             authority_class="OFFICIAL",**extra):
    digest=hashlib.sha256(("TEST_ONLY:"+source_id).encode()).hexdigest()
    return dict(source_id=source_id,canonical_title=canonical_title,
        source_ref="TEST_ONLY:OWNER:"+source_id,index_version="FIXTURE_V1",
        locator="https://example.test/owner/"+source_id,content_hash=digest,
        index_state="INDEXED",authorization_class=authorization_class,
        authority_class=authority_class,**extra)

def verifier_for(*rows):
    # Immutable fixture registry, separate from the proposed row.
    registry={r["source_id"]:dict(r) for r in rows}
    def verify(source_id,proposal):
        row=registry.get(source_id)
        if not row or any(proposal.get(k)!=row[k] for k in FIELDS):
            return None
        return {"receipt":{
            "issuer":"INDEXING_OWNER","reviewed":True,"decision":"INDEXED",
            **{k:row[k] for k in FIELDS},
            "review_evidence_refs":["TEST_ONLY_INDEPENDENT_OWNER_REGISTRY:"+source_id],
            "domain_use_authorized":True,
            "canonical_promotion":False,"current_promoted":False},
            "index_row":dict(row)}
    return verify
