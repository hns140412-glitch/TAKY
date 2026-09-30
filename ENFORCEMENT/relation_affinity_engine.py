#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

SCHEMA="TAKY_RELATION_AFFINITY_EVIDENCE_V1"
STATES=("NOT_MET","KNOWN","FAMILIAR","TRUSTED")
VERIFIED_TYPES={"FIRST_MEETING","SHARED_EPISODE","EXPLORATION_COMPLETE","HELP_ACCEPTED","COACHING_SHARED"}

def clean_events(events):
    out=[];seen=set()
    for x in events or []:
        if not isinstance(x,dict):continue
        eid=str(x.get("event_id","")).strip()
        if not eid or eid in seen:continue
        if x.get("verified") is not True:continue
        if x.get("type") not in VERIFIED_TYPES:continue
        if not str(x.get("evidence_ref","")).strip():continue
        seen.add(eid);out.append({
          "event_id":eid,"type":x["type"],"evidence_ref":str(x["evidence_ref"]),
          "at":x.get("at"),"source":x.get("source")
        })
    return out

def validate_policy(p):
    e=[]
    if not isinstance(p,dict):return ["POLICY_MISSING"]
    f=p.get("familiar_min_verified_episodes")
    t=p.get("trusted_min_verified_episodes")
    if not isinstance(f,int) or f<1:e.append("FAMILIAR_THRESHOLD_INVALID")
    if not isinstance(t,int) or t<=f:e.append("TRUSTED_THRESHOLD_INVALID")
    return e

def evaluate(member:dict,policy:dict)->dict:
    pe=validate_policy(policy)
    if pe:return {"schema":SCHEMA,"pass":False,"detected":pe}
    current=member.get("committed_state","NOT_MET")
    if current not in STATES:return {"schema":SCHEMA,"pass":False,"detected":["COMMITTED_STATE_INVALID"]}
    events=clean_events(member.get("events"))
    met=any(x["type"]=="FIRST_MEETING" for x in events)
    episodes=[x for x in events if x["type"]!="FIRST_MEETING"]
    if not met:
        candidate="NOT_MET"
    elif len(episodes)>=policy["trusted_min_verified_episodes"]:
        candidate="TRUSTED"
    elif len(episodes)>=policy["familiar_min_verified_episodes"]:
        candidate="FAMILIAR"
    else:
        candidate="KNOWN"
    return {
      "schema":SCHEMA,"pass":True,"character_id":member.get("character_id"),
      "committed_state":current,"candidate_state":candidate,
      "verified_first_meeting":met,"verified_episode_count":len(episodes),
      "verified_event_ids":[x["event_id"] for x in events],
      "promotion_required":candidate!=current,
      "promotion_auto_commit":False,
      "reward_delta":0,"power_delta":0,"ability_delta":0,
      "owner_commit_required":True
    }

def commit(result:dict, approved:bool)->dict:
    if not result.get("pass"):return {"pass":False,"error":"INVALID_RELATION_RESULT"}
    if not approved:
        return {"pass":True,"status":"HELD","character_id":result.get("character_id"),
                "effective_relationship_state":result.get("committed_state"),"auto_promoted":False}
    return {"pass":True,"status":"COMMITTED","character_id":result.get("character_id"),
            "effective_relationship_state":result.get("candidate_state"),"auto_promoted":False,
            "evidence_event_ids":result.get("verified_event_ids",[])}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    e=sp.add_parser("evaluate");e.add_argument("input")
    c=sp.add_parser("commit");c.add_argument("result");c.add_argument("--approved",action="store_true")
    a=ap.parse_args()
    if a.cmd=="evaluate":
        x=json.loads(Path(a.input).read_text(encoding="utf8"))
        out=evaluate(x["member"],x["policy"])
    else:
        out=commit(json.loads(Path(a.result).read_text(encoding="utf8")),a.approved)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out.get("pass") else 1
if __name__=="__main__":raise SystemExit(main())
