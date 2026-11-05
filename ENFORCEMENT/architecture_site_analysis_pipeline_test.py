#!/usr/bin/env python3
"""Offline integration regression for the optional site analysis pipeline stage."""
import copy
import hashlib
import importlib.util
import json
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = load(ROOT / "TOOLS" / "ARCHIGROW_PIPELINE_RUN.py", "site_pipeline")
R = load(ROOT / "TOOLS" / "ARCHIGROW_WORKFLOW_ROUTER.py", "site_router")
F = load(ROOT / "ENFORCEMENT" / "architecture_site_analysis_report_test.py", "site_fixture")


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


class SiteAnalysisPipelineTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / ("site_analysis_pipeline_test_" + uuid.uuid4().hex)
        self.root.mkdir()
        self.addCleanup(shutil.rmtree, self.root)
        self.source = write(self.root / "source.json", F.source())
        self.manifest = self.root / "pipeline.json"
        self.out = self.root / "run"
        self.configure({"site_source_receipt": "source.json"})

    def configure(self, cfg, stages=None):
        write(self.manifest, {"schema": "ARCHIGROW_PIPELINE_MANIFEST_V1",
                              "project_id": F.PID, "stages": stages or ["SITE_ANALYSIS"],
                              "inputs": {"site_analysis": cfg}})

    def run_stage(self):
        summary = P.run(self.manifest, self.out)
        receipt = json.loads((self.out / "receipts" / "SITE_ANALYSIS.json").read_text(encoding="utf-8"))
        return summary, receipt

    def test_design_parameter_hold_still_generates_source_bound_report(self):
        summary, receipt = self.run_stage()
        self.assertEqual((summary["status"], receipt["status"]), ("PASS", "PASS"))
        self.assertEqual(receipt["summary"]["source_status"], "PASS")
        self.assertFalse(summary["legal_feasibility_authorized"])
        self.assertFalse(summary["promotion_authorized"])
        self.assertEqual(summary["ledger_write"], "NOT_PERFORMED")
        outputs = {Path(item["ref"]).name: item for item in receipt["outputs"]}
        for name in ("source.json", "analysis_manifest.json", "site_analysis.html", "site_map.svg", "site_analysis.pptx"):
            self.assertIn(name, outputs)
            self.assertEqual(outputs[name]["sha256"], hashlib.sha256(Path(outputs[name]["ref"]).read_bytes()).hexdigest())
        report = json.loads((self.out / "stages" / "SITE_ANALYSIS" / "analysis_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((report["source_status"], report["sections"]["site_source"]["collector_status"]), ("PASS", "HOLD"))
        self.assertEqual(report["design_status"], "NOT_REQUIRED_NOT_PROVIDED")
        self.assertEqual(report["page_count"], 7)
        self.assertNotIn("MASSING", [stage["stage"] for stage in summary["stages"]])

    def test_unchanged_reuses_and_each_source_hash_invalidates(self):
        self.assertEqual(self.run_stage()[1]["status"], "PASS")
        self.assertEqual(self.run_stage()[1]["status"], "REUSED_LAST_PASS")
        context = write(self.root / "context.json", {"schema": "ARCHIGROW_CONTEXT_OBSTACLES_V1", "project_id": F.PID,
                                                      "source_class": "SYNTHETIC_FIXTURE", "obstacles": []})
        self.configure({"site_source_receipt": "source.json", "context": "context.json"})
        self.assertEqual(self.run_stage()[1]["status"], "PASS")
        self.assertEqual(self.run_stage()[1]["status"], "REUSED_LAST_PASS")
        data = json.loads(context.read_text(encoding="utf-8"))
        data["source_class"] = "SYNTHETIC_FIXTURE_REV_2"
        write(context, data)
        self.assertEqual(self.run_stage()[1]["status"], "PASS")
        self.assertEqual(self.run_stage()[1]["status"], "REUSED_LAST_PASS")
        data = json.loads(self.source.read_text(encoding="utf-8"))
        data["eum"]["address"] = "SYNTHETIC REVISED ADDRESS"
        write(self.source, data)
        self.assertEqual(self.run_stage()[1]["status"], "PASS")

    def test_identity_missing_invalid_and_conflicting_inputs_hold(self):
        source = F.source()
        source["project_id"] = "OTHER"
        write(self.source, source)
        _, receipt = self.run_stage()
        self.assertEqual((receipt["status"], receipt["failure_class"]), ("HOLD", "SITE_ANALYSIS_EVIDENCE_HOLD"))
        self.assertIn("PROJECT_ID_MISMATCH", receipt["detail"])
        write(self.source, {"project_id": F.PID, "status": "HOLD", "failure_class": "NO_EVIDENCE"})
        _, receipt = self.run_stage()
        self.assertEqual((receipt["status"], receipt["summary"]["source_status"]), ("HOLD", "HOLD"))
        source = F.source()
        source["eum"]["evidence_sha256"] = "invalid"
        write(self.source, source)
        _, receipt = self.run_stage()
        self.assertIn("SOURCE_EVIDENCE_HASH_MISSING", receipt["detail"])
        self.configure({"site_source_receipt": "absent.json"})
        _, receipt = self.run_stage()
        self.assertEqual(receipt["failure_class"], "SITE_SOURCE_RECEIPT_MISSING")
        self.configure({"site_source_receipt": "source.json", "site_source_input": "source.json"})
        _, receipt = self.run_stage()
        self.assertEqual(receipt["failure_class"], "SITE_SOURCE_EXACTLY_ONE_REQUIRED")

    def test_optional_solar_and_massing_hashes_and_report_failure(self):
        massing = write(self.root / "massing.json", {"schema": "ARCHIGROW_MASSING_RESULT_V1", "project_id": F.PID,
                                                      "options": [], "rule_source_status": "UNVERIFIED_DEMO"})
        solar = write(self.root / "solar.json", {"schema": "ARCHIGROW_SOLAR_STUDY_REPORT_V1", "project_id": F.PID,
                                                  "result_status": "LIMITED", "dates": []})
        self.configure({"site_source_receipt": "source.json", "massing": "massing.json", "solar": "solar.json"})
        self.assertEqual(self.run_stage()[1]["status"], "PASS")
        self.assertEqual(self.run_stage()[1]["status"], "REUSED_LAST_PASS")
        for path in (solar, massing):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["fixture_revision"] = path.stem
            write(path, data)
            self.assertEqual(self.run_stage()[1]["status"], "PASS")
            self.assertEqual(self.run_stage()[1]["status"], "REUSED_LAST_PASS")
        report = P.mod("ARCHIGROW_SITE_ANALYSIS_REPORT.py")
        with patch.object(report, "_pptx", side_effect=RuntimeError("save failed")):
            _, receipt = self.run_stage_forced()
        self.assertEqual((receipt["status"], receipt["summary"]["report_status"]), ("HOLD", "HOLD"))
        self.assertNotIn("site_analysis.pptx", [Path(item["ref"]).name for item in receipt["outputs"]])

    def run_stage_forced(self):
        summary = P.run(self.manifest, self.out, force=True)
        receipt = json.loads((self.out / "receipts" / "SITE_ANALYSIS.json").read_text(encoding="utf-8"))
        return summary, receipt

    def test_router_template_and_unbound_stage(self):
        template = R.manifest_template(F.PID, "SITE_ANALYSIS_REPORT")
        self.assertEqual(template["stages"], ["SITE_ANALYSIS"])
        self.assertEqual(template["inputs"]["site_analysis"], {"site_source_receipt": None})
        write(self.manifest, template)
        summary, receipt = self.run_stage()
        self.assertEqual((summary["status"], receipt["failure_class"]), ("BLOCKED", "INPUT_NOT_BOUND"))
        self.assertEqual(R.plan(F.PID, "SITE_ANALYSIS_REPORT")["steps"][0]["capability"], "SITE_ANALYSIS")

    def test_collector_input_is_consumed_and_never_cached(self):
        write(self.root / "source_input.json", {"schema": "ARCHIGROW_SITE_SOURCE_INPUT_V1", "project_id": F.PID, "pnu": F.PNU})
        self.configure({"site_source_input": "source_input.json"})
        calls = []

        def collector(_input, out):
            calls.append(_input)
            Path(out).mkdir(parents=True, exist_ok=True)
            write(Path(out) / "site_source_receipt.json", F.source())
            return {**copy.deepcopy(F.source()), "raw_refs": []}

        parcel = P.mod("ARCHIGROW_PARCEL_SOURCE.py")
        with patch.object(parcel, "run", side_effect=collector):
            first = self.run_stage()[1]
            second = self.run_stage()[1]
        self.assertEqual((first["status"], second["status"]), ("PASS", "PASS"))
        self.assertEqual(len(calls), 2)
        self.assertIn("site_source_receipt.json", [Path(item["ref"]).name for item in second["outputs"]])


if __name__ == "__main__":
    unittest.main()
