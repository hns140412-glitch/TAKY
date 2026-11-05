#!/usr/bin/env python3
"""TAKY app-to-Drive route CONTRACT (not an authenticated API implementation).

Only trusted server-side callers can request a plan. Real authentication, ACL readback
and data mutations must be implemented and verified in the calling backend.
Never return a direct Drive URL or credentials to a browser.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

_resolver_path = Path(__file__).with_name("drive_route_resolver.py")
_spec = importlib.util.spec_from_file_location("taky_drive_route_resolver", _resolver_path)
_resolver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_resolver)

# Existing Drive folder IDs are resolved from OS/DRIVE_STORAGE_MAP.json.
# These are service-side logical actions, NOT client endpoints.
ACTION_ROLE = {
    "HOMEWORK_READ": ("siezeall", "04_USER_DATA", "read", "user"),
    "HOMEWORK_WRITE": ("siezeall", "04_USER_DATA", "write", "user"),
    "HOMEWORK_UPLOAD": ("siezeall", "04_USER_DATA", "write", "user"),
    "LEARNING_EVIDENCE_WRITE": ("siezeall", "04_USER_DATA", "write", "user"),
    "USER_RECORD_READ": ("siezeall", "04_USER_DATA", "read", "user"),
    "USER_RECORD_WRITE": ("siezeall", "04_USER_DATA", "write", "user"),
    "FAMILY_SHARE_MANAGE": ("siezeall", "04_USER_DATA", "write", "user"),
    "CONTENT_CATALOG_READ": ("siezeall", "03_UPDATES", "read", "service"),
    "CONTENT_PACKAGE_PUBLISH": ("siezeall", "03_UPDATES", "write", "operator"),
    "OPERATION_CONFIG_READ": ("hns", "03_COMMON", "read", "operator"),
    "APPROVED_VISUAL_MASTER_READ": ("hns", "UI_SOURCE_AUTHORITY", "read", "operator"),
}

class RouteBlocked(ValueError):
    pass

def unsafe_public_acl(permissions, *, role):
    if not isinstance(permissions, list) or not permissions:
        raise RouteBlocked("ACL_READBACK_REQUIRED")
    return any(
        isinstance(p, dict)
        and p.get("type") == "anyone"
        and (role == "04_USER_DATA" or p.get("role") in {"owner", "writer", "commenter", "organizer", "fileOrganizer"})
        for p in permissions
    )

def plan_app_operation(action, *, caller, verified_identity=False, owner_user_id=None,
                       approved_operator=False, acl_permissions=None, owner_scope_verified=False):
    """Return a STORAGE ROUTE PLAN, never Drive access authorization.
    
    The caller must separately enforce user authentication, record-level ACL,
    idempotency/version checks and scoped data operations. Missing effective ACL readback
    blocks all sensitive route plans; unsafe public write blocks every operation.
    """
    if caller != "TRUSTED_APP_BACKEND":
        raise RouteBlocked("USER_DIRECT_DRIVE_FORBIDDEN")
    action = str(action).upper()
    if action not in ACTION_ROLE:
        raise RouteBlocked("UNKNOWN_ACTION")
    account, role, access, kind = ACTION_ROLE[action]
    if not verified_identity:
        raise RouteBlocked("APP_IDENTITY_UNVERIFIED")
    if kind == "user" and (not owner_user_id or not owner_scope_verified):
        raise RouteBlocked("USER_SCOPE_UNVERIFIED")
    if kind == "operator" and not approved_operator:
        raise RouteBlocked("OPERATOR_AUTHORITY_REQUIRED")
    if unsafe_public_acl(acl_permissions, role=role):
        raise RouteBlocked("UNSAFE_PUBLIC_DRIVE_ACL")
    r = _resolver.resolve(account, role)
    if not r.get("id"):
        raise RouteBlocked("DRIVE_FOLDER_ID_UNRESOLVED")
    return {
        "route_state": "SERVER_SIDE_PLAN_ONLY_NOT_ACCESS_AUTHORIZATION",
        "action": action,
        "storage_account": r["account"],
        "role": r["role"],
        "drive_folder_id": r["id"],
        "access": access,
        "no_direct_drive_client": True,
        "requires_backend_record_acl": kind == "user",
        "requires_mutation_journal": access == "write",
        "requires_remote_acl_readback": True,
    }
