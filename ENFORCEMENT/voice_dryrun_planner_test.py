import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import voice_dryrun_planner as planner


class VoiceDryRunPlannerTest(unittest.TestCase):
    def test_current_request_is_one_call_explicit_allowance(self):
        result = planner.plan()
        self.assertTrue(result["preflight"]["explicit_user_authorization"])
        self.assertTrue(result["preflight"]["cap_le_500"])
        self.assertTrue(result["preflight"]["paid_calls_exactly_1"])
        self.assertTrue(result["preflight"]["usage_before_non_blocking"])
        paid = [s for s in result["steps"] if s.get("paid_generation")]
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["route_decision"]["route"], "DRYRUN_TECHNICAL_ALLOWED")
        self.assertIsNone(paid[0]["semantic_asset_key"])

    def test_usage_read_failure_is_not_a_preflight_block(self):
        result = planner.plan()
        reads = [s for s in result["steps"] if s.get("type") == "READ_USAGE"]
        self.assertEqual(len(reads), 2)
        self.assertTrue(all(not s.get("required", False) for s in reads))

    def test_allowance_rejects_long_text(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            req = json.loads(planner.REQUEST.read_text(encoding="utf-8"))
            dr1 = next(s for s in req["steps"] if s.get("type") == "TECHNICAL_TTS")
            dr1["text"] = "가" * 61
            regp, reqp, outp = td/"reg.json", td/"req.json", td/"out.json"
            regp.write_text(json.dumps({"assets":[]}), encoding="utf-8")
            reqp.write_text(json.dumps(req, ensure_ascii=False), encoding="utf-8")
            with patch.object(planner, "REGISTRY", regp), patch.object(planner, "REQUEST", reqp), patch.object(planner, "RECEIPT", outp):
                with self.assertRaisesRegex(RuntimeError, "exceeds allowance"):
                    planner.plan()

    def test_allowance_requires_explicit_user_authorization(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            req = json.loads(planner.REQUEST.read_text(encoding="utf-8"))
            req["explicit_user_authorization"] = False
            regp, reqp, outp = td/"reg.json", td/"req.json", td/"out.json"
            regp.write_text(json.dumps({"assets":[]}), encoding="utf-8")
            reqp.write_text(json.dumps(req, ensure_ascii=False), encoding="utf-8")
            with patch.object(planner, "REGISTRY", regp), patch.object(planner, "REQUEST", reqp), patch.object(planner, "RECEIPT", outp):
                with self.assertRaisesRegex(RuntimeError, "explicit user authorization"):
                    planner.plan()


if __name__ == "__main__":
    unittest.main()
