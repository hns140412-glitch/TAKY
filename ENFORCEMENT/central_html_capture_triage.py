"""Bounded raw-verified HTML capture triage and extractive technical index.

WEB_SOURCE_ARCHIVE_UNVERIFIED is a provenance label, not an approved source.
Hash-verified access denial / CAPTCHA pages are recorded as reacquisition
holds, never mined as article content. No browsing, models or paid APIs.
"""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
import taky_central_source_factory as factory

ROOT=factory.WAREHOUSE.resolve()
ACCOUNT="TAKY_SOURCE_ARCHIVE"
ROLE="WEB_SOURCE_ARCHIVE_UNVERIFIED"
MAX_BYTES=600_000
MAX_VISIBLE=80_000
CHUNK=1200
MAX_CHUNKS=80
BLOCK_MARKERS=(
    "you have been blocked", "unable to access medium.com",
    "please enable cookies", "verify you are human",
    "just a moment...", "checking your browser",
    "응답을 기다리는 중", "잠시만 기다려", "확인에 성공했습니다",
    "captcha", "access denied", "cloudflare ray id"
)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def init(c):
    c.execute("""CREATE TABLE IF NOT EXISTS html_text_evidence(
      source_id TEXT NOT NULL REFERENCES source(id),
      chunk_no INTEGER NOT NULL CHECK(chunk_no>0),
      raw_sha256 TEXT NOT NULL,
      visible_sha256 TEXT NOT NULL,
      text_sha256 TEXT NOT NULL,
      excerpt TEXT NOT NULL,
      review_state TEXT NOT NULL DEFAULT 'EXTRACTIVE_UNREVIEWED',
      PRIMARY KEY(source_id,chunk_no))""")

def candidates(c,limit=40,source_ids=None):
    if not isinstance(limit,int) or not 1<=limit<=64:raise ValueError("HTML_LIMIT_INVALID")
    source_ids=list(source_ids or [])
    if source_ids:
        if len(source_ids)>16 or any(not re.fullmatch(r"raw:[0-9a-f]{64}",sid) for sid in source_ids):
            raise ValueError("HTML_EXPLICIT_SOURCE_IDS_INVALID")
        # User-reviewed Workbench HTML: opt-in per SHA, never widen the global crawl.
        scope="AND l.account=? AND l.source_role=? AND s.id IN ("+(",".join("?" for _ in source_ids))+")"
        scope_args=("TAKY_WORKBENCH_REFERENCE","REFERENCE_PENDING_REVIEW",*source_ids)
    else:
        scope="AND l.account=? AND l.source_role=? AND LOWER(l.name)='source.html'"
        scope_args=(ACCOUNT,ROLE)
    table_ready=c.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='html_text_evidence'"
    ).fetchone() is not None
    exclude_existing=(
        " AND NOT EXISTS(SELECT 1 FROM html_text_evidence h WHERE h.source_id=s.id)"
        if table_ready else ""
    )
    rows=c.execute(f"""SELECT s.id,s.original_sha256,s.status,
       s.authoritative_review,l.account,l.source_role,l.locator,l.name,l.size_bytes
       FROM source s JOIN stage t ON t.source_id=s.id
       JOIN location l ON l.source_id=s.id
       WHERE t.stage='EXTRACT' AND t.state='PENDING'
       AND (s.media_kind='TEXT' OR ?=1) AND s.original_sha256 IS NOT NULL
       AND s.status='RAW_VERIFIED' AND s.authoritative_review='UNREVIEWED'
       AND l.provider='LOCAL_FILE' AND l.trust='RAW_HASH_VERIFIED'
       {scope}
       AND l.size_bytes BETWEEN 2048 AND ?
       {exclude_existing}
       ORDER BY l.size_bytes,l.locator LIMIT ?""",(int(bool(source_ids)),*scope_args,MAX_BYTES,limit*4)).fetchall()
    seen=set();out=[]
    for row in rows:
        if row["id"] in seen:continue
        seen.add(row["id"]);out.append(dict(row))
        if len(out)>=limit:break
    return out

def verified_raw(row):
    if (row["id"]!="raw:"+row["original_sha256"]
        or row["status"] not in ("RAW_VERIFIED","INDEXED_CANDIDATE")
        or row["authoritative_review"]!="UNREVIEWED"):
        raise ValueError("HTML_ORIGIN_SCOPE_INVALID")
    archive=(row["account"]==ACCOUNT and row["source_role"]==ROLE)
    workbench=(row["account"]=="TAKY_WORKBENCH_REFERENCE"
               and row["source_role"]=="REFERENCE_PENDING_REVIEW")
    if not (archive or workbench):
        raise ValueError("HTML_ORIGIN_SCOPE_INVALID")
    p=Path(row["locator"])
    name_ok=(p.name.lower()=="source.html" if archive else (p.suffix.lower()==".html" or not p.suffix))
    if not name_ok or p.is_symlink() or p.is_junction():
        raise ValueError("HTML_LOCATOR_INVALID")
    actual=p.resolve(strict=True)
    if not actual.is_relative_to(ROOT):raise ValueError("HTML_OUTSIDE_WORKBENCH")
    stat=p.stat()
    if not 2048<=stat.st_size<=MAX_BYTES or stat.st_size!=row["size_bytes"]:
        raise ValueError("HTML_FILE_SIZE_CHANGED")
    raw=p.read_bytes()
    if workbench and not p.suffix and not raw[:512].lstrip().lower().startswith((b"<!doctype html",b"<html")):
        raise ValueError("EXTENSIONLESS_SOURCE_NOT_HTML")
    if sha(raw)!=row["original_sha256"] or p.stat().st_mtime_ns!=stat.st_mtime_ns:
        raise ValueError("HTML_RAW_SHA_CHANGED")
    return raw

def extract(raw):
    try:text=raw.decode("utf-8-sig","strict")
    except UnicodeDecodeError:return "HTML_ENCODING_SPECIALIST_REQUIRED",[]
    if "<html" not in text.lower()[:10000] and "<!doctype" not in text.lower()[:500]:
        return "NOT_HTML_CAPTURE",[]
    soup=BeautifulSoup(text,"html.parser")
    for el in soup(["script","style","noscript","svg","iframe","nav","footer","aside","form"]):
        el.decompose()
    content=soup.select_one("article") or soup.select_one("main") or soup.body or soup
    visible=" ".join(content.stripped_strings)
    if any(marker in visible[:3500].lower() for marker in BLOCK_MARKERS):
        return "HTML_ACCESS_BLOCKED_REACQUIRE_RAW",[]
    if len(visible)<300:return "HTML_CONTENT_MISSING_REACQUIRE_RAW",[]
    if len(visible)>MAX_VISIBLE:return "HTML_TEXT_TOO_LARGE_SPECIALIST",[]
    chunks=[visible[i:i+CHUNK] for i in range(0,len(visible),CHUNK)]
    if len(chunks)>MAX_CHUNKS:raise ValueError("HTML_TOO_MANY_CHUNKS")
    return "HTML_VISIBLE_TEXT_UNREVIEWED",chunks

def one(c,row):
    raw=verified_raw(row)
    status,chunks=extract(raw)
    sid=row["id"];original=row["original_sha256"]
    if not chunks:
        factory.put_stage(c,sid,"EXTRACT",status,{"raw_sha256":original,
            "html_capture_not_claimed_as_article":True})
        factory.put_stage(c,sid,"REVIEW","WAITING_SOURCE_REACQUISITION",{"reason":status})
        factory.put_stage(c,sid,"FORMING","BLOCKED_NO_VERIFIED_CONTENT",{})
        factory.event(c,sid,"HTML_SOURCE_REACQUISITION_HOLD",
            {"raw_sha256":original,"reason":status,"semantic_approved":False})
        return {"source_id":sid,"state":status,"chunks":0}
    if c.execute("SELECT COUNT(*) FROM html_text_evidence WHERE source_id=?",(sid,)).fetchone()[0]:
        raise ValueError("HTML_DETAIL_ALREADY_EXISTS")
    full="".join(chunks)
    full_hash=sha(full.encode("utf-8"))
    for no,part in enumerate(chunks,1):
        c.execute("""INSERT INTO html_text_evidence
             (source_id,chunk_no,raw_sha256,visible_sha256,text_sha256,excerpt,review_state)
             VALUES(?,?,?,?,?,?,'EXTRACTIVE_UNREVIEWED')""",
             (sid,no,original,full_hash,sha(part.encode("utf-8")),part))
    factory.put_stage(c,sid,"EXTRACT","DONE",{
        "method":"HTML_VISIBLE_EXTRACTIVE_SHA256_V1",
        "original_raw_sha256":original,"chunks":len(chunks),
        "source_is_unreviewed":True})
    factory.put_stage(c,sid,"ANALYZE","PENDING_INDEPENDENT_REVIEW",{})
    factory.put_stage(c,sid,"REVIEW","WAITING_EVIDENCE_REVIEW",{})
    factory.put_stage(c,sid,"INDEX","TECHNICAL_HTML_INDEX_READY",{"chunks":len(chunks)})
    for stage,state in (("FORMING","BLOCKED_REVIEW_NOT_APPROVED"),
                        ("LEARNING","BLOCKED_FORMING_NOT_APPROVED"),
                        ("CONSUME","BLOCKED_NO_APPROVED_CONTRACT")):
        factory.put_stage(c,sid,stage,state,{})
    c.execute("UPDATE source SET status='INDEXED_CANDIDATE',changed_at=? WHERE id=?",
              (factory.utc(),sid))
    factory.event(c,sid,"HTML_VISIBLE_TEXT_ANCHORS_INDEXED",{
        "raw_sha256":original,"chunks":len(chunks),"semantic_approved":False})
    for n in (1,len(chunks)):
        if read_verified(c,sid,n) is None:raise ValueError("HTML_ANCHOR_READBACK_FAILED")
    return {"source_id":sid,"state":status,"chunks":len(chunks)}

def read_verified(c,sid,no):
    row=c.execute("""SELECT h.*,s.status,s.original_sha256,s.authoritative_review,
        l.account,l.source_role,l.locator,l.name,l.size_bytes
        FROM html_text_evidence h JOIN source s ON h.source_id=s.id
        JOIN location l ON h.source_id=l.source_id
        WHERE h.source_id=? AND h.chunk_no=? AND l.provider='LOCAL_FILE'
          AND l.trust='RAW_HASH_VERIFIED'
          AND ((l.account=? AND l.source_role=? AND LOWER(l.name)='source.html')
            OR (l.account='TAKY_WORKBENCH_REFERENCE'
                AND l.source_role='REFERENCE_PENDING_REVIEW'))
          ORDER BY CASE WHEN l.account=? THEN 0 ELSE 1 END LIMIT 1""",
          (sid,no,ACCOUNT,ROLE,ACCOUNT)).fetchone()
    if row is None:return None
    if row["original_sha256"]!=row["raw_sha256"]:
        raise ValueError("HTML_SOURCE_SHA_CONFLICT")
    raw=verified_raw({"id":sid,"original_sha256":row["raw_sha256"],
        "status":row["status"],"authoritative_review":row["authoritative_review"],
        "account":row["account"],"source_role":row["source_role"],
        "locator":row["locator"],"size_bytes":row["size_bytes"]})
    state,chunks=extract(raw)
    if state!="HTML_VISIBLE_TEXT_UNREVIEWED" or not 1<=no<=len(chunks):
        raise ValueError("HTML_SOURCE_NO_LONGER_EXTRACTABLE")
    part=chunks[no-1]
    if (part!=row["excerpt"] or sha(part.encode("utf-8"))!=row["text_sha256"]
        or sha("".join(chunks).encode("utf-8"))!=row["visible_sha256"]):
        raise ValueError("HTML_ANCHOR_BYTES_OR_PROJECTION_CHANGED")
    return {"source_id":sid,"chunk_no":no,"raw_sha256":row["raw_sha256"],
       "content_sha256":row["text_sha256"],"visible_sha256":row["visible_sha256"],
       "text":part,"review_state":row["review_state"],"forming_authorized":False}

def run(c,limit=40,source_ids=None):
    init(c);selected=candidates(c,limit,source_ids)
    result=[]
    for row in selected:
        c.execute("SAVEPOINT html_source")
        try:
            info=one(c,row)
            c.execute("RELEASE SAVEPOINT html_source")
            result.append(info)
        except Exception:
            c.execute("ROLLBACK TO SAVEPOINT html_source")
            c.execute("RELEASE SAVEPOINT html_source")
            raise
    states={}
    for item in result:states[item["state"]]=states.get(item["state"],0)+1
    return {"status":"HTML_RAW_SHA_VERIFIED_TRIAGE",
        "processed_sources":len(result),
        "technical_html_indexed":states.get("HTML_VISIBLE_TEXT_UNREVIEWED",0),
        "new_text_segments":sum(x["chunks"] for x in result),
        "reacquisition_or_specialist_holds":sum(x["chunks"]==0 for x in result),
        "states":states,"approved_semantics":0,"current_changed":False,
        "paid_api_calls":0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--apply",action="store_true")
    ap.add_argument("--limit",type=int,default=40)
    ap.add_argument("--source-id",action="append",dest="source_ids",default=[])
    a=ap.parse_args()
    if a.apply:
        with factory.connect() as c:out=run(c,a.limit,a.source_ids)
    else:
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=10) as c:
            c.row_factory=sqlite3.Row
            out={"status":"HTML_PREVIEW","eligible":len(candidates(c,a.limit,a.source_ids)),
                 "writes":0}
    print(json.dumps(out,ensure_ascii=True))

if __name__=="__main__":main()
