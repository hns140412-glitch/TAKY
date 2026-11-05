#!/usr/bin/env python3
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from resume_preparation_acceptance import run
class AcceptanceTests(unittest.TestCase):
 def test_raw_failure_skips_bundle(self):
  with patch("resume_preparation_acceptance.audit",return_value=["OMITTED_SOURCE_ITEM: D1"]),patch("resume_preparation_acceptance.subprocess.run") as bundle:
   result=run(*(Path("x") for _ in range(5)))
   self.assertFalse(result["pass"]);bundle.assert_not_called()
 def test_bundle_failure_blocks_pass(self):
  with patch("resume_preparation_acceptance.audit",return_value=[]),patch("resume_preparation_acceptance.subprocess.run") as bundle:
   bundle.return_value.returncode=1;bundle.return_value.stdout="bundle fail";bundle.return_value.stderr=""
   self.assertFalse(run(*(Path("x") for _ in range(5)))["pass"])
 def test_both_pass_declared_scope_only(self):
  with patch("resume_preparation_acceptance.audit",return_value=[]),patch("resume_preparation_acceptance.subprocess.run") as bundle:
   bundle.return_value.returncode=0
   result=run(*(Path("x") for _ in range(5)))
   self.assertTrue(result["pass"]);self.assertEqual(result["status"],"PASS_DECLARED_RECOVERED_SCOPE")
if __name__=="__main__":unittest.main()
