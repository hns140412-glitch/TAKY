#!/usr/bin/env python3
import json,sys
from pathlib import Path

def fail(msg):
    print("FAIL:",msg); raise SystemExit(1)

def main(path):
    d=json.loads(Path(path).read_text(encoding="utf-8"))
    raws=d.get("raw_html_pages")
    if not isinstance(raws,list) or not raws: fail("raw_html_pages missing")
    chat_ids=[x.get("chat_id") for x in raws]
    drive_ids=[x.get("drive_id") for x in raws]
    if len(chat_ids)!=len(set(chat_ids)): fail("duplicate chat_id")
    if len(drive_ids)!=len(set(drive_ids)): fail("duplicate drive_id")
    cov=d.get("coverage") or {}
    if cov.get("raw_html_observed")!=len(raws): fail("raw_html_observed mismatch")
    gaps=d.get("discovered_gaps") or []
    for g in gaps:
        if g.get("chat_id") not in set(chat_ids): fail("gap references unknown chat")
    if cov.get("full_account_history") is True: fail("census cannot claim full account history")
    if cov.get("inaccessible_or_unrepresented_account_history")!="UNVERIFIED_SOURCE_COVERAGE":
        fail("unrepresented account history boundary missing")
    print(f"PASS census raw_html={len(raws)} gaps={len(gaps)}")

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("usage: account_conversation_census_validator.py <census.json>")
        raise SystemExit(2)
    main(sys.argv[1])
