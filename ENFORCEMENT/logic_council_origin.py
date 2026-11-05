"""Verified provider-origin binding for the existing TAKY logic council gate.

Not an executor: model invocation remains with the governed TAKY2 transport.
The caller must use the fixed canonical HMAC/anchor-authenticated state.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
from typing import Mapping


class CouncilOriginError(ValueError):
    pass


# Rebind only after independently reviewing a genuine TAKY2 kernel update.
_TAKY2_TRUSTED_SHA = {
    "state_store.py": "9970b38fd564be4438ab8d6b1e49e4b27f6cc6fba758bf808e2cb288bc81c8cd",
    "__init__.py": "8ae14470d526930c01ce351b03480a781ea19fd806d70f02424530a3cb6436ef",
    "enforcement.py": "94d87bb937c00734aedea5ececeefbd8dbc6866146ea815b26988ba245f58394",
}


def _stable_hash(value: object) -> str:
    # Same digest specification as TAKY2.enforcement.stable_hash.
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()[:20]


def load_trusted_execution_runtime(repo_root: Path) -> Mapping:
    """Use this installed TAKY root, not an untrusted task-supplied repo."""
    canonical = Path(__file__).resolve().parents[1]
    if repo_root.resolve() != canonical or canonical.name.casefold() != "taky":
        raise CouncilOriginError("TAKY2_TRUSTED_STORE_UNAVAILABLE")
    kernel = canonical / ".local" / "TAKY-2.0-ORCH"
    package = kernel / "TAKY2"
    for name, expected in _TAKY2_TRUSTED_SHA.items():
        candidate = package / name
        try:
            if (candidate.is_symlink() or not candidate.is_file()
                    or hashlib.sha256(candidate.read_bytes()).hexdigest() != expected):
                raise CouncilOriginError("TAKY2_KERNEL_PIN_MISMATCH")
        except OSError as exc:
            raise CouncilOriginError("TAKY2_KERNEL_PIN_MISMATCH") from exc
    package_root = str(kernel)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    # Reject a preloaded shadow module instead of executing its code.
    for modname, expected_file in (
        ("TAKY2", package / "__init__.py"),
        ("TAKY2.state_store", package / "state_store.py"),
    ):
        existing = sys.modules.get(modname)
        if existing is not None and Path(getattr(existing, "__file__", "")).resolve() != expected_file.resolve():
            raise CouncilOriginError("TAKY2_MODULE_SHADOWED")
    try:
        mod = importlib.import_module("TAKY2.state_store")
        if Path(mod.__file__).resolve() != (package / "state_store.py").resolve():
            raise CouncilOriginError("TAKY2_MODULE_SHADOWED")
        _, runtime, _ = mod.load_bundle()  # HMAC, anchor, authority digest
    except CouncilOriginError:
        raise
    except Exception as exc:
        raise CouncilOriginError("TAKY2_SIGNED_STORE_READBACK_FAILED") from exc
    return runtime


def _call_body(stdout: object) -> dict:
    if not isinstance(stdout, str) or not stdout.strip() or len(stdout) > 150000:
        raise CouncilOriginError("PROVIDER_STDOUT_NOT_BOUNDED_JSON")
    try:
        body = json.loads(stdout.strip())
        if isinstance(body, dict) and body.get("type") == "result":
            if body.get("is_error") is True or body.get("subtype") not in ("success", None):
                raise CouncilOriginError("PROVIDER_ENVELOPE_FAILED")
            if not isinstance(body.get("result"), str):
                raise CouncilOriginError("PROVIDER_RESULT_NOT_JSON")
            body = json.loads(body["result"].strip())
    except CouncilOriginError:
        raise
    except (ValueError, TypeError) as exc:
        raise CouncilOriginError("PROVIDER_RESULT_NOT_JSON") from exc
    if not isinstance(body, dict):
        raise CouncilOriginError("PROVIDER_RESULT_NOT_OBJECT")
    return body


def verify_provider_origin(
    runtime: Mapping,
    receipt_id: object,
    frozen_data: dict,
    used_ids: set[str],
    *,
    call_manifest: object,
    binding: dict,
) -> str:
    """Bind exact provider output AND the signed pre-invocation input manifest.

    A truthful signed invocation with the right role/source/target does not
    itself prove factual correctness, diverse models or independent thought.
    """
    if (not isinstance(receipt_id, str) or not receipt_id.startswith("pf:")
            or receipt_id in used_ids):
        raise CouncilOriginError("RECEIPT_ID_MISSING_OR_REUSED")
    used_ids.add(receipt_id)
    receipts = runtime.get("preflight_receipts")
    calls = runtime.get("execution_calls")
    if not isinstance(receipts, Mapping) or not isinstance(calls, Mapping):
        raise CouncilOriginError("TRUSTED_EXECUTION_LEDGER_MISSING")
    receipt, call = receipts.get(receipt_id), calls.get(receipt_id)
    if not isinstance(receipt, Mapping) or not isinstance(call, Mapping):
        raise CouncilOriginError("RECEIPT_NOT_FOUND_IN_SIGNED_STATE")
    if (receipt.get("allowed") is not True or receipt.get("call_allowed") is not True
            or receipt.get("authority_digest") != runtime.get("authority_digest")):
        raise CouncilOriginError("RECEIPT_NOT_AUTHORIZED")

    if (not isinstance(call_manifest, dict) or not isinstance(binding, dict)
            or call_manifest.get("council_binding") != binding
            or not isinstance(call_manifest.get("packet_digest"), str)
            or not re.fullmatch(r"[a-f0-9]{20,64}", call_manifest["packet_digest"])
            or _stable_hash(call_manifest) != receipt.get("call_digest")):
        raise CouncilOriginError("CALL_INPUT_UNBOUND")

    # Require a complete signed source packet. A role label, hash metadata,
    # or five generated prose files alone are not evidence that the provider
    # received the original source and frozen peer reports.
    inputs = call_manifest.get("source_manifest")
    if (not isinstance(inputs, list) or not 1 <= len(inputs) <= 8
            or any(not isinstance(x, dict)
                   or not isinstance(x.get("sha256"), str)
                   or re.fullmatch(r"[a-f0-9]{64}", x["sha256"]) is None
                   or x.get("complete") is not True
                   for x in inputs)):
        raise CouncilOriginError("SIGNED_SOURCE_INPUTS_UNVERIFIED")
    digest_list = [x["sha256"] for x in inputs]
    if len(set(digest_list)) != len(digest_list):
        raise CouncilOriginError("SIGNED_SOURCE_INPUTS_DUPLICATED")
    original_digest = binding.get("source_sha256")
    target_digest = binding.get("target_sha256")
    stage = str(binding.get("stage", ""))
    if original_digest not in digest_list:
        raise CouncilOriginError("ORIGINAL_SOURCE_NOT_IN_CALL")
    if stage.startswith("ADVISOR_"):
        if target_digest is not None:
            raise CouncilOriginError("ADVISOR_TARGET_UNEXPECTED")
    elif stage.startswith("PEER_"):
        if target_digest not in digest_list:
            raise CouncilOriginError("FROZEN_TARGET_NOT_IN_PEER_CALL")
    elif stage == "CHAIR":
        peer_inputs = sorted(sha for sha in digest_list if sha != original_digest)
        if len(peer_inputs) != 5 or (
            hashlib.sha256(json.dumps(peer_inputs, ensure_ascii=False,
                separators=(",", ":")).encode("utf-8")).hexdigest() != target_digest
        ):
            raise CouncilOriginError("FIVE_FROZEN_PEERS_NOT_IN_CHAIR_CALL")
    else:
        raise CouncilOriginError("COUNCIL_STAGE_INVALID")

    actor = call.get("executor_id")
    actors = {
        "TAKY_MODEL_REVIEW_CLAUDE": ("anthropic", "sonnet", "review:external-model"),
        "TAKY_MODEL_REVIEW_CODEX": ("openai", "codex", "verify:codex-packet"),
    }
    expected = actors.get(actor)
    if (expected is None
            or (call.get("provider"), call.get("model"), receipt.get("action_id")) != expected
            or call.get("status") != "RETURNED" or call.get("actual_calls") != 1):
        raise CouncilOriginError("PROVIDER_INVOCATION_UNVERIFIED")
    result = call.get("result")
    if not isinstance(result, Mapping) or result.get("returncode") != 0:
        raise CouncilOriginError("PROVIDER_RUN_FAILED")
    if call.get("result_digest") != _stable_hash(dict(result)):
        raise CouncilOriginError("PROVIDER_RESULT_DIGEST_MISMATCH")
    if _call_body(result.get("stdout")) != frozen_data:
        raise CouncilOriginError("FROZEN_REPORT_DIFFERS_FROM_EXECUTED_OUTPUT")
    return actor
