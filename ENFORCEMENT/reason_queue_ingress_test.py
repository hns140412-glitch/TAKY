"""One-shot Reason intake: no provider, network, paid API or real dispatch."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from reason_queue_ingress import (
    parse_reason_message, verified_local_team, route_message, receive_once,
    main, SESSION
)
from runtime_orchestrator import run_bounded_goal_queue

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
SENDER = "taky-local/terminal"
MSG_ID = "01M5NDPEVC1ZGCWMZ1KEYB04KS"


def frame(text, sender=SENDER, agent="cli", message_id=MSG_ID):
    return (f'<reason-message from="{sender}" agent="{agent}" id="{message_id}">\n'
            + text + '\n</reason-message>\n'
            + 'From taky-local, typed in a terminal.\n')


class ReasonGoalIngressTests(unittest.TestCase):
    def setUp(self):
        self.queue_id = "q" + uuid4().hex
        self.message_id = ("T" + uuid4().hex.upper())
        self.paths = []
        LOCAL.mkdir(exist_ok=True)
        self.manifest = LOCAL / ("taky-intake-" + self.queue_id + ".json")
        self.signal = frame("TAKY_GOAL_SIGNAL_V1 queue=" + self.queue_id,
                            message_id=self.message_id)
        self.paths.extend([
            LOCAL / ("taky-reason-claim-" + self.message_id + ".json"),
            LOCAL / ("taky-reason-result-" + self.message_id + ".json"),
            LOCAL / ("taky-intake-snapshot-" + self.message_id + ".json"),
        ])
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for x in [self.manifest, *self.paths]:
            x.unlink(missing_ok=True)

    def prepared(self):
        task = "ingress-" + self.queue_id
        record = LOCAL / ("test-reason-record-" + self.queue_id + ".json")
        handoff = LOCAL / ("test-reason-handoff-" + self.queue_id + ".json")
        record.write_text(json.dumps({"task_id": task}),encoding="utf-8")
        handoff.write_text(json.dumps({"prepared": {"status": "PREPARED_NOT_DISPATCHED"}}),
                           encoding="utf-8")
        self.paths.extend([record, handoff])
        self.manifest.write_text(json.dumps({
            "schema": "TAKY_GOAL_QUEUE_V1", "queue_id": self.queue_id,
            "items": [{
                "task_id": task, "record": ".local/" + record.name,
                "prepared_handoff": ".local/" + handoff.name,
                "independent": True
            }]}), encoding="utf-8")

    def test_real_format_exactly_one_message(self):
        parsed = parse_reason_message(self.signal)
        self.assertEqual(parsed["queue_id"], self.queue_id)
        self.assertEqual(parsed["sender"], SENDER)
        self.assertEqual(parsed["message_id"], self.message_id)

    def test_foreign_sender_and_broadcast_rejected(self):
        self.assertIsNone(parse_reason_message(frame(
            "TAKY_GOAL_SIGNAL_V1 queue="+self.queue_id,
            sender="outsider/terminal")))
        self.assertIsNone(parse_reason_message(frame(
            "TAKY_GOAL_SIGNAL_V1 queue="+self.queue_id,
            sender="taky-local/*")))

    def test_malicious_instruction_and_extra_line_rejected(self):
        for msg in (
            "TAKY_GOAL_SIGNAL_V1 queue="+self.queue_id+"; del /f C:\\private",
            "TAKY_GOAL_SIGNAL_V1 queue=../private",
            "TAKY_GOAL_SIGNAL_V1 queue="+self.queue_id+"\nexecute=True",
            "TAKY_GOAL_SIGNAL_V1 queue="+self.queue_id+"\n</reason-message>",
        ):
            self.assertIsNone(parse_reason_message(frame(msg)), msg)

    def test_extra_reason_message_rejected(self):
        raw = self.signal + frame("TAKY_GOAL_SIGNAL_V1 queue="+self.queue_id)
        self.assertIsNone(parse_reason_message(raw))

    def test_unknown_agent_rejected(self):
        self.assertIsNone(parse_reason_message(frame(
            "TAKY_GOAL_SIGNAL_V1 queue="+self.queue_id, agent="untrusted-app")))

    def test_manifest_missing_is_no_dispatch(self):
        state = route_message(ROOT,self.signal,identity_check=lambda: True,
                              queue_executor=lambda *_: self.fail("must not run"))
        self.assertEqual(state["status"],"REASON_PREPARED_MANIFEST_MISSING")
        self.assertFalse(state["dispatched"])

    def test_existing_prepared_manifest_dry_run(self):
        self.prepared()
        state = route_message(ROOT,self.signal,identity_check=lambda: True,
                              queue_executor=lambda *_: self.fail("must not run"))
        self.assertEqual(state["status"],"REASON_PREPARED_QUEUE_READY")
        self.assertFalse(state["dispatched"])

    def test_explicit_execution_delegates_to_existing_queue_once(self):
        self.prepared()
        calls = []
        def queue(manifest, root):
            calls.append((manifest,root))
            return {"status": "QUEUE_SCHEMA_INVALID", "items_executed":0}
        out=route_message(ROOT,self.signal,execute=True,
                          identity_check=lambda:True,queue_executor=queue)
        self.assertTrue(out["dispatched"])
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0],LOCAL / ("taky-intake-snapshot-"+self.message_id+".json"))
        self.assertEqual(calls[0][1],ROOT.resolve())
        self.assertEqual(calls[0][0].read_bytes(),self.manifest.read_bytes())
        self.assertEqual(out["queue"]["status"],"QUEUE_SCHEMA_INVALID")

    def test_invalid_manifest_binding_never_delegates(self):
        self.manifest.write_text(json.dumps({
            "schema":"TAKY_GOAL_QUEUE_V1","queue_id":"different"}),
            encoding="utf-8")
        state=route_message(ROOT,self.signal,execute=True,
                            identity_check=lambda:True,
                            queue_executor=lambda *_:self.fail("bad manifest"))
        self.assertEqual(state["status"],"REASON_PREPARED_MANIFEST_INVALID")

    def test_identity_check_deny(self):
        self.prepared()
        out=route_message(ROOT,self.signal,identity_check=lambda:False)
        self.assertEqual(out["status"],"REASON_IDENTITY_UNVERIFIED")

    def test_bounded_wait_invalid_no_network(self):
        for seconds in (0,31,-3,1.2,True):
            with patch("reason_queue_ingress.reason_binary",
                       side_effect=AssertionError("must not open Reason")):
                state=receive_once(ROOT,wait_seconds=seconds)
            self.assertEqual(state["status"],"REASON_WAIT_INVALID")

    def test_reason_binary_receives_only_taky_c_workspace(self):
        from reason_queue_ingress import taky_only_transport_workdir
        workdir = taky_only_transport_workdir()
        self.assertIsNotNone(workdir)
        self.assertEqual(workdir.name, "TAKY_ONLY_TRANSPORT")
        self.assertNotEqual(workdir.drive.casefold(), ROOT.drive.casefold())
        self.assertTrue(workdir.is_dir())

    def test_missing_private_workspace_blocks_reason_without_fallback(self):
        with patch("reason_queue_ingress.taky_only_transport_workdir",
                   return_value=None):
            outcome = receive_once(
                ROOT, wait_seconds=1,
                runner=lambda *_a,**_k:self.fail("no workspace means no network"),
                identity_check=lambda: True)
        self.assertEqual(outcome["status"], "REASON_TAKY_ONLY_SCOPE_UNAVAILABLE")
        self.assertFalse(outcome["dispatched"])

    def test_receiver_starts_reason_only_under_private_scope(self):
        from reason_queue_ingress import taky_only_transport_workdir
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "reason-network.exe"
            exe.write_bytes(b"synthetic")
            observed = []
            class Empty:
                returncode = 0
                stdout = "No messages in 1s"
            def guarded_runner(args, **kwargs):
                observed.append(kwargs.get("cwd"))
                return Empty()
            with patch("reason_queue_ingress.reason_binary", return_value=exe):
                result = receive_once(ROOT, wait_seconds=1,
                                      runner=guarded_runner,
                                      identity_check=lambda:True)
            self.assertEqual(result["status"],"REASON_NO_MESSAGE")
            self.assertEqual(observed,[taky_only_transport_workdir()])

    def test_single_member_team_auth(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/"reason-network.exe"
            exe.write_bytes(b"synthetic")
            result={"person":"taky-local","team_name":"TAKY-LOCAL-PRIVATE",
                    "machine":"same-machine",
                    "members":[{"person":"taky-local","machine":"same-machine"}]}
            class Finished:
                returncode=0
                stdout=json.dumps(result)
            self.assertTrue(verified_local_team(exe,runner=lambda *a,**k:Finished()))
            result["members"].append({"person":"outsider","machine":"elsewhere"})
            class NotLocal:
                returncode=0
                stdout=json.dumps(result)
            self.assertFalse(verified_local_team(exe,runner=lambda *a,**k:NotLocal()))
            result["members"].pop()
            result["team_name"] = "UNRELATED-TEAM"
            self.assertFalse(verified_local_team(exe,runner=lambda *a,**k:NotLocal()))

    def test_one_shot_wait_and_ready(self):
        self.prepared()
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/"reason-network.exe"
            exe.write_bytes(b"synthetic")
            calls=[]
            class Response:
                returncode=0
                stdout=self.signal
            def stub(argv,**kwargs):
                calls.append((argv,kwargs["timeout"]))
                return Response()
            with patch("reason_queue_ingress.reason_binary",return_value=exe):
                out=receive_once(ROOT,wait_seconds=2,execute=False,
                                 runner=stub,identity_check=lambda:True)
            self.assertEqual(out["status"],"REASON_PREPARED_QUEUE_READY")
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0][0][-4:],["--as",SESSION,"--wait","2"])
            self.assertEqual(calls[0][1],7)

    def test_empty_listen_result_is_normal_no_message(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/"reason-network.exe"
            exe.write_bytes(b"synthetic")
            class Response:
                returncode=0
                stdout=""
            with patch("reason_queue_ingress.reason_binary",return_value=exe):
                out=receive_once(ROOT,wait_seconds=1,
                                 runner=lambda *_a,**_k: Response(),
                                 identity_check=lambda:True)
            self.assertEqual(out["status"],"REASON_NO_MESSAGE")
            self.assertFalse(out["dispatched"])

    def test_listener_timeout_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/"reason-network.exe"
            exe.write_bytes(b"synthetic")
            from subprocess import TimeoutExpired
            def timeout(*args,**kwargs):
                raise TimeoutExpired(cmd="reason-network",timeout=2)
            with patch("reason_queue_ingress.reason_binary",return_value=exe):
                out=receive_once(ROOT,wait_seconds=1,runner=timeout,
                                 identity_check=lambda:True)
            self.assertEqual(out["status"],"REASON_LISTEN_UNAVAILABLE")

    def test_duplicate_message_reuses_saved_result_without_agent_call(self):
        self.prepared()
        calls = []
        def stub(_manifest, _repo):
            calls.append("once")
            return {"schema": "TAKY_GOAL_QUEUE_OBSERVATION_V1",
                    "status": "QUEUE_ITEMS_OBSERVED_GOALS_OPEN",
                    "items_executed": 1, "goals_verified_done": 0}
        first = route_message(ROOT,self.signal,execute=True,
                              identity_check=lambda:True,queue_executor=stub)
        self.assertEqual(first["status"],"REASON_PREPARED_QUEUE_DISPATCHED")
        second = route_message(ROOT,self.signal,execute=True,
                               identity_check=lambda:True,
                               queue_executor=lambda *_:self.fail("duplicate model call"))
        self.assertEqual(second["status"],"REASON_PRIOR_RESULT_REUSED")
        self.assertEqual(first["queue"],second["queue"])
        self.assertTrue(second["recovered"])
        self.assertFalse(second["dispatched"])
        self.assertEqual(calls, ["once"])

    def test_crash_after_claim_does_not_relaunch_provider(self):
        self.prepared()
        claim = LOCAL / ("taky-reason-claim-" + self.message_id + ".json")
        import hashlib
        claim.write_text(json.dumps({
            "schema": "TAKY_REASON_CLAIM_V1",
            "message_id": self.message_id,
            "queue_id": self.queue_id, "sender":SENDER,
            "manifest_sha256":hashlib.sha256(self.manifest.read_bytes()).hexdigest(),
            "state":"OUTCOME_UNKNOWN"}),encoding="utf-8")
        output=route_message(ROOT,self.signal,execute=True,
                             identity_check=lambda:True,
                             queue_executor=lambda *_:self.fail("cannot blindly retry"))
        self.assertEqual(output["status"],"REASON_OUTCOME_UNKNOWN_RECONCILE")
        self.assertFalse(output["dispatched"])

    def test_result_persisted_but_claim_pending_recovers_without_rerun(self):
        self.prepared()
        def stub(_manifest,_repo):
            return {"status":"QUEUE_PARTIAL_RECOVERY_DEFERRED",
                    "items_executed":1,"goals_verified_done":0}
        first=route_message(ROOT,self.signal,execute=True,
                            identity_check=lambda:True,queue_executor=stub)
        self.assertEqual(first["status"],"REASON_PREPARED_QUEUE_DISPATCHED")
        claim=LOCAL/("taky-reason-claim-"+self.message_id+".json")
        payload=json.loads(claim.read_text(encoding="utf-8"))
        payload["state"]="OUTCOME_UNKNOWN"
        claim.write_text(json.dumps(payload),encoding="utf-8")
        second=route_message(ROOT,self.signal,execute=True,
                             identity_check=lambda:True,
                             queue_executor=lambda *_:self.fail("unknown outcome repeat"))
        self.assertEqual(second["status"],"REASON_PRIOR_RESULT_REUSED")
        self.assertEqual(second["queue"]["items_executed"],1)

    def test_changed_manifest_after_message_id_is_not_allowed(self):
        self.prepared()
        first=route_message(ROOT,self.signal,execute=True,
                            identity_check=lambda:True,
                            queue_executor=lambda *_:{"status":"OBSERVED"})
        self.assertTrue(first["dispatched"])
        raw=json.loads(self.manifest.read_text(encoding="utf-8"))
        raw["metadata"]="altered"
        self.manifest.write_text(json.dumps(raw),encoding="utf-8")
        next_result=route_message(ROOT,self.signal,execute=True,
                                  identity_check=lambda:True,
                                  queue_executor=lambda *_:self.fail("modified packet"))
        self.assertEqual(next_result["status"],"REASON_MANIFEST_CHANGED_RECONCILE")

    def test_dispatch_failure_stays_unknown_and_does_not_retry(self):
        self.prepared()
        calls=[]
        def broken(*_):
            calls.append("attempted")
            raise RuntimeError("synthetic provider lost")
        first=route_message(ROOT,self.signal,execute=True,
                            identity_check=lambda:True,queue_executor=broken)
        self.assertEqual(first["status"],"REASON_OUTCOME_UNKNOWN_RECONCILE")
        self.assertEqual(calls,["attempted"])
        second=route_message(ROOT,self.signal,execute=True,
                             identity_check=lambda:True,
                             queue_executor=lambda *_:self.fail("bad retry"))
        self.assertEqual(second["status"],"REASON_OUTCOME_UNKNOWN_RECONCILE")
        self.assertFalse(second["dispatched"])

    def test_burst_processes_ready_tasks_then_stops_on_idle(self):
        from reason_queue_ingress import drain_ready_messages
        incoming = iter([
            {"status":"REASON_PREPARED_QUEUE_DISPATCHED",
             "queue_id":"ready-a","message_id":"A"*26,"dispatched":True,
             "queue":{"status":"QUEUE_ITEMS_OBSERVED_GOALS_OPEN"}},
            {"status":"REASON_PRIOR_RESULT_REUSED",
             "queue_id":"ready-b","message_id":"B"*26,"dispatched":False,
             "recovered":True,"queue":{"status":"QUEUE_PARTIAL_RECOVERY_DEFERRED"}},
            {"status":"REASON_NO_MESSAGE","dispatched":False},
        ])
        calls=[]
        def fake(_repo, *, wait_seconds, execute):
            calls.append((wait_seconds,execute))
            return next(incoming)
        result=drain_ready_messages(ROOT,max_messages=8,execute=True,
                                    intake=fake)
        self.assertEqual(result["status"],"REASON_BURST_DRAINED_NO_MORE_MESSAGES")
        self.assertEqual(result["messages_observed"],2)
        self.assertEqual(result["messages_dispatched"],1)
        self.assertEqual(result["messages_recovered"],1)
        self.assertEqual(calls,[(1,True)]*3)
        self.assertFalse(result["resident_service"])

    def test_burst_no_busy_loop_when_nothing_queued(self):
        from reason_queue_ingress import drain_ready_messages
        calls=[]
        def empty(_repo, **_):
            calls.append(1)
            return {"status":"REASON_NO_MESSAGE"}
        result=drain_ready_messages(ROOT,max_messages=8,intake=empty)
        self.assertEqual(result["messages_observed"],0)
        self.assertEqual(result["status"],"REASON_BURST_DRAINED_NO_MORE_MESSAGES")
        self.assertEqual(calls,[1])

    def test_burst_bounded_limit_is_exact(self):
        from reason_queue_ingress import drain_ready_messages
        calls=[]
        def forever(_repo, **_):
            calls.append(1)
            return {"status":"REASON_SIGNAL_UNTRUSTED","dispatched":False}
        result=drain_ready_messages(ROOT,max_messages=3,intake=forever)
        self.assertEqual(result["messages_observed"],3)
        self.assertEqual(result["status"],"REASON_BURST_LIMIT_REACHED")
        self.assertEqual(len(calls),3)

    def test_burst_invalid_limit_does_not_call_provider(self):
        from reason_queue_ingress import drain_ready_messages
        for n in (0,9,True,-1,1.2):
            result=drain_ready_messages(
                ROOT,max_messages=n,
                intake=lambda *_a,**_k:self.fail("must not poll"))
            self.assertEqual(result["status"],"REASON_BURST_INVALID_LIMIT")

    def test_burst_transport_failure_stops_once_without_busy_loop(self):
        from reason_queue_ingress import drain_ready_messages
        calls=[]
        def down(*_a,**_k):
            calls.append(1)
            return {"status":"REASON_IDENTITY_UNVERIFIED"}
        result=drain_ready_messages(ROOT,max_messages=6,intake=down)
        self.assertEqual(result["status"],"REASON_BURST_TRANSPORT_UNAVAILABLE")
        self.assertEqual(calls,[1])

    def test_snapshot_revalidated_after_manifest_mutates(self):
        self.prepared()
        from unittest.mock import patch
        import reason_queue_ingress as bridge
        original=bridge.run_bounded_goal_queue
        calls=[]
        def mutate_between_checks(path, repo, *,validate_only=False, **extra):
            calls.append(str(path))
            result=original(path,repo,validate_only=validate_only,**extra)
            if len(calls)==1:
                doc=json.loads(self.manifest.read_text(encoding="utf-8"))
                doc["items"][0]["command"]="arbitrary external instruction"
                self.manifest.write_text(json.dumps(doc),encoding="utf-8")
            return result
        with patch.object(bridge,"run_bounded_goal_queue",
                          side_effect=mutate_between_checks):
            out=route_message(ROOT,self.signal,execute=True,
                              identity_check=lambda:True,
                              queue_executor=lambda *_:self.fail("unsafe snapshot launched"))
        self.assertEqual(out["status"],"REASON_MANIFEST_SNAPSHOT_INVALID")
        self.assertEqual(len(calls),2)

    def test_nonzero_listener_is_transport_error_not_idle(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/"reason-network.exe"
            exe.write_bytes(b"synthetic")
            class Bad:
                returncode=2
                stdout=""
            with patch("reason_queue_ingress.reason_binary",return_value=exe):
                out=receive_once(ROOT,wait_seconds=1,
                                 runner=lambda *_a,**_k:Bad(),
                                 identity_check=lambda:True)
            self.assertEqual(out["status"],"REASON_LISTEN_UNAVAILABLE")

    def test_listener_no_message_banner_is_idle(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/"reason-network.exe"
            exe.write_bytes(b"synthetic")
            class Idle:
                returncode=0
                stdout="No messages in 1s"
            with patch("reason_queue_ingress.reason_binary",return_value=exe):
                out=receive_once(ROOT,wait_seconds=1,
                                 runner=lambda *_a,**_k:Idle(),
                                 identity_check=lambda:True)
            self.assertEqual(out["status"],"REASON_NO_MESSAGE")

    def test_unexpected_worker_exception_keeps_unknown_without_repeat(self):
        self.prepared()
        def broken(_a,_b):
            raise KeyError("missing execution evidence")
        first=route_message(ROOT,self.signal,execute=True,
                            identity_check=lambda:True,queue_executor=broken)
        self.assertEqual(first["status"],"REASON_OUTCOME_UNKNOWN_RECONCILE")
        self.assertEqual(first["error_class"],"KeyError")
        again=route_message(ROOT,self.signal,execute=True,
                            identity_check=lambda:True,
                            queue_executor=lambda *_:self.fail("duplicate run"))
        self.assertEqual(again["status"],"REASON_OUTCOME_UNKNOWN_RECONCILE")
        self.assertFalse(again["dispatched"])

    def test_queue_handler_reuses_existing_validation(self):
        # This is intentionally invalid: the entrypoint must not invent a
        # runnable workflow from arbitrary incoming text.
        self.manifest.write_text(json.dumps({
            "schema": "TAKY_GOAL_QUEUE_V1",
            "queue_id": self.queue_id, "items": []}),encoding="utf-8")
        state=run_bounded_goal_queue(self.manifest,ROOT,validate_only=True)
        self.assertEqual(state["status"],"QUEUE_SCHEMA_INVALID")
        invalid=route_message(ROOT,self.signal,execute=True,
                              identity_check=lambda:True,
                              queue_executor=lambda *_:self.fail("invalid input invoked"))
        self.assertEqual(invalid["status"],"REASON_PREPARED_MANIFEST_INVALID")


if __name__ == "__main__":
    unittest.main()
