"""Read-only Central owner-review packet coverage with immutable output guards."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import central_forming_review_queue as queue
import taky_central_source_factory as factory


class FormingReviewQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=12)
        cls.db.row_factory=sqlite3.Row
        cls.result=queue.build_queue(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_original_backed_review_packets_are_never_approved(self):
        v=self.result
        self.assertEqual(v["review_packet_count"]+v["missing_extract_hold_count"],
                         v["source_count"])
        self.assertGreaterEqual(v["source_count"],160)
        self.assertGreater(v["review_packet_count"],120)
        self.assertEqual(sum(v["hold_reason_counts"].values()),
                         v["missing_extract_hold_count"])
        self.assertEqual(v["hold_reason_counts"]["EMPTY_RAW_NO_EXTRACTABLE_BYTES"],1)
        self.assertEqual(v["hold_reason_counts"]["VISUAL_SOURCE_REQUIRES_SPECIALIST_GROUNDING"],6)
        self.assertGreater(v["hold_reason_counts"]["RUNTIME_METADATA_NOT_SEMANTIC_SOURCE"],5)
        self.assertTrue(all(x["assigned_owner_namespace"] is None
                            and not x["route_is_authority"]
                            and x["review_status"]=="OWNER_SEMANTIC_REVIEW_REQUIRED"
                            and x["forming_status"]=="HOLD_PENDING_INDEPENDENT_OWNER_REVIEW"
                            and x["reviewed_claims"]==[]
                            and x["verified_extracts"] for x in v["review_packets"]))
        self.assertFalse(v["forming_approved"])
        self.assertFalse(v["learning_consumed"])
        self.assertTrue(v["canonical_source_db_read_only"])
        architecture=[x for x in v["review_packets"]
                      if x["domain_hint"]=="ARCHITECTURE"]
        self.assertGreater(len(architecture),30)
        self.assertTrue(all("LEGAL_EFFECTIVE_DATE_NOT_VERIFIED" in x["known_gaps"]
                            for x in architecture))
        self.assertEqual(v["verbatim_legal_reference_marker_count"],
            sum(len(x["verbatim_legal_reference_markers"]) for x in architecture))
        self.assertGreater(v["verbatim_legal_reference_marker_count"],10)
        for doc in architecture:
            for marker in doc["verbatim_legal_reference_markers"]:
                anchor=next(a for a in doc["verified_extracts"]
                    if a["ref"]==marker["anchor_ref"] and
                       a["content_sha256"]==marker["content_sha256"])
                start=marker["text_offset_in_excerpt"]
                actual=anchor["excerpt"][start:start+len(marker["text_as_printed"])]
                self.assertEqual(actual,marker["text_as_printed"])
                self.assertFalse(marker["legal_effectiveness_verified"])
                self.assertEqual(marker["evidence_state"],"LEXICAL_UNREVIEWED")
        for packet in v["review_packets"]:
            self.assertEqual(packet["packet_revision"],queue.digest(
                {k:x for k,x in packet.items() if k!="packet_revision"}))
            self.assertTrue(all(a["raw_sha256"]==packet["raw_sha256"]
                                for a in packet["verified_extracts"]))

    def test_relevant_sections_not_readme_decorations(self):
        # This real RAW previously selected <div> and badge links, omitting method.
        sid="raw:66fe062ee3705af835b09ffa8da112fd14bc8a6025f0d4fb22b4291d353268a9"
        focused=queue.build_queue(self.db,[sid])
        self.assertEqual(focused["review_packet_count"],1)
        extracts=focused["review_packets"][0]["verified_extracts"]
        headings=" ".join(e["excerpt"] for e in extracts)
        self.assertEqual([e["ref"] for e in extracts],
            ["MARKDOWN_SECTION:003","MARKDOWN_SECTION:004",
             "MARKDOWN_SECTION:005","MARKDOWN_SECTION:007"])
        self.assertIn("How it works",headings)
        self.assertIn("Why it works",headings)
        self.assertNotIn("MARKDOWN_SECTION:001",[e["ref"] for e in extracts])
        self.assertEqual(focused["review_packets"][0]["forming_status"],
            "HOLD_PENDING_INDEPENDENT_OWNER_REVIEW")
        self.assertFalse(focused["forming_approved"])
        self.assertEqual(queue.verify_queue(self.db,focused)["review_packets"],1)

    def test_revision_replay_and_tamper_rejection(self):
        result=queue.verify_queue(self.db,self.result)
        self.assertEqual(result["review_packets"],
                         self.result["review_packet_count"])
        bad=copy.deepcopy(self.result)
        bad["review_packets"][0]["verified_extracts"][0]["excerpt"]="FORGED"
        with self.assertRaisesRegex(ValueError,"FORMING_QUEUE_MANIFEST_TAMPERED"):
            queue.verify_queue(self.db,bad)

    def test_immutable_export_and_conflict(self):
        with tempfile.TemporaryDirectory() as temp:
            path,created=queue.write_immutable(self.result,temp)
            self.assertTrue(created)
            copy_file,second=queue.write_immutable(self.result,temp)
            self.assertFalse(second)
            self.assertEqual(copy_file,path)
            saved=json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["manifest_sha256"],
                             self.result["manifest_sha256"])
            path.write_text('{"status":"FORGED"}',encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"IMMUTABLE_REVISION_CONFLICT"):
                queue.write_immutable(self.result,temp)


class GsdFormingPreviewCase(unittest.TestCase):
    def test_real_source_method_to_browser_preview_without_approval(self):
        import subprocess
        from bs4 import BeautifulSoup
        import central_full_anchor_review as full
        import central_local_review_console as console
        sid="raw:66fe062ee3705af835b09ffa8da112fd14bc8a6025f0d4fb22b4291d353268a9"
        candidate=json.loads((queue.EVIDENCE/"GSD_FORMING_APPLICATION_CANDIDATE_20261016.json").read_text(encoding="utf-8"))
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=12) as db:
            db.row_factory=sqlite3.Row
            scoped=queue.build_queue(db,[sid])
            projection=full.project(db,scoped)
            validated=console.validated_candidates(projection,candidate)
            self.assertEqual(len(validated),1)
            self.assertIn("Discuss",validated[sid]["observed_method"])
            self.assertEqual(validated[sid]["grounding_state"],
                "TEXTUALLY_GROUNDED_SEMANTIC_REVIEW_PENDING")
            self.assertEqual(len(validated[sid]["source_grounding"]),2)
            altered_quote=copy.deepcopy(candidate)
            altered_quote["items"][0]["source_grounding"][0]["exact_quote"]="Each milestone repeats the same seven-step loop, one phase at a time:"
            with self.assertRaisesRegex(ValueError,"FORMING_GROUNDING_QUOTE_NOT_IN_VERIFIED_SOURCE"):
                console.validated_candidates(projection,altered_quote)
            altered_field=copy.deepcopy(candidate)
            altered_field["items"][0]["source_grounding"][1]["field"]="taky_gap"
            with self.assertRaisesRegex(ValueError,"FORMING_GROUNDING_CLAIM_INVALID"):
                console.validated_candidates(projection,altered_field)
            html=console.render(projection,db,application_candidates=candidate)
            self.assertFalse(projection["forming_approved"])
            self.assertFalse(projection["learning_consumed"])
            altered=copy.deepcopy(candidate)
            altered["items"][0]["review_anchor_sha256"]="0"*64
            with self.assertRaisesRegex(ValueError,"CANDIDATE_RAW_OR_ANCHOR_NOT_BOUND"):
                console.validated_candidates(projection,altered)
        chrome=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        if not chrome.is_file():self.skipTest("CHROME_NOT_INSTALLED")
        script="""<script>document.body.dataset.formingSmoke=JSON.stringify({
          methodCards:document.querySelectorAll('#detail .method-grid .anchor').length,
          methodText:document.querySelector('#detail .method-grid')?.textContent.includes('Discuss'),
          sourceQuoteVisible:document.querySelector('#detail')?.textContent.includes('structured artifacts like'),
          independentApprovalStillPending:document.querySelector('#detail')?.textContent.includes('승인된 사실이 아닙니다'),
          sourceCards:document.querySelectorAll('#sourceList button.source').length,
          anchors:document.querySelectorAll('#detail .anchor').length
        });</script>"""
        with tempfile.TemporaryDirectory(prefix="taky_gsd_forming_") as temp:
            local=Path(temp)/"review.html"
            local.write_text(html.replace("</body>",script+"</body>"),encoding="utf-8")
            cmd=[str(chrome),"--headless=new","--disable-gpu","--disable-extensions",
                 "--no-first-run","--no-default-browser-check","--virtual-time-budget=1300",
                 "--dump-dom",local.as_uri()]
            result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=False)
            self.assertEqual(result.returncode,0)
            page=BeautifulSoup(result.stdout,"html.parser")
            actual=json.loads(page.body.get("data-forming-smoke") or "{}")
            self.assertEqual(actual.get("methodCards"),5)
            self.assertTrue(actual.get("methodText"))
            self.assertTrue(actual.get("sourceQuoteVisible"))
            self.assertTrue(actual.get("independentApprovalStillPending"))
            self.assertEqual(actual.get("sourceCards"),1)
            self.assertGreaterEqual(actual.get("anchors",0),15)


class CrossDomainExtractiveFormingCase(unittest.TestCase):
    """Two real architecture-hinted sources; no source/owner promotion."""
    HTML_SOURCE="raw:00941107e758f1dba6918f3d08a3d0d4eeb096991b151c066af598f34df9eec3"
    PDF_SOURCE="raw:005c5a6fad8873355f0b41561786b4d3add7ed6e6f51bfe8fe45e8ba409d67e1"

    def test_archi_grow_case_stays_case_specific_and_reviewable(self):
        import central_full_anchor_review as full
        import central_local_review_console as console
        import subprocess
        from bs4 import BeautifulSoup
        candidate=json.loads((queue.EVIDENCE/"ARCHI_GROW_FORMING_APPLICATION_CANDIDATE_20261016.json").read_text(encoding="utf-8"))
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=12) as db:
            db.row_factory=sqlite3.Row
            scoped=queue.build_queue(db,[self.PDF_SOURCE])
            projection=full.project(db,scoped)
            validated=console.validated_candidates(projection,candidate)
            self.assertEqual(len(validated),1)
            item=validated[self.PDF_SOURCE]
            self.assertEqual(item["grounding_state"],"TEXTUALLY_GROUNDED_SEMANTIC_REVIEW_PENDING")
            self.assertEqual(len(item["source_grounding"]),2)
            self.assertIn("경기도 양주시",item["observed_method"])
            self.assertIn("서울시",item["taky_gap"])
            tampered=copy.deepcopy(candidate)
            tampered["items"][0]["source_grounding"][1]["exact_quote"]="허위 교통심의 문장으로 변경하면 반드시 실패해야 한다."
            with self.assertRaisesRegex(ValueError,"FORMING_GROUNDING_QUOTE_NOT_IN_VERIFIED_SOURCE"):
                console.validated_candidates(projection,tampered)
            rendered=console.render(projection,db,application_candidates=candidate)
            self.assertFalse(projection["forming_approved"])
        chrome=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        if not chrome.is_file():self.skipTest("CHROME_NOT_INSTALLED")
        script="""<script>document.body.dataset.formingSmoke=JSON.stringify({
          sourceCards:document.querySelectorAll('#sourceList button.source').length,
          groundingVisible:document.querySelector('#detail')?.textContent.includes('건축심의 시 도면과 교통영향평가'),
          proposedChangeVisible:document.querySelector('#detail')?.textContent.includes('SOURCE_CASE_UNAPPROVED'),
          noAutoApproval:document.querySelector('#detail')?.textContent.includes('승인된 사실이 아닙니다')
        });</script>"""
        with tempfile.TemporaryDirectory(prefix="taky_archi_forming_") as temp:
            html=Path(temp)/"case.html"
            html.write_text(rendered.replace("</body>",script+"</body>"),encoding="utf-8")
            output=subprocess.run([str(chrome),"--headless=new","--disable-gpu",
                "--disable-extensions","--no-first-run","--no-default-browser-check",
                "--virtual-time-budget=1200","--dump-dom",html.as_uri()],
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=False)
            self.assertEqual(output.returncode,0)
            page=BeautifulSoup(output.stdout,"html.parser")
            actual=json.loads(page.body.get("data-forming-smoke") or "{}")
            self.assertEqual(actual.get("sourceCards"),1)
            self.assertTrue(actual.get("groundingVisible"))
            self.assertTrue(actual.get("proposedChangeVisible"))
            self.assertTrue(actual.get("noAutoApproval"))

    def test_bounded_html_and_pdf_extractive_selection(self):
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=12) as db:
            db.row_factory=sqlite3.Row
            scoped=queue.build_queue(db,[self.HTML_SOURCE,self.PDF_SOURCE])
            self.assertEqual(scoped["source_count"],2)
            self.assertEqual(scoped["review_packet_count"],2)
            self.assertEqual(scoped["missing_extract_hold_count"],0)
            byid={p["source_id"]:p for p in scoped["review_packets"]}
            for sid,kind in ((self.HTML_SOURCE,"HTML_SEGMENT"),(self.PDF_SOURCE,"PDF_PAGE")):
                p=byid[sid]
                self.assertGreaterEqual(len(p["verified_extracts"]),2)
                self.assertLessEqual(len(p["verified_extracts"]),4)
                self.assertTrue(all(a["kind"]==kind for a in p["verified_extracts"]))
                self.assertEqual(p["review_status"],"OWNER_SEMANTIC_REVIEW_REQUIRED")
                self.assertFalse(p["route_is_authority"])
                self.assertEqual(p["assigned_owner_namespace"],None)
                self.assertTrue(all(a["raw_sha256"]==p["raw_sha256"] for a in p["verified_extracts"]))
            # Index domain label is just a hint; the HTML is about math
            # learning channels, NOT an authorized Archi Grow source.
            excerpts=" ".join(a["excerpt"] for a in byid[self.HTML_SOURCE]["verified_extracts"])
            self.assertIn("수학",excerpts)
            self.assertEqual(byid[self.HTML_SOURCE]["owner_review_route_hint"],"OWNER_ROUTING_REQUIRED")
            self.assertEqual(byid[self.HTML_SOURCE]["domain_hint_conflict"]["reason"],
                             "DOMAIN_HINT_CONTENT_CONFLICT_REVIEW_REQUIRED")
            self.assertEqual(byid[self.PDF_SOURCE]["owner_review_route_hint"],"ARCHI_GROW_OWNER_REVIEW")
            self.assertNotIn("domain_hint_conflict",byid[self.PDF_SOURCE])
            self.assertEqual(queue.verify_queue(db,scoped)["review_packets"],2)


if __name__=="__main__":
    unittest.main()
