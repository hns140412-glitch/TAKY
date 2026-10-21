#!/usr/bin/env python3
"""No-Chrome regressions for chrome_profile_lifecycle: prelaunch failure, normal cleanup, locked file, leak HOLD."""
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome_profile_lifecycle as lifecycle  # noqa: E402


class ProfileLifecycle(unittest.TestCase):
    def setUp(self):
        # exact isolation: every profile is created inside this private temp root
        self.root = tempfile.TemporaryDirectory(prefix="taky_profile_lifecycle_test_")
        self._saved = tempfile.tempdir
        tempfile.tempdir = self.root.name

    def tearDown(self):
        tempfile.tempdir = self._saved
        self.root.cleanup()

    def residual(self):
        return list(Path(self.root.name).iterdir())

    def test_normal_completion_removes_profile_with_files(self):
        with lifecycle.ChromeProfile("taky_chrome_t_", delay=0.01) as profile:
            (profile.path / "sub").mkdir()
            (profile.path / "sub" / "data.bin").write_bytes(b"x")
            self.assertTrue(profile.path.name.startswith("taky_chrome_t_"))
            self.assertEqual(profile.path.parent, Path(self.root.name))
        self.assertEqual(self.residual(), [])

    def test_prelaunch_failure_cleans_and_keeps_original_error(self):
        with self.assertRaises(FileNotFoundError):
            with lifecycle.ChromeProfile("taky_chrome_t_", delay=0.01) as profile:
                profile.adopt(subprocess.Popen([str(Path(self.root.name) / "missing_chrome.exe")]))
        self.assertEqual(self.residual(), [])

    def test_running_child_is_stopped_before_removal(self):
        holder = "import sys,time;f=open(sys.argv[1],'wb');print('up',flush=True);time.sleep(60)"
        with lifecycle.ChromeProfile("taky_chrome_t_", delay=0.05) as profile:
            proc = profile.adopt(subprocess.Popen([sys.executable, "-c", holder, str(profile.path / "held.bin")],
                                                  stdout=subprocess.PIPE))
            proc.stdout.readline()
            self.assertIsNone(proc.poll())
        self.assertIsNotNone(proc.poll())
        proc.stdout.close()
        self.assertEqual(self.residual(), [])

    @unittest.skipUnless(sys.platform == "win32", "open files only block deletion on Windows")
    def test_locked_file_is_reported_as_leak_hold_not_swallowed(self):
        profile = lifecycle.ChromeProfile("taky_chrome_t_", attempts=3, delay=0.01)
        handle = open(profile.path / "locked.bin", "wb")
        try:
            with self.assertRaises(lifecycle.ProfileLeakError) as caught:
                with profile:
                    pass
            self.assertIn("CHROME_PROFILE_LEAK HOLD", str(caught.exception))
            self.assertIn(profile.path.name, str(caught.exception))
            self.assertNotIn(str(Path(self.root.name).parent), str(caught.exception))
        finally:
            handle.close()
        self.assertTrue(profile.path.exists())  # leftover stayed visible; released lock now allows removal
        profile.problems.clear()
        self.assertEqual(profile.cleanup(), [])
        self.assertEqual(self.residual(), [])

    @unittest.skipUnless(sys.platform == "win32", "open files only block deletion on Windows")
    def test_leak_during_failure_preserves_underlying_error(self):
        profile = lifecycle.ChromeProfile("taky_chrome_t_", attempts=2, delay=0.01)
        handle = open(profile.path / "locked.bin", "wb")
        err = io.StringIO()
        try:
            with redirect_stderr(err), self.assertRaises(ZeroDivisionError):
                with profile:
                    1 / 0
        finally:
            handle.close()
        self.assertIn("CHROME_PROFILE_LEAK HOLD", err.getvalue())
        profile.problems.clear()
        self.assertEqual(profile.cleanup(), [])


if __name__ == "__main__":
    unittest.main()
