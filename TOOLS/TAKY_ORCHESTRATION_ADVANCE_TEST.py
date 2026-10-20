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
