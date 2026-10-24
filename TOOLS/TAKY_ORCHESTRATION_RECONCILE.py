#!/usr/bin/env python3
"""Read-only reconciliation of TAKY work, model calls and outcome evidence.

Preparation is immutable history, never the current execution state.
No model, Git, filesystem mutation, inference or completion promotion.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

DEFAULT_BOARD = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\70_EXECUTION_QUEUE\TASK_REGISTER.json")
DEFAULT_ASSIGNMENTS = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL\AI_WORK_ASSIGNMENTS.json")
DEFAULT_HISTORY = Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY")

def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("EXPECTED_JSON_OBJECT:" + path.name)
    return data

def recovery_for(run_state: str | None, proposal_error: str | None) -> str:
    if run_state == "PROPOSAL_REJECTED":
        return "INSPECT_SIGNED_RESULT_REUSE_IF_VALID_NO_RETRY" if proposal_error else "INSPECT_PROPOSAL_REASON_NO_RETRY"
    if run_state in ("FAILED", "OUTCOME_UNKNOWN", "HOLD"):
        return "VERIFY_SIGNED_OUTCOME_BEFORE_ANY_NEW_CALL"
    if run_state == "APPLIED_UNVERIFIED":
        return "EXECUTE_TASK_SPECIFIC_REGRESSION_AND_INDEPENDENT_REVIEW"
    if run_state == "PROPOSAL_VALIDATED_NOT_APPLIED":
        return "CHECK_APPROVAL_AND_APPLY_VALIDATED_PROPOSAL"
    if run_state == "COMPLETE_UNVERIFIED":
        return "VERIFY_RESULT_NOT_TRANSPORT_ONLY"
    if run_state is None:
        return "PREPARED_ONLY_CONFIRM_NECESSITY_BEFORE_CALL"
    return "INSPECT_EXECUTION_RECEIPT_NO_ASSUMED_COMPLETION"


def inspect_scoped_edit_claims(runtime: dict) -> dict:
    """Observe signed local file-apply claims; NEVER finalize or retry.

    The claim is HMAC-authenticated by TAKY2 load_bundle before calling here,
    but files on the Windows filesystem remain independently mutable.
    """
    import hashlib
    from pathlib import PurePosixPath

    registry = runtime.get("scoped_edit_claims", {})
    if not isinstance(registry, dict):
        return {"state": "UNREADABLE_SIGNED_CLAIMS_HOLD", "items": []}
    observations = []
    for ref, claim in sorted(registry.items()):
        observation = {
            "receipt_id": ref,
            "state": "HOLD_UNRESOLVED",
            "recorded_apply_status": None,
            "files": [],
            "user_approval_verified": False,
            "automatic_recovery_permitted": False,
        }
        if not isinstance(claim, dict) or claim.get("receipt_id") != ref:
            observation["state"] = "INVALID_SIGNED_CLAIM_HOLD"
            observations.append(observation)
            continue
        observation["recorded_apply_status"] = claim.get("status")
        signed_receipt = runtime.get("preflight_receipts", {}).get(ref)
        execution_key = signed_receipt.get("execution_key") if isinstance(signed_receipt, dict) else None
        active = runtime.get("active_attempts", {}).get(execution_key)
        attempt = active.get("attempt") if isinstance(active, dict) else None
        root_string = attempt.get("target") if isinstance(attempt, dict) else None
        if not isinstance(root_string, str):
            observation["state"] = "SIGNED_TARGET_ROOT_UNAVAILABLE_HOLD"
            observations.append(observation)
            continue
        try:
            if not Path(root_string).is_absolute():
                raise ValueError("signed target not absolute")
            root = Path(root_string).resolve(strict=True)
            if not root.is_dir():
                raise ValueError("target root not directory")
        except (OSError, ValueError, RuntimeError):
            observation["state"] = "SIGNED_TARGET_ROOT_INVALID_HOLD"
            observations.append(observation)
            continue
        signed_files = claim.get("files")
        if not isinstance(signed_files, list) or not signed_files:
            observation["state"] = "SIGNED_FILE_MANIFEST_INVALID_HOLD"
            observations.append(observation)
            continue
        outcomes = []
        for item in signed_files:
            if (not isinstance(item, dict)
                    or not isinstance(item.get("path"), str)
                    or not item["path"] or "\\" in item["path"]
                    or PurePosixPath(item["path"]).is_absolute()
                    or any(x in {"", ".", ".."} for x in item["path"].split("/"))):
                outcomes.append("INVALID_PATH")
                continue
            try:
                candidate = root
                for component in item["path"].split("/"):
                    candidate = candidate / component
                    if candidate.is_symlink() or candidate.is_junction():
                        raise ValueError("reparse point")
                resolved = candidate.resolve(strict=True)
                if not resolved.is_relative_to(root) or not candidate.is_file():
                    raise ValueError("outside or missing")
                if candidate.stat().st_size > 1024 * 1024:
                    raise ValueError("oversized")
                observed = hashlib.sha256(candidate.read_bytes()).hexdigest()
            except (OSError, ValueError, RuntimeError):
                outcomes.append("MISSING_OR_UNSAFE")
                continue
            if observed == item.get("after_sha256"):
                outcomes.append("POSTIMAGE")
            elif observed == item.get("before_sha256"):
                outcomes.append("PREIMAGE")
            else:
                outcomes.append("DIVERGED")
        if outcomes and all(x == "POSTIMAGE" for x in outcomes):
            observation["state"] = (
                "RECORDED_APPLIED_UNVERIFIED"
                if claim.get("status") == "APPLIED_UNVERIFIED"
                else "PENDING_POSTIMAGE_OBSERVED_REVIEW_REQUIRED"
            )
        elif outcomes and all(x == "PREIMAGE" for x in outcomes):
            observation["state"] = (
                "PENDING_PREIMAGE_OBSERVED_REVIEW_REQUIRED"
                if claim.get("status") == "CLAIMED_PENDING_FILE_APPLY"
                else "APPLIED_RECORD_BUT_PREIMAGE_HOLD"
            )
        else:
            observation["state"] = "PARTIAL_OR_DIVERGENT_HOLD"
        observation["files"] = outcomes
        observations.append(observation)
    actions = {
        "RECORDED_APPLIED_UNVERIFIED":
            "RUN_TASK_ACCEPTANCE_AND_INDEPENDENT_REVIEW_NOT_USER_DONE",
        "PENDING_POSTIMAGE_OBSERVED_REVIEW_REQUIRED":
            "VERIFY_OUTPUT_AND_ATOMIC_CLAIM_BEFORE_MANUAL_FINALIZATION_NO_REAPPLY",
        "PENDING_PREIMAGE_OBSERVED_REVIEW_REQUIRED":
            "INSPECT_INTERRUPTION_AND_PLAN_NEW_AUTHORIZED_TASK_NO_RETRY",
        "APPLIED_RECORD_BUT_PREIMAGE_HOLD":
            "INVESTIGATE_DRIFT_OR_ROLLBACK_BEFORE_ANY_NEW_ACTION",
        "PARTIAL_OR_DIVERGENT_HOLD":
            "FORENSIC_CHECK_FILES_AND_RESTORE_ONLY_WITH_EXPLICIT_SCOPE",
        "SIGNED_TARGET_ROOT_UNAVAILABLE_HOLD":
            "REBIND_ORIGINAL_SIGNED_TARGET_READ_ONLY",
        "SIGNED_TARGET_ROOT_INVALID_HOLD":
            "REVIEW_SIGNED_TARGET_AND_FILESYSTEM_NO_WRITE",
        "SIGNED_FILE_MANIFEST_INVALID_HOLD":
            "REVIEW_SIGNED_CLAIM_INTEGRITY_NO_WRITE",
        "INVALID_SIGNED_CLAIM_HOLD":
            "REVIEW_SIGNED_LEDGER_INTEGRITY_NO_WRITE",
    }
    for item in observations:
        item["next_action"] = actions.get(item["state"], "MANUAL_INTEGRITY_REVIEW_HOLD")
    return {
        "state": "READ_ONLY",
        "total_claims": len(observations),
        "pending": sum(x["recorded_apply_status"] == "CLAIMED_PENDING_FILE_APPLY"
                       for x in observations),
        "needs_inspection": sum(
            x["state"] not in {"RECORDED_APPLIED_UNVERIFIED"} for x in observations),
        "items": observations,
        "model_calls": 0,
        "files_written": 0,
    }


def reconcile(board: dict, assignments: dict, history: Path, signed_readback=None) -> dict:
    if not isinstance(board.get("tasks"), list) or not isinstance(assignments.get("tasks"), list):
        raise ValueError("REGISTRY_LIST_SCHEMA_MISSING")
    portfolio = board["tasks"]
    jobs = assignments["tasks"]
    task_ids = [t.get("id") for t in portfolio]
    work_ids = [x.get("work_id") for x in jobs]
    if len(task_ids) != len(set(task_ids)) or len(work_ids) != len(set(work_ids)):
        raise ValueError("DUPLICATE_REGISTERED_WORK")
    board_ids = set(task_ids)
    observations = []
    for row in jobs:
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or len(task_id) != 32:
            raise ValueError("INVALID_ASSIGNMENT_TASK_ID")
        if row.get("work_id") != "TAKY-CHAT-" + task_id:
            raise ValueError("WORK_ID_TASK_MISMATCH")
        source = next((Path(str(x)) for x in row.get("input_refs", [])
                       if str(x).endswith(task_id + ".json")), None)
        preparation = None
        preparation_kind = None
        if source and source.is_file():
            doc = read_json(source)
            if doc.get("id") != task_id:
                raise ValueError("PREPARATION_TASK_ID_MISMATCH")
            if str(doc.get("portfolio_task_id") or "") != str(row.get("portfolio_task_id") or ""):
                raise ValueError("PREPARATION_PORTFOLIO_ID_MISMATCH")
            preparation = doc.get("state")
            preparation_kind = doc.get("task_kind")
        receipt = history / ("TAKY_ROUTED_" + task_id + ".json")
        run = read_json(receipt) if receipt.is_file() else None
        if run and run.get("task_id") != task_id:
            raise ValueError("EXECUTION_TASK_ID_MISMATCH")
        run_state = run.get("state") if run else None
        claimed = row.get("status", "UNKNOWN")
        derived = ("BLOCKED" if run_state in ("FAILED","OUTCOME_UNKNOWN","PROPOSAL_REJECTED","HOLD")
                   else "REVIEW" if run_state in ("COMPLETE_UNVERIFIED","APPLIED_UNVERIFIED","PROPOSAL_VALIDATED_NOT_APPLIED")
                   else "OPEN" if run_state is None else "UNCLASSIFIED")
        portfolio_id = row.get("portfolio_task_id") or None
        if portfolio_id is not None and portfolio_id not in board_ids:
            raise ValueError("PORTFOLIO_TASK_BINDING_LOST")
        # Bind a registered work item to the existing sealed TAKY2 call ledger.
        # This is a read-only transport witness, NEVER an implementation DONE.
        signed_state = "NOT_CHECKED_BY_THIS_RECONCILER"
        execution_evidence_bound = False
        if signed_readback is not None:
            try:
                witness = signed_readback(task_id)
                if isinstance(witness, dict) and isinstance(witness.get("state"), str):
                    signed_state = witness["state"]
                    execution_evidence_bound = (
                        signed_state == "CLI_RETURNED_UNVERIFIED"
                        and witness.get("executionEvidenceVerified") is True
                        and witness.get("executionVerificationState")
                            == "SIGNED_EXECUTION_EVIDENCED_NOT_USER_DONE"
                    )
                else:
                    signed_state = "SIGNED_READBACK_INVALID"
            except Exception:
                signed_state = "SIGNED_READBACK_FAILED"
        # A portfolio ID is not a source handoff. The implementation's
        # actual post-edit bytes must match the independent review manifest.
        # Both are historical receipts, not claims about today's worktree.
        changed = (run or {}).get("changed_files") or []
        post_edit_sources = {}
        if run_state == "APPLIED_UNVERIFIED" and preparation_kind == "implementation":
            for item in changed:
                if not isinstance(item, dict):
                    continue
                path, digest = item.get("path"), item.get("after_sha256")
                if (isinstance(path, str) and path and not path.startswith(("/", "\\\\"))
                        and ".." not in path.split("/")
                        and isinstance(digest, str) and len(digest) == 64
                        and all(ch in "0123456789abcdef" for ch in digest)):
                    post_edit_sources[path] = digest
        review_manifest = ((run or {}).get("review_source_binding") or {}).get("source_manifest") or []
        reviewed_sources = {}
        if run_state == "COMPLETE_UNVERIFIED" and preparation_kind == "review":
            for item in review_manifest:
                if not isinstance(item, dict):
                    continue
                path, digest = item.get("path"), item.get("sha256")
                included, total = item.get("includedLines"), item.get("totalLines")
                if (isinstance(path, str) and path and not path.startswith(("/", "\\\\"))
                        and ".." not in path.split("/")
                        and isinstance(digest, str) and len(digest) == 64
                        and all(ch in "0123456789abcdef" for ch in digest)
                        and type(included) is int and type(total) is int
                        and 0 < included <= total):
                    reviewed_sources[path] = {"sha256": digest,
                                              "includedLines": included,
                                              "totalLines": total}
        observations.append({
            "post_edit_sources": post_edit_sources,
            "reviewed_source_manifest": reviewed_sources,
            "work_id": row["work_id"], "executor": row.get("executor"),
            "portfolio_task_id": portfolio_id,
            "preparation_state": preparation, "task_kind": preparation_kind,
            "execution_state": run_state,
            "content_qa_state": run.get("content_qa_state") if run else None,
            "registry_state": claimed, "derived_state": derived,
            "registry_consistent": claimed == derived,
            "reviewer": row.get("reviewer", "UNASSIGNED"),
            "execution_verified": row.get("execution_verified") is True,
            "model_invocation_attempted": run.get("model_invocation_attempted") if run else False,
            "model_called_reported": run.get("model_called") if run else None,
            "signed_model_call_verification": signed_state,
            "signed_execution_evidenced": execution_evidence_bound,
            "evidence_count": len(row.get("evidence_refs", [])),
            "next_action": recovery_for(run_state, run.get("proposal_error") if run else None),
        })
    categories = Counter(str(t.get("category","UNKNOWN")) for t in portfolio)
    statuses = Counter(str(t.get("status","UNKNOWN")) for t in portfolio)
    # Join real model jobs by the portfolio ID, without assigning an unverified
    # reviewer or promoting a model response to independent completion.
    handoffs = []
    for portfolio_id in sorted({o["portfolio_task_id"] for o in observations if o["portfolio_task_id"]}):
        rows = [o for o in observations if o["portfolio_task_id"] == portfolio_id]
        implementers = [o for o in rows if o["task_kind"] == "implementation"]
        reviews = [o for o in rows if o["task_kind"] == "review"]
        independent = [o for o in reviews if any(o["executor"] != src["executor"] for src in implementers)]
        source_matches = []
        for implemented in implementers:
            for reviewed in independent:
                if reviewed["executor"] == implemented["executor"]:
                    continue
                for path, digest in implemented["post_edit_sources"].items():
                    source = reviewed["reviewed_source_manifest"].get(path)
                    if source and digest == source["sha256"]:
                        source_matches.append({
                            "implementation_work_id": implemented["work_id"],
                            "review_work_id": reviewed["work_id"],
                            "path": path,
                            "post_edit_sha256": digest,
                            "reviewed_lines": source["includedLines"],
                            "source_lines": source["totalLines"],
                            "review_completeness": (
                                "FULL_INPUT_LINES" if source["includedLines"] == source["totalLines"]
                                else "PARTIAL_INPUT_LINES"),
                            "content_qa_state": reviewed["content_qa_state"],
                            "does_not_prove_semantic_acceptance": True,
                        })
        handoffs.append({
            "exact_post_edit_source_review_pairs": source_matches,
            "source_sha_independent_review_bound": bool(source_matches),
            "source_binding_state": (
                "EXACT_POST_EDIT_SHA_HANDOFF_NOT_CONTENT_APPROVED" if source_matches
                else "NOT_SOURCE_BOUND_HOLD"),
            "portfolio_task_id": portfolio_id,
            "implementation_work_ids": [o["work_id"] for o in implementers],
            "review_work_ids": [o["work_id"] for o in reviews],
            "independent_review_attempted": bool(independent),
            "independent_review_qa_states": [o["content_qa_state"] for o in independent],
            "verified_completion": False,
            "next_action": (
                "REVIEW_FINDINGS_WITH_SOURCE_SHA_AND_LOCAL_ACCEPTANCE_TESTS"
                if source_matches else
                "PROVE_IMPLEMENTATION_POST_EDIT_SHA_EQUALS_REVIEW_INPUT_BEFORE_ACCEPTANCE"
                if independent else
                "ASSIGN_INDEPENDENT_REVIEW_WHEN_IMPLEMENTATION_READY"),
        })
    return {
        "schema": "TAKY_ORCHESTRATION_RECONCILIATION_V1",
        "mode": "READ_ONLY_NOT_EXECUTION_OR_COMPLETION_PROOF",
        "portfolio": {"total": len(portfolio), "categories": dict(categories),
                      "states": dict(statuses), "declared_verified": statuses.get("VERIFIED", 0)},
        "model_jobs": {"total": len(jobs),
                       "states_from_receipts": dict(Counter(o["derived_state"] for o in observations)),
                       # A registry boolean is a claim, not a signed DONE proof.
                       "verified_by_registry": sum(o["execution_verified"] for o in observations),
                       "independently_proven_completion_by_this_reconciler": 0,
                       "signed_execution_evidenced":
                           sum(o["signed_execution_evidenced"] for o in observations),
                       "unproven_verified_registry_claims":
                           sum(o["execution_verified"] and not o["signed_execution_evidenced"]
                               for o in observations),
                       "reviewers_unassigned": sum(o["reviewer"] == "UNASSIGNED" for o in observations),
                       "linked_to_portfolio": sum(o["portfolio_task_id"] is not None for o in observations),
                       "exact_source_sha_bound_independent_handoffs":
                           sum(h["source_sha_independent_review_bound"] for h in handoffs),
                       "registry_receipt_mismatches": sum(not o["registry_consistent"] for o in observations),
                       "signed_cli_returned_not_content_verified":
                           sum(o["signed_model_call_verification"] == "CLI_RETURNED_UNVERIFIED"
                               for o in observations),
                       "unbound_or_unverified_signed_calls":
                           sum(o["signed_model_call_verification"] not in
                               {"NOT_CHECKED_BY_THIS_RECONCILER", "CLI_RETURNED_UNVERIFIED"}
                               for o in observations)},
        "observations": observations,
        "handoffs": handoffs,
        "gaps": [
            "PORTFOLIO_MODEL_JOB_LINKS_INCOMPLETE" if any(o["portfolio_task_id"] is None for o in observations) else
            "PORTFOLIO_MODEL_JOBS_LINKED_OR_NO_JOBS",
            "PORTFOLIO_DECLARED_VERIFIED_NOT_INDEPENDENTLY_PROVEN",
            "NO_AUTOMATIC_POST_EXECUTION_TASK_SPECIFIC_DONE_PROOF",
        ],
        "model_calls_made_by_reconciliation": 0,
        "files_modified_by_reconciliation": 0,
    }

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    p.add_argument("--assignments", type=Path, default=DEFAULT_ASSIGNMENTS)
    p.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    args = p.parse_args()
    # Signed runtime readback is the real existing TAKY2 consumer, not a new store
    # or a new model invocation. A missing receipt is reported, never synthesized.
    from TAKY_SIGNED_EXECUTION_READBACK import read_signed
    report = reconcile(read_json(args.board), read_json(args.assignments),
                       args.history, signed_readback=read_signed)
    try:
        from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
        ensure_trusted_taky2()
        from TAKY2.state_store import load_bundle
        _, runtime, _ = load_bundle()
        report["scoped_edit_claims"] = inspect_scoped_edit_claims(runtime)
        registered = {o["work_id"]: o["portfolio_task_id"]
                      for o in report["observations"]}
        for claim in report["scoped_edit_claims"].get("items", []):
            receipt = claim.get("receipt_id")
            stored = runtime.get("scoped_edit_claims", {}).get(receipt)
            tid = stored.get("task_id") if isinstance(stored, dict) else None
            work_id = "TAKY-CHAT-" + tid if isinstance(tid, str) else None
            claim["registered_work_id"] = work_id if work_id in registered else None
            claim["portfolio_task_id"] = registered.get(work_id)
            claim["registry_binding_state"] = (
                "LINKED_TO_WORK_ID_NOT_DONE" if work_id in registered
                else "UNREGISTERED_WORK_ID_HOLD")
    except Exception:
        report["scoped_edit_claims"] = {
            "state": "SIGNED_LEDGER_UNAVAILABLE_HOLD", "items": [],
            "automatic_recovery_permitted": False,
        }
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
