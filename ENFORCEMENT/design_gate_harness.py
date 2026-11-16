#!/usr/bin/env python3
"""TAKY design-gate harness (TKY-UIREF-001 §20, DGC-01..30).

Turns a DESIGN.md plus a real browser render into a receipt with named
sub-receipts. Facts come from design_gate_render.mjs (Playwright/Chromium);
this file only judges them.

Exit codes: 0 PASS, 1 FAIL, 3 HOLD (harness/environment problem, product verdict UNKNOWN).

Claim ceiling: this checks the mechanical parts of DG-06/DG-08 only. It does
not replace the approved-reference visual compare (design_gate_receipt.py)
or human approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import os
import subprocess
import sys
from pathlib import Path

import yaml

SIZE_TOLERANCE_PCT = 2.0  # max height difference between render and reference, after width scaling

SCHEMA = "TAKY_DESIGN_GATE_HARNESS_RECEIPT_V1"
HERE = Path(__file__).resolve().parent
RENDER = HERE / "design_gate_render.mjs"
# Vendored from Jakeschincariol/replica-skill (MIT, see .claude/skills/REPLICA_SKILL_LICENSE.txt).
IMGDIFF = HERE.parent / ".claude" / "skills" / "replica-diff" / "imgdiff.py"
SUB_ORDER = ("HARNESS_HEALTH", "SPEC_LINT", "TARGET_RENDER", "TOKEN_FIDELITY",
             "FONT_PRINT_PDF", "A11Y_BASIC", "GENERIC_TELLS", "FIRST_VIEWPORT", "PREMIUM", "VISUAL_COMPARE")
# DGC-30 dashboard templates (MASTER/UI_REFERENCE_PROTOCOL.md §20.1e).
DASHBOARD_TEMPLATES = ("T1_DECISION", "T2_WORLD_HUB", "T3_OPS_BOARD", "CUSTOM")
# PREMIUM restraint limits, ported from SAVEY premium-gate.mjs PG01-PG12 (2026-11-07). Override per
# project with taky.thresholds.premium. PG05 (accent hues) is left to the reviewer: charts legitimately need hues.
PREMIUM_DEFAULTS = {"typefaces": 2, "font_sizes": 7, "heavy_weight_pct": 15, "light_weights": 0,
                    "big_shadows": 2, "text_shadows": 0, "radii": 3, "gradients": 1,
                    "interactive": 14, "filled_cta": 2, "chars": 320}
DEFAULTS = {"min_layout_score": 90, "min_font_px": 12, "max_allcaps_labels": 2, "color_tolerance": 6,
            "max_off_token_colors": 0}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------- DESIGN.md parsing (google-labs-code/design.md format) ----------

def parse_design_md(text: str) -> tuple[dict, list[str]]:
    """Return (merged token tree, markdown section headings)."""
    tokens: dict = {}
    blocks = []
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        blocks.append(m.group(1))
    blocks += re.findall(r"```yaml\n(.*?)```", text, re.S)
    for b in blocks:
        data = yaml.safe_load(b) or {}
        if not isinstance(data, dict):
            continue
        for k, v in data.items():
            if k in tokens:
                raise ValueError(f"DUPLICATE_TOP_LEVEL_KEY:{k}")
            tokens[k] = v
    headings = [h.strip().lower() for h in re.findall(r"^##\s+(.+)$", text, re.M)]
    return tokens, headings


def _hexes(colors) -> list[str]:
    out = []
    if isinstance(colors, dict):
        for v in colors.values():
            out += _hexes(v)
    elif isinstance(colors, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", colors.strip()):
        out.append(colors.strip().lower())
    return out


def _families(typo) -> set[str]:
    fams = set()
    if isinstance(typo, dict):
        for k, v in typo.items():
            if k == "fontFamily" and isinstance(v, str):
                fams.add(v.split(",")[0].strip().strip("'\""))
            else:
                fams |= _families(v)
    return fams


def lint_spec(text: str) -> dict:
    """DGC-18: tokens + composition rules + prohibition list. DGC-01/02: taky block."""
    findings, fails = [], []
    try:
        tokens, headings = parse_design_md(text)
    except (yaml.YAMLError, ValueError) as e:
        return {"status": "FAIL", "findings": [f"SPEC_UNPARSEABLE: {e}"], "tokens": {},
                "palette": [], "font_families": [], "mode": "EXPLORE",
                "design_system": "UNKNOWN@UNKNOWN", "thresholds": dict(DEFAULTS),
                "premium": dict(PREMIUM_DEFAULTS), "dashboard": None}
    palette = _hexes(tokens.get("colors"))
    fams = _families(tokens.get("typography"))
    if not palette:
        fails.append("NO_COLOR_TOKENS")
    if not fams:
        fails.append("NO_TYPOGRAPHY_FONTFAMILY")
    if not any(h.startswith("layout") or "composition" in h for h in headings):
        fails.append("NO_LAYOUT_OR_COMPOSITION_SECTION (DGC-18: TOKEN MATCH != DESIGN PASS)")
    dd = re.search(r"^##\s+Do'?s and Don'?ts\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    if not dd or not re.search(r"(?i)(don'?t|never|avoid|금지|하지 ?마)", dd.group(1)):
        fails.append("NO_PROHIBITION_LIST (DGC-18)")
    taky = tokens.get("taky") or {}
    mode = str(taky.get("mode", "")).upper()
    if mode not in ("EXPLORE", "EXECUTE"):
        findings.append("MODE_UNDECLARED → treated as EXPLORE (DGC-01)")
        mode = "EXPLORE"
    for k in ("design_system_id", "version"):
        if not taky.get(k):
            findings.append(f"TAKY_{k.upper()}_MISSING (DGC-02/DGC-20)")
    if mode == "EXECUTE" and not taky.get("source_commit"):
        fails.append("EXECUTE_WITHOUT_SOURCE_COMMIT (DGC-02)")
    dash = tokens.get("dashboard")
    if dash is not None:
        if not isinstance(dash, dict):
            fails.append("DASHBOARD_BLOCK_NOT_A_MAPPING (DGC-24)")
            dash = {}
        if not str(dash.get("question") or "").strip():
            fails.append("DASHBOARD_WITHOUT_QUESTION (DGC-24)")
        if dash.get("template") and dash.get("template") not in DASHBOARD_TEMPLATES:
            fails.append(f"DASHBOARD_TEMPLATE_UNKNOWN:{dash.get('template')} (DGC-30)")
        if not dash.get("template"):
            findings.append("DASHBOARD_TEMPLATE_UNDECLARED (DGC-30)")
    return {"status": "FAIL" if fails else "PASS", "findings": fails + findings,
            "palette": palette, "font_families": sorted(fams), "mode": mode,
            "design_system": f"{taky.get('design_system_id','UNKNOWN')}@{taky.get('version','UNKNOWN')}",
            "thresholds": {**DEFAULTS, **(taky.get("thresholds") or {})},
            "premium": {**PREMIUM_DEFAULTS, **(((taky.get("thresholds") or {}).get("premium")) or {})},
            "dashboard": tokens.get("dashboard") if isinstance(tokens.get("dashboard"), dict) else None}


# ---------- judging render facts ----------

def _rgb(css: str):
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", css)
    if not m:
        return None
    if m.group(4) is not None and float(m.group(4)) == 0:
        return None
    return tuple(int(m.group(i)) for i in (1, 2, 3))


def _hex_rgb(h: str):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def judge(spec: dict, render: dict) -> dict:
    t = spec["thresholds"]
    subs: dict[str, dict] = {}
    if not render.get("harness", {}).get("ok"):
        subs["HARNESS_HEALTH"] = {"status": "HOLD", "cause_class": "HARNESS",
                                  "findings": [render.get("harness", {}).get("error", "render failed")]}
        for k in SUB_ORDER[1:]:
            subs[k] = {"status": "UNKNOWN", "findings": ["not evaluated: harness HOLD"]}
        subs["SPEC_LINT"] = {"status": spec["status"], "findings": spec["findings"]}
        return subs
    subs["HARNESS_HEALTH"] = {"status": "PASS", "findings": []}
    subs["SPEC_LINT"] = {"status": spec["status"], "findings": spec["findings"]}
    vps = render["viewports"]

    over = [f"{v['id']}: horizontal overflow {v['horizontal_overflow_px']}px" for v in vps if v["horizontal_overflow_px"] > 0]
    subs["TARGET_RENDER"] = {"status": "FAIL" if over else "PASS", "findings": over,
                             "screenshots": {v["id"]: v["screenshot_sha256"] for v in vps}}

    pal = [_hex_rgb(h) for h in spec["palette"]]
    off = set()
    for v in vps:
        for c in v["text_colors"]:
            rgb = _rgb(c)
            if rgb is None or not pal:
                continue
            if min(max(abs(a - b) for a, b in zip(rgb, p)) for p in pal) > t["color_tolerance"]:
                off.add(c)
    tf_fail = len(off) > t["max_off_token_colors"]
    subs["TOKEN_FIDELITY"] = {"status": "FAIL" if tf_fail else "PASS",
                              "findings": [f"off-token color {c}" for c in sorted(off)]}

    ff = []
    spec_fams = {f.lower() for f in spec["font_families"]}
    for v in vps:
        for fam in v["primary_font_families"]:
            if fam.lower() not in spec_fams:
                ff.append(f"{v['id']}: rendered family '{fam}' not in DESIGN.md typography")
            elif not v["font_check"].get(fam, False):
                ff.append(f"{v['id']}: '{fam}' declared but not available (silent fallback)")
        if v["gradient_text_count"]:
            ff.append(f"{v['id']}: {v['gradient_text_count']} gradient-clipped text element(s) — print-unsafe")
        if v["mask_image_count"]:
            ff.append(f"{v['id']}: {v['mask_image_count']} mask-image element(s) — print-unsafe")
    if not render.get("print", {}).get("bytes"):
        ff.append("print/PDF output not produced")
    subs["FONT_PRINT_PDF"] = {"status": "FAIL" if ff else "PASS", "findings": sorted(set(ff)),
                              "pdf_sha256": render.get("print", {}).get("pdf_sha256")}

    a11y = []
    for v in vps:
        if v["min_font_px"] is not None and v["min_font_px"] < t["min_font_px"]:
            a11y.append(f"{v['id']}: min text {v['min_font_px']}px < {t['min_font_px']}px")
        if v["small_target_count"]:
            a11y.append(f"{v['id']}: {v['small_target_count']} interactive target(s) under 24px")
    subs["A11Y_BASIC"] = {"status": "FAIL" if a11y else "PASS", "findings": a11y}

    tells = [f"{v['id']}: {v['allcaps_label_count']} small ALL-CAPS labels"
             for v in vps if v["allcaps_label_count"] > t["max_allcaps_labels"]]
    # Advisory only: generic-look heuristics are reviewer input, never an automatic FAIL (DGC-12).
    for v in vps:
        for row in (v.get("dashboard_probe") or {}).get("same_shape_rows") or []:
            tells.append(f"{v['id']}: same-shape card row {row} — rank as a list or vary weight (§20.1g)")
    subs["GENERIC_TELLS"] = {"status": "ADVISORY" if tells else "PASS", "findings": tells}

    # DGC-27/28 (§20.1e). ADVISORY until manual replay on real project screens passes (DGC-12).
    dash = spec.get("dashboard") or {}
    fv = []
    for v in vps:
        f = v.get("first_viewport") or {}
        for hit in v.get("fixed_overlap_at_end") or []:
            fv.append(f"{v['id']}: at scroll end, text under a fixed/sticky element: {hit} (DGC-28)")
        cap = dash.get("max_filled_cta")
        if cap is not None and f.get("filled_cta_count", 0) > cap:
            fv.append(f"{v['id']}: {f['filled_cta_count']} filled CTAs in first viewport > {cap} (DGC-27)")
        dp = v.get("dashboard_probe") or {}
        dm = dp.get("decision_metric")
        if dm and dm.get("missing"):
            fv.append(f"{v['id']}: decision_metric_selector not found: {dm['missing']} (DGC-25)")
        elif dm and dm.get("max_number_px", 0) > dm.get("metric_px", 0) + 0.5:
            fv.append(f"{v['id']}: decision metric {dm['metric_px']}px is smaller than '{dm['max_number_text']}' "
                      f"{dm['max_number_px']}px (DGC-25)")
        sc = dp.get("status_check")
        if sc:
            cfg = dash.get("status_check") or {}
            positive = cfg.get("positive") or ["계획대로", "잘 가고", "순조", "on track", "on plan"]
            tol = float(cfg.get("tolerance_pct", 10))
            if sc.get("missing"):
                fv.append(f"{v['id']}: status_check selector(s) not found: {sc['missing']} (DGC-26)")
            elif (sc.get("burn_pct") is not None and sc.get("elapsed_pct") is not None
                  and any(w.lower() in str(sc.get("status") or "").lower() for w in positive)
                  and sc["burn_pct"] > sc["elapsed_pct"] + tol):
                fv.append(f"{v['id']}: status '{sc['status']}' says on plan but {sc['burn_pct']:g}% used at "
                          f"{sc['elapsed_pct']:g}% of the period (DGC-26)")
    subs["FIRST_VIEWPORT"] = {"status": "ADVISORY" if fv else "PASS", "findings": fv,
                              "screenshots": {v["id"]: v.get("first_viewport_sha256") for v in vps},
                              "reviewer_checks": ["focal points <= dashboard.max_focal_points",
                                                  "decision metric is the largest number (DGC-25)",
                                                  "statement, state chip and numbers agree (DGC-26)"]}

    pm, pr = spec.get("premium") or PREMIUM_DEFAULTS, []
    checks = (("typeface_count", "typefaces", "PG01 typefaces"), ("font_size_count", "font_sizes", "PG02 font sizes"),
              ("heavy_weight_pct", "heavy_weight_pct", "PG03 weight>=800 %"), ("light_weight_count", "light_weights", "PG04 weights<400"),
              ("big_shadow_count", "big_shadows", "PG06 shadows blur>16"), ("text_shadow_count", "text_shadows", "PG07 text-shadow"),
              ("radius_count", "radii", "PG08 radii"), ("gradient_count", "gradients", "PG09 gradients"),
              ("interactive_count", "interactive", "PG10 interactive"), ("filled_cta_count", "filled_cta", "PG11 filled CTA"),
              ("chars", "chars", "PG12 characters"))
    for v in vps:
        f = v.get("first_viewport") or {}
        for fact, lim, label in checks:
            if fact in f and f[fact] > pm[lim]:
                pr.append(f"{v['id']}: {label} {f[fact]} > {pm[lim]}")
    subs["PREMIUM"] = {"status": "ADVISORY" if pr else "PASS", "findings": pr,
                       "score": {v["id"]: sum(1 for fact, lim, _ in checks
                                              if (v.get("first_viewport") or {}).get(fact, 0) <= pm[lim]) for v in vps},
                       "out_of": len(checks)}
    return subs


def visual_compare(reference: Path | None, render: dict, threshold: float, mode: str = "layout") -> dict:
    """DGC-07 / prior C-12: compare the render with the approved (or replica) reference.

    layout mode = structure only, colour ignored (replica-diff semantics).
    The reference screenshot must match the viewport it is compared with.
    """
    if reference is None:
        return {"status": "NOT_APPLICABLE", "findings": ["no --reference given"]}
    vps = render.get("viewports") or []
    shot = next((v for v in vps if v.get("id") == reference.stem), None)
    if shot is None:
        if not vps:
            return {"status": "UNKNOWN", "findings": ["no render to compare"]}
        # Never silently compare against a different screen size (review 2026-11-11 MEDIUM).
        return {"status": "HOLD", "cause_class": "HARNESS",
                "findings": [f"REFERENCE_VIEWPORT_UNMATCHED: name the reference <viewport-id>.png "
                             f"(one of {[v.get('id') for v in vps]})"]}
    try:
        p = subprocess.run([sys.executable, str(IMGDIFF), str(reference), shot["screenshot"],
                            "--mode", mode, "--json"], capture_output=True, text=True, timeout=300)
        rep = json.loads(p.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        return {"status": "HOLD", "cause_class": "HARNESS", "findings": [f"imgdiff failed: {e!r}"]}
    ok = rep["score"] >= threshold
    findings = [] if ok else [f"layout score {rep['score']} < {threshold} ({rep.get('verdict')})"]
    # imgdiff compares only the overlapping height; a missing half-page can still score 100
    # (review 2026-11-11 HIGH). Size mismatch beyond tolerance is a FAIL on its own.
    o, c = rep.get("original") or {}, rep.get("clone") or {}
    if o.get("width") and o.get("height") and c.get("width") and c.get("height"):
        ref_h = o["height"] * (c["width"] / float(o["width"]))
        delta = abs(c["height"] - ref_h) / ref_h * 100.0 if ref_h else 100.0
        if delta > SIZE_TOLERANCE_PCT:
            ok = False
            findings.append(f"SIZE_MISMATCH: render height {c['height']}px vs reference "
                            f"{round(ref_h)}px at render width ({delta:.1f}% > {SIZE_TOLERANCE_PCT}%)")
    else:
        ok = False
        findings.append("SIZE_UNKNOWN: imgdiff report lacks image sizes")
    return {"status": "PASS" if ok else "FAIL", "mode": mode, "score": rep["score"],
            "threshold": threshold, "against_viewport": shot["id"],
            "reference_sha256": sha256_bytes(reference.read_bytes()),
            "findings": findings}


def verdict(subs: dict) -> str:
    st = [s["status"] for s in subs.values() if s["status"] != "NOT_APPLICABLE"]
    if "FAIL" in st:
        return "FAIL"
    if "HOLD" in st or "UNKNOWN" in st:
        return "HOLD"
    return "PASS"


def run(design: Path, target: str, out: Path, viewports: str | None = None,
        reference: Path | None = None, compare_mode: str = "layout") -> dict:
    spec_bytes = design.read_bytes()
    spec = lint_spec(spec_bytes.decode("utf-8"))
    cmd = ["node", str(RENDER), target, str(out)] + ([viewports] if viewports else [])
    try:
        env = {**os.environ, "DGATE_DASHBOARD": json.dumps(spec.get("dashboard") or {}, ensure_ascii=False)}
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
        render = json.loads(proc.stdout) if proc.stdout.strip() else {
            "harness": {"ok": False, "error": proc.stderr.strip()[-500:] or "no output"}}
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        render = {"harness": {"ok": False, "error": repr(e)}}
    subs = judge(spec, render)
    subs["VISUAL_COMPARE"] = (visual_compare(reference, render, spec["thresholds"]["min_layout_score"], compare_mode)
                              if render.get("harness", {}).get("ok") else
                              {"status": "UNKNOWN", "findings": ["not evaluated: harness HOLD"]})
    v = verdict(subs)
    receipt = {
        "schema": SCHEMA,
        "mode": spec.get("mode", "EXPLORE"),
        "claim_ceiling": "PILOT_FIXTURE_ONLY" if spec.get("mode") != "EXECUTE" else "DG08_MECHANICAL_ONLY",
        "design_system": spec.get("design_system"),
        "spec_sha256": sha256_bytes(spec_bytes),
        "artifact_sha256": render.get("artifact_sha256"),
        "target": render.get("target", target),
        "sub_receipts": {k: subs[k] for k in SUB_ORDER},
        "verdict": v,
        # Bridge to ENFORCEMENT/design_gate_receipt.py: the visual compare against the
        # approved reference is a separate step; this supplies the runtime render hash.
        "design_gate_receipt_evidence": {
            "runtime_render_sha256": next((s for s in subs["TARGET_RENDER"].get("screenshots", {}).values()), None),
            "responsive_gate_pass": subs["TARGET_RENDER"]["status"] == "PASS",
            "approved_reference_sha256": subs["VISUAL_COMPARE"].get("reference_sha256"),
            "comparison_method": "replica-diff/imgdiff " + subs["VISUAL_COMPARE"].get("mode", "layout"),
            "comparison_score": subs["VISUAL_COMPARE"].get("score"),
            "threshold": subs["VISUAL_COMPARE"].get("threshold"),
            "comparison_pass": subs["VISUAL_COMPARE"]["status"] == "PASS",
        },
    }
    receipt["receipt_sha256"] = sha256_bytes(json.dumps(receipt, sort_keys=True, ensure_ascii=False).encode())
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False))
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--design", required=True, type=Path, help="DESIGN.md path")
    ap.add_argument("--target", required=True, help="HTML file or http(s) URL")
    ap.add_argument("--out", required=True, type=Path, help="output dir for screenshots, PDF, receipt")
    ap.add_argument("--reference", type=Path, help="approved or replica reference screenshot (PNG); name it <viewport-id>.png")
    ap.add_argument("--compare-mode", choices=("layout", "pixel"), default="layout")
    ap.add_argument("--viewports", help='JSON list, e.g. [{"id":"slide","width":1920,"height":1080}]')
    a = ap.parse_args()
    r = run(a.design, a.target, a.out, a.viewports, a.reference, a.compare_mode)
    print(json.dumps({"verdict": r["verdict"], "mode": r["mode"], "claim_ceiling": r["claim_ceiling"],
                      "failed": {k: s["findings"] for k, s in r["sub_receipts"].items()
                                 if s["status"] in ("FAIL", "HOLD", "ADVISORY")},
                      "receipt": str(a.out / "receipt.json")}, indent=2, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1}.get(r["verdict"], 3)


if __name__ == "__main__":
    sys.exit(main())
