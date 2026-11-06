#!/usr/bin/env python3
"""Read-only outcome observers used by the existing TAKY local executor.

Never edit product or task authority, call a model, or promote work to DONE.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(r"D:\Git PWA")


def _reader():
    workbench = ROOT / "TAKY_AI_WORKBENCH" / "00_CONTROL"
    validator = workbench / "RECONCILE_EXECUTION_REALITY.py"
    spec = importlib.util.spec_from_file_location("taky_readonly_outcome_reader", validator)
    if spec is None or spec.loader is None:
        raise RuntimeError("CANONICAL_OUTCOME_READER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observed_product_outcome(_: int = 75) -> list[dict]:
    module = _reader()
    proof = ROOT / "TAKY_AI_WORKBENCH" / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE" / "PRODUCT_AND_SOURCE_OUTCOME_LOCAL_20261023.json"
    state = module.inspect_local_outcome_receipt(proof)
    verified = (
        state.get("productLaneState") == "LOCAL_BROWSER_AND_CENTRAL_EVIDENCED_NOT_USER_DONE"
        and state.get("productTaskStates") == ["COMPLETED", "COMPLETED", "PARTIAL"]
        and state.get("centralLocalBackendUnapprovedEvidencePersisted") == 0
        and state.get("centralDurableRestartGuardVerified") is True
        and state.get("userOutcomeVerified") is False
    )
    return [{
        "name": "FAMILY_DURABLE_LOCAL_BROWSER_AND_CENTRAL_EVIDENCE",
        "status": "PASS" if verified else "HOLD",
        "observed_state": state.get("productLaneState", state.get("state")),
        "observed_tasks": state.get("productTaskStates"),
        "unapproved_sound_learning_evidence": state.get("centralLocalBackendUnapprovedEvidencePersisted"),
        "app_to_parent_partial_receipt_verified": bool(verified),
        "real_device_verified": False,
        "live_external_google_auth_verified": False,
        "full_learning_complete": False,
        "next_action": "APPROVE_REAL_AUDIO_AND_VERIFY_PHYSICAL_DEVICE_THEN_INDEPENDENT_PRODUCT_ACCEPTANCE",
        "no_app_changes": True, "no_model_calls": True,
        "done_claim": "READ_ONLY_LOCAL_E2E_EVIDENCE_NOT_USER_ACCEPTANCE",
    }]


def original_source_adoption_evidence(_: int = 75) -> list[dict]:
    module = _reader()
    proof = ROOT / "TAKY_AI_WORKBENCH" / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE" / "PRODUCT_AND_SOURCE_OUTCOME_LOCAL_20261023.json"
    try:
        receipt = json.loads(proof.read_text(encoding="utf-8-sig"))
        ref = receipt["source_index_owner"]["frozen_quote_unit_ref"]
        result = module.verify_frozen_source_quote_units(ref)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [{
            "name": "ORIGINAL_SOURCE_TO_CONSUMER_EVIDENCE",
            "status": "HOLD",
            "reason": "FROZEN_ORIGINAL_EVIDENCE_NOT_REPRODUCIBLE",
            "error_type": type(exc).__name__,
            "cross_model_review_verified": False, "learning_consumed": False,
            "no_model_calls": True, "done_claim": "NO_OWNER_APPROVAL_OR_ADOPTION",
        }]
    valid = result.get("quoteUnitsVerified") == 10 and result.get("originalSourcesVerified") == 6
    checks = [{
        "name": "ORIGINAL_SOURCE_TO_CONSUMER_EVIDENCE",
        "status": "PASS" if valid else "HOLD",
        "quote_units_verified": result.get("quoteUnitsVerified"),
        "original_sources_verified": result.get("originalSourcesVerified"),
        "original_source_receipt_sha256": result.get("frozenReceiptSHA256"),
        "cross_model_review_verified": False,
        "index_owner_approved": False,
        "learning_consumed": False,
        "next_action": "FROZEN_GPT_AND_CLAUDE_INDEPENDENT_ORIGINAL_ANALYSES_THEN_CROSS_REVIEW_AND_CODEX_SYNTHESIS",
        "no_model_calls": True, "no_source_adoption": True,
        "done_claim": "SOURCE_INTEGRITY_ONLY_NOT_INDEPENDENT_ADOPTION",
    }]
    # Join the ACTUAL existing 75-source Index Owner queue to the orchestrator.
    # Verify the signed Codex receipt again rather than trusting a copied label
    # from an unsigned JSON queue. Never grant Index Owner or consumer status.
    import sys
    source_root = ROOT / "TAKY-SOURCE-VAULT"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    try:
        import BUILD_SITE_INDEX_OWNER_EVIDENCE_BUNDLE as source_owner
        current = source_owner.read(source_owner.OUT)
        jobs = source_owner.read_current_queue()
        observed, held = source_owner.frozen_source_review_witnesses(jobs)
        source_id = "SITE_WATCH:2e081987263ff2f5d200da75"
        row = next((x for x in current.get("items", [])
                    if x.get("source_id") == source_id), None)
        proof = observed.get(source_id)
        ok = (
            current.get("source_count") == len(jobs.get("items", []))
            and current.get("indexing_owner_approved") == 0
            and current.get("forming_approved") == 0
            and current.get("learning_consumed") == 0
            and current.get("frozen_independent_model_observations") == 1
            and not current.get("frozen_independent_model_observation_holds")
            and len(observed) == 1 and not held
            and isinstance(row, dict) and row.get("raw_sha256") == proof.get("raw_sha256")
            and row.get("frozen_independent_source_observation") == proof
            and proof.get("cross_provider_review_complete") is False
            and proof.get("learning_consumed") is False
        )
    except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError, AttributeError):
        ok = False
        current, observed = {}, {}
    checks.append({
        "name": "SIGNED_SOURCE_REVIEW_REACHED_EXISTING_INDEX_OWNER_QUEUE",
        "status": "PASS" if ok else "HOLD",
        "owner_queue_candidates": current.get("source_count"),
        "source_first_signed_review_candidates": 1 if ok else 0,
        "cross_provider_review_complete": False,
        "index_owner_approved": False,
        "forming_approved": False,
        "learning_consumed": False,
        "next_action": "OBTAIN_INDEPENDENT_CLAUDE_SOURCE_REVIEW_ON_AVAILABLE_APPROVED_ROUTE_BEFORE_OWNER_ADOPTION",
        "no_model_calls": True, "done_claim": "OWNER_QUEUE_CONSUMED_SIGNED_REVIEW_NOT_OWNER_APPROVED",
    })
    return checks


def canonical_current_precheck(_: int = 75) -> list[dict]:
    """CLN-002: inspect existing project authority, no registry or CURRENT rewrite."""
    wb = ROOT / "TAKY_AI_WORKBENCH"
    registry = json.loads((wb/"00_CONTROL/PROJECT_REGISTRY.json").read_text(encoding="utf-8-sig"))
    backlog = json.loads((wb/"01_BACKLOG_AND_ADOPTION/70_EXECUTION_QUEUE/TASK_REGISTER.json").read_text(encoding="utf-8-sig"))
    tasks = {x["id"] for x in backlog["tasks"]}
    seen = set()
    gaps = []
    for key, config in registry["projects"].items():
        current_path = wb / config["workbench_path"] / "PROJECT_CURRENT.json"
        if not current_path.is_file():
            gaps.append({"project":key,"reason":"PROJECT_CURRENT_MISSING"})
            continue
        current = json.loads(current_path.read_text(encoding="utf-8-sig"))
        wid = current.get("current_work_id")
        if key in seen or current.get("project") != key:
            gaps.append({"project":key,"reason":"DUPLICATE_OR_WRONG_CURRENT"})
        if config.get("status") != current.get("status"):
            gaps.append({"project":key,"reason":"REGISTRY_CURRENT_STATUS_MISMATCH"})
        if wid and wid not in tasks:
            gaps.append({"project":key,"reason":"WORK_ID_NOT_REGISTERED"})
        seen.add(key)
    return [{
        "name":"CLN002_EXACT_CURRENT_PROJECT_OWNERSHIP",
        "status":"PASS" if len(seen)==9 and not gaps else "HOLD",
        "checked_projects":len(seen),"declared_project_count":len(registry["projects"]),
        "gaps":gaps[:18],"no_automatic_owner_change":True,
        "current_files_modified":False,"work_ids_created":0,
        "acceptance_scope":"CURRENT_REGISTRY_EXACT_CONSISTENCY_ONLY_NOT_GIT_CHANGE_CUSTODY",
        "independent_review_verified":False,
        "next_action":"TRACE_UNOWNED_GIT_WORKTREE_PATHS_WITH_EXACT_WORK_ID_EVIDENCE",
    }]


def existing_signed_handoff_precheck(_: int = 75) -> list[dict]:
    """INT-001: derive from signed existing routes, not model-return guesses."""
    wb = ROOT / "TAKY_AI_WORKBENCH"
    reader = _reader()
    board = json.loads((wb/"01_BACKLOG_AND_ADOPTION/70_EXECUTION_QUEUE/TASK_REGISTER.json").read_text(encoding="utf-8-sig"))
    assignments = json.loads((wb/"00_CONTROL/AI_WORK_ASSIGNMENTS.json").read_text(encoding="utf-8-sig"))
    signed = reader.inspect_exact_signed_model_handoffs(board, assignments, reader.default_cfg())
    ok = (signed.get("state")=="EXACT_SIGNED_HANDOFFS_RECONCILED_NOT_COMPLETION"
          and signed.get("model_jobs")==signed.get("linked",0)+signed.get("unbound",0)
          and signed.get("independent_done")==0
          and signed.get("model_calls_by_observer")==0)
    # Legacy jobs without an explicit portfolio WORK_ID are quarantined, not
    # permanently fatal to the transport readback. A successful check proves
    # only that the register partitions linked/unbound jobs consistently.
    # It neither assigns anonymous reviews nor approves any result as DONE.
    unbound=signed.get("unbound")
    reviewer_gaps=signed.get("reviewers_unassigned")
    history_held=bool(unbound or reviewer_gaps)
    return [{
        "name":"INT001_SIGNED_PORTFOLIO_WORK_ID_HANDOFF",
        "status":"PASS" if ok else "HOLD",
        "transport_valid":ok,
        "model_jobs":signed.get("model_jobs"),
        "portfolio_linked":signed.get("linked"),
        "historical_unbound":unbound,
        "historical_provenance_state":(
            "QUARANTINED_NO_AUTO_ASSIGNMENT" if history_held
            else "ALL_RECORDED_TASK_OWNERS_KNOWN"),
        "historical_provenance_verified":not history_held,
        "signed_cli_returned_without_content_completion":signed.get("signed_cli_transport_only"),
        "unassigned_reviewers":reviewer_gaps,
        "independent_completion":0,
        "historical_jobs_auto_assigned":0,
        "model_calls":0,
        "next_action":"VERIFY_NEW_REGISTERED_SOURCE_BOUND_EXECUTION_OUTCOME;LEGACY_UNBOUND_REMAINS_QUARANTINED",
        "done_claim":"INT001_SIGNED_TRANSPORT_RECONCILED_ONLY_NOT_SEMANTIC_OR_PORTFOLIO_DONE",
    }]



OUTCOME_READONLY_WORKERS = {
    "FAMILY-DURABLE-001": observed_product_outcome,
    "OPS-001": original_source_adoption_evidence,
    "CLN-002": canonical_current_precheck,
    "INT-001": existing_signed_handoff_precheck,
}
