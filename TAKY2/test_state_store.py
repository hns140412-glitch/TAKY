import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from TAKY2.state_store import (
    StateConflictError,
    StateIntegrityError,
    authority_digest,
    initialize_runtime,
    load_bundle,
    load_or_create_runtime_key,
    save_runtime,
)


KEY = b"k" * 32


class StateStoreTests(unittest.TestCase):
    def test_runtime_key_is_written_byte_exact_on_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime.key"
            raw = b"A" * 10 + b"\n" + b"B" * 21
            with patch("TAKY2.state_store.secrets.token_bytes", return_value=raw):
                key = load_or_create_runtime_key(path)
            self.assertEqual(key, raw)
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(len(path.read_bytes()), 32)

    def make_files(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        authority = {"key": {"x": 1}}
        runtime_example = {
            "runtime_version": 1,
            "authority_digest": "",
            "runtime": {},
            "context": {},
            "route_ledgers": {},
            "preflight_receipts": {},
            "active_attempts": {},
            "execution_outcomes": {},
            "evidence_registry": {},
            "completion_registry": {},
            "consumed_approvals": {},
            "user_events": {},
        }
        ap = root / "authority.json"
        rp = root / "runtime.json"
        ep = root / "runtime.example.json"
        anchor = root / "runtime.anchor.json"
        lock = root / "runtime.lock"
        ap.write_text(json.dumps(authority), encoding="utf-8")
        ep.write_text(json.dumps(runtime_example), encoding="utf-8")
        initialize_runtime(
            ap,
            ep,
            rp,
            runtime_key=KEY,
            anchor_path=anchor,
        )
        return tmp, ap, rp, ep, anchor, lock, authority_digest(authority)

    def test_runtime_hmac_tamper_fails_closed(self):
        tmp, ap, rp, ep, anchor, lock, digest = self.make_files()
        try:
            stored = json.loads(rp.read_text(encoding="utf-8"))
            stored["runtime_version"] = 99
            rp.write_text(json.dumps(stored), encoding="utf-8")
            with self.assertRaises(StateIntegrityError):
                load_bundle(
                    ap, rp, runtime_key=KEY, anchor_path=anchor
                )
        finally:
            tmp.cleanup()

    def test_authority_digest_mismatch_fails_closed(self):
        tmp, ap, rp, ep, anchor, lock, digest = self.make_files()
        try:
            ap.write_text(json.dumps({"key": {"x": 2}}), encoding="utf-8")
            with self.assertRaises(StateIntegrityError):
                load_bundle(
                    ap, rp, runtime_key=KEY, anchor_path=anchor
                )
        finally:
            tmp.cleanup()

    def test_initialize_runtime_signs_and_anchors_state(self):
        tmp, ap, rp, ep, anchor, lock, digest = self.make_files()
        try:
            trusted, loaded, loaded_digest = load_bundle(
                ap, rp, runtime_key=KEY, anchor_path=anchor
            )
            self.assertEqual(loaded_digest, digest)
            self.assertEqual(loaded["runtime_version"], 1)
            self.assertTrue(anchor.exists())
        finally:
            tmp.cleanup()

    def test_save_runtime_increments_version_and_anchor(self):
        tmp, ap, rp, ep, anchor, lock, digest = self.make_files()
        try:
            _, runtime, _ = load_bundle(
                ap, rp, runtime_key=KEY, anchor_path=anchor
            )
            updated = save_runtime(
                runtime,
                expected_version=1,
                authority_digest_value=digest,
                runtime_path=rp,
                lock_path=lock,
                runtime_key=KEY,
                anchor_path=anchor,
            )
            self.assertEqual(updated["runtime_version"], 2)
            _, loaded, _ = load_bundle(
                ap, rp, runtime_key=KEY, anchor_path=anchor
            )
            self.assertEqual(loaded["runtime_version"], 2)
        finally:
            tmp.cleanup()

    def test_compare_and_swap_rejects_stale_writer(self):
        tmp, ap, rp, ep, anchor, lock, digest = self.make_files()
        try:
            _, runtime, _ = load_bundle(
                ap, rp, runtime_key=KEY, anchor_path=anchor
            )
            save_runtime(
                runtime,
                expected_version=1,
                authority_digest_value=digest,
                runtime_path=rp,
                lock_path=lock,
                runtime_key=KEY,
                anchor_path=anchor,
            )
            with self.assertRaises(StateConflictError):
                save_runtime(
                    runtime,
                    expected_version=1,
                    authority_digest_value=digest,
                    runtime_path=rp,
                    lock_path=lock,
                    runtime_key=KEY,
                    anchor_path=anchor,
                )
        finally:
            tmp.cleanup()

    def test_signed_runtime_rollback_is_rejected_by_external_anchor(self):
        tmp, ap, rp, ep, anchor, lock, digest = self.make_files()
        try:
            old_runtime_bytes = rp.read_bytes()
            _, runtime, _ = load_bundle(
                ap, rp, runtime_key=KEY, anchor_path=anchor
            )
            save_runtime(
                runtime,
                expected_version=1,
                authority_digest_value=digest,
                runtime_path=rp,
                lock_path=lock,
                runtime_key=KEY,
                anchor_path=anchor,
            )
            rp.write_bytes(old_runtime_bytes)
            with self.assertRaises(StateIntegrityError):
                load_bundle(
                    ap, rp, runtime_key=KEY, anchor_path=anchor
                )
        finally:
            tmp.cleanup()

    def test_delete_runtime_cannot_reinitialize_when_anchor_exists(self):
        tmp, ap, rp, ep, anchor, lock, digest = self.make_files()
        try:
            rp.unlink()
            with self.assertRaises(StateConflictError):
                initialize_runtime(
                    ap,
                    ep,
                    rp,
                    runtime_key=KEY,
                    anchor_path=anchor,
                )
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
