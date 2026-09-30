#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
from build_badge_production_packets_v2 import ROOT,build

STATES=("PENDING","IN_PROGRESS","QA_PENDING","PASSED","FAILED_ISOLATED","ADMITTED")
def digest_obj(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def make_plan():
    p=build();work=[x for x in p["items"] if x["production_classification"]=="REWORK_REQUIRED"]
    batches=[]
    for n,i in enumerate(range(0,len(work),5),1):
        members=[]
        for x in work[i:i+5]:
            members.append({"badge_id":x["badge_id"],"packet_sha256":digest_obj(x),"state":"PENDING","attempt":0,
                            "last_error":None,"output_receipt":None})
        batches.append({"batch_id":f"REWORK-{n:02d}","members":members})
    plan={"schema":"TAKY_BADGE_CLI_EXECUTION_PLAN_V2","mode":"PLAN_ONLY_NO_GENERATION","batch_size":5,
          "overwrite":False,"failure_policy":"ISOLATE_BADGE_CONTINUE_BATCH","resume":"CHECKPOINT_REQUIRED",
          "batches":batches}
    plan["plan_sha256"]=digest_obj({k:v for k,v in plan.items() if k!="plan_sha256"})
    return plan
def validate(plan):
    errors=[]
    if plan.get("schema")!="TAKY_BADGE_CLI_EXECUTION_PLAN_V2":errors.append("PLAN_SCHEMA")
    if plan.get("mode")!="PLAN_ONLY_NO_GENERATION":errors.append("PLAN_MUST_START_NON_EXECUTING")
    if plan.get("overwrite") is not False:errors.append("OVERWRITE_FORBIDDEN")
    members=[m for b in plan.get("batches",[]) for m in b.get("members",[])]
    if len(members)!=31 or len({m.get("badge_id") for m in members})!=31:errors.append("REWORK_UNIVERSE")
    if any(len(b.get("members",[]))>5 for b in plan.get("batches",[])):errors.append("BATCH_OVER_5")
    if any(m.get("state") not in STATES for m in members):errors.append("INVALID_STATE")
    expected=digest_obj({k:v for k,v in plan.items() if k!="plan_sha256"})
    if plan.get("plan_sha256")!=expected:errors.append("PLAN_HASH_MISMATCH")
    return errors
def resumable_members(plan):
    return [m["badge_id"] for b in plan["batches"] for m in b["members"] if m["state"] in ("PENDING","FAILED_ISOLATED")]
def main():
    p=argparse.ArgumentParser();p.add_argument("--output");p.add_argument("--validate");p.add_argument("--resume-list",action="store_true");a=p.parse_args()
    if a.validate:
        plan=json.loads(Path(a.validate).read_text(encoding="utf-8"));e=validate(plan)
        if e:raise SystemExit("PLAN BLOCKED: "+",".join(e))
        print("PLAN PASS")
        if a.resume_list:print(json.dumps(resumable_members(plan),ensure_ascii=False))
        return
    plan=make_plan();out=json.dumps(plan,ensure_ascii=False,indent=2)+"\n"
    if a.output:Path(a.output).write_text(out,encoding="utf-8")
    print(out,end="")
if __name__=="__main__":main()
