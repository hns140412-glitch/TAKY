#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "LEARNING" / "evidence" / "architecture-competition-representation.jsonl"
ALLOWED_STATES = {"CASE", "STRATEGY", "FRONTIER", "FAILURE_LESSON"}
ALLOWED_OUTCOMES = {"SUCCESS", "PARTIAL", "FAILURE", "OBSERVATION_ONLY"}

def fingerprint(value):
    return hashlib.sha256(value.encode("utf-8", "ignore")).hexdigest()

def append_record(args):
    ledger = Path(args.ledger) if args.ledger else DEFAULT_LEDGER
    if not ledger.is_absolute():
        ledger = (Path.cwd() / ledger).resolve()
    ledger.parent.mkdir(parents=True, exist_ok=True)

    state = args.state.upper()
    outcome = args.outcome.upper()
    if state not in ALLOWED_STATES:
        raise SystemExit(f"invalid state: {state}")
    if outcome not in ALLOWED_OUTCOMES:
        raise SystemExit(f"invalid outcome: {outcome}")

    artifact_refs = [x.strip() for x in args.artifact_ref if x.strip()]
    source_refs = [x.strip() for x in args.source_ref if x.strip()]
    core = {
        "project_id": args.project_id.strip(),
        "competition": args.competition.strip(),
        "agency": args.agency.strip(),
        "entry_id": args.entry_id.strip(),
        "submission_stage": args.submission_stage.strip(),
        "submission_revision": args.submission_revision.strip(),
        "artifact_id": args.artifact_id.strip(),
        "artifact_type": args.artifact_type.strip().upper(),
        "board_no": args.board_no.strip(),
        "page_no": args.page_no,
        "drawing_name": args.drawing_name.strip(),
        "representation_mode": args.mode.upper().strip(),
        "technique": args.technique.strip(),
        "outcome": outcome,
        "state": state,
        "why": args.why.strip(),
        "reviewer_signal": args.reviewer_signal.strip(),
        "failure_mode": args.failure_mode.strip(),
        "artifact_refs": artifact_refs,
        "source_refs": source_refs,
    }
    record = {
        "record_version": "ARCHCOMP_REP_LEARNING_V1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "authority": "ARCHITECTURE_WORK_OS_EVIDENCE_CANDIDATE_ONLY",
        "promotion_authorized": False,
        "raw_evidence_copied": False,
        **core,
        "evidence_fingerprint_sha256": fingerprint(json.dumps(core, ensure_ascii=False, sort_keys=True)),
    }

    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record, ledger
def summarize(ledger_path):
    ledger = Path(ledger_path) if ledger_path else DEFAULT_LEDGER
    if not ledger.is_absolute():
        ledger = (Path.cwd() / ledger).resolve()
    rows = []
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    by_mode = {}
    by_competition = {}
    for row in rows:
        mode = row.get("representation_mode") or "UNKNOWN"
        bucket = by_mode.setdefault(mode, {"count": 0, "success": 0, "partial": 0, "failure": 0})
        bucket["count"] += 1
        outcome = row.get("outcome")
        if outcome == "SUCCESS":
            bucket["success"] += 1
        elif outcome == "PARTIAL":
            bucket["partial"] += 1
        elif outcome == "FAILURE":
            bucket["failure"] += 1

        competition_key = f"{row.get('agency') or 'UNKNOWN'}::{row.get('competition') or row.get('project_id') or 'UNKNOWN'}"
        cb = by_competition.setdefault(competition_key, {"record_count": 0, "entry_ids": set(), "artifact_ids": set()})
        cb["record_count"] += 1
        if row.get("entry_id"):
            cb["entry_ids"].add(row["entry_id"])
        if row.get("artifact_id"):
            cb["artifact_ids"].add(row["artifact_id"])

    by_competition_out = {
        key: {
            "record_count": value["record_count"],
            "entry_count": len(value["entry_ids"]),
            "artifact_count": len(value["artifact_ids"])
        }
        for key, value in by_competition.items()
    }

    return {
        "ledger": str(ledger),
        "record_count": len(rows),
        "by_mode": by_mode,
        "by_competition": by_competition_out,
        "promotion_authorized": False,
        "rule": "Evidence supports review; it never auto-promotes a technique to CURRENT_BEST."
    }

def parse_args():
    p = argparse.ArgumentParser(description="Append-only architecture competition representation learning evidence.")
    p.add_argument("--ledger", default="")
    p.add_argument("--summary", action="store_true")
    p.add_argument("--project-id", default="")
    p.add_argument("--competition", default="")
    p.add_argument("--agency", default="")
    p.add_argument("--entry-id", default="")
    p.add_argument("--submission-stage", default="")
    p.add_argument("--submission-revision", default="")
    p.add_argument("--artifact-id", default="")
    p.add_argument("--artifact-type", default="DRAWING")
    p.add_argument("--board-no", default="")
    p.add_argument("--page-no", type=int, default=None)
    p.add_argument("--drawing-name", default="")
    p.add_argument("--mode", default="")
    p.add_argument("--technique", default="")
    p.add_argument("--outcome", default="OBSERVATION_ONLY")
    p.add_argument("--state", default="CASE")
    p.add_argument("--why", default="")
    p.add_argument("--reviewer-signal", default="")
    p.add_argument("--failure-mode", default="")
    p.add_argument("--artifact-ref", action="append", default=[])
    p.add_argument("--source-ref", action="append", default=[])
    return p.parse_args()
def main():
    args = parse_args()
    if args.summary:
        print(json.dumps(summarize(args.ledger), ensure_ascii=False, indent=2))
        return 0

    if not args.project_id or not args.entry_id or not args.artifact_id or not args.mode or not args.technique:
        raise SystemExit("--project-id, --entry-id, --artifact-id, --mode, --technique are required unless --summary is used")

    record, ledger = append_record(args)
    print(json.dumps({
        "ok": True,
        "ledger": str(ledger),
        "record_id": record["evidence_fingerprint_sha256"][:24],
        "state": record["state"],
        "promotion_authorized": False
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
