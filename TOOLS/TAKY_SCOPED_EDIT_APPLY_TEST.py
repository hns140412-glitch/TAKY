#!/usr/bin/env python3
"""No-model regression checks for bounded TAKY code-edit application."""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from TAKY_SCOPED_EDIT_APPLY import EditRejected, run, sha, extract_proposal

class ScopedEditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="TAKY_EDIT_TEST_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "a.py"
        self.src.write_text("ANSWER = 1\n", encoding="utf-8")
        self.untouched = self.root / "unrelated.py"
        self.untouched.write_text("KEEP = True\n", encoding="utf-8")
        self.task = {"schema": "TAKY_EXECUTION_REQUEST_V1", "mode": "BOUNDED_EDIT_PROPOSAL",
                     "id": "a" * 32, "repo": str(self.root),
                     "no_push": True, "no_deploy": True,
                     "allowed_files": [{"path": "a.py", "sha256": sha(self.src.read_bytes())}]}
        self.proposal = {"task_id": self.task["id"],
                         "edits": [{"path": "a.py", "replacements": [
                             {"old": "ANSWER = 1", "new": "ANSWER = 2"}]}]}



    def test_end_to_end_real_signed_taky2_state_and_once_only_file_apply(self):
        """No model calls: mocked provider return, REAL HMAC/anchor and file IO."""
        from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
        ensure_trusted_taky2()
        from TAKY2.enforcement import stable_hash
        from TAKY2 import state_store as store

        store_dir = self.root / "sealed_store"
        store_dir.mkdir()
        authority_path = store_dir / "authority.json"
        example_path = store_dir / "example.json"
        runtime_path = store_dir / "runtime.json"
        anchor_path = store_dir / "anchor.json"
        lock_path = store_dir / "runtime.lock"
        key = b"T" * 32
        authority_path.write_text('{"key":{"test_owner":"once_only"}}', encoding="utf-8")
        example_path.write_text('{"runtime":{},"context":{},"route_ledgers":{}}',
                                encoding="utf-8")
        store.initialize_runtime(
            authority_path=authority_path, example_path=example_path,
            runtime_path=runtime_path, runtime_key=key, anchor_path=anchor_path)
        _, current, auth = store.load_bundle(
            authority_path=authority_path, runtime_path=runtime_path,
            runtime_key=key, anchor_path=anchor_path)
        task_file = store_dir / "task.json"
        task_file.write_text(json.dumps(self.task), encoding="utf-8")
        digest = sha(task_file.read_bytes())
        tid = self.task["id"]
        rid = f"pf:external-review-{tid}:abababababababab"
        original = self.src.read_bytes()
        manifest = {"model": "codex", "execution_mode": "CODEX_VERIFY_ONLY",
                    "expected_calls": 1,
                    "source_manifest": [{
                        "path": "a.py", "sha256": sha(original),
                        "includedLines": 1, "totalLines": 1, "complete": True}],
                    "packet_digest": "a" * 20,
                    "scoped_edit_contract": {
                        "schema": "TAKY_SCOPED_EDIT_CALL_V1",
                        "task_id": tid, "task_sha256": digest, "repo": str(self.root)}}
        provider_result = {"returncode": 0, "stdout": json.dumps(self.proposal),
                           "stderr": ""}
        current["preflight_receipts"] = {rid: {
            "allowed": True, "call_allowed": True,
            "authority_digest": auth, "action_id": "verify:codex-packet",
            "call_digest": stable_hash(manifest), "execution_key": "exec"}}
        current["execution_calls"] = {rid: {
            "provider": "openai", "model": "codex",
            "executor_id": "TAKY_MODEL_REVIEW_CODEX", "status": "RETURNED",
            "actual_calls": 1, "result": provider_result,
            "result_digest": stable_hash(provider_result)}}
        current["active_attempts"] = {
            "exec": {"attempt": {"target": str(self.root)}}}
        store.save_runtime(
            current, expected_version=current["runtime_version"],
            authority_digest_value=auth, runtime_path=runtime_path,
            lock_path=lock_path, runtime_key=key, anchor_path=anchor_path)

        real_load = store.load_bundle
        real_save = store.save_runtime
        def isolated_load():
            return real_load(
                authority_path=authority_path, runtime_path=runtime_path,
                runtime_key=key, anchor_path=anchor_path)
        def isolated_save(candidate, *, expected_version, authority_digest_value):
            return real_save(
                candidate, expected_version=expected_version,
                authority_digest_value=authority_digest_value,
                runtime_path=runtime_path, lock_path=lock_path,
                runtime_key=key, anchor_path=anchor_path)
        evidence = {"task_id": tid, "taky2_signed_receipt_id": rid,
                    "governed_call_manifest": manifest}
        with (patch("TAKY2.state_store.load_bundle", side_effect=isolated_load),
              patch("TAKY2.state_store.save_runtime", side_effect=isolated_save),
              patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"})):
            first = run(self.task, self.proposal, execute=True,
                        signed_receipt_id=rid, execution_evidence=evidence,
                        task_file_sha256=digest)
            self.assertEqual(first["status"], "APPLIED_UNVERIFIED")
            self.assertEqual(self.src.read_text(encoding="utf-8"), "ANSWER = 2\n")
            _, authenticated, _ = isolated_load()
            self.assertEqual(authenticated["scoped_edit_claims"][rid]["status"],
                             "APPLIED_UNVERIFIED")
            # Replay after restoring the original file is still denied.
            self.src.write_bytes(original)
            with self.assertRaisesRegex(EditRejected, "RECEIPT_ALREADY_CLAIMED"):
                run(self.task, self.proposal, execute=True,
                    signed_receipt_id=rid, execution_evidence=evidence,
                    task_file_sha256=digest)
            self.assertEqual(self.src.read_bytes(), original)
        # File-level mutation of the authentic claim breaks the MAC/anchor.
        forged = json.loads(runtime_path.read_text(encoding="utf-8"))
        forged["scoped_edit_claims"].pop(rid)
        runtime_path.write_text(json.dumps(forged), encoding="utf-8")
        with self.assertRaises(store.StateIntegrityError):
            isolated_load()

    def test_environment_flags_cannot_approve_unsigned_model_proposal(self):
        with patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            with self.assertRaisesRegex(EditRejected, "EXECUTION_RECORD_NOT_BOUND"):
                run(self.task, self.proposal, execute=True)
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")

    def test_model_proposal_matches_real_signed_input_and_output_manifest(self):
        from TAKY_SCOPED_EDIT_APPLY import signed_model_proposal_bound
        from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
        ensure_trusted_taky2()
        from TAKY2.enforcement import stable_hash
        tid = self.task["id"]
        rid = f"pf:external-review-{tid}:0123456789abcdef"
        source = {"path": "a.py", "sha256": sha(self.src.read_bytes()),
                  "includedLines": 1, "totalLines": 1, "complete": True}
        task_digest = sha(json.dumps(self.task, sort_keys=True).encode("utf-8"))
        manifest = {"model": "codex", "execution_mode": "CODEX_VERIFY_ONLY",
                    "expected_calls": 1, "source_manifest": [source],
                    "packet_digest": "a" * 20,
                    "scoped_edit_contract": {
                        "schema": "TAKY_SCOPED_EDIT_CALL_V1",
                        "task_id": tid, "task_sha256": task_digest,
                        "repo": str(self.root)}}
        output = {"returncode": 0, "stdout": json.dumps(self.proposal),
                  "stderr": ""}
        runtime = {
            "authority_digest": "authority",
            "preflight_receipts": {rid: {
                "allowed": True, "call_allowed": True,
                "authority_digest": "authority", "action_id": "verify:codex-packet",
                "call_digest": stable_hash(manifest), "execution_key": "active"}},
            "execution_calls": {rid: {
                "provider": "openai", "model": "codex",
                "executor_id": "TAKY_MODEL_REVIEW_CODEX", "status": "RETURNED",
                "actual_calls": 1, "result": output,
                "result_digest": stable_hash(output)}},
            "active_attempts": {"active": {"attempt": {"target": str(self.root)}}},
        }
        evidence = {"task_id": tid, "taky2_signed_receipt_id": rid,
                    "governed_call_manifest": manifest}
        signed_model_proposal_bound(self.task, self.proposal, rid,
                                    execution_evidence=evidence,
                                    task_file_sha256=task_digest,
                                    trusted_runtime=runtime)
        with self.assertRaisesRegex(EditRejected, "ORIGINAL_TASK_CONTRACT_NOT_SIGNED"):
            signed_model_proposal_bound(
                self.task, self.proposal, rid, execution_evidence=evidence,
                task_file_sha256="f" * 64, trusted_runtime=runtime)
        no_edit_intent = dict(manifest)
        del no_edit_intent["scoped_edit_contract"]
        no_edit_evidence = {**evidence, "governed_call_manifest": no_edit_intent}
        runtime["preflight_receipts"][rid]["call_digest"] = stable_hash(no_edit_intent)
        with self.assertRaisesRegex(EditRejected, "ORIGINAL_TASK_CONTRACT_NOT_SIGNED"):
            signed_model_proposal_bound(
                self.task, self.proposal, rid, execution_evidence=no_edit_evidence,
                task_file_sha256=task_digest, trusted_runtime=runtime)
        runtime["preflight_receipts"][rid]["call_digest"] = stable_hash(manifest)
        # Exercise the actual apply + single-use signed-ledger transition in a
        # temporary repository. The fixture implements the real CAS contract,
        # never writing to the user's production TAKY2 runtime.
        runtime["runtime_version"] = 11
        stored = {"runtime": json.loads(json.dumps(runtime))}
        def load_fixture():
            return {}, json.loads(json.dumps(stored["runtime"])), "authority"
        def save_fixture(candidate, *, expected_version, authority_digest_value):
            if (expected_version != stored["runtime"]["runtime_version"]
                    or authority_digest_value != "authority"):
                raise RuntimeError("CAS_CONFLICT")
            saved = json.loads(json.dumps(candidate))
            saved["runtime_version"] = expected_version + 1
            stored["runtime"] = saved
            return json.loads(json.dumps(saved))
        with (patch("TAKY2.state_store.load_bundle", side_effect=load_fixture),
              patch("TAKY2.state_store.save_runtime", side_effect=save_fixture),
              patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"})):
            # A failed state reservation must leave the file untouched.
            with patch('TAKY2.state_store.save_runtime', side_effect=RuntimeError('collision')):
                with self.assertRaises(EditRejected):
                    run(self.task, self.proposal, execute=True,
                        signed_receipt_id=rid, execution_evidence=evidence,
                        task_file_sha256=task_digest)
            self.assertEqual(self.src.read_text(), 'ANSWER = 1\n')
            # Reserve a signed receipt through the versioned store.
            applied = run(self.task, self.proposal, execute=True,
                          signed_receipt_id=rid, execution_evidence=evidence,
                          task_file_sha256=task_digest)
            self.assertEqual(stored["runtime"]["scoped_edit_claims"][rid]["status"],
                             "APPLIED_UNVERIFIED")
            # The source was reset only to test replay of the *same* evidence.
            self.src.write_text("ANSWER = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(EditRejected, "RECEIPT_ALREADY_CLAIMED"):
                run(self.task, self.proposal, execute=True,
                    signed_receipt_id=rid, execution_evidence=evidence,
                    task_file_sha256=task_digest)
            self.assertEqual(self.src.read_text(), "ANSWER = 1\n")
            # An interrupted file apply spends its own second receipt, but
            # cannot be reported as complete and cannot be retried blindly.
            rid2 = f"pf:external-review-{tid}:fedcba9876543210"
            stored["runtime"]["preflight_receipts"][rid2] = (
                json.loads(json.dumps(stored["runtime"]["preflight_receipts"][rid])))
            stored["runtime"]["execution_calls"][rid2] = (
                json.loads(json.dumps(stored["runtime"]["execution_calls"][rid])))
            evidence2 = {**evidence, "taky2_signed_receipt_id": rid2}
            with patch("TAKY_SCOPED_EDIT_APPLY.apply",
                       side_effect=OSError("TEST_DISK_FAILURE")):
                with self.assertRaisesRegex(OSError, "TEST_DISK_FAILURE"):
                    run(self.task, self.proposal, execute=True,
                        signed_receipt_id=rid2, execution_evidence=evidence2,
                        task_file_sha256=task_digest)
            self.assertEqual(stored["runtime"]["scoped_edit_claims"][rid2]["status"],
                             "CLAIMED_PENDING_FILE_APPLY")
            with self.assertRaisesRegex(EditRejected, "RECEIPT_ALREADY_CLAIMED"):
                run(self.task, self.proposal, execute=True,
                    signed_receipt_id=rid2, execution_evidence=evidence2,
                    task_file_sha256=task_digest)
            self.assertEqual(self.src.read_text(), "ANSWER = 1\n")
        self.assertEqual(applied["status"], "APPLIED_UNVERIFIED")
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")
        # Restore the original preimage to exercise precise tamper checks.
        self.src.write_text("ANSWER = 1\n", encoding="utf-8")
        altered = json.loads(json.dumps(self.proposal))
        altered["edits"][0]["replacements"][0]["new"] = "ANSWER = 999"
        with self.assertRaisesRegex(EditRejected, "PROPOSAL_NOT_SIGNED_MODEL_OUTPUT"):
            signed_model_proposal_bound(self.task, altered, rid,
                                        execution_evidence=evidence,
                                        task_file_sha256=task_digest,
                                        trusted_runtime=runtime)
        runtime["execution_calls"][rid]["result"]["stdout"] = json.dumps(altered)
        with self.assertRaisesRegex(EditRejected, "SIGNED_MODEL_RETURN_INVALID"):
            signed_model_proposal_bound(self.task, altered, rid,
                                        execution_evidence=evidence,
                                        task_file_sha256=task_digest,
                                        trusted_runtime=runtime)
        runtime["execution_calls"][rid]["result"]["stdout"] = json.dumps(self.proposal)
        manifest["source_manifest"][0]["sha256"] = "f" * 64
        with self.assertRaisesRegex(EditRejected, "SIGNED_INPUT_MANIFEST_MISMATCH"):
            signed_model_proposal_bound(self.task, self.proposal, rid,
                                        execution_evidence=evidence,
                                        task_file_sha256=task_digest,
                                        trusted_runtime=runtime)

    def test_extract_plain_model_json(self):
        result = extract_proposal(self.task, json.dumps(self.proposal))
        self.assertEqual(result["task_id"], self.task["id"])

    def test_extract_claude_envelope(self):
        envelope = {"type": "result", "is_error": False, "result": json.dumps(self.proposal)}
        self.assertEqual(extract_proposal(self.task, json.dumps(envelope)), self.proposal)

    def test_extract_rejects_unstructured_output(self):
        with self.assertRaisesRegex(EditRejected, "STRICT_JSON"):
            extract_proposal(self.task, "looks fine - please change ANSWER")

    def test_preview_makes_no_changes(self):
        result = run(self.task, self.proposal)
        self.assertEqual(result["status"], "DRY_RUN_VALID")
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")

    def test_authorized_application(self):
        with patch("TAKY_SCOPED_EDIT_APPLY.claim_scoped_edit_once", return_value={}), patch("TAKY_SCOPED_EDIT_APPLY.finalize_scoped_edit_claim"), patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            result = run(self.task, self.proposal, execute=True, execution_evidence={"fixture": True})
        self.assertEqual(result["status"], "APPLIED_UNVERIFIED")
        self.assertEqual(self.src.read_text(), "ANSWER = 2\n")
        self.assertEqual(self.untouched.read_text(), "KEEP = True\n")

    def test_unapproved_application_refused(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(EditRejected, "AUTHORIZATION_REQUIRED"):
                run(self.task, self.proposal, execute=True)
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")

    def test_changed_preimage_refused(self):
        self.src.write_text("ANSWER = 5\n", encoding="utf-8")
        with self.assertRaisesRegex(EditRejected, "SOURCE_CHANGED"):
            run(self.task, self.proposal)
        self.assertEqual(self.src.read_text(), "ANSWER = 5\n")

    def test_path_escape_and_unlisted_file_refused(self):
        self.proposal["edits"][0]["path"] = "../unrelated.py"
        with self.assertRaisesRegex(EditRejected, "UNAPPROVED"):
            run(self.task, self.proposal)
        self.proposal["edits"][0]["path"] = "unrelated.py"
        with self.assertRaisesRegex(EditRejected, "UNAPPROVED"):
            run(self.task, self.proposal)

    def test_duplicate_replacement_refused(self):
        self.src.write_text("ANSWER = 1\nANSWER = 1\n", encoding="utf-8")
        self.task["allowed_files"][0]["sha256"] = sha(self.src.read_bytes())
        with self.assertRaisesRegex(EditRejected, "NON_UNIQUE"):
            run(self.task, self.proposal)

    def test_sixteen_verified_replacements_are_not_blocked_by_count(self):
        self.src.write_text("".join(f"VALUE_{i:02d} = {i}\n" for i in range(16)), encoding="utf-8")
        self.task["allowed_files"][0]["sha256"] = sha(self.src.read_bytes())
        self.proposal["edits"][0]["replacements"] = [
            {"old": f"VALUE_{i:02d} = {i}", "new": f"VALUE_{i:02d} = {i + 100}"}
            for i in range(16)
        ]
        with patch("TAKY_SCOPED_EDIT_APPLY.claim_scoped_edit_once", return_value={}), patch("TAKY_SCOPED_EDIT_APPLY.finalize_scoped_edit_claim"), patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            result = run(self.task, self.proposal, execute=True, execution_evidence={"fixture": True})
        self.assertEqual(result["status"], "APPLIED_UNVERIFIED")
        self.assertIn("VALUE_15 = 115", self.src.read_text(encoding="utf-8"))
        self.assertEqual(self.untouched.read_text(), "KEEP = True\n")

    def test_sixteen_changes_rejects_last_invalid_without_partial_apply(self):
        self.src.write_text("".join(f"VALUE_{i:02d} = {i}\n" for i in range(16)), encoding="utf-8")
        original = self.src.read_bytes()
        self.task["allowed_files"][0]["sha256"] = sha(original)
        self.proposal["edits"][0]["replacements"] = [
            {"old": f"VALUE_{i:02d} = {i}", "new": f"VALUE_{i:02d} = {i + 100}"}
            for i in range(15)
        ] + [{"old": "NON_EXISTENT", "new": "MALICIOUS"}]
        with patch("TAKY_SCOPED_EDIT_APPLY.claim_scoped_edit_once", return_value={}), patch("TAKY_SCOPED_EDIT_APPLY.finalize_scoped_edit_claim"), patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            with self.assertRaisesRegex(EditRejected, "NON_UNIQUE"):
                run(self.task, self.proposal, execute=True)
        self.assertEqual(self.src.read_bytes(), original)
        self.assertEqual(self.untouched.read_text(), "KEEP = True\n")

    def test_three_explicitly_authorized_files_do_not_hit_arbitrary_count(self):
        for name in ("b.py", "c.py"):
            file = self.root / name
            file.write_text("ANSWER = 1\n", encoding="utf-8")
            self.task["allowed_files"].append({"path": name, "sha256": sha(file.read_bytes())})
            self.proposal["edits"].append({"path": name, "replacements": [
                {"old": "ANSWER = 1", "new": "ANSWER = 2"}]})
        with patch("TAKY_SCOPED_EDIT_APPLY.claim_scoped_edit_once", return_value={}), patch("TAKY_SCOPED_EDIT_APPLY.finalize_scoped_edit_claim"), patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            result = run(self.task, self.proposal, execute=True, execution_evidence={"fixture": True})
        self.assertEqual(len(result["files"]), 3)
        self.assertEqual((self.root / "c.py").read_text(), "ANSWER = 2\n")
        self.assertEqual(self.untouched.read_text(), "KEEP = True\n")

    def test_invalid_python_refused(self):
        self.proposal["edits"][0]["replacements"][0]["new"] = "def broken(:"
        with self.assertRaises(SyntaxError):
            run(self.task, self.proposal)
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")

    def test_atomic_validation_two_files(self):
        second = self.root / "b.py"
        second.write_text("OK = 1\n", encoding="utf-8")
        self.task["allowed_files"].append({"path": "b.py", "sha256": sha(second.read_bytes())})
        self.proposal["edits"].append({"path": "b.py", "replacements": [
            {"old": "MISSING", "new": "WRONG"}]})
        with patch("TAKY_SCOPED_EDIT_APPLY.claim_scoped_edit_once", return_value={}), patch("TAKY_SCOPED_EDIT_APPLY.finalize_scoped_edit_claim"), patch.dict(os.environ, {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1",
                                     "TAKY_ALLOW_SCOPED_FILE_EDIT": "1"}):
            with self.assertRaises(EditRejected):
                run(self.task, self.proposal, execute=True)
        self.assertEqual(self.src.read_text(), "ANSWER = 1\n")
        self.assertEqual(second.read_text(), "OK = 1\n")

if __name__ == "__main__":
    unittest.main()
