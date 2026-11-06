"""Regression: local worktree code success must not be called Git HEAD replay proof."""
from __future__ import annotations
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import taky_live_app_dependency_guard as guard


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(f"git {args}: {p.stderr[-1000:]}")
    return p.stdout.strip()


class WorktreeVsHeadProvenanceTests(unittest.TestCase):
    def test_head_reachable_sources_are_distinct_from_worktree(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_HEAD_ONLY_GUARD_") as td:
            r = Path(td)
            git(r, "init", "-q")
            git(r, "config", "user.name", "TAKY Synthetic QA")
            git(r, "config", "user.email", "taky-qa@example.invalid")
            (r/"index.html").write_text('<script src="./lesson.js"></script>\n', encoding="utf8")
            (r/"lesson.js").write_text("window.lesson='BASE';\n",encoding="utf8")
            git(r, "add", "index.html", "lesson.js")
            git(r, "commit", "-q", "-m", "fixture")
            original_head = git(r, "rev-parse", "HEAD")
            initial = guard.audit_app(r)
            self.assertEqual(initial["missing_total"],0)
            self.assertEqual(initial["unversioned_total"],0)
            self.assertEqual(initial["head_worktree_source_drift_count"],0)
            self.assertEqual(initial["head_worktree_parity"],
                             "TRACKED_REACHABLE_SOURCES_MATCH_HEAD_NOT_BROWSER_PROVEN")
            (r/"lesson.js").write_text("window.lesson='WORKTREE_CHANGED';\n",encoding="utf8")
            modified = guard.audit_app(r)
            self.assertEqual(modified["missing_total"],0)
            self.assertEqual(modified["unversioned_total"],0)
            self.assertEqual(modified["head_worktree_source_drift_paths"],["lesson.js"])
            self.assertEqual(modified["head_worktree_parity"],"SOURCE_DIFFERS_FROM_HEAD_NO_REPLAY_CLAIM")
            (r/"index.html").write_text('<script src="./lesson.js"></script><script src="./extra.js"></script>\n',encoding="utf8")
            (r/"extra.js").write_text("window.extra=1;\n",encoding="utf8")
            index_changed=guard.audit_app(r)
            self.assertEqual(index_changed["head_worktree_source_drift_paths"],["index.html","lesson.js"])
            self.assertEqual(index_changed["unversioned_dependencies"],["extra.js"])
            self.assertEqual(index_changed["missing_total"],0)
            self.assertEqual(git(r,"rev-parse","HEAD"),original_head)
            # Read-only analyzer preserves the original untracked file as-is.
            self.assertEqual((r/"extra.js").read_text(encoding="utf8"),"window.extra=1;\n")

    def test_deleted_runtime_dependency_blocks_even_with_clean_git_index(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_MISSING_GUARD_") as td:
            r=Path(td)
            git(r,"init","-q")
            git(r,"config","user.name","TAKY Synthetic QA")
            git(r,"config","user.email","taky-qa@example.invalid")
            (r/"index.html").write_text('<script src="./missing.js"></script>\n',encoding="utf8")
            git(r,"add","index.html");git(r,"commit","-q","-m","fixture")
            v=guard.audit_app(r)
            self.assertEqual(v["missing_total"],1)
            self.assertEqual(v["head_worktree_source_drift_count"],0)
            self.assertEqual(v["unversioned_total"],0)

    def test_unquoted_html_inline_import_and_css_files_are_real_local_references(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_PARSER_NEGATIVE_") as td:
            r=Path(td)
            git(r,"init","-q")
            git(r,"config","user.name","TAKY Synthetic QA")
            git(r,"config","user.email","taky-qa@example.invalid")
            (r/"index.html").write_text(
                '<script src=./base.js></script><script type=module>import "./nested.js";</script>'
                '<link href="./main.css" rel="stylesheet">\n',encoding="utf8")
            (r/"base.js").write_text("window.base=true;\n",encoding="utf8")
            (r/"main.css").write_text('@import "theme.css";\n@import url(./widget.css);\n',
                                      encoding="utf8")
            git(r,"add","index.html","base.js","main.css")
            git(r,"commit","-q","-m","fixture")
            audit=guard.audit_app(r)
            missed={Path(x["path"]).name for x in audit["missing_dependencies"]}
            self.assertEqual(missed,{"nested.js","theme.css","widget.css"})
            self.assertEqual(audit["unversioned_total"],0)
            for name in missed:
                (r/name).write_text("/* test source */\n",encoding="utf8")
            audit=guard.audit_app(r)
            self.assertEqual(audit["missing_total"],0)
            self.assertEqual(set(audit["unversioned_dependencies"]),missed)

    def test_entrypoint_untracked_and_root_vs_public_precedence(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_PATH_NEGATIVE_") as td:
            r=Path(td)
            git(r,"init","-q")
            git(r,"config","user.name","TAKY Synthetic QA")
            git(r,"config","user.email","taky-qa@example.invalid")
            (r/"index.html").write_text('<script src=./src.js></script>\n',encoding="utf8")
            (r/"src.js").write_text("window.root=true;\n",encoding="utf8")
            (r/"public").mkdir()
            (r/"public"/"src.js").write_text("window.public=true;\n",encoding="utf8")
            git(r,"add","src.js","public/src.js");git(r,"commit","-q","-m","fixture")
            choices=guard.candidates(r,r/"index.html","./src.js",html_entry=True)
            self.assertEqual(choices[0],r/"src.js")
            result=guard.audit_app(r)
            self.assertEqual(result["unversioned_dependencies"],["index.html"])
            self.assertEqual(result["missing_total"],0)

    def test_check_cli_fails_on_head_replay_hold_but_diagnostic_still_runs(self):
        import contextlib
        import io
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix="TAKY_GUARD_CLI_") as td:
            r=Path(td)
            a=r/"fixture"
            a.mkdir()
            git(a,"init","-q")
            git(a,"config","user.name","TAKY Synthetic QA")
            git(a,"config","user.email","taky-qa@example.invalid")
            (a/"index.html").write_text('<script src="./lesson.js"></script>\n',encoding="utf8")
            (a/"lesson.js").write_text("window.lesson=1;\n",encoding="utf8")
            git(a,"add","index.html","lesson.js");git(a,"commit","-q","-m","fixture")
            with patch.object(guard,"ROOT",r),patch.object(guard,"APPS",("fixture",)):
                with patch.object(sys,"argv",["guard","--check"]),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(guard.main(),0)
                (a/"lesson.js").write_text("window.lesson=2;\n",encoding="utf8")
                with patch.object(sys,"argv",["guard"]),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(guard.main(),0)
                with patch.object(sys,"argv",["guard","--check"]),contextlib.redirect_stdout(io.StringIO()) as log:
                    self.assertEqual(guard.main(),3)
                self.assertIn("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD",log.getvalue())


def make_repo(td: str) -> Path:
    r = Path(td)
    git(r, "init", "-q")
    git(r, "config", "user.name", "TAKY Synthetic QA")
    git(r, "config", "user.email", "taky-qa@example.invalid")
    return r


def write(r: Path, rel: str, text: str) -> None:
    (r / rel).parent.mkdir(parents=True, exist_ok=True)
    (r / rel).write_text(text, encoding="utf8")


class RuntimeAssetCustodyTests(unittest.TestCase):
    """Synthetic fixtures only: prove static custody accounting, not browser QA."""
    CREW = "vendor/taky/explorer-crew/"

    SW_BODY = "const {n}=[{items}];\nself.addEventListener('install',e=>e.waitUntil(caches.open('v').then(c=>c.addAll({n}))));\n"

    def sw_fixture(self, r: Path, with_json: bool):
        write(r, "index.html", f'<script src="./{self.CREW}crew.js"></script><script src="./app.js"></script>\n')
        write(r, self.CREW + "crew.js", "window.crew=1;\n")
        write(r, "app.js", "navigator.serviceWorker.register('./sw.js');\n")
        write(r, "sw.js", self.SW_BODY.format(n="A", items=f"'./{self.CREW}registry-v1.json'"))
        if with_json:
            write(r, self.CREW + "registry-v1.json", "{}\n")
        git(r, "add", "index.html", self.CREW + "crew.js", "app.js", "sw.js")
        git(r, "commit", "-q", "-m", "fixture")

    def png_fixture(self, r: Path, count=24, register=True, create=True, extra=""):
        write(r, "index.html", '<script src="./app.js"></script>\n')
        write(r, "app.js", "navigator.serviceWorker.register('./sw.js');\n" if register else "window.x=1;\n")
        names = [f"characters/ui_cutouts/c{i:02d}.png" for i in range(count)]
        items = ",".join(["'./'"] + [f"'./{n}'" for n in names] + ["'./font.woff2'"]) + extra
        write(r, "sw.js", self.SW_BODY.format(n="CORE", items=items))
        if create:
            for n in names:
                write(r, n, "png\n")
        git(r, "add", "index.html", "app.js", "sw.js")
        git(r, "commit", "-q", "-m", "fixture")
        return names

    def test_registered_sw_untracked_pngs_block_then_tracked_pass(self):
        import contextlib
        import io
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_PNG_") as td:
            root = Path(td)
            app = root / "fixture"
            app.mkdir()
            r = make_repo(str(app))
            names = self.png_fixture(r)
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_unversioned_total"], 24)
            self.assertEqual(a["runtime_asset_files_checked"], 25)  # 24 png + sw.js; './' and woff2 skipped
            self.assertEqual(a["runtime_asset_missing_total"], 0)
            self.assertEqual(a["unversioned_total"], 0)
            self.assertEqual(a["runtime_asset_custody"], "FAIL_CLOSED_NOT_HEAD_REPLAY")
            self.assertFalse(a["binary_assets_and_browser_E2E_approved"])
            with patch.object(guard, "ROOT", root), patch.object(guard, "APPS", ("fixture",)), \
                    patch.object(sys, "argv", ["guard"]), contextlib.redirect_stdout(io.StringIO()) as log:
                self.assertEqual(guard.main(), 2)
            self.assertIn('"status": "BLOCK"', log.getvalue())
            self.assertTrue(all((r / n).is_file() for n in names))  # never deleted or staged
            self.assertEqual(git(r, "diff", "--cached", "--name-only"), "")
            git(r, "add", "characters")
            git(r, "commit", "-q", "-m", "assets")
            b = guard.audit_app(r)
            self.assertEqual(b["runtime_asset_unversioned_total"], 0)
            self.assertEqual(b["runtime_asset_custody"], "TRACKED_NOT_BROWSER_PROVEN")

    def test_registered_sw_missing_png_blocks(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_PNG_MISSING_") as td:
            r = make_repo(td)
            self.png_fixture(r, count=3, create=False)
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_missing_total"], 3)
            self.assertEqual(a["runtime_asset_custody"], "FAIL_CLOSED_NOT_HEAD_REPLAY")

    def test_dormant_sw_without_js_registration_is_ignored(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_DORMANT_") as td:
            r = make_repo(td)
            self.png_fixture(r, count=3, register=False)
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_files_checked"], 0)
            self.assertEqual(a["runtime_asset_missing_total"], 0)
            self.assertEqual(a["runtime_asset_unversioned_total"], 0)

    def test_unsafe_sw_entry_and_oversized_precache_rejected(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_UNSAFE_") as td:
            r = make_repo(td)
            self.png_fixture(r, count=1, extra=",'../outside.png'")
            with self.assertRaises(ValueError) as ctx:
                guard.audit_app(r)
            self.assertIn("RUNTIME_REFERENCE_ESCAPES_APP", str(ctx.exception))
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_BOUND_") as td:
            r = make_repo(td)
            self.png_fixture(r, count=guard.SW_MAX_ENTRIES + 1, create=False)
            with self.assertRaises(ValueError) as ctx:
                guard.audit_app(r)
            self.assertIn("SERVICE_WORKER_PRECACHE_EXCEEDS_BOUND", str(ctx.exception))

    def test_untracked_sw_json_blocks_until_committed(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_JSON_") as td:
            r = make_repo(td)
            self.sw_fixture(r, True)
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_unversioned"], [self.CREW + "registry-v1.json"])
            self.assertEqual(a["runtime_asset_custody"], "FAIL_CLOSED_NOT_HEAD_REPLAY")
            self.assertEqual(a["unversioned_total"], 0)  # code counter stays distinct
            self.assertEqual(a["reachable_static_source_files"], 2)
            self.assertTrue((r / self.CREW / "registry-v1.json").is_file())  # never deleted
            git(r, "add", self.CREW + "registry-v1.json")
            git(r, "commit", "-q", "-m", "assets")
            b = guard.audit_app(r)
            self.assertEqual(b["runtime_asset_unversioned_total"], 0)
            self.assertEqual(b["runtime_asset_files_checked"], 2)  # registry json + sw.js
            self.assertEqual(b["runtime_asset_custody"], "TRACKED_NOT_BROWSER_PROVEN")

    def test_missing_sw_json_blocks_and_cli_status_is_block(self):
        import contextlib
        import io
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_MISSING_") as td:
            root = Path(td)
            app = root / "fixture"
            app.mkdir()
            r = make_repo(str(app))
            self.sw_fixture(r, False)
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_missing_total"], 1)
            with patch.object(guard, "ROOT", root), patch.object(guard, "APPS", ("fixture",)), \
                    patch.object(sys, "argv", ["guard"]), contextlib.redirect_stdout(io.StringIO()) as log:
                self.assertEqual(guard.main(), 2)
            self.assertIn('"status": "BLOCK"', log.getvalue())

    def test_registered_sw_edit_is_head_drift_and_check_fails(self):
        import contextlib
        import io
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_HEAD_DRIFT_") as td:
            root = Path(td)
            app = root / "fixture"
            app.mkdir()
            r = make_repo(str(app))
            self.sw_fixture(r, False)  # HEAD sw.js precaches a JSON that does not exist
            write(r, "sw.js", self.SW_BODY.format(n="A", items=""))  # worktree removes it
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_registered_service_workers"], ["sw.js"])
            self.assertEqual(a["runtime_asset_missing_total"], 0)
            self.assertEqual(a["head_worktree_source_drift_paths"], ["sw.js"])
            self.assertEqual(a["head_worktree_source_drift_count"], 1)
            self.assertEqual(a["head_worktree_parity"], "SOURCE_DIFFERS_FROM_HEAD_NO_REPLAY_CLAIM")
            with patch.object(guard, "ROOT", root), patch.object(guard, "APPS", ("fixture",)):
                with patch.object(sys, "argv", ["guard", "--check"]), \
                        contextlib.redirect_stdout(io.StringIO()) as log:
                    self.assertEqual(guard.main(), 3)
                self.assertIn("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", log.getvalue())

    def test_registered_sw_missing_on_disk_stays_blocked_and_listed(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_ABSENT_") as td:
            r = make_repo(td)
            self.sw_fixture(r, False)
            (r / "sw.js").unlink()
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_missing_total"], 1)
            self.assertEqual(a["runtime_registered_service_workers"], ["sw.js"])
            self.assertEqual(a["head_worktree_source_drift_paths"], ["sw.js"])

    def test_dormant_sw_edit_is_not_head_drift(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_DORMANT_DRIFT_") as td:
            r = make_repo(td)
            self.png_fixture(r, count=1, register=False)
            write(r, "sw.js", self.SW_BODY.format(n="CORE", items="'./other.png'"))
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_registered_service_workers"], [])
            self.assertEqual(a["head_worktree_source_drift_count"], 0)

    def test_sw_json_ignored_without_active_registration(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_SW_NOJS_") as td:
            r = make_repo(td)
            write(r, "index.html", "<p>no scripts</p>\n")
            write(r, "sw.js", self.SW_BODY.format(n="A", items=f"'./{self.CREW}registry-v1.json'"))
            write(r, self.CREW + "registry-v1.json", "{}\n")
            git(r, "add", "index.html", "sw.js")
            git(r, "commit", "-q", "-m", "fixture")
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_files_checked"], 0)
            self.assertEqual(a["runtime_asset_missing_total"], 0)

    def ocr_fixture(self, r: Path, referenced: bool):
        body = ('export const cfg={workerPath:"/ocr/worker/worker.min.js",'
                'corePath:"/ocr/core/",langPath:"/ocr/lang/"};\n' if referenced
                else "export const cfg={};\n")
        write(r, "index.html", '<script type="module" src="./src/runtime/local-ocr-provider.ts"></script>\n')
        write(r, "src/runtime/local-ocr-provider.ts", body)
        write(r, "public/ocr/worker/worker.min.js", "//w\n")
        write(r, "public/ocr/core/core.wasm.js", "//c\n")
        write(r, "public/ocr/lang/eng.traineddata.gz", "L\n")
        git(r, "add", "index.html", "src/runtime/local-ocr-provider.ts", "public/ocr/worker/worker.min.js")
        git(r, "commit", "-q", "-m", "fixture")

    def test_untracked_ocr_core_and_lang_block(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_OCR_UNTRACKED_") as td:
            r = make_repo(td)
            self.ocr_fixture(r, True)
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_files_checked"], 3)
            self.assertEqual(a["runtime_asset_unversioned"],
                             ["public/ocr/core/core.wasm.js", "public/ocr/lang/eng.traineddata.gz"])
            self.assertEqual(a["runtime_asset_missing_total"], 0)
            self.assertEqual(a["runtime_asset_custody"], "FAIL_CLOSED_NOT_HEAD_REPLAY")
            (r / "public/ocr/lang/eng.traineddata.gz").unlink()
            b = guard.audit_app(r)
            self.assertEqual(b["runtime_asset_missing_total"], 1)

    def test_no_ocr_reference_has_no_ocr_requirement(self):
        with tempfile.TemporaryDirectory(prefix="TAKY_OCR_ABSENT_") as td:
            r = make_repo(td)
            self.ocr_fixture(r, False)
            a = guard.audit_app(r)
            self.assertEqual(a["runtime_asset_files_checked"], 0)
            self.assertEqual(a["runtime_asset_missing_total"], 0)
            self.assertEqual(a["runtime_asset_unversioned_total"], 0)


if __name__=="__main__":
    unittest.main(verbosity=2)
