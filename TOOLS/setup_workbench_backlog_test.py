"""Canonical WORK_ID intake must precede source implementation and DONE."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL=Path(__file__).with_name("setup_workbench_backlog.py")
CANONICAL=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\70_EXECUTION_QUEUE\TASK_REGISTER.json")
TITLE="TAKY Work ID before code and independent result verification"
KEY="CHAT-20261026:INTAKE-TEST"


class WorkIdAtIntakeTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory(prefix="TAKY_WORK_INTAKE_")
        self.addCleanup(self.dir.cleanup)
        self.board=Path(self.dir.name)/"TASK_REGISTER.json"
        shutil.copyfile(CANONICAL,self.board)
        self.original=json.loads(self.board.read_text(encoding="utf-8-sig"))
        self.canonical_sha=hashlib.sha256(CANONICAL.read_bytes()).hexdigest()

    def run_intake(self,*extra,ok=True):
        command=[sys.executable,"-B",str(TOOL),"--intake","--project","TAKY",
                 "--title",TITLE,"--category","INTEGRATION",
                 "--request-key",KEY,"--test-task-register",str(self.board),*extra]
        result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              text=True,encoding="utf-8",errors="replace",timeout=18)
        if ok:
            self.assertEqual(result.returncode,0,result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode,0)
        return result.stderr

    def test_first_request_registers_work_before_implementation_or_review(self):
        result=self.run_intake()
        self.assertEqual(result["status"],"WORK_ID_ASSIGNED_AT_INTAKE")
        prior=[x.get("id") for x in self.original["tasks"]]
        nums=[int(x[5:]) for x in prior if isinstance(x,str) and
              re.fullmatch(r"TAKY-[0-9]{3,6}",x)]
        self.assertEqual(result["work_id"],"TAKY-"+str(max(nums,default=0)+1).zfill(3))
        self.assertNotIn(result["work_id"],prior)
        self.assertEqual(result["task_state"],"DISCOVERY")
        self.assertFalse(result["implementation_verified"])
        self.assertFalse(result["model_called"])
        self.assertFalse(result["done_issued"])
        data=json.loads(self.board.read_text(encoding="utf-8-sig"))
        self.assertEqual(len(data["tasks"]),len(self.original["tasks"])+1)
        row=data["tasks"][-1]
        self.assertEqual(row["status"],"DISCOVERY")
        self.assertEqual(row["evidence"],[])
        self.assertEqual(row["planned_source_bindings"],[])
        self.assertEqual(row["owner"],"TAKY_ORCHESTRATOR")
        self.assertEqual(hashlib.sha256(CANONICAL.read_bytes()).hexdigest(),
                         self.canonical_sha)

    def test_same_request_reuses_work_id_without_new_task_or_qa(self):
        first=self.run_intake()
        before=self.board.read_bytes()
        second=self.run_intake()
        self.assertEqual(second["status"],"EXISTING_WORK_ID_REUSED")
        self.assertEqual(second["work_id"],first["work_id"])
        self.assertEqual(self.board.read_bytes(),before)

    def test_existing_legacy_task_id_reused_without_needing_done(self):
        selected=self.run_intake("--existing-id","INT-001")
        self.assertEqual(selected["work_id"],"INT-001")
        self.assertEqual(selected["status"],"EXISTING_WORK_ID_REUSED")
        self.assertFalse(selected["done_issued"])
        self.assertEqual(len(json.loads(self.board.read_text(encoding="utf-8-sig"))["tasks"]),
                         len(self.original["tasks"]))

    def test_source_bound_after_id_without_marking_implementation_complete(self):
        first=self.run_intake()
        added=self.run_intake("--source","TOOLS/setup_workbench_backlog.py")
        self.assertEqual(added["work_id"],first["work_id"])
        self.assertEqual(added["planned_source_bindings"],1)
        work=json.loads(self.board.read_text(encoding="utf-8-sig"))["tasks"][-1]
        item=work["planned_source_bindings"][0]
        self.assertTrue(Path(item["path"]).is_file())
        self.assertEqual(item["sha256"],hashlib.sha256(
                         Path(item["path"]).read_bytes()).hexdigest())
        self.assertEqual(work["status"],"DISCOVERY")
        self.assertEqual(work["evidence"],[])

    def test_related_work_receives_own_id_with_parent_not_blocking_dependency(self):
        out=self.run_intake("--parent-work-id","INT-001")
        self.assertEqual(out["status"],"WORK_ID_ASSIGNED_AT_INTAKE")
        self.assertEqual(out["parent_work_id"],"INT-001")
        row=json.loads(self.board.read_text(encoding="utf-8-sig"))["tasks"][-1]
        self.assertEqual(row["parent_work_id"],"INT-001")
        self.assertEqual(row["dependencies"],[])
        self.assertEqual(row["status"],"DISCOVERY")
        self.assertFalse(out["done_issued"])

    def test_parent_unknown_or_self_reference_rejected(self):
        self.assertIn("WORK_PARENT_ID_INVALID_OR_NOT_REGISTERED",
                      self.run_intake("--parent-work-id","UNKNOWN-888",ok=False))
        self.assertEqual(self.board.read_bytes(),CANONICAL.read_bytes())

    def test_dry_run_must_not_register(self):
        result=self.run_intake("--dry-run")
        self.assertTrue(result["dry_run"])
        self.assertEqual(self.board.read_bytes(),CANONICAL.read_bytes())

    def test_conflicting_request_key_or_path_traversal_fail_closed(self):
        self.run_intake()
        before=self.board.read_bytes()
        conflict=self.run_intake("--request-key",KEY,"--title","Another task",ok=False)
        self.assertIn("WORK_REQUEST_KEY_REUSED_FOR_DIFFERENT_TASK_HOLD",conflict)
        bad=self.run_intake("--source","../SAVEY/finance.ts",ok=False)
        self.assertIn("WORK_SOURCE_PATH_INVALID",bad)
        self.assertEqual(self.board.read_bytes(),before)

    def test_exact_existing_legacy_title_requires_explicit_reuse(self):
        title=self.original["tasks"][0]["title"]
        self.assertIn("WORK_EXISTING_TITLE_AMBIGUOUS_REUSE_EXPLICIT_ID",
                      self.run_intake("--title",title,ok=False))
        self.assertEqual(self.board.read_bytes(),CANONICAL.read_bytes())


if __name__=="__main__":
    unittest.main()
