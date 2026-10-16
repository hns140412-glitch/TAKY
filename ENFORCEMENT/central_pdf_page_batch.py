"""Bounded PDF page-text mining into TAKY's single Central DB.

Original SHA256 + 1-based PDF page and extractive text SHA make a
separate searchable PDF DETAIL. Not OCR, legal authority, FORMING, or LEARNING.
"""
import argparse
import hashlib
import io
import json
import sqlite3
from pathlib import Path

from pypdf import PdfReader
import taky_central_source_factory as factory

ROOT=factory.WAREHOUSE.resolve()
MAX_FILE_BYTES=4_000_000
MAX_PAGES=32
MAX_PAGE_CHARS=20_000
MAX_TOTAL_CHARS=125_000
ACCOUNT="TAKY_WORKBENCH_REFERENCE"
ROLE="REFERENCE_PENDING_REVIEW"
VERIFIABLE_ORIGINAL_ROLES=frozenset((ROLE,"REFERENCE_UNREVIEWED"))

def initialize(c):
    c.execute("""CREATE TABLE IF NOT EXISTS pdf_page_evidence (
      source_id TEXT NOT NULL REFERENCES source(id),
      page_number INTEGER NOT NULL CHECK(page_number >= 1),
      raw_sha256 TEXT NOT NULL,
      text_sha256 TEXT NOT NULL,
      page_text TEXT NOT NULL,
      extraction_tool TEXT NOT NULL,
      review_state TEXT NOT NULL DEFAULT 'EXTRACTIVE_UNREVIEWED',
      PRIMARY KEY(source_id,page_number))""")
    c.execute("CREATE INDEX IF NOT EXISTS pdf_page_text_source ON pdf_page_evidence(source_id,page_number)")

def candidates(c,limit=16,*,min_bytes=4096):
    if not isinstance(limit,int) or not 1<=limit<=32:
        raise ValueError("BATCH_LIMIT_INVALID")
    if not isinstance(min_bytes,int) or not 4096<=min_bytes<=MAX_FILE_BYTES:
        raise ValueError("PDF_MIN_SIZE_BOUND_INVALID")
    rows=c.execute("""SELECT s.id,s.original_sha256,s.status,s.authoritative_review,
             l.locator,l.name,l.size_bytes,l.account,l.source_role
        FROM stage st JOIN source s ON s.id=st.source_id
        JOIN location l ON l.source_id=s.id
        WHERE st.stage='EXTRACT' AND st.state='PENDING'
          AND s.original_sha256 IS NOT NULL AND s.status='RAW_VERIFIED'
          AND s.media_kind='PDF' AND s.authoritative_review='UNREVIEWED'
          AND l.provider='LOCAL_FILE' AND l.trust='RAW_HASH_VERIFIED'
          AND l.account=? AND l.source_role=?
          AND l.size_bytes BETWEEN ? AND ?
          AND LOWER(l.name) LIKE '%.pdf'
        ORDER BY l.size_bytes,l.locator LIMIT ?""",(ACCOUNT,ROLE,min_bytes,MAX_FILE_BYTES,limit*2)).fetchall()
    seen=set();out=[]
    for row in rows:
        if row["id"] not in seen:
            out.append(dict(row));seen.add(row["id"])
        if len(out)>=limit:break
    return out

def _verified_original(row):
    if (row["id"]!="raw:"+row["original_sha256"]
        or row["status"] not in ("RAW_VERIFIED","INDEXED_CANDIDATE")
        or row["authoritative_review"]!="UNREVIEWED"
        or row["account"]!=ACCOUNT
        or row["source_role"] not in VERIFIABLE_ORIGINAL_ROLES):
        raise ValueError("PDF_ORIGIN_SCOPE_INVALID")
    p=Path(row["locator"])
    if p.suffix.lower()!=".pdf" or p.is_symlink() or p.is_junction():
        raise ValueError("PDF_NOT_ORIGINAL_SOURCE")
    actual=p.resolve(strict=True)
    if not actual.is_relative_to(ROOT):
        raise ValueError("PDF_OUTSIDE_CANONICAL_REFERENCE")
    stat=p.stat()
    if not 4096<=stat.st_size<=MAX_FILE_BYTES or stat.st_size!=row["size_bytes"]:
        raise ValueError("PDF_SOURCE_SIZE_CHANGED")
    raw=p.read_bytes()
    if (hashlib.sha256(raw).hexdigest()!=row["original_sha256"]
        or p.stat().st_mtime_ns!=stat.st_mtime_ns):
        raise ValueError("PDF_RAW_HASH_CHANGED")
    return raw

def _page_text(page):
    return "\n".join(x.strip() for x in (page.extract_text() or "").splitlines() if x.strip())


def _extract_pages(raw):
    reader=PdfReader(io.BytesIO(raw),strict=False)
    if reader.is_encrypted:
        return "ENCRYPTED_NEEDS_SPECIALIST",len(reader.pages),[]
    pages=len(reader.pages)
    if not 1<=pages<=MAX_PAGES:
        return "PAGE_LIMIT_SPECIALIST_REQUIRED",pages,[]
    result=[]; total=0
    for n,page in enumerate(reader.pages,1):
        text=_page_text(page)
        if len(text)>MAX_PAGE_CHARS:
            return "PAGE_TEXT_TOO_LARGE",pages,[]
        total+=len(text)
        if total>MAX_TOTAL_CHARS:
            return "TOTAL_TEXT_TOO_LARGE",pages,[]
        if text:
            result.append((n,hashlib.sha256(text.encode("utf-8")).hexdigest(),text))
    if total<60:
        return "OCR_REQUIRED",pages,[]
    return "PDF_TEXT_EXTRACTED_UNREVIEWED",pages,result

def process_one(c,row):
    raw=_verified_original(row)
    status,page_count,pages=_extract_pages(raw)
    sid=row["id"];sha=row["original_sha256"]
    if c.execute("SELECT COUNT(*) FROM pdf_page_evidence WHERE source_id=?",(sid,)).fetchone()[0]:
        raise ValueError("PDF_DETAIL_ALREADY_PRESENT_RECONCILE_REQUIRED")
    if not pages:
        factory.put_stage(c,sid,"EXTRACT",status,{"pages":page_count,"raw_sha256":sha})
        factory.put_stage(c,sid,"REVIEW","WAITING_SPECIALIST_EXTRACTION",{"reason":status})
        factory.put_stage(c,sid,"FORMING","BLOCKED_NO_REVIEWED_CONTENT",{})
        return {"source_id":sid,"status":status,"page_units":0}
    for n,digest,text in pages:
        c.execute("""INSERT INTO pdf_page_evidence
           (source_id,page_number,raw_sha256,text_sha256,page_text,extraction_tool,review_state)
           VALUES(?,?,?,?,?,'pypdf-local-v1','EXTRACTIVE_UNREVIEWED')""",
           (sid,n,sha,digest,text))
    short=" ".join(x[2] for x in pages)[:400]
    c.execute("""INSERT INTO evidence VALUES(?,?,?,?,?,?)""",
         (sid,sha,status,short,"[]",factory.utc()))
    factory.put_stage(c,sid,"EXTRACT","DONE",{"method":"PYDPF_PAGE_TEXT_SOURCE_BOUND","pages":page_count,"units":len(pages)})
    factory.put_stage(c,sid,"ANALYZE","PENDING_INDEPENDENT_REVIEW",{"auto_semantic":False})
    factory.put_stage(c,sid,"REVIEW","WAITING_EVIDENCE_REVIEW",{"raw_sha256":sha})
    factory.put_stage(c,sid,"INDEX","TECHNICAL_PDF_INDEX_READY",{"pages":page_count,"source_sha256":sha})
    for stage,state in (("FORMING","BLOCKED_REVIEW_NOT_APPROVED"),
                        ("LEARNING","BLOCKED_FORMING_NOT_APPROVED"),
                        ("CONSUME","BLOCKED_NO_APPROVED_CONTRACT")):
        factory.put_stage(c,sid,stage,state,{})
    c.execute("UPDATE source SET status='INDEXED_CANDIDATE',changed_at=? WHERE id=?",(factory.utc(),sid))
    factory.event(c,sid,"PDF_TEXT_PAGE_ANCHORS_INDEXED",{
       "raw_sha256":sha,"page_count":page_count,"page_units":len(pages),
       "extraction_tool":"pypdf-local-v1","semantic_approval":False})
    for n,_,_ in (pages[0],pages[-1]):
        if not read_verified_page(c,sid,n):
            raise ValueError("PDF_PAGE_READBACK_FAILED")
    return {"source_id":sid,"status":status,"page_units":len(pages)}

def read_verified_page(c,sid,page_number):
    row=c.execute("""SELECT p.*,l.locator,l.source_role,l.size_bytes,
         s.status,s.original_sha256,s.authoritative_review
       FROM pdf_page_evidence p JOIN source s ON s.id=p.source_id
       JOIN location l ON l.source_id=p.source_id
       WHERE p.source_id=? AND p.page_number=? AND l.provider='LOCAL_FILE'
         AND l.account=? AND l.trust='RAW_HASH_VERIFIED'
         AND l.source_role IN ('REFERENCE_PENDING_REVIEW','REFERENCE_UNREVIEWED')
         AND LOWER(l.name) LIKE '%.pdf'
       ORDER BY CASE WHEN l.source_role='REFERENCE_PENDING_REVIEW' THEN 0 ELSE 1 END
       LIMIT 1""",(sid,page_number,ACCOUNT)).fetchone()
    if not row:return None
    if row["original_sha256"]!=row["raw_sha256"]:
        raise ValueError("PDF_PAGE_SOURCE_SHA_MISMATCH")
    raw=_verified_original({"id":sid,"original_sha256":row["raw_sha256"],
        "status":row["status"],"authoritative_review":row["authoritative_review"],
        "account":ACCOUNT,"source_role":row["source_role"],"locator":row["locator"],
        "size_bytes":row["size_bytes"]})
    reader=PdfReader(io.BytesIO(raw),strict=False)
    if (reader.is_encrypted or not 1<=page_number<=len(reader.pages)
        or len(reader.pages)>MAX_PAGES):
        raise ValueError("PDF_PAGE_SOURCE_SCOPE_CHANGED")
    text=_page_text(reader.pages[page_number-1])
    if (not text or text!=row["page_text"] or
        hashlib.sha256(text.encode("utf-8")).hexdigest()!=row["text_sha256"]):
        raise ValueError("PDF_PAGE_EXTRACTED_TEXT_CHANGED")
    return {"source_id":sid,"page_number":page_number,
       "raw_sha256":row["raw_sha256"],"text_sha256":row["text_sha256"],
       "text":text,"review_state":row["review_state"],
       "forming_authorized":False}

def find_pdf_page_units(c, query, *, limit=25):
    """Bounded source-linked search, not a reviewed semantic answer."""
    if not isinstance(query,str) or not 2<=len(query.strip())<=160:
        raise ValueError("PDF_SEARCH_QUERY_INVALID")
    if not isinstance(limit,int) or not 1<=limit<=100:
        raise ValueError("PDF_SEARCH_LIMIT_INVALID")
    term=query.strip().casefold().replace("\\","\\\\").replace("%","\\%").replace("_","\\_")
    rows=c.execute("""SELECT p.source_id,p.page_number,p.raw_sha256,
         p.text_sha256,p.page_text,p.review_state
       FROM pdf_page_evidence p JOIN source s ON s.id=p.source_id
       WHERE LOWER(p.page_text) LIKE ? ESCAPE '\\'
         AND s.authoritative_review='UNREVIEWED'
       ORDER BY p.source_id,p.page_number LIMIT ?""",("%"+term+"%",limit)).fetchall()
    return [{"source_id":r["source_id"],"page_number":r["page_number"],
             "raw_sha256":r["raw_sha256"],"text_sha256":r["text_sha256"],
             "snippet":r["page_text"][:700],"review_state":r["review_state"],
             "authority":False} for r in rows]


def run(c,limit=16,*,min_bytes=4096):
    initialize(c); rows=candidates(c,limit,min_bytes=min_bytes)
    results=[]
    for row in rows:
        c.execute("SAVEPOINT pdf_source")
        try:
            entry=process_one(c,row)
            c.execute("RELEASE SAVEPOINT pdf_source")
            results.append(entry)
        except Exception:
            c.execute("ROLLBACK TO SAVEPOINT pdf_source")
            c.execute("RELEASE SAVEPOINT pdf_source")
            raise
    return {"status":"PDF_EXTRACTIVE_BATCH_UNREVIEWED",
       "processed":len(results),"indexed_pdf_sources":sum(x["page_units"]>0 for x in results),
       "page_units_added":sum(x["page_units"] for x in results),
       "specialist_hold":sum(x["page_units"]==0 for x in results),
       "states":[x["status"] for x in results],
       "forming_approved":0,"learning_approved":0,"current_changed":False,"paid_api_calls":0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true")
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--min-bytes",type=int,default=4096)
    args=p.parse_args()
    if args.apply:
        with factory.connect() as c:result=run(c,args.limit,min_bytes=args.min_bytes)
    else:
        with sqlite3.connect("file:"+str(factory.DB).replace("\\","/")+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row
            items=candidates(c,args.limit,min_bytes=args.min_bytes)
            result={"status":"PDF_PREVIEW_ONLY","selected":len(items),"writes":0}
    print(json.dumps(result,ensure_ascii=True))

if __name__=="__main__":
    main()
