"""Existing TAKY source-review console: scoped real RAW anchors and interactive Chrome smoke."""
import copy
import json
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

import central_forming_review_queue as queue
import central_full_anchor_review as full
import central_local_review_console as console
import taky_central_source_factory as factory

PROJ=queue.EVIDENCE/"SKAX_SHA_ANCHORED_EDITORIAL_PROJECTION_20261015.json"
CHROME=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

class ScopedSKAXConsole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert PROJ.is_file(), "SKAX_PROJECTION_NOT_PRESENT"
        d=json.loads(PROJ.read_text(encoding="utf-8"))
        cls.source_ids=[x["source_id"] for x in d["articles"]]
        assert len(cls.source_ids)>=8
        cls.annotations=json.loads((queue.EVIDENCE/"SKAX_APPLICATION_CANDIDATES_20261015.json").read_text(encoding="utf-8"))
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=12) as db:
            db.row_factory=sqlite3.Row
            cls.queue=queue.build_queue(db,cls.source_ids)
            cls.review=full.project(db,cls.queue)
            cls.html=console.render(cls.review,db,application_candidates=cls.annotations)

    def test_source_scope_full_detail_and_unapproved(self):
        self.assertEqual(self.review["review_ready_sources"],len(self.source_ids))
        self.assertEqual(self.review["source_count"],len(self.source_ids))
        self.assertEqual(self.review["verified_anchor_count"],34)
        self.assertFalse(self.review["forming_approved"])
        self.assertFalse(self.review["learning_consumed"])
        self.assertFalse(self.review["current_untouched"] is False)
        self.assertEqual(self.queue["missing_extract_hold_count"],0)
        self.assertIn("SK AX AI Continuity",self.html)
        self.assertIn("TAKY_LOCAL_REVIEW_UI_DATA_V1",self.html)
        self.assertIn("방식·디자인·TAKY 적용 가설",self.html)
        self.assertEqual(len(console.validated_candidates(self.review,self.annotations)),8)
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=10) as db:
            db.row_factory=sqlite3.Row
            with self.assertRaisesRegex(ValueError,"FORMING_SCOPE_SOURCE_NOT_INDEXED"):
                queue.build_queue(db,["raw:"+"f"*64])

    def test_untrusted_annotation_cannot_claim_approval_or_rebind_raw(self):
        d=copy.deepcopy(self.annotations)
        d["semantic_approved"]=True
        with self.assertRaisesRegex(ValueError,"CANDIDATE_SCOPE_OR_AUTHORITY_INVALID"):
            console.validated_candidates(self.review,d)
        d=copy.deepcopy(self.annotations)
        d["items"][0]["raw_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"CANDIDATE_RAW_OR_ANCHOR_NOT_BOUND"):
            console.validated_candidates(self.review,d)
        d=copy.deepcopy(self.annotations)
        d["full_review_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"CANDIDATE_SCOPE_OR_AUTHORITY_INVALID"):
            console.validated_candidates(self.review,d)

    def test_pc_design_candidate_is_opt_in_and_accessibility_bounded(self):
        css=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\20_DESIGN_STUDIO\UI-UX\TAKY_SOURCE_REVIEW_PC_DESIGN_CANDIDATE_V1.css").read_text(encoding="utf-8")
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=12) as db:
            db.row_factory=sqlite3.Row
            candidate=console.render(self.review,db,application_candidates=self.annotations,
                                     candidate_stylesheet=css)
            self.assertIn("CANDIDATE_NOT_APPROVED",candidate)
            self.assertIn('role="group" aria-label="원문 목록"',candidate)
            self.assertIn("b.setAttribute('aria-pressed'",candidate)
            self.assertIn("aria-label','원문 검토 메모'",candidate)
            self.assertNotIn("CANDIDATE_NOT_APPROVED",self.html)
            with self.assertRaisesRegex(ValueError,"DESIGN_CANDIDATE_CSS_INVALID"):
                console.render(self.review,db,application_candidates=self.annotations,
                               candidate_stylesheet="</style><script>invalid</script>"+"x"*90)

    def test_design_gate_blocks_visual_promotion_without_approved_mockup(self):
        import central_review_workbench_one_shot as runner
        with tempfile.TemporaryDirectory(prefix="taky_design_gate_") as temp:
            original=Path(temp)/"review.html"
            original.write_text(self.html,encoding="utf-8")
            first=runner.ui_design_gate_hold(original,Path(temp))
            self.assertEqual(first,runner.ui_design_gate_hold(original,Path(temp)))
            record=json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(record["status"],"HOLD_APPROVED_VISUAL_AND_DESIGN_CONTRACT_MISSING")
            self.assertIn("RULE_NOT_APPLIED",record["taky_gate_findings"])
            self.assertIsNone(record["design_contract_ref"])
            self.assertFalse(record["design_promotion_allowed"])
            self.assertTrue(record["local_preview_allowed"])
            original.write_text(self.html+"<!--changed-->",
                                encoding="utf-8")
            updated=runner.ui_design_gate_hold(original,Path(temp))
            self.assertNotEqual(first,updated)

    @unittest.skipUnless(CHROME.is_file(),"Chrome not present")
    def test_browser_search_select_notes_smoke(self):
        instrument=r"""<script>
        (() => {
          const q=document.getElementById('search');
          q.value='AI Continuity';
          q.dispatchEvent(new Event('input',{bubbles:true}));
          const count=document.querySelectorAll('#sourceList button.source').length;
          const detail=document.querySelectorAll('#detail .anchor').length;
          const memo=document.querySelector('#detail textarea');
          if(memo){memo.value='검토 메모 테스트';memo.dispatchEvent(new Event('input',{bubbles:true}));}
          const noted=Array.from(document.querySelectorAll('#stats .stat strong'))
            .map(e=>e.textContent.trim()).at(-1);
          document.body.dataset.takySmoke=JSON.stringify({count,detail,noted,hasMemo:!!memo});
        })();
        </script>"""
        with tempfile.TemporaryDirectory(prefix="taky_console_smoke_") as temporary:
            file=Path(temporary)/"review.html"
            file.write_text(self.html.replace("</body>",instrument+"</body>"),encoding="utf-8")
            run=subprocess.run([str(CHROME),"--headless=new","--disable-gpu",
                "--disable-extensions","--no-first-run","--no-default-browser-check",
                "--virtual-time-budget=1500","--dump-dom",file.as_uri()],
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                timeout=25,check=False)
            self.assertEqual(run.returncode,0)
            soup=BeautifulSoup(run.stdout,"html.parser")
            result=json.loads(soup.body.get("data-taky-smoke") or "{}")
            self.assertEqual(result["count"],1)
            self.assertEqual(result["detail"],9)
            self.assertEqual(result["noted"],"1")
            self.assertTrue(result["hasMemo"])

if __name__=="__main__":
    unittest.main()
