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
    "ROLE_OWNER_VIOLATION","KNOWN_CONTEXT_EVIDENCE_MISSING","HISTORY_EVIDENCE_MISSING",
    "VALIDATION_AS_PRODUCT_PROGRESS","ROLE_MISSING","ACTION_CLASS_MISSING","EXECUTION_OWNER_MISSING",
    "UNKNOWN_ROLE","UNKNOWN_ACTION_CLASS","ROLE_ACTION_NOT_ALLOWED",
}

VALID_ROLES = {"ORCHESTRATOR","IMPLEMENTER","VALIDATOR","HUMAN_APPROVER"}
VALID_ACTION_CLASSES = {
    "ORCHESTRATE","ROUTE","SPECIFY_ACCEPTANCE","INSPECT","VALIDATION_ONLY","CROSS_VALIDATE",
    "HANDOFF","REWORK_REQUEST","GOVERNANCE_WRITE","IMPLEMENTATION_WRITE","IMPLEMENTATION_EXECUTE",
    "HUMAN_APPROVAL","STATUS_REPORT"
}
ORCHESTRATOR_ALLOWED_ACTIONS = {
    "ORCHESTRATE","ROUTE","SPECIFY_ACCEPTANCE","INSPECT","VALIDATION_ONLY","CROSS_VALIDATE",
    "HANDOFF","REWORK_REQUEST","GOVERNANCE_WRITE","STATUS_REPORT"
}
IMPLEMENTER_ALLOWED_ACTIONS = {"IMPLEMENTATION_WRITE","IMPLEMENTATION_EXECUTE","STATUS_REPORT"}
VALIDATOR_ALLOWED_ACTIONS = {"VALIDATION_ONLY","INSPECT","CROSS_VALIDATE","STATUS_REPORT"}
HUMAN_APPROVER_ALLOWED_ACTIONS = {"HUMAN_APPROVAL","STATUS_REPORT"}
ROLE_ACTION_ALLOWLIST = {
    "ORCHESTRATOR": ORCHESTRATOR_ALLOWED_ACTIONS,
    "IMPLEMENTER": IMPLEMENTER_ALLOWED_ACTIONS,
    "VALIDATOR": VALIDATOR_ALLOWED_ACTIONS,
    "HUMAN_APPROVER": HUMAN_APPROVER_ALLOWED_ACTIONS,
}

def b(r: Dict[str, Any], k: str, d: bool=False)->bool: return bool(r.get(k,d))
def i(r: Dict[str, Any], k: str, d: int=0)->int:
    try: return int(r.get(k,d))
    except (TypeError, ValueError): return d
def sl(r: Dict[str, Any], k: str)->List[str]:
    v=r.get(k,[])
    return [str(x) for x in v] if isinstance(v,list) else []

def has_refs(r: Dict[str, Any], k: str)->bool:
    v = r.get(k, [])
    if not isinstance(v, list): return False
    return any(x for x in v)

def validate_record(r: Dict[str, Any]) -> List[str]:
    f: List[str]=[]
    for key, token in [
        ("intent_drift","INTENT_DRIFT"),("scope_shrunk_without_authority","SCOPE_SHRINKAGE"),
        ("substitute_result","SUBSTITUTE_RESULT"),("output_form_mismatch","OUTPUT_FORM_MISMATCH"),
        ("material_omission","OMISSION"),("stale_state_used","STALE_STATE"),
        ("unclassified_conflict","UNCLASSIFIED_CONFLICT")]:
        if b(r,key): f.append(token)

    # Universal TAKY basis auto-activation for material TAKY-governed turns.
    # Material TAKY work must enter pre-execution without relying on the user
    # to repeat "TAKY 기준" every time.
    if b(r,"material_taky_turn") and not b(r,"pre_execution_gate_required"):
        f.append("RULE_NOT_APPLIED")

    # Evidence-backed pre-execution activation. Unknown/missing role/action fails closed.
    if b(r,"pre_execution_gate_required"):
        if not has_refs(r,"applicable_rule_refs"):
            f.append("KNOWN_CONTEXT_EVIDENCE_MISSING")
        if not has_refs(r,"context_evidence_refs"):
            f.append("KNOWN_CONTEXT_EVIDENCE_MISSING")
        if not has_refs(r,"history_query_refs"):
            f.append("HISTORY_EVIDENCE_MISSING")
        if b(r,"resumed_or_context_compacted") and not has_refs(r,"preflight_rehydration_evidence_refs"):
            f.append("HISTORY_EVIDENCE_MISSING")

        role=str(r.get("role","")).strip().upper()
        owner=str(r.get("execution_owner","")).strip().upper()
        action=str(r.get("action_class","")).strip().upper()

        if not role:
            f.append("ROLE_MISSING")
        elif role not in VALID_ROLES:
            f.append("UNKNOWN_ROLE")

        if not action:
            f.append("ACTION_CLASS_MISSING")
        elif action not in VALID_ACTION_CLASSES:
            f.append("UNKNOWN_ACTION_CLASS")

        if not owner:
            f.append("EXECUTION_OWNER_MISSING")

        if role in ROLE_ACTION_ALLOWLIST and action in VALID_ACTION_CLASSES:
            if action not in ROLE_ACTION_ALLOWLIST[role]:
                f.append("ROLE_ACTION_NOT_ALLOWED")

        if role == "ORCHESTRATOR" and action in {"IMPLEMENTATION_WRITE","IMPLEMENTATION_EXECUTE"}:
            f.append("ROLE_OWNER_VIOLATION")

        if action == "VALIDATION_ONLY" and b(r,"claims_product_progress_advance"):
            f.append("VALIDATION_AS_PRODUCT_PROGRESS")

        # Rule retrieval is not enough. Material preflight must compile rules into an
        # operational working model that can drive execution.
        wm = r.get("working_model")
        if not isinstance(wm, dict):
            f.append("RULE_NOT_APPLIED")
        else:
            primary = str(wm.get("primary_outcome","")).strip()
            next_action = str(wm.get("next_action","")).strip()
            priorities = wm.get("priority_order", [])
            implications = wm.get("execution_implications", [])
            mappings = wm.get("rule_to_execution", [])
            if not primary or not next_action:
                f.append("RULE_NOT_APPLIED")
            if not isinstance(priorities, list) or not any(str(x).strip() for x in priorities):
                f.append("RULE_NOT_APPLIED")
            if not isinstance(implications, list) or not any(str(x).strip() for x in implications):
                f.append("RULE_NOT_APPLIED")
            if not isinstance(mappings, list):
                f.append("RULE_NOT_APPLIED")
            else:
                usable = []
                for m in mappings:
                    if not isinstance(m, dict):
                        continue
                    ref = str(m.get("rule_ref","")).strip()
                    effect = str(m.get("effect","")).strip().upper()
                    implication = str(m.get("implication","")).strip()
                    if ref and effect in {"ACTION","CONSTRAINT","ACCEPTANCE","HOLD","NOT_APPLICABLE"} and implication:
                        usable.append(ref)
                applicable = r.get("applicable_rule_refs", [])
                if len(set(usable)) < len(applicable):
                    f.append("RULE_NOT_APPLIED")
            if b(wm,"read_only_summary"):
                f.append("RULE_NOT_APPLIED")

    if b(r,"claims_runtime_enforced") and not b(r,"live_runtime_auto_invocation_verified"):
        f.append("STATE_CLAIM_MISMATCH")


    # Generic pre-action rule-application gate.
    # A material action is not allowed to rely on "rule loaded" alone. The action must
    # carry explicit rule bindings and all required preconditions must be satisfied.
    if b(r,"material_action_planned"):
        action_id=str(r.get("action_id","")).strip()
        refs=sl(r,"action_rule_refs")
        bindings=r.get("action_rule_bindings",[])
        preconditions=r.get("action_preconditions",[])
        if not action_id:
            f.append("RULE_NOT_APPLIED")
        if not refs:
            f.append("KNOWN_CONTEXT_EVIDENCE_MISSING")
        usable=set()
        if isinstance(bindings,list):
            for item in bindings:
                if not isinstance(item,dict):
                    continue
                ref=str(item.get("rule_ref","")).strip()
                effect=str(item.get("effect","")).strip().upper()
                implication=str(item.get("implication","")).strip()
                if ref and effect in {"ACTION","CONSTRAINT","ACCEPTANCE","HOLD","NOT_APPLICABLE"} and implication:
                    usable.add(ref)
        if len(usable) < len(set(refs)):
            f.append("RULE_NOT_APPLIED")
        if not isinstance(preconditions,list) or not preconditions:
            f.append("RULE_NOT_APPLIED")
        else:
            for p in preconditions:
                if not isinstance(p,dict):
                    f.append("RULE_NOT_APPLIED")
                    continue
                if bool(p.get("required",True)) and not bool(p.get("satisfied",False)):
                    f.append("RULE_NOT_APPLIED")
        if b(r,"action_conflicts_with_rule"):
            f.append("RULE_NOT_APPLIED")
        if b(r,"lower_impact_compliant_path_available") and b(r,"higher_cost_side_effect_selected") and not b(r,"explicit_override_approved"):
            f.append("RULE_NOT_APPLIED")

    # External-resource call budget / duplicate-call gate.
    # Prevents hosted validation/deploy/status APIs from being used as a substitute for
    # branch/local/CI closure and blocks repeated external calls without new evidence.
    if b(r,"external_resource_action"):
        budget=max(1,i(r,"external_call_budget",1))
        used=i(r,"external_call_count_for_same_goal")
        if used > budget and not b(r,"explicit_override_approved"):
            f.append("RULE_NOT_APPLIED")
        if b(r,"same_external_call_repeated_without_new_evidence"):
            f.append("RULE_NOT_APPLIED")
        if b(r,"deployment_attempted_before_candidate_frozen"):
            f.append("RULE_NOT_APPLIED")
        if (b(r,"lower_cost_local_validation_available")
            and b(r,"external_call_selected_before_local_closure")
            and not b(r,"explicit_override_approved")):
            f.append("RULE_NOT_APPLIED")
        if (b(r,"external_status_poll")
            and b(r,"no_new_trigger_since_last_external_check")
            and not b(r,"material_external_state_change_expected")):
            f.append("RULE_NOT_APPLIED")

    if (b(r,"delegated_continuation") and b(r,"authorized_next_action_available")
        and not b(r,"real_blocker_present") and not b(r,"human_confirmation_required_now")
        and b(r,"stopped_before_blocker")):
        f.append("PREMATURE_STOP")

    if (b(r,"artifact_or_action_required") and b(r,"authorized_action_available")
        and not b(r,"artifact_or_action_delivered") and b(r,"explanation_only")):
        f += ["SUBSTITUTE_RESULT","OUTPUT_FORM_MISMATCH"]

    # Notion link-intelligence review: source acquisition must precede analysis/compare/improve.
    if b(r,"notion_link_review_required"):
        root_required=b(r,"notion_root_source_applicable",True)
        root_attempted=b(r,"notion_root_source_attempted")
        descendants_inventoried=b(r,"notion_material_descendants_inventoried")
        discovered=i(r,"notion_material_source_nodes_discovered")
        dispositioned=i(r,"notion_material_source_nodes_dispositioned")
        graph_closed=b(r,"notion_source_graph_closed")
        fallback_required = (
            b(r,"notion_root_direct_fetch_failed")
            and b(r,"notion_recoverable_snapshot_available")
        )
        fallback_used = b(r,"notion_recoverable_snapshot_used")

        if fallback_required and not fallback_used:
            f += ["RECOVERY_FAILED","OMISSION"]
            if b(r,"notion_source_declared_unreadable"):
                f.append("FALSE_MISSING_DECLARATION")

        if b(r,"notion_browser_runtime_stall"):
            attempts=i(r,"notion_browser_retry_attempts")
            if attempts > i(r,"notion_browser_retry_budget",2):
                f += ["RECOVERY_FAILED","PREMATURE_STOP"]
            if not b(r,"notion_browser_fallback_selected"):
                f += ["RECOVERY_FAILED","OMISSION"]
            if b(r,"notion_unrelated_sibling_nodes_stalled"):
                f.append("SCOPE_SHRINKAGE")

        phase_a_missing = (
            (root_required and not root_attempted)
            or not descendants_inventoried
            or discovered != dispositioned
            or not graph_closed
            or not b(r,"notion_structured_source_evidence_present")
        )
        phase_b_missing = (
            not b(r,"notion_analysis_completed")
            or not b(r,"notion_compare_completed")
            or not b(r,"notion_improvement_assessment_completed")
            or not b(r,"notion_review_record_updated")
        )

        if phase_a_missing:
            f.append("OMISSION")
        if phase_b_missing or b(r,"notion_database_housekeeping_only"):
            f.append("SUBSTITUTE_RESULT")

    # Notion Work launch preflight: do not use the user as the runtime tester.
    if b(r,"notion_work_launch_preflight_required"):
        stable_reads = i(r,"notion_inventory_stability_reads")
        inventory_stable = b(r,"notion_inventory_stable")
        structured_complete = b(r,"notion_preflight_structured_state_complete")
        fallback_verified = b(r,"notion_preflight_fallback_archives_verified")
        priority_consistent = b(r,"notion_preflight_priority_state_consistent")
        if stable_reads < 2 or not inventory_stable:
            f += ["STALE_STATE","OMISSION"]
        if not structured_complete or not fallback_verified or not priority_consistent:
            f.append("OMISSION")
        if b(r,"notion_user_used_as_smoke_tester"):
            f += ["USER_AS_QA","USER_FORCED_RECOVERY"]

    # Architecture-profile auto-activation.
    # A material architecture/shared-core/OS-boundary change must not bypass
    # TKY-ENGEXEC-001 merely because the caller forgot to set the profile-required flag.
    architecture_change = (
        b(r,"architecture_change_planned")
        or b(r,"shared_core_change_planned")
        or b(r,"os_boundary_change_planned")
        or b(r,"cross_domain_architecture_change_planned")
        or b(r,"ownership_move_planned")
    )
    if architecture_change:
        if not b(r,"engineering_execution_profile_required"):
            f.append("RULE_NOT_APPLIED")
        if str(r.get("engineering_profile","")).strip().upper() != "ARCHITECTURE_CHANGE":
            f.append("RULE_NOT_APPLIED")

    # Engineering execution profiles: reusable task-specific contracts.
    if b(r,"engineering_execution_profile_required"):
        profile=str(r.get("engineering_profile","")).strip().upper()
        allowed={"REPAIR","ARCHITECTURE_CHANGE","DATABASE_MIGRATION","SECURITY_REVIEW","UI_IMPLEMENTATION"}
        ec=r.get("engineering_contract")
        if profile not in allowed or not isinstance(ec,dict):
            f.append("RULE_NOT_APPLIED")
        else:
            common_lists=["baseline_evidence_refs","protected_state","acceptance_conditions","validation_steps","regression_scope"]
            for key in common_lists:
                val=ec.get(key)
                if not isinstance(val,list) or not any(str(x).strip() for x in val):
                    f.append("RULE_NOT_APPLIED")
            if not str(ec.get("target_delta","")).strip():
                f.append("RULE_NOT_APPLIED")
            if not str(ec.get("report_mode","")).strip():
                f.append("RULE_NOT_APPLIED")
            if "remaining_unknowns" not in ec or not isinstance(ec.get("remaining_unknowns"), list):
                f.append("RULE_NOT_APPLIED")
            if b(ec,"concise_user_output") and b(ec,"internal_validation_reduced_for_concise_output"):
                f.append("RULE_NOT_APPLIED")
            if b(ec,"material_failed_or_unknown_gate_hidden"):
                f.append("STATE_CLAIM_MISMATCH")

            if profile=="REPAIR":
                if not has_refs(ec,"failure_evidence_refs"):
                    f.append("RULE_NOT_APPLIED")
                for key in ["root_cause","minimal_delta_defined","targeted_retest_defined","regression_check_defined"]:
                    val=ec.get(key)
                    if (key=="root_cause" and not str(val or "").strip()) or (key!="root_cause" and val is not True):
                        f.append("RULE_NOT_APPLIED")
                if b(ec,"same_failed_approach_repeated_without_new_evidence"):
                    f.append("RULE_NOT_APPLIED")

            elif profile=="ARCHITECTURE_CHANGE":
                if not has_refs(ec,"existing_pattern_refs"):
                    f.append("RULE_NOT_APPLIED")
                for key in ["owner_boundary_checked","interface_contract_checked","minimum_sufficient_complexity","integration_check_defined",
                            "semantic_boundary_checked","authority_boundary_checked"]:
                    if ec.get(key) is not True:
                        f.append("RULE_NOT_APPLIED")

                owner_map=ec.get("owner_map")
                if not isinstance(owner_map,list) or not owner_map:
                    f.append("RULE_NOT_APPLIED")
                else:
                    for item in owner_map:
                        if not isinstance(item,dict):
                            f.append("RULE_NOT_APPLIED"); continue
                        if not str(item.get("scope","")).strip() or not str(item.get("owner","")).strip():
                            f.append("RULE_NOT_APPLIED")

                sharing=ec.get("sharing_classification")
                allowed_sharing={"SHARED_TECHNICAL_PRIMITIVE","DOMAIN_OWNED_SEMANTIC","EXPLICIT_FEDERATION","NOT_SHARED"}
                if not isinstance(sharing,list) or not sharing:
                    f.append("RULE_NOT_APPLIED")
                else:
                    for item in sharing:
                        if not isinstance(item,dict):
                            f.append("RULE_NOT_APPLIED"); continue
                        cls=str(item.get("class","")).strip().upper()
                        if not str(item.get("item","")).strip() or cls not in allowed_sharing:
                            f.append("RULE_NOT_APPLIED")
                        if cls in {"DOMAIN_OWNED_SEMANTIC","EXPLICIT_FEDERATION","NOT_SHARED"} and not str(item.get("owner","")).strip():
                            f.append("RULE_NOT_APPLIED")

                counterexamples=ec.get("boundary_counterexamples")
                if not isinstance(counterexamples,list) or not counterexamples:
                    f.append("RULE_NOT_APPLIED")
                else:
                    usable_counterexample=False
                    for item in counterexamples:
                        if not isinstance(item,dict):
                            continue
                        if str(item.get("scenario","")).strip() and str(item.get("expected_boundary","")).strip():
                            usable_counterexample=True
                    if not usable_counterexample:
                        f.append("RULE_NOT_APPLIED")

                if b(ec,"shared_layer_proposed") and ec.get("shared_layer_semantic_light") is not True:
                    f.append("RULE_NOT_APPLIED")
                if b(ec,"cross_domain_authority_shared_by_default"):
                    f.append("AUTHORITY_BOUNDARY_VIOLATION")
                if b(ec,"shared_semantic_or_authority_without_explicit_federation"):
                    f.append("AUTHORITY_BOUNDARY_VIOLATION")
                if b(ec,"forced_fragmentation_without_benefit"):
                    f.append("RULE_NOT_APPLIED")

            elif profile=="DATABASE_MIGRATION":
                for key in ["migration_artifact_defined","backward_compatibility_checked","referential_action_justified",
                            "rls_or_access_control_checked","index_lock_impact_checked","rollback_or_forward_fix_defined",
                            "migration_test_defined","post_migration_verify_defined"]:
                    if ec.get(key) is not True:
                        f.append("RULE_NOT_APPLIED")
                if b(ec,"unconditional_cascade_without_lifecycle_justification"):
                    f.append("RULE_NOT_APPLIED")

            elif profile=="SECURITY_REVIEW":
                for key in ["attack_surface_defined","severity_prioritized","security_regression_defined"]:
                    if ec.get(key) is not True:
                        f.append("RULE_NOT_APPLIED")
                if not has_refs(ec,"applicable_controls_refs"):
                    f.append("RULE_NOT_APPLIED")
                findings=ec.get("evidence_based_findings")
                if not isinstance(findings,list):
                    f.append("RULE_NOT_APPLIED")
                if b(ec,"arbitrary_finding_quota"):
                    f.append("RULE_NOT_APPLIED")
                if b(ec,"claims_security_complete") and not b(ec,"complete_security_scope_evidenced"):
                    f.append("STATE_CLAIM_MISMATCH")

            elif profile=="UI_IMPLEMENTATION":
                for key in ["project_reference_checked","responsive_states_defined","accessibility_check_defined"]:
                    if ec.get(key) is not True:
                        f.append("RULE_NOT_APPLIED")
                if not str(ec.get("design_contract_ref","")).strip():
                    f.append("RULE_NOT_APPLIED")
                if b(ec,"external_style_as_project_authority"):
                    f.append("AUTHORITY_BOUNDARY_VIOLATION")

    # Product implementation integrity: prevent validation/test/documentation success
    # from inflating interactive-product completion claims.
    if b(r,"product_integrity_gate_required"):
        matrix=r.get("product_completion_matrix")
        if not isinstance(matrix,list) or not matrix:
            f.append("RULE_NOT_APPLIED")
        else:
            valid_status={"NOT_STARTED","SKELETON","PARTIAL","FUNCTIONAL","RUNTIME_VERIFIED","DEVICE_VERIFIED"}
            for row in matrix:
                if not isinstance(row,dict):
                    f.append("RULE_NOT_APPLIED"); continue
                if not str(row.get("feature","")).strip():
                    f.append("RULE_NOT_APPLIED")
                if str(row.get("status","")).strip().upper() not in valid_status:
                    f.append("RULE_NOT_APPLIED")
                if not str(row.get("evidence_ref","")).strip():
                    f.append("KNOWN_CONTEXT_EVIDENCE_MISSING")
                if "user_path_reachable" not in row:
                    f.append("RULE_NOT_APPLIED")
                if "known_gaps" not in row or not isinstance(row.get("known_gaps"),list):
                    f.append("RULE_NOT_APPLIED")

        claim_levels=r.get("product_claim_levels")
        required_levels=["CODED","CI_VERIFIED","RUNTIME_VERIFIED","DEVICE_VERIFIED"]
        if not isinstance(claim_levels,dict):
            f.append("RULE_NOT_APPLIED")
        else:
            for key in required_levels:
                if key not in claim_levels:
                    f.append("RULE_NOT_APPLIED")

        structural=str(r.get("structural_integrity_status","")).strip().upper()
        if structural not in {"PASS","REVIEW_REQUIRED","FAIL","REWRITE_REQUIRED"}:
            f.append("RULE_NOT_APPLIED")

        if b(r,"representative_input_material") and not str(r.get("representative_input_status","")).strip():
            f.append("RULE_NOT_APPLIED")
        if b(r,"cross_app_or_service_integration_material") and not str(r.get("integration_freshness_status","")).strip():
            f.append("RULE_NOT_APPLIED")

        if b(r,"docs_tests_or_fixtures_directly_increased_product_completion"):
            f.append("STATE_CLAIM_MISMATCH")
        if b(r,"fixture_only_evidence_claimed_as_real_input_complete"):
            f.append("STATE_CLAIM_MISMATCH")
        if b(r,"stale_integration_path_counted_as_current"):
            f.append("STATE_CLAIM_MISMATCH")

        if structural in {"FAIL","REWRITE_REQUIRED"}:
            disposition=str(r.get("architecture_disposition","")).strip().upper()
            if disposition not in {"REPAIR","REFACTOR","REWRITE","REBUILD"}:
                f.append("RULE_NOT_APPLIED")
            if disposition in {"REWRITE","REBUILD"}:
                for key in ["preserved_assets","migration_boundary","cutover_condition","rollback_or_reference_path","intentionally_not_migrated"]:
                    val=r.get(key)
                    if key in {"preserved_assets","intentionally_not_migrated"}:
                        if not isinstance(val,list):
                            f.append("RULE_NOT_APPLIED")
                    elif not str(val or "").strip():
                        f.append("RULE_NOT_APPLIED")
            if b(r,"feature_growth_claimed_complete_without_architecture_disposition"):
                f.append("PREMATURE_PASS")

        try:
            reported=float(r.get("reported_product_completion"))
            ceiling=float(r.get("evidence_product_completion_ceiling"))
            if reported > ceiling:
                f.append("STATE_CLAIM_MISMATCH")
                if b(r,"claims_product_complete"):
                    f.append("PREMATURE_PASS")
        except (TypeError,ValueError):
            if r.get("reported_product_completion") is not None or r.get("evidence_product_completion_ceiling") is not None:
                f.append("RULE_NOT_APPLIED")

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
