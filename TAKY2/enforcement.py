from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .orchestration import validate_orchestration_contract


USER_PROVENANCE = {"USER_STATED", "USER_CONFIRMED"}
ACCOUNT_AUTH_SOURCE = "central-family-session"
ACCOUNT_IDENTITY_PROVIDER = "GOOGLE_OIDC_VERIFIED"
BINDING_FIELDS = {
    "USER_INTENT", "DESIRED_OUTCOME", "NON_NEGOTIABLE",
    "FORBIDDEN", "ACCEPTANCE", "AUTHORIZED_TARGET",
    "AUTHORIZED_ACTION_CLASSES",
}
ACTION_KINDS = {"READ", "LOCAL_WRITE", "EXTERNAL_WRITE", "DELETE", "PUBLISH"}
EXTERNAL_ACTIONS = {"EXTERNAL_WRITE", "DELETE", "PUBLISH"}
IRREVERSIBLE_ACTIONS = {"DELETE", "PUBLISH"}
TRANSIENT_FAILURES = {"TIMEOUT", "RATE_LIMIT", "LOCK_CONTENTION", "TEMP_UNAVAILABLE"}
FAILURE_CLASSES = TRANSIENT_FAILURES | {
    "INPUT", "AUTHORITY", "METHOD", "TOOL", "ENVIRONMENT",
    "PERMISSION", "DATA", "VALIDATION", "EXTERNAL",
}
VALID_EVIDENCE_TYPES = {
    "tool_output", "artifact", "diff", "runtime_test",
    "source_ref", "independent_review",
}
TRANSIENT_LIMIT = 2


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    state: str
    reason: str
    evidence: tuple[str, ...] = ()


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()[:20]


def trusted_user_ref(trusted: Mapping[str, Any], ref: Any, *, kind: str | None = None,
                     receipt_id: str | None = None) -> bool:
    if not isinstance(ref, str) or not ref:
        return False
    src = trusted.get("source_registry", {}).get(ref)
    if not isinstance(src, Mapping) or src.get("actor") != "USER":
        return False
    if kind is not None and src.get("kind") != kind:
        return False
    if receipt_id is not None and src.get("receipt_id") != receipt_id:
        return False
    return True


def trusted_user_event(
    trusted: Mapping[str, Any],
    ref: Any,
    *,
    kind: str,
    receipt_id: str,
) -> bool:
    if not isinstance(ref, str) or not ref:
        return False
    event = trusted.get("user_events", {}).get(ref)
    return (
        isinstance(event, Mapping)
        and event.get("actor") == "USER"
        and event.get("kind") == kind
        and event.get("receipt_id") == receipt_id
        and isinstance(event.get("verified_by"), str)
        and bool(event.get("verified_by"))
    )


def trusted_approval(trusted: Mapping[str, Any], key: str) -> str | None:
    ref = trusted.get("approvals", {}).get(key)
    consumed_ref = trusted.get("consumed_approvals", {}).get(key)
    if consumed_ref == ref:
        return None
    return ref if trusted_user_ref(trusted, ref, kind="approval") else None


def resolve_action(trusted: Mapping[str, Any], plan: Mapping[str, Any]) -> Mapping[str, Any] | None:
    action_id = plan.get("action_id")
    if not isinstance(action_id, str) or not action_id:
        return None
    action = trusted.get("action_registry", {}).get(action_id)
    return action if isinstance(action, Mapping) else None


def action_digest(action: Mapping[str, Any]) -> str:
    return stable_hash(dict(action))


def verification_tier(action: Mapping[str, Any]) -> str:
    kind = action.get("kind")
    if (
        kind in EXTERNAL_ACTIONS
        or kind in IRREVERSIBLE_ACTIONS
        or action.get("external_facing") is True
        or action.get("meaning_or_authority_changing") is True
    ):
        return "STRONG"
    return "STANDARD"


def required_verifications_for_tier(tier: Any) -> set[str]:
    if tier == "STRONG":
        return {"structural", "technical", "intent", "independent"}
    return {"technical", "intent"}


def _norm_token(value: Any) -> str:
    return str(value or "").strip().lower()


def route_fingerprint(attempt: Mapping[str, Any]) -> str:
    return stable_hash({
        "target": _norm_token(attempt.get("target")),
        "method_or_tool": _norm_token(attempt.get("method_or_tool")),
    })


def validate_key(trusted: Mapping[str, Any]) -> GateResult | None:
    key = trusted.get("key", {})
    intent = key.get("USER_INTENT") or key.get("DESIRED_OUTCOME")
    if not isinstance(intent, Mapping):
        return GateResult(False, "KEY_NOT_LOCKED", "user-grounded intent missing")

    for name in BINDING_FIELDS:
        field = key.get(name)
        if field is None:
            continue
        if not isinstance(field, Mapping):
            return GateResult(False, "BLOCKED", f"{name} must be structured")
        provenance = field.get("provenance")
        ref = field.get("source_ref")
        scope = field.get("scope")
        version = field.get("version")
        if provenance == "AI_INFERRED":
            return GateResult(False, "USER_DECISION_REQUIRED", f"{name} cannot bind from AI_INFERRED")
        if provenance not in USER_PROVENANCE or not trusted_user_ref(trusted, ref):
            return GateResult(False, "BLOCKED", f"{name} lacks trusted USER provenance")
        if not isinstance(scope, str) or not scope.strip():
            return GateResult(False, "BLOCKED", f"{name} trusted scope missing")
        if not isinstance(version, int) or version < 1:
            return GateResult(False, "BLOCKED", f"{name} trusted version missing")
    return None


def key_gate(trusted: Mapping[str, Any], plan: Mapping[str, Any]) -> GateResult:
    contract_ok, contract_reason = validate_orchestration_contract(trusted)
    if not contract_ok:
        return GateResult(False, "BLOCKED", contract_reason)

    invalid = validate_key(trusted)
    if invalid:
        return invalid

    action = resolve_action(trusted, plan)
    if action is None:
        return GateResult(False, "BLOCKED", "action_id is not registered in trusted authority")

    kind = action.get("kind")
    if kind not in ACTION_KINDS:
        return GateResult(False, "BLOCKED", "trusted action kind is unknown")

    key = trusted["key"]
    forbidden_field = key.get("FORBIDDEN")
    forbidden = []
    if forbidden_field is not None:
        value = forbidden_field.get("value") if isinstance(forbidden_field, Mapping) else None
        if not isinstance(value, list):
            return GateResult(False, "BLOCKED", "FORBIDDEN must be a list")
        forbidden = value
    blocked = {str(v) for v in forbidden}
    if str(kind) in blocked or str(action.get("action_class")) in blocked:
        return GateResult(False, "BLOCKED", "trusted action conflicts with FORBIDDEN")

    if kind in EXTERNAL_ACTIONS:
        target = key.get("AUTHORIZED_TARGET")
        classes = key.get("AUTHORIZED_ACTION_CLASSES")
        runtime = trusted.get("runtime", {})
        attestation = runtime.get("account_attestation") if isinstance(runtime, Mapping) else None
        actual = (
            attestation.get("account")
            if isinstance(attestation, Mapping) and attestation.get("verified") is True
            else None
        )
        if isinstance(attestation, Mapping):
            attestation_evidence = (
                attestation.get("source"),
                attestation.get("evidence_ref"),
                attestation.get("session_id"),
                attestation.get("verified_by"),
            )
            identity_binding = (
                attestation.get("identity_provider"),
                attestation.get("principal_id"),
                attestation.get("family_id"),
                attestation.get("self_member_id"),
                attestation.get("first_bound_evidence_ref"),
                attestation.get("first_bound_session_id"),
            )
            binding_mode = attestation.get("binding_mode")
        else:
            attestation_evidence = ()
            identity_binding = ()
            binding_mode = None
        requested = action.get("target_account")
        action_class = action.get("action_class")

        if not isinstance(target, Mapping) or not isinstance(target.get("value"), str):
            return GateResult(False, "BLOCKED", "authorized target missing")
        if not actual or target["value"] != actual:
            return GateResult(False, "BLOCKED", "verified account attestation mismatch")
        if (
            len(attestation_evidence) != 4
            or not all(isinstance(v, str) and v.strip() for v in attestation_evidence)
        ):
            return GateResult(False, "BLOCKED", "verified account attestation evidence missing")
        if any(v != v.strip() for v in attestation_evidence):
            return GateResult(False, "BLOCKED", "verified account attestation evidence is not canonical")
        if attestation.get("source") != ACCOUNT_AUTH_SOURCE:
            return GateResult(False, "BLOCKED", "account attestation source is not trusted")
        if binding_mode != "FIRST_AUTH_RUNTIME":
            return GateResult(False, "BLOCKED", "runtime first-auth target binding missing")
        if (
            len(identity_binding) != 6
            or not all(isinstance(v, str) and v.strip() for v in identity_binding)
        ):
            return GateResult(False, "BLOCKED", "verified runtime identity binding missing")
        if attestation.get("identity_provider") != ACCOUNT_IDENTITY_PROVIDER:
            return GateResult(False, "BLOCKED", "account identity provider is not trusted")
        verifier_name = str(attestation.get("verified_by") or "").strip().casefold()
        self_identity = {
            str(attestation.get("account") or "").strip().casefold(),
            str(attestation.get("principal_id") or "").strip().casefold(),
            str(attestation.get("self_member_id") or "").strip().casefold(),
        }
        if verifier_name in self_identity:
            return GateResult(False, "BLOCKED", "account principal/member cannot self-verify binding")
        if not requested or target["value"] != requested:
            return GateResult(False, "BLOCKED", "registered target mismatch")

        allowed_classes = []
        if isinstance(classes, Mapping) and isinstance(classes.get("value"), list):
            allowed_classes = [x for x in classes["value"] if isinstance(x, str)]

        if not isinstance(action_class, str) or not action_class:
            return GateResult(False, "BLOCKED", "trusted external action_class missing")

        approval_key = "action:" + action_digest(action)
        approval_needed = (
            action_class not in allowed_classes
            or kind in IRREVERSIBLE_ACTIONS
        )
        approval_ref = trusted_approval(trusted, approval_key) if approval_needed else None
        if approval_needed and not approval_ref:
            return GateResult(False, "USER_DECISION_REQUIRED", "external action needs bound approval")

    refs = []
    for name in BINDING_FIELDS:
        field = key.get(name)
        if isinstance(field, Mapping) and field.get("source_ref"):
            refs.append(str(field["source_ref"]))
    if kind in EXTERNAL_ACTIONS and approval_needed and approval_ref:
        refs.append("approval-key:" + approval_key)
    return GateResult(True, "KEY_OK", "Key and trusted action verified", tuple(refs))


def context_gate(trusted: Mapping[str, Any], request: Mapping[str, Any]) -> GateResult:
    if not trusted.get("_authority_digest"):
        return GateResult(False, "READ_ONLY", "authority digest missing")

    mode = request.get("mode")
    if mode not in {"full", "snapshot", "delta"}:
        return GateResult(False, "CONTEXT_BLOCKED", "unknown context mode")

    ctx = trusted.get("context", {})
    premise_loaded = bool(ctx.get("premise_loaded"))
    snapshot_verified = bool(ctx.get("snapshot_verified"))
    reread_allowed = bool(ctx.get("full_reread_authorized"))

    if mode == "full" and premise_loaded and not reread_allowed:
        return GateResult(False, "SKIP_FULL_REREAD", "premise already loaded")
    if mode == "snapshot" and not snapshot_verified:
        return GateResult(False, "CONTEXT_BLOCKED", "snapshot not verified")
    if mode == "delta" and not (premise_loaded or snapshot_verified):
        return GateResult(False, "CONTEXT_BLOCKED", "DELTA needs loaded premise/snapshot")

    return GateResult(True, "CONTEXT_OK", f"context mode={mode}")


def route_gate(trusted: Mapping[str, Any], attempt: Mapping[str, Any]) -> GateResult:
    ledger = trusted.get("route_ledger", {})
    budget = ledger.get("route_budget", 3)
    if not isinstance(budget, int) or not 1 <= budget <= 3:
        return GateResult(False, "BLOCKED", "trusted route budget must be 1..3")

    if not attempt.get("target") or not attempt.get("method_or_tool"):
        return GateResult(False, "BLOCKED", "target/method required")

    route_fp = route_fingerprint(attempt)
    seen_routes = set(ledger.get("seen_routes", []))
    failed_sigs = set(ledger.get("failed_signatures", []))

    approval_evidence = []
    if route_fp not in seen_routes and len(seen_routes) >= budget:
        approval_key = "route_budget:" + route_fp
        if not trusted_approval(trusted, approval_key):
            return GateResult(False, "USER_DECISION_REQUIRED", "different-route budget exhausted")
        approval_evidence.append("approval-key:" + approval_key)

    failure_by_route = ledger.get("last_failure_by_route", {})
    last = failure_by_route.get(route_fp, {}) if isinstance(failure_by_route, Mapping) else {}
    failure_class = last.get("class", "INITIAL")
    sig = stable_hash({"route": route_fp, "failure_class": failure_class})

    if failure_class in TRANSIENT_FAILURES:
        tf = ledger.get("transient_failures", {})
        if not isinstance(tf, Mapping):
            return GateResult(False, "BLOCKED", "invalid transient ledger")
        count = tf.get(route_fp, 0)
        if not isinstance(count, int):
            return GateResult(False, "BLOCKED", "invalid transient counter")
        if count >= TRANSIENT_LIMIT:
            return GateResult(False, "USER_DECISION_REQUIRED", "transient retry cap reached")
        return GateResult(
            True,
            "ROUTE_OK",
            "bounded transient retry",
            tuple([route_fp] + approval_evidence),
        )

    if sig in failed_sigs:
        return GateResult(False, "BLOCKED", "same failed route/failure-class cannot repeat")

    capability = attempt.get("needed_capability")
    if attempt.get("ask_user") and capability in set(trusted.get("capabilities", [])):
        return GateResult(False, "USER_DEBUGGER_VIOLATION", "AI has required capability itself")

    return GateResult(
        True,
        "ROUTE_OK",
        "route available",
        tuple([sig, route_fp] + approval_evidence),
    )


def record_failure(ledger: Mapping[str, Any], attempt: Mapping[str, Any],
                   failure_class: str, *, route_exhausted: bool = False) -> dict[str, Any]:
    if failure_class not in FAILURE_CLASSES:
        raise ValueError("unknown failure_class")

    out = deepcopy(dict(ledger))
    route_fp = route_fingerprint(attempt)
    out.setdefault("failed_signatures", [])
    out.setdefault("seen_routes", [])
    out.setdefault("transient_failures", {})
    out.setdefault("last_failure_by_route", {})

    sig = stable_hash({"route": route_fp, "failure_class": failure_class})
    if failure_class not in TRANSIENT_FAILURES and sig not in out["failed_signatures"]:
        out["failed_signatures"].append(sig)

    out["last_failure_by_route"][route_fp] = {
        "class": failure_class,
        "target": attempt.get("target"),
        "method_or_tool": attempt.get("method_or_tool"),
    }

    if failure_class in TRANSIENT_FAILURES:
        out["transient_failures"][route_fp] = int(
            out["transient_failures"].get(route_fp, 0)
        ) + 1

    return out


def cost_gate(
    trusted: Mapping[str, Any],
    action: Mapping[str, Any],
    call: Mapping[str, Any],
) -> GateResult:
    policy = action.get("call_policy")
    if not isinstance(policy, Mapping):
        return GateResult(False, "BLOCKED", "trusted action call_policy missing")

    mode = policy.get("mode")
    if mode == "LOCAL_ONLY":
        return GateResult(True, "SKIP_CALL", "trusted action policy is local-only")
    if mode not in {"EXTERNAL_REQUIRED", "EXTERNAL_OPTIONAL"}:
        return GateResult(False, "BLOCKED", "unknown trusted call policy mode")

    if call.get("context") == "full" and trusted.get("context", {}).get("premise_loaded"):
        if not trusted.get("context", {}).get("full_reread_authorized"):
            return GateResult(False, "SKIP_FULL_REREAD", "full context reread blocked")

    allowed_models = policy.get("allowed_models")
    if not isinstance(allowed_models, list) or not allowed_models:
        return GateResult(False, "BLOCKED", "trusted allowed_models missing")
    allowed_models = {_norm_token(v) for v in allowed_models if isinstance(v, str)}

    model = _norm_token(call.get("model"))
    if not model or model not in allowed_models:
        return GateResult(False, "REROUTE_CHEAPER", "requested model is not trusted for this action")

    expected_calls = call.get("expected_calls", 1)
    if not isinstance(expected_calls, int) or expected_calls < 1:
        return GateResult(False, "REROUTE_CHEAPER", "invalid expected_calls")

    max_calls = policy.get("max_calls", 1)
    if not isinstance(max_calls, int) or max_calls < 1:
        return GateResult(False, "BLOCKED", "trusted max_calls must be >= 1")

    call_key = "cost:" + stable_hash(dict(call))
    approval = trusted_approval(trusted, call_key)
    approval_evidence = []

    if mode == "EXTERNAL_OPTIONAL":
        if not approval:
            return GateResult(False, "REROUTE_CHEAPER", "optional external call needs trusted approval")
        approval_evidence.append("approval-key:" + call_key)

    if expected_calls > max_calls:
        if not approval:
            return GateResult(False, "REROUTE_CHEAPER", "requested call count exceeds trusted action policy")
        if "approval-key:" + call_key not in approval_evidence:
            approval_evidence.append("approval-key:" + call_key)

    effort = _norm_token(call.get("effort"))
    max_effort = _norm_token(policy.get("max_effort", "medium"))
    effort_rank = {"low": 1, "medium": 2, "high": 3, "xhigh": 4, "max": 5}
    if effort not in effort_rank or max_effort not in effort_rank:
        return GateResult(False, "BLOCKED", "invalid trusted/requested effort")
    if effort_rank[effort] > effort_rank[max_effort]:
        if not approval:
            return GateResult(False, "REROUTE_CHEAPER", "requested effort exceeds trusted action policy")
        if "approval-key:" + call_key not in approval_evidence:
            approval_evidence.append("approval-key:" + call_key)

    if call.get("parallel") and policy.get("allow_parallel") is not True:
        key = "parallel:" + stable_hash(dict(call))
        if not trusted_approval(trusted, key):
            return GateResult(False, "REROUTE_CHEAPER", "parallel calls are not trusted for this action")
        approval_evidence.append("approval-key:" + key)

    if call.get("subagents") and policy.get("allow_subagents") is not True:
        key = "subagents:" + stable_hash(dict(call))
        if not trusted_approval(trusted, key):
            return GateResult(False, "REROUTE_CHEAPER", "subagents are not trusted for this action")
        approval_evidence.append("approval-key:" + key)

    return GateResult(
        True,
        "COST_OK",
        "trusted action call policy satisfied",
        tuple(approval_evidence),
    )


def done_gate(trusted: Mapping[str, Any], report: Mapping[str, Any]) -> GateResult:
    receipt_id = report.get("preflight_receipt")
    receipts = trusted.get("preflight_receipts", {})
    receipt = receipts.get(receipt_id) if isinstance(receipt_id, str) else None
    if not isinstance(receipt, Mapping) or receipt.get("allowed") is not True:
        return GateResult(False, "NOT_DONE", "valid preflight receipt required")
    outcome = trusted.get("execution_outcomes", {}).get(receipt_id)
    if outcome == "ABANDONED":
        return GateResult(False, "ABANDONED", "explicit USER stop abandoned this receipt")
    if receipt.get("consumed"):
        return GateResult(False, "NOT_DONE", "preflight receipt already consumed")
    if receipt.get("authority_digest") != trusted.get("_authority_digest"):
        return GateResult(False, "NOT_DONE", "preflight receipt authority is stale")

    if outcome != "SUCCESS":
        return GateResult(False, "NOT_DONE", "execution SUCCESS is not recorded")

    completion_registry = trusted.get("completion_registry", {})
    completion = completion_registry.get(receipt_id)
    if not isinstance(completion, Mapping):
        return GateResult(False, "NOT_DONE", "trusted completion record missing")
    if completion.get("plan_digest") != receipt.get("plan_digest"):
        return GateResult(False, "NOT_DONE", "completion plan_digest mismatch")
    if completion.get("action_digest") != receipt.get("action_digest"):
        return GateResult(False, "NOT_DONE", "completion action_digest mismatch")
    if completion.get("call_digest") != receipt.get("call_digest"):
        return GateResult(False, "NOT_DONE", "completion call_digest mismatch")

    if completion.get("critical_gaps"):
        return GateResult(False, "REWORK", "trusted critical gaps remain")
    if completion.get("key_match") is not True:
        return GateResult(False, "REWORK", "trusted Key match not verified")

    required = set(completion.get("required_verifications", []))
    passed = set(completion.get("passed_verifications", []))
    minimum = required_verifications_for_tier(receipt.get("verification_tier", "STANDARD"))
    if not minimum.issubset(required):
        return GateResult(False, "BLOCKED", "required verification tier is under-specified")
    missing = sorted(required - passed)
    if missing:
        return GateResult(False, "PARTIAL", "missing verifications: " + ",".join(missing))

    refs = report.get("evidence_refs", [])
    if not isinstance(refs, list) or not refs:
        return GateResult(False, "NOT_DONE", "NO EVIDENCE, NO DONE")

    registry = trusted.get("evidence_registry", {})
    verified_refs = []
    for ref in refs:
        item = registry.get(ref)
        if not isinstance(item, Mapping):
            return GateResult(False, "NOT_DONE", f"untrusted evidence ref: {ref}")
        if item.get("receipt_id") != receipt_id:
            return GateResult(False, "NOT_DONE", f"evidence not bound to receipt: {ref}")
        if item.get("plan_digest") != receipt.get("plan_digest"):
            return GateResult(False, "NOT_DONE", f"evidence plan_digest mismatch: {ref}")
        if item.get("action_digest") != receipt.get("action_digest"):
            return GateResult(False, "NOT_DONE", f"evidence action_digest mismatch: {ref}")
        if item.get("call_digest") != receipt.get("call_digest"):
            return GateResult(False, "NOT_DONE", f"evidence call_digest mismatch: {ref}")
        if item.get("verified") is not True or item.get("type") not in VALID_EVIDENCE_TYPES:
            return GateResult(False, "NOT_DONE", f"evidence not verified: {ref}")
        verified_refs.append(str(ref))

    confirm_ref = completion.get("user_confirmation_ref")
    if confirm_ref:
        if not trusted_user_event(
            trusted, confirm_ref, kind="confirmation", receipt_id=receipt_id
        ):
            return GateResult(False, "DELIVERED_UNCONFIRMED", "confirmation is not bound to receipt")
        return GateResult(True, "USER_CONFIRMED", "verified and explicitly confirmed", tuple(verified_refs))

    return GateResult(
        False,
        "DELIVERED_UNCONFIRMED",
        "verified result awaits explicit USER confirmation",
        tuple(verified_refs),
    )
