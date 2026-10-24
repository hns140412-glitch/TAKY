#!/usr/bin/env python3
"""Proof that portfolio routing continues valid local work without redundant calls."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import TAKY_ORCHESTRATION_ADVANCE as a

def sample_board(**overrides):
    target={"id":"CLN-009","title":"Audit local toolchain paths",
            "category":"POST_CLEANUP","status":"IMPLEMENTING","priority":"P1",
            "approval_required":False,"dependencies":["CLN-003"]}
    target.update(overrides)
    return {"tasks":[{"id":"CLN-003","status":"VERIFIED","title":"Worktree original audit"},
                     target,
                     {"id":"INT-002","status":"IMPLEMENTING","title":"UI visual approval",
                      "dependencies":["CLN-003"],"priority":"P0"},
                     {"id":"UPD-004","status":"NOT_STARTED","title":"Remote updater",
                      "approval_required":True,"dependencies":["CLN-003"],"priority":"P0"}]}

class LocalAdvanceTests(unittest.TestCase):

    def test_dependency_wake_and_plain_continuation_share_claim(self):
        from taky_registered_goal_queue import registered_dependency_revision
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            upstream=root/"upstream.json"
            upstream.write_text('{"verified":"registered"}',encoding="utf-8")
            rows=[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(upstream)]},
                {"id":"CLN-009","status":"IMPLEMENTING","approval_required":False,
                 "dependencies":["CLN-003"],"title":"Bounded local audit"},
            ]
            board=root/"board.json"
            board.write_text(json.dumps({"tasks":rows}),encoding="utf-8")
            revision=registered_dependency_revision(
                ["CLN-003"],{x["id"]:x for x in rows},root)
            calls=[]
            def audit(*_args):
                calls.append(1)
                return [{"name":"LOCAL_SAFE_CHECK","status":"PASS"}]
            with patch.object(a,"run_path_and_toolchain_checks",side_effect=audit):
                first=a.run_checks("CLN-009",board,root,
                                   dependency_revision=revision)
                with self.assertRaisesRegex(
                      ValueError,"CANONICAL_WORK_ALREADY_CLAIMED_NO_RETRY"):
                    a.run_checks("CLN-009",board,root)
            self.assertEqual(calls,[1])
            self.assertFalse(json.loads(
                Path(first["evidence"]).read_text(encoding="utf-8")
            )["portfolio_done"])

    def test_corrupt_one_local_receipt_does_not_block_other_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            evidence=root/"evidence"
            evidence.mkdir()
            rows={"tasks":[
                {"id":"CLN-009","status":"IMPLEMENTING",
                 "approval_required":False,"dependencies":[],
                 "title":"Local path verification"},
                {"id":"MCP-001","status":"IMPLEMENTING",
                 "approval_required":False,"dependencies":[],
                 "title":"Local MCP inventory"},
            ]}
            bad=evidence/"TAKY_LOCAL_WORK_CLN-009_fixed.json"
            bad.write_text("{broken-json",encoding="utf-8")
            with patch.object(a,"evidence_signature",
                     side_effect=lambda _board,work:(
                         {"work_id":work},"fixed" if work=="CLN-009" else "other")):
                decided=a.choose(rows,evidence)
            index={x["task_id"]:x for x in decided["considered"]}
            self.assertEqual(index["CLN-009"]["route"],
                             "LOCAL_EVIDENCE_INTEGRITY_HOLD")
            self.assertEqual(index["MCP-001"]["route"],
                             "READY_FOR_LOCAL_EXECUTION")
            self.assertEqual(decided["selected"]["task_id"],"MCP-001")

    def test_registered_worker_does_not_rerun_after_missing_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            proof=root/"parent.json"
            proof.write_text("source",encoding="utf-8")
            board={"tasks":[
                {"id":"CLN-003","status":"VERIFIED","evidence":[str(proof)]},
                {"id":"CLN-009","status":"IMPLEMENTING","approval_required":False,
                 "dependencies":["CLN-003"],"title":"Local checks"}]}
            source=root/"board.json"
            source.write_text(json.dumps(board),encoding="utf-8")
            calls=[]
            def broken(*_args):
                calls.append(1)
                raise ValueError("CHECK_DID_NOT_RETURN")
            with patch.object(a,"run_path_and_toolchain_checks",side_effect=broken):
                with self.assertRaisesRegex(ValueError,"CHECK_DID_NOT_RETURN"):
                    a.run_checks("CLN-009",source,root)
                with self.assertRaisesRegex(ValueError,"CANONICAL_WORK_ALREADY_CLAIMED"):
                    a.run_checks("CLN-009",source,root)
            self.assertEqual(calls,[1])
            self.assertEqual(len(list((root/".local").glob(
                "taky-canonical-worker-CLN-009-*.json"))),1)

    def test_parent_dependency_revision_change_mid_probe_never_publishes(self):
        from taky_registered_goal_queue import registered_dependency_revision
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            proof=root/"upstream.json"
            proof.write_text('{"source":"before"}',encoding="utf-8")
            child={"id":"CLN-009","title":"Safe local toolchain audit",
                   "category":"POST_CLEANUP","status":"IMPLEMENTING",
                   "priority":"P1","approval_required":False,
                   "dependencies":["CLN-003"]}
            upstream={"id":"CLN-003","status":"VERIFIED",
                      "evidence":[str(proof)]}
            board={"tasks":[upstream,child]}
            board_file=root/"board.json"
            board_file.write_text(json.dumps(board),encoding="utf-8")
            expected=registered_dependency_revision(["CLN-003"],
                            {"CLN-003":upstream,"CLN-009":child},root)
            def worker(*_args):
                proof.write_text('{"source":"changed while worker running"}',
                                 encoding="utf-8")
                return [{"name":"PATH_CHECK","status":"PASS"}]
            evidence_files=lambda:list(root.glob("TAKY_LOCAL_WORK_CLN-009_*.json"))
            with patch.object(a,"run_path_and_toolchain_checks",side_effect=worker), \
                 patch.object(a,"evidence_signature",
                              return_value=({"canonical":"test"},"sourcerev")):
                with self.assertRaisesRegex(
                        ValueError,"REGISTERED_DEPENDENCY_CHANGED_DURING_AUDIT"):
                    a.run_checks("CLN-009",board_file,root,
                                 dependency_revision=expected)
            self.assertEqual(evidence_files(),[])

    def test_approval_revocation_during_worker_blocks_receipt_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            task={"id":"OPS-001","title":"Source evidence observation",
                  "category":"TOOLS","status":"IMPLEMENTING",
                  "priority":"P0","approval_required":False,
                  "dependencies":["CLN-001"]}
            board_path=root/"board.json"
            board={"tasks":[{"id":"CLN-001","status":"IMPLEMENTING",
                             "title":"Unfinished cleanup"},task]}
            board_path.write_text(json.dumps(board),encoding="utf-8")
            calls=[]
            def worker(_timeout):
                calls.append("worker")
                changed=json.loads(board_path.read_text(encoding="utf-8"))
                changed["tasks"][1]["approval_required"]=True
                board_path.write_text(json.dumps(changed),encoding="utf-8")
                return [{"name":"SOURCE_OBSERVATION","status":"PASS",
                         "next_action":"REVIEW_PENDING"}]
            with patch.object(a,"ALL_READONLY_WORKERS",{"OPS-001":worker}), \
                 patch.object(a,"evidence_signature",
                              return_value=({"task_contract":"fixed"},"revocation")):
                with self.assertRaisesRegex(
                    ValueError, "TASK_ADMISSION_REVOKED_DURING_AUDIT"
                ):
                    a.run_checks("OPS-001",board_path,root/"evidence")
            self.assertEqual(calls,["worker"])
            self.assertFalse((root/"evidence").exists())
            self.assertTrue(json.loads(board_path.read_text())["tasks"][1]["approval_required"])

    def test_pending_dependencies_survive_in_source_evidence_not_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            task={"id":"OPS-001","title":"Original source evidence",
                  "category":"TOOLS","status":"IMPLEMENTING",
                  "priority":"P0","approval_required":False,
                  "dependencies":["CLN-001"]}
            board={"tasks":[{"id":"CLN-001","status":"IMPLEMENTING",
                             "title":"Unfinished inventory"},task]}
            board_path=root/"board.json"
            board_path.write_text(json.dumps(board),encoding="utf-8")
            with patch.object(a,"ALL_READONLY_WORKERS",{
                "OPS-001":lambda _: [
                    {"name":"SOURCE_SCOPE","status":"PASS",
                     "next_action":"INDEPENDENT_REVIEW_REQUIRED"}]
            }),patch.object(a,"evidence_signature",
                            return_value=({"task":"fixed"},"preserve-deps")):
                actual=a.run_checks("OPS-001",board_path,root/"proof")
            saved=json.loads(Path(actual["evidence"]).read_text(encoding="utf-8"))
            self.assertEqual(saved["pending_dependencies_at_execution"],["CLN-001"])
            self.assertIn("INDEPENDENT_REVIEW_REQUIRED",saved["remaining_work"])
            self.assertFalse(saved["work_owner_claimed_by_this_receipt"])
            self.assertFalse(saved["portfolio_done"])

    def test_existing_family_and_original_source_evidence_are_safely_routed(self):
        board = sample_board()
        board["tasks"].extend([
            {"id": "FAMILY-DURABLE-001", "title": "Family durable learning evidence",
             "category": "FAMILY", "status": "IMPLEMENTING", "priority": "P0",
             "approval_required": False, "dependencies": ["External family data permission"]},
            {"id": "OPS-001", "title": "Local collector source review evidence",
             "category": "TOOLS", "status": "IMPLEMENTING", "priority": "P0",
             "approval_required": False, "dependencies": ["CLN-001"]},
            {"id": "INT-003", "title": "Audio voice approvals",
             "category": "INTEGRATION", "status": "IMPLEMENTING", "priority": "P0",
             "approval_required": False, "dependencies": []},
        ])
        states = {task["id"]: task["status"] for task in board["tasks"]}
        family_route, family_dependencies = a.decision(board["tasks"][-3], states)
        source_route, source_dependencies = a.decision(board["tasks"][-2], states)
        voice_route, _ = a.decision(board["tasks"][-1], states)
        self.assertEqual(family_route, "READY_FOR_LOCAL_EXECUTION")
        self.assertEqual(family_dependencies, ["External family data permission"])
        self.assertEqual(source_route, "READY_FOR_LOCAL_EXECUTION")
        self.assertEqual(source_dependencies, ["CLN-001"])
        self.assertEqual(voice_route, "USER_HOLD_UI_AUDIO_ARCHI_FAMILY")
        board["tasks"][-3]["approval_required"] = True
        self.assertEqual(a.decision(board["tasks"][-3], states)[0], "REQUIRES_APPROVAL")
        self.assertFalse(a.continue_local.__doc__ is None)

    def test_outcome_slice_receipts_never_promote_parent_tasks(self):
        from TAKY_ORCHESTRATION_OUTCOME_WORKERS import OUTCOME_READONLY_WORKERS
        self.assertEqual(
            set(OUTCOME_READONLY_WORKERS), {"CLN-002","INT-001","FAMILY-DURABLE-001","OPS-001"})
        from unittest.mock import patch
        with patch.object(a, "ALL_READONLY_WORKERS",
                          {"OPS-001": lambda _timeout: [{
                              "name": "ORIGINAL_SOURCE_TO_CONSUMER_EVIDENCE",
                              "status": "HOLD", "learning_consumed": False}] }):
            with tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp)
                task={"id":"OPS-001", "title":"Source observation",
                      "category":"TOOLS", "status":"IMPLEMENTING",
                      "priority":"P0", "approval_required":False,
                      "dependencies":["CLN-001"]}
                board={"tasks":[{"id":"CLN-001","status":"IMPLEMENTING",
                                 "title":"Unfinished cleanup"},task]}
                path=base/"register.json"
                path.write_text(json.dumps(board))
                with patch.object(a, "evidence_signature",
                                  return_value=({"task_sha256":"fixture"},"fixture")):
                    result=a.run_checks("OPS-001",path,base/"proof")
                self.assertEqual(result["status"],"LOCAL_SLICE_FINDINGS_NEED_ACTION")
                self.assertEqual(json.loads(path.read_text())["tasks"][1]["status"],"IMPLEMENTING")
                recorded=json.loads(Path(result["evidence"]).read_text())
                self.assertFalse(recorded["portfolio_done"])
                self.assertFalse(recorded["checks"][0]["learning_consumed"])



    def test_one_unavailable_source_proof_does_not_block_independent_task(self):
        board={"tasks":[
            {"id":"OPS-001","status":"IMPLEMENTING",
             "title":"Original source evidence","priority":"P0",
             "category":"TOOLS","approval_required":False,
             "dependencies":["CLN-001"]},
            {"id":"FAMILY-DURABLE-001","status":"IMPLEMENTING",
             "title":"Family local evidence","priority":"P0",
             "category":"FAMILY","approval_required":False,
             "dependencies":["External family approval"]},
        ]}
        def observed_signature(_board,work):
            if work=="OPS-001":
                raise ValueError("SOURCE_PROVENANCE_TARGET_UNSAFE")
            return {"source":"safe"},"fixture"
        with tempfile.TemporaryDirectory() as temp, patch.object(
                a,"evidence_signature",side_effect=observed_signature):
            result=a.choose(board,Path(temp))
        self.assertEqual(result["eligible_count"],1)
        self.assertEqual(result["selected"]["task_id"],"FAMILY-DURABLE-001")
        broken=next(x for x in result["considered"] if x["task_id"]=="OPS-001")
        self.assertEqual(broken["route"],"LOCAL_INPUT_PROVENANCE_HOLD")
        self.assertEqual(broken["input_error_type"],"ValueError")

    def test_local_product_cache_invalidated_by_actual_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            repo=base/"TAKY"
            repo.mkdir()
            workbench=base/"TAKY_AI_WORKBENCH"
            evidence=workbench/"01_BACKLOG_AND_ADOPTION/80_EVIDENCE"
            evidence.mkdir(parents=True)
            entrypoints=(
                "TAKY-MOBILE/index.html", "Ready & Set/index.html",
                "Hide & Seek/index.html", "Snap & Pop/index.html",
                "Play Camp/src/App.tsx", "Play Camp/src/main.tsx",
                "Play Camp/src/lib/readyBridge.ts",
            )
            manifest=[]
            for name in entrypoints:
                target=base/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(b"original_entrypoint")
                manifest.append({"path":str(target).replace("\\","/")})
            refs={
                "result_ref":"TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/approval-hold-result.json",
                "screenshot_ref":"TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/05-play-camp.png",
                "ready_partial_screenshot_ref":"TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/06-ready-approval-hold-result.png",
                "mobile_partial_screenshot_ref":"TAKY-MOBILE/artifacts/learning-loop-multi-specialist-roundtrip-20261010/07-mobile-approval-hold-return.png",
                "test_source_ref":"TAKY-MOBILE/tests/learning-loop-multi-specialist-roundtrip-e2e.cjs",
                "audio_authority_ref":"Play Camp/src/data/playCampPronunciationAssets.ts",
            }
            payload={"browser_journey":{"pinned_entrypoint_sources_at_local_observation":manifest}}
            for key,name in refs.items():
                target=base/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(b"original_artifact")
                payload["browser_journey"][key]={"path":str(target).replace("\\","/")}
            (evidence/"PRODUCT_AND_SOURCE_OUTCOME_LOCAL_20261023.json").write_text(
                json.dumps(payload),encoding="utf-8")
            with patch.object(a,"TAKY",repo):
                before=a.live_outcome_provenance_fingerprint(
                    "FAMILY-DURABLE-001",workbench)
                (base/"Play Camp/src/lib/readyBridge.ts").write_bytes(
                    b"new_code_without_changing_receipt")
                after=a.live_outcome_provenance_fingerprint(
                    "FAMILY-DURABLE-001",workbench)
                self.assertNotEqual(before,after)
                payload["browser_journey"]["result_ref"]["path"]=str(base/"other.txt")
                (evidence/"PRODUCT_AND_SOURCE_OUTCOME_LOCAL_20261023.json").write_text(
                    json.dumps(payload),encoding="utf-8")
                with self.assertRaisesRegex(ValueError,"PROVENANCE_PATH_NOT_PINNED"):
                    a.live_outcome_provenance_fingerprint("FAMILY-DURABLE-001",workbench)

    def test_frozen_source_cache_invalidated_by_actual_raw_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            repo=base/"TAKY"
            repo.mkdir()
            workbench=base/"TAKY_AI_WORKBENCH"
            evidence=workbench/"01_BACKLOG_AND_ADOPTION/80_EVIDENCE"
            evidence.mkdir(parents=True)
            (evidence/"PRODUCT_AND_SOURCE_OUTCOME_LOCAL_20261023.json").write_text(
                "{}",encoding="utf-8")
            vault=base/"TAKY-SOURCE-VAULT"
            paths=[
                vault/"reports/site_watch/mining_generations/gen.json",
                vault/"data/site_watch/snapshots/raw.bin",
                vault/"data/site_watch/local_content_candidates/unit.txt",
            ]
            for path in paths:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b"same_provenance")
            frozen={"mining_generation_ref":{"path":str(paths[0])},
                    "items":[{"raw_path":str(paths[1]),
                              "text_path":str(paths[2])}]}
            (evidence/"SOURCE_FIRST_FROZEN_UNITS_V2_20261023.json").write_text(
                json.dumps(frozen),encoding="utf-8")
            with patch.object(a,"TAKY",repo):
                before=a.live_outcome_provenance_fingerprint("OPS-001",workbench)
                paths[1].write_bytes(b"raw_changed_without_receipt_change")
                after=a.live_outcome_provenance_fingerprint("OPS-001",workbench)
                self.assertNotEqual(before,after)
                frozen["items"][0]["raw_path"]=str(base/"outside.bin")
                (base/"outside.bin").write_bytes(b"arbitrary_file")
                (evidence/"SOURCE_FIRST_FROZEN_UNITS_V2_20261023.json").write_text(
                    json.dumps(frozen),encoding="utf-8")
                with self.assertRaisesRegex(ValueError,"SOURCE_PROVENANCE_TARGET_UNSAFE"):
                    a.live_outcome_provenance_fingerprint("OPS-001",workbench)

    def test_select_real_dependent_work_not_ui_or_approval(self):
        plan=a.choose(sample_board())
        self.assertEqual(plan["selected"]["task_id"],"CLN-009")
        self.assertEqual(plan["eligible_count"],1)
        reasons={x["task_id"]:x["route"] for x in plan["considered"]}
        self.assertEqual(reasons["INT-002"],"USER_HOLD_UI_AUDIO_ARCHI_FAMILY")
        self.assertEqual(reasons["UPD-004"],"REQUIRES_APPROVAL")
        self.assertNotIn("MCP-002", reasons)

    def test_dependency_not_verified_refuses_execution(self):
        board=sample_board()
        board["tasks"][0]["status"]="IMPLEMENTING"
        self.assertIsNone(a.choose(board)["selected"])
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"board.json";src.write_text(json.dumps(board))
            with self.assertRaisesRegex(ValueError,"TASK_NOT_DEPENDENCY_READY"):
                a.run_checks("CLN-009",src,Path(td)/"out")

    def test_real_local_check_reuses_evidence_without_rerun(self):
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td)
            base=temp/"checks";base.mkdir()
            (base/"workspace_cleanup_path_guard.py").write_text(
                'import json\nprint(json.dumps({"status":"PASS","no_changes_made":True,"errors":[],"evidence":{"paths":3}}))\n',
                encoding="utf-8")
            (base/"taky_toolchain_paths_guard.py").write_text(
                'import json\ndef main():\n OUT.write_text(json.dumps({"schema":"TAKY_TOOLCHAIN_PATHS_GUARD_V1","read_only":True,"status":"PASS","checks":{"codex":True},"skills":[],"broken":[]}))\n',
                encoding="utf-8")
            board=temp/"board.json";board.write_text(json.dumps(sample_board()),encoding="utf-8")
            evidence=temp/"evidence"
            with patch.object(a,"GUARDS",base):
                self.assertEqual(a.choose(json.loads(board.read_text()))["eligible_count"],1)
                proof=a.run_checks("CLN-009",board,evidence)
                self.assertEqual(proof["status"],"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE")
                self.assertEqual(len(proof["checks"]),2)
                recorded=json.loads(Path(proof["evidence"]).read_text(encoding="utf-8"))
                self.assertFalse(recorded["portfolio_done"])
                self.assertEqual(len(list(evidence.glob("*.json"))),1)
                routed=a.choose(json.loads(board.read_text()),evidence)
                self.assertIsNone(routed["selected"])
                self.assertEqual(routed["eligible_count"],0)
                self.assertEqual(a.run_checks("CLN-009",board,evidence)["status"],
                                 "REUSED_EXISTING_EVIDENCE")
                self.assertEqual(len(list(evidence.glob("*.json"))),1)
                self.assertEqual(json.loads(board.read_text())["tasks"][1]["status"],"IMPLEMENTING")

    def test_safe_mcp_preflight_does_not_require_completed_cleanup(self):
        board=sample_board()
        board["tasks"].append({"id":"MCP-002","status":"IMPLEMENTING",
            "title":"Verify Remote Desktop Commander paths and CPU",
            "dependencies":["CLN-001"],"priority":"P0","approval_required":False})
        plan=a.choose(board)
        self.assertEqual(plan["selected"]["task_id"],"MCP-002")
        self.assertEqual(plan["selected"]["unresolved"],["CLN-001"])
        self.assertEqual(plan["eligible_count"],2)
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td);base=temp/"guards";base.mkdir()
            for filename in ("workspace_cleanup_path_guard.py","taky_toolchain_paths_guard.py"):
                (base/filename).write_text("# Unused in MCP scope\n",encoding="utf-8")
            (base/"taky_mcp_executable_preflight.py").write_text(
                'import json\ndef main():\n OUT.write_text(json.dumps({"schema":"TAKY_MCP_EXECUTABLE_PREFLIGHT_V1","external_call":False,"state":"REFERENCES_PRESENT","launchers":[{"program_name":"python","present":True}],"missing":[]}))\n',
                encoding="utf-8")
            board_path=temp/"board.json";board_path.write_text(json.dumps(board))
            with patch.object(a,"GUARDS",base):
                result=a.run_checks("MCP-002",board_path,temp/"evidence")
                self.assertEqual(result["status"],"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE")
                record=json.loads(Path(result["evidence"]).read_text(encoding="utf-8"))
                self.assertFalse(record["portfolio_done"])
                self.assertFalse(record["checks"][0]["protocol_handshake_verified"])
                self.assertFalse(record["checks"][0]["cpu_limits_verified"])
                next_plan=a.choose(board,temp/"evidence")
                self.assertEqual(next_plan["selected"]["task_id"],"CLN-009")

    def test_modified_task_reopens_local_evidence_scope(self):
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td); base=temp/"checks";base.mkdir()
            for name in ("workspace_cleanup_path_guard.py","taky_toolchain_paths_guard.py"):
                (base/name).write_text("# placeholder\n")
            with patch.object(a,"GUARDS",base):
                board=sample_board()
                inputs,digest=a.evidence_signature(board,"CLN-009")
                root=temp/"evidence";root.mkdir()
                old=root/("TAKY_LOCAL_WORK_CLN-009_"+digest+".json")
                old.write_text(json.dumps({"schema":"TAKY_LOCAL_WORK_SLICE_V1",
                    "task_id":"CLN-009","inputs":inputs,"state":"LOCAL_SLICE_FINDINGS_NEED_ACTION"}))
                self.assertEqual(a.choose(board,root)["eligible_count"],0)
                board["tasks"][1]["title"]="Changed local path audit requirements"
                self.assertEqual(a.choose(board,root)["eligible_count"],1)

    def test_evidence_and_resume_notes_do_not_replay_completed_local_slice(self):
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td);base=temp/"checks";base.mkdir()
            for name in ("workspace_cleanup_path_guard.py","taky_toolchain_paths_guard.py"):
                (base/name).write_text("# existing test guard\\n",encoding="utf-8")
            with patch.object(a,"GUARDS",base):
                board=sample_board()
                inputs,digest=a.evidence_signature(board,"CLN-009")
                receipt_dir=temp/"proof";receipt_dir.mkdir()
                receipt=receipt_dir/("TAKY_LOCAL_WORK_CLN-009_"+digest+".json")
                receipt.write_text(json.dumps({"schema":"TAKY_LOCAL_WORK_SLICE_V1",
                    "task_id":"CLN-009","inputs":inputs,
                    "state":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE"}),encoding="utf-8")
                target=board["tasks"][1]
                target["evidence"]=["D:/proof/new_receipt.json"]
                target["resume_checkpoint"]={"next_action":"Check owner", "global_done":False}
                self.assertEqual(a.evidence_signature(board,"CLN-009"),(inputs,digest))
                plan=a.choose(board,receipt_dir)
                row=next(v for v in plan["considered"] if v["task_id"]=="CLN-009")
                self.assertEqual(row["route"],"LOCAL_SLICE_ALREADY_EVIDENCED")
                self.assertIsNone(plan["selected"])
                target["approval_required"]=True
                self.assertNotEqual(a.evidence_signature(board,"CLN-009"),(inputs,digest))
                self.assertEqual(a.choose(board,receipt_dir)["considered"][1]["route"],"REQUIRES_APPROVAL")

if __name__=="__main__":
    unittest.main()
