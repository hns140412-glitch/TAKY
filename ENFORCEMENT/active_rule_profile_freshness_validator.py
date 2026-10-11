#!/usr/bin/env python3
"""Validate freshness of the non-semantic ACTIVE_RULE_PROFILE projection."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

REQUIRED_HEADERS = (
    "PROFILE_VERSION",
    "SOURCE_REPOSITORY",
    "SOURCE_CANONICAL_HEAD",
    "SOURCE_STATE",
    "SOURCE_OWNER_PATHS",
    "SOURCE_OWNER_FINGERPRINT",
    "GENERATED_AT",
    "STATUS",
)
ALLOWED_SOURCE_STATES = {"WORKTREE_DERIVED", "COMMITTED_SNAPSHOT"}
PROFILE_BINDING_ROLE = "CANONICAL_REVIEW_ATTESTATION"
PROFILE_REVIEW_BASIS = "OWNER_TO_PROJECTION_SEMANTIC_REVIEW"
PROFILE_REVIEWER_ROLE = "TAKY_VALIDATOR"
PROFILE_ATTESTATION_VERSION = "1.0"

# Mechanical minimum coverage independent from the projection being checked.
# These owners materially define rules currently projected in ACTIVE_RULE_PROFILE.
REQUIRED_OWNER_PATHS = {
    "TAKY.md",
    "AGENTS.md",
    "MASTER/ENFORCEMENT_PROTOCOL.md",
    "MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md",
    "MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md",
    "MASTER/VALIDATION_RULES.md",
    "MASTER/RULE_REGISTRY.json",
    "MASTER/OUTCOME_OPTIMIZATION_PROTOCOL.md",
    "MASTER/INTENT_EXECUTION_PROTOCOL.md",
    "OS/AI_CONNECTION_SECURITY.md",
    "OS/DEPLOYMENT_OPS.md",
    "OS/SAVEY_AI_ECONOMY.md",
    "OS/WORKSTATION_CONTROL.md",
}


def parse_headers(text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in REQUIRED_HEADERS:
            headers[key] = value.strip()
    return headers


def duplicate_headers(text: str) -> list[str]:
    counts = {key: 0 for key in REQUIRED_HEADERS}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key = line.split(":", 1)[0].strip()
        if key in counts:
            counts[key] += 1
    return [key for key, count in counts.items() if count > 1]


def owner_paths(headers: dict[str, str]) -> list[str]:
    raw = headers.get("SOURCE_OWNER_PATHS", "")
    return [x.strip().replace("\\", "/") for x in raw.split(";") if x.strip()]


def _owner_bytes(candidate: Path, rel: str) -> bytes:
    if rel == "MASTER/RULE_REGISTRY.json":
        try:
            registry = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except Exception:
            return candidate.read_bytes()
        if isinstance(registry, dict):
            semantic = dict(registry)
            semantic.pop("projection_bindings", None)
            return (
                json.dumps(
                    semantic,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode("utf-8")
    return candidate.read_bytes()


def projection_body_hash(text: str) -> str:
    body_lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = raw.strip()
        if stripped == "[TAKY_ACTIVE_RULE_PROFILE]":
            continue
        if ":" in raw:
            key = raw.split(":", 1)[0].strip()
            if key in REQUIRED_HEADERS:
                continue
        body_lines.append(raw.rstrip())
    while body_lines and body_lines[-1] == "":
        body_lines.pop()
    payload = ("\n".join(body_lines) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _canonical_object_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_review_attestation(
    repo_root: Path,
    binding: dict,
    *,
    profile_key: str,
    owner_fp: str | None,
    body_hash: str,
    source_head: str | None,
) -> tuple[dict | None, list[str]]:
    failures: list[str] = []
    ref = binding.get("review_attestation_ref")
    expected_file_hash = binding.get("review_attestation_sha256")
    if not isinstance(ref, str) or not ref.strip():
        return None, ["ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_REF_MISSING"]
    if not isinstance(expected_file_hash, str) or not expected_file_hash.startswith("sha256:"):
        return None, ["ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_HASH_MISSING"]

    root = repo_root.resolve()
    path = (repo_root / ref).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None, ["ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_PATH_INVALID"]
    rel = path.relative_to(root).as_posix()
    if not rel.startswith("HISTORY/PROJECTION_ATTESTATIONS/"):
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_NOT_HISTORY_BOUND")
    if not path.is_file():
        return None, failures + ["ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_MISSING"]
    if _file_sha256(path) != expected_file_hash:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_FILE_HASH_MISMATCH")
    try:
        receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None, failures + ["ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_UNREADABLE"]
    if not isinstance(receipt, dict):
        return None, failures + ["ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_INVALID"]

    if receipt.get("attestation_version") != PROFILE_ATTESTATION_VERSION:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_VERSION_INVALID")
    if receipt.get("binding_role") != PROFILE_BINDING_ROLE:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_ROLE_INVALID")
    if receipt.get("profile_path") != profile_key:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_PROFILE_MISMATCH")
    if receipt.get("source_owner_fingerprint") != owner_fp:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_OWNER_MISMATCH")
    if receipt.get("projection_body_hash") != body_hash:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_BODY_MISMATCH")
    if receipt.get("source_canonical_head") != source_head:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_HEAD_MISMATCH")
    if receipt.get("review_basis") != PROFILE_REVIEW_BASIS:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_BASIS_INVALID")
    if receipt.get("reviewer_role") != PROFILE_REVIEWER_ROLE:
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_REVIEWER_INVALID")
    if receipt.get("review_result") != "PASS":
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_NOT_PASS")
    if not isinstance(receipt.get("reviewed_at"), str) or not receipt.get("reviewed_at", "").strip():
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_TIME_MISSING")

    stored_hash = receipt.get("attestation_hash")
    core = dict(receipt)
    core.pop("attestation_hash", None)
    if stored_hash != _canonical_object_hash(core):
        failures.append("ACTIVE_RULE_PROFILE_REVIEW_ATTESTATION_INTEGRITY_MISMATCH")
    return receipt, failures


def owner_fingerprint(repo_root: Path, paths: list[str]) -> tuple[str | None, list[str]]:
    failures: list[str] = []
    root = repo_root.resolve()
    rows: list[str] = []
    for rel in sorted(paths):
        candidate = (repo_root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            failures.append(f"ACTIVE_RULE_PROFILE_OWNER_PATH_ESCAPES_REPO:{rel}")
            continue
        if not candidate.is_file():
            failures.append(f"ACTIVE_RULE_PROFILE_OWNER_MISSING:{rel}")
            continue
        digest = hashlib.sha256(_owner_bytes(candidate, rel)).hexdigest()
        rows.append(f"{rel}\0{digest}\n")
    if failures:
        return None, failures
    payload = "".join(rows).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest(), []


def git_head(repo_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    return proc.stdout.strip()


def git_is_ancestor(repo_root: Path, source_head: str, current_head: str) -> bool | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", source_head, current_head],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except Exception:
        return None
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def validate(repo_root: Path, profile_path: Path, *, current_head: str | None = None) -> dict:
    failures: list[str] = []
    try:
        text = profile_path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return {
            "pass": False,
            "detected": [f"ACTIVE_RULE_PROFILE_UNREADABLE:{type(exc).__name__}"],
        }

    headers = parse_headers(text)
    for key in REQUIRED_HEADERS:
        if not headers.get(key):
            failures.append(f"ACTIVE_RULE_PROFILE_HEADER_MISSING:{key}")
    for key in duplicate_headers(text):
        failures.append(f"ACTIVE_RULE_PROFILE_HEADER_DUPLICATE:{key}")

    state = headers.get("SOURCE_STATE")
    if state and state not in ALLOWED_SOURCE_STATES:
        failures.append("ACTIVE_RULE_PROFILE_SOURCE_STATE_INVALID")

    paths = owner_paths(headers)
    if not paths:
        failures.append("ACTIVE_RULE_PROFILE_OWNER_PATHS_EMPTY")
        actual_fp = None
    else:
        missing_required = sorted(REQUIRED_OWNER_PATHS - set(paths))
        for rel in missing_required:
            failures.append(f"ACTIVE_RULE_PROFILE_REQUIRED_OWNER_MISSING:{rel}")
        actual_fp, fp_failures = owner_fingerprint(repo_root, paths)
        failures.extend(fp_failures)

    expected_fp = headers.get("SOURCE_OWNER_FINGERPRINT")
    if actual_fp is not None and expected_fp != actual_fp:
        failures.append("ACTIVE_RULE_PROFILE_OWNER_FINGERPRINT_STALE")

    body_hash = projection_body_hash(text)
    source_head = headers.get("SOURCE_CANONICAL_HEAD")
    profile_key = None
    try:
        profile_key = profile_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        failures.append("ACTIVE_RULE_PROFILE_PATH_OUTSIDE_REPO")

    binding = None
    review_attestation = None
    registry_path = repo_root / "MASTER" / "RULE_REGISTRY.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    except Exception:
        failures.append("ACTIVE_RULE_PROFILE_ATTESTATION_REGISTRY_UNREADABLE")
        registry = {}
    bindings = registry.get("projection_bindings") if isinstance(registry, dict) else None
    if not isinstance(bindings, dict):
        failures.append("ACTIVE_RULE_PROFILE_ATTESTATION_BINDINGS_MISSING")
    elif profile_key:
        binding = bindings.get(profile_key)
        if not isinstance(binding, dict):
            failures.append("ACTIVE_RULE_PROFILE_ATTESTATION_MISSING")
        else:
            if binding.get("binding_role") != PROFILE_BINDING_ROLE:
                failures.append("ACTIVE_RULE_PROFILE_ATTESTATION_ROLE_INVALID")
            if binding.get("source_owner_fingerprint") != actual_fp:
                failures.append("ACTIVE_RULE_PROFILE_SOURCE_ATTESTATION_MISMATCH")
            if binding.get("projection_body_hash") != body_hash:
                failures.append("ACTIVE_RULE_PROFILE_BODY_ATTESTATION_MISMATCH")
            review_attestation, review_failures = _validate_review_attestation(
                repo_root,
                binding,
                profile_key=profile_key,
                owner_fp=actual_fp,
                body_hash=body_hash,
                source_head=source_head,
            )
            failures.extend(review_failures)

    head = current_head if current_head is not None else git_head(repo_root)
    source_head_is_ancestor = None
    if not head:
        failures.append("ACTIVE_RULE_PROFILE_GIT_HEAD_UNAVAILABLE")
    elif not source_head:
        failures.append("ACTIVE_RULE_PROFILE_BASE_HEAD_STALE")
    elif source_head == head:
        source_head_is_ancestor = True
    else:
        source_head_is_ancestor = git_is_ancestor(repo_root, source_head, head)
        if source_head_is_ancestor is not True:
            failures.append("ACTIVE_RULE_PROFILE_BASE_HEAD_STALE")

    status = headers.get("STATUS", "")
    if "NON_SEMANTIC_OWNER" not in status:
        failures.append("ACTIVE_RULE_PROFILE_STATUS_OWNER_BOUNDARY_INVALID")

    return {
        "pass": not failures,
        "detected": list(dict.fromkeys(failures)),
        "source_state": state,
        "source_head": source_head,
        "current_head": head,
        "source_head_is_ancestor": source_head_is_ancestor,
        "expected_owner_fingerprint": expected_fp,
        "actual_owner_fingerprint": actual_fp,
        "projection_body_hash": body_hash,
        "profile_key": profile_key,
        "attestation": binding,
        "review_attestation": review_attestation,
        "owner_paths": paths,
        "required_owner_paths": sorted(REQUIRED_OWNER_PATHS),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument(
        "--profile",
        type=Path,
        default=Path("PROJECTIONS/ACTIVE_RULE_PROFILE.md"),
    )
    ap.add_argument("--print-fingerprint", action="store_true")
    args = ap.parse_args()

    if args.print_fingerprint:
        text = args.profile.read_text(encoding="utf-8-sig")
        headers = parse_headers(text)
        fp, failures = owner_fingerprint(args.repo_root, owner_paths(headers))
        result = {
            "pass": not failures,
            "detected": failures,
            "fingerprint": fp,
            "projection_body_hash": projection_body_hash(text),
        }
    else:
        result = validate(args.repo_root, args.profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
