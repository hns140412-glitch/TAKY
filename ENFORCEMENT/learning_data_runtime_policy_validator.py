#!/usr/bin/env python3
# Branch-only Policy Gate validation target; no product feature activation.
import argparse, json, sys
from pathlib import Path

ALLOWED_CLASSES={"READY_WITH_GUARDS","CONDITIONAL","HOLD"}
REQUIRED_POLICY_FIELDS=[
 "policy_id","function_id","source_family","evidence_class","authorization_class","consumer_app",
 "allowed_behaviors","forbidden_behaviors","cannot_claim","required_provenance","requires_human_review",
 "authority_owner","fail_closed_on_unknown"
]

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_registry(reg):
    errors=[]
    if reg.get("schema")!="TAKY_LEARNING_DATA_RUNTIME_POLICY_V1": errors.append("INVALID_SCHEMA")
    if not reg.get("policy_version"): errors.append("POLICY_VERSION_MISSING")
    if reg.get("fail_closed_on_unknown") is not True: errors.append("GLOBAL_FAIL_CLOSED_REQUIRED")
    seen=set()
    for row in reg.get("records",[]):
        for field in REQUIRED_POLICY_FIELDS:
            if field not in row: errors.append(f"POLICY_FIELD_MISSING:{row.get('policy_id','?')}:{field}")
        pid=row.get("policy_id")
        if pid in seen: errors.append(f"DUPLICATE_POLICY_ID:{pid}")
        seen.add(pid)
        cls=row.get("authorization_class")
        if cls not in ALLOWED_CLASSES: errors.append(f"INVALID_AUTHORIZATION_CLASS:{pid}")
        if row.get("fail_closed_on_unknown") is not True: errors.append(f"POLICY_FAIL_CLOSED_REQUIRED:{pid}")
        if cls=="HOLD" and row.get("allowed_behaviors"): errors.append(f"HOLD_ALLOWED_BEHAVIOR_FORBIDDEN:{pid}")
        if cls=="CONDITIONAL" and not row.get("required_provenance"): errors.append(f"CONDITIONAL_PROVENANCE_REQUIRED:{pid}")
        if not row.get("consumer_app"): errors.append(f"EXPLICIT_CONSUMER_REQUIRED:{pid}")
    return errors

def find_policy(reg,function_id,consumer_app):
    return next((x for x in reg.get("records",[]) if x.get("function_id")==function_id and x.get("consumer_app")==consumer_app),None)

def decide(reg,req):
    fid=req.get("function_id"); consumer=req.get("consumer_app"); behavior=req.get("requested_behavior")
    row=find_policy(reg,fid,consumer)
    base={"function_id":fid,"consumer_app":consumer,"requested_behavior":behavior}
    if not row:
        return {**base,"decision":"DENY","reason":"DENY_UNKNOWN_POLICY","cannot_claim":[]}
    cls=row["authorization_class"]
    out={**base,"policy_id":row["policy_id"],"policy_version":reg["policy_version"],"authorization_class":cls,"cannot_claim":row.get("cannot_claim",[])}
    if cls=="HOLD":
        return {**out,"decision":"DENY","reason":"DENY_HOLD"}
    if behavior not in row.get("allowed_behaviors",[]):
        reason="DENY_FORBIDDEN_BEHAVIOR" if behavior in row.get("forbidden_behaviors",[]) else "DENY_BEHAVIOR_NOT_ALLOWED"
        return {**out,"decision":"DENY","reason":reason}
    requested_claims=set(req.get("requested_claims",[]))
    if requested_claims.intersection(set(row.get("cannot_claim",[]))):
        return {**out,"decision":"DENY","reason":"DENY_CLAIM_BOUNDARY"}
    provided=set(req.get("provenance",[]))
    required=set(row.get("required_provenance",[]))
    if not required.issubset(provided):
        return {**out,"decision":"DENY","reason":"DENY_PROVENANCE_REQUIRED","missing_provenance":sorted(required-provided)}
    expected_owner=req.get("evidence_authority_owner")
    if expected_owner and expected_owner!=row.get("authority_owner"):
        return {**out,"decision":"DENY","reason":"DENY_AUTHORITY_MISMATCH"}
    if row.get("requires_human_review") and not req.get("human_review_evidence"):
        return {**out,"decision":"DENY","reason":"DENY_HUMAN_REVIEW_REQUIRED"}
    decision="ALLOW_CONDITIONAL" if cls=="CONDITIONAL" else "ALLOW"
    return {**out,"decision":decision,"reason":"POLICY_ALLOW"}

def replay(reg,fixture):
    failures=[]
    for case in fixture.get("cases",[]):
        result=decide(reg,case["request"])
        if result.get("decision")!=case.get("expected_decision") or result.get("reason")!=case.get("expected_reason"):
            failures.append({"id":case.get("id"),"expected":[case.get("expected_decision"),case.get("expected_reason")],"actual":[result.get("decision"),result.get("reason")]})
    return failures

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--policy",default="MASTER/LEARNING_DATA_RUNTIME_POLICY.json")
    ap.add_argument("--replay")
    args=ap.parse_args()
    reg=load(args.policy)
    errors=validate_registry(reg)
    if errors:
        for e in errors: print(e)
        return 1
    if args.replay:
        failures=replay(reg,load(args.replay))
        if failures:
            print(json.dumps(failures,ensure_ascii=False,indent=2))
            return 1
        print("LEARNING_DATA_RUNTIME_POLICY_REPLAY_PASS")
    else:
        print("LEARNING_DATA_RUNTIME_POLICY_SCHEMA_PASS")
    return 0

if __name__=="__main__":
    sys.exit(main())
