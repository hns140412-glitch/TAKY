#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/"BADGE/production/badge-cli-executor-adapter-contract-v1.json"
def verify(doc=None):
 d=doc or json.loads(P.read_text(encoding="utf-8"));e=[];r=d.get("resource_policy",{});i=d.get("image_policy",{})
 if d.get("schema")!="TAKY_BADGE_CLI_EXECUTOR_ADAPTER_CONTRACT_V1":e.append("SCHEMA")
 if r.get("max_badges_per_batch")!=5:e.append("BATCH_LIMIT")
 if not isinstance(r.get("max_generation_attempts_per_badge"),int) or not 1<=r["max_generation_attempts_per_badge"]<=2:e.append("RETRY_LIMIT")
 for k in ("sequential_batches","no_parallel_batch_fanout","checkpoint_after_each_badge","checkpoint_after_each_batch","stop_on_quota_or_rate_limit","resume_without_regenerating_passed"):
  if r.get(k) is not True:e.append("RESOURCE_"+k)
 if r.get("keep_track_generation_default") is not False:e.append("KEEP_CALL_WASTE")
 if i.get("contact_sheet_generation") is not False or i.get("required_layers")!=["base","bg","subject","fx"]:e.append("IMAGE_CONTRACT")
 if d.get("generation_enabled") and not d.get("provider"):e.append("PROVIDER_REQUIRED")
 return sorted(set(e))
if __name__=="__main__":
 e=verify()
 if e:raise SystemExit("EXECUTOR CONTRACT BLOCKED: "+",".join(e))
 print("EXECUTOR ADAPTER CONTRACT PASS: quota-safe behavior locked; provider remains unbound.")
