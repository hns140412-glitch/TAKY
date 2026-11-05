#!/usr/bin/env python3
"""Only synthetic Git path strings; no original files or sync accounts used."""
import unittest
from github_storage_boundary import inspect_paths, reason_for_tracked_path as guard


class GitDataBoundaryTests(unittest.TestCase):
    def test_reject_raw_source_at_root_and_nested(self):
        for path in (
            "SOURCE_ARCHIVE/fullpage.png",
            "work/SOURCE_ARCHIVE/2026/image.jpg",
            "SOURCE_VAULT/original.pdf",
            "nested/TAKY-SOURCE-VAULT/captures/1.png",
            "nested/90_RAW_SOURCE_ARCHIVE/export.txt",
            "app/captures_v04/screenshot.jpg",
            "data/acquired_external/original.html",
            "WORK_OS_SOURCE_CACHE/file.bin",
            "source_reference/runtime/private.json",
            "data/notion_incremental/snapshots/a/blocks.json",
        ):
            with self.subTest(path=path):
                self.assertIsNotNone(guard(path))

    def test_reject_case_and_windows_separators(self):
        self.assertEqual(guard("app\\source_archive\\raw.PNG"),
                         "source_or_data_directory")

    def test_reject_private_data_filenames_at_any_depth(self):
        for name in (
            "INCREMENTAL_QUEUE.json", "INCREMENTAL_SUMMARY.json",
            "INCREMENTAL_ERRORS.json", "MINING_INBOX_HANDOFF.json",
            "SOURCE_ARCHIVE_COMPARE.json", "SOURCE_VAULT_ROUTER_RECEIPT.json",
            "SOURCE_VAULT_SNAPSHOT_EVIDENCE.json",
            "SOURCE_VAULT_EXTERNAL_ACQUISITION.json", "blocks.json",
        ):
            with self.subTest(name=name):
                self.assertEqual(guard("anywhere/" + name), "private_data_receipt")

    def test_local_config_and_secrets_rejected(self):
        for path in (
            ".env", "project/.env.local", "SOURCE_REFERENCE/session.local.json",
            "project/secret.p12", "project/secret.pfx", "private.key",
        ):
            with self.subTest(path=path):
                self.assertIsNotNone(guard(path))

    def test_approved_app_asset_and_pwa_code_paths_are_not_blanket_blocked(self):
        for path in (
            "app/src/main.tsx", "app/public/assets/approved-scene.png",
            "MOBILE_DEV_GATEWAY/runtime_hub.py",
            "PWA/service-worker.js", "PWA/manifest.webmanifest",
            ".github/workflows/build.yml", ".env.example",
            "app/data/default-config.json", "tests/fixtures/example.json",
            "ENFORCEMENT/source_vault_handoff_bridge.py",
            "SOURCE_REFERENCE/git_data_boundary.py",
        ):
            with self.subTest(path=path):
                self.assertIsNone(guard(path))

    def test_mixed_paths_report_counts_not_names(self):
        report = inspect_paths([
            "src/app.ts", "app/SOURCE_ARCHIVE/a.png",
            "SOURCE_REFERENCE/runtime/x.json", "approved/assets/icon.svg",
            "SOURCE_ARCHIVE/b.jpg",
        ])
        self.assertEqual(report, {
            "private_runtime_or_capture_tree": 1,
            "source_or_data_directory": 2,
        })
        self.assertNotIn("a.png", str(report))
        self.assertNotIn("b.jpg", str(report))

    def test_invalid_git_paths_rejected(self):
        for path in ("", "../raw.txt", "data//raw.json", "x/\x00/z"):
            with self.subTest(path=path):
                self.assertEqual(guard(path), "invalid_git_path")


if __name__ == "__main__":
    unittest.main()
