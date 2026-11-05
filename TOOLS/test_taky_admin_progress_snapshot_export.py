import copy
import runpy
import unittest
from pathlib import Path

exporter = runpy.run_path(str(Path(__file__).with_name("TAKY_ADMIN_PROGRESS_SNAPSHOT_EXPORT.py")))
build = exporter["build"]


def fixture():
    return {
        "schema": "TAKY_CONVERSATION_PROGRESS_PROJECTION_V1",
        "safe_to_publish_to_public_app": False,
        "source_scope": {"oct_native_chat_count": 0},
        "counts": {"blocked": 1, "review": 0, "open": 0,
                   "independently_verified_completion": 0},
        "projects": [{"project": "TAKY", "registry_status": "IDLE",
                      "current_status": "IDLE", "work_count": 1,
                      "repo_evidence": {"head_date": "2026-10-17T00:00:00Z"}}],
        "work_items": [{"work_id": "W1", "project": "TAKY", "title": "Review",
                        "registry_status": "BLOCKED", "executor": "Claude",
                        "reviewer": "UNASSIGNED", "receipt_count": 4,
                        "output_refs": [],
                        "chat_source_link": "NOT_PROVEN",
                        "last_observed": "2026-10-18T00:00:00Z",
                        "receipts": [
                            {"model_called": False, "reported_status": "PREPARED_NOT_EXECUTED",
                             "source_ref": "D:/private/path"},
                            {"model_called": False, "reported_status": "LOCAL_DETERMINISTIC_CHECK"},
                            {"model_called": True, "reported_status": "CLAIMED",
                             "provider_key": "SHOULD_NOT_EXPOSE"},
                            {"reported_status": "UNKNOWN"},
                        ]}],
        "alerts": [],
    }


class AdminExporterTests(unittest.TestCase):
    def test_receipts_are_evidence_categories_not_completion(self):
        actual = build(fixture())
        x = actual["work"][0]
        self.assertEqual((x["preparedCount"], x["noModelCount"],
                          x["callClaimCount"], x["unclassifiedReceiptCount"]), (1, 1, 1, 1))
        self.assertEqual(x["receiptCount"], 4)
        self.assertFalse(x["verified"])
        self.assertFalse(x["chatLinked"])
        self.assertEqual(actual["counts"]["verified"], 0)
        self.assertEqual(actual["projects"][0]["registered"], "IDLE")
        import json
        rendered = json.dumps(actual)
        self.assertNotIn("D:/private/path", rendered)
        self.assertNotIn("SHOULD_NOT_EXPOSE", rendered)
        self.assertNotIn("source_ref", rendered)

    def test_private_export_reports_local_wip_without_leaking_paths(self):
        item=fixture()
        item["projects"][0]["local_activity"]={
            "tracked_wip_observed":True,
            "tracked_changed_files":27,
            "source_path":"D:/private/local/source/never-expose",
        }
        item["projects"][0]["work_registration_gap"]=True
        output=build(item)["projects"][0]
        self.assertTrue(output["localTrackedWipObserved"])
        self.assertEqual(output["localTrackedChangedFiles"],27)
        self.assertTrue(output["workRegistrationGap"])
        self.assertEqual(output["activityEvidence"],
                         "GIT_TRACKED_WIP_ONLY_NOT_TASK_OR_DONE_PROOF")
        self.assertEqual(output["registered"],"IDLE")
        self.assertNotIn("D:/private/local/source",str(output))

    def test_explicit_current_work_stays_unregistered_and_private(self):
        item=fixture()
        item["projects"][0]["current_work_link"]={
            "id":"MCP-REA-20261016",
            "registration":"CURRENT_DECLARED_UNREGISTERED",
            "pending_gate_count":7,
            "source_ref":"D:/#. BACKUP/protected-not-to-share",
        }
        p=build(item)["projects"][0]
        self.assertEqual(p["currentWorkId"],"MCP-REA-20261016")
        self.assertEqual(p["currentWorkRegistration"],"CURRENT_DECLARED_UNREGISTERED")
        self.assertEqual(p["currentWorkPendingGates"],7)
        self.assertFalse(p["currentWorkVerified"])
        self.assertEqual(p["workCount"],1)
        self.assertNotIn("D:/#. BACKUP",str(p))

    def test_local_qa_receipt_projects_only_ids_not_private_reason(self):
        import json
        import tempfile
        import hashlib
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"qa.json"
            source={"contract":"TAKY_FAMILY_PERIODIC_QA_V1","mode":"quick",
               "productionVerified":False,"finishedAt":"2026-10-19T11:41:10Z",
               "statuses":{"passed":17,"failed":0,"blocked":0,"openGaps":2},
               "results":[{"state":"PASS"} for _ in range(17)],
               "gaps":[{"id":"administrator-qa-consumption","priority":"P0","area":"TAKY-MOBILE",
                        "why":"F:/PRIVATE_DO_NOT_EXPOSE"},
                       {"id":"snap-expression-validity","priority":"P0","area":"SNAP",
                        "why":"Some private detail"}],
               "secret":"DONOT_LEAK_QA_INPUT"}
            p.write_text(json.dumps(source),encoding="utf8")
            qa=exporter["read_local_qa"](p)
            self.assertEqual((qa["passed"],qa["openGaps"],qa["openP0"]),(17,2,2))
            self.assertFalse(qa["productionVerified"])
            self.assertFalse(qa["independentUserOutcomeVerified"])
            self.assertEqual(qa["sourceSha256"],hashlib.sha256(p.read_bytes()).hexdigest())
            rendered=json.dumps(build(fixture(),qa=qa))
            self.assertIn("administrator-qa-consumption",rendered)
            self.assertNotIn("PRIVATE_DO_NOT_EXPOSE",rendered)
            self.assertNotIn("DONOT_LEAK_QA_INPUT",rendered)
            source["statuses"]["openGaps"]=0
            p.write_text(json.dumps(source),encoding="utf8")
            self.assertIsNone(exporter["read_local_qa"](p))
            source["statuses"]["openGaps"]=2
            source["statuses"]["passed"]="17"
            p.write_text(json.dumps(source),encoding="utf8")
            self.assertIsNone(exporter["read_local_qa"](p))
            source["statuses"]["passed"]=17
            source["gaps"]=source["gaps"]*51
            source["statuses"]["openGaps"]=102
            p.write_text(json.dumps(source),encoding="utf8")
            self.assertIsNone(exporter["read_local_qa"](p))
            source["gaps"]=source["gaps"][:2]
            source["statuses"]["openGaps"]=2
            source["productionVerified"]=True
            p.write_text(json.dumps(source),encoding="utf8")
            self.assertIsNone(exporter["read_local_qa"](p))

    def test_free_text_with_local_path_is_redacted(self):
        item=fixture()
        item["work_items"][0]["title"]="Open D:/private/location/secret.txt then review"
        item["alerts"]=[{"type":"WARNING","reason":"F:/user/private/contract"}]
        output=build(item)
        serialized=__import__("json").dumps(output)
        self.assertIn("PRIVATE_TEXT_REDACTED",serialized)
        self.assertNotIn("D:/private/location",serialized)
        self.assertNotIn("F:/user/private",serialized)

    def test_project_current_sha_drift_does_not_validate_old_work(self):
        import hashlib
        import tempfile
        verify=exporter["current_source_verified"]
        original=verify.__globals__["ROOT"]
        with tempfile.TemporaryDirectory() as t:
            ctrl=Path(t)/"00_CONTROL"
            ctrl.mkdir()
            current=Path(t)/"10_PROJECTS"/"TAKY"/"PROJECT_CURRENT.json"
            current.parent.mkdir(parents=True)
            current.write_text('{"project":"TAKY","current_work_id":"KNOWN"}',encoding="utf8")
            manifest={"path":str(current),"sha256":hashlib.sha256(current.read_bytes()).hexdigest()}
            item=fixture()
            item["source_manifest"]=[manifest]
            item["projects"][0]["current_work_link"]={
                "id":"KNOWN","registration":"CURRENT_DECLARED_UNREGISTERED"}
            try:
                verify.__globals__["ROOT"]=ctrl
                self.assertTrue(build(item)["projects"][0]["currentWorkSourceVerified"])
                current.write_text('{"project":"TAKY","current_work_id":"DIFFERENT"}',encoding="utf8")
                stale=build(item)["projects"][0]
                self.assertFalse(stale["currentWorkSourceVerified"])
                self.assertFalse(stale["currentWorkVerified"])
                self.assertEqual(stale["currentWorkId"],"KNOWN")
            finally:
                verify.__globals__["ROOT"]=original

    def test_claim_is_not_a_runtime_attestation(self):
        item = fixture()
        item["work_items"][0]["receipts"] = [{"model_called": True, "reported_status": "PREPARED_NOT_EXECUTED"}]
        item["work_items"][0]["receipt_count"] = 1
        got = build(item)["work"][0]
        self.assertEqual(got["callClaimCount"], 1)
        self.assertEqual(got["preparedCount"], 0)
        self.assertFalse(got["verified"])

    def test_kernel_join_requires_exact_registered_task_id(self):
        attach = exporter["attach_evidence"]
        item = fixture()
        item["work_items"][0]["work_id"] = "TAKY-CHAT-job123"
        item["work_items"][0]["task_id"] = "job123"
        topic = {"schema": "TAKY_CONVERSATION_2026_10_ONWARD_SOURCE_LIMITED_V1",
                 "chats": [], "topics": []}
        kernel = {
            "runtime_version": 42,
            "preflight_receipts": {
                "pf:match": {"task_id": "job123", "correction_provenance":
                             {"state": "TRUSTED_LOCAL_ROUTE_RECOVERY"}},
                "pf:near": {"task_id": "job123-extra"},
            },
            "execution_calls": {
                "pf:match": {"actual_calls": 1, "status": "RETURNED",
                             "result": {"stdout": "SENSITIVE_BLOB"}},
                "pf:near": {"actual_calls": 1, "status": "OUTCOME_UNKNOWN"},
            },
            "done_gate_receipts": {"not-related": {"status": "DONE"}}
        }
        result = attach(build(item), item, topic, kernel,
                        topic_digest="a" * 64, kernel_digest="b" * 64)
        self.assertEqual(result["lineage"]["exactWorkKernelLinks"], 1)
        self.assertEqual(result["work"][0]["kernelExact"]["preflightCount"], 1)
        self.assertEqual(result["work"][0]["kernelExact"]["invokedCount"], 1)
        self.assertEqual(result["work"][0]["kernelExact"]["routeRecoveryCount"], 1)
        self.assertEqual(result["kernel"]["returnedReceipts"], 1)
        self.assertEqual(result["kernel"]["outcomeUnknownReceipts"], 1)
        self.assertEqual(result["kernel"]["doneGateRecords"], 1)
        self.assertFalse(result["work"][0]["verified"])
        self.assertNotIn("SENSITIVE_BLOB", __import__("json").dumps(result))
        item["work_items"][0]["task_id"] = "other-job"
        blocked = attach(build(item), item, topic, kernel)
        self.assertEqual(blocked["lineage"]["exactWorkKernelLinks"], 0)
        self.assertEqual(blocked["work"][0]["kernelExact"]["relation"],
                         "NO_EXACT_TASK_ID_MATCH")

    def test_three_way_signed_routed_receipt_and_tamper_hold(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import json
        verifier = exporter["_verified_routed_receipt_id"]
        task = "a" * 32
        signed = "pf:external-review-" + task + ":" + "b" * 16
        routed = {
            "task_id": task, "work_id": "TAKY-CHAT-" + task,
            "executor": "Codex",
            "signed_readback_state": "CLI_RETURNED_UNVERIFIED",
            "taky2_signed_receipt_id": signed,
            "taky2_receipt_id": signed, "result": "MODEL_RAW_SECRET_DO_NOT_PROJECT",
        }
        kernel = {
            "preflight_receipts": {signed: {
                "task_id": "external-review-" + task,
                "action_id": "verify:codex-packet"
            }},
            "execution_calls": {signed: {"actual_calls": 1, "status": "RETURNED"}},
        }
        with TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / ("TAKY_ROUTED_" + task + ".json")
            file.write_text(json.dumps(routed), encoding="utf-8")
            work = {"work_id": "TAKY-CHAT-" + task, "task_id": task,
                    "executor": "Codex", "output_refs": [{
                        "path": str(file), "exists": True, "size": file.stat().st_size
                    }]}
            with patch.dict(verifier.__globals__, {"ROUTED_HISTORY": root}):
                self.assertEqual(verifier(work, kernel), signed)
                self.assertNotIn("MODEL_RAW_SECRET_DO_NOT_PROJECT", str(
                    exporter["attach_evidence"](
                        exporter["build"]({**fixture(), "work_items": [{
                            **fixture()["work_items"][0],
                            **work,
                        }]}),
                        {**fixture(), "work_items": [{
                            **fixture()["work_items"][0], **work
                        }]},
                        {"schema": "TAKY_CONVERSATION_2026_10_ONWARD_SOURCE_LIMITED_V1",
                         "chats": [], "topics": []},
                        {**kernel, "done_gate_receipts": {}}
                    )))
                self.assertIsNone(verifier({**work, "executor": "Claude"}, kernel))
                self.assertIsNone(verifier({**work, "work_id": "TAKY-CHAT-" + "c"*32}, kernel))
                self.assertIsNone(verifier({**work, "output_refs": []}, kernel))
                corrupt = {**kernel, "preflight_receipts": {signed: {
                    "task_id": "external-review-" + "c"*32,
                    "action_id": "verify:codex-packet"
                }}}
                self.assertIsNone(verifier(work, corrupt))
                routed["work_id"] = "TAKY-CHAT-" + "c"*32
                file.write_text(json.dumps(routed), encoding="utf-8")
                work["output_refs"][0]["size"] = file.stat().st_size
                self.assertIsNone(verifier(work, kernel))

    def test_unbound_execution_class_and_provenance(self):
        attach=exporter["attach_evidence"]
        item=fixture()
        task="c"*32
        row=item["work_items"][0]
        row.update(work_id="TAKY-CHAT-"+task,task_id=task,registry_status="OPEN",
                   receipts=[{"reported_status":"PREPARED_NOT_EXECUTED","model_called":False},
                             {"reported_status":"PREVIEW_ONLY_NOT_EXECUTED","model_called":False}],
                   receipt_count=2,output_refs=[])
        topic={"schema":"TAKY_CONVERSATION_2026_10_ONWARD_SOURCE_LIMITED_V1",
               "chats":[],"topics":[], "source_coverage":"ONLY_AUTHENTICATED_NATIVE_EXPORT_FILES_IN_LOCAL_INBOX",
               "original_export_sources":[{"state":"SOURCE_PARSED"}]}
        kernel={"preflight_receipts":{},"execution_calls":{},"done_gate_receipts":{}}
        snapshot=attach(build(item),item,topic,kernel)
        self.assertEqual(snapshot["work"][0]["executionGap"],"PREPARATION_PREVIEW_ONLY_OBSERVED")
        self.assertEqual(snapshot["lineage"]["workItemsWithNativeTopicReference"],0)
        self.assertFalse(snapshot["work"][0]["chatLinked"])
        # A forged topic link with no native messages cannot create a chat connection.
        topic["topics"]=[{"topic_id":"TOPIC-test","chat_ids":["CHAT-test"],
                          "work_ids":[row["work_id"]],
                          "ai_work_links":[{"work_id":row["work_id"],"binding":"EXPLICIT_ID_MATCH"}]}]
        snapshot=attach(build(item),item,topic,kernel)
        self.assertFalse(snapshot["work"][0]["chatLinked"])
        topic["chats"]=[{"chat_id":"CHAT-test","topic_ids":["TOPIC-test"],"links":[]}]
        snapshot=attach(build(item),item,topic,kernel)
        self.assertFalse(snapshot["work"][0]["chatLinked"],"topic-only link is not a message proof")
        topic["chats"][0]["links"]=[{"event_id":"MESSAGE-test","topic_ids":["TOPIC-test"],
                                     "work_ids":[row["work_id"]]}]
        snapshot=attach(build(item),item,topic,kernel)
        self.assertTrue(snapshot["work"][0]["chatLinked"])
        self.assertEqual(snapshot["work"][0]["nativeTopicMatches"],1)
        self.assertEqual(snapshot["lineage"]["workItemsWithNativeTopicReference"],1)
        row["registry_status"]="BLOCKED"
        row["receipts"]=[{"reported_status":"FAILED"}]
        row["output_refs"]=[{"path":"NOT_DISCLOSED","exists":True}]
        snapshot=attach(build(item),item,topic,kernel)
        self.assertEqual(snapshot["work"][0]["executionGap"],
                         "FAILURE_RECORDED_BUT_SIGNED_EXECUTION_LINK_MISSING")
        self.assertFalse(snapshot["work"][0]["verified"])
        self.assertNotIn("NOT_DISCLOSED",__import__("json").dumps(snapshot))

    def test_prepared_source_pin_drift_blocks_old_task_reuse(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from types import SimpleNamespace
        import hashlib
        import json
        checker = exporter["_prepared_source_pin_state"]
        task_id = "d" * 32
        with TemporaryDirectory() as root_dir:
            repo = Path(root_dir) / "TAKY"
            inbox = Path(root_dir) / "AI_TASKS"
            source = repo / "TOOLS" / "unit.py"
            source.parent.mkdir(parents=True)
            inbox.mkdir()
            source.write_text("original = 1\n", encoding="utf-8")
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            work = {"task_id": task_id, "work_id": "TAKY-CHAT-" + task_id,
                    "input_refs": [{"path": str(inbox / (task_id + ".json")),
                                    "exists": True}]}
            task = {"id": task_id, "mode": "BOUNDED_EDIT_PROPOSAL",
                    "repo": str(repo), "head": "h" * 40,
                    "allowed_files": [{"path": "TOOLS/unit.py", "sha256": sha}]}
            prepared = inbox / (task_id + ".json")
            prepared.write_text(json.dumps(task), encoding="utf-8")
            with patch.dict(checker.__globals__, {
                    "PREPARED_TASK_INBOX": inbox, "TAKY_CODE_REPO": repo}), patch(
                    "subprocess.run", return_value=SimpleNamespace(
                        returncode=0, stdout="h" * 40)):
                self.assertEqual(checker(work), "SOURCE_PIN_MATCH_NOT_EXECUTION_AUTHORIZATION")
                source.write_text("modified = 2\n", encoding="utf-8")
                self.assertEqual(checker(work), "PREPARED_SOURCE_SHA_DRIFT_HOLD")
                task["head"] = "z" * 40
                prepared.write_text(json.dumps(task), encoding="utf-8")
                self.assertEqual(checker(work), "PREPARED_SOURCE_AND_HEAD_DRIFT_HOLD")
                work["input_refs"] = []
                self.assertEqual(checker(work), "PREPARED_TASK_NOT_IN_REGISTERED_INPUTS")
                work["input_refs"] = [{"path": str(prepared), "exists": True}]
                task["allowed_files"][0]["path"] = "../outside.py"
                prepared.write_text(json.dumps(task), encoding="utf-8")
                self.assertEqual(checker(work), "SOURCE_PIN_SCOPE_INVALID")

    def test_topic_and_kernel_source_validation(self):
        attach = exporter["attach_evidence"]
        item = fixture()
        with self.assertRaisesRegex(ValueError,"INVALID_TOPIC_SOURCE"):
            attach(build(item), item, {"schema": "FAKE"}, {})
        topic = {"schema":"TAKY_CONVERSATION_2026_10_ONWARD_SOURCE_LIMITED_V1",
                 "chats":[],"topics":[]}
        with self.assertRaisesRegex(ValueError,"INVALID_KERNEL_COLLECTION"):
            attach(build(item),item,topic,{"preflight_receipts":[]})

    def test_bad_source_authority_and_receipt_type_hold(self):
        item = fixture()
        item["safe_to_publish_to_public_app"] = True
        with self.assertRaises(ValueError):
            build(item)
        item = fixture()
        item["work_items"][0]["receipts"] = {"not": "list"}
        with self.assertRaises(ValueError):
            build(item)


if __name__ == "__main__":
    unittest.main()
