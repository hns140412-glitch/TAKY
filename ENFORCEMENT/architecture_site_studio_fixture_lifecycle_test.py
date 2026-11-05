"""No-Chrome regression for the Site Studio test fixture lifecycle (OS temp, bounded cleanup, explicit HOLD)."""
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import architecture_site_studio_browser_test as B  # noqa: E402

TMP = Path(tempfile.gettempdir())
PREFIX = "site_studio_lifecycle_probe_"


def temp_count():
    return len([p for p in TMP.glob("site_studio_*")])


def root_count():
    return len([p for p in B.ROOT.glob("site_studio_test_*")])


def run(case):
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(case).run(result)
    return result


class Counts:
    def __enter__(self):
        self.root, self.temp = root_count(), temp_count()
        return self

    def __exit__(self, *exc):
        assert root_count() == self.root, "repo-root site_studio_test_* count changed"
        assert temp_count() == self.temp, "OS-temp site_studio_* count changed"
        return False


class FixtureLifecycle(unittest.TestCase):
    def test_success_removes_dir_in_os_temp(self):
        seen = []

        class Case(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                cls.tmp = B.own_fixture_dir(cls, PREFIX)
                seen.append(cls.tmp)

            def test_ok(self):
                (self.tmp / "report.json").write_text("{}")

        with Counts():
            result = run(Case)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(seen[0].parent.resolve(), TMP.resolve())
        self.assertFalse(seen[0].exists())

    def test_test_exception_preserved_and_dir_removed(self):
        seen = []

        class Case(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                seen.append(B.own_fixture_dir(cls, PREFIX))

            def test_boom(self):
                raise ValueError("original")

        with Counts():
            result = run(Case)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("ValueError: original", result.errors[0][1])
        self.assertFalse(seen[0].exists())

    def test_setup_exception_still_cleans(self):
        seen = []

        class Case(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                seen.append(B.own_fixture_dir(cls, PREFIX))
                raise RuntimeError("setup original")

            def test_never(self):
                pass

        with Counts():
            result = run(Case)
        self.assertIn("RuntimeError: setup original", result.errors[0][1])
        self.assertFalse(seen[0].exists())

    def test_server_stops_before_directory_removal(self):
        order = []

        class Case(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                cls.tmp = B.own_fixture_dir(cls, PREFIX)
                cls.addClassCleanup(lambda: order.append(("server", cls.tmp.exists())))

            def test_ok(self):
                pass

        with Counts():
            run(Case)
        self.assertEqual(order, [("server", True)])

    def test_locked_cleanup_is_explicit_hold_and_keeps_original_error(self):
        seen = []

        class Case(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                cls.tmp = B.own_fixture_dir(cls, PREFIX)
                seen.append(cls.tmp)

            def test_boom(self):
                raise ValueError("original")

        before = temp_count()
        try:
            with mock.patch.object(B.shutil, "rmtree", side_effect=PermissionError("locked")), \
                    mock.patch.object(B.time, "sleep"):
                result = run(Case)
            texts = "\n".join(text for _, text in result.errors)
            self.assertIn("ValueError: original", texts)
            self.assertIn("FIXTURE_LEAK HOLD", texts)
            self.assertTrue(seen[0].exists())  # residue is surfaced, not hidden
        finally:
            shutil.rmtree(seen[0], ignore_errors=True)  # probe-owned directory only
        self.assertEqual(temp_count(), before)

    def test_bounded_retry_then_success(self):
        path = B.make_fixture_dir(PREFIX)
        real, calls = shutil.rmtree, []

        def flaky(p, *a, **k):
            calls.append(p)
            if len(calls) < 3:
                raise PermissionError("locked")
            return real(p, *a, **k)

        with mock.patch.object(B.shutil, "rmtree", side_effect=flaky), mock.patch.object(B.time, "sleep"):
            B.remove_fixture_dir(path)
        self.assertEqual(len(calls), 3)
        self.assertFalse(path.exists())

    def test_browser_module_has_no_repo_root_or_silent_cleanup(self):
        source = Path(B.__file__).read_text(encoding="utf-8")
        self.assertNotIn("dir=ROOT", source)
        self.assertNotIn("ignore_errors=True", source)


if __name__ == "__main__":
    unittest.main()
