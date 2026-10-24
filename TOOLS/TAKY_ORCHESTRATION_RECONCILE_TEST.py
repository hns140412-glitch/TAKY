#!/usr/bin/env python3
"""Regression: truthful portfolio + execution reconciliation, no writes or models."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from TAKY_ORCHESTRATION_RECONCILE import reconcile, recovery_for

class OrchestrationReconcileTests(TestCase):
    def test_preparation_never_promoted_to_completion(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            tid="a"*32
            preparation=root/(tid+".json")
            preparation.write_text('{"id":"'+tid+'","state":"PREPARED_NOT_EXECUTED"}',encoding="utf-8")
            board={"tasks":[{"id":"INT-001","status":"IMPLEMENTING","category":"INTEGRATION"},
                            {"id":"OPS-001","status":"VERIFIED","category":"TOOLS"}]}
            assignments={"tasks":[{"work_id":"TAKY-CHAT-"+tid,"task_id":tid,
                "input_refs":[str(preparation)],"evidence_refs":[],
                "reviewer":"UNASSIGNED","status":"OPEN","execution_verified":False}]}
            before=sorted(str(x) for x in root.iterdir())
            result=reconcile(board,assignments,root)
            self.assertEqual(result["portfolio"]["total"],2)
            self.assertEqual(result["portfolio"]["declared_verified"],1)
            self.assertEqual(result["model_jobs"]["verified_by_registry"],0)
            self.assertEqual(result["observations"][0]["execution_state"],None)
            self.assertEqual(result["observations"][0]["next_action"],
                             "PREPARED_ONLY_CONFIRM_NECESSITY_BEFORE_CALL")
            self.assertEqual(before,sorted(str(x) for x in root.iterdir()))

    def test_existing_signed_output_reuse_no_retry(self):
        with TemporaryDirectory() as d:
            root=Path(d); tid="b"*32
            (root/("TAKY_ROUTED_"+tid+".json")).write_text(
                '{"task_id":"'+tid+'","state":"PROPOSAL_REJECTED",'
                '"proposal_error":"INVALID_REPLACEMENTS",'
                '"model_invocation_attempted":true}',encoding="utf-8")
            result=reconcile({"tasks":[]},{"tasks":[{"work_id":"TAKY-CHAT-"+tid,
                "task_id":tid,"input_refs":[],"evidence_refs":[],
                "status":"BLOCKED","execution_verified":False}]},root)
            row=result["observations"][0]
            self.assertEqual(row["derived_state"],"BLOCKED")
            self.assertIn("NO_RETRY",row["next_action"])
            self.assertTrue(row["model_invocation_attempted"])
            self.assertIsNone(row["model_called_reported"])
            self.assertEqual(row["signed_model_call_verification"],"NOT_CHECKED_BY_THIS_RECONCILER")

    def test_invalid_receipt_binding_is_rejected(self):
        with TemporaryDirectory() as d:
            root=Path(d);tid="c"*32
            (root/("TAKY_ROUTED_"+tid+".json")).write_text('{"task_id":"wrong","state":"COMPLETE_UNVERIFIED"}')
            with self.assertRaisesRegex(ValueError,"EXECUTION_TASK_ID_MISMATCH"):
                reconcile({"tasks":[]},{"tasks":[{"work_id":"TAKY-CHAT-"+tid,
                    "task_id":tid,"status":"REVIEW"}]},root)

    def test_registry_drift_is_visible_not_silently_rewritten(self):
        with TemporaryDirectory() as d:
            root=Path(d);tid="d"*32
            (root/("TAKY_ROUTED_"+tid+".json")).write_text(
                '{"task_id":"'+tid+'","state":"FAILED"}')
            result=reconcile({"tasks":[]},{"tasks":[{"work_id":"TAKY-CHAT-"+tid,
                    "task_id":tid,"status":"OPEN"}]},root)
            self.assertEqual(result["model_jobs"]["registry_receipt_mismatches"],1)
            self.assertEqual(result["observations"][0]["next_action"],
                             "VERIFY_SIGNED_OUTCOME_BEFORE_ANY_NEW_CALL")

    def test_explicit_portfolio_binding_is_evidence_not_completion(self):
        tid="f"*32
        entry={"work_id":"TAKY-CHAT-"+tid,"task_id":tid,"status":"OPEN",
               "portfolio_task_id":"INT-001","execution_verified":False}
        with TemporaryDirectory() as d:
            result=reconcile({"tasks":[{"id":"INT-001","status":"IMPLEMENTING",
                "category":"INTEGRATION"}]},{"tasks":[entry]},Path(d))
            self.assertEqual(result["model_jobs"]["linked_to_portfolio"],1)
            self.assertEqual(result["model_jobs"]["verified_by_registry"],0)
            entry["portfolio_task_id"]="UNKNOWN"
            with self.assertRaisesRegex(ValueError,"PORTFOLIO_TASK_BINDING_LOST"):
                reconcile({"tasks":[{"id":"INT-001"}]},{"tasks":[entry]},Path(d))

    def test_claude_codex_same_portfolio_handoff_not_false_verification(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            impl_id="a"*32
            review_id="b"*32
            jobs=[]
            for task_id,kind,executor,state,qa in (
                (impl_id,"implementation","Claude","APPLIED_UNVERIFIED",None),
                (review_id,"review","Codex","COMPLETE_UNVERIFIED","NO_CHECKABLE_CITATIONS_REVIEW_HOLD"),
            ):
                path=root/(task_id+".json")
                path.write_text(__import__("json").dumps({
                    "id":task_id,"state":"PREPARED_NOT_EXECUTED","task_kind":kind,
                    "portfolio_task_id":"MCP-002"}))
                (root/("TAKY_ROUTED_"+task_id+".json")).write_text(__import__("json").dumps({
                    "task_id":task_id,"state":state,"content_qa_state":qa}))
                jobs.append({"work_id":"TAKY-CHAT-"+task_id,"task_id":task_id,
                    "executor":executor,"portfolio_task_id":"MCP-002",
                    "input_refs":[str(path)],"status":"REVIEW",
                    "reviewer":"UNASSIGNED","execution_verified":False})
            result=reconcile({"tasks":[{"id":"MCP-002","status":"IMPLEMENTING",
                "category":"MCP"}]},{"tasks":jobs},root)
            self.assertEqual(len(result["handoffs"]),1)
            handoff=result["handoffs"][0]
            self.assertEqual(handoff["implementation_work_ids"],["TAKY-CHAT-"+impl_id])
            self.assertEqual(handoff["review_work_ids"],["TAKY-CHAT-"+review_id])
            self.assertTrue(handoff["independent_review_attempted"])
            self.assertFalse(handoff["verified_completion"])
            self.assertEqual(handoff["independent_review_qa_states"],
                             ["NO_CHECKABLE_CITATIONS_REVIEW_HOLD"])
            self.assertEqual(result["model_jobs"]["verified_by_registry"],0)

    def test_exact_post_edit_sha_handoff_and_mismatched_review_hold(self):
        import json
        with TemporaryDirectory() as d:
            root=Path(d)
            implemented,reviewer="1"*32,"2"*32
            rows=[]
            for tid,who,kind,state in [
                (implemented,"Claude","implementation","APPLIED_UNVERIFIED"),
                (reviewer,"Codex","review","COMPLETE_UNVERIFIED"),
            ]:
                task=root/(tid+".json")
                task.write_text(json.dumps({"id":tid,"portfolio_task_id":"MCP-002",
                    "task_kind":kind,"state":"PREPARED_NOT_EXECUTED"}),encoding="utf8")
                receipt={"task_id":tid,"state":state}
                if kind=="implementation":
                    receipt["changed_files"]=[{"path":"TOOLS/TAKY_ORCHESTRATION_ADVANCE.py",
                                               "after_sha256":"a"*64}]
                else:
                    receipt["review_source_binding"]={"source_manifest":[{
                        "path":"TOOLS/TAKY_ORCHESTRATION_ADVANCE.py","sha256":"a"*64,
                        "includedLines":286,"totalLines":298}]}
                    receipt["content_qa_state"]="NO_CHECKABLE_CITATIONS_REVIEW_HOLD"
                (root/("TAKY_ROUTED_"+tid+".json")).write_text(json.dumps(receipt),encoding="utf8")
                rows.append({"work_id":"TAKY-CHAT-"+tid,"task_id":tid,
                    "executor":who,"portfolio_task_id":"MCP-002",
                    "input_refs":[str(task)],"status":"REVIEW","execution_verified":False})
            board={"tasks":[{"id":"MCP-002","status":"IMPLEMENTING"}]}
            first=reconcile(board,{"tasks":rows},root)
            handoff=first["handoffs"][0]
            self.assertEqual(first["model_jobs"]["exact_source_sha_bound_independent_handoffs"],1)
            self.assertTrue(handoff["source_sha_independent_review_bound"])
            self.assertEqual(handoff["source_binding_state"],
                             "EXACT_POST_EDIT_SHA_HANDOFF_NOT_CONTENT_APPROVED")
            self.assertFalse(handoff["verified_completion"])
            self.assertEqual(handoff["exact_post_edit_source_review_pairs"][0][
                "review_completeness"],"PARTIAL_INPUT_LINES")
            bad=root/("TAKY_ROUTED_"+reviewer+".json")
            doc=json.loads(bad.read_text("utf8"))
            doc["review_source_binding"]["source_manifest"][0]["sha256"]="b"*64
            bad.write_text(json.dumps(doc),encoding="utf8")
            changed=reconcile(board,{"tasks":rows},root)["handoffs"][0]
            self.assertFalse(changed["source_sha_independent_review_bound"])
            self.assertEqual(changed["exact_post_edit_source_review_pairs"],[])
            self.assertEqual(changed["source_binding_state"],"NOT_SOURCE_BOUND_HOLD")

    def test_signed_cli_receipt_joins_without_false_completion(self):
        with TemporaryDirectory() as d:
            tid = "9" * 32
            row = {"work_id": "TAKY-CHAT-" + tid, "task_id": tid,
                   "status": "OPEN", "reviewer": "UNASSIGNED",
                   "execution_verified": False, "portfolio_task_id": "INT-001"}
            calls = []
            def signed_reader(task_id):
                calls.append(task_id)
                return {"state": "CLI_RETURNED_UNVERIFIED",
                        "modelSuccessVerified": False}
            observed = reconcile(
                {"tasks": [{"id": "INT-001", "status": "IMPLEMENTING"}]},
                {"tasks": [row]}, Path(d), signed_readback=signed_reader)
            self.assertEqual(calls, [tid])
            self.assertEqual(observed["observations"][0][
                "signed_model_call_verification"], "CLI_RETURNED_UNVERIFIED")
            self.assertEqual(observed["model_jobs"][
                "signed_cli_returned_not_content_verified"], 1)
            self.assertEqual(observed["model_jobs"]["verified_by_registry"], 0)
            self.assertEqual(observed["model_calls_made_by_reconciliation"], 0)
            self.assertEqual(observed["files_modified_by_reconciliation"], 0)
            row["execution_verified"] = True
            claimed = reconcile(
                {"tasks": [{"id": "INT-001", "status": "IMPLEMENTING"}]},
                {"tasks": [row]}, Path(d), signed_readback=signed_reader)
            self.assertEqual(claimed["model_jobs"]["verified_by_registry"], 1)
            self.assertEqual(claimed["model_jobs"][
                "independently_proven_completion_by_this_reconciler"], 0)
            self.assertEqual(claimed["model_jobs"][
                "unproven_verified_registry_claims"], 1)
            row["execution_verified"] = False
            attested = reconcile(
                {"tasks": [{"id": "INT-001", "status": "IMPLEMENTING"}]},
                {"tasks": [row]}, Path(d),
                signed_readback=lambda _: {
                    "state": "CLI_RETURNED_UNVERIFIED",
                    "executionEvidenceVerified": True,
                    "executionVerificationState":
                        "SIGNED_EXECUTION_EVIDENCED_NOT_USER_DONE"})
            self.assertEqual(attested["model_jobs"]["signed_execution_evidenced"], 1)
            self.assertEqual(attested["model_jobs"][
                "independently_proven_completion_by_this_reconciler"], 0)
            self.assertFalse(attested["handoffs"][0]["verified_completion"])
            observed = reconcile(
                {"tasks": [{"id": "INT-001", "status": "IMPLEMENTING"}]},
                {"tasks": [row]}, Path(d),
                signed_readback=lambda _: {"state": "SIGNED_PREFLIGHT_NOT_FOUND"})
            self.assertEqual(observed["model_jobs"][
                "unbound_or_unverified_signed_calls"], 1)


    def test_pending_scoped_claim_observes_bytes_without_changing_state(self):
        from TAKY_ORCHESTRATION_RECONCILE import inspect_scoped_edit_claims
        import hashlib
        import copy
        with TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "module.py"
            original = b"value = 1\\n"
            altered = b"value = 2\\n"
            src.write_bytes(original)
            rid = "pf:external-review-" + "a" * 32 + ":1234567890abcdef"
            runtime = {
                "preflight_receipts": {rid: {"execution_key": "operation"}},
                "active_attempts": {"operation": {"attempt": {"target": str(root)}}},
                "scoped_edit_claims": {rid: {
                    "receipt_id": rid, "status": "CLAIMED_PENDING_FILE_APPLY",
                    "files": [{"path": "module.py",
                               "before_sha256": hashlib.sha256(original).hexdigest(),
                               "after_sha256": hashlib.sha256(altered).hexdigest()}],
                }},
            }
            initial = copy.deepcopy(runtime)
            result = inspect_scoped_edit_claims(runtime)
            self.assertEqual(result["items"][0]["state"],
                             "PENDING_PREIMAGE_OBSERVED_REVIEW_REQUIRED")
            self.assertEqual(result["files_written"], 0)
            self.assertFalse(result["items"][0]["automatic_recovery_permitted"])
            self.assertEqual(initial, runtime)
            src.write_bytes(altered)
            result = inspect_scoped_edit_claims(runtime)
            self.assertEqual(result["items"][0]["state"],
                             "PENDING_POSTIMAGE_OBSERVED_REVIEW_REQUIRED")
            self.assertEqual(runtime, initial)
            runtime["scoped_edit_claims"][rid]["status"] = "APPLIED_UNVERIFIED"
            result = inspect_scoped_edit_claims(runtime)
            self.assertEqual(result["items"][0]["state"],
                             "RECORDED_APPLIED_UNVERIFIED")
            src.write_bytes(b"value = 99\\n")
            result = inspect_scoped_edit_claims(runtime)
            self.assertEqual(result["items"][0]["state"],
                             "PARTIAL_OR_DIVERGENT_HOLD")

    def test_pending_claim_missing_files_and_unavailable_target_are_holds(self):
        from TAKY_ORCHESTRATION_RECONCILE import inspect_scoped_edit_claims
        with TemporaryDirectory() as temp:
            rid = "pf:external-review-" + "b" * 32 + ":1234567890abcdef"
            record = {"receipt_id": rid, "status": "CLAIMED_PENDING_FILE_APPLY",
                      "files": [{"path": "missing.py",
                                 "before_sha256": "a" * 64,
                                 "after_sha256": "b" * 64}]}
            ledger = {"scoped_edit_claims": {rid: record},
                      "preflight_receipts": {rid: {"execution_key": "k"}},
                      "active_attempts": {"k": {"attempt": {"target": str(temp)}}}}
            observed = inspect_scoped_edit_claims(ledger)
            self.assertEqual(observed["items"][0]["state"],
                             "PARTIAL_OR_DIVERGENT_HOLD")
            del ledger["active_attempts"]["k"]
            self.assertEqual(inspect_scoped_edit_claims(ledger)["items"][0]["state"],
                             "SIGNED_TARGET_ROOT_UNAVAILABLE_HOLD")
            ledger["active_attempts"]["k"] = {"attempt": {"target": str(temp)}}
            record["files"][0]["path"] = "../outside.py"
            self.assertEqual(inspect_scoped_edit_claims(ledger)["items"][0]["state"],
                             "PARTIAL_OR_DIVERGENT_HOLD")

    def test_duplicate_work_rejected(self):
        entry={"work_id":"TAKY-CHAT-"+("e"*32),"task_id":"e"*32}
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"DUPLICATE_REGISTERED_WORK"):
                reconcile({"tasks":[]},{"tasks":[entry,entry]},Path(d))

if __name__=="__main__":
    main()
