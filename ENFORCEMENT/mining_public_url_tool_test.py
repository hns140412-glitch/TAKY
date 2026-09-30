#!/usr/bin/env python3
"""No mocked search result counts as an original file without physically verified bytes."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from mining_public_url_tool import build_public_url_tool
from mining_operation_runner import run_with_providers

URL="https://official.example/assessment.pdf"
BYTES=b"%PDF-1.7\n%%EOF"


def acquired(url, *, destination_dir, max_bytes=100, override_hash=None,
             other_path=None):
    path=Path(other_path) if other_path else destination_dir/"sample.pdf"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(BYTES)
    return {
        "pass":True,"acquisition_state":"ACQUIRED_AND_PRESERVED",
        "preserved":True,"preserved_path":str(path),
        "sha256":override_hash or hashlib.sha256(BYTES).hexdigest(),
        "content_length":len(BYTES),"final_url":url,
        "content_type":"application/pdf","canonical_promotion":False,
    }


class ExplicitPublicAcquisitionTest(unittest.TestCase):
    def test_correct_original_bytes_produce_candidate_and_sha_receipt(self):
        calls=[]
        def getter(url,**opts):
            calls.append(url)
            return acquired(url,**opts)
        with tempfile.TemporaryDirectory() as td:
            fn=build_public_url_tool(Path(td),acquisition=getter)
            result=fn({"query":URL})
            self.assertEqual(calls,[URL])
            self.assertEqual(result["state"],"SUCCESS")
            self.assertEqual(result["source_acquisition"]["state"],"ACQUIRED_AND_PRESERVED")
            self.assertEqual(result["source_acquisition"]["size_bytes"],len(BYTES))
            self.assertEqual(result["source_acquisition"]["sha256"],hashlib.sha256(BYTES).hexdigest())
            self.assertTrue(Path(result["source_acquisition"]["preserved_path"]).is_file())
            row=result["response"]["results"][0]
            self.assertFalse(row["direct_support"])
            self.assertFalse(row["fresh_enough"])
            self.assertFalse(result["source_acquisition"]["canonical_promotion"])

    def test_search_phrase_cannot_invent_a_source_url(self):
        calls=[]
        def getter(url,**opts):
            calls.append(url)
            return acquired(url,**opts)
        with tempfile.TemporaryDirectory() as td:
            fn=build_public_url_tool(Path(td),acquisition=getter)
            self.assertEqual(fn({"query":"find a PDF about mathematics"})["error"],
                             "EXPLICIT_PUBLIC_URL_REQUIRED")
            self.assertFalse(calls)

    def test_reported_hash_mismatch_fails_without_source_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            fn=build_public_url_tool(Path(td),acquisition=lambda url,**kw:
                acquired(url,**kw,override_hash="0"*64))
            result=fn({"query":URL})
            self.assertEqual(result["state"],"FAILED")
            self.assertEqual(result["error"],"PRESERVED_SOURCE_INTEGRITY_MISMATCH")
            self.assertNotIn("response",result)

    def test_external_path_cannot_be_used_as_original_proof(self):
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root)/"target"; outside=Path(root)/"outside.pdf"
            fn=build_public_url_tool(dest,acquisition=lambda url,**kw:
                acquired(url,**kw,other_path=outside))
            result=fn({"query":URL})
            self.assertEqual(result["error"],"PRESERVED_SOURCE_INTEGRITY_MISMATCH")

    def test_access_restriction_does_not_switch_to_download_claim(self):
        def getter(url,**opts):
            return {"pass":True,"acquisition_state":"ACCESS_RESTRICTED","preserved":False}
        with tempfile.TemporaryDirectory() as td:
            result=build_public_url_tool(Path(td),acquisition=getter)({"query":URL})
            self.assertEqual(result["state"],"FAILED")
            self.assertEqual(result["error"],"ACCESS_HOLD")
            self.assertNotIn("response",result)

    def test_end_to_end_registered_tool_keeps_binary_proof_but_no_claim_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            fn=build_public_url_tool(Path(td),acquisition=acquired)
            output=run_with_providers({
                "task":{"goal":"acquire a known official original",
                        "task_family":"SOURCE_ACQUISITION",
                        "unknown":[URL],"route_signature":"search:web",
                        "max_research_depth":"D1"},
                "memory":{},
            },{"WEB":fn},max_rounds=3)
            self.assertEqual(output["invocations"],1)
            self.assertEqual(output["source_files_preserved"],1)
            self.assertEqual(output["events"][0]["source_acquisition"]["sha256"],
                             hashlib.sha256(BYTES).hexdigest())
            self.assertEqual(output["state"],"NEEDS_EVIDENCE_VERIFICATION")
            self.assertFalse(output["operational_research_ready"])
            self.assertFalse(output["real_user_outcome_countable"])
            self.assertNotEqual(output["checkpoint"]["frontier"][0]["status"],"CLOSED")
            self.assertEqual(len(output["checkpoint"]["evidence"]),1)


if __name__=="__main__":
    unittest.main()
