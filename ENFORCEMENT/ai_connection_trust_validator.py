#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = (
    "server_id","purpose","transport","protocol_revision","version",
    "version_verification_state","source_trust","allowed_tools","denied_tools",
    "action_scope","auth_method","issuer","audience","scopes",
    "credential_binding","token_passthrough","data_sensitivity","cost_class",
    "approval_class","timeout_seconds","rate_or_budget_ceiling",
    "last_verify","reverify_after","trust_state",
)
REMOTE_TRANSPORTS = {"http", "sse"}
KNOWN_TRANSPORTS = {"stdio", "http", "sse", "other"}
KNOWN_VERSION_STATES = {"PINNED_CONFIG", "VERIFIED_RUNTIME", "UNVERIFIED", "UNKNOWN"}
KNOWN_CREDENTIAL_BINDINGS = {"LOCAL_PROCESS", "HOST_MANAGED", "ACCOUNT_SESSION", "UNKNOWN", "NONE"}
KNOWN_TRUST_STATES = {"TRUSTED_BOUNDED", "CONDITIONAL", "UNVERIFIED_REMOTE", "DISABLED"}
APPROVAL_CLASS_COVERAGE = {
    "HIGH_IMPACT_REQUIRES_EXPLICIT_APPROVAL": {"HIGH_IMPACT"},
    "PRODUCTION_DEPLOY_ALWAYS_REQUIRES_EXPLICIT_APPROVAL": {
        "PRODUCTION",
        "HIGH_IMPACT",
    },
    "COST_OR_WRITE_REQUIRES_EXPLICIT_APPROVAL": {
        "COST",
        "WRITE",
        "ACCOUNT_STATE",
        "GENERATION_WORKFLOW",
        "HIGH_IMPACT",
    },
}


def _required_approval_domains(entry: dict) -> set[str]:
    gate = str(entry.get("approval_gate") or "").lower()
    action_scope = str(entry.get("action_scope") or "").upper()
    cost = str(entry.get("cost") or entry.get("cost_class") or "").upper()
    required: set[str] = set()
    if "production deploy" in gate or "publish" in gate:
        required.add("PRODUCTION")
    if any(word in gate for word in ("write", "delete", "model", "workflow")):
        required.add("WRITE")
    if "METERED" in cost:
        required.add("COST")
    if "ACCOUNT_STATE" in action_scope:
        required.add("ACCOUNT_STATE")
    if "GENERATION_WORKFLOW" in action_scope:
        required.add("GENERATION_WORKFLOW")
    if "HIGH_IMPACT" in action_scope or "high-impact" in gate or "REMOTE_STATE" in action_scope:
        required.add("HIGH_IMPACT")
    return required


def _approval_coverage(entry: dict) -> set[str]:
    approval = str(entry.get("approval_class") or "").upper()
    return set(APPROVAL_CLASS_COVERAGE.get(approval, set()))


def _manifest_has_explicit_approval(entry: dict) -> bool:
    return bool(_approval_coverage(entry))


def validate(manifest: dict, audit: dict) -> dict:
    detected: list[str] = []
    if not isinstance(manifest, dict):
        return {"pass": False, "detected": ["TRUST_MANIFEST_INVALID"]}
    if manifest.get("owner") != "OS/AI_CONNECTION_SECURITY.md":
        detected.append("TRUST_MANIFEST_OWNER_MISMATCH")
    if manifest.get("projection_role") != "NON_SEMANTIC_TRUST_PROJECTION":
        detected.append("TRUST_MANIFEST_ROLE_INVALID")

    connections = manifest.get("connections")
    if not isinstance(connections, list) or not connections:
        return {"pass": False, "detected": detected + ["TRUST_MANIFEST_CONNECTIONS_INVALID"]}

    audit_connections = audit.get("connections") if isinstance(audit, dict) else None
    if not isinstance(audit_connections, list):
        detected.append("CONNECTION_AUDIT_INVALID")
        audit_connections = []

    audit_by_id: dict[str, dict] = {}
    audit_duplicates: set[str] = set()
    for item in audit_connections:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        sid = item["id"]
        if sid in audit_by_id:
            audit_duplicates.add(sid)
        audit_by_id[sid] = item
    for sid in sorted(audit_duplicates):
        detected.append(f"CONNECTION_AUDIT_DUPLICATE:{sid}")
    audit_ids = set(audit_by_id)
    seen: set[str] = set()
    manifest_ids: set[str] = set()

    for entry in connections:
        if not isinstance(entry, dict):
            detected.append("TRUST_CONNECTION_ENTRY_INVALID")
            continue
        sid = entry.get("server_id")
        if not isinstance(sid, str) or not sid.strip():
            detected.append("TRUST_CONNECTION_SERVER_ID_MISSING")
            continue
        sid = sid.strip()
        if sid in seen:
            detected.append(f"TRUST_CONNECTION_DUPLICATE:{sid}")
        seen.add(sid)
        manifest_ids.add(sid)

        for key in REQUIRED:
            if key not in entry:
                detected.append(f"TRUST_FIELD_MISSING:{sid}:{key}")

        transport = entry.get("transport")
        version_state = entry.get("version_verification_state")
        credential_binding = entry.get("credential_binding")
        trust_state = entry.get("trust_state")
        token_passthrough = entry.get("token_passthrough")

        if transport not in KNOWN_TRANSPORTS:
            detected.append(f"TRUST_TRANSPORT_INVALID:{sid}")
        if version_state not in KNOWN_VERSION_STATES:
            detected.append(f"TRUST_VERSION_STATE_INVALID:{sid}")
        if credential_binding not in KNOWN_CREDENTIAL_BINDINGS:
            detected.append(f"TRUST_CREDENTIAL_BINDING_INVALID:{sid}")
        if trust_state not in KNOWN_TRUST_STATES:
            detected.append(f"TRUST_STATE_INVALID:{sid}")
        if token_passthrough is not False and token_passthrough != "UNKNOWN":
            detected.append(f"TOKEN_PASSTHROUGH_FORBIDDEN:{sid}")

        if transport in REMOTE_TRANSPORTS and trust_state == "TRUSTED_BOUNDED":
            version = str(entry.get("version") or "").strip()
            auth_method = str(entry.get("auth_method") or "").strip()
            source_trust = str(entry.get("source_trust") or "").strip().upper()
            remote_trust_ok = (
                bool(version)
                and version.upper() not in {"UNKNOWN", "UNVERIFIED"}
                and version_state in {"PINNED_CONFIG", "VERIFIED_RUNTIME"}
                and bool(auth_method)
                and auth_method.upper() not in {"UNKNOWN", "UNVERIFIED", "NONE"}
                and credential_binding not in {"UNKNOWN", "NONE"}
                and token_passthrough is False
                and bool(source_trust)
                and source_trust not in {"UNKNOWN", "UNVERIFIED"}
                and "UNVERIFIED" not in source_trust
            )
            if not remote_trust_ok:
                detected.append(f"REMOTE_TRUST_OVERCLAIM:{sid}")

        cost_class = str(entry.get("cost_class") or "")
        approval_class = str(entry.get("approval_class") or "")
        coverage = _approval_coverage(entry)
        if approval_class.upper() not in APPROVAL_CLASS_COVERAGE:
            detected.append(f"APPROVAL_CLASS_INVALID:{sid}")
        if "METERED" in cost_class and "COST" not in coverage:
            detected.append(f"METERED_COST_APPROVAL_MISSING:{sid}")

        action_scope = str(entry.get("action_scope") or "")
        if any(k in action_scope for k in ("REMOTE_STATE", "ACCOUNT_STATE", "HIGH_IMPACT")):
            if not coverage:
                detected.append(f"HIGH_IMPACT_APPROVAL_MISSING:{sid}")

        allowed = entry.get("allowed_tools")
        denied = entry.get("denied_tools")
        scopes = entry.get("scopes")
        if not isinstance(allowed, list) or any(not isinstance(x, str) or not x.strip() for x in allowed):
            detected.append(f"ALLOWED_TOOLS_INVALID:{sid}")
        if not isinstance(denied, list) or any(not isinstance(x, str) or not x.strip() for x in denied):
            detected.append(f"DENIED_TOOLS_INVALID:{sid}")
        if not isinstance(scopes, list) or any(not isinstance(x, str) for x in scopes):
            detected.append(f"AUTH_SCOPES_INVALID:{sid}")

        source = audit_by_id.get(sid)
        if source is None:
            continue

        exact_pairs = (
            ("purpose", "purpose"),
            ("transport", "transport"),
            ("action_scope", "action_scope"),
            ("cost_class", "cost"),
            ("last_verify", "last_verify"),
        )
        for manifest_key, audit_key in exact_pairs:
            if source.get(audit_key) is not None and entry.get(manifest_key) != source.get(audit_key):
                detected.append(f"TRUST_PROJECTION_SEMANTIC_DRIFT:{sid}:{manifest_key}")

        if source.get("version") is not None and entry.get("version") != source.get("version"):
            detected.append(f"TRUST_PROJECTION_SEMANTIC_DRIFT:{sid}:version")
        if source.get("source_trust") is not None and entry.get("source_trust") != source.get("source_trust"):
            detected.append(f"TRUST_PROJECTION_SEMANTIC_DRIFT:{sid}:source_trust")
        if source.get("auth_method") is not None and entry.get("auth_method") != source.get("auth_method"):
            detected.append(f"TRUST_PROJECTION_SEMANTIC_DRIFT:{sid}:auth_method")
        required_domains = _required_approval_domains(source)
        if not required_domains.issubset(_approval_coverage(entry)):
            detected.append(f"TRUST_PROJECTION_APPROVAL_DOWNGRADE:{sid}")

    missing = sorted(audit_ids - manifest_ids)
    extra = sorted(manifest_ids - audit_ids)
    for sid in missing:
        detected.append(f"TRUST_PROJECTION_MISSING_CONNECTION:{sid}")
    for sid in extra:
        detected.append(f"TRUST_PROJECTION_UNKNOWN_CONNECTION:{sid}")

    return {
        "pass": not detected,
        "detected": list(dict.fromkeys(detected)),
        "audit_connection_count": len(audit_ids),
        "manifest_connection_count": len(manifest_ids),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=Path("OS/AI_CONNECTION_TRUST_MANIFEST.json"))
    ap.add_argument("--audit", type=Path, default=Path("OS/AI_CONNECTION_AUDIT.json"))
    args = ap.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        audit = json.loads(args.audit.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        result = {"pass": False, "detected": [f"TRUST_INPUT_UNREADABLE:{type(exc).__name__}"]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    result = validate(manifest, audit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
