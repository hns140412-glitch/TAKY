from __future__ import annotations

import argparse
import json
from typing import Mapping

from TAKY2.bridges import BridgeViolation, verify_execution
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
    if review.get("action_id") != "review:external-model":
        raise BridgeViolation("REVIEW_ACTION_MISMATCH")

    orch = target.get("orchestration", {})
    actor = str(orch.get("verifier_actor") or "").upper()
    binding = ACTORS.get(actor)
    if not binding:
        raise BridgeViolation("VERIFIER_ACTOR_UNSUPPORTED")
    provider, model, executor_id = binding
    if (
        review_call.get("provider") != provider
        or review_call.get("model") != model
        or review_call.get("executor_id") != executor_id
    ):
        raise BridgeViolation("REVIEW_ACTOR_BINDING_MISMATCH")

    result = review_call.get("result", {})
    if result.get("returncode") != 0:
        raise BridgeViolation("REVIEW_EXECUTION_FAILED")
    try:
        verdict = json.loads(str(result.get("stdout") or "").strip())
    except Exception as exc:
        raise BridgeViolation("REVIEW_STDOUT_NOT_JSON") from exc

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
