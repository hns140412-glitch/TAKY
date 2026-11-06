#!/usr/bin/env python3
"""Canonical repository-level TAKY preflight bridge.

Combines evidence-reference integrity validation with the existing TAKY deterministic gate.
This proves repository-executable preflight only. It does NOT prove hosted ChatGPT native
tool calls automatically invoke this bridge.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

from evidence_ref_validator import validate_manifest
from taky_gate import validate_record


# Existing MASTER/INTENT_EXECUTION_PROTOCOL operationalized at the preflight
# boundary.  It checks structured evidence, not human semantic equivalence.
RESULT_ACTIONS = {"SPECIFY_ACCEPTANCE", "IMPLEMENTATION_WRITE", "IMPLEMENTATION_EXECUTE"}
ANALYSIS_TERMS = ("분석", "검토", "사례", "원문", "research", "analy")
BUILD_TERMS = ("구현", "코딩", "개발", "만들", "build", "implement")
OUTPUT_KINDS = {"PIPELINE", "APPLICATION", "IMAGE", "DOCUMENT", "CODE_CHANGE",
                "ANALYSIS", "TASK_CONTRACT", "OTHER"}


def validate_intent_fidelity(record: dict, root: Path) -> list[str]:
    """Fail result dispatch when the proposed output or prerequisite drifts.

    A PASS is a *deterministic contract* check only. Exact semantic agreement
    with the user still requires independent review of original request.
    Analysis evidence is checked for structure (source/analysis hashes, analysis
    cites the source hash); it does NOT prove the analysis is semantically adequate.
    """
    action = str(record.get("action_class", "")).strip().upper()
    if action not in RESULT_ACTIONS and record.get("artifact_production") is not True:
        return []
    errors = []
    contract = record.get("intent_contract")
    if not isinstance(contract, dict):
        return ["INTENT_CONTRACT_MISSING"]

    original = contract.get("literal_user_request")
    correction = contract.get("latest_user_correction", "")
    requested = contract.get("requested_result")
    planned = contract.get("planned_result")
    req_kind = contract.get("requested_kind")
    plan_kind = contract.get("planned_kind")
    ref = contract.get("user_source_id")
    if not all(isinstance(v, str) and v.strip() for v in (original, requested, planned, ref)):
        errors.append("INTENT_ORIGINAL_OR_RESULT_TRACE_MISSING")
    if not isinstance(correction, str):
        errors.append("INTENT_LATEST_CORRECTION_INVALID")
        correction = ""
    if req_kind not in OUTPUT_KINDS or plan_kind not in OUTPUT_KINDS:
        errors.append("INTENT_DELIVERABLE_KIND_INVALID")
    elif req_kind != plan_kind:
        errors.append("INTENT_DELIVERABLE_KIND_DRIFT")

    # A simple independent literal anchor catches a second failure mode:
    # the assistant labels BOTH requested and planned results as an app even
    # though the actual user explicitly requested pipeline construction.
    # This is deliberately narrow; it is not a general-language judge.
    # The original constraint survives any correction that does not itself negate the
    # pipeline; only an explicit "pipeline 말고/대신/아니라" in the user's latest correction
    # lifts it.  Requested AND planned kinds must both stay PIPELINE.
    def _pipeline_signal(text: object) -> tuple[bool, bool]:
        if not isinstance(text, str):
            return False, False
        negated = bool(re.search(
            r"(?:파이프\s*라인|pipeline)\s*(?:이?\s*아니라|말고|대신)", text, re.I))
        required = bool(re.search(
            r"(?:파이프\s*라인|pipeline).{0,120}(?:구현|구축|개발|만들|implement|build)",
            text, re.I | re.S))
        return required, negated

    orig_required, orig_negated = _pipeline_signal(original)
    corr_required, corr_negated = _pipeline_signal(correction)
    pipeline_required = (orig_required and not orig_negated) or (corr_required and not corr_negated)
    if pipeline_required and not corr_negated and (req_kind != "PIPELINE" or plan_kind != "PIPELINE"):
        errors.append("INTENT_LITERAL_PIPELINE_RELABELED")

    wm = record.get("working_model")
    if not isinstance(wm, dict) or wm.get("primary_outcome") != planned:
        errors.append("INTENT_WORKING_MODEL_OUTCOME_DIVERGED")
    if not isinstance(wm, dict) or wm.get("intent_contract") != contract:
        errors.append("INTENT_CONTRACT_NOT_BOUND_TO_EXECUTOR_CONTEXT")
    sources = record.get("context_evidence_refs")
    known_ids = {v.get("source_id") for v in sources if isinstance(v, dict)} if isinstance(sources, list) else set()
    if ref not in known_ids:
        errors.append("INTENT_SOURCE_REFERENCE_UNBOUND")

    # Inferred work products may be useful dependencies, but cannot silently
    # replace the requested result.
    kind = str(record.get("artifact_kind", "")).lower()
    artifact = record.get("artifact_contract")
    if isinstance(artifact, dict):
        kind = str(artifact.get("kind", kind)).lower()
    if req_kind == "PIPELINE" and kind in {"ui", "pwa"}:
        errors.append("SUBSTITUTE_RESULT_PIPELINE_TO_UI")

    # A literal analysis+implementation request must not jump directly to
    # implementation-ready specifications or code without source comparisons.
    words = (original if isinstance(original, str) else "") + " " + correction
    words = words.lower()
    analysis_first = any(t in words for t in ANALYSIS_TERMS) and any(t in words for t in BUILD_TERMS)
    if analysis_first:
        if contract.get("analysis_before_implementation") is not True:
            errors.append("INTENT_ANALYSIS_BEFORE_IMPLEMENTATION_REQUIRED")
        evidence = contract.get("source_analysis_evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append("INTENT_SOURCE_ANALYSIS_EVIDENCE_MISSING")
        else:
            for e in evidence:
                if not isinstance(e, dict):
                    errors.append("INTENT_SOURCE_ANALYSIS_EVIDENCE_INVALID")
                    continue
                for field in ("source_path", "analysis_path"):
                    rel = e.get(field)
                    if not isinstance(rel, str) or not rel.strip() or Path(rel).is_absolute():
                        errors.append("INTENT_SOURCE_ANALYSIS_EVIDENCE_INVALID")
                        continue
                    candidate = (root / rel).resolve()
                    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file() or not candidate.stat().st_size:
                        errors.append("INTENT_SOURCE_ANALYSIS_EVIDENCE_NOT_FOUND")
                review = e.get("analysis_path")
                digest = e.get("analysis_sha256")
                src_digest = e.get("source_sha256")
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    errors.append("INTENT_ANALYSIS_PROOF_HASH_INVALID")
                elif isinstance(review, str) and not Path(review).is_absolute():
                    path = (root / review).resolve()
                    if path.is_relative_to(root.resolve()) and path.is_file():
                        analysis_bytes = path.read_bytes()
                        if hashlib.sha256(analysis_bytes).hexdigest() != digest:
                            errors.append("INTENT_ANALYSIS_PROOF_HASH_MISMATCH")
                        else:
                            # A hash of "some file" proves nothing about analysis of THIS
                            # source: bind it to the source bytes and require a cite of them.
                            src = e.get("source_path")
                            src_ok = False
                            if isinstance(src, str) and not Path(src).is_absolute():
                                sp = (root / src).resolve()
                                src_ok = (sp.is_relative_to(root.resolve()) and sp.is_file()
                                          and sp != path
                                          and isinstance(src_digest, str)
                                          and hashlib.sha256(sp.read_bytes()).hexdigest() == src_digest)
                            if not src_ok:
                                errors.append("INTENT_ANALYSIS_SOURCE_BINDING_INVALID")
                            elif src_digest.encode("ascii") not in analysis_bytes:
                                errors.append("INTENT_ANALYSIS_DOES_NOT_CITE_SOURCE")

    return list(dict.fromkeys(errors))


def run(record: dict, repo_root: Path) -> dict:
    failures = []
    evidence_failures = validate_manifest(record, repo_root)
    if record.get("pre_execution_gate_required"):
        required = ["applicable_rule_refs", "context_evidence_refs", "history_query_refs"]
        if record.get("resumed_or_context_compacted"):
            required.append("preflight_rehydration_evidence_refs")
        for bucket in required:
            refs = record.get(bucket)
            if not isinstance(refs, list) or not refs:
                failures.append(f"{bucket}:MISSING")
        if not isinstance(record.get("working_model"), dict):
            failures.append("working_model:MISSING")
    failures.extend(evidence_failures)
    failures.extend(validate_intent_fidelity(record, repo_root))
    failures.extend(validate_record(record))
    unique = list(dict.fromkeys(failures))
    return {
        "pass": not unique,
        "detected": unique,
        "runtime_claim_ceiling": "REPOSITORY_EXECUTABLE_CI_ENFORCED",
        "semantic_analysis_verified": False,
        "live_runtime_auto_invocation_verified": bool(record.get("live_runtime_auto_invocation_verified", False)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    a = ap.parse_args()
    record = json.loads(a.record.read_text(encoding="utf-8"))
    result = run(record, a.repo_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
