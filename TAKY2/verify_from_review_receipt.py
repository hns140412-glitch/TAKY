from __future__ import annotations

import argparse
import json
from typing import Mapping

from TAKY2.bridges import BridgeViolation, verify_execution
from TAKY2.enforcement import stable_hash
from TAKY2.state_store import load_bundle, save_runtime


ACTORS = {
    "CODEX": ("openai", "codex", "TAKY_MODEL_REVIEW_CODEX"),
    "CLAUDE": ("anthropic", "sonnet", "TAKY_MODEL_REVIEW_CLAUDE"),
    "GEMINI": ("google", "gemini", "TAKY_MODEL_REVIEW_GEMINI"),
}


def verify_bound_review(runtime: Mapping, target_receipt: str, review_receipt: str):
    receipts = runtime.get("preflight_receipts", {})
    calls = runtime.get("execution_calls", {})
    target = receipts.get(target_receipt)
    review = receipts.get(review_receipt)
    target_call = calls.get(target_receipt)
    review_call = calls.get(review_receipt)

    if not all(isinstance(x, Mapping) for x in (target, review, target_call, review_call)):
        raise BridgeViolation("BOUND_RECEIPT_MISSING")
    if target_receipt == review_receipt:
        raise BridgeViolation("REVIEW_CANNOT_VERIFY_ITSELF")
    if (target.get("allowed") is not True or target.get("consumed") is True
            or target_receipt in runtime.get("completion_registry", {})
            or target_receipt in runtime.get("execution_outcomes", {})):
        raise BridgeViolation("TARGET_ALREADY_VERIFIED_OR_NOT_AUTHORIZED")
    if (not isinstance(runtime.get("authority_digest"), str)
            or target.get("authority_digest") != runtime["authority_digest"]):
        raise BridgeViolation("TARGET_REVIEW_STALE_AUTHORITY")
    if (review.get("allowed") is not True or review.get("call_allowed") is not True
            or review.get("consumed") is True):
        raise BridgeViolation("REVIEW_PREFLIGHT_NOT_ACTIVE_AUTHORIZED")
    if review.get("action_id") not in {"review:external-model", "verify:codex-packet"}:
        raise BridgeViolation("REVIEW_ACTION_MISMATCH")
    if (not isinstance(target.get("authority_digest"), str)
            or review.get("authority_digest") != target.get("authority_digest")):
        raise BridgeViolation("REVIEW_TARGET_AUTHORITY_NOT_BOUND")
    if not isinstance(review.get("call_digest"), str) or not review["call_digest"]:
        raise BridgeViolation("REVIEW_SIGNED_CALL_DIGEST_MISSING")
    if (target_call.get("status") != "RETURNED" or
            target_call.get("actual_calls") != 1 or
            not isinstance(target_call.get("result"), Mapping) or
            target_call["result"].get("returncode") != 0 or
            target_call.get("result_digest") != stable_hash(dict(target_call["result"]))):
        raise BridgeViolation("TARGET_EXECUTION_DIGEST_NOT_VERIFIED")
    if (review_call.get("status") != "RETURNED" or
            review_call.get("actual_calls") != 1 or
            not isinstance(review_call.get("result"), Mapping) or
            review_call["result"].get("returncode") != 0 or
            review_call.get("result_digest") != stable_hash(dict(review_call["result"]))):
        raise BridgeViolation("REVIEW_EXECUTION_DIGEST_NOT_VERIFIED")

    orch = target.get("orchestration", {})
    actor = str(orch.get("verifier_actor") or "").upper()
    binding = ACTORS.get(actor)
    if not binding:
        raise BridgeViolation("VERIFIER_ACTOR_UNSUPPORTED")
    provider, model, executor_id = binding
    expected_action = "verify:codex-packet" if actor == "CODEX" else "review:external-model"
    if review.get("action_id") != expected_action:
        raise BridgeViolation("REVIEW_ACTOR_ACTION_MISMATCH")
    if (
        review_call.get("provider") != provider
        or review_call.get("model") != model
        or review_call.get("executor_id") != executor_id
        or executor_id == target_call.get("executor_id")
    ):
        raise BridgeViolation("REVIEW_ACTOR_BINDING_MISMATCH")

    # This proof can only be emitted by TAKY2's hardened execute_with_receipt
    # after it compared the reviewer's exact stdin bytes to the sealed target
    # result. A model-authored verdict and a signed call receipt alone cannot
    # establish that the reviewer actually received the target material.
    proof = review_call.get("target_review_evidence")
    if (not isinstance(proof, Mapping)
            or proof.get("schema") != "TAKY_TARGET_REVIEW_RECEIPT_V1"
            or proof.get("target_receipt_id") != target_receipt
            or proof.get("target_result_digest") != target_call.get("result_digest")
            or proof.get("review_call_digest") != review.get("call_digest")
            or proof.get("review_result_digest") != review_call.get("result_digest")
            or not isinstance(proof.get("packet_digest"), str)
            or len(proof["packet_digest"]) != 20):
        raise BridgeViolation("REVIEW_TARGET_STDIN_PROVENANCE_MISSING")

    result = review_call.get("result", {})
    if result.get("returncode") != 0:
        raise BridgeViolation("REVIEW_EXECUTION_FAILED")
    try:
        verdict = json.loads(str(result.get("stdout") or "").strip())
    except Exception as exc:
        raise BridgeViolation("REVIEW_STDOUT_NOT_JSON") from exc
    if not isinstance(verdict, dict):
        raise BridgeViolation("REVIEW_VERDICT_MUST_BE_OBJECT")

    if verdict.get("target_receipt_id") != target_receipt:
        raise BridgeViolation("TARGET_RECEIPT_MISMATCH")
    if verdict.get("target_result_digest") != target_call.get("result_digest"):
        raise BridgeViolation("TARGET_RESULT_DIGEST_MISMATCH")
    if verdict.get("authority_digest") != target.get("authority_digest"):
        raise BridgeViolation("AUTHORITY_DIGEST_MISMATCH")

    updated = verify_execution(
        runtime,
        target_receipt,
        verifier=lambda _call, _receipt: verdict,
        verifier_id="TAKY_REVIEW_RECEIPT_BRIDGE:" + review_receipt,
    )
    if (updated.get("execution_outcomes", {}).get(target_receipt) != "SUCCESS"
            or target_receipt not in updated.get("completion_registry", {})):
        raise BridgeViolation("REVIEW_NOT_ACCEPTED_NO_COMPLETION")

    # The review action is an internal verification transport. Once its returned
    # result has been bound to and accepted as evidence for the target receipt,
    # it must not keep owning the reusable verifier route.
    stored_review = updated.setdefault("preflight_receipts", {}).get(review_receipt)
    if isinstance(stored_review, dict):
        review_execution_key = stored_review.get("execution_key")
        stored_review["consumed"] = True
        stored_review["consumed_as_verification_evidence_for"] = target_receipt
        if review_execution_key:
            updated.setdefault("active_attempts", {}).pop(review_execution_key, None)
    return updated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target_receipt")
    ap.add_argument("review_receipt")
    ns = ap.parse_args()

    _, runtime, authority_digest = load_bundle()
    try:
        updated = verify_bound_review(runtime, ns.target_receipt, ns.review_receipt)
    except BridgeViolation as exc:
        print("VERIFY_BLOCKED:" + str(exc))
        return 2

    save_runtime(
        updated,
        expected_version=runtime["runtime_version"],
        authority_digest_value=authority_digest,
    )
    completion = updated.get("completion_registry", {}).get(ns.target_receipt, {})
    print(json.dumps({
        "state": "EXECUTION_VERIFIED",
        "target_receipt": ns.target_receipt,
        "review_receipt": ns.review_receipt,
        "evidence_refs": completion.get("evidence_refs", []),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
