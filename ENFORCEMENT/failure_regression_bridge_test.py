#!/usr/bin/env python3
import tempfile, unittest
from pathlib import Path
from failure_regression_bridge import unresolved_repeated_failures,to_regression_candidate,summarize

class FailureBridgeTest(unittest.TestCase):
    def test_unresolved_only_and_candidate(self):
        rows=[
          {"kind":"REPEATED_FAILURE","failed_sig":"A","cause":"INPUT","action":"read:x"},
          {"kind":"RECOVERY_ROUTE","failed_sig":"A","new_sig":"B"},
          {"kind":"REPEATED_FAILURE","failed_sig":"C","cause":"RUNTIME","action":"run:y","error_fingerprint":"z"}
        ]
        u=unresolved_repeated_failures(rows)
        self.assertEqual([x["failed_sig"] for x in u],["C"])
        c=to_regression_candidate(u[0],{"route_changed":True,"user_debugger":False})
        self.assertTrue(c["pass"]); self.assertFalse(c["regression_case"]["auto_promote"])

    def test_summary_missing_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            s=summarize(Path(td)/"none.jsonl")
            self.assertEqual(s["events"],0); self.assertFalse(s["auto_promote"])

if __name__=="__main__":
    unittest.main()
