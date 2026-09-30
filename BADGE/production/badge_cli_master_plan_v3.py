#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
from build_badge_production_packets_v2 import ROOT,build
STATES=("PENDING","IN_PROGRESS","QA_PENDING","PASSED","FAILED_ISOLATED","ADMITTED","REWORK_ESCALATED")
def digest_obj(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def member(x,track):
 return {"badge_id":x["badge_id"],"visual_id":x["visual_id"],"track":track,
  "action":"VERIFY_EXISTING_NO_GENERATION" if track=="KEEP_VERIFY" else "GENERATE_REWORK_CANDIDATE",
  "generation_allowed":track=="REWORK_GENERATE","packet_sha256":digest_obj(x),"state":"PENDING","attempt":0,"last_error":None,"output_receipt":None}
def batches(items,prefix):
 return [{"batch_id":f"{prefix}-{n:02d}","members":[member(x,"KEEP_VERIFY" if prefix=="KEEP" else "REWORK_GENERATE") for x in items[i:i+5]]}
         for n,i in enumerate(range(0,len(items),5),1)]
def make_plan():
 p=build();keep=[x for x in p["items"] if x["production_classification"]=="KEEP_CANDIDATE"];rw=[x for x in p["items"] if x["production_classification"]=="REWORK_REQUIRED"]
 plan={"schema":"TAKY_BADGE_CLI_MASTER_EXECUTION_PLAN_V3","mode":"PLAN_ONLY_NO_GENERATION","universe_count":len(p["items"]),"batch_size":5,
  "overwrite":False,"keep_failure_policy":"ESCALATE_TO_REWORK_ONLY_AFTER_QA_FAILURE","failure_policy":"ISOLATE_BADGE_CONTINUE_BATCH",
  "resume":"CHECKPOINT_REQUIRED","tracks":{"KEEP_VERIFY":{"count":len(keep),"generation_default":False,"batches":batches(keep,"KEEP")},
  "REWORK_GENERATE":{"count":len(rw),"generation_default":True,"batches":batches(rw,"REWORK")}}}
 plan["plan_sha256"]=digest_obj({k:v for k,v in plan.items() if k!="plan_sha256"});return plan
def all_members(p):return [m for t in p["tracks"].values() for b in t["batches"] for m in b["members"]]
def validate(p):
 e=[];ms=all_members(p)
 if p.get("schema")!="TAKY_BADGE_CLI_MASTER_EXECUTION_PLAN_V3":e.append("PLAN_SCHEMA")
 if p.get("mode")!="PLAN_ONLY_NO_GENERATION":e.append("PLAN_START_MODE")
 if p.get("universe_count")!=60 or len(ms)!=60 or len({m["badge_id"] for m in ms})!=60:e.append("MASTER_60_UNIVERSE")
 if p["tracks"]["KEEP_VERIFY"]["count"]!=29 or p["tracks"]["REWORK_GENERATE"]["count"]!=31:e.append("TRACK_COUNTS")
 if any(m["generation_allowed"] for b in p["tracks"]["KEEP_VERIFY"]["batches"] for m in b["members"]):e.append("KEEP_GENERATION_FORBIDDEN")
 if any(not m["generation_allowed"] for b in p["tracks"]["REWORK_GENERATE"]["batches"] for m in b["members"]):e.append("REWORK_GENERATION_REQUIRED")
 if any(len(b["members"])>5 for t in p["tracks"].values() for b in t["batches"]):e.append("BATCH_OVER_5")
 if p.get("overwrite") is not False:e.append("OVERWRITE_FORBIDDEN")
 if p.get("plan_sha256")!=digest_obj({k:v for k,v in p.items() if k!="plan_sha256"}):e.append("PLAN_HASH_MISMATCH")
 return sorted(set(e))
def main():
 a=argparse.ArgumentParser();a.add_argument("--output");a.add_argument("--validate");x=a.parse_args()
 p=json.loads(Path(x.validate).read_text(encoding="utf-8")) if x.validate else make_plan();e=validate(p)
 if e:raise SystemExit("MASTER PLAN BLOCKED: "+",".join(e))
 out=json.dumps(p,ensure_ascii=False,indent=2)+"\n"
 if x.output:Path(x.output).write_text(out,encoding="utf-8")
 print("MASTER PLAN PASS: 60/60; KEEP 29 verify-only; REWORK 31 generation-eligible; max batch 5." if x.validate else out,end="" if not x.validate else "\n")
if __name__=="__main__":main()
