"""Local SHA-bound HTML access-block and technical text index proofs."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import central_html_capture_triage as html
import taky_central_source_factory as factory


class HtmlTriageTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        self.db=factory.connect(self.root/"isolated.sqlite3")
        self.addCleanup(self.db.close)

    def insert(self,content):
        f=self.root/"source.html"
        raw=content.encode("utf-8")
        f.write_bytes(raw)
        sha=hashlib.sha256(raw).hexdigest()
        sid=factory.register(self.db,"LOCAL_FILE",html.ACCOUNT,
                             str(f),f.name,html.ROLE,sha=sha,size=len(raw))
        return sid,f,sha

    def test_visible_html_page_has_original_proof_and_no_approval(self):
        content="<html><body><main><article><h1>Verified article</h1>" + "".join(
            f"<p>Meaningful sample paragraph {i}, source-bound original factual text.</p>"
            for i in range(55))+"</article></main></body></html>"
        sid,f,sha=self.insert(content)
        with patch.object(html,"ROOT",self.root):
            result=html.run(self.db,4)
            self.assertEqual(result["technical_html_indexed"],1)
            self.assertGreater(result["new_text_segments"],1)
            part=html.read_verified(self.db,sid,1)
            self.assertEqual(part["raw_sha256"],sha)
            self.assertFalse(part["forming_authorized"])
            self.assertEqual(html.run(self.db,4)["processed_sources"],0)
            self.assertEqual(self.db.execute(
                "SELECT state FROM stage WHERE source_id=? AND stage='INDEX'",
                (sid,)).fetchone()[0],"TECHNICAL_HTML_INDEX_READY")
            self.assertEqual(self.db.execute(
                "SELECT authoritative_review FROM source WHERE id=?",(sid,)
            ).fetchone()[0],"UNREVIEWED")
            self.db.execute(
                "UPDATE html_text_evidence SET text_sha256=? WHERE source_id=? AND chunk_no=1",
                ("0"*64,sid))
            with self.assertRaisesRegex(ValueError,"HTML_ANCHOR_BYTES_OR_PROJECTION_CHANGED"):
                html.read_verified(self.db,sid,1)

    def test_blocked_capture_is_not_marked_as_extracted(self):
        content="<html><body><main><h1>Sorry, you have been blocked</h1>" + (
            "<p>Please enable cookies. You are unable to access medium.com.</p>"*60
        )+"</main></body></html>"
        sid,f,sha=self.insert(content)
        with patch.object(html,"ROOT",self.root):
            outcome=html.run(self.db,4)
            self.assertEqual(outcome["technical_html_indexed"],0)
            self.assertEqual(outcome["reacquisition_or_specialist_holds"],1)
            self.assertEqual(self.db.execute(
                "SELECT state FROM stage WHERE stage='EXTRACT' AND source_id=?",
                (sid,)).fetchone()[0],"HTML_ACCESS_BLOCKED_REACQUIRE_RAW")
            self.assertEqual(self.db.execute(
                "SELECT COUNT(*) FROM html_text_evidence").fetchone()[0],0)
            self.assertFalse(self.db.execute(
                "SELECT state FROM stage WHERE stage='INDEX' AND source_id=?",
                (sid,)).fetchone())

    def test_original_sha_change_is_rejected(self):
        content="<html><body><main>"+("<p>Meaningful contextual evidence content</p>"*60)+"</main></body></html>"
        sid,f,sha=self.insert(content)
        f.write_bytes(f.read_bytes()+b"CHANGED")
        with patch.object(html,"ROOT",self.root):
            with self.assertRaisesRegex(ValueError,"HTML_FILE_SIZE_CHANGED"):
                html.run(self.db,4)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM html_text_evidence").fetchone()[0],0)

    def test_workbench_html_requires_explicit_source_and_preserves_gates(self):
        content="<html><body><main><h1>Agent operations evidence</h1>"+(
            "<p>Bounded research, observability and human-controlled approval.</p>"*60
        )+"</main></body></html>"
        file=self.root/"skax_article.html"
        raw=content.encode("utf-8");file.write_bytes(raw)
        sha=hashlib.sha256(raw).hexdigest()
        sid=factory.register(self.db,"LOCAL_FILE","TAKY_WORKBENCH_REFERENCE",
            str(file),file.name,"REFERENCE_PENDING_REVIEW",sha=sha,size=len(raw))
        with patch.object(html,"ROOT",self.root):
            self.assertEqual(len(html.candidates(self.db,4)),0)
            self.assertEqual(len(html.candidates(self.db,4,[sid])),1)
            self.assertEqual(html.run(self.db,4,[sid])["technical_html_indexed"],1)
            self.assertEqual(html.read_verified(self.db,sid,1)["raw_sha256"],sha)
            self.assertFalse(html.read_verified(self.db,sid,1)["forming_authorized"])
            self.assertEqual(self.db.execute(
                "SELECT state FROM stage WHERE source_id=? AND stage='FORMING'",
                (sid,)).fetchone()[0],"BLOCKED_REVIEW_NOT_APPROVED")
            self.assertEqual(html.run(self.db,4,[sid])["processed_sources"],0)

    def test_archive_label_never_routes_to_architecture(self):
        self.assertEqual(factory.domain_hint("skax_newsletters.html",
            "AI SK AX newsletter archive"),"AI_REFERENCE")
        self.assertEqual(factory.domain_hint("Archi Grow application",
            "building approval"),"ARCHITECTURE")
        self.assertEqual(factory.domain_hint("PPT Hunter AI usage prompt guide",
            "user review"),"AI_REFERENCE")
        self.assertEqual(factory.domain_hint("responsive UI layout",
            "design"),"DESIGN_ASSET")

    def test_explicit_extensionless_public_html_is_indexed_with_hash_gate(self):
        content="<html><body><main><article><h1>AI usage operations</h1>"+(
            "<p>Use a bounded context contract and cite the original evidence.</p>"*60
        )+"</article></main></body></html>"
        file=self.root/"ai-usage-guide__digest"
        raw=content.encode("utf-8");file.write_bytes(raw)
        digest=hashlib.sha256(raw).hexdigest()
        sid=factory.register(self.db,"LOCAL_FILE","TAKY_WORKBENCH_REFERENCE",
                             str(file),file.name,"REFERENCE_PENDING_REVIEW",
                             sha=digest,size=len(raw))
        self.assertNotEqual(self.db.execute(
            "SELECT media_kind FROM source WHERE id=?",(sid,)).fetchone()[0],"TEXT")
        with patch.object(html,"ROOT",self.root):
            self.assertEqual(len(html.candidates(self.db,4)),0)
            self.assertEqual(len(html.candidates(self.db,4,[sid])),1)
            self.assertEqual(html.run(self.db,4,[sid])["technical_html_indexed"],1)
            self.assertEqual(html.read_verified(self.db,sid,1)["raw_sha256"],digest)
            self.assertEqual(self.db.execute("SELECT state FROM stage WHERE source_id=? AND stage='FORMING'",
                          (sid,)).fetchone()[0],"BLOCKED_REVIEW_NOT_APPROVED")

    def test_extensionless_non_html_is_rejected_even_if_explicit(self):
        file=self.root/"nonhtml__digest"
        data=b"not html"*1000;file.write_bytes(data)
        sid=factory.register(self.db,"LOCAL_FILE","TAKY_WORKBENCH_REFERENCE",
                             str(file),file.name,"REFERENCE_PENDING_REVIEW",
                             sha=hashlib.sha256(data).hexdigest(),size=len(data))
        with patch.object(html,"ROOT",self.root):
            with self.assertRaisesRegex(ValueError,"EXTENSIONLESS_SOURCE_NOT_HTML"):
                html.run(self.db,4,[sid])
            self.assertEqual(self.db.execute(
                "SELECT COUNT(*) FROM html_text_evidence").fetchone()[0],0)

    def test_ai_continuity_design_is_operational_reference(self):
        self.assertEqual(factory.domain_hint(
            "SK AX AI Continuity resilience design and operations",
            "skax_3876.html"),"AI_REFERENCE")
        self.assertEqual(factory.domain_hint(
            "Explorer badge illustration design","asset"),"DESIGN_ASSET")


if __name__=="__main__":unittest.main()
