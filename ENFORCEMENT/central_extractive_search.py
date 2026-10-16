"""Single read-only RAW-backed search across text lines and PDF pages.

A search hit is an extractive locator, NOT a reviewed knowledge claim.
Reads canonical Central SQLite in mode=ro; rechecks original source bytes on
every returned hit; never writes, invokes an API, or changes CURRENT.
"""
import argparse
import json
import sqlite3
from pathlib import Path

import central_pdf_page_batch as pdf
import central_html_capture_triage as html_capture
import taky_central_source_factory as factory


def search(c, query, *, limit=10):
    if not isinstance(query,str) or not 2<=len(query.strip())<=160:
        raise ValueError("CENTRAL_SEARCH_QUERY_INVALID")
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=20:
        raise ValueError("CENTRAL_SEARCH_LIMIT_INVALID")
    text_hits=factory.find_evidence_units(c,query,limit=limit)
    page_hits=pdf.find_pdf_page_units(c,query,limit=limit)
    valid_text=[]
    for h in text_hits:
        original=factory.read_verified_evidence_unit(c,h["source_id"],h["unit_id"])
        if (original is None or original["source_authority"]!="UNREVIEWED"
            or original["review_state"]!="EXTRACTIVE_UNREVIEWED"
            or original["raw_sha256"]!=h["raw_sha256"]):
            raise ValueError("TEXT_DETAIL_SOURCE_NOT_VERIFIED")
        valid_text.append({
            "media":"TEXT", "source_id":h["source_id"],
            "anchor":{"line_start":original["line_start"],
                      "line_end":original["line_end"],"unit_id":h["unit_id"]},
            "raw_sha256":original["raw_sha256"],
            "content_sha256":original["content_sha256"],
            "excerpt":original["content"][:320],
            "review_state":"EXTRACTIVE_UNREVIEWED", "semantic_authority":False})
    valid_pdf=[]
    for h in page_hits:
        original=pdf.read_verified_page(c,h["source_id"],h["page_number"])
        if (original is None or original["review_state"]!="EXTRACTIVE_UNREVIEWED"
            or original["raw_sha256"]!=h["raw_sha256"]
            or original["text_sha256"]!=h["text_sha256"]):
            raise ValueError("PDF_DETAIL_SOURCE_NOT_VERIFIED")
        valid_pdf.append({
            "media":"PDF", "source_id":h["source_id"],
            "anchor":{"page_number":original["page_number"]},
            "raw_sha256":original["raw_sha256"],
            "content_sha256":original["text_sha256"],
            "excerpt":original["text"][:320],
            "review_state":"EXTRACTIVE_UNREVIEWED", "semantic_authority":False})
    available=c.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='html_text_evidence'"
    ).fetchone() is not None
    valid_html=[]
    if available:
        term=query.strip().casefold().replace("\\","\\\\").replace("%","\\%").replace("_","\\_")
        rows=c.execute("""SELECT h.source_id,h.chunk_no,h.raw_sha256,h.text_sha256
             FROM html_text_evidence h JOIN source s ON s.id=h.source_id
             WHERE s.authoritative_review='UNREVIEWED'
             AND LOWER(h.excerpt) LIKE ? ESCAPE '\\'
             ORDER BY h.source_id,h.chunk_no LIMIT ?""",("%"+term+"%",limit)).fetchall()
        for row in rows:
            a=html_capture.read_verified(c,row["source_id"],row["chunk_no"])
            if (a is None or a["raw_sha256"]!=row["raw_sha256"]
                or a["content_sha256"]!=row["text_sha256"]
                or a["review_state"]!="EXTRACTIVE_UNREVIEWED"):
                raise ValueError("HTML_DETAIL_SOURCE_NOT_VERIFIED")
            valid_html.append({
                "media":"HTML","source_id":row["source_id"],
                "anchor":{"segment_no":a["chunk_no"]},
                "raw_sha256":a["raw_sha256"],
                "content_sha256":a["content_sha256"],
                "excerpt":a["text"][:320],
                "review_state":"EXTRACTIVE_UNREVIEWED","semantic_authority":False})
    # Alternate media categories instead of allowing one type to starve another.
    merged=[]
    for i in range(max(len(valid_text),len(valid_pdf),len(valid_html))):
        for batch in (valid_text,valid_pdf,valid_html):
            if i<len(batch):
                merged.append(batch[i])
                if len(merged)==limit:break
        if len(merged)==limit:break
    return {"schema":"TAKY_CENTRAL_EXTRACTIVE_SEARCH_V1",
        "status":"SOURCE_HASH_VERIFIED_UNREVIEWED_RESULTS",
        "query":query,"hits":merged,"returned_count":len(merged),
        "text_count":sum(x["media"]=="TEXT" for x in merged),
        "pdf_count":sum(x["media"]=="PDF" for x in merged),
        "html_count":sum(x["media"]=="HTML" for x in merged),
        "semantic_approval":False,"knowledge_promotion":False,
        "database_read_only":True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("--limit",type=int,default=10)
    args=p.parse_args()
    db=factory.DB.as_uri()+"?mode=ro"
    with sqlite3.connect(db,uri=True,timeout=8) as c:
        c.row_factory=sqlite3.Row
        result=search(c,args.query,limit=args.limit)
    print(json.dumps(result,ensure_ascii=True))


if __name__=="__main__":
    main()
