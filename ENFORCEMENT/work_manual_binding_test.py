#!/usr/bin/env python3
"""Offline regression for the existing TAKY task/manual/review loop."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import unittest

from codex_task_contract_builder import build
from codex_task_contract_validator import validate
from executor_review_loop import review
from executor_transport import build_envelope
from executor_cycle import run as run_cycle

FIXTURES = Path(__file__).with_name("fixtures")


def case():
    task = json.loads((FIXTURES / "executor_review_task.json").read_text(encoding="utf-8"))
    task["allowed_change_scope"] = task["change_scope"]["allowed"]
    task["required_validation"] = task["validation"]["required"]
    task["work_manual_skill_id"] = "runtime-e2e"
    built = build(task)
    if not built["pass"]:
        raise AssertionError(built["detected"])
    report = json.loads((FIXTURES / "executor_review_pass.json").read_text(encoding="utf-8"))
    contract = built["task_contract"]
    binding = contract["work_manual_binding"]
    report["work_manual_evidence"] = {
        "skill_id": binding["skill_id"],
        "version_sha256": binding["version_sha256"],
        "execution_implication": "Run the bounded runtime checks and capture evidence.",
        "evidence_ref": "LOCAL_TEST:runtime-check-01",
    }
    return contract, report


class WorkManualContractTest(unittest.TestCase):
    def test_approved_existing_skill_pinned_and_reviewed(self):
        contract, report = case()
        self.assertEqual(validate(contract), [])
        self.assertEqual(contract["work_manual_binding"]["source"], "TAKY_SKILL_MANIFEST")
        outcome = review(contract, report)
        self.assertTrue(outcome["pass"], outcome["defects"])
        manual = [x for x in outcome["evidence"] if x["kind"] == "work_manual"][0]
        self.assertEqual(manual["status"], "EXECUTOR_REPORTED_NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(outcome["review_decision"], "HUMAN_APPROVAL")

    def test_unknown_and_traversal_skills_hold(self):
        contract, _ = case()
        for name in ("does-not-exist", "../secrets", "C:/absolute/path"):
            payload = copy.deepcopy(contract)
            payload["work_manual_binding"]["skill_id"] = name
            self.assertTrue(any(x.startswith("WORK_MANUAL_") for x in validate(payload)))

    def test_changed_content_hash_holds(self):
        contract, _ = case()
        contract["work_manual_binding"]["version_sha256"] = "0" * 64
        self.assertIn("WORK_MANUAL_VERSION_DRIFT", validate(contract))

    def test_injected_manual_command_holds(self):
        contract, _ = case()
        contract["work_manual_binding"]["command"] = "run arbitrary shell"
        self.assertIn("WORK_MANUAL_BINDING_INVALID", validate(contract))

    def test_forged_task_manual_cannot_pass_through_matching_executor_claim(self):
        contract, report = case()
        contract["work_manual_binding"]["version_sha256"] = "0" * 64
        report["work_manual_evidence"]["version_sha256"] = "0" * 64
        outcome = review(contract, report)
        self.assertFalse(outcome["pass"])
        self.assertIn("WORK_MANUAL_VERSION_DRIFT", [d["code"] for d in outcome["defects"]])

    def test_malformed_manual_binding_fails_closed_without_crashing(self):
        contract, report = case()
        contract["work_manual_binding"] = "malicious manual"
        outcome = review(contract, report)
        self.assertFalse(outcome["pass"])
        self.assertIn("WORK_MANUAL_BINDING_INVALID", [d["code"] for d in outcome["defects"]])

    def test_existing_real_intake_artifact_readback(self):
        repo = Path(__file__).resolve().parents[1]
        name = "REV-690e86dd01ee35c0350b7241.json"
        path = (repo.parents[1].parent / "TAKY-SOURCE-VAULT" / "data"
                / "direction_intake" / "review_events" / name)
        if not path.is_file():
            self.skipTest("Real local review event not mounted on this machine")
        contract, report = case()
        contract["work_manual_binding"]["artifact_evidence"] = {
            "anchor": "SOURCE_VAULT_REVIEW_EVENTS",
            "name": name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "expected_fields": {
                "event_id": name.removesuffix(".json"),
                "review_stage": "ANALYSIS_RECORDED",
                "index_state": "REVIEW_REFERENCE_ONLY",
                "forming_state": "CANDIDATE_ONLY",
                "canonical_promotion": False,
            },
        }
        report["work_manual_evidence"]["evidence_ref"] = (
            "SOURCE_VAULT_REVIEW_EVENTS:" + name
        )
        self.assertEqual(validate(contract), [])
        reviewed = review(contract, report)
        self.assertTrue(reviewed["pass"], reviewed["defects"])
        self.assertEqual([x for x in reviewed["evidence"] if x["kind"] == "work_manual"][0]["status"],
                         "LOCAL_ARTIFACT_READBACK_VERIFIED")
        drift = copy.deepcopy(contract)
        drift["work_manual_binding"]["artifact_evidence"]["sha256"] = "0" * 64
        self.assertIn("WORK_MANUAL_ARTIFACT_SHA256_MISMATCH",
                      [x["code"] for x in review(drift, report)["defects"]])
        bad_field = copy.deepcopy(contract)
        bad_field["work_manual_binding"]["artifact_evidence"]["expected_fields"]["canonical_promotion"] = True
        self.assertIn("WORK_MANUAL_ARTIFACT_POSTCONDITION_MISMATCH",
                      [x["code"] for x in review(bad_field, report)["defects"]])
        traversal = copy.deepcopy(contract)
        traversal["work_manual_binding"]["artifact_evidence"]["name"] = "../private.json"
        self.assertIn("WORK_MANUAL_ARTIFACT_NAME_INVALID", validate(traversal))

    def test_missing_manual_evidence_returns_rework_not_success(self):
        contract, report = case()
        del report["work_manual_evidence"]
        outcome = review(contract, report)
        self.assertFalse(outcome["pass"])
        self.assertIn("WORK_MANUAL_EVIDENCE_MISSING",
                      [x["code"] for x in outcome["defects"]])
        self.assertEqual(outcome["rework_actions"][0]["route"], "RECHECK_MANUAL_BINDING")
        self.assertFalse(outcome["rework_actions"][0]["manual_auto_edit"])

    def test_wrong_manual_version_returns_rework(self):
        contract, report = case()
        report["work_manual_evidence"]["version_sha256"] = "0" * 64
        out = review(contract, report)
        self.assertIn("WORK_MANUAL_VERSION_MISMATCH", [d["code"] for d in out["defects"]])

    def test_confirmed_failure_routes_fix_and_candidate_without_promotion(self):
        contract, report = case()
        report["acceptance_results"][0]["status"] = "FAIL"
        report["validation_results"]["relevant_tests"]["status"] = "FAIL"
        report["confirmed_failure_event"] = {
            "outcome_state": "FAILED_CONFIRMED", "task_family": "RUNTIME",
            "source_ref": "LOCAL_TEST:runtime-check-02",
            "invariant": "persist_after_navigation", "expected": True, "observed": False,
        }
        out = review(contract, report)
        self.assertEqual(out["review_decision"], "REWORK")
        routes = [x["route"] for x in out["rework_actions"]]
        self.assertIn("FIX_IMPLEMENTATION_AND_REGRESSION", routes)
        self.assertEqual(routes.count("FIX_IMPLEMENTATION_AND_REGRESSION"), 1)
        candidate = out["regression_case_candidate"]
        self.assertEqual(candidate["status"], "CANDIDATE")
        self.assertFalse(candidate["auto_promote"])
        self.assertTrue(all(not x["blind_retry_allowed"] for x in out["rework_actions"]))

    def test_transport_to_review_to_approval_without_executor_call(self):
        contract, report = case()
        dispatched = build_envelope(contract)
        self.assertTrue(dispatched["pass"])
        envelope = dispatched["dispatch_envelope"]
        result = {
            "task_id": contract["task_id"], "provider": "CODEX",
            "task_contract_sha256": envelope["task_contract_sha256"],
            "completion_report": report,
        }
        outcome = run_cycle(envelope, result)
        self.assertTrue(outcome["pass"], outcome["detected"])
        self.assertEqual(outcome["transition"]["current_state"], "HUMAN_APPROVAL")
        self.assertFalse(outcome["external_executor_invocation_verified"])

    def test_transport_to_review_to_rework_on_manual_mismatch(self):
        contract, report = case()
        report["work_manual_evidence"]["version_sha256"] = "0" * 64
        envelope = build_envelope(contract)["dispatch_envelope"]
        result = {
            "task_id": contract["task_id"], "provider": "CODEX",
            "task_contract_sha256": envelope["task_contract_sha256"],
            "completion_report": report,
        }
        outcome = run_cycle(envelope, result)
        self.assertEqual(outcome["review"]["review_decision"], "REWORK")
        self.assertEqual(outcome["transition"]["current_state"], "REWORK")
        self.assertEqual(outcome["review"]["rework_actions"][0]["route"],
                         "RECHECK_MANUAL_BINDING")

    def test_unverified_failure_cannot_create_regression_candidate(self):
        contract, report = case()
        report["validation_results"]["regression"]["status"] = "FAIL"
        report["confirmed_failure_event"] = {
            "outcome_state": "OUTCOME_UNKNOWN", "task_family": "RUNTIME",
            "source_ref": "LOCAL_TEST:unknown",
            "invariant": "checks_ran", "expected": True, "observed": False,
        }
        out = review(contract, report)
        self.assertFalse(out["pass"])
        self.assertIsNone(out["regression_case_candidate"])


if __name__ == "__main__":
    unittest.main()
