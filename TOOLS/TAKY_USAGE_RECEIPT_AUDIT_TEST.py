#!/usr/bin/env python3
"""Offline tests of TAKY receipt evidence classification; never call models."""
import json
import os
import time
import tempfile
import unittest
from pathlib import Path
from TAKY_USAGE_RECEIPT_AUDIT import audit, quota_pair, audited_receipt

TASK_ID = "a" * 32


def receipt(state="COMPLETE_UNVERIFIED", **overrides):
    row = {
        "task_id": TASK_ID, "executor": "Claude", "state": state,
        "started_utc": "2026-10-15T00:01:00+00:00",
        "finished_utc": "2026-10-15T00:03:00+00:00",
        "quota_before": {"fiveHour": 20, "week": 30},
        "quota_after": {"fiveHour": 23, "week": 33},
        "quota_before_observed_at": "2026-10-15T00:00:00+00:00",
        "quota_after_observed_at": "2026-10-15T00:04:00+00:00",
        "result": "DO NOT LEAK THIS OR PROMOTE TO PASS",
    }
    row.update(overrides)
    return row


class ReceiptAuditTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def save(self, row, prefix="TAKY_ROUTED_", suffix=TASK_ID):
        path = self.root / (prefix + suffix + ".json")
        path.write_text(json.dumps(row), encoding="utf-8")
        return path

    def test_independent_times_show_unattributed_change(self):
        self.save(receipt())
        result = audit(self.root)
        self.assertEqual(result["validReceipts"], 1)
        self.assertEqual(result["quotaEvidenceStates"], {
            "OBSERVED_DIFFERENCE_NOT_TASK_ATTRIBUTED": 1})
        self.assertEqual(result["outcomes"]["COMPLETE_UNVERIFIED"], 1)
        self.assertEqual(result["verifiedSuccessfulOutcomes"], 0)
        self.assertIsNone(result["verifiedCreditSavingsPercent"])
        self.assertEqual(result["samples"][0]["quota"]["observedDeltaPercentagePoints"],
                         {"fiveHour": 3.0, "week": 3.0})
        self.assertNotIn("DO NOT LEAK", json.dumps(result))

    def test_same_cached_snapshot_no_delta(self):
        row = receipt(quota_after_observed_at="2026-10-15T00:00:00+00:00")
        self.save(row)
        self.assertEqual(audit(self.root)["quotaEvidenceStates"],
                         {"SAME_OR_REVERSED_CACHED_SNAPSHOT": 1})

    def test_after_not_bracketing_execution(self):
        self.save(receipt(quota_after_observed_at="2026-10-15T00:02:00+00:00"))
        self.assertEqual(audit(self.root)["quotaEvidenceStates"],
                         {"QUOTA_NOT_BRACKETING_EXECUTION": 1})

    def test_missing_values_are_not_zero(self):
        self.save(receipt(quota_before=None))
        self.assertEqual(audit(self.root)["quotaEvidenceStates"],
                         {"QUOTA_VALUES_MISSING": 1})

    def test_no_receipts_is_no_evidence(self):
        result = audit(self.root)
        self.assertEqual(result["scanned"], 0)
        self.assertIsNone(result["verifiedCreditSavingsPercent"])

    def test_failed_codex_stays_failed(self):
        self.save({"id": TASK_ID, "executor": "Codex", "status": "FAILED",
                   "result": "model was not called"}, prefix="CODEX_CHAT_")
        result = audit(self.root)
        self.assertEqual(result["outcomes"]["FAILED"], 1)
        self.assertEqual(result["verifiedSuccessfulOutcomes"], 0)

    def test_timeout_outcome_unknown_is_auditable(self):
        self.save(receipt("OUTCOME_UNKNOWN", quota_after=None))
        result = audit(self.root)
        self.assertEqual(result["outcomes"]["OUTCOME_UNKNOWN"], 1)
        self.assertEqual(result["verifiedSuccessfulOutcomes"], 0)

    def test_forged_pass_is_rejected(self):
        self.save(receipt("PASS"))
        result = audit(self.root)
        self.assertEqual(result["validReceipts"], 0)
        self.assertEqual(result["invalidReceipts"], 1)

    def test_task_id_filename_mismatch_is_rejected(self):
        self.save(receipt(), suffix="b" * 32)
        self.assertEqual(audit(self.root)["validReceipts"], 0)

    def test_untrusted_result_is_never_rendered(self):
        self.save(receipt(result={"credentials": "sensitive"}))
        self.assertNotIn("sensitive", json.dumps(audit(self.root)))

    def test_empty_prepared_execution_receipt_is_visible_not_success(self):
        path = self.root / ("TAKY_ROUTED_" + TASK_ID + ".json")
        path.write_bytes(b"")
        result = audit(self.root)
        self.assertEqual(result["validReceipts"], 1)
        self.assertEqual(result["outcomes"]["RESERVED_NO_FINAL_RECEIPT"], 1)
        self.assertEqual(result["samples"][0]["quota"]["status"], "NO_RECEIPT_QUOTA_VALUES")
        self.assertIsNone(result["verifiedCreditSavingsPercent"])

    def test_stale_empty_execution_receipt_is_not_silently_lost(self):
        path = self.root / ("TAKY_ROUTED_" + TASK_ID + ".json")
        path.write_bytes(b"")
        old = time.time() - 360
        os.utime(path, (old, old))
        result = audit(self.root)
        self.assertEqual(result["outcomes"]["STALE_UNFINALIZED_RESERVATION"], 1)
        self.assertEqual(result["verifiedSuccessfulOutcomes"], 0)

    def test_untrusted_empty_file_name_is_invalid(self):
        (self.root / "TAKY_ROUTED_not-an-id.json").write_bytes(b"")
        self.assertEqual(audit(self.root)["invalidReceipts"], 1)

    def test_bounded_limit(self):
        with self.assertRaises(ValueError):
            audit(self.root, limit=101)
        with self.assertRaises(ValueError):
            audit(self.root, limit=0)


if __name__ == "__main__":
    unittest.main()
