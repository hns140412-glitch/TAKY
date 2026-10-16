"""Offline tests for pinned TAKY2 import provenance."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2, ROOT


class TrustedKernelImportTests(unittest.TestCase):
    def test_does_not_prepend_untrusted_repo_to_sys_path(self):
        existing = tuple(sys.path)
        module = ensure_trusted_taky2()
        self.assertEqual(tuple(sys.path), existing)
        self.assertEqual(str(module.__file__).casefold(),
                         str((ROOT / "TAKY2" / "__init__.py").resolve()).casefold())

    def test_rejects_preloaded_forged_package(self):
        forged = SimpleNamespace(__file__=r"C:\untrusted\TAKY2\__init__.py")
        with patch.dict(sys.modules, {"TAKY2": forged}):
            with self.assertRaisesRegex(RuntimeError, "UNTRUSTED_TAKY2"):
                ensure_trusted_taky2()


if __name__ == "__main__":
    unittest.main()
