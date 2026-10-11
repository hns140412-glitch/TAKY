#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"TOOLS"/"ARCHIGROW_PROJECT_LEARN.py"

spec=importlib.util.spec_from_file_location("archigrow_project_learn",TOOL)
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

def args(tmp, **kw):
    base=dict(
        ledger=str(Path(tmp)/"project-evidence.jsonl"),
        lineage_ledger=str(Path(tmp)/"grow-lineage.jsonl"),
        project_id="P-001", case_id="CASE-001",
        project_source_role="COMPANY_PROJECT", project_type="OFFICE",
        stage="DESIGN", revision="R1", state="CASE", outcome="SUCCESS",
        evidence_grade="A_PRIMARY_VERIFIED", access_class="INTERNAL",
        golden_candidate=False, anonymized=False, client_confidential=True,
        quality_criterion="Reviewer can trace design logic to verified constraints.",
        interpretation="Keep site/legal facts locked and expose the design response.",
        design_decision="Separate fixed constraints from option variables.",
        implementation_move="Bind CAD/Excel checks to report diagrams.",
        result_evidence="Issued internal review package passed source cross-check.",
        gap_analysis="", why="Trace reduced rework.", reusable_strategy="",
        failure_mode="", constraint_tag=["FAR","PARKING"],
        toolchain_tag=["CAD","EXCEL","PPT"], output_type=["REPORT"],
        source_ref=["PROJECT:P-001:REVIEW:R1"], artifact_ref=["ARTIFACT:REPORT:R1"]
    )
    base.update(kw)
    return SimpleNamespace(**base)

class TestArchitectureCompanyEvidence(unittest.TestCase):
    def test_append_idempotent_and_lineage(self):
        with tempfile.TemporaryDirectory() as td:
            first, ledger, dup=M.append_record(args(td))
            self.assertFalse(dup)
            self.assertFalse(first["promotion_authorized"])
            self.assertFalse(first["authority_transfer"])
            self.assertFalse(first["raw_evidence_copied"])
            self.assertEqual(first["state"],"CASE")
            self.assertTrue(first["trace_digest_sha256"])
            second, _, dup2=M.append_record(args(td))
            self.assertTrue(dup2)
            self.assertEqual(first["evidence_fingerprint_sha256"],second["evidence_fingerprint_sha256"])
            rows=[json.loads(x) for x in Path(ledger).read_text(encoding="utf-8").splitlines() if x.strip()]
            self.assertEqual(len(rows),1)
            lineage=[json.loads(x) for x in (Path(td)/"grow-lineage.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
            self.assertEqual(len(lineage),2)
            self.assertEqual({x["stage"] for x in lineage},{"RAW","LEARNING"})

    def test_required_trace_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"TRACE_INTERPRETATION_REQUIRED"):
                M.append_record(args(td,interpretation=""))

    def test_strategy_requires_reusable_strategy(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"REUSABLE_STRATEGY_REQUIRED"):
                M.append_record(args(td,state="STRATEGY",reusable_strategy=""))

    def test_failure_lesson_requires_failure_mode(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"FAILURE_MODE_REQUIRED"):
                M.append_record(args(td,state="FAILURE_LESSON",outcome="FAILURE",failure_mode=""))

    def test_confidentiality_and_golden_candidate_guards(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"CLIENT_CONFIDENTIAL_CANNOT_BE_PUBLIC_SOURCE"):
                M.append_record(args(td,access_class="PUBLIC_SOURCE"))
            with self.assertRaisesRegex(ValueError,"ANONYMIZATION_REQUIRED_FOR_SHAREABLE"):
                M.append_record(args(td,access_class="SHAREABLE_ANONYMIZED",client_confidential=False,anonymized=False))
            with self.assertRaisesRegex(ValueError,"GOLDEN_CANDIDATE_COMPANY_PROJECT_REQUIRED"):
                M.append_record(args(td,golden_candidate=True,project_source_role="PUBLIC_REFERENCE_CASE",client_confidential=False))
            with self.assertRaisesRegex(ValueError,"GOLDEN_CANDIDATE_EVIDENCE_GRADE_INSUFFICIENT"):
                M.append_record(args(td,golden_candidate=True,evidence_grade="D_OBSERVATION"))

    def test_golden_candidate_is_never_selected_or_promoted(self):
        with tempfile.TemporaryDirectory() as td:
            record, _, dup=M.append_record(args(td,golden_candidate=True))
            self.assertFalse(dup)
            self.assertTrue(record["golden_project_candidate"])
            self.assertFalse(record["promotion_authorized"])
            summary=M.summarize(str(Path(td)/"project-evidence.jsonl"))
            self.assertEqual(summary["golden_candidate_count"],1)
            self.assertFalse(summary["promotion_authorized"])

    def test_invalid_project_source_role_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"SOURCE_ROLE_INVALID"):
                M.append_record(args(td,project_source_role="FOO"))

    def test_lineage_failure_never_leaves_evidence_row(self):
        with tempfile.TemporaryDirectory() as td:
            original=M.materialize
            calls={"n":0}
            def fail_second(event, ledger):
                calls["n"]+=1
                return {"ok":calls["n"]==1}
            M.materialize=fail_second
            try:
                with self.assertRaisesRegex(RuntimeError,"GROW_LINEAGE_MATERIALIZATION_FAILED"):
                    M.append_record(args(td))
            finally:
                M.materialize=original
            evidence=Path(td)/"project-evidence.jsonl"
            self.assertFalse(evidence.exists() and evidence.read_text(encoding="utf-8").strip(),
                             "evidence row must not exist when lineage materialization fails")

if __name__=="__main__":
    unittest.main()
