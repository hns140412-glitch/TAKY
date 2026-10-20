"""Read-only TAKY cleanup gate: actual six-app HTML->static module graph.

Verifies existing, Git-versioned JS/TS/CSS/JSON dependency files. Does NOT
approve UI, data/audio/image release, bundled runtime or browser E2E.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPS = ("Ready & Set", "Hide & Seek", "Snap & Pop", "Play Camp", "SAVEY", "TAKY-MOBILE")
CODE = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".css"}
HTML_REF = re.compile(
    r"""<(?:script|link|source)\b[^>]*?\b(?:src|href)\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>"']+))""",
    re.IGNORECASE | re.DOTALL,
)
MODULE_REF = re.compile(
    r'''(?:\b(?:import|export)\s+(?:[^;]*?\s+from\s+)?|\brequire\s*\(\s*|\bimport\s*\(\s*)['"]([^'"]+)['"]''',
    re.IGNORECASE,
)
CSS_REF = re.compile(r"""@import\s+(?:url\s*\(\s*)?(?:"([^"]+)"|'([^']+)'|([^\s;)]+))""", re.IGNORECASE)
INLINE_MODULE = re.compile(r"""<script\b(?=[^>]*\btype\s*=\s*(?:"module"|'module'|module))[^>]*>(.*?)</script\s*>""", re.IGNORECASE | re.DOTALL)

def match_value(match):
    return next((x for x in match.groups() if x is not None), "")
COMPUTED_IMPORT = re.compile(r"""\bimport\s*\(\s*[^'"\s]""")


def tracked_files(repo: Path) -> set[str]:
    cp = subprocess.run(
        ("git", "-C", str(repo), "ls-files", "-z"),
        capture_output=True, timeout=35, check=True,
    )
    return {v.decode("utf-8", "replace").replace("\\", "/")
            for v in cp.stdout.split(b"\0") if v}


def modified_tracked_from_head(repo: Path) -> set[str]:
    """Observable HEAD-vs-worktree source drift; does not claim a HEAD-only E2E."""
    cp = subprocess.run(
        ("git", "-C", str(repo), "diff", "--name-only", "-z", "HEAD", "--"),
        capture_output=True, timeout=35, check=True,
    )
    return {v.decode("utf-8", "replace").replace("\\", "/")
            for v in cp.stdout.split(b"\0") if v}


def candidates(repo: Path, caller: Path, spec: str, html_entry=False):
    spec = html.unescape(spec).split("?", 1)[0].split("#", 1)[0]
    if not spec or spec.startswith(("http:", "https:", "//", "data:", "blob:",
                                    "javascript:", "mailto:", "#")):
        return None
    if not html_entry and not spec.startswith(("./", "../", "/")):
        return None
    bases = ([repo / "public" / spec.lstrip("/"), repo / spec.lstrip("/")]
             if html_entry and spec.startswith("/") else
             [repo / spec, repo / "public" / spec] if html_entry else
             [repo / "public" / spec.lstrip("/"), repo / spec.lstrip("/")]
             if spec.startswith("/") else
             [caller.parent / spec])
    paths = []
    for base in bases:
        paths.append(base)
        if base.suffix == ".js":
            paths.extend((base.with_suffix(".ts"), base.with_suffix(".tsx")))
        elif not base.suffix:
            paths.extend(base.with_suffix(ext) for ext in
                         (".js", ".ts", ".tsx", ".mjs", ".json", ".css"))
            paths.extend((base / "index.ts", base / "index.tsx", base / "index.js"))
    return paths


def audit_app(repo: Path):
    root = repo.resolve()
    index = repo / "index.html"
    if not index.is_file():
        raise ValueError("APP_INDEX_MISSING:" + repo.name)
    tracked = tracked_files(repo)
    modified_from_head = modified_tracked_from_head(repo)
    queue = []
    html_body = index.read_text(encoding="utf-8-sig", errors="replace")
    for hit in HTML_REF.finditer(html_body):
        spec = match_value(hit)
        if Path(spec.split("?", 1)[0]).suffix.lower() not in CODE:
            continue
        choices = candidates(repo, index, spec, html_entry=True)
        if choices:
            queue.append((next((p for p in choices if p.is_file()), choices[-1]),
                          "index.html:" + spec))
    # Inline ES module source can import relative runtime files without a src attribute.
    for module in INLINE_MODULE.finditer(html_body):
        for imported in MODULE_REF.finditer(module.group(1)):
            spec = imported.group(1)
            opts = candidates(repo, index, spec, html_entry=True)
            if opts:
                queue.append((next((p for p in opts if p.is_file()), opts[0]),
                              "index.html:inline-module:" + spec))
    visited: set[Path] = set()
    missing = []
    untracked = []
    if "index.html" not in tracked:
        untracked.append("index.html")
    bare = Counter()
    dynamic = 0
    while queue:
        source, referring = queue.pop()
        canonical = source.resolve()
        if not canonical.is_relative_to(root):
            raise ValueError("RUNTIME_REFERENCE_ESCAPES_APP:" + str(source))
        if canonical in visited:
            continue
        visited.add(canonical)
        if not source.is_file():
            missing.append({"path":str(source),"from":referring})
            continue
        relative = canonical.relative_to(root).as_posix()
        if relative not in tracked:
            untracked.append(relative)
        if source.suffix.lower() not in CODE:
            continue
        if source.stat().st_size > 3_000_000:
            raise ValueError("EXECUTABLE_SOURCE_EXCEEDS_REVIEW_BOUND:" + relative)
        body = source.read_text(encoding="utf-8-sig", errors="replace")
        dynamic += len(COMPUTED_IMPORT.findall(body))
        refs = [m.group(1) for m in MODULE_REF.finditer(body)]
        if source.suffix.lower() == ".css":
            for imp in CSS_REF.finditer(body):
                imported = match_value(imp)
                if not imported.startswith((".", "/", "http:", "https:", "//")):
                    imported = "./" + imported
                refs.append(imported)
        for spec in refs:
            if not spec.startswith(("./","../","/")):
                bare[spec.split("/", 1)[0]] += 1
                continue
            opts = candidates(repo, source, spec)
            if opts:
                queue.append((next((p for p in opts if p.is_file()), opts[0]),
                              relative + ":" + spec))
        if len(visited) > 4000:
            raise ValueError("UNBOUNDED_IMPORT_GRAPH:" + repo.name)
    reachable = {p.relative_to(root).as_posix() for p in visited}
    head_drift = sorted(modified_from_head & (reachable | {"index.html"}))
    return {"app":repo.name,
            "reachable_static_source_files":len(visited),
            "head_worktree_source_drift_count":len(head_drift),
            "head_reachable_graph_only":True,
            "head_omitted_imports_and_unscanned_assets_not_proven":True,
            "head_worktree_source_drift_paths":head_drift[:30],
            "head_worktree_parity":("SOURCE_DIFFERS_FROM_HEAD_NO_REPLAY_CLAIM" if head_drift
                                    else "TRACKED_REACHABLE_SOURCES_MATCH_HEAD_NOT_BROWSER_PROVEN"),
            "missing_dependencies":missing[:25],
            "missing_total":len(missing),
            "unversioned_dependencies":sorted(set(untracked))[:30],
            "unversioned_total":len(set(untracked)),
            "dynamic_imports_not_proven":dynamic,
            "external_packages_not_covered":sorted(bare),
            "binary_assets_and_browser_E2E_approved":False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    results = [audit_app(ROOT / app) for app in APPS]
    total_missing = sum(x["missing_total"] for x in results)
    total_untracked = sum(x["unversioned_total"] for x in results)
    head_drift = sum(x["head_worktree_source_drift_count"] for x in results)
    success = total_missing == 0 and total_untracked == 0
    print(json.dumps({"schema":"TAKY_APP_STATIC_DEPENDENCY_CUSTODY_V1",
                      "status":("BLOCK" if not success else
                                "WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD" if head_drift else
                                "PASS_STATIC_ONLY_HEAD_BROWSER_NOT_PROVEN"),
                      "apps_checked":len(results),
                      "source_files_checked":sum(x["reachable_static_source_files"] for x in results),
                      "missing_file_count":total_missing,
                      "git_unversioned_count":total_untracked,
                      "head_worktree_source_drift_count":head_drift,
                      "head_only_browser_reproduction_verified":False,
                      "no_private_held_roots_scanned":True,
                      "runtime_E2E_and_content_approval":"NOT_VERIFIED",
                      "apps":results},ensure_ascii=False))
    # Explicit --check is a guarded HEAD-replay preflight; a source-drift HOLD
    # may still be useful for local development, but cannot pass a release gate.
    return 2 if not success else 3 if args.check and head_drift else 0


if __name__ == "__main__":
    sys.exit(main())
