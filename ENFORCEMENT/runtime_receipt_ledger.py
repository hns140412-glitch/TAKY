#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_RUNTIME_RECEIPT_LEDGER_V1"

def _hash(x)->str:
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def append(ledger:dict,receipt:dict)->dict:
    if ledger.get("schema")!=SCHEMA:return {"pass":False,"error":"LEDGER_SCHEMA_INVALID"}
    entries=list(ledger.get("entries") or [])
    if receipt.get("pass") is not True:return {"pass":False,"error":"RECEIPT_INVALID"}
    rsha=receipt.get("log_sha256") or receipt.get("receipt_sha256") or receipt.get("handoff_sha256")
    if not isinstance(rsha,str) or len(rsha)!=64:return {"pass":False,"error":"RECEIPT_SHA_INVALID"}
    if any(e.get("receipt_sha256")==rsha for e in entries):
        return {"pass":False,"error":"DUPLICATE_RECEIPT"}
    prev=entries[-1]["entry_sha256"] if entries else None
    body={
      "sequence":len(entries)+1,
      "receipt_sha256":rsha,
      "receipt_schema":receipt.get("schema"),
      "app_id":receipt.get("app_id") or receipt.get("target_app"),
      "scene_id":receipt.get("scene_id"),
      "previous_entry_sha256":prev
    }
    entry={**body,"entry_sha256":_hash(body)}
    return {"pass":True,"ledger":{"schema":SCHEMA,"entries":[*entries,entry]}}

def verify(ledger:dict)->list[str]:
    e=[]
    if ledger.get("schema")!=SCHEMA:return ["LEDGER_SCHEMA_INVALID"]
    prev=None
    for i,row in enumerate(ledger.get("entries") or [],start=1):
        if row.get("sequence")!=i:e.append(f"{i}:SEQUENCE_INVALID")
        if row.get("previous_entry_sha256")!=prev:e.append(f"{i}:PREVIOUS_HASH_MISMATCH")
        body={k:row.get(k) for k in ("sequence","receipt_sha256","receipt_schema","app_id","scene_id","previous_entry_sha256")}
        if row.get("entry_sha256")!=_hash(body):e.append(f"{i}:ENTRY_HASH_MISMATCH")
        prev=row.get("entry_sha256")
    return e
