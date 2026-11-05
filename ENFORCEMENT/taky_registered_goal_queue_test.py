"""Bounded canonical V2 dependencies: real register & synthetic isolation tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from uuid import uuid4
import unittest

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/".local"
sys.path.insert(0,str(ROOT/"TOOLS"))
import TAKY_ORCHESTRATION_ADVANCE as canonical
from runtime_orchestrator import run_bounded_goal_queue


class CanonicalDependentQueueTests(unittest.TestCase):
    def setUp(self):
        LOCAL.mkdir(exist_ok=True)
        self.manifest=LOCAL/("test-registered-goal-"+uuid4().hex+".json")
        self.receipts=[]
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for file in [self.manifest,*self.receipts]:
            file.unlink(missing_ok=True)

    def run_manifest(self, items, *, validate_only=False):
        content={"schema":"TAKY_GOAL_QUEUE_V2",
                 "queue_id":"registered-"+uuid4().hex,
                 "items":items}
        self.manifest.write_text(json.dumps(content),encoding="utf-8")
        out=run_bounded_goal_queue(self.manifest,ROOT,validate_only=validate_only)
        if out.get("local_queue_receipt"):
            self.receipts.append(ROOT/out["local_queue_receipt"])
        return out

    def test_reason_prepared_v2_routes_via_existing_queue_without_models(self):
        from reason_queue_ingress import route_message
        token=uuid4().hex
        qid="reason-v2-"+token[:15]
        message_id="T"+token.upper()
        prepared=LOCAL/("taky-intake-"+qid+".json")
        prepared.write_text(json.dumps({
            "schema":"TAKY_GOAL_QUEUE_V2","queue_id":qid,
            "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}],
        }),encoding="utf-8")
        self.receipts.append(prepared)
        frame=(f'<reason-message from="taky-local/terminal" agent="cli" '
               f'id="{message_id}">\nTAKY_GOAL_SIGNAL_V1 queue={qid}\n'
               '</reason-message>\n')
        first=route_message(ROOT,frame,execute=True,
                            identity_check=lambda:True)
        self.assertEqual(first["status"],"REASON_PREPARED_QUEUE_DISPATCHED")
        self.assertEqual(first["queue"]["schema"],"TAKY_GOAL_QUEUE_OBSERVATION_V2")
        self.assertEqual(first["queue"]["model_calls"],0)
        self.assertEqual(first["queue"]["goals_verified_done"],0)
        again=route_message(ROOT,frame,execute=True,
                            identity_check=lambda:True,
                            queue_executor=lambda *_:self.fail(
                                "Duplicate message must not reexecute worker"))
        self.assertEqual(again["status"],"REASON_PRIOR_RESULT_REUSED")
        self.assertFalse(again["dispatched"])
        self.assertEqual(again["queue"],first["queue"])
        self.receipts.extend([
            LOCAL/("taky-reason-claim-"+message_id+".json"),
            LOCAL/("taky-reason-result-"+message_id+".json"),
            LOCAL/("taky-intake-snapshot-"+message_id+".json"),
            ROOT/first["queue"]["local_queue_receipt"],
        ])

    def test_real_registry_verified_dependency_reuses_existing_evidence(self):
        output=self.run_manifest([{"work_id":"CLN-009","depends_on":["CLN-003"]}])
        self.assertEqual(output["status"],"REGISTERED_LOCAL_TASKS_OBSERVED")
        self.assertEqual(output["items_total"],1)
        self.assertEqual(output["items_executed"],0)
        self.assertEqual(output["items"][0]["status"],
                         "REUSED_CANONICAL_LOCAL_EVIDENCE")
        self.assertEqual(len(output["items"][0]["evidence_sha256"]),64)
        self.assertEqual(output["goals_verified_done"],0)
        self.assertEqual(output["model_calls"],0)

    def test_real_registry_pending_dependent_does_not_wait_on_other(self):
        output=self.run_manifest([
            {"work_id":"SKL-001","depends_on":["CLN-001","CLN-002"]},
            {"work_id":"CLN-009","depends_on":["CLN-003"]},
        ])
        self.assertEqual(output["status"],"REGISTERED_LOCAL_TASKS_PARTIALLY_DEFERRED")
        self.assertEqual(output["items_deferred"],1)
        self.assertEqual(output["items"][0]["status"],
                         "WAIT_FOR_REGISTERED_VERIFIED_EVIDENCE")
        self.assertEqual(output["items"][1]["status"],
                         "REUSED_CANONICAL_LOCAL_EVIDENCE")
        self.assertEqual(output["items_executed"],0)

    def test_source_board_does_not_match_manifest_dependency_rejected(self):
        output=self.run_manifest([
            {"work_id":"CLN-009","depends_on":[]},
        ])
        self.assertEqual(output["status"],"QUEUE_V2_CANONICAL_BINDING_REJECTED")

    def test_approval_or_unbound_executor_never_accepted(self):
        output=self.run_manifest([{"work_id":"UPD-001","depends_on":[]}])
        self.assertEqual(output["status"],"QUEUE_V2_CANONICAL_BINDING_REJECTED")

    def test_unsafe_custom_fields_never_turn_into_tools(self):
        output=self.run_manifest([{"work_id":"CLN-009",
                                   "depends_on":["CLN-003"],
                                   "command":"powershell.exe /c something"}])
        self.assertEqual(output["status"],"QUEUE_V2_STEP_INVALID")

    def test_validate_only_checks_canonical_authority_without_local_execution(self):
        output=self.run_manifest([{"work_id":"CLN-009","depends_on":["CLN-003"]}],
                                 validate_only=True)
        self.assertEqual(output["status"],"QUEUE_INPUT_VERIFIED_NOT_DISPATCHED")
        self.assertEqual(output["items_executed"],0)
        self.assertEqual(output["goals_verified_done"],0)
        self.assertNotIn("local_queue_receipt",output)

    def test_synthetic_unverified_upstream_never_dispatches(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)
            board_file=target/"REGISTER.json"
            source=target/"signed-proof.json"
            source.write_text('{"test":"canonical source"}',encoding="utf-8")
            board={"tasks":[
                {"id":"CLN-003","status":"IMPLEMENTING","evidence":[str(source)],
                 "approval_required":False,"dependencies":[]},
                {"id":"CLN-009","status":"IMPLEMENTING","approval_required":False,
                 "dependencies":["CLN-003"],"title":"Safe cleanup work",
                 "priority":"P0"},
            ]}
            board_file.write_text(json.dumps(board),encoding="utf-8")
            with patch.object(canonical,"DEFAULT_BOARD",board_file), patch.object(
                    canonical,"EVIDENCE",target), patch.object(
                    canonical,"run_checks",
                    side_effect=AssertionError("not yet done, do not call")):
                result=self.run_manifest([
                    {"work_id":"CLN-009","depends_on":["CLN-003"]}])
            self.assertEqual(result["items"][0]["status"],
                             "WAIT_FOR_REGISTERED_VERIFIED_EVIDENCE")
            self.assertEqual(result["goals_verified_done"],0)

    def test_synthetic_verified_parent_calls_existing_worker_once(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)
            board_file=target/"REGISTER.json"
            parent_proof=target/"signed-parent.json"
            parent_proof.write_text('{"source":"registry-anchored evidence"}',encoding="utf-8")
            board={"tasks":[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(parent_proof)],
                 "approval_required":False,"dependencies":[]},
                {"id":"CLN-009","status":"IMPLEMENTING","approval_required":False,
                 "dependencies":["CLN-003"],"title":"Safe cleanup work",
                 "priority":"P0"},
            ]}
            board_file.write_text(json.dumps(board),encoding="utf-8")
            calls=[]
            def fake_existing_executor(work_id,src,evidence):
                calls.append(work_id)
                proof=evidence/"signed-child.json"
                proof.write_text(json.dumps({
                    "schema":"TAKY_LOCAL_WORK_SLICE_V1","task_id":work_id,
                    "state":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE",
                    "portfolio_done":False,"no_model_calls":True}),encoding="utf-8")
                return {"task_id":work_id,"status":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE",
                        "evidence":str(proof),"no_model_calls":True}
            with patch.object(canonical,"DEFAULT_BOARD",board_file), patch.object(
                    canonical,"EVIDENCE",target):
                from taky_registered_goal_queue import execute_registered_queue
                import hashlib
                from taky_registered_goal_queue import registered_dependency_revision
                idx={x["id"]:x for x in board["tasks"]}
                revision=registered_dependency_revision(["CLN-003"],idx,target)
                stamp=hashlib.sha256(("CLN-009|"+revision).encode()).hexdigest()[:24]
                self.receipts.append(LOCAL/(
                    "taky-registered-worker-CLN-009-"+stamp+".json"))
                result=execute_registered_queue({
                    "schema":"TAKY_GOAL_QUEUE_V2","queue_id":"synthetic-verified",
                    "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}]},
                    ROOT,LOCAL,registered_executor=fake_existing_executor)
            self.assertEqual(calls,["CLN-009"])
            self.assertEqual(result["items"][0]["status"],
                             "LOCAL_DIAGNOSIS_EVIDENCED_NOT_DONE")
            self.assertEqual(result["model_calls"],0)
            self.assertEqual(result["goals_verified_done"],0)
            self.receipts.append(ROOT/result["local_queue_receipt"])

    def test_stale_cached_probe_is_not_new_dependency_acceptance(self):
        from taky_registered_goal_queue import (
            execute_registered_queue, registered_dependency_revision)
        with tempfile.TemporaryDirectory() as tmp:
            temp=Path(tmp)
            board=temp/"board.json"
            parent_evidence=temp/"parent.json"
            parent_evidence.write_text('{"evidence":"registered"}',encoding="utf-8")
            old_child=temp/"child-old.json"
            old_child.write_text(json.dumps({
                "schema":"TAKY_LOCAL_WORK_SLICE_V1","task_id":"CLN-009",
                "portfolio_done":False}),encoding="utf-8")
            rows={"tasks":[
                {"id":"CLN-003","status":"VERIFIED",
                 "evidence":[str(parent_evidence)]},
                {"id":"CLN-009","status":"IMPLEMENTING",
                 "approval_required":False,"dependencies":["CLN-003"]},
            ]}
            board.write_text(json.dumps(rows),encoding="utf-8")
            source={"CLN-003":rows["tasks"][0],"CLN-009":rows["tasks"][1]}
            expected=registered_dependency_revision(["CLN-003"],source,temp)
            def cached(*args,**kwargs):
                return {"considered":[{"task_id":"CLN-009",
                        "route":"LOCAL_SLICE_ALREADY_EVIDENCED",
                        "existing_evidence":str(old_child)}]}
            new_child=temp/"child-with-revision.json"
            called=[]
            def worker(work_id,board_path,evidence_dir):
                called.append(work_id)
                new_child.write_text(json.dumps({
                    "schema":"TAKY_LOCAL_WORK_SLICE_V1","task_id":work_id,
                    "state":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE",
                    "portfolio_done":False,
                    "inputs":{"registered_dependency_revision":expected}}),
                    encoding="utf-8")
                return {"task_id":work_id,"no_model_calls":True,
                        "evidence":str(new_child)}
            claims_before=set(LOCAL.glob("taky-registered-worker-CLN-009-*.json"))
            with patch.object(canonical,"DEFAULT_BOARD",board),patch.object(
                    canonical,"EVIDENCE",temp),patch.object(
                    canonical,"choose",side_effect=cached):
                outcome=execute_registered_queue({
                    "schema":"TAKY_GOAL_QUEUE_V2","queue_id":"registered-stale-cache",
                    "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}]},
                    ROOT,LOCAL,expected_dependencies={"CLN-009":expected},
                    registered_executor=worker)
            self.assertEqual(outcome["items"][0]["status"],
                             "LOCAL_DIAGNOSIS_EVIDENCED_NOT_DONE")
            self.assertEqual(called,["CLN-009"])
            self.assertTrue(old_child.is_file())
            self.assertTrue(new_child.is_file())
            self.assertEqual(outcome["items_deferred"],0)
            self.assertEqual(outcome["goals_verified_done"],0)
            self.receipts.append(ROOT/outcome["local_queue_receipt"])
            self.receipts.extend(set(LOCAL.glob(
                "taky-registered-worker-CLN-009-*.json"))-claims_before)

    def test_pinned_parent_revision_rejects_altered_proof_before_dispatch(self):
        from taky_registered_goal_queue import execute_registered_queue
        with tempfile.TemporaryDirectory() as tmp:
            temp=Path(tmp)
            board=temp/"board.json"
            proof=temp/"parent.json"
            proof.write_text('{"revision":1}',encoding="utf-8")
            board.write_text(json.dumps({"tasks":[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(proof)]},
                {"id":"CLN-009","status":"IMPLEMENTING",
                 "approval_required":False,"dependencies":["CLN-003"]},
            ]}),encoding="utf-8")
            with patch.object(canonical,"DEFAULT_BOARD",board),patch.object(
                    canonical,"EVIDENCE",temp):
                outcome=execute_registered_queue({
                    "schema":"TAKY_GOAL_QUEUE_V2","queue_id":"registered-stale-source",
                    "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}]},
                    ROOT,LOCAL,expected_dependencies={"CLN-009":"f"*64},
                    registered_executor=lambda *_:self.fail("drift must not run"))
            self.assertEqual(outcome["items"][0]["status"],
                             "DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED")
            self.receipts.append(ROOT/outcome["local_queue_receipt"])

    def test_dependency_preclaim_drift_is_not_registered_worker_launch(self):
        from taky_registered_goal_queue import (
            execute_registered_queue,registered_dependency_revision)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            parent=base/"parent.json"
            parent.write_text('{"version":"A"}',encoding="utf-8")
            board=base/"board.json"
            rows={"tasks":[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(parent)]},
                {"id":"CLN-009","status":"IMPLEMENTING",
                 "approval_required":False,"dependencies":["CLN-003"],
                 "title":"Local audit"},
            ]}
            board.write_text(json.dumps(rows),encoding="utf-8")
            first=registered_dependency_revision(["CLN-003"],
                  {x["id"]:x for x in rows["tasks"]},base)
            parent.write_text('{"version":"B"}',encoding="utf-8")
            changed=registered_dependency_revision(["CLN-003"],
                  {x["id"]:x for x in rows["tasks"]},base)
            parent.write_text('{"version":"A"}',encoding="utf-8")
            with patch.object(canonical,"DEFAULT_BOARD",board),patch.object(
                 canonical,"EVIDENCE",base),patch.object(
                 canonical,"run_checks",side_effect=
                   canonical.CanonicalPreclaimDependencyHold(changed)):
                result=execute_registered_queue({
                    "schema":"TAKY_GOAL_QUEUE_V2","queue_id":"rev-rejected-a",
                    "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}]},
                    ROOT,LOCAL,expected_dependencies={"CLN-009":first})
            row=result["items"][0]
            self.assertEqual(row["status"],
                             "DEPENDENCY_REVISION_CHANGED_RECHECK_REQUIRED")
            self.assertEqual(row["gate_observed_dependency_revision"],changed)
            self.assertFalse(row["attempted"])
            self.receipts.append(ROOT/result["local_queue_receipt"])

    def test_canonical_typed_preclaim_source_hold_is_rearmable(self):
        from taky_registered_goal_queue import execute_registered_queue
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            parent=base/"parent-proof.json"
            parent.write_text('{"source":"verified"}',encoding="utf-8")
            board=base/"tasks.json"
            board.write_text(json.dumps({"tasks":[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(parent)]},
                {"id":"CLN-009","status":"IMPLEMENTING",
                 "approval_required":False,"dependencies":["CLN-003"],
                 "title":"Local read-only checks"},
            ]}),encoding="utf-8")
            with patch.object(canonical,"DEFAULT_BOARD",board),patch.object(
                 canonical,"EVIDENCE",base),patch.object(
                 canonical,"run_checks",side_effect=
                     canonical.CanonicalPreclaimSourceHold("OSError")):
                result=execute_registered_queue({
                    "schema":"TAKY_GOAL_QUEUE_V2","queue_id":"canonical-typed-hold",
                    "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}]},
                    ROOT,LOCAL)
            event=result["items"][0]
            self.assertEqual(event["status"],"EXISTING_CANONICAL_GATE_HOLD")
            self.assertEqual(event["gate_route"],"LOCAL_INPUT_PROVENANCE_HOLD")
            self.assertEqual(event["gate_input_error_type"],"OSError")
            self.assertFalse(event["attempted"])
            self.assertEqual(result["goals_verified_done"],0)
            self.receipts.append(ROOT/result["local_queue_receipt"])

    def test_canonical_prefail_not_claimed_as_worker_launch(self):
        from taky_registered_goal_queue import execute_registered_queue
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            parent=base/"parent-proof.json"
            parent.write_text('{"source":"verified"}',encoding="utf-8")
            board=base/"tasks.json"
            board.write_text(json.dumps({"tasks":[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(parent)]},
                {"id":"CLN-009","status":"IMPLEMENTING",
                 "approval_required":False,"dependencies":["CLN-003"],
                 "title":"Local read-only checks"},
            ]}),encoding="utf-8")
            with patch.object(canonical,"DEFAULT_BOARD",board),patch.object(
                 canonical,"EVIDENCE",base),patch.object(
                 canonical,"run_checks",side_effect=ValueError(
                     "PREFLIGHT_SOURCE_MISSING")):
                result=execute_registered_queue({
                    "schema":"TAKY_GOAL_QUEUE_V2","queue_id":"canonical-predisp",
                    "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}]},
                    ROOT,LOCAL)
            self.assertEqual(result["items"][0]["status"],
                             "SAFE_LOCAL_RECOVERY_REQUIRED")
            self.assertFalse(result["items"][0]["attempted"])
            self.assertEqual(result["goals_verified_done"],0)
            self.receipts.append(ROOT/result["local_queue_receipt"])

    def test_same_source_worker_claim_blocks_duplicate_independent_message(self):
        from taky_registered_goal_queue import (
            execute_registered_queue,registered_dependency_revision)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            board=base/"REGISTER.json"
            parent=base/"parent.json"
            parent.write_text('{"registered":"verified"}',encoding="utf-8")
            rows={"tasks":[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(parent)]},
                {"id":"CLN-009","status":"IMPLEMENTING","approval_required":False,
                 "dependencies":["CLN-003"],"priority":"P0"},
            ]}
            board.write_text(json.dumps(rows),encoding="utf-8")
            child=base/"child.json"
            calls=[]
            def worker(work,src,evidence):
                calls.append(work)
                child.write_text(json.dumps({
                    "schema":"TAKY_LOCAL_WORK_SLICE_V1",
                    "task_id":work,"portfolio_done":False,
                    "state":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE"}),
                    encoding="utf-8")
                return {"task_id":work,"evidence":str(child),
                        "no_model_calls":True}
            def ready(*_a,**_k):
                return {"considered":[{"task_id":"CLN-009",
                         "route":"READY_FOR_LOCAL_EXECUTION"}]}
            source_version="test-source-"+uuid4().hex
            existing=set(LOCAL.glob("taky-registered-worker-CLN-009-*.json"))
            with patch.object(canonical,"DEFAULT_BOARD",board),patch.object(
                    canonical,"EVIDENCE",base),patch.object(
                    canonical,"choose",side_effect=ready),patch.object(
                    canonical,"evidence_signature",
                    return_value=({"test":"registered"},source_version)):
                doc={"schema":"TAKY_GOAL_QUEUE_V2","queue_id":"test-double-claim",
                     "items":[{"work_id":"CLN-009","depends_on":["CLN-003"]}]}
                first=execute_registered_queue(doc,ROOT,LOCAL,
                     registered_executor=worker)
                again=execute_registered_queue(doc,ROOT,LOCAL,
                     registered_executor=lambda *_:self.fail("must not run twice"))
            self.assertEqual(first["items"][0]["status"],
                             "LOCAL_DIAGNOSIS_EVIDENCED_NOT_DONE")
            self.assertEqual(again["items"][0]["status"],
                             "REGISTERED_WORKER_ALREADY_CLAIMED")
            self.assertEqual(again["items_executed"],0)
            self.assertEqual(calls,["CLN-009"])
            self.receipts.extend([ROOT/first["local_queue_receipt"],
                                  ROOT/again["local_queue_receipt"]])
            self.receipts.extend(set(LOCAL.glob(
                "taky-registered-worker-CLN-009-*.json"))-existing)

    def test_missing_upstream_evidence_cannot_advance_even_if_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)
            board_file=target/"REGISTER.json"
            board={"tasks":[
                {"id":"CLN-003","status":"VERIFIED",
                 "evidence":[str(target/"missing.json")],
                 "approval_required":False,"dependencies":[]},
                {"id":"CLN-009","status":"IMPLEMENTING","approval_required":False,
                 "dependencies":["CLN-003"],"title":"Safe cleanup work",
                 "priority":"P0"},
            ]}
            board_file.write_text(json.dumps(board),encoding="utf-8")
            with patch.object(canonical,"DEFAULT_BOARD",board_file), patch.object(
                    canonical,"EVIDENCE",target):
                result=self.run_manifest([
                    {"work_id":"CLN-009","depends_on":["CLN-003"]}])
            self.assertEqual(result["items"][0]["status"],
                             "WAIT_FOR_REGISTERED_VERIFIED_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
