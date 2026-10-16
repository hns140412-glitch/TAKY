"""Collapse failed HTML captures into a bounded source-URL reacquisition queue.

URLs from sibling meta.json are untrusted locators, not content or authority.
No browser retry, no access-control bypass, no API, no CURRENT mutation.
"""
import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import central_forming_review_queue as review
import central_html_capture_triage as html
import taky_central_source_factory as factory

SCHEMA="TAKY_SOURCE_URL_REACQUISITION_CANDIDATES_V1"
STATES=("HTML_ACCESS_BLOCKED_REACQUIRE_RAW","HTML_CONTENT_MISSING_REACQUIRE_RAW")


def build(c):
    rows=c.execute("""SELECT DISTINCT s.id AS source_id,s.original_sha256,
        s.authoritative_review,t.state,l.locator,l.size_bytes,l.account,l.source_role
        FROM stage t JOIN source s ON t.source_id=s.id
        JOIN location l ON l.source_id=s.id
        WHERE t.stage='EXTRACT'
          AND t.state IN ('HTML_ACCESS_BLOCKED_REACQUIRE_RAW',
                          'HTML_CONTENT_MISSING_REACQUIRE_RAW')
          AND s.authoritative_review='UNREVIEWED'
          AND l.provider='LOCAL_FILE' AND l.trust='RAW_HASH_VERIFIED'
          AND l.account=? AND l.source_role=? AND LOWER(l.name)='source.html'
        ORDER BY s.id,l.locator""",(html.ACCOUNT,html.ROLE)).fetchall()
    unique_sources={}
    for r in rows:
        sid=r["source_id"]
        if sid in unique_sources:continue
        raw=html.verified_raw({"id":sid,"original_sha256":r["original_sha256"],
            "status":"RAW_VERIFIED",
            "authoritative_review":r["authoritative_review"],
            "account":r["account"],"source_role":r["source_role"],
            "locator":r["locator"],"size_bytes":r["size_bytes"]})
        state,_=html.extract(raw)
        if state!=r["state"]:
            raise ValueError("REQUERY_CAPTURE_STATE_CHANGED")
        meta=Path(r["locator"]).parent/"meta.json"
        url=None
        if meta.is_file() and not meta.is_symlink() and meta.stat().st_size<=160000:
            item=json.loads(meta.read_text(encoding="utf-8-sig"))
            if isinstance(item,dict):
                url=item.get("normalized_url") or item.get("input_url")
        if not isinstance(url,str) or not 1<=len(url)<=2048:
            url=None
        if url:
            u=urlsplit(url)
            if (u.scheme!="https" or not u.hostname or u.username or u.password
                or u.hostname in ("localhost","127.0.0.1","::1")):
                url=None
        unique_sources[sid]={
            "source_id":sid,"raw_sha256":r["original_sha256"],
            "stage_reason":r["state"],"advisory_url":url,
            "original_raw_locator":r["locator"],"url_verified_available":False,
            "notion_metadata_is_content_proof":False}
    grouped={}
    unresolved=[]
    for item in unique_sources.values():
        url=item["advisory_url"]
        if not url:
            unresolved.append(item)
            continue
        entry=grouped.setdefault(url,{
            "url":url,"host":urlsplit(url).hostname,
            "captured_source_ids":[],"block_reasons":[],
            "reacquisition_state":"REQUERY_REQUIRED_NOT_EXECUTED",
            "independent_content_verified":False,
            "source_url_from_unverified_capture_metadata":True})
        entry["captured_source_ids"].append(item["source_id"])
        if item["stage_reason"] not in entry["block_reasons"]:
            entry["block_reasons"].append(item["stage_reason"])
    out={
        "schema":SCHEMA,"status":"REQUERY_INPUTS_DEDUPLICATED_NOT_FETCHED",
        "blocked_or_missing_source_count":len(unique_sources),
        "unique_https_url_count":len(grouped),
        "source_url_unresolved_count":len(unresolved),
        "host_counts":dict(Counter(x["host"] for x in grouped.values())),
        "requery_candidates":sorted(grouped.values(),key=lambda x:x["url"]),
        "unresolved_sources":unresolved,
        "provider_access_bypass_attempts":0,"web_requests_made":0,
        "raw_source_files_changed":False,"central_db_read_only":True,
        "knowledge_approvals":0,"learning_consumed":False}
    out["manifest_sha256"]=review.digest(out)
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--export",action="store_true")
    args=ap.parse_args()
    with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=10) as c:
        c.row_factory=sqlite3.Row
        result=build(c)
    preview={k:v for k,v in result.items() if k not in ("requery_candidates","unresolved_sources")}
    if args.export:
        target=review.EVIDENCE/("TAKY_HTML_REQUERY_INPUTS_"+result["manifest_sha256"][:20]+".json")
        if target.exists():
            if json.loads(target.read_text(encoding="utf-8"))!=result:
                raise ValueError("REQUERY_IMMUTABLE_COLLISION")
            created=False
        else:
            with target.open("x",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,indent=2)
            created=True
        preview.update({"path":str(target),"new":created})
    print(json.dumps(preview,ensure_ascii=True))


if __name__=="__main__":main()
