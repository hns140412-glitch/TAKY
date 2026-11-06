#!/usr/bin/env python3
"""Offline evidence quality screen for one previously signed external review.

Checks transport authenticity and elementary citations without accepting
semantic correctness. Never executes a model, clears routes, or changes state.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

from TAKY_SIGNED_EXECUTION_READBACK import correlate
from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2

SKILL_CANONICAL_ROOT = Path(r"D:\Git PWA\TAKY\.claude\skills")
BOUND_SKILLS = frozenset(("authority-check", "cross-model-review", "outcome-quality",
                          "archi-grow", "learning-grow", "mobile-webapp-build"))
# Must be identical to the signed dry_run_plan in TAKY_MODEL_REVIEW.ps1.
# The regression test reads the signer source and fails on future drift.
SIGNED_REVIEW_OPERATION = "one bounded packet-only review (not an independent repository investigation)"
APPROVED_REPOS = frozenset((
    r"D:\Git PWA\TAKY",
    r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH",
    r"D:\Git PWA\Play Camp",
    r"D:\Git PWA\Ready & Set",
    r"D:\Git PWA\Hide & Seek",
    r"D:\Git PWA\Snap & Pop",
    r"D:\Git PWA\SAVEY",
))
SOURCE_PATH = re.compile(
    r"^(?:TAKY2|TOOLS|ENFORCEMENT|DOMAIN|LEARNING|src|app|lib|pages|components|tests)/[A-Za-z0-9_./-]+"
    r"\.(?:py|ps1|js|ts|tsx|jsx|json|css|html|md)$", re.I,
)
SOURCE_CITE = re.compile(
    r"(?<![A-Za-z0-9_./\\\\-])(?P<path>(?:TAKY2|TOOLS|ENFORCEMENT|DOMAIN|LEARNING|src|app|lib|pages|components|tests)/"
    r"[A-Za-z0-9_./-]+\.(?:py|ps1|js|ts|tsx|jsx|json|css|html|md))"
    r":(?P<start>\d{1,7})(?:\s*[-–]\s*(?P<end>\d{1,7}))?", re.I,
)


def _screen_reply(text: str, repo: str, sources: list[str],
                  included_line_counts: dict[str, int] | None = None) -> dict:
    if not isinstance(text, str) or not 0 < len(text) <= 100_000:
        return {"state": "RESPONSE_MISSING_OR_OVERSIZE", "qualityVerified": False}
    if (repo not in APPROVED_REPOS or not isinstance(sources, list) or
            not 1 <= len(sources) <= 2 or len({str(x).casefold() for x in sources}) != len(sources)):
        return {"state": "UNAPPROVED_QA_SCOPE", "qualityVerified": False}
    root = Path(repo).resolve(strict=True)
    counts = {}
    for source in sources:
        if not isinstance(source, str) or not SOURCE_PATH.fullmatch(source):
            return {"state": "UNAPPROVED_SOURCE_PATH", "qualityVerified": False}
        target = (root / source).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file() or target.stat().st_size > 100_000:
            return {"state": "SOURCE_UNAVAILABLE_OR_OUTSIDE_SCOPE", "qualityVerified": False}
        counts[source.casefold()] = len(target.read_text(encoding="utf-8-sig").splitlines())
    citations = []
    invalid = []
    for match in SOURCE_CITE.finditer(text):
        source = match.group("path")
        start = int(match.group("start"))
        end = int(match.group("end") or start)
        size = counts.get(source.casefold())
        item = {"source": source, "start": start, "end": end,
                "lineCountCurrent": size}
        citations.append(item)
        if size is None:
            invalid.append({**item, "reason": "SOURCE_NOT_IN_REVIEW_PACKET"})
        elif not 1 <= start <= end <= size:
            invalid.append({**item, "reason": "CITATION_OUTSIDE_CURRENT_SOURCE_LINES"})
        elif included_line_counts is not None and end > included_line_counts.get(source.casefold(), 0):
            invalid.append({**item, "reason": "CITATION_OUTSIDE_SUPPLIED_PACKET_EXCERPT"})
    review_state = ("REVIEW_HAS_SOURCE_CITATION_ERRORS" if invalid else
                    "NO_CHECKABLE_CITATIONS_REVIEW_HOLD" if not citations else
                    "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED")
    return {"state": review_state,
            "qualityVerified": False,
            "currentFilesOnly": True,
            "historicalSourceSnapshotVerified": False,
            "responseSha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "citationCount": len(citations),
            "invalidCitations": invalid,
            "sourceLineCounts": counts}


def verify_signed_source_manifest(
    receipt: dict, repo: str, sources: list[str], binding: dict | None,
    *, model: str = "sonnet"
) -> dict:
    """Authenticate the packet file hashes using TAKY2's HMAC-protected call_digest.

    A local sidecar is not trusted until reconstructing the EXACT model call
    matches the signed preflight. Never infer historical bytes from a changed
    file, and never infer semantic quality from a matching hash.
    """
    if binding is None:
        return {"status": "LEGACY_SOURCE_MANIFEST_UNAVAILABLE",
                "historicalSourceHashBound": False,
                "historicalSourceSnapshotVerified": False}
    legacy_fields = {"packet_digest", "source_manifest"}
    if (not isinstance(binding, dict) or
            set(binding) not in (legacy_fields, legacy_fields | {"skill_manifest"})):
        return {"status": "INVALID_SOURCE_BINDING_HOLD"}
    packet_digest = binding["packet_digest"]
    manifest = binding["source_manifest"]
    skill_manifest = binding.get("skill_manifest")
    if "skill_manifest" in binding:
        if (not isinstance(skill_manifest, list) or
                not 2 <= len(skill_manifest) <= 4):
            return {"status": "INVALID_SKILL_BINDING_HOLD"}
        names = []
        for item in skill_manifest:
            if (not isinstance(item, dict) or set(item) != {"name", "sha256"}
                    or item.get("name") not in BOUND_SKILLS
                    or not isinstance(item.get("sha256"), str)
                    or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"])):
                return {"status": "INVALID_SKILL_BINDING_HOLD"}
            names.append(item["name"])
        if (len(names) != len(set(names)) or names[0] != "authority-check" or
                ("cross-model-review" in names) == ("outcome-quality" in names)):
            return {"status": "INVALID_SKILL_BINDING_HOLD"}
    if (not isinstance(packet_digest, str) or
            re.fullmatch(r"[a-f0-9]{20}", packet_digest) is None or
            not isinstance(manifest, list) or not 1 <= len(manifest) <= 2 or
            len(manifest) != len(sources)):
        return {"status": "INVALID_SOURCE_BINDING_HOLD"}
    included = {}
    for entry, expected in zip(manifest, sources):
        if not isinstance(entry, dict) or set(entry) != {
                "path", "sha256", "includedLines", "totalLines"}:
            return {"status": "INVALID_SOURCE_BINDING_HOLD"}
        path = entry.get("path")
        sha = entry.get("sha256")
        lines = entry.get("includedLines")
        total = entry.get("totalLines")
        if (not isinstance(path, str) or path.casefold() != expected.casefold()
                or SOURCE_PATH.fullmatch(path) is None or
                not isinstance(sha, str) or re.fullmatch(r"[a-f0-9]{64}", sha) is None
                or type(lines) is not int or type(total) is not int
                or not 0 <= lines <= total <= 100_000):
            return {"status": "INVALID_SOURCE_BINDING_HOLD"}
        included[path.casefold()] = lines
    if model not in {"sonnet", "codex"}:
        return {"status": "UNSUPPORTED_SIGNED_MODEL_HOLD"}
    ensure_trusted_taky2()
    from TAKY2.enforcement import stable_hash
    # The original bounded packet signer includes these *deterministic*
    # provenance fields in the sealed source_manifest. The routed readback
    # sidecar carries only four core fields; reconstructing those alone
    # falsely rejects valid signed calls. Derive all omitted fields from the
    # frozen line counts and the packet builder's fixed LIMITED policy.
    signed_manifest = [
        {**entry, "evidenceClass": "LIMITED",
         "complete": entry["includedLines"] == entry["totalLines"],
         "independentReview": False}
        for entry in manifest
    ]
    call = {
        "model": model, "effort": "medium", "context": "delta",
        "expected_calls": 1,
        "execution_mode": "CODEX_VERIFY_ONLY" if model == "codex" else "PACKET_ONLY",
        "packet_digest": packet_digest, "source_manifest": signed_manifest,
        "dry_run_plan": {
            "expected_calls": 1,
            "operations": [SIGNED_REVIEW_OPERATION],
            "batch_strategy": "single-review-batch",
            "fallback": "HOLD",
            "paid_api": False,
        },
    }
    if skill_manifest is not None:
        call["skill_manifest"] = skill_manifest
    if stable_hash(call) != receipt.get("call_digest"):
        # Backward compatibility: historical calls before the expanded packet
        # source manifest used the four-field form. Both forms are accepted
        # ONLY when their exact full-call hash matches the sealed preflight.
        # This never trusts a sidecar, source hash, or claimed review result.
        call["source_manifest"] = manifest
        if stable_hash(call) != receipt.get("call_digest"):
            return {"status": "SIGNED_CALL_DIGEST_MISMATCH_HOLD",
                    "historicalSourceHashBound": False}
    if skill_manifest is not None:
        for item in skill_manifest:
            canonical = SKILL_CANONICAL_ROOT / item["name"] / "SKILL.md"
            if (not canonical.is_file() or canonical.is_symlink()
                    or canonical.stat().st_size > 10_000
                    or hashlib.sha256(canonical.read_bytes()).hexdigest() != item["sha256"]):
                return {"status": "SKILL_CHANGED_SINCE_SIGNED_REVIEW_HOLD",
                        "historicalSourceHashBound": True, "skillManifestSigned": True}
    root = Path(repo).resolve(strict=True)
    for entry in manifest:
        target = (root / entry["path"]).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file() or target.stat().st_size > 100000:
            return {"status": "SOURCE_MISSING_OR_UNAPPROVED_HOLD",
                    "historicalSourceHashBound": True}
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
            return {"status": "SOURCE_CHANGED_SINCE_SIGNED_REVIEW_HOLD",
                    "historicalSourceHashBound": True}
    return {"status": "SIGNED_SOURCE_HASHES_MATCH_CURRENT_FILES",
            "historicalSourceHashBound": True,
            "historicalSourceSnapshotVerified": False,
            "currentFileHashesMatchReview": True,
            "skillManifestSigned": skill_manifest is not None,
            "skillHashesMatchCurrent": skill_manifest is not None,
            "includedLineCounts": included}


def inspect_signed(task_id: str, repo: str, sources: list[str],
                   runtime: dict, source_binding: dict | None = None) -> dict:
    summary = correlate(task_id, runtime)
    if summary.get("state") == "SIGNED_RETURN_DIGEST_MISMATCH_HOLD":
        # Preserve the signed readback failure reason. A corrupted execution
        # result is never interpreted as a successful independent review.
        return {"state": "SIGNED_RESULT_DIGEST_MISMATCH",
                "readbackState": summary.get("state"), "qualityVerified": False,
                "readOnly": True, "modelCalls": 0}
    if summary.get("state") != "CLI_RETURNED_UNVERIFIED":
        return {"state": "SIGNED_EXECUTION_NOT_RETURNED", "readbackState": summary.get("state"),
                "qualityVerified": False, "readOnly": True, "modelCalls": 0}
    receipt_id = summary["receiptId"]
    record = runtime.get("execution_calls", {}).get(receipt_id, {})
    result = record.get("result")
    if not isinstance(result, dict) or result.get("returncode") != 0:
        return {"state": "EXECUTION_RESULT_INVALID", "qualityVerified": False}
    ensure_trusted_taky2()
    from TAKY2.enforcement import stable_hash
    if (not isinstance(record.get("result_digest"), str) or
            stable_hash(result) != record["result_digest"]):
        return {"state": "SIGNED_RESULT_DIGEST_MISMATCH", "qualityVerified": False}
    executor = (record.get("provider"), record.get("model"))
    if executor not in {("anthropic", "sonnet"), ("openai", "codex")}:
        return {"state": "UNSUPPORTED_MODEL_PAYLOAD_FOR_THIS_SCREEN", "qualityVerified": False}
    raw = result.get("stdout")
    if not isinstance(raw, str) or len(raw) > 250_000:
        return {"state": "INVALID_MODEL_PAYLOAD", "qualityVerified": False}
    if executor == ("anthropic", "sonnet"):
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            return {"state": "NON_JSON_MODEL_PAYLOAD", "qualityVerified": False}
        if (not isinstance(payload, dict) or
                payload.get("subtype") != "success" or
                payload.get("is_error") is not False or
                not isinstance(payload.get("result"), str)):
            return {"state": "CLAUDE_RESPONSE_NOT_SUCCESS", "qualityVerified": False}
        review_text = payload["result"]
    else:
        # TAKY2 Codex bridge exposes --output-last-message as plain stdout.
        # It has no Claude-style JSON success envelope.
        review_text = raw
    preflight = runtime.get("preflight_receipts", {}).get(receipt_id, {})
    binding_state = verify_signed_source_manifest(
        preflight, repo, sources, source_binding, model=executor[1])
    binding_status = binding_state["status"]
    if source_binding is not None and binding_status != "SIGNED_SOURCE_HASHES_MATCH_CURRENT_FILES":
        return {"state": binding_status, "qualityVerified": False,
                "taskId": task_id, "receiptId": receipt_id, "readOnly": True,
                "modelCalls": 0, "historicalSourceHashBound":
                    binding_state.get("historicalSourceHashBound", False)}
    screened = _screen_reply(
        review_text, repo, sources,
        included_line_counts=binding_state.get("includedLineCounts"))
    screened["sourceBindingState"] = binding_status
    screened["historicalSourceHashBound"] = binding_state.get(
        "historicalSourceHashBound", False)
    screened["currentFileHashesMatchReview"] = binding_state.get(
        "currentFileHashesMatchReview", False)
    screened["skillManifestSigned"] = binding_state.get("skillManifestSigned", False)
    screened["skillHashesMatchCurrent"] = binding_state.get("skillHashesMatchCurrent", False)
    screened.update({"taskId": task_id, "receiptId": receipt_id,
                     "signedCliStatus": "RETURNED", "readOnly": True,
                     "modelCalls": 0,
                     "provider": "Codex" if executor[1] == "codex" else "Claude",
                     "responseFormat": ("Codex CLI last-message text" if executor[1] == "codex"
                                        else "Claude CLI JSON success")})
    return screened


def signed_inspection(task_id: str, repo: str, sources: list[str],
                      source_binding: dict | None = None) -> dict:
    try:
        ensure_trusted_taky2()
        from TAKY2.state_store import load_bundle, RUNTIME_KEY_PATH
        if not RUNTIME_KEY_PATH.is_file():
            return {"state": "SIGNED_RUNTIME_KEY_UNAVAILABLE", "qualityVerified": False}
        _, runtime, _ = load_bundle()
        result = inspect_signed(task_id, repo, sources, runtime, source_binding)
        result["signedRuntimeIntegrity"] = "PASS"
        return result
    except (OSError, ValueError, RuntimeError, KeyError, UnicodeError) as exc:
        return {"state": "QA_UNAVAILABLE_FAIL_CLOSED", "errorClass": type(exc).__name__,
                "qualityVerified": False, "modelCalls": 0}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--source", action="append", required=True)
    ap.add_argument("--binding-file", type=Path)
    args = ap.parse_args()
    binding = None
    if args.binding_file:
        if args.binding_file.stat().st_size > 2400:
            raise SystemExit("REVIEW_SOURCE_BINDING_OVERSIZE")
        binding = json.loads(args.binding_file.read_text(encoding="utf-8-sig"))
    print(json.dumps(signed_inspection(args.task_id, args.repo, args.source, binding),
                     ensure_ascii=False, indent=2))
