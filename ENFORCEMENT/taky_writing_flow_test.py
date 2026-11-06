#!/usr/bin/env python3
"""Regression for PERSONAL content writer only; Archi Grow has a separate path."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "TOOLS"
sys.path.insert(0,str(TOOLS))
import TAKY_WRITING_FLOW as writer

def run(*cmd,**kwargs):
    kwargs.setdefault("env",{**os.environ,"PYTHONIOENCODING":"utf-8"})
    kwargs.setdefault("encoding","utf-8")
    kwargs.setdefault("errors","replace")
    kwargs.setdefault("text",True)
    kwargs.setdefault("capture_output",True)
    return subprocess.run(*cmd,**kwargs)

def personal():
    return {
        "title":"주말 산책 기록","goal":"직접 본 장면을 가족에게 전한다","audience":"가족",
        "samples":["다녀온 사진을 다시 보니 기억이 나요. 좋네요!"],
        "facts":[{"text":"공원 입구에 벤치가 있다.","source":"PERSONAL_NOTE"},
                 {"text":"사진은 한 장만 골랐다.","source":"PERSONAL_NOTE"}],
        "photos":[{"caption":"나무 아래 놓인 벤치","source":"MY_CAPTION"}],
        "keywords":["산책","사진"],"takeaway":"다음에 사진을 더 남기고 싶다."
    }

class PersonalWriterTests(unittest.TestCase):
    def test_01_personal_genres_only(self):
        self.assertEqual(set(writer.GENRES),{
            "BLOG","PHOTOLOG","TRAVEL_JOURNAL","SOCIAL_POST",
            "REVIEW","NEWSLETTER","ESSAY"})
        for name in ["OFFICE_REPORT","EMAIL","NOTICE","보고서","이메일","공문","업무보고서"]:
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,"INVALID_KIND"):
                writer.normalize_genre(name)

    def test_02_personal_seven_parallel(self):
        variants=writer.compose_parallel(personal(),list(writer.GENRES))
        self.assertEqual(len(variants),7)
        for kind,doc in variants.items():
            self.assertEqual(doc["fact_ids_covered"],2)
            self.assertEqual(doc["photo_count"],1)
            if kind!="NEWSLETTER":
                self.assertEqual(doc["editorial_review"]["photo_captions_missing"],[])
            else:
                self.assertEqual(doc["editorial_review"]["photo_captions_missing"],["P01"])
            self.assertFalse(doc["writing_model_trained"])
            self.assertFalse(doc["editorial_review"]["factual_truth_verified"])
            self.assertEqual(doc["publication_status"],"LOCAL_DRAFT_NOT_PUBLISHED")
        self.assertIn("#산책",variants["SOCIAL_POST"]["draft_markdown"])
        self.assertIn("## 사진으로 남긴 장면",variants["BLOG"]["draft_markdown"])
        self.assertIn("## 여행에서 기억할 내용",variants["TRAVEL_JOURNAL"]["draft_markdown"])

    def test_03_no_workflow_crossover(self):
        with self.assertRaisesRegex(ValueError,"INVALID_KIND"):
            writer.compose_parallel(personal(),["BLOG","OFFICE_REPORT"])
        self.assertNotIn("OFFICE_REPORT",writer.ALIASES.values())

    def test_04_style_is_signal_not_model_training(self):
        a=writer.compose({**personal(),"kind":"BLOG"})
        b=writer.compose({**personal(),"kind":"BLOG","samples":["해당 내용을 기록합니다. 자료를 확인하였습니다."]})
        self.assertNotEqual(a["draft_sha256"],b["draft_sha256"])
        self.assertEqual(a["fact_ids_covered"],b["fact_ids_covered"])
        self.assertEqual(a["style_profile"]["sample_count"],1)

    def test_05_no_photo_content_claim(self):
        d=writer.compose({"kind":"PHOTOLOG","title":"사진 기록",
                          "photos":[{"path":"unknown.jpg"}]})
        self.assertIn("PHOTO_CONTENT_UNVERIFIED",d["holds"])
        self.assertFalse(d["photo_visual_analysis_performed"])
        self.assertEqual(d["status"],"DRAFT_CANDIDATE_HOLD")

    def test_06_source_gate_for_newsletter(self):
        d=writer.compose({"kind":"NEWSLETTER","title":"뉴스레터",
                          "facts":[{"text":"자료에 한 줄이 있다."}]})
        self.assertIn("NEWSLETTER_FACT_SOURCE_MISSING",d["holds"])
        self.assertEqual(d["editorial_review"]["source_references_missing"],["F01"])

    def test_07_personal_file_cli_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=root/"input.json";src.write_text(json.dumps(personal(),ensure_ascii=False),encoding="utf-8")
            cmd=[sys.executable,str(TOOLS/"TAKY_WRITING_FLOW.py"),
                 "--input",str(src),"--variants","BLOG,SOCIAL_POST,REVIEW","--output-dir",str(root/"out")]
            for _ in range(2):
                p=run(cmd);self.assertEqual(p.returncode,0,p.stderr)
                receipt=json.loads(p.stdout)
                self.assertEqual(len(receipt["genres"]),3)
                self.assertEqual(json.loads((root/"out"/"parallel_receipt.json").read_text(encoding="utf-8")),receipt)
                for kind,item in receipt["genres"].items():
                    source=(root/"out"/(kind.lower()+".md")).read_bytes()
                    self.assertEqual(item["draft_sha256"],hashlib.sha256(source).hexdigest())

    def test_08_prohibited_parallel_cli(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=root/"input.json";src.write_text(json.dumps(personal(),ensure_ascii=False),encoding="utf-8")
            p=run([sys.executable,str(TOOLS/"TAKY_WRITING_FLOW.py"),
                    "--input",str(src),"--variants","BLOG,OFFICE_REPORT",
                    "--output-dir",str(root/"output")])
            self.assertNotEqual(p.returncode,0)
            self.assertIn("INVALID_KIND",p.stderr)
            self.assertFalse((root/"output").exists())

    def test_09_archigrow_cli_is_not_linked_to_personal_writer(self):
        help_text=run([sys.executable,str(TOOLS/"ARCHIGROW_COMPETITION_REPORT.py"),"--help"])
        self.assertEqual(help_text.returncode,0,help_text.stderr)
        self.assertNotIn("--writing-input",help_text.stdout)
        archi=run([sys.executable,str(TOOLS/"ARCHIGROW_COMPETITION_REPORT.py"),
                   "--project-type","urban","--focus","site context","--json"])
        self.assertEqual(archi.returncode,0,archi.stderr)
        self.assertNotIn("writing_draft",json.loads(archi.stdout))

    def test_10_input_limits(self):
        with self.assertRaises(ValueError):
            writer.compose({"kind":"BLOG","title":"테스트","samples":["x"*10001]})
        with self.assertRaisesRegex(ValueError,"INVALID_FACT"):
            writer.compose({"kind":"BLOG","title":"테스트","facts":"invalid"})

    def test_11_added_value_grounded_to_user_input(self):
        src={**personal(),"kind":"BLOG",
             "insights":[{"text":"사진과 메모를 함께 두면 나중에 장면을 찾기 쉽다는 활용 팁",
                          "kind":"PRACTICAL_TIP","evidence_ids":["F02","P01"]}]}
        result=writer.compose(src)
        self.assertIn("나중에 장면을 찾기 쉽다는 활용 팁",result["draft_markdown"])
        self.assertEqual(result["value_add_count"],1)
        self.assertTrue(result["value_add_review_required"])
        self.assertEqual(result["fact_ids_covered"],2)
        self.assertEqual(result["value_add_verified_sources"][0]["evidence_ids"],["F02","P01"])

    def test_12_unknown_value_add_ref_is_blocked(self):
        with self.assertRaisesRegex(ValueError,"INSIGHT_UNGROUNDED"):
            writer.compose({**personal(),"kind":"BLOG",
                            "insights":[{"text":"출처 없는 주장","evidence_ids":["F99"]}]})
        with self.assertRaisesRegex(ValueError,"INSIGHT_UNGROUNDED"):
            writer.compose({**personal(),"kind":"BLOG",
                            "insights":[{"text":"근거 미입력","evidence_ids":[]}]})

    def test_13_photo_story_not_same_as_blog(self):
        src=personal()
        blog=writer.compose({**src,"kind":"BLOG"})["draft_markdown"]
        photolog=writer.compose({**src,"kind":"PHOTOLOG"})["draft_markdown"]
        self.assertNotEqual(blog,photolog)
        self.assertIn("## 사진 01:",photolog)
        self.assertIn("## 사진으로 남긴 장면",blog)

    def test_14_value_add_not_claimed_without_user_insights(self):
        result=writer.compose({**personal(),"kind":"BLOG"})
        self.assertEqual(result["value_add_count"],0)
        self.assertEqual(result["added_value_without_new_evidence"],"NOT_CLAIMED")

    def test_15_revision_prompt_has_original_context(self):
        result=writer.compose({**personal(),"kind":"BLOG","insights":[
            {"text":"기록의 활용 방법을 설명한다","kind":"ANALYSIS","evidence_ids":["F01"]}]})
        prompt=result["prompt_for_existing_model"]
        self.assertIn("문체 표본",prompt)
        self.assertIn("원자료를 넘어",result["draft_markdown"])
        self.assertIn("F01",prompt)
        self.assertIn("독자의 질문에 바로 답하는",prompt)


    def test_16_photo_lead_preserves_user_objective_in_visible_opening(self):
        source=personal()
        for kind in ("PHOTOLOG","TRAVEL_JOURNAL","SOCIAL_POST","BLOG","NEWSLETTER","REVIEW","ESSAY"):
            with self.subTest(kind=kind):
                row=writer.compose({**source,"kind":kind})
                self.assertIn(source["goal"],row["draft_markdown"][:400])
                self.assertEqual(row["editorial_review"]["purpose_literal_in_draft"],True)
                self.assertEqual(row["editorial_review"]["purpose_in_first_400_characters"],True)
                self.assertEqual(row["fact_ids_covered"],len(source["facts"]))
                self.assertFalse(row["editorial_review"]["factual_truth_verified"])
                self.assertEqual(row["publication_status"],"LOCAL_DRAFT_NOT_PUBLISHED")

    def test_18_single_photo_is_not_misrepresented_as_a_sequence(self):
        source=personal()
        one=writer.compose({**source,"kind":"SOCIAL_POST"})["draft_markdown"]
        self.assertNotIn("사진 순서대로",one)
        self.assertIn("기록된 내용을 살펴봅니다",one)
        two=writer.compose({**source,"kind":"PHOTOLOG",
                            "photos":source["photos"]+[
                                {"caption":"입구에서 본 안내판","source":"MY_CAPTION"}]})
        self.assertIn("사진 순서대로",two["draft_markdown"])

    def test_17_parallel_blocks_objective_or_fact_drift(self):
        from unittest.mock import patch
        real=writer.compose
        def corrupted_fact(payload):
            answer=real(payload)
            if payload["kind"]=="SOCIAL_POST":
                answer["fact_ids_covered"]-=1
                answer["editorial_review"]["facts_missing"]=["F02"]
            return answer
        with patch.object(writer,"compose",side_effect=corrupted_fact):
            with self.assertRaisesRegex(ValueError,"PARALLEL_FACT_COVERAGE_FAILED"):
                writer.compose_parallel(personal(),["BLOG","SOCIAL_POST"])
        def corrupted_purpose(payload):
            answer=real(payload)
            if payload["kind"]=="SOCIAL_POST":
                answer["editorial_review"]["purpose_in_first_400_characters"]=False
            return answer
        with patch.object(writer,"compose",side_effect=corrupted_purpose):
            with self.assertRaisesRegex(ValueError,"PARALLEL_PURPOSE_COVERAGE_FAILED"):
                writer.compose_parallel(personal(),["BLOG","SOCIAL_POST"])


    def test_19_real_loopback_ui_and_multi_genre_user_result(self):
        """Start the real app server in an isolated child, not a mocked route."""
        import socket
        import time
        import urllib.request
        from urllib.error import URLError
        with socket.socket() as socket_probe:
            socket_probe.bind(("127.0.0.1",0))
            port=socket_probe.getsockname()[1]
        command=[sys.executable,"-X","utf8",
                 str(TOOLS/"TAKY_WRITING_FLOW.py"),"--serve","--port",str(port)]
        proc=subprocess.Popen(command,stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                              env={**os.environ,"PYTHONIOENCODING":"utf-8"})
        try:
            base=f"http://127.0.0.1:{port}"
            for _ in range(60):
                if proc.poll() is not None:
                    self.fail("LOCAL_WRITING_UI_SERVER_TERMINATED")
                try:
                    with urllib.request.urlopen(base+"/health",timeout=.6) as response:
                        health=json.load(response)
                    break
                except (OSError,URLError):
                    time.sleep(.1)
            else:
                self.fail("LOCAL_WRITING_UI_SERVER_UNAVAILABLE")
            self.assertEqual(health["status"],"LOCAL_PREVIEW_CANDIDATE")
            with urllib.request.urlopen(base+"/",timeout=3) as response:
                self.assertEqual(response.status,200)
                self.assertIn(b"<!",response.read(4000))
            doc={"input":personal(),
                 "genres":["PHOTOLOG","TRAVEL_JOURNAL","SOCIAL_POST"]}
            request=urllib.request.Request(
                base+"/compose",
                json.dumps(doc,ensure_ascii=False).encode("utf-8"),
                {"Content-Type":"application/json; charset=utf-8",
                 "Origin":base},method="POST")
            with urllib.request.urlopen(request,timeout=5) as response:
                output=json.load(response)
            self.assertIs(output["published"],False)
            self.assertEqual(output["paid_api_calls"],0)
            for kind,result in output["results"].items():
                self.assertIn(doc["input"]["goal"],result["draft"][:400])
                self.assertEqual(result["fact_ids_covered"],2)
                self.assertIs(result["editorial_review"]["purpose_in_first_400_characters"],True)
                self.assertEqual(result["status"],"EVIDENCE_COVERED_DRAFT_CANDIDATE")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)

    def test_11_repeat_protection(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_PARALLEL_KIND"):
            writer.compose_parallel(personal(),["블로그","BLOG"])

if __name__=="__main__":
    unittest.main(verbosity=2)
