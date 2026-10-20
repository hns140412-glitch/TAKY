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


if __name__=="__main__":
    unittest.main(verbosity=2)
