#!/usr/bin/env python3
"""Read-only, exact-ID evidence provenance from the existing Index projection.

Mining may use Index-owned identity/relation evidence to *reduce* unsupported
corroboration, never create canonical records, infer publisher independence
from URLs, or make a domain-owner utilization decision.
"""
from __future__ import annotations

DUPLICATE_GROUP_RELATIONS={"EXACT_DUPLICATE_OF","VERSION_OF"}
REVIEWED_STATES={"REVIEWED","APPROVED","VERIFIED"}


def _id(row:dict)->str:
    identity=(row.get("index_l1") or {}).get("identity") or row.get("identity") or {}
    return str(row.get("source_id") or identity.get("source_id") or "")


def _canonical(row:dict)->str:
    identity=(row.get("index_l1") or {}).get("identity") or row.get("identity") or {}
    return str(row.get("canonical_source_id") or identity.get("canonical_source_id") or "")


def _reviewed(row:dict)->bool:
    if row.get("source_group_reviewed") is True:
        return True
    # General source review is NOT the same as a reviewed canonical grouping.
    state=row.get("canonical_group_review_state")
    return str(state or "").upper() in REVIEWED_STATES


def enrich_from_index(evidence:list[dict], index_rows:list[dict]|None=None,
                      index_relations:list[dict]|None=None)->list[dict]:
    rows={_id(row):row for row in (index_rows or []) if isinstance(row,dict) and _id(row)}
    parent={key:key for key in rows}
    def root(key):
        while parent[key]!=key:
            parent[key]=parent[parent[key]]
            key=parent[key]
        return key
    def union(a,b):
        ra,rb=root(a),root(b)
        if ra!=rb: parent[max(ra,rb)]=min(ra,rb)
    for rel in index_relations or []:
        if not isinstance(rel,dict): continue
        typ=str(rel.get("type") or "").upper()
        a=str(rel.get("from") or rel.get("source_id") or "")
        b=str(rel.get("to") or rel.get("target_id") or "")
        if typ in DUPLICATE_GROUP_RELATIONS and a in rows and b in rows:
            union(a,b)

    groups={}
    for source_id in rows:
        groups.setdefault(root(source_id),[]).append(source_id)

    out=[]
    for source in evidence or []:
        item=dict(source)
        # The legacy External Adapter does not reliably retain the receipt's
        # provider name; entering through this function is the origin evidence.
        item["evidence_origin"]="PROVIDER_RECEIPT"
        sid=str(item.get("source_id") or "")
        row=rows.get(sid)
        item["provenance_group_reviewed"]=False
        if row is None:
            item["provenance_match"]="NO_EXACT_INDEX_ID"
            out.append(item)
            continue
        item["provenance_match"]="INDEX_EXACT_SOURCE_ID"
        explicit=_canonical(row)
        if explicit:
            item["canonical_source_id"]=explicit
            item["provenance_group_reviewed"]=_reviewed(row)
            item["source_group_basis"]="INDEX_EXPLICIT_GROUP"
        elif len(groups[root(sid)])>1:
            # Exact/versions relations let us collapse duplicate observations.
            # That relation ALONE does not prove *different* independent publishers.
            item["canonical_source_id"]="INDEX_DUPLICATE_GROUP:"+root(sid)
            item["source_group_basis"]="INDEX_EXACT_OR_VERSION_RELATION"
        out.append(item)
    return out
