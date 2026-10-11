#!/usr/bin/env python3
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import side_effect_ledger as ledger
from side_effect_ledger import canonical_bytes, guard, paths, persist, record_hash

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
ACTION_KIND = "SEND_MESSAGE"
TARGET = "remote:message-target"


def record(status="PLANNED", policy="FORBID", *, updated_at="2026-10-03T23:59:00+09:00"):
    item = {
        "ledger_version": "1.0",
        "effect_id": "send-001",
        "task_id": "TASK-1",
        "namespace": "RUNTIME",
        "action_kind": ACTION_KIND,
        "action_payload_hash": HASH_A,
        "idempotency_key": "idem-001",
        "state_schema_version": "1",
        "target_ref": TARGET,
        "execution_status": status,
        "replay_policy": policy,
        "updated_at": updated_at,
        "before_state_ref": "receipt:before",
    }
    if status in {"APPLIED", "VERIFIED"}:
        item["after_state_ref"] = "receipt:after"
    return item


def check(root: Path, **overrides):
    args = {
        "namespace": "RUNTIME",
        "task_id": "TASK-1",
        "effect_id": "send-001",
        "idempotency_key": "idem-001",
        "action_payload_hash": HASH_A,
        "action_kind": ACTION_KIND,
        "target_ref": TARGET,
    }
    args.update(overrides)
    return guard(root, **args)


class SideEffectLedgerTest(unittest.TestCase):
    def compensated_record(self, root):
        evidence = root / "compensation.json"
        evidence.write_text('{"event_id":"rollback-001","effect_id":"send-001"}', encoding="utf-8")
        item = record("COMPENSATED", "COMPENSATE", updated_at="2026-10-04T00:00:00+09:00")
        item["compensation_ref"] = "rollback-001"
        item["compensation_evidence"] = {
            "source_kind": "repo_file", "source_id": "rollback-001",
            "path": "compensation.json", "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        }
        return item

    def test_compensated_retry_is_stable_across_metadata_and_reopen(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "COMPENSATE"), root)["pass"])
            item = self.compensated_record(root)
            self.assertTrue(persist(item, root)["pass"])
            first = check(root)
            self.assertTrue(first["pass"], first)
            self.assertFalse(check(root)["pass"])
            item["updated_at"] = "2026-10-04T00:01:00+09:00"
            self.assertTrue(persist(item, root)["pass"])
            refreshed = check(root)
            self.assertFalse(refreshed["pass"])
            self.assertEqual(first["claim_path"], refreshed["claim_path"])
            item.update(execution_status="PLANNED", updated_at="2026-10-04T00:02:00+09:00")
            self.assertTrue(persist(item, root)["pass"])
            self.assertFalse(check(root)["pass"])
            self.assertEqual(len(list((root / "HISTORY/SIDE_EFFECT_CLAIMS").rglob("*.json"))), 1)

    def test_compensation_evidence_fails_closed_before_persist_or_claim(self):
        for defect in ("missing", "tampered", "external", "unbound", "legacy"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                item = self.compensated_record(root)
                if defect == "missing":
                    (root / "compensation.json").unlink()
                elif defect == "tampered":
                    (root / "compensation.json").write_text("changed", encoding="utf-8")
                elif defect == "external":
                    item["compensation_evidence"]["source_kind"] = "other_external"
                elif defect == "unbound":
                    item["compensation_ref"] = "unrelated"
                else:
                    item.pop("compensation_evidence")
                    item["compensation_ref"] = "receipt:does-not-exist"
                self.assertFalse(persist(item, root)["pass"])
                # Legacy CURRENT records must also fail without relying on the writer.
                current, _ = paths(root, item)
                current.parent.mkdir(parents=True, exist_ok=True)
                current.write_bytes(canonical_bytes(dict(item, record_hash=record_hash(item))))
                self.assertFalse(check(root)["pass"])
                self.assertFalse((root / "HISTORY/SIDE_EFFECT_CLAIMS").exists())

    def test_compensation_evidence_revalidated_and_frozen_on_refresh(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = self.compensated_record(root)
            self.assertTrue(persist(item, root)["pass"])
            changed = dict(item, compensation_ref="other", updated_at="2026-10-04T00:01:00+09:00")
            changed["compensation_evidence"] = dict(item["compensation_evidence"], source_id="other")
            self.assertFalse(persist(changed, root)["pass"])
            (root / "compensation.json").unlink()
            self.assertFalse(check(root)["pass"])

    def test_new_compensation_event_allows_next_legitimate_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = self.compensated_record(root)
            self.assertTrue(persist(item, root)["pass"])
            first = check(root)
            self.assertTrue(first["pass"])
            item.update(execution_status="APPLYING", updated_at="2026-10-04T00:01:00+09:00")
            self.assertTrue(persist(item, root)["pass"])
            item.update(execution_status="APPLIED", after_state_ref="receipt:second-send",
                        updated_at="2026-10-04T00:02:00+09:00")
            self.assertTrue(persist(item, root)["pass"])
            evidence = root / "compensation-002.json"
            evidence.write_text('{"event_id":"rollback-002","effect_id":"send-001"}', encoding="utf-8")
            item.update(execution_status="COMPENSATED", compensation_ref="rollback-002",
                        updated_at="2026-10-04T00:03:00+09:00")
            item["compensation_evidence"] = {
                "source_kind": "repo_file", "source_id": "rollback-002",
                "path": evidence.name, "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            }
            self.assertTrue(persist(item, root)["pass"])
            second = check(root)
            self.assertTrue(second["pass"], second)
            self.assertNotEqual(first["claim_path"], second["claim_path"])
            self.assertFalse(check(root)["pass"])

    def test_missing_record_allows_first_execution_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = check(root)
            self.assertTrue(first["pass"], first)
            self.assertEqual(first["decision"], "ALLOW_FIRST_EXECUTION")
            second = check(root)
            self.assertFalse(second["pass"])
            self.assertIn("SIDE_EFFECT_EXECUTION_ALREADY_CLAIMED", second["detected"])

    def test_planned_record_allows_initial_execution_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record(), root)["pass"])
            first = check(root)
            self.assertTrue(first["pass"], first)
            self.assertEqual(first["decision"], "ALLOW_INITIAL_EXECUTION")
            second = check(root)
            self.assertFalse(second["pass"])
            self.assertIn("SIDE_EFFECT_EXECUTION_ALREADY_CLAIMED", second["detected"])

    def test_missing_claim_then_planned_persist_cannot_reauthorize(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = check(root)
            self.assertTrue(first["pass"], first)
            self.assertTrue(persist(record(), root)["pass"])
            second = check(root)
            self.assertFalse(second["pass"])
            self.assertIn("SIDE_EFFECT_EXECUTION_ALREADY_CLAIMED", second["detected"])

    def test_planned_metadata_refresh_does_not_create_new_claim_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record(), root)["pass"])
            first = check(root)
            self.assertTrue(first["pass"], first)
            refreshed = record(updated_at="2026-10-04T00:00:00+09:00")
            self.assertTrue(persist(refreshed, root)["pass"])
            second = check(root)
            self.assertFalse(second["pass"])
            self.assertIn("SIDE_EFFECT_EXECUTION_ALREADY_CLAIMED", second["detected"])

    def test_applied_forbid_blocks_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "FORBID"), root)["pass"])
            result = check(root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_DUPLICATE_EXECUTION_FORBIDDEN", result["detected"])

    def test_applied_idempotent_retry_is_exclusively_claimed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "IDEMPOTENT_RETRY"), root)["pass"])
            first = check(root)
            self.assertTrue(first["pass"], first)
            self.assertEqual(first["decision"], "ALLOW_IDEMPOTENT_RETRY")
            second = check(root)
            self.assertFalse(second["pass"])
            self.assertIn("SIDE_EFFECT_EXECUTION_ALREADY_CLAIMED", second["detected"])

    def test_payload_change_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "IDEMPOTENT_RETRY"), root)["pass"])
            result = check(root, action_payload_hash=HASH_B)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_ACTION_PAYLOAD_HASH_MISMATCH", result["detected"])

    def test_action_kind_and_target_are_bound(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "IDEMPOTENT_RETRY"), root)["pass"])
            changed_action = check(root, action_kind="DELETE")
            self.assertIn("SIDE_EFFECT_ACTION_KIND_MISMATCH", changed_action["detected"])
            changed_target = check(root, target_ref="remote:other")
            self.assertIn("SIDE_EFFECT_TARGET_REF_MISMATCH", changed_target["detected"])

    def test_applying_is_indeterminate_and_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLYING", "IDEMPOTENT_RETRY"), root)["pass"])
            result = check(root)
            self.assertFalse(result["pass"])
            self.assertEqual(result["decision"], "VERIFY_BEFORE_RETRY")

    def test_identity_cannot_change_on_same_effect(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record(), root)["pass"])
            changed = record(updated_at="2026-10-04T00:00:00+09:00")
            changed["action_payload_hash"] = HASH_B
            result = persist(changed, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_ACTION_PAYLOAD_HASH_MISMATCH", result["detected"])

    def test_completed_effect_cannot_roll_back_to_planned(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "FORBID"), root)["pass"])
            changed = record("PLANNED", "FORBID", updated_at="2026-10-04T00:00:00+09:00")
            result = persist(changed, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_STATUS_TRANSITION_INVALID", result["detected"])

    def test_replay_policy_cannot_be_relaxed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "FORBID"), root)["pass"])
            changed = record("APPLIED", "IDEMPOTENT_RETRY", updated_at="2026-10-04T00:00:00+09:00")
            result = persist(changed, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_REPLAY_POLICY_MISMATCH", result["detected"])

    def test_compensation_requires_policy_and_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "FORBID"), root)["pass"])
            changed = record("COMPENSATED", "FORBID", updated_at="2026-10-04T00:00:00+09:00")
            result = persist(changed, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_COMPENSATED_POLICY_INVALID", result["detected"])
            self.assertIn("SIDE_EFFECT_COMPENSATION_EVIDENCE_MISSING", result["detected"])

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertTrue(persist(record("APPLIED", "COMPENSATE"), root)["pass"])
            changed = record("COMPENSATED", "COMPENSATE", updated_at="2026-10-04T00:00:00+09:00")
            result = persist(changed, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_COMPENSATION_EVIDENCE_MISSING", result["detected"])

    def test_corrupted_current_cannot_be_laundered_by_update(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            saved = persist(record(), root)
            self.assertTrue(saved["pass"])
            current = Path(saved["current_path"])
            payload = json.loads(current.read_text(encoding="utf-8"))
            payload["execution_status"] = "FAILED"
            current.write_text(json.dumps(payload), encoding="utf-8")
            changed = record("APPLYING", "FORBID", updated_at="2026-10-04T00:00:00+09:00")
            result = persist(changed, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_CURRENT_INTEGRITY_MISMATCH", result["detected"])

    def test_missing_current_with_history_blocks_first_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            saved = persist(record("APPLIED", "FORBID"), root)
            self.assertTrue(saved["pass"])
            Path(saved["current_path"]).unlink()
            result = check(root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_CURRENT_MISSING_HISTORY_PRESENT", result["detected"])

    def test_history_conflict_never_advances_current(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = record()
            saved = persist(first, root)
            self.assertTrue(saved["pass"])
            current = Path(saved["current_path"])
            before = current.read_bytes()
            changed = record(updated_at=first["updated_at"])
            changed["before_state_ref"] = "different"
            result = persist(changed, root)
            self.assertFalse(result["pass"])
            self.assertEqual(current.read_bytes(), before)

    def test_effect_lock_blocks_concurrent_writer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            current, _ = paths(root, record())
            current.parent.mkdir(parents=True, exist_ok=True)
            lock = current.with_name(current.name + ".lock")
            lock.write_text("held", encoding="utf-8")
            result = persist(record(), root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_CONCURRENT_WRITE", result["detected"])

    def test_forward_history_descendant_blocks_despite_older_timestamp(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            planned = record("PLANNED", "FORBID", updated_at="2026-10-04T00:00:00+09:00")
            saved = persist(planned, root)
            self.assertTrue(saved["pass"])

            applied = record("APPLIED", "FORBID", updated_at="2026-10-03T23:59:00+09:00")
            enriched = dict(applied)
            enriched["record_hash"] = record_hash(applied)
            _, history = paths(root, applied)
            history.parent.mkdir(parents=True, exist_ok=True)
            history.write_bytes(canonical_bytes(enriched))

            result = check(root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_HISTORY_FORWARD_DESCENDANT", result["detected"])

    def test_newer_history_blocks_stale_current_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            planned = record("PLANNED", "FORBID", updated_at="2026-10-03T23:59:00+09:00")
            saved = persist(planned, root)
            self.assertTrue(saved["pass"])
            applied = record("APPLIED", "FORBID", updated_at="2026-10-04T00:00:00+09:00")
            enriched = dict(applied)
            enriched["record_hash"] = record_hash(applied)
            _, history = paths(root, applied)
            history.parent.mkdir(parents=True, exist_ok=True)
            history.write_bytes(canonical_bytes(enriched))
            result = check(root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_CURRENT_STALE_VS_HISTORY", result["detected"])

    def test_original_external_receipt_is_not_compensation_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            applied = record("APPLIED", "COMPENSATE")
            applied["external_receipt"] = "receipt:original-send"
            self.assertTrue(persist(applied, root)["pass"])
            compensated = record(
                "COMPENSATED",
                "COMPENSATE",
                updated_at="2026-10-04T00:00:00+09:00",
            )
            compensated["external_receipt"] = "receipt:original-send"
            result = persist(compensated, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_COMPENSATION_EVIDENCE_MISSING", result["detected"])


    def test_persist_cas_rejects_current_changed_after_history_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            planned = record("PLANNED", "FORBID", updated_at="2026-10-03T23:59:00+09:00")
            saved = persist(planned, root)
            self.assertTrue(saved["pass"])
            current = Path(saved["current_path"])
            next_record = record("APPLYING", "FORBID", updated_at="2026-10-04T00:00:00+09:00")
            original_write = ledger._write_immutable

            def write_then_mutate(path, payload):
                result = original_write(path, payload)
                external = record("PLANNED", "FORBID", updated_at="2026-10-04T00:00:30+09:00")
                enriched = dict(external)
                enriched["record_hash"] = record_hash(external)
                current.write_bytes(canonical_bytes(enriched))
                return result

            with patch.object(ledger, "_write_immutable", side_effect=write_then_mutate):
                result = persist(next_record, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_CURRENT_CAS_MISMATCH", result["detected"])
            guarded = check(root)
            self.assertFalse(guarded["pass"])
            self.assertIn("SIDE_EFFECT_CURRENT_HISTORY_DIVERGENCE", guarded["detected"])

    def test_persist_refuses_to_launder_stale_current_against_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            planned = record("PLANNED", "FORBID", updated_at="2026-10-03T23:59:00+09:00")
            saved = persist(planned, root)
            self.assertTrue(saved["pass"])
            applied = record("APPLIED", "FORBID", updated_at="2026-10-04T00:00:00+09:00")
            enriched = dict(applied)
            enriched["record_hash"] = record_hash(applied)
            _, history = paths(root, applied)
            history.parent.mkdir(parents=True, exist_ok=True)
            history.write_bytes(canonical_bytes(enriched))
            refreshed = record("PLANNED", "FORBID", updated_at="2026-10-04T00:01:00+09:00")
            result = persist(refreshed, root)
            self.assertFalse(result["pass"])
            self.assertIn("SIDE_EFFECT_CURRENT_STALE_VS_HISTORY", result["detected"])

if __name__ == "__main__":
    unittest.main()
