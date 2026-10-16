"""Local trust-boundary tests. No inference and no account access."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from TAKY_TRUSTED_SHELL import resolve_trusted_shell, trusted_shell_candidates


class TrustedShellTests(unittest.TestCase):
    def test_real_shell_is_pinned(self):
        shell = resolve_trusted_shell()
        self.assertIn(shell.casefold(), tuple(str(p).casefold() for p in trusted_shell_candidates()))
        self.assertTrue(Path(shell).is_file())

    def test_prepend_fake_path_does_not_select_it(self):
        with tempfile.TemporaryDirectory() as folder:
            forged = Path(folder) / "pwsh.exe"
            forged.write_bytes(b"not a real signed shell")
            with patch.dict(os.environ, {"PATH":folder + os.pathsep + os.getenv("PATH", "")}):
                actual = resolve_trusted_shell()
            self.assertNotEqual(Path(actual), forged)

    def test_arbitrary_executable_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "pwsh.exe"
            fake.write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError, "NO_PINNED"):
                resolve_trusted_shell(candidates=(fake,))

    def test_current_shell_is_executable_offline(self):
        import subprocess
        shell = resolve_trusted_shell()
        result = subprocess.run(
            [shell, "-NoLogo", "-NoProfile", "-NonInteractive",
             "-Command", "Write-Output PINNED_SHELL_OK"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"PINNED_SHELL_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
