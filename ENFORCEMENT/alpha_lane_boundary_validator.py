from pathlib import Path
import json,hashlib,sys
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003"); REVIEW=ROOT/"ALPHA_REVIEW"; fail=[]
lane=json.loads((ROOT/"ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json").read_text(encoding="utf-8"))
post=json.loads((ROOT/"ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json").read_text(encoding="utf-8"))
master=(ROOT/"ALPHA/TAKY_ALPHA_MASTER_V0_1.md").read_text(encoding="utf-8")
if lane.get("scope")!="LOCAL_INFRA_ONLY" or lane.get("implies_system_alpha") is not False: fail.append("LANE_SCOPE_LEAK")
if post.get("authority_transfer") is not False: fail.append("POST_FREEZE_AUTHORITY_TRANSFER")
expected=lane.get("canonical_rule_registry",{}).get("expected_blob_sha") or lane.get("canonical_rule_registry",{}).get("blob_sha")
b=(ROOT/"MASTER/RULE_REGISTRY.json").read_bytes().replace(b"\r\n",b"\n")
blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
if expected and blob!=expected: fail.append("LANE_CANONICAL_REGISTRY_BLOB_MISMATCH")
d=lane.get("local_candidate_registry_diff",{})
if not d.get("candidate_only") or not d.get("canonical_only") or "NO_AUTHORITY_TRANSFER" not in str(d.get("disposition")): fail.append("LANE_REGISTRY_DIFF_NOT_EXPLICIT")
if "LOCAL_ALPHA_COMPLETE != SYSTEM_ALPHA_COMPLETE" not in master: fail.append("MASTER_LANE_BOUNDARY_MISSING")
res={"schema":"TAKY_ALPHA_LANE_BOUNDARY_VALIDATION_V1","date":"2026-10-04","status":"PASS" if not fail else "FAIL","failure_count":len(fail),"failures":fail,"normalized_canonical_rule_blob":blob}
(REVIEW/"ALPHA_LANE_BOUNDARY_VALIDATION_20261004.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False)); sys.exit(0 if not fail else 1)
