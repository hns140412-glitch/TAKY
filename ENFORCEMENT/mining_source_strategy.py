#!/usr/bin/env python3
"""Source strategy for TAKY Mining Core.

Plans source families by evidence need; does not execute external search.
"""
from __future__ import annotations

SOURCE_POLICIES={
 "RULE":{"preferred":["PRIMARY","OFFICIAL"],"secondary":["ACADEMIC"],"community_role":"DISCOVERY_ONLY"},
 "FACT":{"preferred":["PRIMARY","OFFICIAL","ACADEMIC"],"secondary":["IMPLEMENTATION"],"community_role":"DISCOVERY_OR_EXPERIENCE"},
 "IMPLEMENTATION":{"preferred":["PRIMARY","IMPLEMENTATION"],"secondary":["ACADEMIC","COMMUNITY"],"community_role":"PRACTICE_EVIDENCE"},
 "EXPERIENCE":{"preferred":["COMMUNITY","IMPLEMENTATION"],"secondary":["PRIMARY"],"community_role":"DIRECT_EXPERIENCE"},
 "TREND":{"preferred":["PRIMARY","IMPLEMENTATION","COMMUNITY"],"secondary":["ACADEMIC"],"community_role":"SIGNAL_NOT_AUTHORITY"},
}

def infer_need(item:dict)->str:
    explicit=str(item.get("evidence_need","")).upper()
    if explicit in SOURCE_POLICIES:return explicit
    kind=str(item.get("kind","")).upper()
    text=str(item.get("question","")).lower()
    if kind=="CONFLICT" or any(x in text for x in ("rule","law","official","regulation","기준","법","고시")):return "RULE"
    if kind=="ADVANCED" or any(x in text for x in ("implement","runtime","code","구현")):return "IMPLEMENTATION"
    if any(x in text for x in ("review","experience","community","후기","경험")):return "EXPERIENCE"
    if any(x in text for x in ("trend","latest","current","트렌드","최신")):return "TREND"
    return "FACT"

def plan_sources(frontier:list[dict])->list[dict]:
    out=[]
    for item in frontier:
        if item.get("status")=="CLOSED":continue
        need=infer_need(item); policy=SOURCE_POLICIES[need]
        out.append({"frontier_id":item.get("id"),"evidence_need":need,"preferred_source_classes":policy["preferred"],"secondary_source_classes":policy["secondary"],"community_role":policy["community_role"],"independent_sources_target":2 if item.get("status")=="CONFLICT" else 1})
    return out

def diversity_check(evidence:list[dict],frontier_id:str)->dict:
    rows=[e for e in evidence if str(e.get("frontier_id"))==str(frontier_id)]
    identities={str(e.get("source_identity") or e.get("source_url") or e.get("source_id") or "") for e in rows}
    identities.discard("")
    classes={str(e.get("source_class","UNKNOWN")).upper() for e in rows}
    return {"independent_source_count":len(identities),"source_classes":sorted(classes),"has_authoritative_source":bool(classes & {"PRIMARY","OFFICIAL","ACADEMIC"})}
