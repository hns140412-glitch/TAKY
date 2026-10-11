"""TAKY portable, IDE-independent local task/evidence console.

This is a subordinate surface, not a second authority or approval engine.
All external execution is delegated to the existing TAKY2 receipt bridge.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path.home() / ".taky" / "portable-ai"
ID_RE = re.compile(r"^[0-9a-f]{32}$")
MAX_EVIDENCE_BYTES = 10 * 1024 * 1024
ALLOWED_OWNERS = {"CODEX", "CLAUDE"}
STATUSES = {"SUBMITTED", "REVIEW_PENDING", "BLOCKED"}
SECRET_NAMES = (".env", "secret", "token", "credential", "private", "id_rsa", ".pem", ".key")


class PortableError(RuntimeError):
    pass


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def encoded(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_id(value: str) -> str:
    if not ID_RE.fullmatch(str(value)):
        raise PortableError("invalid task/evidence identifier")
    return value


def _path(root: Path, task_id: str) -> Path:
    return root / "tasks" / (safe_id(task_id) + ".json")


def _seal(record: dict) -> dict:
    data = dict(record)
    data.pop("checksum", None)
    data["checksum"] = digest(encoded(data))
    return data


def _read(path: Path) -> dict:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PortableError("unreadable task record") from exc
    if not isinstance(record, dict) or _seal(record) != record:
        raise PortableError("task integrity check failed")
    if path.stem != record.get("task_id"):
        raise PortableError("task identity mismatch")
    return record


def _atomic(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=".pending-", dir=str(path.parent))
    try:
        with os.fdopen(handle, "wb") as output:
            output.write(encoded(_seal(record)) + b"\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


@contextmanager
def _locked(root: Path, task_id: str):
    path = _path(root, task_id).with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PortableError("task is busy; no competing mutation attempted") from exc
    try:
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def submit(root: Path, *, title: str, owner: str, scope: str) -> dict:
    if owner not in ALLOWED_OWNERS:
        raise PortableError("owner must be CODEX or CLAUDE")
    if not title.strip() or not scope.strip() or len(title) > 200 or len(scope) > 1500:
        raise PortableError("title or scope invalid")
    root = root.resolve()
    task_id = uuid.uuid4().hex
    entry = {
        "schema": "TAKY_PORTABLE_TASK_V1",
        "task_id": task_id,
        "title": title.strip(),
        "owner": owner,
        "scope": scope.strip(),
        "status": "SUBMITTED",
        "created_at": stamp(),
        "updated_at": stamp(),
        "evidence": [],
        "execution": None,
        "authority": "TAKY2_EXISTING_GATES",
        "verified": False,
    }
    _atomic(_path(root, task_id), entry)
    return _seal(entry)


def show(root: Path, task_id: str) -> dict:
    path = _path(root.resolve(), task_id)
    if not path.is_file():
        raise PortableError("task does not exist")
    return _read(path)


def tasks(root: Path) -> list[dict]:
    directory = root.resolve() / "tasks"
    if not directory.is_dir():
        return []
    result = []
    for path in directory.glob("*.json"):
        if not ID_RE.fullmatch(path.stem):
            continue
        result.append(_read(path))
    return sorted(result, key=lambda item: item["created_at"], reverse=True)


def _safe_source(value: str, roots: tuple[Path, ...]) -> Path:
    source = Path(value).expanduser().resolve(strict=True)
    if not source.is_file():
        raise PortableError("evidence source must be a regular file")
    if any(part.lower() == ".git" for part in source.parts):
        raise PortableError("Git internals cannot be attached")
    if any(term in source.name.lower() for term in SECRET_NAMES):
        raise PortableError("possible credential file rejected")
    if not any(source.is_relative_to(base.resolve()) for base in roots):
        raise PortableError("source must be inside an explicitly allowed workspace")
    if source.stat().st_size > MAX_EVIDENCE_BYTES:
        raise PortableError("evidence exceeds 10 MiB limit")
    return source


def attach(root: Path, task_id: str, source_file: str, source_root: Path | None = None) -> dict:
    root = root.resolve()
    source = _safe_source(source_file, (REPO, root) if source_root is None else (REPO, root, source_root))
    with _locked(root, task_id):
        entry = show(root, task_id)
        if entry["status"] == "BLOCKED":
            raise PortableError("blocked task cannot accept evidence")
        evidence_id = uuid.uuid4().hex
        destination = root / "artifacts" / task_id / (evidence_id + ".bin")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_file = destination.with_suffix(".pending")
        try:
            with source.open("rb") as reader, temp_file.open("xb") as writer:
                file_hash = hashlib.sha256()
                total = 0
                while True:
                    chunk = reader.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_EVIDENCE_BYTES:
                        raise PortableError("evidence grew beyond limit during copy")
                    file_hash.update(chunk)
                    writer.write(chunk)
                writer.flush()
                os.fsync(writer.fileno())
            os.replace(temp_file, destination)
        finally:
            temp_file.unlink(missing_ok=True)
        evidence = {
            "evidence_id": evidence_id,
            "filename": source.name,
            "sha256": file_hash.hexdigest(),
            "bytes": total,
            "captured_at": stamp(),
        }
        entry["evidence"].append(evidence)
        entry["status"] = "REVIEW_PENDING"
        entry["updated_at"] = stamp()
        _atomic(_path(root, task_id), entry)
        return evidence


def _config_names(path: Path) -> list[str]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        servers = config.get("mcpServers", config.get("mcp_servers", {}))
        return sorted(str(k) for k in servers) if isinstance(servers, dict) else []
    except (OSError, ValueError, AttributeError):
        return []


def doctor(root: Path) -> dict:
    repo_skills = []
    for folder in (REPO / ".agents" / "skills", REPO / ".claude" / "skills"):
        if folder.is_dir():
            for child in folder.iterdir():
                if child.is_dir() and (child / "SKILL.md").is_file():
                    repo_skills.append({"name": child.name, "location": str(folder.relative_to(REPO))})
    workflows = REPO / ".agents" / "workflows"
    return {
        "schema": "TAKY_PORTABLE_DOCTOR_V1",
        "platform": sys.platform,
        "repository": str(REPO),
        "data_root": str(root.resolve()),
        "tools": {name: shutil.which(name) is not None for name in ("python", "git", "node", "codex", "claude")},
        "skills": repo_skills,
        "mcp_server_names_only": _config_names(REPO / ".mcp.json"),
        "legacy_workflows_detected": len(list(workflows.glob("*.md"))) if workflows.is_dir() else 0,
        "external_calls_performed": 0,
        "authority": "EXISTING_TAKY2_NOT_REDEFINED",
        "browser_agent": "NOT_VERIFIED",
        "ide_dependency": "NONE",
    }


def _validate_local_json(path_str: str) -> Path:
    try:
        source = Path(path_str).expanduser().resolve(strict=True)
    except OSError as exc:
        raise PortableError("contract JSON is missing or inaccessible") from exc
    if source.suffix.lower() != ".json" or not source.is_relative_to(REPO):
        raise PortableError("plan and invocation must be repository JSON files")
    if ".git" in source.parts:
        raise PortableError("Git internals not allowed")
    return source


def execute_gated(root: Path, task_id: str, plan_json: str, invocation_json: str) -> dict:
    """Only the existing receipt-bound preflight/execute can run providers."""
    root = root.resolve()
    plan_file = _validate_local_json(plan_json)
    invocation_file = _validate_local_json(invocation_json)
    try:
        plan = json.loads(plan_file.read_text(encoding="utf-8-sig"))
        invocation = json.loads(invocation_file.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise PortableError("invalid execution contract") from exc
    if not isinstance(plan, dict) or not isinstance(invocation, dict) or plan.get("call") != invocation.get("call"):
        raise PortableError("invocation does not match trusted plan call")
    with _locked(root, task_id):
        current = show(root, task_id)
        if current.get("execution") is not None:
            raise PortableError("task already attempted; no automatic retry")
        if current["status"] == "BLOCKED":
            raise PortableError("blocked task")
        # Persist an unknown attempt BEFORE contacting the receipt kernel.
        # A crash/timeout cannot turn an uncertain paid call into a free retry.
        current["execution"] = {"state": "PREFLIGHT_ATTEMPTED_OUTCOME_UNKNOWN", "recorded_at": stamp()}
        current["updated_at"] = stamp()
        _atomic(_path(root, task_id), current)
        command = [sys.executable, "-m", "TAKY2.orchestrator"]
        # This existing kernel provides KEY/CONTEXT/ROUTE/COST/DONE gates.
        first = subprocess.run(command + ["preflight", str(plan_file)], cwd=REPO,
                               stdin=subprocess.DEVNULL, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=30)
        try:
            preflight = json.loads(first.stdout)
        except ValueError as exc:
            raise PortableError("TAKY preflight returned no valid receipt") from exc
        allowed = preflight.get("allowed") is True and bool(preflight.get("receipt_id"))
        result = {"state": "BLOCKED", "receipt_id": None, "recorded_at": stamp()}
        if allowed and first.returncode == 0:
            receipt_id = str(preflight["receipt_id"])
            second = subprocess.run(command + ["execute", receipt_id, str(invocation_file),
                                                 "--executor-id", "TAKY_PORTABLE_AI"],
                                    cwd=REPO, stdin=subprocess.DEVNULL, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=310)
            result = {"state": "UNVERIFIED_EXECUTION_RETURN" if second.returncode == 0 else "EXECUTION_FAILED_OR_UNKNOWN",
                      "receipt_id": receipt_id, "recorded_at": stamp(),
                      "exit_code": second.returncode}
            current["status"] = "REVIEW_PENDING"
        else:
            current["status"] = "BLOCKED"
        current["execution"] = result
        current["updated_at"] = stamp()
        _atomic(_path(root, task_id), current)
        return result


STYLE = """body{font-family:system-ui,-apple-system,sans-serif;margin:32px auto;max-width:1050px;padding:0 20px;color:#142235;background:#f8fafc}
h1{font-size:26px}article{background:white;border:1px solid #dce4eb;border-radius:12px;padding:18px;margin:12px 0}
small{color:#526273}code{word-break:break-word}a{color:#1c5c9c}.head{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}.stat{font-size:13px}
ul{padding-left:20px}li{margin:5px 0} .pill{display:inline-block;background:#edf0f4;padding:4px 8px;border-radius:12px}"""


class Dashboard(BaseHTTPRequestHandler):
    root: Path = DEFAULT_ROOT

    def _response(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            try:
                items = tasks(self.root)
            except PortableError:
                return self._response(500, b"Task integrity error", "text/plain")
            cards = []
            for task in items:
                evidence_html = "".join(
                    "<li><a href='/evidence/{}/{}'>{}</a> <small>SHA-256: {}</small></li>".format(
                        task["task_id"], e["evidence_id"], escape(e["filename"]), e["sha256"]
                    ) for e in task["evidence"]
                )
                cards.append("<article><div class='head'><strong>{}</strong><span class='pill'>{}</span></div>"
                             "<p>{}</p><small>Owner {} · {} · ID <code>{}</code> · VERIFIED: NO</small>"
                             "<ul>{}</ul></article>".format(
                                 escape(task["title"]), escape(task["status"]),
                                 escape(task["scope"]), escape(task["owner"]), escape(task["created_at"]),
                                 task["task_id"], evidence_html))
            body = ("<!doctype html><html lang='ko'><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
                    "<title>TAKY Portable AI</title><style>" + STYLE + "</style><main><h1>TAKY · Portable AI</h1>"
                    "<p>Antigravity 독립 · 로컬 작업 현황 · 증거 기반 검증. 표시된 작업은 승인이나 배포를 의미하지 않습니다.</p>"
                    + "".join(cards or ["<article>등록된 작업이 없습니다.</article>"])
                    + "<small>localhost 전용 · 읽기 전용 · 승인/배포 기능 없음</small></main></html>")
            return self._response(200, body.encode("utf-8"), "text/html; charset=utf-8")
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "evidence" and ID_RE.fullmatch(parts[1]) and ID_RE.fullmatch(parts[2]):
            try:
                task = show(self.root, parts[1])
                matches = [e for e in task["evidence"] if e["evidence_id"] == parts[2]]
                if len(matches) != 1:
                    raise PortableError("evidence not registered")
                file = self.root.resolve() / "artifacts" / parts[1] / (parts[2] + ".bin")
                data = file.read_bytes()
                if digest(data) != matches[0]["sha256"]:
                    raise PortableError("artifact integrity mismatch")
            except (PortableError, OSError):
                return self._response(404, b"Evidence unavailable", "text/plain")
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", "attachment; filename=evidence.bin")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return self.wfile.write(data)
        return self._response(404, b"Not found", "text/plain")

    def do_POST(self) -> None:
        return self._response(405, b"Read-only", "text/plain")

    def log_message(self, format: str, *args: object) -> None:
        pass


def serve(root: Path, port: int = 8787) -> None:
    if not 1025 <= port <= 65535:
        raise PortableError("port must be 1025..65535")
    class LocalDashboard(Dashboard):
        pass
    LocalDashboard.root = root.resolve()
    server = ThreadingHTTPServer(("127.0.0.1", port), LocalDashboard)
    print(f"TAKY Portable AI: http://127.0.0.1:{port}/", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TAKY portable AI; no IDE dependency")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="local task store (outside Git by default)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    create = sub.add_parser("submit")
    create.add_argument("--title", required=True)
    create.add_argument("--owner", choices=sorted(ALLOWED_OWNERS), required=True)
    create.add_argument("--scope", required=True)
    sub.add_parser("list")
    detail = sub.add_parser("show")
    detail.add_argument("task_id")
    ev = sub.add_parser("evidence")
    ev.add_argument("task_id")
    ev.add_argument("--file", required=True)
    ev.add_argument("--source-root", type=Path)
    run = sub.add_parser("execute")
    run.add_argument("task_id")
    run.add_argument("--plan-json", required=True)
    run.add_argument("--invocation-json", required=True)
    page = sub.add_parser("serve")
    page.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            serve(args.root, args.port)
            return 0
        if args.command == "doctor":
            output = doctor(args.root)
        elif args.command == "submit":
            output = submit(args.root, title=args.title, owner=args.owner, scope=args.scope)
        elif args.command == "list":
            output = tasks(args.root)
        elif args.command == "show":
            output = show(args.root, args.task_id)
        elif args.command == "evidence":
            output = attach(args.root, args.task_id, args.file, args.source_root)
        else:
            output = execute_gated(args.root, args.task_id, args.plan_json, args.invocation_json)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except (PortableError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
