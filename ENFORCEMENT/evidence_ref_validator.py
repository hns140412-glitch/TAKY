#!/usr/bin/env python3
"""Validate TAKY preflight evidence references.

Repository-file evidence is verified against actual bytes in the checked-out repository.
Repository-commit evidence is verified against actual git history and, by default, must be
an ancestor of HEAD. History-query evidence must additionally prove relevance to canonical
HISTORY content. External/session evidence cannot be independently re-fetched here; it must
carry stable provenance metadata and remains STRUCTURED_EXTERNAL_EVIDENCE, not
LIVE_RUNTIME_VERIFIED.
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

HEX64 = re.compile(r"^[0-9a-f]{64}$", re.I)
HEX40 = re.compile(r"^[0-9a-f]{40}$", re.I)
ALLOWED_KINDS = {"repo_file","repo_commit","conversation","handoff","drive","notion","runtime_log","other_external"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_ok(repo_root: Path, *args: str) -> bool:
    try:
        p = subprocess.run(
            ["git", *args], cwd=repo_root, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, check=False
        )
        return p.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def validate_ref(ref: Dict[str, Any], repo_root: Path) -> Tuple[bool, str]:
    if not isinstance(ref, dict): return False, "REF_NOT_OBJECT"
    kind = str(ref.get("source_kind", ""))
    if kind not in ALLOWED_KINDS: return False, "SOURCE_KIND_INVALID"
    source_id = str(ref.get("source_id", "")).strip()
    if not source_id: return False, "SOURCE_ID_MISSING"

    if kind == "repo_file":
        rel = str(ref.get("path", "")).strip()
        digest = str(ref.get("sha256", "")).strip().lower()
        if not rel or not HEX64.match(digest): return False, "REPO_FILE_EVIDENCE_INCOMPLETE"
        p = (repo_root / rel).resolve()
        try: p.relative_to(repo_root.resolve())
        except ValueError: return False, "REPO_PATH_ESCAPE"
        if not p.is_file(): return False, "REPO_FILE_MISSING"
        if sha256_file(p) != digest: return False, "REPO_FILE_HASH_MISMATCH"
        return True, "VERIFIED_REPO_FILE"

    if kind == "repo_commit":
        commit = str(ref.get("commit_sha", "")).strip().lower()
        if not HEX40.match(commit): return False, "REPO_COMMIT_SHA_INVALID"
        if not (repo_root / ".git").exists(): return False, "REPO_GIT_METADATA_MISSING"
        if not git_ok(repo_root, "cat-file", "-e", f"{commit}^{{commit}}"):
            return False, "REPO_COMMIT_NOT_FOUND"
        require_ancestor = ref.get("require_ancestor_of_head", True)
        if bool(require_ancestor) and not git_ok(repo_root, "merge-base", "--is-ancestor", commit, "HEAD"):
            return False, "REPO_COMMIT_NOT_HEAD_ANCESTOR"
        return True, "VERIFIED_REPO_COMMIT"

    digest = str(ref.get("content_sha256", "")).strip().lower()
    immutable_revision = str(ref.get("immutable_revision", "")).strip()
    captured_at = str(ref.get("captured_at", "")).strip()
    if not captured_at: return False, "CAPTURE_TIME_MISSING"
    if not (HEX64.match(digest) or immutable_revision):
        return False, "EXTERNAL_EVIDENCE_IMMUTABILITY_MISSING"
    return True, "STRUCTURED_EXTERNAL_EVIDENCE"


def validate_history_relevance(ref: Dict[str, Any], repo_root: Path) -> Tuple[bool, str]:
    """History evidence must point to canonical HISTORY content, not merely a valid SHA."""
    kind = str(ref.get("source_kind", ""))
    if kind == "repo_file":
        rel = str(ref.get("path", "")).strip()
        if not rel.startswith("HISTORY/"):
            return False, "HISTORY_PATH_OUTSIDE_CANONICAL_HISTORY"
        return True, "VERIFIED_HISTORY_FILE"

    if kind == "repo_commit":
        commit = str(ref.get("commit_sha", "")).strip().lower()
        paths = ref.get("evidence_paths", [])
        if not isinstance(paths, list) or not paths:
            return False, "HISTORY_EVIDENCE_PATHS_MISSING"
        for raw in paths:
            rel = str(raw).strip()
            if not rel.startswith("HISTORY/"):
                return False, "HISTORY_PATH_OUTSIDE_CANONICAL_HISTORY"
            if not git_ok(repo_root, "cat-file", "-e", f"{commit}:{rel}"):
                return False, "HISTORY_EVIDENCE_PATH_NOT_IN_COMMIT"
        return True, "VERIFIED_HISTORY_COMMIT_PATHS"

    return False, "HISTORY_EVIDENCE_NOT_CANONICAL"


def validate_manifest(manifest: Dict[str, Any], repo_root: Path) -> List[str]:
    failures: List[str] = []
    for bucket in ("applicable_rule_refs","context_evidence_refs","history_query_refs","preflight_rehydration_evidence_refs"):
        refs = manifest.get(bucket, [])
        if refs is None: refs = []
        if not isinstance(refs, list):
            failures.append(f"{bucket}:NOT_LIST"); continue
        for idx, ref in enumerate(refs):
            ok, reason = validate_ref(ref, repo_root)
            if not ok:
                failures.append(f"{bucket}[{idx}]:{reason}")
                continue
            if bucket == "history_query_refs":
                relevant, history_reason = validate_history_relevance(ref, repo_root)
                if not relevant:
                    failures.append(f"{bucket}[{idx}]:{history_reason}")
    return failures


def main() -> int:
    if len(sys.argv) not in {2,3}:
        print("usage: evidence_ref_validator.py <manifest.json> [repo-root]", file=sys.stderr); return 2
    manifest_path = Path(sys.argv[1])
    repo_root = Path(sys.argv[2]) if len(sys.argv)==3 else Path.cwd()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = validate_manifest(payload, repo_root)
    print(json.dumps({"pass": not failures, "failures": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
