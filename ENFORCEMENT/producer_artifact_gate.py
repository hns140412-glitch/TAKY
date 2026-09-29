#!/usr/bin/env python3
"""AI-producer artifact PRE/POST control for controlled repository runtimes.

Not a hosted ChatGPT hook. A producer MUST call pre before writing the output
and post before claiming verified completion. Evidence presence is not a human
visual approval or proof of visual quality.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

VISUAL_KINDS = {"spreadsheet", "document", "pdf", "presentation", "image", "asset", "ui", "pwa"}
KINDS = VISUAL_KINDS | {"code", "structured_data", "handoff", "research"}

def _rooted(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("INVALID_RELATIVE_PATH")
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("PATH_ESCAPES_ROOT")
    return path

def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())

def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def preflight(contract: dict, root: Path) -> dict:
    errors = []
    kind = contract.get("kind")
    if kind not in KINDS:
        errors.append("ARTIFACT_KIND_INVALID")
    for key in ("task_id", "user_intent", "output_path", "source_ref", "authority_ref", "protected_state", "acceptance_plan", "producer"):
        if not _nonempty(contract.get(key)):
            errors.append("PRE_" + key.upper() + "_MISSING")
    if contract.get("user_as_debugger"):
        errors.append("USER_AS_QA")
    try:
        output = _rooted(root, contract.get("output_path"))
        if output.exists():
            errors.append("PRE_OUTPUT_ALREADY_EXISTS")
    except ValueError as exc:
        errors.append(str(exc))
    baseline_hashes = {}
    for key in ("source_ref", "authority_ref"):
        try:
            source = _rooted(root, contract.get(key))
            if not source.is_file():
                errors.append("PRE_" + key.upper() + "_NOT_FOUND")
            else:
                baseline_hashes[key] = _sha(source)
        except ValueError:
            errors.append("PRE_" + key.upper() + "_INVALID_PATH")
    if kind in VISUAL_KINDS and not _nonempty(contract.get("visual_witness_plan")):
        errors.append("PRE_VISUAL_WITNESS_PLAN_MISSING")
    return {"pass": not errors, "detected": errors, "contract_sha256": _digest(contract),
            "baseline_hashes": baseline_hashes if not errors else {}}

def postflight(contract: dict, receipt: dict, evidence: dict, root: Path) -> dict:
    errors = []
    if not receipt.get("pass") or receipt.get("contract_sha256") != _digest(contract):
        errors.append("POST_PRE_RECEIPT_INVALID")
    baselines = receipt.get("baseline_hashes")
    if not isinstance(baselines, dict) or set(baselines) != {"source_ref", "authority_ref"}:
        errors.append("POST_BASELINE_RECEIPT_MISSING")
    else:
        for key in ("source_ref", "authority_ref"):
            try:
                p = _rooted(root, contract.get(key))
                if not p.is_file() or _sha(p) != baselines[key]:
                    errors.append("POST_" + key.upper() + "_CHANGED")
            except (ValueError, KeyError):
                errors.append("POST_" + key.upper() + "_INVALID")
    if evidence.get("contract_sha256") != _digest(contract):
        errors.append("POST_CONTRACT_BINDING_MISSING")
    output = None
    try:
        output = _rooted(root, contract.get("output_path"))
        if not output.is_file() or not output.stat().st_size:
            errors.append("POST_OUTPUT_MISSING")
        elif evidence.get("output_sha256") != _sha(output):
            errors.append("POST_OUTPUT_HASH_MISMATCH")
    except ValueError:
        errors.append("POST_OUTPUT_PATH_INVALID")
    required = ["source_trace", "semantic_check", "regression_check", "delivery_check"]
    if contract.get("kind") in VISUAL_KINDS:
        required.append("visual_check")
    if contract.get("kind") in {"code", "ui", "pwa"}:
        required.append("runtime_check")
    evidence_paths = set()
    for key in required:
        witness = evidence.get(key)
        if not isinstance(witness, dict) or witness.get("passed") is not True:
            errors.append("POST_" + key.upper() + "_UNVERIFIED")
            continue
        try:
            p = _rooted(root, witness.get("evidence_path"))
            if not p.is_file() or not p.stat().st_size:
                errors.append("POST_" + key.upper() + "_EVIDENCE_MISSING")
            elif p == output or p in evidence_paths:
                errors.append("POST_" + key.upper() + "_EVIDENCE_NOT_DISTINCT")
            else:
                evidence_paths.add(p)
        except ValueError:
            errors.append("POST_" + key.upper() + "_EVIDENCE_INVALID")
    if evidence.get("user_as_debugger"):
        errors.append("USER_AS_QA")
    if evidence.get("claim") in {"COMPLETE", "RELEASE_READY"} and not evidence.get("human_approval_ref"):
        errors.append("HUMAN_APPROVAL_MISSING")
    return {"pass": not errors, "detected": errors, "claim_ceiling": "EVIDENCE_RECORDED_NOT_INDEPENDENTLY_VERIFIED" if not errors else "UNVERIFIED"}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=("pre", "post"))
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--receipt", type=Path)
    p.add_argument("--evidence", type=Path)
    args = p.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if args.phase == "pre":
        result = preflight(contract, args.root)
        if args.receipt and result["pass"]:
            args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        if not args.receipt or not args.evidence:
            p.error("post requires --receipt and --evidence")
        result = postflight(contract, json.loads(args.receipt.read_text()), json.loads(args.evidence.read_text()), args.root)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
