#!/usr/bin/env python3
import unittest

from execution_state_engine import cancellation_context, transition
from executor_transport import sha256_json
from github_issue_executor_queue import cancellation_comment, issue_payload
from github_queue_consumer import consume
from github_queue_poll_plan import plan


def lifecycle_cancel_record(target="queue_issue:7"):
    record = {
        "task_id": "cancel-test",
        "current_state": "IN_PROGRESS",
        "requested_state": "CANCELLED",
        "transition_target_ref": target,
    }
    context, failures = cancellation_context(record, "IN_PROGRESS")
    assert not failures, failures
    record["cancellation_evidence"] = {
        "cancellation_id": "cancel-001",
        "authority_ref": "user",
        "decision": "CANCEL",
        "reason": "user requested stop",
        **context,
    }
    return record


def queue_fixture():
    task = {
        "task_id": "cancel-test",
        "repository": "hns140412-glitch/Ready-Set",
        "executor_automation": {"target_repository_local": False},
    }
    envelope = {
        "task_id": task["task_id"],
        "task_contract_sha256": sha256_json(task),
        "task_contract": task,
        "transport": "GITHUB_ISSUE_QUEUE",
        "provider": "CODEX",
        "dispatch_status": "DISPATCH_READY",
    }
    issue = issue_payload(envelope)["issue"]
    cancel = cancellation_comment(
        envelope,
        {
            "cancellation_id": "cancel-001",
            "authority_ref": "alice",
            "decision": "CANCEL",
            "reason": "user no longer wants this task",
            "queue_issue_number": 7,
        },
    )
    assert cancel["pass"], cancel
    return envelope, issue, cancel["comment"]


class TaskCancellationContractTest(unittest.TestCase):
    def test_pre_merge_task_can_cancel_to_terminal_state(self):
        result = transition(lifecycle_cancel_record())
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["current_state"], "CANCELLED")
        self.assertEqual(result["cancellation_verified"]["decision"], "CANCEL")

    def test_changed_cancellation_target_is_rejected(self):
        record = lifecycle_cancel_record("queue_issue:7")
        record["transition_target_ref"] = "queue_issue:8"
        result = transition(record)
        self.assertFalse(result["pass"])
        self.assertIn("CANCELLATION_TARGET_REF_MISMATCH", result["detected"])
        self.assertIn("CANCELLATION_CONTEXT_HASH_MISMATCH", result["detected"])

    def test_merged_work_cannot_be_relabelled_cancelled(self):
        result = transition({
            "task_id": "cancel-test",
            "current_state": "MERGED",
            "requested_state": "CANCELLED",
            "transition_target_ref": "commit:abc",
            "cancellation_evidence": {},
        })
        self.assertFalse(result["pass"])
        self.assertIn("FORBIDDEN_STATE_TRANSITION:MERGED->CANCELLED", result["detected"])

    def test_trusted_queue_actor_cancels_and_closes_issue(self):
        _, issue, body = queue_fixture()
        result = consume({
            "_event_name": "issue_comment",
            "issue": {"number": 7, "title": issue["title"], "body": issue["body"]},
            "comment": {
                "id": 77,
                "body": body,
                "user": {"login": "alice"},
                "author_association": "OWNER",
            },
        })
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["action"], "TASK_CANCELLED")
        self.assertTrue(result["close_issue"])

    def test_untrusted_queue_actor_cannot_cancel(self):
        _, issue, body = queue_fixture()
        result = consume({
            "_event_name": "issue_comment",
            "issue": {"number": 7, "title": issue["title"], "body": issue["body"]},
            "comment": {
                "id": 78,
                "body": body,
                "user": {"login": "alice"},
                "author_association": "NONE",
            },
        })
        self.assertFalse(result["pass"])
        self.assertIn("CANCELLATION_AUTHORITY_NOT_REPOSITORY_TRUSTED", result["comment"])
        self.assertFalse(result["close_issue"])

    def test_poller_recovers_missed_cancellation_event(self):
        _, issue, body = queue_fixture()
        snapshot = {
            "number": 7,
            "title": issue["title"],
            "body": issue["body"],
            "comments": [{
                "id": 79,
                "body": body,
                "author": {"login": "alice"},
                "authorAssociation": "OWNER",
            }],
        }
        result = plan(snapshot)
        self.assertTrue(result["pass"], result)
        self.assertTrue(result["close_issue"], result)
        self.assertTrue(any(
            item.get("action") == "TASK_CANCELLED"
            for item in result["processed"]
        ))


if __name__ == "__main__":
    unittest.main()
