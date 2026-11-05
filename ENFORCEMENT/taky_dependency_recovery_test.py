"""State-change recovery for TAKY's canonical deferred V2 tasks.

Tests exercise durable Reason receipt binding, source-provenance changes,
at-most-once recovery and no false DONE; no real providers or registry edits.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"TOOLS"))
import TAKY_ORCHESTRATION_ADVANCE as c
from taky_dependency_recovery import recover_deferred_once


class DeferredRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name)
        self.local=self.repo/".local"
        self.local.mkdir()
        (self.repo/"TOOLS").mkdir()
        self.proofs=self.repo/"evidence"
        self.proofs.mkdir()
        self.board=self.repo/"board.json"
        self.mid="01M5TESTRECO" + "Q"*15
        self.qid="recovery-e2e"
        self.snap=self.local/("taky-intake-snapshot-"+self.mid+".json")
        manifest={"schema":"TAKY_GOAL_QUEUE_V2","queue_id":self.qid,"items":[
            {"work_id":"CLN-009","depends_on":["CLN-003"]}]}
        data=json.dumps(manifest).encode()
        self.snap.write_bytes(data)
        self.manifest_hash=hashlib.sha256(data).hexdigest()
        (self.local/("taky-reason-claim-"+self.mid+".json")).write_text(json.dumps({
            "schema":"TAKY_REASON_CLAIM_V1","state":"RECORDED",
            "message_id":self.mid,"queue_id":self.qid,
            "manifest_sha256":self.manifest_hash}),encoding="utf-8")
        self.base_result={"schema":"TAKY_REASON_RESULT_V1","message_id":self.mid,
             "queue_id":self.qid,"manifest_sha256":self.manifest_hash,
             "queue":{"schema":"TAKY_GOAL_QUEUE_OBSERVATION_V2",
                      "items":[{"work_id":"CLN-009",
                                "status":"WAIT_FOR_REGISTERED_VERIFIED_EVIDENCE"}]}}
        self.source=self.local/("taky-reason-result-"+self.mid+".json")
        self.source.write_text(json.dumps(self.base_result),encoding="utf-8")
        self.evidence=self.proofs/"parent-evidence.json"
        self.evidence.write_text(json.dumps({"source":"canonical original"}),encoding="utf-8")
        self.tasks=[
            {"id":"CLN-003","status":"IMPLEMENTING","approval_required":False,
             "evidence":[str(self.evidence)]},
            {"id":"CLN-009","status":"IMPLEMENTING","approval_required":False,
             "dependencies":["CLN-003"]},
        ]
        self.save_board()
        p1=patch.object(c,"DEFAULT_BOARD",self.board)
        p2=patch.object(c,"EVIDENCE",self.proofs)
        p1.start();p2.start();self.addCleanup(p1.stop);self.addCleanup(p2.stop)
        self.calls=[]
        self.output_files=[]

    def save_board(self):
        self.board.write_text(json.dumps({"tasks":self.tasks}),encoding="utf-8")

    def fake_queue(self,doc,root,local,*,expected_dependencies=None):
        self.calls.append(doc)
        result={"schema":"TAKY_GOAL_QUEUE_OBSERVATION_V2",
                "queue_id":doc["queue_id"],"status":"REGISTERED_LOCAL_TASKS_OBSERVED",
                "items":[{"work_id":"CLN-009",
                          "status":"REUSED_CANONICAL_LOCAL_EVIDENCE"}],
                "model_calls":0,"goals_verified_done":0}
        path=local/("taky-goal-queue-test-result-"+str(len(self.calls))+".json")
        path.write_text(json.dumps(result),encoding="utf-8")
        self.output_files.append(path)
        return {**result,"local_queue_receipt":".local/"+path.name}

    def scan(self,executor=None):
        return recover_deferred_once(self.repo,
              observer=lambda:json.loads(self.board.read_text(encoding="utf-8")),
              admission=executor or self.fake_queue)

    def test_no_busy_wait_until_verified_upstream(self):
        a=self.scan()
        b=self.scan()
        self.assertEqual(a["new_attempts"],0)
        self.assertEqual(b["new_attempts"],0)
        self.assertEqual(self.calls,[])
        self.assertEqual(a["still_waiting"],1)

    def test_source_verified_then_one_recovery_and_no_duplicate(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        first=self.scan()
        second=self.scan()
        self.assertEqual(first["new_attempts"],1)
        self.assertEqual(first["reused_evidence"],1)
        self.assertEqual(second["new_attempts"],0)
        self.assertEqual(second["already_claimed"],1)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(first["new_model_calls"],0)
        self.assertFalse(first["portfolio_done_claimed"])

    def test_approval_revocation_blocks_recovery(self):
        self.tasks[0]["status"]="VERIFIED"
        self.tasks[1]["approval_required"]=True
        self.save_board()
        self.assertEqual(self.scan()["new_attempts"],0)
        self.assertEqual(len(self.calls),0)

    def test_missing_parent_evidence_keeps_waiting(self):
        self.tasks[0]["status"]="VERIFIED"
        self.evidence.unlink()
        self.save_board()
        state=self.scan()
        self.assertEqual(state["new_attempts"],0)
        self.assertEqual(state["still_waiting"],1)

    def test_unverified_worker_stdout_does_not_count(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        def forged(*args):
            return {"schema":"TAKY_GOAL_QUEUE_OBSERVATION_V2",
                    "queue_id":self.qid,"model_calls":0,"goals_verified_done":0,
                    "local_queue_receipt":".local/not-actually-saved.json"}
        state=self.scan(forged)
        self.assertEqual(state["new_attempts"],0)
        self.assertEqual(state["uncertain"],1)
        state2=self.scan(forged)
        self.assertEqual(state2["already_claimed"],1)

    def test_parent_changed_proof_can_be_rechecked_with_new_receipt(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        self.scan()
        self.evidence.write_text(json.dumps({"source":"new approved canonical"}),encoding="utf-8")
        state=self.scan()
        self.assertEqual(state["new_attempts"],1)
        self.assertEqual(len(self.calls),2)
        self.assertFalse(state["portfolio_done_claimed"])

    def test_spoofed_result_without_claim_not_recovered(self):
        (self.local/("taky-reason-claim-"+self.mid+".json")).unlink()
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        result=self.scan()
        self.assertEqual(result["new_attempts"],0)
        self.assertEqual(self.calls,[])

    def test_same_registered_revision_cannot_wake_twice_from_two_messages(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        second="01M5TESTRECO"+"R"*15
        old=self.local/("taky-reason-result-"+second+".json")
        duplicate=dict(self.base_result,message_id=second)
        old.write_text(json.dumps(duplicate),encoding="utf-8")
        (self.local/("taky-reason-claim-"+second+".json")).write_text(json.dumps({
            "schema":"TAKY_REASON_CLAIM_V1","state":"RECORDED",
            "message_id":second,"queue_id":self.qid,
            "manifest_sha256":self.manifest_hash}),encoding="utf-8")
        (self.local/("taky-intake-snapshot-"+second+".json")).write_bytes(
            self.snap.read_bytes())
        first=self.scan()
        self.assertEqual(first["new_attempts"],1)
        self.assertEqual(first["already_claimed"],1)
        self.assertEqual(len(self.calls),1)

    def test_rotating_cursor_does_not_starve_old_deferred_work(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        for index in range(42):
            # Valid filenames but unrelated schema: must not block a later
            # eligible real Reason receipt forever.
            (self.local/("taky-reason-result-00FAKE"+str(index).zfill(35)+".json")
             ).write_text("{}",encoding="utf-8")
        attempts=[]
        for _ in range(4):
            attempts.append(recover_deferred_once(
                self.repo,max_receipts=16,
                observer=lambda:json.loads(self.board.read_text(encoding="utf-8")),
                admission=self.fake_queue))
        self.assertEqual(sum(x["new_attempts"] for x in attempts),1)
        self.assertEqual(len(self.calls),1)
        cursor=json.loads((self.local/"taky-dependency-scan-cursor.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(cursor["schema"],"TAKY_DEPENDENCY_CURSOR_V1")

    def test_known_predispatch_hold_rearms_only_after_correction(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        called=[]
        def hold_before_worker(doc,root,local,*,expected_dependencies=None):
            called.append(doc["items"][0]["work_id"])
            result={"schema":"TAKY_GOAL_QUEUE_OBSERVATION_V2",
                    "queue_id":doc["queue_id"],"model_calls":0,
                    "goals_verified_done":0,
                    "status":"REGISTERED_LOCAL_TASKS_PARTIALLY_DEFERRED",
                    "items":[{"work_id":"CLN-009",
                        "status":"EXISTING_CANONICAL_GATE_HOLD",
                        "attempted":False}]}
            path=local/("taky-goal-queue-hold-"+str(len(called))+".json")
            path.write_text(json.dumps(result),encoding="utf-8")
            return {**result,"local_queue_receipt":".local/"+path.name}
        first=self.scan(hold_before_worker)
        self.assertEqual(first["new_attempts"],1)
        claims=list(self.local.glob("taky-dependency-attempt-CLN-009-*.json"))
        self.assertEqual(len(claims),1)
        self.assertEqual(json.loads(claims[0].read_text(encoding="utf-8"))["state"],
                         "PREDISPATCH_HOLD_NO_WORKER_CALL")
        second=self.scan(hold_before_worker)
        self.assertEqual(second["new_attempts"],0)
        self.tasks[1]["title"]="Corrected canonical readiness"
        self.save_board()
        third=self.scan(hold_before_worker)
        self.assertEqual(third["new_attempts"],1)
        self.assertEqual(called,["CLN-009","CLN-009"])
        fourth=self.scan(hold_before_worker)
        self.assertEqual(fourth["new_attempts"],0)
        self.assertEqual(len(called),2)

    def test_gate_observed_unavailable_not_old_available_rearm_pin(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        visits=[]
        def outage_at_gate(doc,root,local,*,expected_dependencies=None):
            visits.append(1)
            data={"schema":"TAKY_GOAL_QUEUE_OBSERVATION_V2",
                  "queue_id":doc["queue_id"],"model_calls":0,
                  "goals_verified_done":0,
                  "status":"REGISTERED_LOCAL_TASKS_PARTIALLY_DEFERRED",
                  "items":[{"work_id":"CLN-009",
                            "status":"EXISTING_CANONICAL_GATE_HOLD",
                            "gate_route":"LOCAL_INPUT_PROVENANCE_HOLD",
                            "gate_input_error_type":"OSError",
                            "attempted":False}]}
            output=local/("taky-goal-queue-gate-fail-"+str(len(visits))+".json")
            output.write_text(json.dumps(data),encoding="utf-8")
            return {**data,"local_queue_receipt":".local/"+output.name}
        a=self.scan(outage_at_gate)
        b=self.scan(outage_at_gate)
        c=self.scan(outage_at_gate)
        self.assertEqual(a["new_attempts"],1)
        self.assertEqual(b["new_attempts"],1)
        self.assertEqual(c["new_attempts"],0)
        self.assertEqual(len(visits),2)
        self.assertFalse(b["portfolio_done_claimed"])

    def test_malformed_cursor_and_non_object_receipts_do_not_starve_work(self):
        self.tasks[0]["status"]="VERIFIED"
        self.save_board()
        cursor=self.local/"taky-dependency-scan-cursor.json"
        cursor.write_text("[]",encoding="utf-8")
        malformed=self.local/"taky-reason-result-00BADRECEIPT.json"
        malformed.write_text("[]",encoding="utf-8")
        first=self.scan()
        self.assertEqual(first["new_attempts"],1)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(json.loads(cursor.read_text(encoding="utf-8"))["schema"],
                         "TAKY_DEPENDENCY_CURSOR_V1")
        again=self.scan()
        self.assertEqual(again["new_attempts"],0)

    def test_max_receipts_rejects_invalid_limits(self):
        for count in (0,-1,51,True):
            self.assertEqual(recover_deferred_once(self.repo,max_receipts=count)["status"],
                             "DEPENDENCY_WATCH_INVALID_LIMIT")


if __name__=="__main__":
    unittest.main()
