#!/usr/bin/env python3
from __future__ import annotations

SCHEMA="TAKY_CREW_EVIDENCE_EVENT_V1"
TYPES={"FIRST_MEETING","SHARED_EPISODE","EXPLORATION_COMPLETE","HELP_ACCEPTED","COACHING_SHARED"}

def validate(e:dict)->list[str]:
    out=[]
    if e.get("schema") not in (None,SCHEMA):out.append("SCHEMA_INVALID")
    if not str(e.get("event_id","")).strip():out.append("EVENT_ID_MISSING")
    if e.get("type") not in TYPES:out.append("TYPE_INVALID")
    if e.get("verified") is not True:out.append("VERIFIED_REQUIRED")
    if not str(e.get("evidence_ref","")).strip():out.append("EVIDENCE_REF_MISSING")
    if not str(e.get("character_id","")).strip():out.append("CHARACTER_ID_MISSING")
    if not str(e.get("source","") or e.get("source_app","")).strip():out.append("SOURCE_MISSING")
    if not str(e.get("at","") or e.get("occurred_at","")).strip():out.append("TIME_MISSING")
    return out

def to_relation_event(e:dict)->dict:
    errors=validate(e)
    if errors:return {"pass":False,"detected":errors}
    return {"pass":True,"event":{
      "event_id":str(e["event_id"]),
      "type":e["type"],
      "verified":True,
      "evidence_ref":str(e["evidence_ref"]),
      "at":e.get("at") or e.get("occurred_at"),
      "source":e.get("source") or e.get("source_app")
    }}
