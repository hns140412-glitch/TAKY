"""Reconcile technical state damaged by rediscovering an identical RAW SHA.

Only a fully reverified local TAKY_REVIEW_RAW text DETAIL can be restored from
PENDING/RAW_VERIFIED to DONE/INDEXED_CANDIDATE. No meaning or approval changes.
"""
import argparse
import json
import sqlite3
from pathlib import Path

import taky_central_source_factory as factory


def select_inconsistent(c,limit=100):
    if not isinstance(limit,int) or not 1<=limit<=500:
        raise ValueError("REPAIR_BUDGET_INVALID")
    rows=c.execute("""SELECT s.id AS source_id,s.original_sha256 AS raw_sha256,s.status,
        e.state AS extraction_state,i.state AS index_state
      FROM source s JOIN stage e ON s.id=e.source_id AND e.stage='EXTRACT'
      JOIN stage i ON s.id=i.source_id AND i.stage='INDEX'
      WHERE e.state='PENDING' AND i.state='TECHNICAL_INDEX_READY'
        AND s.original_sha256 IS NOT NULL
        AND s.status IN ('RAW_VERIFIED','INDEXED_CANDIDATE')
        AND s.authoritative_review='UNREVIEWED'
        AND EXISTS (SELECT 1 FROM evidence_unit u WHERE u.source_id=s.id)
      ORDER BY s.id LIMIT ?""",(limit,)).fetchall()
    return [dict(r) for r in rows]


def repair_one(c,row):
    sid=row["source_id"]
    if (sid!="raw:"+row["raw_sha256"] or row["extraction_state"]!="PENDING"
        or row["index_state"]!="TECHNICAL_INDEX_READY"
        or row["status"] not in ("RAW_VERIFIED","INDEXED_CANDIDATE")):
        raise ValueError("REPAIR_INVALID_STAGE_BOUNDARY")
    units=c.execute("""SELECT unit_id,raw_sha256,review_state
       FROM evidence_unit WHERE source_id=? ORDER BY line_start,unit_id""",(sid,)).fetchall()
    if not units or len(units)>500:
        raise ValueError("REPAIR_MISSING_OR_OVERSIZED_DETAIL")
    for unit in units:
        if unit["raw_sha256"]!=row["raw_sha256"] or unit["review_state"]!="EXTRACTIVE_UNREVIEWED":
            raise ValueError("REPAIR_EVIDENCE_REVIEW_SCOPE_CHANGED")
        checked=factory.read_verified_evidence_unit(c,sid,unit["unit_id"])
        if (checked is None or checked["raw_sha256"]!=row["raw_sha256"]
            or checked["review_state"]!="EXTRACTIVE_UNREVIEWED"
            or checked["source_authority"]!="UNREVIEWED"):
            raise ValueError("REPAIR_ORIGINAL_BYTES_OR_ANCHOR_INVALID")
    factory.put_stage(c,sid,"EXTRACT","DONE",{
        "restored_from":"HASH_BOUND_TEXT_DETAIL_AFTER_SHA_REINGEST",
        "raw_sha256":row["raw_sha256"],"verified_detail_units":len(units),
        "semantic_approval":False})
    if row["status"]!="INDEXED_CANDIDATE":
        c.execute("UPDATE source SET status='INDEXED_CANDIDATE',changed_at=? WHERE id=?",
                  (factory.utc(),sid))
    factory.event(c,sid,"TECHNICAL_STAGE_RECONCILED_FROM_RAW_EVIDENCE",{
        "raw_sha256":row["raw_sha256"],"verified_detail_units":len(units),
        "semantic_approved":False,"learning_eligible":False})
    if c.execute("SELECT state FROM stage WHERE source_id=? AND stage='EXTRACT'",(sid,)).fetchone()[0]!="DONE":
        raise ValueError("REPAIR_STATE_READBACK_FAILED")
    return {"source_id":sid,"fully_reverified_anchor_count":len(units)}


def reconcile(c, limit=100):
    rows=select_inconsistent(c,limit)
    results=[]
    for row in rows:
        c.execute("SAVEPOINT repair_source")
        try:
            item=repair_one(c,row)
            c.execute("RELEASE SAVEPOINT repair_source")
            results.append(item)
        except BaseException:
            c.execute("ROLLBACK TO SAVEPOINT repair_source")
            c.execute("RELEASE SAVEPOINT repair_source")
            raise
    return {"status":"RAW_INDEX_STAGE_RECONCILED_UNREVIEWED",
      "corrected_sources":len(results),
      "verified_original_line_units":sum(x["fully_reverified_anchor_count"] for x in results),
      "corrected_source_ids":[x["source_id"] for x in results],
      "new_approved_semantics":0,"CURRENT_mutated":False,
      "LEARNING_promoted":False,"paid_api_calls":0}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--limit",type=int,default=100)
    p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    if args.apply:
        with factory.connect() as c:result=reconcile(c,args.limit)
    else:
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row
            items=select_inconsistent(c,args.limit)
            result={"status":"TECHNICAL_STAGE_REPAIR_PREVIEW",
                    "potential_sources":len(items),
                    "source_ids":[x["source_id"] for x in items],
                    "writes":0}
    print(json.dumps(result,ensure_ascii=True))


if __name__=="__main__":
    main()
