#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

VALID_DOMAINS={"ARCHI_GROW","LEARNING_GROW","SYSTEM_GROW","UNROUTED"}
VALID_STAGES={"RAW","INDEX","LEARNING","RELATION","EXECUTION","OUTCOME","GROWTH"}

def _clean(v): return str(v or "").strip()

def _stable_id(payload:dict)->str:
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return "GLE-"+hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

def make_event(*,grow_domain:str,stage:str,producer:str,source_ref:str,parent_refs:list[str]|None=None,
               authority:str="EVIDENCE_ONLY",payload:dict|None=None,recorded_at:str|None=None)->dict:
    grow_domain=_clean(grow_domain).upper() or "UNROUTED"
    stage=_clean(stage).upper()
    if grow_domain not in VALID_DOMAINS: raise ValueError("GROW_DOMAIN_INVALID")
    if stage not in VALID_STAGES: raise ValueError("GROW_STAGE_INVALID")
    parents=[_clean(x) for x in (parent_refs or []) if _clean(x)]
    if stage in {"LEARNING","RELATION","EXECUTION","OUTCOME","GROWTH"} and not parents:
        raise ValueError("GROW_PARENT_REQUIRED")
    identity={
        "grow_domain":grow_domain,"stage":stage,"producer":_clean(producer),
        "source_ref":_clean(source_ref),"parent_refs":sorted(set(parents)),
        "payload":payload or {}
    }
    return {
        "schema":"GROW_LINEAGE_EVENT_V1",
        "event_id":_stable_id(identity),
        "grow_domain":grow_domain,
        "stage":stage,
        "producer":_clean(producer),
        "source_ref":_clean(source_ref),
        "parent_refs":identity["parent_refs"],
        "authority":_clean(authority) or "EVIDENCE_ONLY",
        "promotion_authorized":False,
        "authority_transfer":False,
        "recorded_at":recorded_at or datetime.now(timezone.utc).isoformat(),
        "payload":payload or {}
    }

def validate_event(event:dict)->list[str]:
    errors=[]
    for k in ("event_id","grow_domain","stage","producer","source_ref","authority"):
        if not _clean(event.get(k)): errors.append("GROW_EVENT_MISSING:"+k)
    if event.get("grow_domain") not in VALID_DOMAINS: errors.append("GROW_EVENT_DOMAIN_INVALID")
    if event.get("stage") not in VALID_STAGES: errors.append("GROW_EVENT_STAGE_INVALID")
    if event.get("promotion_authorized") is not False: errors.append("GROW_EVENT_PROMOTION_FORBIDDEN")
    if event.get("authority_transfer") is not False: errors.append("GROW_EVENT_AUTHORITY_TRANSFER_FORBIDDEN")
    if event.get("stage") in {"LEARNING","RELATION","EXECUTION","OUTCOME","GROWTH"} and not event.get("parent_refs"):
        errors.append("GROW_EVENT_PARENT_REQUIRED")
    return errors

def _refresh_outcome_utility_best_effort(ledger_path:Path)->dict:
    if ledger_path.name.lower() != "grow-lineage.jsonl":
        return {"attempted":False,"ok":True,"reason":"NOT_SHARED_GROW_LINEAGE"}
    sidecar = ledger_path.parent / "data-index-outcome-utility.json"
    try:
        from data_index_outcome_utility import aggregate_events, load_jsonl
        utility = aggregate_events(load_jsonl(ledger_path))
        payload = {
            "schema":"TAKY_DATA_INDEX_OUTCOME_UTILITY_V1",
            "authoritative":False,
            "ranking_role":"SECONDARY_ONLY",
            "precedence":"EXACT -> CURRENT -> OUTCOME_UTILITY -> RETRIEVAL_SCORE",
            "source_count":len(utility),
            "by_source_id":utility,
        }
        tmp = sidecar.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        tmp.replace(sidecar)
        return {"attempted":True,"ok":True,"path":str(sidecar),"source_count":len(utility)}
    except Exception as exc:
        return {"attempted":True,"ok":False,"error_type":type(exc).__name__,"non_blocking":True}


def materialize(event:dict, ledger_path:Path)->dict:
    errors=validate_event(event)
    if errors: return {"ok":False,"errors":errors,"appended":False}
    ledger_path=Path(ledger_path)
    ledger_path.parent.mkdir(parents=True,exist_ok=True)
    existing_ids=set()
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8-sig").splitlines():
            try:
                row=json.loads(line)
                if row.get("event_id"): existing_ids.add(row["event_id"])
            except Exception:
                continue
    if event["event_id"] in existing_ids:
        projection = _refresh_outcome_utility_best_effort(ledger_path)
        return {"ok":True,"errors":[],"appended":False,"idempotent":True,"event_id":event["event_id"],"utility_projection":projection}
    with ledger_path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(event,ensure_ascii=False)+"\n")
    projection = _refresh_outcome_utility_best_effort(ledger_path)
    return {"ok":True,"errors":[],"appended":True,"idempotent":False,"event_id":event["event_id"],"utility_projection":projection}

if __name__=="__main__":
    print(json.dumps({"schema":"GROW_LINEAGE_EVENT_V1"},ensure_ascii=False))
