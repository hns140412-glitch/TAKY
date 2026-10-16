"""Explicit local browser capture -> verified SYSTEM_GROW feedback candidate.

A live *local* browser run is verified against its saved config, screenshot,
accessibility state and source/code lineage. No semantic approval, operational
Central write, automatic application rollout, or curriculum learning.
"""
import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import central_review_source_intake as intake
import global_source_learning_feedback as flow
import taky_central_source_factory as factory
from ai_execution_guard import _browser_runtime_receipt_verified

EVIDENCE = flow.EVIDENCE
RUN_ROOT = EVIDENCE / "UI_BROWSER_RECEIPTS"
RUN_PATTERN = re.compile(r"taky-live-[A-Za-z0-9_.:-]{3,83}$")
WORKS = {"TAKY-PLAYWRIGHT-SOURCE-PILOT", "TAKY-PLAYWRIGHT-SOURCE-MULTIAPP"}
MAX_RECEIPT_BYTES = 128_000


def _live_evidence(run_id):
    if not isinstance(run_id, str) or not RUN_PATTERN.fullmatch(run_id):
        raise ValueError("LIVE_RUN_ID_INVALID")
    root = RUN_ROOT.resolve(strict=True)
    folder = (root / run_id).resolve()
    if not folder.is_relative_to(root) or folder.name != run_id:
        raise ValueError("RUN_OUTSIDE_EVIDENCE_ROOT")
    if not folder.is_dir():
        raise ValueError("LIVE_RECEIPT_MISSING_OR_OVERSIZED")
    file = folder / "browser_receipt.json"
    if not file.is_file() or not 0 < file.stat().st_size <= MAX_RECEIPT_BYTES:
        raise ValueError("LIVE_RECEIPT_MISSING_OR_OVERSIZED")
    data_bytes = file.read_bytes()
    data = json.loads(data_bytes.decode("utf-8-sig"))
    if (data.get("schema") != "TAKY_UI_BROWSER_RUNTIME_RECEIPT_V2"
        or data.get("run_id") != run_id or data.get("work_id") not in WORKS
        or data.get("target_kind") != "LOOPBACK_APP"
        or data.get("release_approved") is not False):
        raise ValueError("LIVE_RECEIPT_SCOPE_INVALID")
    config_path = Path(data.get("config_path", "")).resolve(strict=True)
    if not config_path.is_relative_to(EVIDENCE.resolve(strict=True)):
        raise ValueError("LIVE_CONFIG_OUTSIDE_EVIDENCE_ROOT")
    context = {"work_id": data["work_id"], "screen_id": data["screen_id"],
        "run_id": run_id, "viewport": data["viewport"],
        "visual": {"rendered_screenshot": data["rendered_screenshot"]},
        "browser_runtime_receipt": {"path": str(file),
            "sha256": hashlib.sha256(data_bytes).hexdigest()}}
    if not _browser_runtime_receipt_verified(context):
        raise ValueError("LIVE_BROWSER_INDEPENDENT_GUARD_REJECTED")
    return context["browser_runtime_receipt"]["sha256"]


def verify_local_outcome(receipt, binding):
    """Readback verifier; an untrusted payload cannot self-declare success."""
    if not isinstance(receipt, dict):
        return False
    run_id = receipt.get("run_id", "")
    if isinstance(run_id, str) and run_id.startswith("taky-live-"):
        if (receipt.get("outcome") != "SUCCESS"
            or binding.get("owner") != "SYSTEM_GROW"
            or binding.get("consumer") != "TAKY_EXECUTION_EVIDENCE"
            or binding.get("consumer_revision") != flow.sha(flow.CODE.read_bytes())
            or binding.get("guard_revision") != flow.sha(flow.GUARD.read_bytes())):
            return False
        return receipt.get("evidence_sha256") == _live_evidence(run_id)
    return flow._verify_local_outcome(receipt, binding)


def consume_live_runtime(c, run_id):
    """Transactional capture receipt -> decision -> feedback -> next decision."""
    evidence_sha = _live_evidence(run_id)
    receipt = {"run_id": run_id, "outcome": "SUCCESS",
               "evidence_sha256": evidence_sha}
    c.execute("SAVEPOINT live_local_feedback")
    try:
        before = flow.technical_method_decision(c, outcome_verifier=verify_local_outcome)
        binding = before["binding"]
        existing = []
        decision_run = "TAKY-LIVE-DECISION-" + run_id
        for row in c.execute("SELECT event_id FROM event WHERE source_id=? AND kind=?",
                             (binding["source_id"], flow.DECISION_KIND)):
            data = flow._event_payload(c, row[0], flow.DECISION_KIND, binding["source_id"])
            if data["run_id"] == decision_run:
                existing.append((row[0], data))
        if len(existing) > 1:
            raise ValueError("LIVE_DECISION_AMBIGUOUS")
        if existing:
            decision_id, previous = existing[0]
            if (previous["binding"] != binding
                or previous["artifact_revision"] != before["artifact_revision"]):
                raise ValueError("LIVE_DECISION_REVISION_CHANGED")
        else:
            decision_id = flow.record_technical_method_decision(
                c, decision_run, outcome_verifier=verify_local_outcome)["decision_event_id"]
        feedback_id = flow.record_technical_feedback(
            c, decision_id, receipt, outcome_verifier=verify_local_outcome)
        after = flow.technical_method_decision(c, outcome_verifier=verify_local_outcome)
        result = {"status": "NEW_LOCAL_BROWSER_RUN_FEEDBACK_RECORDED",
            "run_id": run_id, "receipt_sha256": evidence_sha,
            "source_id": binding["source_id"], "raw_sha256": binding["raw_sha256"],
            "anchor_sha256": binding["anchor_sha256"],
            "forming_revision": before["artifact_revision"],
            "consumer_code_sha256": binding["consumer_revision"],
            "decision_event_id": decision_id, "feedback_event_id": feedback_id,
            "before": before["decision"], "after": after["decision"],
            "feedback_count": len(after["feedback"]),
            "semantic_approved": after["approved_local_consumption"],
            "knowledge_approved": after["knowledge_projection"]["authoritative"],
            "live_browser_evidence": True, "production_rollout": False,
            "current_written": False, "operational_db_written": False}
        c.execute("RELEASE SAVEPOINT live_local_feedback")
        return result
    except BaseException:
        c.execute("ROLLBACK TO SAVEPOINT live_local_feedback")
        c.execute("RELEASE SAVEPOINT live_local_feedback")
        raise


def reconcile_verified_live_receipts(c, *, max_runs=32):
    """Consume all bounded, verified local V2 receipts, once per run_id.

    A malformed candidate blocks the batch rather than producing partial PASS.
    Caller controls transaction/SQLite lifetime; no recurring watcher is started.
    """
    root = RUN_ROOT.resolve(strict=True)
    entries = sorted(p for p in root.iterdir()
                     if p.name.startswith("taky-live-") and p.is_dir())
    if len(entries) > max_runs:
        raise ValueError("LOCAL_RECONCILIATION_BUDGET_EXCEEDED")
    c.execute("SAVEPOINT local_reconciliation")
    try:
        before = c.execute("SELECT COUNT(*) FROM event WHERE kind=?",
                           (flow.FEEDBACK_KIND,)).fetchone()[0]
        results = []
        for entry in entries:
            if not RUN_PATTERN.fullmatch(entry.name):
                raise ValueError("LOCAL_RECONCILIATION_RUN_ID_INVALID")
            if entry.resolve() != entry or not entry.resolve().is_relative_to(root):
                raise ValueError("LOCAL_RECONCILIATION_PATH_CHANGED")
            results.append(consume_live_runtime(c, entry.name))
        after = c.execute("SELECT COUNT(*) FROM event WHERE kind=?",
                          (flow.FEEDBACK_KIND,)).fetchone()[0]
        report = {"status": "VERIFIED_LOCAL_RECEIPTS_RECONCILED",
                  "run_count": len(results),
                  "new_feedback_event_count": after - before,
                  "already_recorded_count": len(results) - (after - before),
                  "run_ids": [x["run_id"] for x in results],
                  "run_details": results,
                  "all_semantic_approval_blocked": all(not x["semantic_approved"]
                                                       for x in results),
                  "source_and_current_untouched": True}
        c.execute("RELEASE SAVEPOINT local_reconciliation")
        return report
    except BaseException:
        c.execute("ROLLBACK TO SAVEPOINT local_reconciliation")
        c.execute("RELEASE SAVEPOINT local_reconciliation")
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture-config", type=Path)
    mode.add_argument("--reconcile-existing", action="store_true")
    parser.add_argument("--persist-verified-feedback", action="store_true",
                        help="Append-only verified local technical feedback candidates")
    args = parser.parse_args()
    if args.persist_verified_feedback and not args.reconcile_existing:
        parser.error("PERSISTENCE_REQUIRES_RECONCILIATION")
    temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
    db_path = args.db.resolve()
    if (not db_path.is_relative_to(temp_root) or db_path == factory.DB.resolve()
        or db_path.suffix != ".sqlite3"):
        parser.error("LIVE_FEEDBACK_DISPOSABLE_DB_REQUIRED")
    if args.capture_config is not None:
        config_path = args.capture_config.resolve(strict=True)
        if not config_path.is_relative_to(EVIDENCE.resolve(strict=True)):
            parser.error("CAPTURE_CONFIG_OUTSIDE_EVIDENCE_ROOT")
        config = flow.load_json(config_path)
        run_id = config.get("run_id")
        if (not isinstance(run_id, str) or not RUN_PATTERN.fullmatch(run_id)
            or config.get("work_id") not in WORKS):
            parser.error("UNAUTHORIZED_LIVE_CAPTURE_SCOPE")
        runner = flow.CODE
        process = subprocess.run(["node", str(runner), str(config_path)],
                                 check=False, capture_output=True, text=True,
                                 encoding="utf-8", timeout=90)
        if process.returncode != 0:
            raise ValueError("BROWSER_CAPTURE_FAILED: " + process.stderr[-1000:])
        _live_evidence(run_id)
    with factory.connect(db_path) as c:
        base = intake.advance_verified_review_pipeline(c, intake.verified_documents())
        if args.reconcile_existing:
            local = reconcile_verified_live_receipts(c)
        else:
            local = consume_live_runtime(c, run_id)
    journal = None
    if args.persist_verified_feedback:
        from local_feedback_candidate_journal import persist
        journal = persist(local)
    print(json.dumps({"status": "LOCAL_LIVE_CONSUMPTION_E2E",
        "source_count": base["verified_source_count"],
        "anchor_count": base["durable_detail_units"],
        "feedback": local, "journal": journal},
        ensure_ascii=False))


if __name__ == "__main__":
    main()
