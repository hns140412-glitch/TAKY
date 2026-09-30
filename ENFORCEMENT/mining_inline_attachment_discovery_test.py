#!/usr/bin/env python3
"""Real publisher HTML snippet: four original DEXT5 entries, not four ordinary links."""
import unittest
from mining_inline_attachment_discovery import discover_exact_inline_attachments as discover
PAGE="https://www.ice.go.kr/ice/na/ntt/selectNttInfo.do?bbsAllView=Y&bbsId=1630&mi=&nttSn=3383177"
NAMES=[
    "[부록] 초등 수학과 서논술형 평가 문항.hwpx",
    "[부록] 초등 과학과 서논술형 평가 문항.hwpx",
    "초등 수학과 서논술형 평가 도움자료.pdf",
    "초등 과학과 서논술형 평가 도움자료.pdf",
]
RECORDS=[
    ("fc7f54814aad43d790d39eb799aba533.hwpx",25170695,2700091),
    ("322d8a263b0b4fe5860bf4b68bc66720.hwpx",82304095,2700092),
    ("611131ca7e3b4a759d63b64bdc81e2e3.pdf",10813448,2700235),
    ("cea30c60a7d443a8aee27f481d76e073.pdf",12129043,2700236),
]
PATH="/upload/ice/na/bbs_1630/2026/09/"
def call(name,path,size,file_id,post="3383177"):
    return f"DEXT5UPLOAD.AddUploadedFile('{post}', '{name}','{path}','{size}','{file_id}', G_UploadID);"
REAL_SNIPPET="function fn_addFile() { " + " ".join(
    call(n,PATH+file,s,id) for n,(file,s,id) in zip(NAMES,RECORDS)
) + " }"

class ExactInlineDiscoveryTest(unittest.TestCase):
    def test_four_exact_official_paths_recovered_from_actual_page_structure(self):
        out=discover(REAL_SNIPPET,PAGE,NAMES,post_id="3383177")
        self.assertEqual(out["state"],"CANDIDATES_REQUIRE_ORIGINAL_FETCH")
        self.assertEqual(out["unresolved_names"],[])
        self.assertEqual(len(out["candidates"]),4)
        for row,name,(file,size,id) in zip(out["candidates"],NAMES,RECORDS):
            self.assertEqual(row["original_filename"],name)
            self.assertEqual(row["source_url"],"https://www.ice.go.kr"+PATH+file)
            self.assertEqual(row["publisher_size_bytes"],size)
            self.assertEqual(row["publisher_file_id"],str(id))
            self.assertFalse(row["acquired_original_bytes"])
            self.assertFalse(row["automatic_index_promotion"])
    def test_wrong_post_is_not_other_pages_source(self):
        out=discover(REAL_SNIPPET,PAGE,NAMES,post_id="another")
        self.assertEqual(out["state"],"HOLD_INVALID_SOURCE_CONTEXT")
        out=discover(REAL_SNIPPET,PAGE,NAMES,post_id="3383178")
        self.assertEqual(out["candidates"],[])
        self.assertEqual(out["unresolved_names"],NAMES)
    def test_near_filename_is_not_exact_original(self):
        out=discover(REAL_SNIPPET,PAGE,["초등 과학과 서논술형 평가 도움자료 최종.pdf"],post_id="3383177")
        self.assertEqual(out["candidates"],[])
        self.assertEqual(len(out["unresolved_names"]),1)
    def test_block_external_or_encoded_traversal_and_wrong_extension(self):
        malicious=" ".join([
            call(NAMES[0],"https://attacker.example/a.hwpx",25170695,1),
            call(NAMES[1],"/upload/%2e%2e/secret.hwpx",82304095,2),
            call(NAMES[2],"/upload/real.hwpx",10813448,3),
            call(NAMES[3],"//attacker.example/fake.pdf",12129043,4),
        ])
        out=discover(malicious,PAGE,NAMES,post_id="3383177")
        self.assertEqual(len(out["candidates"]),0)
        self.assertEqual(len(out["rejected"]),4)
        self.assertEqual(set(x["reason"] for x in out["rejected"]),{"UNSAFE_OR_MISMATCHED_PUBLISHER_PATH"})
    def test_conflicting_same_named_origin_does_not_pick_arbitrary_first(self):
        snippet=call(NAMES[0],PATH+RECORDS[0][0],25170695,1)+call(
            NAMES[0],PATH+"different.hwpx",25170695,2)
        out=discover(snippet,PAGE,[NAMES[0]],post_id="3383177")
        self.assertEqual(out["candidates"],[])
        self.assertEqual(out["rejected"][0]["reason"],"CONFLICTING_DUPLICATE_INLINE_ENTRY")
    def test_script_is_not_executed_or_treated_as_binary_evidence(self):
        content=REAL_SNIPPET+"<script>throw new Error('must-not-run')</script>"
        out=discover(content,PAGE,NAMES,post_id="3383177")
        self.assertEqual(len(out["candidates"]),4)
        self.assertTrue(out["guards"]["no_network_calls"])
        self.assertTrue(all(not row["independently_verified"] for row in out["candidates"]))
    def test_size_and_page_limits_fail_closed(self):
        big=call(NAMES[0],PATH+RECORDS[0][0],9000000000,1)
        out=discover(big,PAGE,[NAMES[0]],post_id="3383177")
        self.assertEqual(out["candidates"],[])
        self.assertEqual(out["rejected"][0]["reason"],"PUBLISHER_SIZE_OUT_OF_BOUND")
        self.assertEqual(discover("x"*2000001,PAGE,NAMES,post_id="3383177")["state"],
                         "HOLD_INVALID_SOURCE_CONTEXT")

if __name__=="__main__":unittest.main()
