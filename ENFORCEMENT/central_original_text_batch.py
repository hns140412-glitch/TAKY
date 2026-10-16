"""TAKY RAW body-text -> hash/line anchored Central DETAIL, never semantic authority.

Only independently SHA-verified, original captured source.txt files are eligible.
Small, deterministic local batches; no model/API, indexing promotion or CURRENT write.
"""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import taky_central_source_factory as factory

LIMIT = 64
MAX_BYTES = 256_000
MAX_CHARS_PER_UNIT = 12_000
MAX_UNITS = 500
ROOT = factory.WAREHOUSE.resolve()
ACCOUNT = "TAKY_REVIEW_RAW"
EXCLUDED_NAMES = frozenset({
    "readme.md", "readme.txt", "license.md", "license.txt",
    "checksums_sha256.txt", "manifest.txt", "index.txt",
    "robots.txt", "sitemap.txt"
})


def original_document_filename(name):
    if not isinstance(name, str):
        return False
    lowered = name.strip().lower()
    if not lowered or lowered in EXCLUDED_NAMES:
        return False
    if any(x in lowered for x in (".log.", ".test.", "_test.", "checksum", "password", "secret")):
        return False
    return lowered.endswith((".md", ".txt"))


def candidates(c, limit):
    if not 1 <= limit <= LIMIT:
        raise ValueError("BATCH_LIMIT_INVALID")
    rows = c.execute("""SELECT s.id,s.original_sha256,s.status,s.authoritative_review,
            l.locator,l.size_bytes,l.account,l.source_role
        FROM stage t JOIN source s ON s.id=t.source_id
        JOIN location l ON l.source_id=s.id
        WHERE t.stage='EXTRACT' AND t.state='PENDING'
          AND s.status='RAW_VERIFIED' AND s.original_sha256 IS NOT NULL
          AND s.authoritative_review='UNREVIEWED'
          AND l.provider='LOCAL_FILE' AND l.trust='RAW_HASH_VERIFIED'
          AND l.account=? AND (LOWER(l.name) LIKE '%.txt' OR LOWER(l.name) LIKE '%.md')
          AND NOT EXISTS (SELECT 1 FROM evidence_unit existing WHERE existing.source_id=s.id)
          AND l.size_bytes BETWEEN 3500 AND ?
        ORDER BY l.size_bytes,l.locator LIMIT ?""",(ACCOUNT,MAX_BYTES,limit*3)).fetchall()
    selected=[]
    seen=set()
    for row in rows:
        if not original_document_filename(Path(row["locator"]).name):
            continue
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        selected.append(dict(row))
        if len(selected)>=limit:
            break
    return selected


def _units(raw):
    lines = raw.decode("utf-8-sig", errors="strict").splitlines()
    if not lines or len(lines) > 30000:
        raise ValueError("TEXT_LINE_COUNT_UNSUPPORTED")
    units = []
    start = 1
    pos = 0
    while pos < len(lines):
        first = pos
        size = 0
        while pos < len(lines) and pos-first < 30:
            n = len(lines[pos]) + 1
            if n > MAX_CHARS_PER_UNIT:
                raise ValueError("SINGLE_LINE_TOO_LONG")
            if pos > first and size+n > MAX_CHARS_PER_UNIT:
                break
            size += n
            pos += 1
        text = "\n".join(lines[first:pos]).strip()
        if text:
            end = pos
            units.append((f"RAW-L{start:06d}-L{end:06d}",
                          start,end,factory.hashbytes(text.encode("utf-8")),text))
            if len(units)>MAX_UNITS:
                raise ValueError("TOO_MANY_EXTRACTIVE_UNITS")
        start=pos+1
    if not units:
        raise ValueError("NO_EXTRACTABLE_TEXT")
    return units


def process_one(c, row):
    sid, sha = row["id"],row["original_sha256"]
    if sid != "raw:"+sha or row["status"]!="RAW_VERIFIED" or row["authoritative_review"]!="UNREVIEWED":
        raise ValueError("SOURCE_NOT_VERIFIED_OR_UNREVIEWED")
    if row["account"]!=ACCOUNT or row["source_role"]!="RAW_VERIFIED_PENDING_REVIEW":
        raise ValueError("SOURCE_ACCOUNT_ROLE_SCOPE_INVALID")
    p=Path(row["locator"])
    if not original_document_filename(p.name) or p.is_symlink() or p.is_junction():
        raise ValueError("NOT_ORIGINAL_TEXT_LOCATOR")
    resolved=p.resolve(strict=True)
    if not resolved.is_relative_to(ROOT) or not p.is_file():
        raise ValueError("RAW_OUTSIDE_WAREHOUSE")
    before=p.stat()
    if not 3500<=before.st_size<=MAX_BYTES or before.st_size!=row["size_bytes"]:
        raise ValueError("RAW_SIZE_CHANGED")
    data=p.read_bytes()
    if factory.hashbytes(data)!=sha or before.st_mtime_ns!=p.stat().st_mtime_ns:
        raise ValueError("RAW_HASH_CHANGED")
    units=_units(data)
    if c.execute("SELECT COUNT(*) FROM evidence_unit WHERE source_id=?",(sid,)).fetchone()[0]:
        raise ValueError("EXISTING_DETAIL_REQUIRES_SEPARATE_RECONCILIATION")
    for unit_id,start,end,digest,text in units:
        c.execute("""INSERT INTO evidence_unit
            (source_id,unit_id,raw_sha256,line_start,line_end,content_sha256,excerpt,review_state)
            VALUES(?,?,?,?,?,?,?,'EXTRACTIVE_UNREVIEWED')""",
            (sid,unit_id,sha,start,end,digest,text))
    excerpt=" ".join(data.decode("utf-8-sig").split())[:400]
    c.execute("""INSERT INTO evidence(source_id,raw_sha256,parse_state,summary,index_terms,modified_at)
          VALUES(?,?,?,?,?,?)""",(sid,sha,"SOURCE_ANCHORED_TEXT_UNREVIEWED",excerpt,"[]",factory.utc()))
    factory.put_stage(c,sid,"EXTRACT","DONE",{"method":"SHA256_LINE_ANCHOR","units":len(units),"semantic_review":False})
    factory.put_stage(c,sid,"ANALYZE","PENDING_INDEPENDENT_REVIEW",{"automatic_semantics":False})
    factory.put_stage(c,sid,"REVIEW","WAITING_EVIDENCE_REVIEW",{"raw_sha256":sha})
    factory.put_stage(c,sid,"INDEX","TECHNICAL_INDEX_READY",{"unit_count":len(units),"authoritative":False})
    for stage,state in (("FORMING","BLOCKED_REVIEW_NOT_APPROVED"),
                        ("LEARNING","BLOCKED_FORMING_NOT_APPROVED"),
                        ("CONSUME","BLOCKED_NO_APPROVED_CONTRACT")):
        factory.put_stage(c,sid,stage,state,{})
    c.execute("UPDATE source SET status='INDEXED_CANDIDATE',changed_at=? WHERE id=?",
              (factory.utc(),sid))
    factory.event(c,sid,"SOURCE_DETAIL_ANCHORS_INDEXED",{
        "raw_sha256":sha,"unit_count":len(units),"original_raw":True,
        "full_semantic_review":False,"forming_authorized":False})
    # Use original bytes again, not only the derived row, to validate indexes.
    for unit_id,*_ in (units[0],units[-1]):
        verified=factory.read_verified_evidence_unit(c,sid,unit_id)
        if not verified or verified["raw_sha256"]!=sha or verified["review_state"]!="EXTRACTIVE_UNREVIEWED":
            raise ValueError("DETAIL_READBACK_FAILED")
    return {"source_id":sid,"unit_count":len(units),"raw_sha256":sha}


def run(c, limit=16):
    rows=candidates(c,limit)
    results=[]
    for row in rows:
        c.execute("SAVEPOINT bounded_source")
        try:
            result=process_one(c,row)
            c.execute("RELEASE SAVEPOINT bounded_source")
            results.append(result)
        except Exception:
            c.execute("ROLLBACK TO SAVEPOINT bounded_source")
            c.execute("RELEASE SAVEPOINT bounded_source")
            raise
    return {"status":"ORIGINAL_TEXT_EXTRACTIVE_INDEXED_UNREVIEWED",
        "selected":len(rows),"processed":len(results),
        "units_added":sum(x["unit_count"] for x in results),
        "source_ids":[x["source_id"] for x in results],
        "semantic_approval_count":0,"forming_promoted":False,
        "learning_consumed":False,"current_changed":False,
        "model_calls":0,"paid_api_calls":0}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=16)
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--db",type=Path,default=factory.DB)
    args=ap.parse_args()
    if args.apply:
        with factory.connect(args.db) as c:
            out=run(c,args.limit)
    else:
        with sqlite3.connect("file:"+str(args.db).replace("\\","/")+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row
            selected=candidates(c,args.limit)
            out={"status":"PREVIEW_ONLY","selected":len(selected),
                 "raw_source_ids":[x["id"] for x in selected],"writes":0}
    print(json.dumps(out,ensure_ascii=True))


if __name__=="__main__":
    main()
