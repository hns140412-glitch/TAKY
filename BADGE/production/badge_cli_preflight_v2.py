#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
from build_badge_production_packets_v2 import ROOT,build
from verify_badge_production_packets_v2 import verify as verify_packets

CFG="BADGE/production/badge-cli-preflight-v2.json"
LEGACY="BADGE/production/badge-production-pipeline.json"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(root,rel): return json.loads((Path(root)/rel).read_text(encoding="utf-8"))

def inspect(root=ROOT, executor_adapter=None, enable_generation=False):
    root=Path(root); errors=[]; blockers=[]; warnings=[]
    cfg=load(root,CFG); packets=build(root); legacy=load(root,LEGACY)
    if cfg.get("schema")!="TAKY_BADGE_CLI_PREFLIGHT_V2": errors.append("PREFLIGHT_SCHEMA")
    if cfg.get("executable_authority")!="BADGE/production/badge-production-packets-v2.json": errors.append("EXECUTABLE_AUTHORITY_DRIFT")
    if legacy.get("executable") is not False or legacy.get("status")!="HISTORICAL_NON_EXECUTABLE_SUPERSEDED_BY_V2":
        errors.append("LEGACY_V1_EXECUTABLE")
    errors.extend("PACKET_"+x for x in verify_packets(root))
    items=packets["items"]; batch_size=cfg.get("batch_size")
    if batch_size!=5: errors.append("BATCH_SIZE_MUST_BE_5")
    work=[x for x in items if x["production_classification"]=="REWORK_REQUIRED"]
    batches=[work[i:i+batch_size] for i in range(0,len(work),batch_size)]
    flat=[x["badge_id"] for b in batches for x in b]
    if flat!=[x["badge_id"] for x in work] or any(len(b)>5 for b in batches): errors.append("BATCH_PLAN_DRIFT")
    ex=cfg.get("execution",{})
    for k in ("allow_overwrite","allow_shell_from_packet","allow_network_from_preflight"):
        if ex.get(k) is not False: errors.append("UNSAFE_"+k.upper())
    for k in ("resume_required","checkpoint_required","per_badge_failure_isolation","continue_other_badges_after_isolated_failure"):
        if ex.get(k) is not True: errors.append("MISSING_"+k.upper())
    own=cfg.get("ownership_rules",{})
    if own!={"unearned_star_count":0,"initial_award_star_count":1}: errors.append("OWNERSHIP_RULE_DRIFT")
    depth=cfg.get("detail_depth",{})
    if depth.get("surface")!="BADGE_DETAIL_VIEW_ONLY" or depth.get("earned_only") is not True: errors.append("DETAIL_DEPTH_DRIFT")
    if not executor_adapter: blockers.append("EXECUTOR_ADAPTER_NOT_BOUND")
    if not enable_generation: blockers.append("GENERATION_NOT_EXPLICITLY_ENABLED")
    if enable_generation and not executor_adapter: errors.append("GENERATION_WITHOUT_EXECUTOR_FORBIDDEN")
    source_files=[
      "BADGE/badge-60-story-20-history-working.json","BADGE/assets/individual-art-direction-60.json",
      "BADGE/badge-wow-inspired-copyworking.json","BADGE/production/badge-production-baseline-v2.json",
      "BADGE/assets/visual-rework-queue-working.json","BADGE/production/badge-production-standard-v2.json",
      "BADGE/production/badge-production-packets-v2.json"
    ]
    receipt={
      "schema":"TAKY_BADGE_CLI_PREFLIGHT_RECEIPT_V2",
      "structural_preflight_pass":not errors,
      "cli_ready":not errors and not blockers,
      "generation_executed":False,
      "errors":sorted(set(errors)),"blockers":sorted(set(blockers)),"warnings":warnings,
      "counts":packets["classification_counts"],"batch_size":5,
      "rework_batch_count":len(batches),
      "rework_batches":[[x["badge_id"] for x in b] for b in batches],
      "source_sha256":{p:sha(root/p) for p in source_files},
      "executor_adapter":executor_adapter,
      "generation_enabled_requested":bool(enable_generation)
    }
    return receipt

def main():
    p=argparse.ArgumentParser(description="Badge CLI structural preflight. Never invokes a generator.")
    p.add_argument("--executor-adapter")
    p.add_argument("--enable-generation",action="store_true")
    p.add_argument("--require-cli-ready",action="store_true")
    p.add_argument("--output")
    a=p.parse_args()
    r=inspect(executor_adapter=a.executor_adapter,enable_generation=a.enable_generation)
    out=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
    if a.output: Path(a.output).write_text(out,encoding="utf-8")
    print(out,end="")
    if not r["structural_preflight_pass"]: raise SystemExit(2)
    if a.require_cli_ready and not r["cli_ready"]: raise SystemExit(3)
if __name__=="__main__": main()
