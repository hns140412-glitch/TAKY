#!/usr/bin/env python3
"""Regression for same-chat topic switching and cross-chat topic reuse."""
import json
import tempfile
import unittest
from pathlib import Path
import TAKY_CONVERSATION_TOPIC_PROJECTION as topic

def event(i, chat="native-chat-1", key=None, project="TAKY-MOBILE", **more):
    v = {"event_id": f"e{i}", "conversation_id": chat,
         "captured_at": f"2026-10-18T11:{i:02d}:00Z",
         "message_index": i, "project_namespace": project,
         "source_ref": f"chat-turn-{i}"}
    if key:
        v.update(topic_key=key, topic_label=key)
    v.update(more)
    return v

class TopicProjectionTests(unittest.TestCase):
    def test_switch_and_return_keep_topic_id(self):
        rows = [event(1, key="webapp"), event(2, key="server"),
                event(3, key="webapp")]
        p = topic.build_projection(rows)
        t = p["transitions"]
        self.assertEqual([x["kind"] for x in t],
                         ["TOPIC_STARTED", "TOPIC_SWITCHED", "TOPIC_RETURNED"])
        self.assertEqual(t[0]["to_topic_id"], t[2]["to_topic_id"])
        self.assertNotEqual(t[0]["to_topic_id"], t[1]["to_topic_id"])
        self.assertEqual(len(p["topics"]), 2)

    def test_same_topic_across_multiple_chats(self):
        p = topic.build_projection([event(1, chat="chat-a", key="webapp"),
                                    event(2, chat="chat-b", key="webapp")])
        self.assertEqual(len(p["chats"]), 2)
        self.assertEqual(len(p["topics"]), 1)
        self.assertEqual(len(p["topics"][0]["chat_ids"]), 2)

    def test_distinct_projects_same_topic_label(self):
        p = topic.build_projection([event(1, key="UI", project="TAKY-MOBILE"),
                                    event(2, chat="chat-b", key="UI", project="PLAY-CAMP")])
        self.assertEqual(len(p["topics"]), 2)

    def test_multi_topic_without_primary_preserves_current(self):
        p = topic.build_projection([event(1, key="mobile-app"),
            event(2, topic_refs=[{"project":"TAKY-MOBILE","topic_key":"storage"},
                                 {"project":"TAKY-MOBILE","topic_key":"orchestration"}]),
            event(3, key="mobile-app")])
        self.assertEqual(len(p["transitions"]), 1)
        self.assertEqual(p["chats"][0]["links"][1]["status"], "MULTI_TOPIC_PRIMARY_UNRESOLVED")

    def test_multi_topic_with_explicit_primary_switches(self):
        p = topic.build_projection([event(1, key="mobile-app"),
            event(2, topic_refs=[{"project":"TAKY-MOBILE","topic_key":"storage"},
                                 {"project":"TAKY-MOBILE","topic_key":"orchestration"}],
                  primary_topic_key="storage")])
        self.assertEqual([v["kind"] for v in p["transitions"]], ["TOPIC_STARTED", "TOPIC_SWITCHED"])
        self.assertEqual(p["chats"][0]["active_topic_id"], topic.stable_topic_id("TAKY-MOBILE", "storage"))

    def test_untagged_event_preserved_for_review_not_assumed_done(self):
        p = topic.build_projection([event(1,key="webapp"),
                                    event(2,source_ref="unknown-switch")])
        self.assertEqual(p["counts"]["unresolved"], 1)
        self.assertEqual(p["chats"][0]["active_topic_id"], topic.stable_topic_id("TAKY-MOBILE","webapp"))
        self.assertEqual(len(p["chats"][0]["links"]), 2)

    def test_native_id_missing_not_fabricated(self):
        row = event(1,key="server")
        del row["conversation_id"]
        row["session_id"] = "20261018"
        p = topic.build_projection([row])
        self.assertEqual(p["counts"]["chat"],0)
        self.assertEqual(p["unbound_events"][0]["session_ref"], "20261018")

    def test_duplicate_event_is_idempotent_conflict_raises(self):
        one = event(1, key="webapp")
        self.assertEqual(topic.build_projection([one,one])["chats"][0]["event_count"],1)
        changed = dict(one, topic_key="server")
        with self.assertRaisesRegex(ValueError, "EVENT_ID_REPLAY_CONFLICT"):
            topic.build_projection([one,changed])

    def test_broken_primary_rejected(self):
        with self.assertRaisesRegex(ValueError,"PRIMARY_TOPIC_NOT_IN_REFERENCES"):
            topic.build_projection([event(1,key="webapp",primary_topic_key="unrelated")])

    def test_jsonl_input_non_mutating_and_work_id_bound(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"existing.jsonl"
            row=event(1,key="orchestration",work_ids=["TAKY-CHAT-0001"])
            original=json.dumps(row,ensure_ascii=False)+"\n"
            path.write_text(original,encoding="utf-8")
            p=topic.build_projection(topic.load_events([path]))
            self.assertEqual(p["topics"][0]["work_ids"],["TAKY-CHAT-0001"])
            self.assertEqual(path.read_text(encoding="utf-8"),original)
            self.assertFalse(p["canonical_changed"])

if __name__ == "__main__":
    unittest.main()
