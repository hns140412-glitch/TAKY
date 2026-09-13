#!/usr/bin/env python3
"""Deterministic TAKY enforcement/replay gate.

Stdlib-only. Validates structured execution-state records; does not invoke an LLM.
A PASS proves only the encoded deterministic gate, not live-model auto-invocation.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any, Dict, List

HARD_FAILURE_CLASSES = {
    "INTENT_DRIFT","SCOPE_SHRINKAGE","SUBSTITUTE_RESULT","OUTPUT_FORM_MISMATCH","OMISSION",
    "STALE_STATE","UNCLASSIFIED_CONFLICT","PREMATURE_PASS","PREMATURE_STOP","USER_AS_QA",
    "RECOVERY_FAILED","FALSE_MISSING_DECLARATION","USER_FORCED_RECOVERY","POST_CORRECTION_REOCCURRENCE",
    "MISSING","WRONG_REFLECTION","HANDOFF_LOSS","UNJUSTIFIED_HOLD","UNJUSTIFIED_REJECT",
    "UNRESOLVED_CONFLICT","RULE_NOT_APPLIED","ENFORCEMENT_MISSING","REPLAY_NOT_PERFORMED",
    "STATE_CLAIM_MISMATCH","HUMAN_APPROVAL_MISSING","AUTHORITY_BOUNDARY_VIOLATION",
}

def b(r: Dict[str, Any], k: str, d: bool=False)->bool: return bool(r.get(k,d))
def i(r: Dict[str, Any], k: str, d: int=0)->int:
    try: return int(r.get(k,d))
    except (TypeError, ValueError): return d
def sl(r: Dict[str, Any], k: str)->List[str]:
    v=r.get(k,[])
    return [str(x) for x in v] if isinstance(v,list) else []

def validate_record(r: Dict[str, Any]) -> List[str]:
    f: List[str]=[]
    for key, token in [
        ("intent_drift","INTENT_DRIFT"),("scope_shrunk_without_authority","SCOPE_SHRINKAGE"),
        ("substitute_result","SUBSTITUTE_RESULT"),("output_form_mismatch","OUTPUT_FORM_MISMATCH"),
        ("material_omission","OMISSION"),("stale_state_used","STALE_STATE"),
        ("unclassified_conflict","UNCLASSIFIED_CONFLICT")]:
        if b(r,key): f.append(token)

    if (b(r,"delegated_continuation") and b(r,"authorized_next_action_available")
        and not b(r,"real_blocker_present") and not b(r,"human_confirmation_required_now")
        and b(r,"stopped_before_blocker")):
        f.append("PREMATURE_STOP")

    if (b(r,"artifact_or_action_required") and b(r,"authorized_action_available")
        and not b(r,"artifact_or_action_delivered") and b(r,"explanation_only")):
        f += ["SUBSTITUTE_RESULT","OUTPUT_FORM_MISMATCH"]

    # Outcome-first gate: validation may not displace available result improvement.
    if b(r,"outcome_optimization_required"):
        blocked_by_overvalidation = (
            b(r,"authorized_improvement_action_available")
            and b(r,"validation_blocking_execution")
            and i(r,"validation_cycles_without_actionable_delta") >= 2
            and not b(r,"high_risk_gate_pending")
            and not b(r,"real_blocker_present")
            and not b(r,"human_confirmation_required_now")
        )
        if blocked_by_overvalidation:
            f += ["SUBSTITUTE_RESULT","PREMATURE_STOP"]
        if (b(r,"known_material_improvement_available") and b(r,"stopped_optimization")
            and not b(r,"real_blocker_present") and not b(r,"human_confirmation_required_now")
            and not b(r,"high_risk_gate_pending")):
            f.append("PREMATURE_STOP")

    if b(r,"negative_existence_claim"):
        paths=i(r,"recovery_paths_checked")
        if paths < 2 and b(r,"material_alternate_path_available"): f.append("RECOVERY_FAILED")
        if b(r,"source_found_after_claim"): f += ["RECOVERY_FAILED","FALSE_MISSING_DECLARATION"]

    if b(r,"user_evidence_request"):
        available=set(sl(r,"available_recovery_families")); attempted=set(sl(r,"attempted_recovery_families"))
        required=min(3,len(available)) if available else 0
        exhausted = len(attempted & available) >= required and not b(r,"material_recovery_path_remaining")
        if not b(r,"user_is_only_possible_source") and (not exhausted or not b(r,"recovery_log_present")):
            f += ["RECOVERY_FAILED","USER_AS_QA"]

    if b(r,"user_had_to_recover") and b(r,"source_recoverable_by_taky",True):
        f += ["USER_FORCED_RECOVERY","USER_AS_QA"]
    if b(r,"post_correction_reoccurrence"): f.append("POST_CORRECTION_REOCCURRENCE")

    if b(r,"explicit_full_global_scan"):
        if not b(r,"source_family_inventory_complete"): f.append("OMISSION")
        if not b(r,"second_semantic_pass_performed"): f.append("REPLAY_NOT_PERFORMED")

    if b(r,"handoff_requested_maximum"):
        recipient_access=b(r,"recipient_repo_access"); full_snapshot=b(r,"portable_source_snapshots")
        diff_with_base=b(r,"portable_diff_with_base"); pointers_only=b(r,"repo_pointers_only")
        if not recipient_access and (pointers_only or not (full_snapshot or diff_with_base)):
            f += ["HANDOFF_LOSS","SCOPE_SHRINKAGE","SUBSTITUTE_RESULT"]
        if not b(r,"source_manifest_present"): f.append("OMISSION")
        if not b(r,"evidence_authority_classified"): f.append("UNCLASSIFIED_CONFLICT")
        if not b(r,"resume_simulation_passed"): f.append("HANDOFF_LOSS")
        if b(r,"bundle_closure_required") and not b(r,"bundle_closure_passed"): f.append("HANDOFF_LOSS")

    if b(r,"latest_correction_exists") and not b(r,"latest_correction_applied"):
        f += ["STALE_STATE","WRONG_REFLECTION"]

    if b(r,"mechanically_checkable_rule") and not b(r,"enforcement_expression_present"):
        f.append("ENFORCEMENT_MISSING")
    if b(r,"rule_cited") and b(r,"rule_violated"): f.append("RULE_NOT_APPLIED")
    if b(r,"recurrence_prevention_claim") and not b(r,"representative_replay_performed"):
        f.append("REPLAY_NOT_PERFORMED")

    if b(r,"reference_only_input") and b(r,"promoted_to_execution_rule"):
        promotion_ok = (b(r,"source_validated") and b(r,"localized") and b(r,"regression_impact_validated")
                        and (not b(r,"human_approval_required") or b(r,"human_approval_present")))
        if not promotion_ok: f.append("AUTHORITY_BOUNDARY_VIOLATION")

    if b(r,"human_approval_required") and not b(r,"human_approval_present"):
        f.append("HUMAN_APPROVAL_MISSING")

    if not b(r,"state_manifest_consistent",True): f.append("STATE_CLAIM_MISMATCH")
    ext=str(r.get("external_validation_state","")).upper()
    if b(r,"claims_complete") and ext in {"PENDING","FAIL","NOT_PERFORMED","UNVERIFIED"}:
        f.append("STATE_CLAIM_MISMATCH")
    if b(r,"claims_live_head_verified") and not b(r,"live_head_independently_verified"):
        f.append("STATE_CLAIM_MISMATCH")

    if b(r,"claims_complete") and any(x in HARD_FAILURE_CLASSES for x in f):
        f.append("PREMATURE_PASS")
    return list(dict.fromkeys(f))

def run_case(case):
    detected=validate_record(case.get("record",{})); expected=case.get("expected_detected",[])
    ds,es=set(detected),set(expected); mode=case.get("expectation","exact")
    ok = ds==es if mode=="exact" else es.issubset(ds) if mode=="contains" else not detected if mode=="clean" else False
    return ok, {"id":case.get("id"),"phase":case.get("phase"),"expectation":mode,
                "expected_detected":expected,"detected":detected,"pass":ok}

def replay(path: Path)->int:
    payload=json.loads(path.read_text(encoding="utf-8")); results=[]; failed=0
    for c in payload.get("cases",[]):
        ok,res=run_case(c); results.append(res); failed += (0 if ok else 1)
    print(json.dumps({"fixture_version":payload.get("fixture_version"),"case_count":len(results),
                      "passed":len(results)-failed,"failed":failed,"results":results}, ensure_ascii=False,indent=2))
    return 1 if failed else 0

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--replay",type=Path); p.add_argument("--record",type=Path); a=p.parse_args()
    if bool(a.replay)==bool(a.record): p.error("Provide exactly one of --replay or --record")
    if a.replay: return replay(a.replay)
    rec=json.loads(a.record.read_text(encoding="utf-8")); failures=validate_record(rec)
    print(json.dumps({"detected":failures,"pass":not failures},ensure_ascii=False,indent=2)); return 1 if failures else 0
if __name__=="__main__": sys.exit(main())
