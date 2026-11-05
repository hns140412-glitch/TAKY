#!/usr/bin/env python3
"""Loopback-only bridge for the ArchiGrow site studio.

It adds no generator. Every export calls ARCHIGROW_SITE_ANALYSIS_REPORT.build()
with the option the browser has selected, so PPTX/HTML/SVG always match the
on-screen selection. Nothing leaves 127.0.0.1 and no network service is used.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import re
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
FORMATS = {
    "pptx": ("site_analysis.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    "html": ("site_analysis.html", "text/html; charset=utf-8"),
    "svg": ("site_map.svg", "image/svg+xml"),
    "manifest": ("analysis_manifest.json", "application/json; charset=utf-8"),
}


NOT_BOUND = "SITE_SOURCE_NOT_BOUND"
ABS_PATH = re.compile(r"(?:[A-Za-z]:[\/]|\\|/(?:Users|home|mnt)/)(?:[^\/:*?\"<>|\r\n]+[\/])*[^\s\/:*?\"<>|,;)']*")
OPTIONAL_LAYERS = (("context", "주변 컨텍스트(context)"), ("solar", "일조 분석(solar)"), ("massing", "매스 옵션(massing)"))
CERTIFIED_ROLES = ()  # Manifest source-role text alone never proves independent certification.


def _safe_text(value, limit=300):
    """User-controlled manifest text: absolute paths removed, length bounded."""
    return ABS_PATH.sub("[경로 생략]", str(value))[:limit]


def load_report():
    spec = importlib.util.spec_from_file_location("archigrow_site_report", HERE / "ARCHIGROW_SITE_ANALYSIS_REPORT.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Studio:
    def __init__(self, project_id, receipt, out_dir, context=None, solar=None, massing=None, manifest=None):
        self.report = load_report()
        self.manifest = manifest if isinstance(manifest, dict) else {}
        self.args = dict(project_id=project_id, site_source_receipt=receipt, context=context, solar=solar, massing=massing)
        self.out_dir = Path(out_dir)
        self.lock = threading.Lock()
        self._published_hashes = None

    def _source_hashes(self):
        result = {}
        for field in ("site_source_receipt", "context", "solar", "massing"):
            path = self.args.get(field)
            if not path:
                continue
            try:
                result[field] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            except OSError as exc:
                raise self.report.ReportHold("STUDIO_SOURCE_UNREADABLE:" + field) from exc
        return result

    @property
    def bound(self):
        receipt = self.args.get("site_source_receipt")
        return bool(receipt) and Path(receipt).is_file()

    def readiness(self):
        """Read-only evidence summary. Never fetches, never infers PNU/geometry/law, no absolute paths."""
        inputs = self.manifest.get("inputs") or {}
        workbook = inputs.get("workbook") if isinstance(inputs.get("workbook"), dict) else {}
        role = _safe_text(workbook.get("source_role") or "UNKNOWN", 80)
        declared = bool(self.args.get("site_source_receipt"))
        layers = [{"id": "SITE_ANALYSIS", "label": "현장 소스 영수증(site_source_receipt)", "required": True,
                   "state": "BOUND" if self.bound else ("DECLARED_FILE_MISSING" if declared else "MISSING")}]
        for key, label in OPTIONAL_LAYERS:
            path = self.args.get(key)
            layers.append({"id": key, "label": label, "required": False,
                           "state": "PRESENT" if path and Path(path).is_file() else ("DECLARED_FILE_MISSING" if path else "ABSENT")})
        notes = self.manifest.get("source_lock_notes")
        notes = {_safe_text(k, 60): _safe_text(v) for k, v in notes.items()} if isinstance(notes, dict) else {}
        return {"status": "READY" if self.bound else "HOLD",
                "failure_class": None if self.bound else NOT_BOUND,
                "project_id": _safe_text(self.args.get("project_id") or "UNKNOWN", 120),
                "route": _safe_text(self.manifest.get("route") or "UNKNOWN", 60),
                "stages": [_safe_text(x, 60) for x in (self.manifest.get("stages") or []) if isinstance(x, str)],
                "workbook": {"source_role": role, "certified": role in CERTIFIED_ROLES,
                             "file": _safe_text(Path(str(workbook["xlsx"])).name, 120) if workbook.get("xlsx") else None},
                "layers": layers, "source_lock_notes": notes,
                "pnu_status": "NOT_PROVIDED_NOT_INFERRED",
                "next_steps": [
                    "이 프로젝트 ID와 정확히 일치하는 19자리 PNU를 사용자/원본 자료에서 확인합니다(추정 금지).",
                    "ARCHIGROW_SITE_SOURCE_INPUT_V1 입력(project_id + pnu, 또는 주소 + 무료 VWorld 키)을 만들고 ARCHIGROW_PARCEL_SOURCE.py로 출처 영수증을 생성합니다.",
                    "무료 VWorld 키는 기존 로컬 비밀 환경변수(VWORLD_KEY)로만 설정합니다. 값은 화면·로그에 표시하지 않습니다.",
                    "생성된 site_source_receipt.json을 pipeline manifest의 inputs.site_analysis.site_source_receipt에 연결한 뒤 스튜디오를 다시 실행합니다."]}

    def readiness_html(self):
        r = self.readiness()
        e = lambda v: html.escape(str(v), quote=True)
        state_ko = {"BOUND": "연결됨", "PRESENT": "있음", "MISSING": "없음 — HOLD", "ABSENT": "없음(선택)",
                    "DECLARED_FILE_MISSING": "선언됨, 파일 없음"}

        def tone(l):
            return "ok" if l["state"] in ("BOUND", "PRESENT") else ("bad" if l["required"] else "warn")
        rows = "".join(
            f'<tr><td>{e(l["label"])}</td><td>{"필수" if l["required"] else "선택"}</td>'
            f'<td class="st {tone(l)}">{e(state_ko[l["state"]])}</td></tr>' for l in r["layers"])
        notes = "".join(f"<li><b>{e(k)}</b> — {e(v)}</li>" for k, v in r["source_lock_notes"].items()) or "<li>기록된 원천 잠금 메모 없음</li>"
        steps = "".join(f"<li>{e(t)}</li>" for t in r["next_steps"])
        wb = r["workbook"]
        cert = ("원본 역할 표시 · 공식 확인 별도" if wb["source_role"] in ("ORIGINAL", "VERIFIED_ORIGINAL", "CERTIFIED")
                else "공식 인증 아님 — 파생/임시 자료")
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ArchiGrow 소스 준비 상태 — {e(r["project_id"])}</title><style>
:root{{--ink:#1d2430;--mut:#667085;--line:#d9dee7;--bg:#f4f6f9;--bad:#b42318;--warn:#b54708;--ok:#067647}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Malgun Gothic",system-ui,sans-serif}}
header{{background:#111827;color:#fff;padding:22px 48px}}header small{{color:#9aa4b2;letter-spacing:.08em}}
header h1{{margin:4px 0 0;font-size:24px}}main{{max-width:1180px;margin:28px auto;padding:0 32px;display:grid;grid-template-columns:1.2fr 1fr;gap:20px}}
section{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:20px 24px}}section.wide{{grid-column:1/-1}}
h2{{margin:0 0 12px;font-size:16px}}.hold{{border-left:6px solid var(--bad)}}.hold b{{color:var(--bad)}}
table{{width:100%;border-collapse:collapse}}td{{padding:8px 6px;border-top:1px solid var(--line)}}.st{{font-weight:700}}.ok{{color:var(--ok)}}.bad{{color:var(--bad)}}.warn{{color:var(--warn)}}
dl{{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;margin:0}}dt{{color:var(--mut)}}dd{{margin:0;word-break:break-all}}
ol,ul{{margin:0;padding-left:20px}}li{{margin:6px 0}}.actions{{display:flex;gap:10px;flex-wrap:wrap}}
.btn{{padding:8px 14px;border-radius:8px;border:1px solid var(--line);background:#fff;color:var(--ink);text-decoration:none;font:inherit}}
.btn[aria-disabled=true]{{color:#98a2b3;background:#f2f4f7;cursor:not-allowed}}
</style></head><body>
<header><small>ARCHIGROW SITE STUDIO · 소스 준비 상태(읽기 전용)</small><h1>프로젝트 {e(r["project_id"])}</h1></header>
<main>
<section class="wide hold" id="hold"><h2>상태: <b>HOLD · {e(NOT_BOUND)}</b></h2>
<p>이 프로젝트에는 검증된 현장 소스 영수증(SITE_ANALYSIS)이 연결되어 있지 않습니다. 지적·필지·법규·일조·매스 결과를 만들거나 PPT/내보내기를 제공하지 않습니다. 자동 수집도 하지 않습니다.</p></section>
<section><h2>프로젝트 / 워크북</h2><dl>
<dt>프로젝트 ID</dt><dd id="pid">{e(r["project_id"])}</dd>
<dt>경로(route)</dt><dd>{e(r["route"])}</dd>
<dt>매니페스트 등록 단계(완료 증거 아님)</dt><dd>{e(", ".join(r["stages"]) or "없음")}</dd>
<dt>워크북 역할</dt><dd id="wb-role">{e(wb["source_role"])} — {e(cert)}</dd>
<dt>워크북 파일</dt><dd>{e(wb["file"] or "없음")}</dd>
<dt>PNU</dt><dd id="pnu">미제공 — 추정하지 않음</dd></dl></section>
<section><h2>소스 계층</h2><table id="layers">{rows}</table></section>
<section class="wide"><h2>원천 잠금 메모(매니페스트 기록)</h2><ul id="notes">{notes}</ul></section>
<section class="wide"><h2>확보해야 할 것</h2><ol id="steps">{steps}</ol></section>
<section class="wide"><h2>동작</h2><div class="actions">
<a class="btn" href="/api/readiness" id="json-link">준비 상태 JSON 열기</a>
<button class="btn" aria-disabled="true" disabled>PPT 내보내기 — HOLD</button>
<button class="btn" aria-disabled="true" disabled>지도·일조·매스 — HOLD</button></div></section>
</main></body></html>"""

    def snapshot_stale(self):
        if not self.bound:
            return True
        if self._published_hashes is None:
            return True
        try:
            return self._source_hashes() != self._published_hashes
        except self.report.ReportHold:
            return True


    @classmethod
    def from_pipeline_manifest(cls, manifest_path, out_dir):
        manifest_path = Path(manifest_path)
        doc = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if not isinstance(doc, dict):
            raise ValueError("PIPELINE_MANIFEST_NOT_OBJECT")
        inputs = (doc.get("inputs") or {}).get("site_analysis") or {}
        inputs = inputs if isinstance(inputs, dict) else {}
        base = manifest_path.parent

        def path(key):
            return str(base / inputs[key]) if inputs.get(key) else None
        return cls(doc.get("project_id"), path("site_source_receipt"), out_dir,
                   path("context"), path("solar"), path("massing"), manifest=doc)

    def build(self, out_dir, option=None, baseline=None):
        if not self.bound:
            raise self.report.ReportHold(NOT_BOUND)
        with self.lock:
            before = self._source_hashes()
            if self._published_hashes is not None and before != self._published_hashes:
                raise self.report.ReportHold("STALE_SOURCE_REFRESH_REQUIRED")
            result = self.report.build(out_dir=out_dir, option=option, baseline=baseline, **self.args)
            if self._source_hashes() != before:
                raise self.report.ReportHold("SOURCE_CHANGED_DURING_EXPORT")
            return result

    def publish(self, option=None, baseline=None):
        if not self.bound:
            raise self.report.ReportHold(NOT_BOUND)
        with self.lock:
            before = self._source_hashes()
            result = self.report.build(out_dir=self.out_dir, option=option, baseline=baseline, **self.args)
            if self._source_hashes() != before:
                raise self.report.ReportHold("SOURCE_CHANGED_DURING_PUBLISH")
            self._published_hashes = before
            return result

    def export(self, fmt, option, baseline=None):
        name, mime = FORMATS[fmt]
        tmp = Path(tempfile.mkdtemp(prefix="site_studio_"))
        try:
            manifest = self.build(tmp, option, baseline)
            if fmt == "pptx" and manifest["capabilities"]["pptx"] != "AVAILABLE":
                raise self.report.ReportHold("PPTX_" + manifest["capabilities"]["pptx"])
            selected = (manifest.get("selected_option") or {}).get("id") or ""
            return (tmp / name).read_bytes(), mime, selected
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def make_handler(studio):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ArchiGrowSiteStudio/1"

        def log_message(self, *args):
            pass

        def _send(self, code, body, mime, extra=None):
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, doc):
            self._send(code, json.dumps(doc, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            url = urlparse(self.path)
            query = parse_qs(url.query)
            if url.path == "/api/health":
                return self._json(200, {"studio": "ARCHIGROW_SITE_STUDIO", "loopback_only": True,
                                        "formats": sorted(FORMATS),
                                        "snapshot": "NOT_BOUND" if not studio.bound else ("STALE" if studio.snapshot_stale() else "CURRENT")})
            if url.path == "/api/readiness":
                return self._json(200, studio.readiness())
            if url.path in ("/", "/site_analysis.html"):
                if not studio.bound:
                    return self._send(200, studio.readiness_html().encode("utf-8"), FORMATS["html"][1])
                if studio.snapshot_stale():
                    return self._json(409, {"status": "HOLD", "failure_class": "STALE_SOURCE_REFRESH_REQUIRED"})
                return self._send(200, (studio.out_dir / "site_analysis.html").read_bytes(), FORMATS["html"][1])
            if url.path in ("/api/export", "/api/recalc"):
                fmt = "manifest" if url.path == "/api/recalc" else (query.get("format") or ["pptx"])[0]
                option = (query.get("option") or [None])[0]
                baseline = (query.get("baseline") or [None])[0]
                if fmt not in FORMATS:
                    return self._json(400, {"status": "REJECTED", "failure_class": "FORMAT_UNSUPPORTED"})
                try:
                    body, mime, selected = studio.export(fmt, option, baseline)
                except studio.report.ReportHold as exc:
                    return self._json(409, {"status": "HOLD", "failure_class": str(exc)})
                if url.path == "/api/recalc":
                    doc = json.loads(body.decode("utf-8"))
                    return self._json(200, {"selected_option": doc.get("selected_option"), "recalc": doc.get("recalc"),
                                            "comparison": doc.get("comparison")})
                return self._send(200, body, mime, {"X-Selected-Option": selected,
                                                    "Content-Disposition": f'attachment; filename="{FORMATS[fmt][0]}"'})
            return self._json(404, {"status": "NOT_FOUND"})

    return Handler


def serve(studio, port=0, ready=None):
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(studio))
    if ready:
        ready(server)
    return server


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--pipeline-manifest", required=True)
    s.add_argument("--out-dir", required=True)
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--option", help="initial option for the published studio page")
    s.add_argument("--baseline", help="initial baseline option for the delta comparison (default first option)")
    a = ap.parse_args()
    studio = Studio.from_pipeline_manifest(a.pipeline_manifest, a.out_dir)
    if studio.bound:
        studio.publish(a.option, a.baseline)
    server = serve(studio, a.port)
    print(json.dumps({"status": "SERVING", "url": f"http://127.0.0.1:{server.server_address[1]}/"}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
