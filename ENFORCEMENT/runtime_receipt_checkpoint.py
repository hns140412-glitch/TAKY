#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json

SCHEMA="TAKY_RUNTIME_RECEIPT_LEDGER_V1"
CHECKPOINT_SCHEMA="TAKY_RUNTIME_RECEIPT_LEDGER_CHECKPOINT_V1"

def _hash(x)->str:
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def checkpoint(ledger:dict,interval:int=100)->dict:
    entries=list(ledger.get("entries") or [])
    if ledger.get("schema")!=SCHEMA:return {"pass":False,"error":"LEDGER_SCHEMA_INVALID"}
    if not entries:return {"pass":False,"error":"NO_ENTRIES"}
    if interval<1:return {"pass":False,"error":"INTERVAL_INVALID"}
    if len(entries)%interval!=0:return {"pass":False,"error":"CHECKPOINT_INTERVAL_NOT_REACHED"}
    body={
      "schema":CHECKPOINT_SCHEMA,
      "sequence":entries[-1].get("sequence"),
      "last_entry_sha256":entries[-1].get("entry_sha256"),
      "entry_count":len(entries),
      "ledger_sha256":_hash(entries)
    }
    return {"pass":True,**body,"checkpoint_sha256":_hash(body)}

def recover(entries:list[dict],cp:dict)->dict:
    if cp.get("schema")!=CHECKPOINT_SCHEMA:return {"pass":False,"error":"CHECKPOINT_SCHEMA_INVALID"}
    count=cp.get("entry_count")
    if not isinstance(count,int) or count<1 or len(entries)<count:return {"pass":False,"error":"CHECKPOINT_COUNT_INVALID"}
    prefix=entries[:count]
    if _hash(prefix)!=cp.get("ledger_sha256"):return {"pass":False,"error":"CHECKPOINT_LEDGER_HASH_MISMATCH"}
    if prefix[-1].get("entry_sha256")!=cp.get("last_entry_sha256"):return {"pass":False,"error":"CHECKPOINT_LAST_ENTRY_MISMATCH"}
    return {"pass":True,"verified_entry_count":count,"last_verified_entry_sha256":cp.get("last_entry_sha256"),
            "resume_from_sequence":count+1}
