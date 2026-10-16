"""Lossless anchored extractive review projection, independent of CURRENT and approval.

Read full Central DETAIL and original SHA-bound RAW. Creates an immutable
offline review packet covering every verified line unit and PDF page; never
interprets legal effect, elevates semantic status, edits DB, or calls models.
"""
import argparse
import collections
import hashlib
import io
import json
import re
import sqlite3
from pathlib import Path

import central_forming_review_queue as base
import central_pdf_page_batch as pdf
import central_html_capture_triage as html_capture
import taky_central_source_factory as factory

SCHEMA = "TAKY_CENTRAL_FULL_ANCHOR_REVIEW_PROJECTION_V1"
DEST = base.EVIDENCE
MAX_UNITS_PER_SOURCE = 500
MAX_SOURCE_COUNT = 1000
ARTICLE = re.compile(r"제\s*\d{1,4}\s*조(?:의\s*\d{1,3})?")
DATE = re.compile(r"(?:시행|개정)\s*[\\[(: ]*\s*\d{4}\s*[.\-/]\s*\d{1,2}\s*[.\-/]\s*\d{1,2}")
HOLD = "INDEPENDENT_OWNER_REVIEW_NOT_COMPLETED"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def signals(text, kind, identifier, content_sha):
    results=[]
    for regex, label in ((ARTICLE,"ARTICLE_TEXT_ONLY"),(DATE,"DATE_TEXT_ONLY")):
        for match in regex.finditer(text):
            results.append({"kind":label, "verbatim":match.group(0),
                            "anchor_kind":kind, "anchor_id":identifier,
                            "content_sha256":content_sha,
                            "offset":match.start(),
                            "legal_validity_verified":False})
            if len(results)>=40:
                return results
    return results


def all_text(c, packet):
    sid=packet["source_id"]
    records=c.execute("""SELECT unit_id FROM evidence_unit
        WHERE source_id=? ORDER BY line_start,unit_id""",(sid,)).fetchall()
    if not records or len(records)>MAX_UNITS_PER_SOURCE:
        raise ValueError("TEXT_FULL_DETAIL_BUDGET_OR_ABSENCE")
    anchors=[]
    for rec in records:
        a=factory.read_verified_evidence_unit(c,sid,rec["unit_id"])
        if (not a or a["source_authority"]!="UNREVIEWED"
            or a["review_state"]!="EXTRACTIVE_UNREVIEWED"
            or a["raw_sha256"]!=packet["raw_sha256"]):
            raise ValueError("TEXT_FULL_SOURCE_REVALIDATION_FAILED")
        body=a["content"]
        anchors.append({"kind":"TEXT_LINE","id":rec["unit_id"],
          "from_line":a["line_start"],"to_line":a["line_end"],
          "content_sha256":a["content_sha256"],
          "excerpt":body[:520],"characters":len(body),
          "lexical_signals":signals(body,"TEXT_LINE",rec["unit_id"],a["content_sha256"])})
    return anchors


def all_pdf(c, packet):
    sid=packet["source_id"]
    original=c.execute("""SELECT l.locator,l.name,l.size_bytes,l.account,l.source_role
        FROM location l WHERE l.source_id=? AND l.provider='LOCAL_FILE'
        AND l.trust='RAW_HASH_VERIFIED' AND l.account=?
        AND l.source_role IN ('REFERENCE_PENDING_REVIEW','REFERENCE_UNREVIEWED')
        AND LOWER(l.name) LIKE '%.pdf'
        ORDER BY CASE WHEN l.source_role='REFERENCE_PENDING_REVIEW' THEN 0 ELSE 1 END,
                 l.locator LIMIT 1""",(sid,pdf.ACCOUNT)).fetchone()
    if not original:
        raise ValueError("PDF_VERIFIED_ORIGINAL_NOT_FOUND")
    raw=pdf._verified_original({
       "id":sid,"original_sha256":packet["raw_sha256"],
       "status":"RAW_VERIFIED","authoritative_review":"UNREVIEWED",
       "account":original["account"],"source_role":original["source_role"],
       "locator":original["locator"],"size_bytes":original["size_bytes"]})
    status,total,full=pdf._extract_pages(raw)
    if status!="PDF_TEXT_EXTRACTED_UNREVIEWED":
        raise ValueError("PDF_FULL_EXTRACTION_UNSUPPORTED:"+status)
    stored=c.execute("""SELECT page_number,raw_sha256,text_sha256,page_text,review_state
       FROM pdf_page_evidence WHERE source_id=? ORDER BY page_number""",(sid,)).fetchall()
    if not stored or len(stored)>MAX_UNITS_PER_SOURCE or len(full)!=len(stored):
        raise ValueError("PDF_PAGE_COVERAGE_OR_BUDGET_MISMATCH")
    anchors=[]
    for (number,digest,body),row in zip(full,stored):
        if (number!=row["page_number"] or digest!=row["text_sha256"]
            or body!=row["page_text"] or row["raw_sha256"]!=packet["raw_sha256"]
            or row["review_state"]!="EXTRACTIVE_UNREVIEWED"):
            raise ValueError("PDF_FULL_PAGE_SOURCE_REVALIDATION_FAILED")
        anchors.append({"kind":"PDF_PAGE","id":str(number),"page":number,
          "content_sha256":digest,"excerpt":body[:520],
          "characters":len(body),"lexical_signals":signals(body,"PDF_PAGE",str(number),digest)})
    return anchors


def all_html(c, packet):
    sid=packet["source_id"]
    rows=c.execute("""SELECT chunk_no FROM html_text_evidence
        WHERE source_id=? ORDER BY chunk_no""",(sid,)).fetchall()
    if not rows or len(rows)>MAX_UNITS_PER_SOURCE:
        raise ValueError("HTML_FULL_DETAIL_BUDGET_OR_ABSENCE")
    result=[]
    for row in rows:
        checked=html_capture.read_verified(c,sid,row["chunk_no"])
        if (not checked or checked["raw_sha256"]!=packet["raw_sha256"]
            or checked["review_state"]!="EXTRACTIVE_UNREVIEWED"):
            raise ValueError("HTML_FULL_SOURCE_REVALIDATION_FAILED")
        body=checked["text"];num=row["chunk_no"]
        result.append({"kind":"HTML_SEGMENT","id":str(num),"segment_no":num,
           "content_sha256":checked["content_sha256"],"excerpt":body[:520],
           "characters":len(body),
           "lexical_signals":signals(body,"HTML_SEGMENT",str(num),
                                     checked["content_sha256"])})
    return result


def project(c, queue):
    # Freshly regenerate the authoritative read-only technical source inventory.
    base.verify_queue(c,queue)
    if len(queue["review_packets"])>MAX_SOURCE_COUNT:
        raise ValueError("SOURCE_COUNT_BUDGET_EXCEEDED")
    projections=[]
    repeats=collections.Counter()
    for p in queue["review_packets"]:
        if p["technical_index_state"]=="TECHNICAL_PDF_INDEX_READY":
            evidence=all_pdf(c,p)
        elif p["technical_index_state"]=="TECHNICAL_HTML_INDEX_READY":
            evidence=all_html(c,p)
        else:
            evidence=all_text(c,p)
        if not evidence:
            raise ValueError("UNVERIFIED_EMPTY_REVIEW_PACKET")
        for anchor in evidence:
            repeats[anchor["content_sha256"]]+=1
        projections.append({
            "source_id":p["source_id"],"raw_sha256":p["raw_sha256"],
            "domain_hint":p["domain_hint"],
            "owner_route_hint":p["owner_review_route_hint"],
            "media_kind":p["media_kind"],
            "full_anchor_count":len(evidence),
            "anchor_coverage":"ALL_AVAILABLE_SOURCE_HASH_VERIFIED_DETAIL",
            "anchors":evidence,
            "review_state":HOLD,"approved_claims":[],
            "legal_effect_verified":False,
            "forming_approved":False,"consumer_enabled":False})
    result={"schema":SCHEMA,
        "status":"FULL_EXTRACTIVE_DETAIL_READY_FOR_OWNER_REVIEW",
        "queue_manifest_sha256":queue["manifest_sha256"],
        "source_count":queue["source_count"],
        "review_ready_sources":len(projections),
        "existing_holds":queue["holds"],
        "verified_anchor_count":sum(p["full_anchor_count"] for p in projections),
        "verbatim_reference_mentions":sum(len(a["lexical_signals"])
                                           for p in projections for a in p["anchors"]),
        "duplicate_anchor_hash_occurrences":sum(v-1 for v in repeats.values() if v>1),
        "domain_counts":dict(collections.Counter(p["domain_hint"] for p in projections)),
        "projected_sources":projections,
        "independent_owner_reviewed_count":0,
        "approved_claim_count":0,
        "forming_approved":False,"learning_consumed":False,
        "current_untouched":True,"central_db_readonly":True,
        "no_paid_api":True}
    result["manifest_sha256"]=base.digest(result)
    return result


def save_immutable(result, root=DEST):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    file=root/("TAKY_FULL_ANCHOR_REVIEW_"+result["manifest_sha256"][:20]+".json")
    if file.exists():
        if json.loads(file.read_text(encoding="utf-8"))!=result:
            raise ValueError("IMMUTABLE_FULL_ANCHOR_CONFLICT")
        return file,False
    with file.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    return file,True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--export",action="store_true")
    parser.add_argument("--queue",type=Path,default=DEST/
      "TAKY_FORMING_REVIEW_QUEUE_4a7c2de00d2e9fc12821.json")
    args=parser.parse_args()
    with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=10) as c:
        c.row_factory=sqlite3.Row
        queue=json.loads(args.queue.read_text(encoding="utf-8"))
        result=project(c,queue)
    summary={k:v for k,v in result.items() if k not in ("projected_sources","existing_holds")}
    if args.export:
        file,created=save_immutable(result)
        summary["path"]=str(file)
        summary["created"]=created
    print(json.dumps(summary,ensure_ascii=False))


if __name__=="__main__":
    main()
