#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "TOOLS" / "ARCHIGROW_COMPETITION_LEARN.py"

spec = importlib.util.spec_from_file_location("archlearn", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Args:
    ledger = str(Path(tempfile.gettempdir()) / "archcomp-learning-test.jsonl")
    lineage_ledger = str(Path(tempfile.gettempdir()) / "archcomp-grow-lineage-test.jsonl")
    project_id = "TEST-001"
    competition = "TEST"
    agency = "LH"
    entry_id = "ENTRY-01"
    submission_stage = "FINAL"
    submission_revision = "R1"
    artifact_id = "BOARD-01-SECTION-A"
    artifact_type = "DRAWING"
    board_no = "1"
    page_no = None
    drawing_name = "주요 단면도"
    mode = "SECTION"
    technique = "sectional_perspective"
    outcome = "SUCCESS"
    state = "CASE"
    why = "Section made the vertical public-space relationship legible."
    reviewer_signal = "Reviewer understood the atrium sequence immediately."
    failure_mode = ""
    artifact_ref = ["artifact:section-v3"]
    source_ref = ["source:verified-section-v2"]

def main():
    ledger = Path(Args.ledger)
    lineage_path = Path(Args.lineage_ledger)
    ledger.unlink(missing_ok=True)
    lineage_path.unlink(missing_ok=True)

    record, out = mod.append_record(Args())
    assert out == ledger
    assert record["authority"] == "ARCHITECTURE_WORK_OS_EVIDENCE_CANDIDATE_ONLY"
    assert record["promotion_authorized"] is False
    assert record["raw_evidence_copied"] is False
    assert record["representation_mode"] == "SECTION"
    assert record["outcome"] == "SUCCESS"
    assert record["agency"] == "LH"
    assert record["entry_id"] == "ENTRY-01"
    assert record["artifact_id"] == "BOARD-01-SECTION-A"
    assert record["record_version"] == "ARCHCOMP_REP_LEARNING_V2"
    assert lineage_path.exists()
    lineage = [json.loads(x) for x in lineage_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert [x["stage"] for x in lineage] == ["RAW", "LEARNING"]
    assert all(x["grow_domain"] == "ARCHI_GROW" for x in lineage)
    assert record["grow_lineage_event_id"] == lineage[-1]["event_id"]

    summary = mod.summarize(str(ledger))
    assert summary["record_count"] == 1
    assert summary["by_mode"]["SECTION"]["success"] == 1
    assert summary["by_competition"]["LH::TEST"]["entry_count"] == 1
    assert summary["by_competition"]["LH::TEST"]["artifact_count"] == 1
    assert summary["promotion_authorized"] is False

    row = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert row["artifact_refs"] == ["artifact:section-v3"]
    assert row["source_refs"] == ["source:verified-section-v2"]

    print("PASS: architecture competition append-only learning evidence")

if __name__ == "__main__":
    raise SystemExit(main())
