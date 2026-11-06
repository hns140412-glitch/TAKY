#!/usr/bin/env python3
"""Transactional, hash-bound local application of a bounded model edit proposal.

No network or model calls. Plans are data, never shell commands. Existing UTF-8
files only; this helper cannot create, rename, delete, push, deploy, or run tests.
"""
from __future__ import annotations

import argparse
import ast
import copy
import difflib
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import stat
import tempfile

EXTENSIONS = {".py", ".ps1", ".js", ".ts", ".tsx", ".jsx", ".json", ".css", ".html"}
MAX_BYTES = 100_000

class EditRejected(ValueError):
    pass

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def file_path(repo: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise EditRejected("INVALID_RELATIVE_PATH")
    rel = PurePosixPath(name)
    if rel.is_absolute() or any(x in {"", ".", ".."} for x in name.split("/")):
        raise EditRejected("UNSAFE_RELATIVE_PATH")
    if rel.suffix.lower() not in EXTENSIONS:
        raise EditRejected("UNSUPPORTED_EXTENSION")
    dst = repo.joinpath(*rel.parts)
    # Refuse symlinks/junctions at every part, not just at the final file.
    cursor = repo
    for component in rel.parts:
        cursor = cursor / component
        if cursor.is_symlink() or cursor.is_junction():
            raise EditRejected("REPARSE_POINT_NOT_ALLOWED")
    if not dst.is_file() or dst.stat().st_size > MAX_BYTES:
        raise EditRejected("ORIGINAL_MISSING_OR_TOO_LARGE")
    if not dst.resolve().is_relative_to(repo.resolve()):
        raise EditRejected("OUTSIDE_REPOSITORY")
    return dst

def plan_edits(task: dict, proposal: dict) -> list[dict]:
    if task.get("schema") != "TAKY_EXECUTION_REQUEST_V1" or task.get("mode") != "BOUNDED_EDIT_PROPOSAL":
        raise EditRejected("NOT_AN_IMPLEMENTATION_TASK")
    task_id = task.get("id")
    if not isinstance(task_id, str) or len(task_id) != 32 or proposal.get("task_id") != task_id:
        raise EditRejected("TASK_ID_MISMATCH")
    if task.get("no_push") is not True or task.get("no_deploy") is not True:
        raise EditRejected("UNSAFE_TASK_CONTRACT")
    repo = Path(task["repo"]).resolve(strict=True)
    approved = task.get("allowed_files")
    edits = proposal.get("edits")
    if not isinstance(approved, list) or not approved:
        raise EditRejected("ALLOWED_FILES_MISSING")
    if not isinstance(edits, list) or not 1 <= len(edits) <= len(approved):
        raise EditRejected("INVALID_EDIT_COUNT")
    allowed = {}
    for entry in approved:
        if not isinstance(entry, dict):
            raise EditRejected("INVALID_APPROVED_ENTRY")
        name, expected = entry.get("path"), entry.get("sha256")
        if name in allowed or not isinstance(expected, str) or len(expected) != 64:
            raise EditRejected("INVALID_APPROVED_DIGEST")
        file_path(repo, name)
        allowed[name] = expected.lower()
    seen = set()
    prepared = []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"path", "replacements"}:
            raise EditRejected("UNEXPECTED_EDIT_FIELDS")
        name = edit["path"]
        if name in seen or name not in allowed:
            raise EditRejected("UNAPPROVED_OR_DUPLICATE_FILE")
        seen.add(name)
        dst = file_path(repo, name)
        before = dst.read_bytes()
        if sha(before) != allowed[name]:
            raise EditRejected("SOURCE_CHANGED_SINCE_APPROVAL")
        try:
            old = before.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise EditRejected("NON_UTF8_FILE") from exc
        replacements = edit["replacements"]
        if not isinstance(replacements, list) or not replacements:
            raise EditRejected("INVALID_REPLACEMENTS")
        updated = old
        for item in replacements:
            if not isinstance(item, dict) or set(item) != {"old", "new"}:
                raise EditRejected("INVALID_REPLACEMENT_FIELDS")
            previous, replacement = item["old"], item["new"]
            if not isinstance(previous, str) or not previous or not isinstance(replacement, str):
                raise EditRejected("EMPTY_OR_INVALID_REPLACEMENT")
            if previous == replacement or updated.count(previous) != 1:
                raise EditRejected("NON_UNIQUE_OR_NOOP_REPLACEMENT")
            updated = updated.replace(previous, replacement, 1)
        encoded = (b"\xef\xbb\xbf" if before.startswith(b"\xef\xbb\xbf") else b"") + updated.encode("utf-8")
        if len(encoded) > MAX_BYTES or encoded == before:
            raise EditRejected("OVERSIZE_OR_NOOP_RESULT")
        if dst.suffix.lower() == ".json":
            json.loads(updated)
        if dst.suffix.lower() == ".py":
            ast.parse(updated, filename=str(dst))
        preview = "".join(difflib.unified_diff(old.splitlines(True), updated.splitlines(True),
                         fromfile=name, tofile=name))
        prepared.append({"path": str(dst), "relative": name, "before": before, "after": encoded,
                         "diff": preview[:5000], "before_sha256": sha(before), "after_sha256": sha(encoded)})
    return prepared

def apply(prepared: list[dict]) -> None:
    # Validate every preimage a second time before writing anything.
    for item in prepared:
        if sha(Path(item["path"]).read_bytes()) != item["before_sha256"]:
            raise EditRejected("CONCURRENT_SOURCE_CHANGE")
    staged = []
    replaced = []
    try:
        for item in prepared:
            dst = Path(item["path"])
            fd, name = tempfile.mkstemp(prefix=".taky-edit-", dir=str(dst.parent))
            os.close(fd)
            tmp = Path(name)
            staged.append(tmp)
            tmp.write_bytes(item["after"])
            os.chmod(tmp, stat.S_IMODE(dst.stat().st_mode))
        for item, tmp in zip(prepared, staged):
            dst = Path(item["path"])
            if sha(dst.read_bytes()) != item["before_sha256"]:
                raise EditRejected("CONCURRENT_SOURCE_CHANGE")
            os.replace(tmp, dst)
            replaced.append(item)
    except Exception:
        # Restore only files modified by this transaction, never unrelated files.
        for item in reversed(replaced):
            dst = Path(item["path"])
            if sha(dst.read_bytes()) == item["after_sha256"]:
                fd, name = tempfile.mkstemp(prefix=".taky-restore-", dir=str(dst.parent))
                os.close(fd)
                rollback = Path(name)
                try:
                    rollback.write_bytes(item["before"])
                    os.replace(rollback, dst)
                finally:
                    rollback.unlink(missing_ok=True)
        raise
    finally:
        for tmp in staged:
            tmp.unlink(missing_ok=True)

def signed_model_proposal_bound(task: dict, proposal: dict, receipt_id: str,
                                *, execution_evidence: dict | None = None,
                                task_file_sha256: str | None = None,
                                trusted_runtime: dict | None = None) -> None:
    """Require a sealed model call carrying these exact proposed edits.

    No signature key or synthetic receipt can be supplied through CLI args.
    Testing may supply a fixture; real calls always load TAKY2's sealed ledger.
    """
    task_id = task.get("id")
    if (not isinstance(task_id, str) or re.fullmatch(r"[a-f0-9]{32}", task_id) is None
            or not isinstance(receipt_id, str) or
            re.fullmatch(r"pf:external-review-" + task_id + r":[a-f0-9]{16,32}", receipt_id) is None):
        raise EditRejected("SCOPED_EDIT_SIGNED_RECEIPT_REQUIRED")
    if trusted_runtime is None:
        from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
        ensure_trusted_taky2()
        from TAKY2.state_store import load_bundle
        try:
            _, trusted_runtime, _ = load_bundle()
        except Exception as exc:
            raise EditRejected("SCOPED_EDIT_SIGNED_LEDGER_UNAVAILABLE") from exc
    if not isinstance(trusted_runtime, dict):
        raise EditRejected("SCOPED_EDIT_LEDGER_INVALID")
    from TAKY2.enforcement import stable_hash
    if (not isinstance(execution_evidence, dict)
            or execution_evidence.get("task_id") != task_id
            or execution_evidence.get("taky2_signed_receipt_id") != receipt_id):
        raise EditRejected("SCOPED_EDIT_EXECUTION_RECORD_NOT_BOUND")
    receipt = trusted_runtime.get("preflight_receipts", {}).get(receipt_id)
    call = trusted_runtime.get("execution_calls", {}).get(receipt_id)
    if not isinstance(receipt, dict) or not isinstance(call, dict):
        raise EditRejected("SCOPED_EDIT_SIGNED_CALL_MISSING")
    if (receipt.get("allowed") is not True or receipt.get("call_allowed") is not True
            or receipt.get("authority_digest") != trusted_runtime.get("authority_digest")
            or not isinstance(receipt.get("call_digest"), str)
            or not receipt.get("call_digest")):
        raise EditRejected("SCOPED_EDIT_CALL_NOT_AUTHORIZED")
    actors = {
        ("openai", "codex", "TAKY_MODEL_REVIEW_CODEX"): "verify:codex-packet",
        ("anthropic", "sonnet", "TAKY_MODEL_REVIEW_CLAUDE"): "review:external-model",
    }
    actual = (call.get("provider"), call.get("model"), call.get("executor_id"))
    if receipt.get("action_id") != actors.get(actual):
        raise EditRejected("SCOPED_EDIT_SIGNED_PROVIDER_OR_ACTION_MISMATCH")
    # Reconstruct the exact preflight call from the original governed wrapper's
    # output. This untrusted disk copy has no authority unless its canonical
    # digest equals the HMAC-verified TAKY2 preflight receipt.
    signed_call = execution_evidence.get("governed_call_manifest")
    if (not isinstance(signed_call, dict)
            or stable_hash(signed_call) != receipt.get("call_digest")
            or signed_call.get("model") != call.get("model")
            or signed_call.get("execution_mode") not in {"PACKET_ONLY", "CODEX_VERIFY_ONLY"}
            or signed_call.get("expected_calls") != 1
            or not isinstance(signed_call.get("source_manifest"), list)):
        raise EditRejected("SCOPED_EDIT_SIGNED_INPUT_MANIFEST_MISMATCH")
    contract = signed_call.get("scoped_edit_contract")
    if (not isinstance(contract, dict)
            or set(contract) != {"schema", "task_id", "task_sha256", "repo"}
            or contract.get("schema") != "TAKY_SCOPED_EDIT_CALL_V1"
            or contract.get("task_id") != task_id
            or contract.get("task_sha256") != task_file_sha256
            or not isinstance(task_file_sha256, str)
            or re.fullmatch(r"[a-f0-9]{64}", task_file_sha256) is None
            or contract.get("repo") != task.get("repo")):
        raise EditRejected("SCOPED_EDIT_ORIGINAL_TASK_CONTRACT_NOT_SIGNED")
    originals = signed_call["source_manifest"]
    for approved in task.get("allowed_files", []):
        if (not isinstance(approved, dict) or
                not any(isinstance(src, dict)
                        and src.get("path") == approved.get("path")
                        and src.get("sha256") == approved.get("sha256")
                        and src.get("complete") is True
                        and type(src.get("includedLines")) is int
                        and src.get("includedLines") == src.get("totalLines")
                        for src in originals)):
            raise EditRejected("SCOPED_EDIT_FILE_NOT_IN_SIGNED_COMPLETE_PACKET")
    result = call.get("result")
    if (call.get("status") != "RETURNED" or call.get("actual_calls") != 1
            or not isinstance(result, dict) or result.get("returncode") != 0
            or stable_hash(result) != call.get("result_digest")):
        raise EditRejected("SCOPED_EDIT_SIGNED_MODEL_RETURN_INVALID")
    active = trusted_runtime.get("active_attempts", {}).get(receipt.get("execution_key"))
    if not isinstance(active, dict) or not isinstance(active.get("attempt"), dict):
        raise EditRejected("SCOPED_EDIT_SIGNED_TARGET_MISSING")
    try:
        root = Path(task["repo"]).resolve(strict=True)
        signed_root = Path(active["attempt"]["target"]).resolve(strict=True)
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise EditRejected("SCOPED_EDIT_SIGNED_TARGET_INVALID") from exc
    if root != signed_root:
        raise EditRejected("SCOPED_EDIT_REPOSITORY_ROUTE_MISMATCH")
    # Parse exactly the model's sealed stdout; do not trust arbitrary sidecar
    # candidates or a pasted proposal that did not come from this invocation.
    try:
        original = extract_proposal(task, result.get("stdout", ""))
    except (EditRejected, ValueError, TypeError) as exc:
        raise EditRejected("SCOPED_EDIT_MODEL_OUTPUT_NOT_VALID_PROPOSAL") from exc
    if original != proposal:
        raise EditRejected("SCOPED_EDIT_PROPOSAL_NOT_SIGNED_MODEL_OUTPUT")



def _scoped_edit_identity(task: dict, proposal: dict, prepared: list[dict],
                          receipt_id: str, task_file_sha256: str) -> dict:
    from TAKY2.enforcement import stable_hash
    return {
        "schema": "TAKY_SCOPED_EDIT_CLAIM_V1",
        "receipt_id": receipt_id,
        "task_id": task["id"],
        "task_file_sha256": task_file_sha256,
        "proposal_digest": stable_hash(proposal),
        "files": [{
            "path": item["relative"],
            "before_sha256": item["before_sha256"],
            "after_sha256": item["after_sha256"],
        } for item in prepared],
    }


def claim_scoped_edit_once(task: dict, proposal: dict, prepared: list[dict],
                           receipt_id: str, task_file_sha256: str,
                           execution_evidence: dict) -> dict:
    """Atomic signed-ledger reservation BEFORE changing any files.

    A conflict, replay, crash or unknown result stays HOLD. This uses the
    existing TAKY2 HMAC/anchor state and optimistic versioned store, not a
    second approval or execution registry. The claim itself is NOT user consent.
    """
    from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
    ensure_trusted_taky2()
    from TAKY2.state_store import load_bundle, save_runtime
    from TAKY2.enforcement import stable_hash
    try:
        _, current, authority = load_bundle()
        # Re-check exactly the version that will be atomically saved. The prior
        # admission check cannot be reused across a conflicting state update.
        signed_model_proposal_bound(
            task, proposal, receipt_id, execution_evidence=execution_evidence,
            task_file_sha256=task_file_sha256, trusted_runtime=current)
        if receipt_id in current.get("scoped_edit_claims", {}):
            raise EditRejected("SCOPED_EDIT_RECEIPT_ALREADY_CLAIMED")
        expected = _scoped_edit_identity(
            task, proposal, prepared, receipt_id, task_file_sha256)
        updated = copy.deepcopy(current)
        updated.setdefault("scoped_edit_claims", {})[receipt_id] = {
            **expected,
            "status": "CLAIMED_PENDING_FILE_APPLY",
            "authority_digest": authority,
        }
        save_runtime(updated, expected_version=current["runtime_version"],
                     authority_digest_value=authority)
        return expected
    except EditRejected:
        raise
    except Exception as exc:
        raise EditRejected("SCOPED_EDIT_CLAIM_NOT_CONFIRMED_HOLD") from exc


def finalize_scoped_edit_claim(task: dict, prepared: list[dict],
                                identity: dict) -> None:
    """Confirm the output bytes, then mark the existing receipt applied.

    Never retry an uncertain claim; only a distinct authorized task can start
    again. If the state commit fails, files may have been applied and the claim
    deliberately stays PENDING for inspection rather than claiming success.
    """
    from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
    ensure_trusted_taky2()
    from TAKY2.state_store import load_bundle, save_runtime
    try:
        _, current, authority = load_bundle()
        receipt_id = identity["receipt_id"]
        recorded = current.get("scoped_edit_claims", {}).get(receipt_id)
        if (not isinstance(recorded, dict)
                or recorded.get("status") != "CLAIMED_PENDING_FILE_APPLY"
                or recorded.get("authority_digest") != authority
                or {k: recorded.get(k) for k in identity} != identity):
            raise EditRejected("SCOPED_EDIT_CLAIM_MISSING_OR_CHANGED")
        repo = Path(task["repo"]).resolve(strict=True)
        for item in prepared:
            output_file = file_path(repo, item["relative"])
            if sha(output_file.read_bytes()) != item["after_sha256"]:
                raise EditRejected("SCOPED_EDIT_OUTPUT_NOT_ATTESTED")
        updated = copy.deepcopy(current)
        updated["scoped_edit_claims"][receipt_id]["status"] = "APPLIED_UNVERIFIED"
        save_runtime(updated, expected_version=current["runtime_version"],
                     authority_digest_value=authority)
    except EditRejected:
        raise
    except Exception as exc:
        raise EditRejected("SCOPED_EDIT_FINALIZATION_UNCERTAIN_HOLD") from exc


def run(task: dict, proposal: dict, *, execute=False,
        signed_receipt_id: str | None = None,
        execution_evidence: dict | None = None,
        task_file_sha256: str | None = None) -> dict:
    prepared = plan_edits(task, proposal)
    if execute:
        if os.getenv("TAKY_USER_EXPLICIT_AUTHORIZATION") != "1" or os.getenv("TAKY_ALLOW_SCOPED_FILE_EDIT") != "1":
            raise EditRejected("SCOPED_EDIT_AUTHORIZATION_REQUIRED")
        if not isinstance(execution_evidence, dict):
            raise EditRejected("SCOPED_EDIT_EXECUTION_RECORD_NOT_BOUND")
        # Persist a single-use claim in the existing HMAC/anchor-verified runtime
        # before touching a source file. Unknown outcomes remain claimed/HOLD.
        claim = claim_scoped_edit_once(
            task, proposal, prepared, signed_receipt_id, task_file_sha256,
            execution_evidence)
        apply(prepared)
        finalize_scoped_edit_claim(task, prepared, claim)
    return {"status": "APPLIED_UNVERIFIED" if execute else "DRY_RUN_VALID",
            "task_id": task["id"], "files": [{"path": x["relative"],
            "before_sha256": x["before_sha256"], "after_sha256": x["after_sha256"],
            "diff": x["diff"]} for x in prepared],
            "model_calls": 0, "paid_api_calls": 0}

def extract_proposal(task: dict, text: str) -> dict:
    """Accept only a complete structured model proposal, never free-form patches."""
    if len(text) > 180_000:
        raise EditRejected("MODEL_RESPONSE_OVERSIZE")
    body = text.strip()
    if body.startswith("```json") and body.endswith("```"):
        body = body[7:-3].strip()
    try:
        proposal = json.loads(body)
    except (json.JSONDecodeError, TypeError) as exc:
        raise EditRejected("MODEL_RESPONSE_NOT_STRICT_JSON") from exc
    if isinstance(proposal, dict) and isinstance(proposal.get("result"), str):
        if proposal.get("is_error") is True:
            raise EditRejected("MODEL_REPORTED_ERROR")
        candidate = proposal["result"].strip()
        if candidate.startswith("```json") and candidate.endswith("```"):
            candidate = candidate[7:-3].strip()
        proposal = json.loads(candidate)
    if not isinstance(proposal, dict) or set(proposal) != {"task_id", "edits"}:
        raise EditRejected("MODEL_PROPOSAL_SCHEMA_INVALID")
    plan_edits(task, proposal)
    return proposal

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--proposal-file")
    parser.add_argument("--extract-output-file")
    parser.add_argument("--candidate-file")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--signed-receipt")
    parser.add_argument("--execution-record")
    args = parser.parse_args()
    try:
        task_bytes = Path(args.task_file).read_bytes()
        task = json.loads(task_bytes.decode("utf-8-sig"))
        if args.extract_output_file:
            if args.apply or not args.candidate_file or args.proposal_file:
                raise EditRejected("EXTRACTION_ARGUMENTS_INVALID")
            source = Path(args.extract_output_file).read_text(encoding="utf-8-sig")
            proposal = extract_proposal(task, source)
            dst = Path(args.candidate_file)
            if dst.exists():
                raise EditRejected("CANDIDATE_ALREADY_EXISTS")
            with dst.open("x", encoding="utf-8") as stream:
                json.dump(proposal, stream, ensure_ascii=False, indent=2)
            result = {"status": "PROPOSAL_VALIDATED_NOT_APPLIED",
                      "task_id": task["id"], "proposal_file": str(dst), "model_calls": 0}
        else:
            if not args.proposal_file:
                raise EditRejected("PROPOSAL_FILE_REQUIRED")
            proposal = json.loads(Path(args.proposal_file).read_text(encoding="utf-8-sig"))
            proof = (json.loads(Path(args.execution_record).read_text(encoding="utf-8-sig"))
                     if args.apply and args.execution_record else None)
            result = run(task, proposal, execute=args.apply,
                         signed_receipt_id=args.signed_receipt,
                         execution_evidence=proof,
                         task_file_sha256=sha(task_bytes))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (EditRejected, OSError, KeyError, TypeError, json.JSONDecodeError, SyntaxError) as exc:
        print(json.dumps({"status": "HOLD", "reason": str(exc)[:180]}, ensure_ascii=False))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
