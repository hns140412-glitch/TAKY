#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any

REQUIRED_ITEM_FIELDS=(
    "source_id","title","url","source_family","source_type","authority_level",
    "source_review_state","current_relation","version_relation","source_ref",
    "source_actor","source_actor_class","source_author_identity_state",
    "source_direction","source_direction_signals","applicability_scope","authority_ceiling",
)

def _read(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def _sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def _norm_url(value:object)->str:
    s=str(value or "").strip()
    if not s:return ""
    return s.rstrip("/").lower()

def _version_num(path:Path)->int:
    m=re.search(r"_V(\d+)",path.name,re.I)
    return int(m.group(1)) if m else -1

def _existing_records(root:Path,target_delta:Path)->list[dict[str,Any]]:
    out=[]
    c2s=root/"C2S"
    for p in sorted(c2s.glob("NOTION_REFERENCE_INDEX_DELTA_V*.json"),key=_version_num):
        if p.resolve()==target_delta.resolve():continue
        try:d=_read(p)
        except Exception:continue
        for item in d.get("items") or []:
            if isinstance(item,dict):
                out.append({"origin":p.relative_to(root).as_posix(),**item})
    ledger=root/"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json"
    if ledger.exists():
        try:d=_read(ledger)
        except Exception:d={}
        for e in d.get("entries") or []:
            if not isinstance(e,dict):continue
            det=e.get("details") or {}
            sid=str(det.get("source_id") or e.get("source_key") or "").strip()
            url=str(det.get("source_url") or "").strip()
            if sid or url:
                out.append({"origin":"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json","source_id":sid,"url":url})
    ai=root/"CURRENT/DATA/AI_REFERENCE_INDEX.json"
    if ai.exists():
        try:d=_read(ai)
        except Exception:d={}
        candidates=d.get("items") or d.get("source_entries") or d.get("records") or []
        for x in candidates:
            if isinstance(x,dict):
                out.append({"origin":"CURRENT/DATA/AI_REFERENCE_INDEX.json",**x})
    return out

def verify_delta(root:Path,delta_path:Path)->dict[str,Any]:
    delta=_read(delta_path)
    errors=[]
    parent_name=str(delta.get("parent") or "").strip()
    parent_path=root/"C2S"/parent_name if parent_name else None
    if not parent_path or not parent_path.is_file():
        errors.append("PARENT_DELTA_MISSING")
    elif _sha(parent_path)!=str(delta.get("parent_sha256") or "").lower():
        errors.append("PARENT_SHA256_MISMATCH")
    mining_rel=str(delta.get("input_mining_receipt") or "").strip()
    mining_path=(root.parent/mining_rel) if mining_rel.startswith("TAKY-SOURCE-VAULT/") else (root/mining_rel)
    if not mining_path.is_file():
        errors.append("MINING_RECEIPT_MISSING")
    elif _sha(mining_path)!=str(delta.get("input_mining_sha256") or "").lower():
        errors.append("MINING_SHA256_MISMATCH")

    items=delta.get("items") or []
    if not items:errors.append("NO_INDEX_ITEMS")
    prior=_existing_records(root,delta_path)
    prior_ids={}
    prior_urls={}
    for x in prior:
        sid=str(x.get("source_id") or "").strip()
        if sid:prior_ids.setdefault(sid,[]).append(x.get("origin"))
        for k in ("url","secondary_url","origin_locator"):
            u=_norm_url(x.get(k))
            if u:prior_urls.setdefault(u,[]).append((sid,x.get("origin"),k))
    seen_ids=set();seen_urls=set();reviews=[]
    for item in items:
        missing=[k for k in REQUIRED_ITEM_FIELDS if not item.get(k)]
        sid=str(item.get("source_id") or "").strip()
        url=_norm_url(item.get("url"))
        item_errors=[]
        if missing:item_errors.append("REQUIRED_FIELDS_MISSING:"+",".join(missing))
        if sid in seen_ids:item_errors.append("DUPLICATE_SOURCE_ID_WITHIN_DELTA")
        if url and url in seen_urls:item_errors.append("DUPLICATE_URL_WITHIN_DELTA")
        if sid in prior_ids:item_errors.append("SOURCE_ID_ALREADY_INDEXED")
        exact=prior_urls.get(url,[]) if url else []
        if exact:item_errors.append("EXACT_PRIMARY_URL_ALREADY_INDEXED")
        seen_ids.add(sid);seen_urls.add(url)
        reviews.append({
            "source_id":sid,
            "source_ref":str(item.get("source_ref") or "").strip(),
            "url":item.get("url"),
            "required_fields_pass":not missing,
            "duplicate_source_id_origins":prior_ids.get(sid,[]),
            "exact_url_matches":[{"source_id":a,"origin":b,"field":c} for a,b,c in exact],
            "decision":"INDEXED" if not item_errors else "HOLD",
            "errors":item_errors,
        })
    if any(r["errors"] for r in reviews):errors.append("ITEM_REVIEW_HOLD")
    index_version=re.search(r"_V(\d+)",delta_path.name,re.I)
    index_version=f"V{index_version.group(1)}-NOTION-DELTA" if index_version else "UNKNOWN"
    return {
        "schema":"TAKY_DETERMINISTIC_INDEXING_OWNER_REVIEW_V1",
        "issuer":"INDEXING_OWNER",
        "reviewed":not errors,
        "decision":"INDEXED" if not errors else "HOLD",
        "index_version":index_version,
        "delta_path":delta_path.relative_to(root).as_posix(),
        "delta_sha256":_sha(delta_path),
        "parent":parent_name or None,
        "parent_sha256_verified":"PARENT_SHA256_MISMATCH" not in errors and "PARENT_DELTA_MISSING" not in errors,
        "mining_receipt":mining_rel or None,
        "mining_sha256_verified":"MINING_SHA256_MISMATCH" not in errors and "MINING_RECEIPT_MISSING" not in errors,
        "items":reviews,
        "errors":errors,
        "guards":{
            "request_side_approval_ignored":True,
            "prior_delta_and_ledger_duplicate_check":True,
            "canonical_promotion":False,
            "learning_use_authorized":False,
        }
    }

def owner_binding(review:dict,source_id:str,proposal:dict)->dict|None:
    if review.get("issuer")!="INDEXING_OWNER" or review.get("decision")!="INDEXED" or review.get("reviewed") is not True:
        return None
    row=next((x for x in review.get("items") or [] if x.get("source_id")==source_id and x.get("decision")=="INDEXED"),None)
    if not row:return None
    if str(proposal.get("source_ref") or "")!=str(row.get("source_ref") or ""):return None
    if str(proposal.get("index_version") or "")!=str(review.get("index_version") or ""):return None
    return {
        "issuer":"INDEXING_OWNER","reviewed":True,"decision":"INDEXED",
        "source_id":source_id,"source_ref":row["source_ref"],"index_version":review["index_version"],
        "duplicate_relation":"NONE","version_relation":"NEW_SOURCE_OR_REFERENCE",
        "review_evidence_refs":[review["delta_path"],review["mining_receipt"],"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json"],
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--delta",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    r=verify_delta(a.root,a.delta)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 0 if r.get("decision")=="INDEXED" else 2

if __name__=="__main__":raise SystemExit(main())
