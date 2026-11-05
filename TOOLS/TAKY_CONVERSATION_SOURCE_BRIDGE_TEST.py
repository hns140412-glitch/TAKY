#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
import TAKY_CONVERSATION_SOURCE_BRIDGE as bridge
from TAKY_CONVERSATION_TOPIC_PROJECTION import build_projection, stable_topic_id

def share(nodes, backing="abc-native"):
    base = [
        "# SANITIZED CHATGPT TRANSCRIPT — Test",
        "STATUS: TRANSCRIPT_ONLY / NOTEBOOKLM_INPUT_CANDIDATE",
        "SCOPE: SAVED PAGE linear_conversation; USER↔ASSISTANT only",
        "SHARE_CONVERSATION_ID: share-001",
        "BACKING_CONVERSATION_ID: "+backing,
        "",
        "---",
    ]
    for idx,(role,txt) in enumerate(nodes,1):
        base.extend(["",f"## [{idx:04d}] {role} — 2026-10-18T11:{idx:02d}:00+00:00",
                     f"SOURCE_NODE_ID: node-{idx}", "CONTENT_TYPE: text", "", txt, "", "---"])
    return "\n".join(base)+"\n"

def export_fixture():
    return [{
        "id":"native-998", "title":"Mixed subjects", "current_node":"m3",
        "mapping":{
            "m0":{"parent":None,"message":None},
            "m1":{"parent":"m0","message":{"id":"m1","author":{"role":"user"},"content":{"parts":["웹앱 설치와 관리자 인증"]},"create_time":1792321201}},
            "m2":{"parent":"m1","message":{"id":"m2","author":{"role":"assistant"},"content":{"parts":["설명"]},"create_time":1792321202}},
            "m3":{"parent":"m2","message":{"id":"m3","author":{"role":"user"},"content":{"parts":["구글드라이브 용량 및 데이터 서버"]},"create_time":1792321203}},
            "alt":{"parent":"m1","message":{"id":"alt","author":{"role":"assistant"},"content":{"parts":["버려진 분기"]},"create_time":1792321202}},
        }
    }]

class BridgeTests(unittest.TestCase):
    def temp_source(self, data, name="share.md"):
        folder=tempfile.TemporaryDirectory()
        p=Path(folder.name)/name
        p.write_text(data,encoding="utf-8")
        self.addCleanup(folder.cleanup)
        return p

    def test_share_topic_switch_and_return(self):
        p=self.temp_source(share([
            ("USER","관리자 인증과 웹앱 설치 문제"),("ASSISTANT","설명"),
            ("USER","이제 구글드라이브 용량 및 운영 서버 관리"),
            ("ASSISTANT","알겠습니다"),("USER","웹앱 설치로 돌아가자")]))
        view=build_projection(bridge.from_sanitized_share(p))
        self.assertEqual([x["kind"] for x in view["transitions"]],
                         ["TOPIC_STARTED","TOPIC_SWITCHED","TOPIC_RETURNED"])
        self.assertEqual(view["counts"]["chat"],1)
        self.assertEqual(view["counts"]["topic"],2)

    def test_share_and_export_native_chat_identity_matches(self):
        share_row=bridge.from_sanitized_share(self.temp_source(share([("USER","웹앱 설치")],backing="native-998")))[0]
        e=self.temp_source(json.dumps(export_fixture(),ensure_ascii=False),"conversations.json")
        export_row=bridge.from_export(e)[0]
        self.assertEqual(share_row["conversation_id"],export_row["conversation_id"])

    def test_account_export_selected_branch_only(self):
        e=self.temp_source(json.dumps(export_fixture(),ensure_ascii=False),"conversations.json")
        rows=bridge.from_export(e)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]["actor"],"USER")
        self.assertEqual([r["message_index"] for r in rows],[1,2,3])
        self.assertFalse(any("alt" in r["source_ref"] for r in rows))
        view=build_projection(rows)
        self.assertEqual(view["counts"]["transitions"],2)

    def test_no_chat_id_fails_closed(self):
        p=self.temp_source(share([("USER","웹앱 설치")],backing="UNKNOWN_BACKING_ID").replace(
            "SHARE_CONVERSATION_ID: share-001","SHARE_CONVERSATION_ID: UNKNOWN_SHARE_ID"))
        with self.assertRaisesRegex(ValueError,"NATIVE_OR_SHARE_CONVERSATION_ID_REQUIRED"):
            bridge.from_sanitized_share(p)

    def test_missing_native_branch_no_guessing(self):
        e=export_fixture()
        del e[0]["current_node"]
        p=self.temp_source(json.dumps(e),"conversations.json")
        with self.assertRaisesRegex(ValueError,"EXPORT_SELECTED_BRANCH_MISSING"):
            bridge.from_export(p)

    def test_source_text_is_not_copied_into_projection(self):
        secret="private-parent-note-that-must-not-appear-4287"
        p=self.temp_source(share([("USER","관리자 인증 "+secret)]))
        s=json.dumps(build_projection(bridge.from_sanitized_share(p)),ensure_ascii=False)
        self.assertNotIn(secret,s)
        self.assertIn("source_text_sha256",s) if False else None
        self.assertEqual(p.read_text(encoding="utf-8"),share([("USER","관리자 인증 "+secret)]))

    def test_unclassified_long_turn_kept_review(self):
        p=self.temp_source(share([("USER","전혀 다른 주제에 대한 설명입니다.")]))
        out=build_projection(bridge.from_sanitized_share(p))
        self.assertEqual(out["counts"]["unresolved"],1)

    def test_short_continue_stays_in_topic(self):
        p=self.temp_source(share([("USER","주제별 아이디 부여"),("USER","ㄱ")]))
        out=build_projection(bridge.from_sanitized_share(p))
        self.assertEqual(out["counts"]["transitions"],1)
        self.assertEqual(out["chats"][0]["links"][1]["status"],"LINKED")

    def test_multi_topic_needs_primary_not_fabricated(self):
        p=self.temp_source(share([("USER","관리자 인증, 구글드라이브 용량, 주제별 분류")]))
        out=build_projection(bridge.from_sanitized_share(p))
        self.assertEqual(out["counts"]["topic"],3)
        self.assertEqual(out["counts"]["unresolved"],1)

    def test_duplicate_id_conflict_rejected(self):
        r=bridge.from_sanitized_share(self.temp_source(share([("USER","웹앱 설치")])))
        with self.assertRaisesRegex(ValueError,"EVENT_ID_REPLAY_CONFLICT"):
            build_projection(r+[dict(r[0],classification_basis="TAMPERED")])

    def test_explicit_ai_assignment_join_not_completion(self):
        work_id="TAKY-CHAT-" + "a"*32
        p=self.temp_source(share([("USER","워크벤치 작업 "+work_id)]))
        view=build_projection(bridge.from_sanitized_share(p))
        assign={"tasks":[{"work_id":work_id,"executor":"Claude","reviewer":"UNASSIGNED",
                          "status":"REVIEW","execution_verified":False,
                          "evidence_refs":["old-evidence"],"output_refs":["artifact"]}]}
        linked=bridge.attach_ai_assignments(view,assign)
        row=[t for t in linked["topics"] if work_id in t["work_ids"]][0]["ai_work_links"][0]
        self.assertEqual(row["binding"],"EXPLICIT_ID_MATCH")
        self.assertFalse(row["reported_verified"])
        self.assertEqual(linked["ai_workbench"]["topic_linked"],1)
        self.assertEqual(len(linked["ai_workbench"]["unlinked"]),0)

    def test_unrelated_ai_assignment_not_assigned_by_project(self):
        view=build_projection(bridge.from_sanitized_share(self.temp_source(
            share([("USER","워크벤치의 중복 여부")]))) )
        assign={"tasks":[{"work_id":"TAKY-CHAT-"+"b"*32,"status":"OPEN",
                          "project":"TAKY-MOBILE","executor":"Codex","execution_verified":False}]}
        view=bridge.attach_ai_assignments(view,assign)
        self.assertEqual(view["ai_workbench"]["topic_linked"],0)
        self.assertEqual(len(view["ai_workbench"]["unlinked"]),1)

    def test_ambiguous_topic_does_not_leak_to_assistant_reply(self):
        view=build_projection(bridge.from_sanitized_share(self.temp_source(share([
            ("USER","웹앱 설치"),("USER","관리자 인증과 데이터 서버 관련"),
            ("ASSISTANT","이후 설명")]))))
        self.assertEqual(view["chats"][0]["links"][-1]["status"],"REQUIRES_TOPIC_CLASSIFICATION")

    def test_same_message_from_two_sources_merges_references(self):
        base=bridge.from_sanitized_share(self.temp_source(share([("USER","웹앱 설치")])))
        alternate=dict(base[0], source_ref="another-export.json#node=node-1",
                       source_kind="ACCOUNT_EXPORT_SELECTED_BRANCH")
        result=bridge.merge_events(base,[alternate])
        self.assertEqual(result["chats"][0]["event_count"],1)
        self.assertEqual(len(result["chats"][0]["links"][0]["source_observation_refs"]),2)

    def test_same_native_id_changed_content_blocks_collision(self):
        base=bridge.from_sanitized_share(self.temp_source(share([("USER","웹앱 설치")])))
        altered=dict(base[0], source_text_sha256="a"*64)
        with self.assertRaisesRegex(ValueError,"SOURCE_MESSAGE_CONFLICT"):
            bridge.merge_events(base,[altered])

if __name__=="__main__": unittest.main()
