#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ENFORCEMENT = ROOT / "ENFORCEMENT"
if str(ENFORCEMENT) not in sys.path:
    sys.path.insert(0, str(ENFORCEMENT))
from grow_lineage_packet import make_event, materialize

SCHEMA_PATH = ROOT / "DOMAIN" / "ARCHITECTURE_COMPANY_EVIDENCE_SCHEMA.json"
DEFAULT_LEDGER = ROOT / "LEARNING" / "evidence" / "architecture-project-evidence.jsonl"
DEFAULT_GROW_LINEAGE = ROOT / "LEARNING" / "evidence" / "grow-lineage.jsonl"

def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def canonical_sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def clean(value):
    return str(value or "").strip()

def unique(values):
    out = []
    seen = set()
    for value in values or []:
        v = clean(value)
        if v and v not in seen:
            out.append(v)
            seen.add(v)
    return out

def validate_core(core, schema):
    issues = []
    identity = core["identity"]
    trace = core["trace"]
    privacy = core["privacy"]

    for key in schema["required_identity"]:
        if not clean(identity.get(key)):
            issues.append("MISSING_" + key.upper())

    if identity["project_source_role"] not in schema["source_roles"]:
        issues.append("SOURCE_ROLE_INVALID")
    if core["state"] not in schema["states"]:
        issues.append("STATE_INVALID")
    if core["outcome"] not in schema["outcomes"]:
        issues.append("OUTCOME_INVALID")
    if core["evidence_grade"] not in schema["evidence_grades"]:
        issues.append("EVIDENCE_GRADE_INVALID")
    if privacy["access_class"] not in schema["access_classes"]:
        issues.append("ACCESS_CLASS_INVALID")
    if not (core["source_refs"] or core["artifact_refs"]):
        issues.append("SOURCE_OR_ARTIFACT_REF_REQUIRED")

    for key in schema["required_trace"]:
        if not clean(trace.get(key)):
            issues.append("TRACE_" + key.upper() + "_REQUIRED")

    if core["state"] in {"STRATEGY", "FRONTIER"}:
        if not clean(trace.get("why_it_worked_failed")):
            issues.append("WHY_REQUIRED_FOR_REUSABLE_STATE")
        if not clean(trace.get("reusable_strategy")):
            issues.append("REUSABLE_STRATEGY_REQUIRED")
    if core["state"] == "FAILURE_LESSON":
        if not clean(trace.get("failure_mode")):
            issues.append("FAILURE_MODE_REQUIRED")
        if not clean(trace.get("why_it_worked_failed")):
            issues.append("WHY_REQUIRED_FOR_FAILURE_LESSON")

    if privacy["client_confidential"] and privacy["access_class"] == "PUBLIC_SOURCE":
        issues.append("CLIENT_CONFIDENTIAL_CANNOT_BE_PUBLIC_SOURCE")
    if privacy["access_class"] == "SHAREABLE_ANONYMIZED" and not privacy["anonymized"]:
        issues.append("ANONYMIZATION_REQUIRED_FOR_SHAREABLE")

    if core["golden_project_candidate"]:
        if identity["project_source_role"] != schema["golden_project_candidate"]["allowed_source_role"]:
            issues.append("GOLDEN_CANDIDATE_COMPANY_PROJECT_REQUIRED")
        if core["evidence_grade"] not in schema["golden_project_candidate"]["minimum_evidence_grade"]:
            issues.append("GOLDEN_CANDIDATE_EVIDENCE_GRADE_INSUFFICIENT")

    return issues

def build_core(args):
    return {
        "identity": {
            "project_id": clean(args.project_id),
            "case_id": clean(args.case_id),
            "project_source_role": clean(args.project_source_role).upper(),
            "project_type": clean(args.project_type),
            "stage": clean(args.stage),
            "revision": clean(args.revision),
        },
        "state": clean(args.state).upper(),
        "outcome": clean(args.outcome).upper(),
        "evidence_grade": clean(args.evidence_grade).upper(),
        "golden_project_candidate": bool(args.golden_candidate),
        "privacy": {
            "access_class": clean(args.access_class).upper(),
            "anonymized": bool(args.anonymized),
            "client_confidential": bool(args.client_confidential),
        },
        "trace": {
            "quality_criterion": clean(args.quality_criterion),
            "interpretation": clean(args.interpretation),
            "design_decision": clean(args.design_decision),
            "implementation_move": clean(args.implementation_move),
            "result_evidence": clean(args.result_evidence),
            "gap_analysis": clean(args.gap_analysis),
            "why_it_worked_failed": clean(args.why),
            "reusable_strategy": clean(args.reusable_strategy),
            "failure_mode": clean(args.failure_mode),
        },
        "similarity_features": {
            "constraint_tags": unique(args.constraint_tag),
            "toolchain_tags": unique(args.toolchain_tag),
            "output_types": unique(args.output_type),
        },
        "source_refs": unique(args.source_ref),
        "artifact_refs": unique(args.artifact_ref),
    }

def _ledger_rows(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows

def append_record(args):
    schema = load_schema()
    core = build_core(args)
    issues = validate_core(core, schema)
    if issues:
        raise ValueError("ARCHIGROW_COMPANY_EVIDENCE_INVALID:" + ",".join(issues))

    ledger = Path(args.ledger) if clean(args.ledger) else DEFAULT_LEDGER
    if not ledger.is_absolute():
        ledger = (Path.cwd() / ledger).resolve()
    ledger.parent.mkdir(parents=True, exist_ok=True)

    lineage_arg = clean(getattr(args, "lineage_ledger", ""))
    if lineage_arg:
        lineage_ledger = Path(lineage_arg)
        if not lineage_ledger.is_absolute():
            lineage_ledger = (Path.cwd() / lineage_ledger).resolve()
    elif ledger.resolve() == DEFAULT_LEDGER.resolve():
        lineage_ledger = DEFAULT_GROW_LINEAGE
    else:
        lineage_ledger = ledger.parent / "grow-lineage.jsonl"

    evidence_fp = canonical_sha(core)
    existing = next((row for row in _ledger_rows(ledger)
                     if row.get("evidence_fingerprint_sha256") == evidence_fp), None)
    if existing:
        return existing, ledger, True

    recorded_at = datetime.now(timezone.utc).isoformat()
    source_ref = (core["source_refs"][0] if core["source_refs"] else
                  core["artifact_refs"][0])
    trace_digest = canonical_sha(core["trace"])

    raw_event = make_event(
        grow_domain="ARCHI_GROW",
        stage="RAW",
        producer="ARCHIGROW_PROJECT_LEARN",
        source_ref=source_ref,
        authority="ARCHITECTURE_WORK_OS_EVIDENCE_CANDIDATE_ONLY",
        payload={
            "project_id": core["identity"]["project_id"],
            "case_id": core["identity"]["case_id"],
            "project_source_role": core["identity"]["project_source_role"],
        },
        recorded_at=recorded_at,
    )
    learning_event = make_event(
        grow_domain="ARCHI_GROW",
        stage="LEARNING",
        producer="ARCHIGROW_PROJECT_LEARN",
        source_ref=f"ARCHPROJECT_LEARNING:{evidence_fp[:24]}",
        parent_refs=[raw_event["event_id"]],
        authority="ARCHITECTURE_WORK_OS_EVIDENCE_CANDIDATE_ONLY",
        payload={
            "state": core["state"],
            "outcome": core["outcome"],
            "evidence_grade": core["evidence_grade"],
            "trace_digest_sha256": trace_digest,
            "golden_project_candidate": core["golden_project_candidate"],
        },
        recorded_at=recorded_at,
    )

    record = {
        "record_version": schema["schema"],
        "recorded_at": recorded_at,
        "authority": "ARCHITECTURE_WORK_OS_EVIDENCE_CANDIDATE_ONLY",
        "promotion_authorized": False,
        "authority_transfer": False,
        "raw_evidence_copied": False,
        **core,
        "trace_digest_sha256": trace_digest,
        "evidence_fingerprint_sha256": evidence_fp,
        "grow_lineage_event_id": learning_event["event_id"],
    }

    rr = materialize(raw_event, lineage_ledger)
    lr = materialize(learning_event, lineage_ledger)
    if not rr.get("ok") or not lr.get("ok"):
        raise RuntimeError("GROW_LINEAGE_MATERIALIZATION_FAILED")

    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record, ledger, False

def summarize(ledger_path=""):
    ledger = Path(ledger_path) if clean(ledger_path) else DEFAULT_LEDGER
    if not ledger.is_absolute():
        ledger = (Path.cwd() / ledger).resolve()
    rows = _ledger_rows(ledger)
    by_state, by_outcome, by_grade = {}, {}, {}
    projects = set()
    golden = 0
    for row in rows:
        projects.add(row.get("identity", {}).get("project_id"))
        by_state[row.get("state", "UNKNOWN")] = by_state.get(row.get("state", "UNKNOWN"), 0) + 1
        by_outcome[row.get("outcome", "UNKNOWN")] = by_outcome.get(row.get("outcome", "UNKNOWN"), 0) + 1
        by_grade[row.get("evidence_grade", "UNKNOWN")] = by_grade.get(row.get("evidence_grade", "UNKNOWN"), 0) + 1
        golden += 1 if row.get("golden_project_candidate") else 0
    projects.discard(None)
    projects.discard("")
    return {
        "ledger": str(ledger),
        "record_count": len(rows),
        "project_count": len(projects),
        "golden_candidate_count": golden,
        "by_state": by_state,
        "by_outcome": by_outcome,
        "by_evidence_grade": by_grade,
        "promotion_authorized": False,
        "rule": "Intake records candidate evidence only; CURRENT_BEST requires the shared GROW promotion gate."
    }

def parse_args():
    p = argparse.ArgumentParser(description="Append-only ArchiGrow company/public project evidence intake.")
    p.add_argument("--ledger", default="")
    p.add_argument("--lineage-ledger", default="")
    p.add_argument("--summary", action="store_true")
    p.add_argument("--project-id", default="")
    p.add_argument("--case-id", default="")
    p.add_argument("--project-source-role", default="COMPANY_PROJECT")
    p.add_argument("--project-type", default="")
    p.add_argument("--stage", default="")
    p.add_argument("--revision", default="")
    p.add_argument("--state", default="CASE")
    p.add_argument("--outcome", default="OBSERVATION_ONLY")
    p.add_argument("--evidence-grade", default="D_OBSERVATION")
    p.add_argument("--access-class", default="INTERNAL")
    p.add_argument("--golden-candidate", action="store_true")
    p.add_argument("--anonymized", action="store_true")
    p.add_argument("--client-confidential", action="store_true")
    p.add_argument("--quality-criterion", default="")
    p.add_argument("--interpretation", default="")
    p.add_argument("--design-decision", default="")
    p.add_argument("--implementation-move", default="")
    p.add_argument("--result-evidence", default="")
    p.add_argument("--gap-analysis", default="")
    p.add_argument("--why", default="")
    p.add_argument("--reusable-strategy", default="")
    p.add_argument("--failure-mode", default="")
    p.add_argument("--constraint-tag", action="append", default=[])
    p.add_argument("--toolchain-tag", action="append", default=[])
    p.add_argument("--output-type", action="append", default=[])
    p.add_argument("--source-ref", action="append", default=[])
    p.add_argument("--artifact-ref", action="append", default=[])
    return p.parse_args()

def main():
    args = parse_args()
    if args.summary:
        print(json.dumps(summarize(args.ledger), ensure_ascii=False, indent=2))
        return 0
    record, ledger, duplicate = append_record(args)
    print(json.dumps({
        "ok": True,
        "ledger": str(ledger),
        "record_id": record["evidence_fingerprint_sha256"][:24],
        "duplicate": duplicate,
        "state": record["state"],
        "promotion_authorized": False,
        "golden_project_selected": False,
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
