from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from .orchestration import WORKER_ROLE_REGISTRY, validate_orchestration_contract


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
    "source_ref", "independent_review", "user_decision", "state_snapshot",
}
ACCEPTED_EVIDENCE_STATE = "ACCEPTED"
REJECTED_EVIDENCE_STATES = {"REJECTED", "PARTIAL", "STALE", "UNKNOWN"}
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


def safe_tool_gate(tool_action: Mapping[str, Any] | None) -> GateResult:
    """Deterministic pre-tool safety/route check; not a sixth HARD GATE."""
    if tool_action is None:
        return GateResult(True, "SAFE_TOOL_NOT_APPLICABLE", "no tool_action declared")
    if not isinstance(tool_action, Mapping):
        return GateResult(False, "SAFE_TOOL_BLOCKED", "tool_action must be an object")

    detected: list[str] = []
    purpose = str(tool_action.get("purpose") or "").strip()
    purposes = tool_action.get("purposes")
    if purposes is not None:
        if not isinstance(purposes, list) or len([x for x in purposes if str(x or "").strip()]) != 1:
            detected.append("ONE_CALL_ONE_PRIMARY_PURPOSE_REQUIRED")
    elif not purpose:
        detected.append("PRIMARY_PURPOSE_MISSING")

    target = str(tool_action.get("target") or "").strip()
    if not target:
        detected.append("EXACT_TARGET_REQUIRED")

    operation = str(tool_action.get("operation") or "").strip().lower()
    transport = str(tool_action.get("transport") or "").strip().lower()
    command = str(tool_action.get("command") or "")
    connector_available = tool_action.get("connector_available") is True
    drive_id = str(tool_action.get("drive_file_id") or tool_action.get("drive_folder_id") or "").strip()

    if operation in {"google_drive", "drive", "drive_intake"} and connector_available and drive_id:
        if transport in {"local_scan", "drivefs_reverse_lookup", "shell_drive_search"}:
            detected.append("DRIVE_CONNECTOR_ID_ROUTE_REQUIRED")

    if re.match(r"^[A-Za-z]:\\?$", target) or re.match(r"^[A-Za-z]:\\Users\\?$", target, re.I):
        detected.append("BROAD_ROOT_SCAN_FORBIDDEN")

    combined = "\n".join([target, command])
    auth_patterns = (
        r"\\AppData\\.*\\Google\\DriveFS",
        r"\\AppData\\.*\\Credentials?",
        r"\\\.ssh(?:\\|$)",
        r"credential",
    )
    if tool_action.get("explicit_auth_inspection") is not True:
        if any(re.search(pattern, combined, re.I) for pattern in auth_patterns):
            detected.append("AUTH_ADJACENT_ENUMERATION_REQUIRES_EXPLICIT_NECESSITY")

    if re.search(r"Get-ChildItem\s+Env:", command, re.I):
        detected.append("BROAD_ENV_ENUMERATION_FORBIDDEN")

    previous = str(tool_action.get("previous_block_signature") or "").strip()
    current = str(tool_action.get("action_signature") or "").strip()
    if previous and current and previous == current:
        detected.append("BLOCKED_ACTION_SIGNATURE_RETRY_FORBIDDEN")

    if tool_action.get("file_io_only") is True and transport == "shell":
        detected.append("FILE_TOOL_REQUIRED_BEFORE_SHELL")

    if detected:
        return GateResult(False, "SAFE_TOOL_BLOCKED", ";".join(detected), tuple(detected))
    return GateResult(True, "SAFE_TOOL_OK", "safe tool precheck passed")


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
        and event.get("explicit") is True
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


BILLING_CLASSES = {"UNMETERED", "SUBSCRIPTION_QUOTA", "PAID_API"}


def _resolve_billing_class(
    policy: Mapping[str, Any],
    model: Any,
) -> tuple[str | None, str | None]:
    normalized_model = _norm_token(model)
    model_billing = policy.get("model_billing")
    if model_billing is not None:
        if not isinstance(model_billing, Mapping):
            return None, "trusted model_billing must be a mapping"
        normalized = {
            _norm_token(name): str(value or "").strip().upper()
            for name, value in model_billing.items()
            if isinstance(name, str)
        }
        billing = normalized.get(normalized_model)
        if billing is None:
            return None, "trusted model billing class missing for requested model"
    else:
        raw = policy.get("billing_class")
        if not isinstance(raw, str) or not raw.strip():
            return None, "trusted billing_class required for external action"
        billing = raw.strip().upper()
    if billing not in BILLING_CLASSES:
        return None, "unknown trusted billing_class"
    return billing, None


def _model_has_capability(
    policy: Mapping[str, Any],
    model: Any,
    capability: str,
) -> bool:
    mapping = policy.get("model_capabilities")
    if not isinstance(mapping, Mapping):
        return False
    caps = mapping.get(_norm_token(model))
    if caps is None:
        # accept original-case keys while normalizing lookup
        for name, values in mapping.items():
            if _norm_token(name) == _norm_token(model):
                caps = values
                break
    if not isinstance(caps, list):
        return False
    normalized = {str(v or "").strip().upper() for v in caps if isinstance(v, str)}
    return capability.strip().upper() in normalized


def route_fingerprint(attempt: Mapping[str, Any]) -> str:
    return stable_hash({
        "target": _norm_token(attempt.get("target")),
        "method_or_tool": _norm_token(attempt.get("method_or_tool")),
        # Only material execution transport revisions belong in the route identity.
        # Cosmetic model effort/batch details intentionally do not.
        "transport_profile": _norm_token(attempt.get("transport_profile")),
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

    semantic_owner_ref = action.get("semantic_owner_ref")
    semantic_owner_scope = action.get("semantic_owner_scope")
    if not isinstance(semantic_owner_ref, str) or not semantic_owner_ref.strip():
        return GateResult(False, "BLOCKED", "trusted action semantic_owner_ref missing")
    if not isinstance(semantic_owner_scope, str) or not semantic_owner_scope.strip():
        return GateResult(False, "BLOCKED", "trusted action semantic_owner_scope missing")
    if semantic_owner_ref.strip().upper() in {
        "CHATGPT", "CODEX", "CLAUDE", "LOCAL", "MCP", "ROUTER", "TOOL"
    }:
        return GateResult(False, "BLOCKED", "routing/tool actor cannot be semantic owner")

    owner_registry = trusted.get("semantic_owner_registry")
    if not isinstance(owner_registry, Mapping):
        return GateResult(False, "OWNER_GAP", "semantic owner registry missing")
    owner_entry = owner_registry.get(semantic_owner_ref.strip())
    if not isinstance(owner_entry, Mapping):
        return GateResult(False, "OWNER_GAP", "semantic owner is not registered")
    if owner_entry.get("status") != "RESOLVED":
        return GateResult(False, "OWNER_GAP", "semantic owner remains unresolved OWNER_GAP")
    if owner_entry.get("can_own_semantics") is not True:
        return GateResult(False, "BLOCKED", "registered projection/tool cannot own semantics")
    owner_scopes = owner_entry.get("scopes")
    if not isinstance(owner_scopes, list) or not owner_scopes:
        return GateResult(False, "OWNER_GAP", "semantic owner scope registry missing")
    scope_ok = any(
        isinstance(scope, str)
        and (
            semantic_owner_scope.strip() == scope
            or semantic_owner_scope.strip().startswith(scope + "/")
        )
        for scope in owner_scopes
    )
    if not scope_ok:
        return GateResult(False, "BLOCKED", "semantic owner scope mismatch")

    worker_roles = action.get("worker_roles", [])
    if worker_roles is None:
        worker_roles = []
    if not isinstance(worker_roles, list):
        return GateResult(False, "BLOCKED", "trusted action worker_roles must be a list")
    if len(worker_roles) != len(set(worker_roles)):
        return GateResult(False, "BLOCKED", "trusted action worker_roles contain duplicates")
    unknown_worker_roles = [
        role for role in worker_roles
        if not isinstance(role, str) or role not in WORKER_ROLE_REGISTRY
    ]
    if unknown_worker_roles:
        return GateResult(False, "BLOCKED", "trusted action has unknown worker role")

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


STARTUP_READBACK_SOURCE_ORDER = (
    "START_HERE",
    "CANONICAL",
    "SYSTEMWIDE_V2",
    "CURRENT",
)
STARTUP_READBACK_REQUIRED = set(STARTUP_READBACK_SOURCE_ORDER)
STARTUP_READBACK_SOURCE_REFS = {
    "START_HERE": "drive:11BG91-phb11WmmIHoF6rS2TfWFK6yuJJEszFTsQ7B9M",
    "CANONICAL": "drive:1YWeGE6L1ya9cIbKDqE-IzUTBNwSZFO6iPDbPwXXYpqc",
    "SYSTEMWIDE_V2": "drive:1FodnFDgmNr0ZHFFl_zw1mUonpPBj7T9B6O-hauYHhYE",
    "CURRENT": "drive:1Cb_nJ55KyKui1sAoc_yOgkTsQ-7vVNqM6Hr19LoNd1c",
}


def canonical_startup_readback_sources(sources: Any) -> tuple[list[dict[str, str]] | None, str | None]:
    if not isinstance(sources, list):
        return None, "startup readback sources missing"
    by_kind: dict[str, dict[str, str]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            return None, "startup readback source malformed"
        kind = source.get("kind")
        ref = source.get("ref")
        revision = source.get("revision")
        if not isinstance(kind, str) or not kind.strip():
            return None, "startup readback source kind missing"
        kind = kind.strip()
        if kind not in STARTUP_READBACK_REQUIRED:
            return None, "startup readback source kind is not authorized"
        if kind in by_kind:
            return None, "startup readback source kind duplicated"
        if not isinstance(ref, str) or ref.strip() != STARTUP_READBACK_SOURCE_REFS[kind]:
            return None, "startup readback source ref mismatch"
        if not isinstance(revision, str) or not revision.strip() or revision != revision.strip():
            return None, "startup readback source revision missing/noncanonical"
        by_kind[kind] = {
            "kind": kind,
            "ref": ref.strip(),
            "revision": revision,
        }
    missing = sorted(STARTUP_READBACK_REQUIRED - set(by_kind))
    if missing:
        return None, "startup readback required sources missing: " + ",".join(missing)
    if len(by_kind) != len(STARTUP_READBACK_REQUIRED):
        return None, "startup readback source set is not exact"
    return [by_kind[kind] for kind in STARTUP_READBACK_SOURCE_ORDER], None


def startup_readback_receipt_id(authority_digest: str, sources: Any) -> str | None:
    normalized, error = canonical_startup_readback_sources(sources)
    if error or normalized is None:
        return None
    return "startup:" + stable_hash({
        "authority_digest": authority_digest,
        "sources": normalized,
    })


def _valid_startup_readback_receipt(
    trusted: Mapping[str, Any],
    receipt: Any,
) -> tuple[bool, str]:
    if not isinstance(receipt, Mapping):
        return False, "startup readback receipt missing"
    if receipt.get("authority_digest") != trusted.get("_authority_digest"):
        return False, "startup readback receipt authority is stale"
    if receipt.get("verified") is not True:
        return False, "startup readback receipt is not verified"
    if not isinstance(receipt.get("verified_by"), str) or not receipt.get("verified_by").strip():
        return False, "startup readback verifier missing"
    sources, error = canonical_startup_readback_sources(receipt.get("sources"))
    if error or sources is None:
        return False, error or "startup readback sources invalid"
    expected_id = startup_readback_receipt_id(
        str(trusted.get("_authority_digest") or ""),
        sources,
    )
    if receipt.get("receipt_id") != expected_id:
        return False, "startup readback receipt_id mismatch"
    return True, "startup readback verified"


def validate_startup_readback_receipt_for_digest(
    authority_digest_value: str,
    receipt: Any,
) -> tuple[bool, str]:
    return _valid_startup_readback_receipt(
        {"_authority_digest": authority_digest_value},
        receipt,
    )


def context_gate(trusted: Mapping[str, Any], request: Mapping[str, Any]) -> GateResult:
    if not trusted.get("_authority_digest"):
        return GateResult(False, "READ_ONLY", "authority digest missing")

    mode = request.get("mode")
    if mode not in {"full", "snapshot", "delta"}:
        return GateResult(False, "CONTEXT_BLOCKED", "unknown context mode")

    ctx = trusted.get("context", {})
    startup_ok, startup_reason = _valid_startup_readback_receipt(
        trusted, ctx.get("startup_readback_receipt") if isinstance(ctx, Mapping) else None
    )
    if not startup_ok:
        return GateResult(False, "READ_ONLY", startup_reason)

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
    soft_budget_exceeded = route_fp not in seen_routes and len(seen_routes) >= budget
    if soft_budget_exceeded:
        # Route budget is an optimization signal, not an authority wall.
        # A materially different route may continue; downstream COST/KEY controls
        # still govern spend, privilege, and irreversible actions.
        approval_evidence.append("route-budget-soft-exceeded:" + str(len(seen_routes)))

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
            return GateResult(
                False,
                "REROUTE_REQUIRED",
                "transient retry cap reached; choose a materially different route internally",
            )
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
        "ROUTE_SOFT_BUDGET_EXCEEDED" if soft_budget_exceeded else "ROUTE_OK",
        (
            "materially different route allowed; soft optimization budget exceeded"
            if soft_budget_exceeded
            else "route available"
        ),
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


ECONOMY_DECISION_KINDS = {
    "EXTERNAL_NOT_NECESSARY",
    "REUSE_SUFFICIENT",
    "LOCAL_SUFFICIENT",
}


def _trusted_economy_decision(
    trusted: Mapping[str, Any],
    action: Mapping[str, Any],
    ref: Any,
    *,
    expected_kind: str,
    requirement_class: str | None = None,
    required_capability: str | None = None,
) -> tuple[bool, str]:
    if expected_kind not in ECONOMY_DECISION_KINDS:
        return False, "unknown economy decision kind"
    if not isinstance(ref, str) or not ref.strip():
        return False, "trusted economy decision ref missing"
    registry = trusted.get("economy_evidence_registry", {})
    item = registry.get(ref) if isinstance(registry, Mapping) else None
    if not isinstance(item, Mapping):
        return False, "economy decision is not trusted"
    if item.get("decision_kind") != expected_kind:
        return False, "economy decision kind mismatch"
    if item.get("verified") is not True:
        return False, "economy decision is not verified"
    if item.get("acceptance_state") != ACCEPTED_EVIDENCE_STATE:
        return False, "economy decision is not accepted"
    if item.get("source_status") in REJECTED_EVIDENCE_STATES:
        return False, "economy decision is stale/rejected"
    if item.get("authority_digest") != trusted.get("_authority_digest"):
        return False, "economy decision authority is stale"
    if item.get("action_digest") != action_digest(action):
        return False, "economy decision action binding mismatch"
    if item.get("semantic_owner_ref") != action.get("semantic_owner_ref"):
        return False, "economy decision semantic owner mismatch"
    if item.get("semantic_owner_scope") != action.get("semantic_owner_scope"):
        return False, "economy decision semantic owner scope mismatch"
    if requirement_class in {"CAPABILITY_REQUIRED", "QUALITY_REQUIRED"}:
        if item.get("requirement_class") != requirement_class:
            return False, "economy decision requirement class mismatch"
        acceptance_ref = item.get("acceptance_ref")
        if not isinstance(acceptance_ref, str) or not acceptance_ref.strip():
            return False, "required economy decision acceptance_ref missing"
    if requirement_class == "CAPABILITY_REQUIRED":
        expected_capability = str(required_capability or "").strip().upper()
        if not expected_capability:
            return False, "capability-required economy decision lacks required capability"
        if str(item.get("required_capability") or "").strip().upper() != expected_capability:
            return False, "economy decision required capability mismatch"
    return True, ref



def dry_run_gate(
    trusted: Mapping[str, Any],
    action: Mapping[str, Any],
    call: Mapping[str, Any],
) -> GateResult:
    """Require a bounded execution plan before any real external call."""
    policy = action.get("call_policy")
    if not isinstance(policy, Mapping):
        return GateResult(False, "BLOCKED", "trusted action call_policy missing")

    mode = policy.get("mode")
    if mode == "LOCAL_ONLY":
        return GateResult(True, "DRY_RUN_LOCAL", "local-only action needs no external dry run")
    if mode not in {"EXTERNAL_REQUIRED", "EXTERNAL_OPTIONAL"}:
        return GateResult(False, "BLOCKED", "unknown trusted call policy mode")

    raw_plan = call.get("dry_run_plan")
    if raw_plan is None:
        plan = {}
    elif isinstance(raw_plan, Mapping):
        plan = dict(raw_plan)
    else:
        return GateResult(False, "DRY_RUN_INVALID", "dry_run_plan must be an object when provided")

    expected_calls = call.get("expected_calls", 1)
    if not isinstance(expected_calls, int) or expected_calls < 1:
        return GateResult(False, "BLOCKED", "external call expected_calls must be a positive integer")

    planned_calls = plan.get("expected_calls", expected_calls)
    if not isinstance(planned_calls, int) or planned_calls < 1:
        return GateResult(False, "DRY_RUN_INVALID", "dry_run expected_calls must be a positive integer")
    if "expected_calls" in plan and planned_calls != expected_calls:
        return GateResult(False, "DRY_RUN_MISMATCH", "explicit dry_run expected_calls conflicts with call expected_calls")

    max_calls = policy.get("max_calls", 1)
    if not isinstance(max_calls, int) or max_calls < 1:
        return GateResult(False, "BLOCKED", "trusted max_calls must be >= 1")
    effective_max_calls = 1
    if planned_calls > effective_max_calls:
        return GateResult(
            False,
            "REROUTE_LOWEST_SUFFICIENT",
            "requested call count exceeds current single-invocation executor; batch workload and rerun",
        )

    derived_fields = []
    operations = plan.get("operations")
    if operations is None:
        operation_hint = call.get("operation_hint")
        if isinstance(operation_hint, str) and operation_hint.strip():
            operations = [operation_hint.strip()]
        else:
            scope = str(action.get("execution_scope") or action.get("kind") or "external-action").strip()
            operations = [f"execute trusted action within {scope}"]
        derived_fields.append("operations")
    if not isinstance(operations, list) or not operations or not all(isinstance(x, str) and x.strip() for x in operations):
        return GateResult(False, "DRY_RUN_INVALID", "dry_run operations must be a non-empty string list")

    batch_strategy = plan.get("batch_strategy")
    if batch_strategy is None:
        batch_strategy = "single-call" if planned_calls == 1 else "bounded-batch"
        derived_fields.append("batch_strategy")
    if not isinstance(batch_strategy, str) or not batch_strategy.strip():
        return GateResult(False, "DRY_RUN_INVALID", "dry_run batch_strategy must be a string")

    fallback = plan.get("fallback", "REROUTE")
    if "fallback" not in plan:
        derived_fields.append("fallback")
    if fallback not in {"HOLD", "REROUTE", "LOCAL", "STOP"}:
        return GateResult(False, "DRY_RUN_INVALID", "dry_run fallback must be HOLD/REROUTE/LOCAL/STOP")

    billing_class, billing_error = _resolve_billing_class(policy, call.get("model"))
    if billing_error:
        return GateResult(False, "BLOCKED", billing_error)
    assert billing_class is not None
    declared_paid = plan.get("paid_api", billing_class == "PAID_API")
    if "paid_api" not in plan:
        derived_fields.append("paid_api")
    if not isinstance(declared_paid, bool):
        return GateResult(False, "DRY_RUN_INVALID", "dry_run paid_api must be boolean")
    if declared_paid != (billing_class == "PAID_API"):
        return GateResult(False, "DRY_RUN_MISMATCH", "explicit dry_run paid_api conflicts with trusted billing_class")

    execution_mode = str(policy.get("execution_mode") or "BOUNDED").strip().upper()
    if execution_mode not in {"BOUNDED", "PACKET_ONLY", "CODEX_VERIFY_ONLY"}:
        return GateResult(False, "BLOCKED", "unknown trusted execution_mode")
    packet_digest = None
    if execution_mode in {"PACKET_ONLY", "CODEX_VERIFY_ONLY"}:
        if str(call.get("execution_mode") or "").strip().upper() != execution_mode:
            return GateResult(
                False,
                "DRY_RUN_MISMATCH",
                "packet-bound action requires matching execution_mode call binding",
            )
        packet_digest = call.get("packet_digest")
        if not isinstance(packet_digest, str) or not packet_digest.strip():
            return GateResult(False, "DRY_RUN_INVALID", "packet-bound action requires packet_digest")

    digest = stable_hash({
        "action_digest": action_digest(action),
        "expected_calls": planned_calls,
        "operations": operations,
        "batch_strategy": batch_strategy,
        "fallback": fallback,
        "billing_class": billing_class,
        "paid_api": declared_paid,
        "execution_mode": execution_mode,
        "packet_digest": packet_digest,
    })
    evidence = ["dry-run:" + digest]
    if raw_plan is None:
        evidence.append("dry-run-source:AUTO_DERIVED")
    elif derived_fields:
        evidence.append("dry-run-source:NORMALIZED")
    if derived_fields:
        evidence.append("dry-run-derived:" + ",".join(sorted(derived_fields)))
    return GateResult(
        True,
        "DRY_RUN_OK",
        "bounded external execution plan accepted",
        tuple(evidence),
    )


def evaluate_savey_ai_economy(
    trusted: Mapping[str, Any],
    action: Mapping[str, Any],
    call: Mapping[str, Any],
    *,
    route_fp: str | None = None,
) -> GateResult:
    policy = action.get("call_policy")
    if not isinstance(policy, Mapping):
        return GateResult(False, "BLOCKED", "trusted action call_policy missing")

    mode = policy.get("mode")
    if mode == "LOCAL_ONLY":
        return GateResult(True, "SKIP_CALL", "trusted action policy is local-only")
    if mode not in {"EXTERNAL_REQUIRED", "EXTERNAL_OPTIONAL"}:
        return GateResult(False, "BLOCKED", "unknown trusted call policy mode")

    requirement_class = str(
        policy.get("requirement_class")
        or ("QUALITY_REQUIRED" if mode == "EXTERNAL_REQUIRED" else "OPTIONAL_CONVENIENCE")
    ).strip().upper()
    if requirement_class not in {
        "CAPABILITY_REQUIRED",
        "QUALITY_REQUIRED",
        "OPTIONAL_CONVENIENCE",
    }:
        return GateResult(False, "BLOCKED", "unknown trusted requirement_class")

    required_capability = None
    if requirement_class == "CAPABILITY_REQUIRED":
        required_capability = policy.get("required_capability")
        if not isinstance(required_capability, str) or not required_capability.strip():
            return GateResult(
                False,
                "REROUTE_REQUIRED",
                "capability-required action must resolve required_capability from acceptance",
            )
        required_capability = required_capability.strip().upper()

    # Driver Necessity/Re-use/Local decisions may only reduce external work
    # when backed by a current trusted economy decision bound to this action/owner.
    skip_claims = (
        ("necessity_decision_ref", "EXTERNAL_NOT_NECESSARY", "external call is unnecessary"),
        ("reuse_decision_ref", "REUSE_SUFFICIENT", "reusable evidence/context satisfies acceptance"),
        ("local_decision_ref", "LOCAL_SUFFICIENT", "local deterministic route satisfies acceptance"),
    )
    for field, decision_kind, reason in skip_claims:
        if field in call:
            ok, detail = _trusted_economy_decision(
                trusted,
                action,
                call.get(field),
                expected_kind=decision_kind,
                requirement_class=requirement_class,
                required_capability=required_capability,
            )
            if not ok:
                return GateResult(False, "BLOCKED", detail)
            skip_evidence = ["requirement-class:" + requirement_class]
            if required_capability:
                skip_evidence.append("required-capability:" + required_capability)
            skip_evidence.append("economy-decision:" + detail)
            return GateResult(
                True,
                "SKIP_CALL",
                reason,
                tuple(skip_evidence),
            )

    # Legacy/self-asserted skip booleans are an integrity violation, not evidence.
    if call.get("necessary") is False:
        return GateResult(False, "BLOCKED", "untrusted economy necessity claim")
    if call.get("reuse_available") is True or call.get("reuse_satisfies_acceptance") is True:
        return GateResult(False, "BLOCKED", "untrusted economy reuse claim")
    if call.get("local_sufficient") is True or call.get("local_meets_acceptance") is True:
        return GateResult(False, "BLOCKED", "untrusted economy local-sufficiency claim")

    if call.get("context") == "full" and trusted.get("context", {}).get("premise_loaded"):
        if not trusted.get("context", {}).get("full_reread_authorized"):
            return GateResult(False, "SKIP_FULL_REREAD", "full context reread blocked")

    if requirement_class == "QUALITY_REQUIRED":
        model_quality = policy.get("model_quality")
        minimum_quality = policy.get("minimum_quality")
        if not isinstance(model_quality, Mapping) or not isinstance(minimum_quality, int):
            return GateResult(False, "BLOCKED", "quality-required action needs a trusted quality floor")

    allowed_models = policy.get("allowed_models")
    if not isinstance(allowed_models, list) or not allowed_models:
        return GateResult(False, "BLOCKED", "trusted allowed_models missing")
    allowed_models = {_norm_token(v) for v in allowed_models if isinstance(v, str)}

    model = _norm_token(call.get("model"))
    if not model or model not in allowed_models:
        return GateResult(False, "REROUTE_LOWEST_SUFFICIENT", "requested model is not trusted for this action")
    if required_capability and not _model_has_capability(policy, model, required_capability):
        return GateResult(
            False,
            "REROUTE_LOWEST_SUFFICIENT",
            "requested model does not provide the trusted required capability",
        )

    model_quality = policy.get("model_quality")
    minimum_quality = policy.get("minimum_quality")
    if model_quality is not None or minimum_quality is not None:
        if not isinstance(model_quality, Mapping) or not isinstance(minimum_quality, int):
            return GateResult(False, "BLOCKED", "trusted acceptance-quality policy is malformed")
        normalized_quality = {
            _norm_token(name): score
            for name, score in model_quality.items()
            if isinstance(name, str) and isinstance(score, int)
        }
        selected_quality = normalized_quality.get(model)
        if selected_quality is None:
            return GateResult(False, "BLOCKED", "trusted quality score missing for requested model")
        if selected_quality < minimum_quality:
            return GateResult(
                False,
                "REROUTE_QUALITY_FLOOR",
                "lowest-cost route is below trusted acceptance quality floor",
            )

    expected_calls = call.get("expected_calls", 1)
    if not isinstance(expected_calls, int) or expected_calls < 1:
        return GateResult(False, "REROUTE_LOWEST_SUFFICIENT", "invalid expected_calls")

    max_calls = policy.get("max_calls", 1)
    if not isinstance(max_calls, int) or max_calls < 1:
        return GateResult(False, "BLOCKED", "trusted max_calls must be >= 1")

    billing_class, billing_error = _resolve_billing_class(policy, model)
    if billing_error:
        return GateResult(False, "BLOCKED", billing_error)
    assert billing_class is not None

    call_key = "cost:" + stable_hash(dict(call))
    approval = trusted_approval(trusted, call_key)
    approval_evidence = ["requirement-class:" + requirement_class]
    if required_capability:
        approval_evidence.append("required-capability:" + required_capability)
    approval_evidence.append("billing-class:" + billing_class)

    # SAVEY optimizes route cost after acceptance quality is protected.
    # A bounded subscription-quota call may proceed without per-call USER approval.
    # Real paid API spend, or an authority policy that explicitly demands approval,
    # still requires a trusted approval bound to this exact call.
    approval_required = (
        billing_class == "PAID_API"
        or (
            mode == "EXTERNAL_OPTIONAL"
            and policy.get("require_optional_approval") is True
        )
    )
    if approval_required:
        if not approval:
            reason = (
                "paid API call needs trusted approval"
                if billing_class == "PAID_API"
                else "optional external call policy requires trusted approval"
            )
            return GateResult(False, "USER_DECISION_REQUIRED", reason)
        approval_evidence.append("approval-key:" + call_key)

    if expected_calls > 1:
        return GateResult(
            False,
            "REROUTE_LOWEST_SUFFICIENT",
            "requested call count exceeds current single-invocation executor; batch workload and rerun",
        )

    effort = _norm_token(call.get("effort"))
    max_effort = _norm_token(policy.get("max_effort", "medium"))
    effort_rank = {"low": 1, "medium": 2, "high": 3, "xhigh": 4, "max": 5}
    if effort not in effort_rank or max_effort not in effort_rank:
        return GateResult(False, "BLOCKED", "invalid trusted/requested effort")

    allowed_efforts = policy.get("allowed_efforts")
    if allowed_efforts is not None:
        if not isinstance(allowed_efforts, list) or not allowed_efforts:
            return GateResult(False, "BLOCKED", "trusted allowed_efforts is malformed")
        normalized_efforts = {
            _norm_token(value)
            for value in allowed_efforts
            if isinstance(value, str)
        }
        if not normalized_efforts or any(value not in effort_rank for value in normalized_efforts):
            return GateResult(False, "BLOCKED", "trusted allowed_efforts contains invalid values")
        if effort not in normalized_efforts:
            return GateResult(
                False,
                "REROUTE_LOWEST_SUFFICIENT",
                "requested effort is not allowed for this action",
            )
    if effort_rank[effort] > effort_rank[max_effort]:
        if not approval:
            return GateResult(False, "REROUTE_LOWEST_SUFFICIENT", "requested effort exceeds trusted action policy")
        if "approval-key:" + call_key not in approval_evidence:
            approval_evidence.append("approval-key:" + call_key)

    batch_size = call.get("batch_size", 1)
    if not isinstance(batch_size, int) or batch_size < 1:
        return GateResult(False, "BLOCKED", "invalid batch_size")
    if batch_size > 1:
        if policy.get("allow_batch") is not True or policy.get("batch_safe") is not True:
            return GateResult(False, "REROUTE_LOWEST_SUFFICIENT", "batching is not trusted safe for this action")

    if call.get("parallel"):
        if policy.get("allow_parallel") is not True:
            key = "parallel:" + stable_hash(dict(call))
            if not trusted_approval(trusted, key):
                return GateResult(False, "REROUTE_LOWEST_SUFFICIENT", "parallel calls are not trusted for this action")
            approval_evidence.append("approval-key:" + key)
        elif policy.get("parallel_safe") is not True or policy.get("independent_items") is not True:
            return GateResult(False, "BLOCKED", "parallel execution lacks trusted safety/independence")

    if "retry_count" in call:
        return GateResult(False, "BLOCKED", "retry_count must come from trusted route ledger")
    max_retries = policy.get("max_retries", TRANSIENT_LIMIT - 1)
    if (
        not isinstance(max_retries, int)
        or max_retries < 0
        or max_retries >= TRANSIENT_LIMIT
    ):
        return GateResult(
            False,
            "BLOCKED",
            "trusted max_retries must stay below the hard transient retry limit",
        )
    if route_fp is not None:
        ledger = trusted.get("route_ledger", {})
        transient = ledger.get("transient_failures", {}) if isinstance(ledger, Mapping) else {}
        retry_count = transient.get(route_fp, 0) if isinstance(transient, Mapping) else 0
        if not isinstance(retry_count, int) or retry_count < 0:
            return GateResult(False, "BLOCKED", "trusted transient retry ledger is invalid")
        if retry_count > max_retries:
            return GateResult(False, "THROTTLE_HOLD", "retry count exceeds trusted throttle policy")

    if call.get("subagents") and policy.get("allow_subagents") is not True:
        key = "subagents:" + stable_hash(dict(call))
        if not trusted_approval(trusted, key):
            return GateResult(False, "REROUTE_LOWEST_SUFFICIENT", "subagents are not trusted for this action")
        approval_evidence.append("approval-key:" + key)

    return GateResult(
        True,
        "COST_OK",
        "trusted action call policy satisfied",
        tuple(approval_evidence),
    )


def cost_gate(
    trusted: Mapping[str, Any],
    action: Mapping[str, Any],
    call: Mapping[str, Any],
    *,
    evaluation: GateResult | None = None,
    route_fp: str | None = None,
) -> GateResult:
    return evaluation if isinstance(evaluation, GateResult) else evaluate_savey_ai_economy(
        trusted, action, call, route_fp=route_fp
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
    if not isinstance(receipt.get("semantic_owner_ref"), str) or not receipt.get("semantic_owner_ref").strip():
        return GateResult(False, "NOT_DONE", "preflight receipt semantic_owner_ref missing")
    if not isinstance(receipt.get("semantic_owner_scope"), str) or not receipt.get("semantic_owner_scope").strip():
        return GateResult(False, "NOT_DONE", "preflight receipt semantic_owner_scope missing")

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
    if completion.get("authority_digest") != receipt.get("authority_digest"):
        return GateResult(False, "NOT_DONE", "completion authority_digest mismatch")
    if completion.get("verification_tier") != receipt.get("verification_tier", "STANDARD"):
        return GateResult(False, "NOT_DONE", "completion verification_tier mismatch")
    if completion.get("semantic_owner_ref") != receipt.get("semantic_owner_ref"):
        return GateResult(False, "NOT_DONE", "completion semantic_owner_ref mismatch")
    if completion.get("semantic_owner_scope") != receipt.get("semantic_owner_scope"):
        return GateResult(False, "NOT_DONE", "completion semantic_owner_scope mismatch")

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

    completion_refs = completion.get("evidence_refs", [])
    if not isinstance(completion_refs, list) or not completion_refs:
        return GateResult(False, "NOT_DONE", "completion evidence bindings missing")
    if not set(completion_refs).issubset(set(refs)):
        return GateResult(False, "NOT_DONE", "report omits completion-bound evidence")

    verification_evidence = completion.get("verification_evidence", {})
    if not isinstance(verification_evidence, Mapping):
        return GateResult(False, "BLOCKED", "verification predicate bindings missing")
    missing_predicates = sorted(required - set(verification_evidence))
    if missing_predicates:
        return GateResult(
            False,
            "BLOCKED",
            "verification predicates lack evidence bindings: " + ",".join(missing_predicates),
        )

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

        evidence_type = item.get("evidence_type", item.get("type"))
        if item.get("verified") is not True or evidence_type not in VALID_EVIDENCE_TYPES:
            return GateResult(False, "NOT_DONE", f"evidence not verified: {ref}")
        if item.get("acceptance_state") != ACCEPTED_EVIDENCE_STATE:
            state = item.get("acceptance_state")
            if state in REJECTED_EVIDENCE_STATES:
                return GateResult(False, "NOT_DONE", f"evidence acceptance rejected: {ref}:{state}")
            return GateResult(False, "NOT_DONE", f"evidence acceptance state missing: {ref}")
        if item.get("authority_digest_or_key_version") != receipt.get("authority_digest"):
            return GateResult(False, "NOT_DONE", f"evidence authority mismatch: {ref}")
        if item.get("semantic_owner_ref") != receipt.get("semantic_owner_ref"):
            return GateResult(False, "NOT_DONE", f"evidence semantic_owner_ref mismatch: {ref}")
        if item.get("semantic_owner_scope") != receipt.get("semantic_owner_scope"):
            return GateResult(False, "NOT_DONE", f"evidence semantic_owner_scope mismatch: {ref}")
        receipt_scope = receipt.get("execution_scope")
        if isinstance(receipt_scope, str) and receipt_scope:
            if item.get("scope") != receipt_scope:
                return GateResult(False, "NOT_DONE", f"evidence scope mismatch: {ref}")
        if item.get("verification_tier") != receipt.get("verification_tier", "STANDARD"):
            return GateResult(False, "NOT_DONE", f"evidence verification tier mismatch: {ref}")
        if item.get("source_status") in {"SUPERSEDED", "STALE"}:
            return GateResult(False, "NOT_DONE", f"stale/superseded evidence cannot prove current claim: {ref}")
        if not isinstance(item.get("claim_supported"), str) or not item.get("claim_supported").strip():
            return GateResult(False, "NOT_DONE", f"evidence claim binding missing: {ref}")
        if not isinstance(item.get("source_or_artifact_ref"), str) or not item.get("source_or_artifact_ref").strip():
            return GateResult(False, "NOT_DONE", f"evidence artifact/source ref missing: {ref}")
        producer = item.get("producer")
        validator = item.get("validator")
        if not isinstance(producer, str) or not producer.strip():
            return GateResult(False, "NOT_DONE", f"evidence producer missing: {ref}")
        if not isinstance(validator, str) or not validator.strip():
            return GateResult(False, "NOT_DONE", f"evidence validator missing: {ref}")
        if receipt.get("verification_tier") == "STRONG":
            if producer.strip() == validator.strip():
                return GateResult(False, "PARTIAL", f"STRONG evidence lacks independent validator: {ref}")
            orchestration = receipt.get("orchestration", {})
            expected_review_role = (
                orchestration.get("independent_reviewer_role")
                if isinstance(orchestration, Mapping)
                else None
            )
            expected_review_actor = (
                orchestration.get("independent_reviewer_actor")
                if isinstance(orchestration, Mapping)
                else None
            )
            if expected_review_role and item.get("independent_reviewer_role") != expected_review_role:
                return GateResult(False, "PARTIAL", f"STRONG independent reviewer role missing: {ref}")
            if expected_review_actor and item.get("independent_reviewer_actor") != expected_review_actor:
                return GateResult(False, "PARTIAL", f"STRONG independent reviewer actor missing: {ref}")
        verified_refs.append(str(ref))

    verified_ref_set = set(verified_refs)
    for predicate in required:
        bound_ref = verification_evidence.get(predicate)
        if not isinstance(bound_ref, str) or bound_ref not in verified_ref_set:
            return GateResult(
                False,
                "NOT_DONE",
                f"verification predicate evidence not accepted: {predicate}",
            )
        if predicate == "intent":
            intent_item = registry.get(bound_ref)
            if intent_item.get("claim_supported") in {
                "installation", "extension_installed", "build_pass", "syntax_pass",
                "unit_tests_pass", "implementation_complete",
            }:
                return GateResult(
                    False, "NOT_DONE",
                    "installation/build-only evidence cannot prove user intent",
                )
        if predicate == "independent":
            independent_item = registry.get(bound_ref)
            if not isinstance(independent_item, Mapping):
                return GateResult(False, "PARTIAL", "independent review evidence missing")
            independent_type = independent_item.get("evidence_type", independent_item.get("type"))
            if independent_type != "independent_review":
                return GateResult(False, "PARTIAL", "independent predicate lacks independent review artifact")
            review_registry = trusted.get("independent_review_registry", {})
            review = (
                review_registry.get(bound_ref)
                if isinstance(review_registry, Mapping)
                else None
            )
            if (
                not isinstance(review, Mapping)
                or review.get("acceptance_state") != ACCEPTED_EVIDENCE_STATE
                or review.get("receipt_id") != receipt_id
                or review.get("authority_digest") != receipt.get("authority_digest")
            ):
                return GateResult(False, "PARTIAL", "independent review receipt not accepted/bound")

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
