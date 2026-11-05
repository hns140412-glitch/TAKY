#!/usr/bin/env python3
"""Source-bound, offline site-analysis report over existing ArchiGrow evidence.

The parcel collector owns acquisition and identity comparison. This projection
never converts source evidence into design or legal approval.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

VERSION = "ARCHIGROW_SITE_ANALYSIS_REPORT/2026-10-19.2"
PAGES = ("Identity", "Parcel geometry", "Source quality", "Building context",
         "Solar evidence", "Design evidence", "Verification agenda")


SEL_ATTR = ' class="sel"'


class ReportHold(Exception):
    pass


def _read(path, project_id, label):
    path = Path(path)
    raw = path.read_bytes()
    doc = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(doc, dict) or doc.get("project_id") != project_id:
        raise ReportHold(f"PROJECT_ID_MISMATCH:{label}")
    return doc, {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest()}


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _ring(value):
    if not isinstance(value, list) or len(value) < 3 or len(value) > 2000:
        raise ReportHold("PARCEL_RING_INVALID")
    if value[0] == value[-1]:
        value = value[:-1]
    if len(value) < 3 or any(not isinstance(p, list) or len(p) != 2 or
                             not all(_number(v) for v in p) for p in value):
        raise ReportHold("PARCEL_RING_INVALID")
    if len(set((p[0], p[1]) for p in value)) != len(value):
        raise ReportHold("PARCEL_RING_INVALID")
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def meets(a, b, c, d):
        s1, s2, s3, s4 = cross(a,b,c), cross(a,b,d), cross(c,d,a), cross(c,d,b)
        return (s1*s2 < 0 and s3*s4 < 0) or any(
            s == 0 and min(p[0],q[0]) <= r[0] <= max(p[0],q[0]) and
            min(p[1],q[1]) <= r[1] <= max(p[1],q[1])
            for s,p,q,r in ((s1,a,b,c),(s2,a,b,d),(s3,c,d,a),(s4,c,d,b)))
    for i in range(len(value)):
        for j in range(i+2, len(value)):
            if i == 0 and j == len(value)-1:
                continue
            if meets(value[i],value[(i+1)%len(value)],value[j],value[(j+1)%len(value)]):
                raise ReportHold("PARCEL_RING_SELF_INTERSECTION")
    return value


def _area(ring):
    return abs(sum(p[0]*ring[(i+1)%len(ring)][1] - ring[(i+1)%len(ring)][0]*p[1]
                   for i, p in enumerate(ring))) / 2


def _fmt(value, digits=1):
    return f"{value:,.{digits}f}" if _number(value) else "Unknown"


def _esc(value):
    return html.escape(str(value if value is not None else "Unknown"), quote=True)


def _centroid(ring):
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return (min(xs)+max(xs))/2, (min(ys)+max(ys))/2


def _known_height(value):
    return _number(value) and value > 0


def _height_bands(heights):
    """Equal-interval classes over known heights only; unknown has its own class."""
    if not heights:
        return []
    lo, hi = min(heights), max(heights)
    if lo == hi:
        return [(lo, hi)]
    step = (hi-lo)/3
    return [(lo+step*i, lo+step*(i+1)) for i in range(3)]


def _band_class(value, bands):
    if not _known_height(value) or not bands:
        return "hu"
    for i, (lo, hi) in enumerate(bands):
        if value <= hi or i == len(bands)-1:
            return f"h{i}"


def _map(site, context, crs, north_angle=0, mass=None, selected_id=None):
    """Projected SVG. Grid, scale and bands derive from supplied metres only."""
    obstacles = []
    if context:
        for o in context.get("obstacles", []):
            try:
                obstacles.append((o, _ring(o.get("footprint_m"))))
            except ReportHold:
                raise ReportHold("CONTEXT_FOOTPRINT_INVALID")
    points = [p for ring in [site]+[r for _, r in obstacles] for p in ring]
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    extent = max(x1-x0, y1-y0, 1)
    scale = 600 / extent
    cx, cy = (x0+x1)/2, (y0+y1)/2
    def sx(x): return 400+(x-cx)*scale
    def sy(y): return 400-(y-cy)*scale
    def path(r):
        return " ".join(("M" if i == 0 else "L") + f"{sx(p[0]):.3f},{sy(p[1]):.3f}"
                        for i, p in enumerate(r)) + " Z"
    # EPSG:5186/5179 have projected north along +Y; screen Y is inverted above.
    bar_m = 10 ** math.floor(math.log10(extent / 5))
    while bar_m * scale < 55:
        bar_m *= 2
    while bar_m * scale > 160:
        bar_m /= 2
    bar_px = bar_m * scale
    bands = _height_bands([o["height_m"] for o, _ in obstacles if _known_height(o.get("height_m"))])
    grid = ['<g id="grid" stroke="#d3dfd3" stroke-width="1" vector-effect="non-scaling-stroke">']
    gx = math.ceil((cx-400/scale)/bar_m)*bar_m
    while sx(gx) < 1200:
        grid.append(f'<path d="M{sx(gx):.2f} -400V1200"/>'); gx += bar_m
    gy = math.ceil((cy-400/scale)/bar_m)*bar_m
    while sy(gy) > -400:
        grid.append(f'<path d="M-400 {sy(gy):.2f}H1200"/>'); gy += bar_m
    grid.append('</g>')
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" role="img" aria-label="Projected parcel and supplied building footprints" data-scale-px-per-m="%.6f" data-bar-m="%g">' % (scale, bar_m),
             '<defs><style>.bld{fill:#cfd8d5;cursor:pointer}.bld.h0{fill:#dde8e3}.bld.h1{fill:#b9cec7}.bld.h2{fill:#8fb0a6}.bld.hu{fill:url(#hatch)}.bld:hover,.bld:focus,.bld.on{stroke:#0c4f49;stroke-width:3;outline:none}</style><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="#eceeed"/><path d="M0 0V8" stroke="#8a9893" stroke-width="2"/></pattern></defs>',
             '<rect width="800" height="800" fill="#e8f0e6"/>',
             '<g id="viewport">']
    parts.extend(grid)
    parts.append('<g id="buildings" stroke="#587377" stroke-width="1.5" vector-effect="non-scaling-stroke">')
    for o, r in obstacles:
        h = o.get("height_m")
        label = f'{o.get("id")}: height {h:g} m ({o.get("height_source") or "source unknown"})' if _known_height(h) else f'{o.get("id")}: height UNKNOWN'
        parts.append(f'<path class="bld {_band_class(h, bands)}" d="{path(r)}" tabindex="0" role="button" aria-label="{_esc(label)}" data-id="{_esc(o.get("id"))}"/>')
    parts.append('</g><g id="heights" font-family="Arial,sans-serif" font-size="11" fill="#203735" text-anchor="middle" pointer-events="none">')
    for o, r in obstacles:
        mx, my = _centroid(r)
        h = o.get("height_m")
        parts.append(f'<text x="{sx(mx):.1f}" y="{sy(my)+4:.1f}">{f"{h:g} m" if _known_height(h) else "?"}</text>')
    parts.append('</g><g id="parcel" fill="#e0457f" fill-opacity=".26" stroke="#c0245f" stroke-width="3" vector-effect="non-scaling-stroke">')
    parts.append(f'<path d="{path(site)}"/></g>')
    mass = [m for m in (mass or []) if m.get("ring")]
    if mass:
        top = max([m["max_height_m"] for m in mass if m.get("max_height_m")] or [1])
        parts.append('<g id="massing" font-family="Arial,sans-serif" font-size="13" font-weight="700">')
        for m in mass:
            lift = 6+30*(m["max_height_m"] or 0)/top  # screen-px height cue, relative between options only
            base = path(m["ring"])
            roof = [(sx(p[0]), sy(p[1])-lift) for p in m["ring"]]
            roof_d = " ".join(("M" if i == 0 else "L") + f"{x:.3f},{y:.3f}" for i, (x, y) in enumerate(roof)) + " Z"
            posts = "".join(f"M{sx(p[0]):.2f},{sy(p[1]):.2f}L{x:.2f},{y:.2f}" for p, (x, y) in zip(m["ring"], roof))
            mx, my = _centroid(m["ring"])
            hs = f'{m["max_height_m"]:g} m' if m.get("max_height_m") else "?"
            tag = f'{_esc(m["label"].split()[0])} · {hs}'
            on = "" if m["id"] == selected_id else ' style="display:none"'
            parts.append(f'<g class="mass" data-opt="{_esc(m["id"])}" data-geometry-status="{m["geometry_status"]}"{on}>'
                         f'<path d="{base}" fill="{m["color"]}" fill-opacity=".28" stroke="{m["color"]}" stroke-width="2" vector-effect="non-scaling-stroke"/>'
                         f'<path d="{posts}" stroke="{m["color"]}" stroke-width="1.5" vector-effect="non-scaling-stroke"/>'
                         f'<path d="{roof_d}" fill="{m["color"]}" fill-opacity=".62" stroke="#fff" stroke-width="2" vector-effect="non-scaling-stroke"/>'
                         f'<text x="{sx(mx):.1f}" y="{sy(my)-lift:.1f}" text-anchor="middle" fill="#fff" stroke="{m["color"]}" stroke-width="3" paint-order="stroke" pointer-events="none">{tag}</text></g><!--/mass-->')
        parts.append('</g>')
    parts.append('</g>')
    parts.append(f'<g id="scale" font-family="Arial,sans-serif" fill="#203735" font-size="15"><rect x="56" y="690" width="{bar_px+30:.1f}" height="64" fill="#e8f0e6" fill-opacity=".85"/><path d="M70 716h{bar_px:.2f}" stroke="#203735" stroke-width="4"/><text x="70" y="743">{bar_m:g} m</text></g>')
    parts.append(f'<g id="north" transform="translate(720 95) rotate({north_angle:g})" fill="#203735" font-family="Arial,sans-serif"><path d="M0 22V-25 M0-25l-8 15 M0-25l8 15" stroke="#203735" stroke-width="3" fill="none"/><text x="-12" y="-34" font-size="19">GN</text></g>')
    parts.append(f'<text x="70" y="785" fill="#47615e" font-family="Arial,sans-serif" font-size="13">{_esc(crs)} · local projected metres · screening geometry</text></svg>')
    return "".join(parts), {"bands": bands, "bar_m": bar_m, "scale": scale}


def _options(massing):
    """Bind each selectable option to its actual massing_result entry (index + optional id)."""
    out = []
    for i, o in enumerate((massing or {}).get("options") or []):
        kpi = o.get("kpi") or {}
        strategy = str(o.get("strategy") or f"Option {i+1}")
        out.append({"id": str(o.get("id") or f"O{i+1}"), "index": i, "label": strategy,
                    "gfa_m2": kpi.get("gross_floor_area_m2") if _number(kpi.get("gross_floor_area_m2")) else None,
                    "max_height_m": kpi.get("max_height_m") if _number(kpi.get("max_height_m")) else None,
                    "legal_source": (o.get("validation") or {}).get("source_law") or "NOT_VERIFIED"})
    if len({o["id"] for o in out}) != len(out):
        raise ReportHold("MASSING_OPTION_ID_DUPLICATE")
    return out


MASS_COLORS = ("#2f6fb3", "#d98a1c", "#7a4ab0", "#2a8f6a", "#b5483a")


def _inside(pt, ring):
    x, y, hit = pt[0], pt[1], False
    for i, a in enumerate(ring):
        b = ring[(i+1) % len(ring)]
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            hit = not hit
    return hit


def _schematic_massing(ring, massing, options):
    """Per-option massing footprints for the map.

    Supplied `footprint_m` is used as-is. Otherwise a SCHEMATIC block is drawn from the
    option's own KPI only: the parcel outline scaled about its centre, where the scale
    follows GFA / max height (a relative floor-plate indicator). It is a visual aid to tell
    options apart, never a design geometry, setback, coverage or legal result.
    """
    raw = (massing or {}).get("options") or []
    plates = [o["gfa_m2"]/o["max_height_m"] for o in options if o["gfa_m2"] and o["max_height_m"]]
    lo, hi = (min(plates), max(plates)) if plates else (0, 0)
    out = []
    for o in options:
        supplied = (raw[o["index"]] or {}).get("footprint_m")
        color = MASS_COLORS[o["index"] % len(MASS_COLORS)]
        base = {"id": o["id"], "label": o["label"], "color": color, "max_height_m": o["max_height_m"]}
        if supplied:
            out.append(dict(base, ring=_ring(supplied), geometry_status="SUPPLIED_UNVERIFIED"))
            continue
        if not (o["gfa_m2"] and o["max_height_m"]):
            out.append(dict(base, ring=None, geometry_status="NO_KPI_NO_GEOMETRY"))
            continue
        norm = (o["gfa_m2"]/o["max_height_m"]-lo)/(hi-lo) if hi > lo else .5
        f = .35+.3*norm
        cx = sum(p[0] for p in ring)/len(ring)
        cy = sum(p[1] for p in ring)/len(ring)
        for _ in range(8):
            cand = [[round(cx+(p[0]-cx)*f, 3), round(cy+(p[1]-cy)*f, 3)] for p in ring]
            if all(_inside(p, ring) for p in cand):
                break
            f *= .8
        else:
            cand = None
        out.append(dict(base, ring=cand, geometry_status="SCHEMATIC_FROM_KPI_NOT_DESIGN_GEOMETRY" if cand else "NO_SCHEMATIC_FIT"))
    return out


def _select_option(options, requested):
    if requested in (None, ""):
        return (options[0], "DEFAULT_FIRST") if options else (None, "NO_OPTIONS")
    key = str(requested).strip()
    for o in options:
        if key in (o["id"], str(o["index"]+1), o["label"]) or key.upper() == o["label"].split()[0].upper():
            return o, "EXPLICIT"
    raise ReportHold("OPTION_NOT_FOUND:" + key)


def recalculate(ring, area_ref, context, option):
    """Bounded deterministic recomputation from current evidence (mirrored in the studio JS)."""
    computed = _area(ring)
    official, recorded = area_ref.get("eum_area_m2"), area_ref.get("recorded_polygon_area_m2")
    delta = computed-official if _number(official) else None
    tol = max(1.0, official*.005) if _number(official) else None
    buildings = []
    for o in (context or {}).get("obstacles") or []:
        r = _ring(o.get("footprint_m"))
        buildings.append((o, _area(r)))
    known = [o["height_m"] for o, _ in buildings if _known_height(o.get("height_m"))]
    area_mismatch = [o.get("id") for o, a in buildings
                     if _number(o.get("footprint_area_m2")) and abs(a-o["footprint_area_m2"]) > max(.5, a*.005)]
    ratio = option["gfa_m2"]/computed if option and option["gfa_m2"] and computed else None
    ok = (_number(recorded) and abs(computed-recorded) <= max(.01, computed*1e-6) and
          delta is not None and abs(delta) <= tol)
    return {"parcel_area_m2": round(computed, 3), "recorded_polygon_area_m2": recorded,
            "eum_area_m2": official, "delta_m2": None if delta is None else round(delta, 3),
            "tolerance_m2": tol, "building_count": len(buildings),
            "unknown_height_count": len(buildings)-len(known),
            "tallest_known_height_m": max(known) if known else None,
            "footprint_area_mismatch_ids": area_mismatch,
            "selected_option_id": option["id"] if option else None,
            "gfa_to_parcel_area_ratio": None if ratio is None else round(ratio, 4),
            "ratio_meaning": "SCREENING_RATIO_GFA_OVER_GEOMETRY_AREA_NOT_STATUTORY_FAR",
            "outcome": "PASS" if ok and not area_mismatch else "HOLD"}


DELTA_METRICS = (("gfa_m2", 1, " m²"), ("max_height_m", 1, " m"), ("gfa_ratio", 3, ""))
DELTA_MEANING = "ARITHMETIC_DIFFERENCE_OF_SUPPLIED_KPI_NOT_RANKING_NOT_LEGAL_FAR_NOT_APPROVAL"


def delta_matrix(options, parcel_area, baseline_id):
    """Per-option KPI values and differences against a reference option (mirrored in the studio JS).

    Only supplied KPIs are used. A missing KPI, or a reference without that KPI, gives None
    (shown as Unknown); it is never coerced to 0. gfa_ratio is a screening ratio, not statutory FAR.
    """
    base = next((o for o in options if o["id"] == baseline_id), None)
    if options and base is None:
        raise ReportHold("BASELINE_NOT_FOUND:" + str(baseline_id))

    def values(o):
        g = o["gfa_m2"]
        return {"gfa_m2": g, "max_height_m": o["max_height_m"],
                "gfa_ratio": g / parcel_area if g is not None and parcel_area else None}
    bv = values(base) if base else {}
    rows = []
    for o in options:
        v = values(o)
        delta = {}
        for key, _, _ in DELTA_METRICS:
            if v[key] is None or bv.get(key) is None:
                delta[key] = {"abs": None, "pct": None}
            else:
                d = v[key]-bv[key]
                delta[key] = {"abs": round(d, 4), "pct": round(d/bv[key]*100, 2) if bv[key] else None}
        rows.append({"id": o["id"], "label": o["label"], "is_baseline": o["id"] == baseline_id,
                     "values": {k: None if x is None else round(x, 4) for k, x in v.items()}, "delta": delta})
    return rows


def delta_text(row, key, empty="Unknown", base_word="기준"):
    """Text of one delta cell: signed difference and percent, Unknown when not computable."""
    digits, unit = next((d, u) for k, d, u in DELTA_METRICS if k == key)
    if row["is_baseline"]:
        return base_word
    d = row["delta"][key]
    if d["abs"] is None:
        return empty
    pct = f' ({d["pct"]:+.1f}%)' if d["pct"] is not None else ""
    return f'{d["abs"]:+,.{digits}f}{unit}{pct}'


def _source_is_synthetic(*values):
    return any("SYNTHETIC" in str(v).upper() for v in values)


EVIDENCE_OUTPUTS = {
    "site_source": ("site", ("지도 필지·축척·격자", "KPI 필지 면적, GFA÷면적 비율", "델타 매트릭스 비율 열",
                             "보고서 01–03·07쪽", "PPTX 슬라이드 1–3·7")),
    "context": ("context", ("지도 주변 건물·높이 등급", "높이 미상 건물 수", "보고서 04쪽", "PPTX 슬라이드 2·4")),
    "massing": ("massing", ("대안 카드·델타 매트릭스", "지도 선택안 매스(도식)", "보고서 06쪽 비교표", "PPTX 슬라이드 6")),
    "solar": ("solar", ("일조 안내(미산정 표시)", "보고서 05쪽", "PPTX 슬라이드 5")),
}


def evidence_impact(manifest, site, context, solar, massing, hashes):
    """Source status, hash, evidence class and the outputs that depend on each input.

    No freshness date is derived: the supplied files carry none this report can vouch for.
    """
    docs = {"site_source": site, "context": context, "solar": solar, "massing": massing}
    sections = manifest["sections"]
    out = []
    for key, (category, outputs) in EVIDENCE_OUTPUTS.items():
        doc = docs[key]
        status = sections[key]["status"]
        unknowns = []
        if doc is None:
            klass, integrity = "MISSING", "NOT_PROVIDED"
            unknowns.append("선택 자료 미제공 — 해당 산출물만 비어 있음 (오류 아님)")
        else:
            if key == "site_source":
                synthetic = _source_is_synthetic(doc.get("fixture_class"), (doc.get("parcel") or {}).get("source"))
                integrity = "OK" if status == "PASS" else "HOLD"
                if status != "PASS":
                    unknowns.append("데이터 무결성 HOLD: " + str(doc.get("failure_class") or "출처·면적 불일치"))
            else:
                integrity = "OK"
                synthetic = _source_is_synthetic(doc.get("source_class"), doc.get("fixture_class"),
                                                 doc.get("result_status") if key == "solar" else None,
                                                 doc.get("rule_source_status") if key == "massing" else None)
            if key == "context":
                unknowns.append(f'높이 미상 {(doc.get("completeness") or {}).get("height_unknown_count", "Unknown")}동')
            if key == "solar":
                unknowns.append("일조·그림자 미산정" if _source_is_synthetic(doc.get("result_status")) or
                                doc.get("result_status") in (None, "NOT_CALCULATED") else "일조 범위·한계는 보고서 05쪽")
            if key == "massing":
                unknowns.append("법규 근거 미검증 — " + str(doc.get("rule_source_status") or "Unknown"))
            klass = "SYNTHETIC" if synthetic else ("VERIFIED_SCREENING" if key == "site_source" and status == "PASS" else "SUPPLIED_UNVERIFIED")
        out.append({"key": key, "category": category, "state": status, "integrity": integrity,
                    "evidence_class": klass, "sha256": hashes.get(key), "outputs": list(outputs), "unknowns": unknowns})
    return out


def _studio_payload(manifest, site, ring, context, solar, options, selected, selection, crs, meta, hashes, baseline=None, baseline_kind="NO_OPTIONS", evidence=()):
    synthetic = any("SYNTHETIC" in str(v).upper() for v in (
        (site or {}).get("fixture_class"), (context or {}).get("source_class"),
        ((site or {}).get("parcel") or {}).get("source")))
    obstacles = []
    for o in (context or {}).get("obstacles") or []:
        r = _ring(o.get("footprint_m"))
        h = o.get("height_m")
        obstacles.append({"id": o.get("id"), "name": o.get("name") or "Unnamed", "ring": r,
                          "declared_area_m2": o.get("footprint_area_m2"),
                          "height_m": h if _known_height(h) else None,
                          "height_source": o.get("height_source") or "UNKNOWN",
                          "source_class": o.get("source_class") or (context or {}).get("source_class") or "UNKNOWN"})
    area = manifest["area"]
    area_ref = {"eum_area_m2": area["eum_area_m2"], "recorded_polygon_area_m2": site["parcel"]["polygon_area_m2"]}
    return {"project_id": manifest["project_id"], "pnu": manifest.get("pnu"), "crs": crs, "synthetic": synthetic,
            "source_status": manifest["source_status"], "parcel_ring": ring, "area_ref": area_ref,
            "buildings": obstacles, "bands": meta["bands"], "grid_m": meta["bar_m"], "options": options,
            "massing": [{k: m[k] for k in ("id", "color", "geometry_status", "max_height_m")} for m in meta.get("mass", [])],
            "selected": selected["id"] if selected else None, "built_option": selected["id"] if selected else None,
            "selection_kind": selection, "input_sha256": hashes,
            "baseline": baseline["id"] if baseline else None, "built_baseline": baseline["id"] if baseline else None,
            "baseline_kind": baseline_kind, "delta_meaning": DELTA_MEANING, "evidence": list(evidence),
            "delta_python": {o["id"]: delta_matrix(options, _area(ring), o["id"]) for o in options},
            "solar": {"status": (solar or {}).get("result_status"), "provided": bool(solar),
                      "calculated": False if not solar else (solar.get("result_status") not in (
                          None, "SYNTHETIC_SCENARIO_NOT_CALCULATED", "NOT_CALCULATED"))},
            "recalc_python": dict(recalculate(ring, area_ref, context, selected), ratio_by_option={
                o["id"]: recalculate(ring, area_ref, None, o)["gfa_to_parcel_area_ratio"] for o in options})}
def _card(label, value, note=""):
    return f'<div class="card"><small>{_esc(label)}</small><strong>{_esc(value)}</strong><span>{_esc(note)}</span></div>'


def _page(index, title, eyebrow, body):
    return f'<section class="page" id="page-{index}"><header><span>ARCHI GROW / SITE ANALYSIS<b class="seltag" data-bind="sel-tag"></b></span><span>{index:02d} / {len(PAGES):02d}</span></header><div class="content"><p class="eyebrow">{_esc(eyebrow)}</p><h2>{_esc(title)}</h2>{body}</div><footer><span>Source-bound screening report · no legal certification</span><span>{index:02d}</span></footer></section>'


STUDIO_CSS = r"""body{background:#f3f1ea}.studio{width:min(1240px,100%);margin:0 auto 34px}.topbar{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;padding:6px 2px 18px}.topbar h1{font-size:30px;letter-spacing:-.03em;margin:4px 0 0}.chips{display:flex;gap:8px;flex-wrap:wrap}.chip{font-size:12px;padding:6px 11px;border-radius:99px;background:#e3ebe2;color:#25574f;border:1px solid #c5d6c8}.chip.warn{background:#fdebf2;color:#9a1f52;border-color:#f1bfd3}.chip.ok{background:#dcefe3;color:#17623f}.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:16px}.kpi{background:#fbfaf5;border:1px solid #dcdacc;border-radius:12px;padding:16px 18px}.kpi small{display:block;color:#66786f;font-size:12px}.kpi strong{display:block;font-size:24px;margin:8px 0 4px;letter-spacing:-.02em}.kpi span{font-size:12px;color:#66786f}.studio-grid{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;align-items:start}.mapcard,.panel,.box{min-width:0}.kpi{min-width:0;overflow-wrap:anywhere}.mapcard{background:#fbfaf5;border:1px solid #dcdacc;border-radius:12px;padding:12px;position:relative}.toolbar{display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap}.btn{border:1px solid #b9cbbd;background:#fff;color:#18433d;border-radius:8px;padding:9px 13px;font-size:13px;cursor:pointer;min-height:40px}.btn:hover{background:#eef5ee}.btn:focus-visible,.bld:focus-visible,#studio-map:focus-visible,input:focus-visible{outline:3px solid #e0457f;outline-offset:2px}.btn.primary{background:#184c45;color:#fff;border-color:#184c45}.btn.primary:hover{background:#226358}.btn[disabled]{opacity:.5;cursor:not-allowed}.zoomlabel{margin-left:auto;font-size:12px;color:#66786f}.mapwrap{position:relative;border-radius:8px;overflow:hidden;touch-action:none}#studio-map{display:block;width:100%;height:auto;max-height:68vh;cursor:grab;background:#e8f0e6}#studio-map.drag{cursor:grabbing}.tip{position:absolute;pointer-events:none;background:#123b37;color:#fff;font-size:12px;padding:7px 10px;border-radius:7px;display:none;white-space:nowrap;z-index:3}.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:#4d6660;margin-top:10px}.legend i{display:inline-block;width:14px;height:14px;margin-right:5px;vertical-align:-2px;border:1px solid #587377}.panel{display:grid;gap:14px}.box{background:#fbfaf5;border:1px solid #dcdacc;border-radius:12px;padding:15px 16px}.box h3{margin:0 0 11px;font-size:13px;letter-spacing:.06em;color:#25574f}.opt{display:flex;gap:10px;padding:10px;border:1px solid #d8e2d6;border-radius:9px;margin-bottom:8px;cursor:pointer;align-items:flex-start;background:#fff}.opt:has(input:checked){border-color:#184c45;background:#eaf3ec}.opt small{display:block;color:#66786f;font-size:11px}.lay{display:flex;gap:9px;margin:9px 0;font-size:13px;align-items:center}.panel input{accent-color:#184c45}dl{margin:0;display:grid;grid-template-columns:96px 1fr;gap:6px 10px;font-size:13px}dt{color:#66786f}dd{margin:0;overflow-wrap:anywhere}.out{font-size:12px;line-height:1.7;color:#35514a;margin-top:10px;white-space:pre-wrap;font-family:Consolas,monospace}.out b.ok{color:#17623f}.out b.hold{color:#9a1f52}.note2{font-size:12px;color:#66786f;line-height:1.5;margin:8px 0 0}.btnrow{display:flex;gap:8px;flex-wrap:wrap}.seltag{margin-left:10px;color:#c0245f}.page tr.sel td{background:#fdebf2;font-weight:700}@media(max-width:1100px){.studio-grid{grid-template-columns:minmax(0,1fr)}.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:850px){nav{display:flex;align-items:center;gap:4px;overflow-x:auto;padding:10px 12px}nav h1{margin:0 14px 0 0;font-size:15px;white-space:nowrap}nav a{white-space:nowrap;border:0;padding:8px 10px}main{min-width:0}}@media(max-width:560px){.kpis{gap:10px}.kpi strong{font-size:19px}.topbar h1{font-size:23px}.btn{flex:1 1 auto}}@media(max-width:850px){body{max-width:100%;overflow-x:hidden}nav{max-width:100vw;box-sizing:border-box}main{width:100%;max-width:100vw;margin:0;padding:10px;overflow-x:hidden}.studio{width:100%;max-width:100%;min-width:0}.topbar,.topbar>*{min-width:0}.topbar h1{overflow-wrap:anywhere;word-break:break-word}.page,.content{width:100%;max-width:100%;min-width:0}.agenda li{grid-template-columns:minmax(0,1fr)}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.studio-grid{grid-template-columns:minmax(0,1fr)}.topbar{display:block}.topbar h1{font-size:20px}.chips{margin-top:12px}.mapcard,.panel{max-width:100%;width:100%}.btnrow .btn{min-width:0}}.context-print-note{display:none}.option-compare{margin-bottom:16px}.compare-heading{display:flex;gap:12px;align-items:baseline;justify-content:space-between;flex-wrap:wrap;margin-bottom:8px}.compare-heading h2{font-size:16px;margin:0;color:#184c45;letter-spacing:0}.compare-heading span{font-size:11px;color:#66786f}.compare-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.compare-card{min-width:0;text-align:left;background:#fbfaf5;border:1px solid #dcdacc;padding:13px;border-radius:11px;display:grid;gap:7px;cursor:pointer;color:#183633;overflow-wrap:anywhere}.compare-card:hover{border-color:#2f7566}.compare-card.active{border:2px solid #184c45;background:#eaf3ec;padding:12px}.compare-card:focus-visible{outline:3px solid #e0457f;outline-offset:2px}.compare-card>span:not(.compare-head){display:flex;justify-content:space-between;gap:10px;font-size:12px;flex-wrap:wrap}.compare-card strong{font-size:14px}.compare-card small{font-size:10px;color:#637b72;overflow-wrap:anywhere}.compare-head{display:flex;justify-content:space-between;gap:8px}.compare-head b{font-size:15px}.page-previews{margin-top:20px}.preview-heading{font-size:10px;letter-spacing:.18em;color:#a5dac3;margin:7px 9px}.page-preview{display:flex;align-items:center;gap:9px;padding:8px 9px!important;border-bottom:1px solid #38615a!important}.preview-sheet{display:flex;flex:none;flex-direction:column;width:38px;height:51px;background:#e8efea;border-radius:2px;padding:5px;color:#285b50}.preview-index{font-size:9px;font-weight:bold}.preview-lines{display:grid;gap:3px;margin-top:5px}.preview-lines i{display:block;height:3px;background:#9abcb0}.preview-lines i:nth-child(2){width:76%;background:#e6a9bd}.preview-lines i:nth-child(3){width:54%}.preview-caption{display:grid;gap:4px;min-width:0;font-size:11px}.preview-caption b{font-weight:600}.preview-caption small{color:#a5dac3;font-size:10px;overflow-wrap:anywhere}@media(max-width:850px){.page-previews{display:flex;gap:6px;overflow-x:auto;margin-top:10px}.page-preview{min-width:165px}.compare-grid{grid-template-columns:repeat(3,minmax(195px,1fr));overflow-x:auto;padding-bottom:8px}}@media(max-width:560px){.compare-grid{display:flex;overflow-x:auto;scroll-snap-type:x mandatory}.compare-card{min-width:78%;scroll-snap-align:start}}@media print{.option-compare,.page-previews{display:none!important}}@media print{.studio,nav{display:none}.page{width:296mm;min-height:206mm;height:206mm} .page:last-child{break-after:auto;page-break-after:auto}tr[data-print-overflow="1"]{display:none}.context-print-note{display:block;font-size:11px;color:#52645f;margin-top:8px}}"""

DESKTOP_CSS = r"""
.decision{display:grid;grid-template-columns:minmax(0,1fr);gap:16px;margin-top:16px;align-items:start}.decision .box{min-width:0}
.mxwrap{overflow-x:auto}.mx{border-collapse:collapse;width:100%;font-size:13px;background:#fff}.mx th,.mx td{padding:10px 12px;border-bottom:1px solid #e1e8df;text-align:left;vertical-align:middle}
.mx thead th{background:#e5eee8;color:#2e6258;font-size:12px;white-space:nowrap}.mx tbody th small{display:block;color:#66786f;font-weight:400;font-size:11px}.mx .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.mx .dl{font-weight:700;color:#184c45}
.mx tbody th{min-width:9.5em}.mx td:nth-child(2){white-space:nowrap}.mx tbody tr{cursor:pointer}.mx tbody tr:hover td,.mx tbody tr:hover th{background:#f3f8f3}.mx tr.sel td,.mx tr.sel th{background:#eaf3ec}.mx tr.base th{box-shadow:inset 4px 0 0 #c0245f}.mx tr.base .dl{color:#9a1f52}
.badge{display:inline-block;font-style:normal;font-size:11px;color:#9a1f52;font-weight:700;margin-top:2px}.basepick{display:inline-flex;gap:6px;align-items:center;cursor:pointer;font-size:12px}
.mx-summary{margin:12px 2px 0;font-size:13px;line-height:1.6;color:#25574f}
.evidence .ev{border:1px solid #dcdacc;border-radius:9px;padding:10px 12px;margin-top:9px;background:#fff;min-width:0}.evidence .ev header{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.evidence .ev b{font-size:13px}
.tag{font-size:11px;padding:3px 8px;border-radius:99px;border:1px solid #c5d6c8;background:#e3ebe2;color:#25574f}.tag.cls{background:#fff4d6;border-color:#e8d18a;color:#6d5410}.ev-MISSING .tag.cls{background:#eee;border-color:#ccc;color:#555}.ev-VERIFIED_SCREENING .tag.cls{background:#dcefe3;border-color:#a9d3b8;color:#17623f}
.tag.int.HOLD{background:#fdebf2;border-color:#f1bfd3;color:#9a1f52;font-weight:700}.tag.int.NOT_PROVIDED{background:#f0f0ee;border-color:#d4d4cf;color:#555}
.sha{display:block;margin:7px 0 4px;font-size:11px;color:#47615e;overflow-wrap:anywhere}.ev .dep,.ev .unk{margin:4px 0 0;font-size:12px;line-height:1.5;color:#35514a}.ev .unk{color:#8a3a14}.ev-sum{font-size:12px;margin:0 0 4px;color:#25574f}
@media(min-width:1180px){.studio{width:min(1560px,100%)}.studio-grid{grid-template-columns:minmax(0,1fr) 380px}.evgrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}#studio-map{max-height:calc(100vh - 150px)}.kpis{gap:16px}}
@media(min-width:1700px){.studio-grid{grid-template-columns:minmax(0,1fr) 420px}.decision{grid-template-columns:minmax(0,1.9fr) minmax(0,1fr)}.evgrid{grid-template-columns:minmax(0,1fr)}}
@media(max-width:560px){.mx{font-size:12px}.mx th,.mx td{padding:8px}}
@media print{.decision{display:none!important}}
"""

STUDIO_JS = r"""(function(){
var D=JSON.parse(document.getElementById('studio-data').textContent);
var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
var svg=$('#studio-map'),vp=$('#viewport',svg),tip=$('#tip');
var S={k:1,tx:0,ty:0,opt:D.selected,base:D.baseline,rows:[],bld:null,runs:0},BASE=parseFloat(svg.getAttribute('data-scale-px-per-m')),BAR0=parseFloat(svg.getAttribute('data-bar-m'));
var fmt=function(n,d){d=d==null?1:d;return (n==null||!isFinite(n))?'Unknown':Number(n).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d})};
function area(r){var s=0;for(var i=0;i<r.length;i++){var a=r[i],b=r[(i+1)%r.length];s+=a[0]*b[1]-b[0]*a[1]}return Math.abs(s)/2}
function opt(id){return D.options.filter(function(o){return o.id===id})[0]||null}
function legalLabel(value){var s=String(value||'근거 없음');return s.indexOf('NOT_VERIFIED')===0?'가상·법규 미검증':s}
function svgPt(e){var p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform(svg.getScreenCTM().inverse())}
function apply(){vp.setAttribute('transform','translate('+S.tx+' '+S.ty+') scale('+S.k+')');
 var ppm=BASE*S.k,m=BAR0,cand=[1,2,5],best=null;for(var e=-2;e<=5&&!best;e++)for(var i=0;i<3;i++){var v=cand[i]*Math.pow(10,e);if(v*ppm>=55&&v*ppm<=170){best=v;break}}
 m=best||BAR0;var sc=$('#scale',svg);sc.querySelector('path').setAttribute('d','M70 716h'+(m*ppm).toFixed(2));sc.querySelector('text').textContent=(m>=1?m:m.toFixed(2))+' m';
 sc.querySelector('rect').setAttribute('width',(m*ppm+30).toFixed(1));$('#zoomlabel').textContent='×'+S.k.toFixed(2)}
function zoomAt(f,p){var nk=Math.max(.5,Math.min(60,S.k*f));p=p||{x:400,y:400};S.tx=p.x-(p.x-S.tx)*nk/S.k;S.ty=p.y-(p.y-S.ty)*nk/S.k;S.k=nk;apply()}
function reset(){S.k=1;S.tx=0;S.ty=0;apply()}
svg.addEventListener('wheel',function(e){e.preventDefault();zoomAt(Math.exp(-e.deltaY*.0016),svgPt(e))},{passive:false});
var drag=null;
svg.addEventListener('pointerdown',function(e){if(e.button>0)return;drag={x:e.clientX,y:e.clientY,tx:S.tx,ty:S.ty,id:e.pointerId,moved:false}});
svg.addEventListener('pointermove',function(e){if(!drag)return;var dx=e.clientX-drag.x,dy=e.clientY-drag.y;
 if(!drag.moved&&Math.abs(dx)+Math.abs(dy)<5)return;if(!drag.moved){drag.moved=true;svg.classList.add('drag');try{svg.setPointerCapture(drag.id)}catch(x){}}
 var u=800/svg.getBoundingClientRect().width;S.tx=drag.tx+dx*u;S.ty=drag.ty+dy*u;apply();hideTip()});
function endDrag(){if(drag&&drag.moved){var d=drag;setTimeout(function(){if(drag===d)drag=null},0)}else drag=null;svg.classList.remove('drag')}
svg.addEventListener('pointerup',endDrag);svg.addEventListener('pointercancel',endDrag);
svg.addEventListener('keydown',function(e){var k=e.key,st=40;
 if(k==='ArrowLeft'){S.tx+=st}else if(k==='ArrowRight'){S.tx-=st}else if(k==='ArrowUp'){S.ty+=st}else if(k==='ArrowDown'){S.ty-=st}
 else if(k==='+'||k==='='){zoomAt(1.25)}else if(k==='-'||k==='_'){zoomAt(.8)}else if(k==='0'){reset()}
 else if((k==='Enter'||k===' ')&&e.target.classList&&e.target.classList.contains('bld')){pick(e.target)}else return;
 e.preventDefault();apply()});
$('#z-in').onclick=function(){zoomAt(1.25)};$('#z-out').onclick=function(){zoomAt(.8)};$('#z-reset').onclick=reset;
function bdata(id){return D.buildings.filter(function(b){return b.id===id})[0]}
function hideTip(){tip.style.display='none'}
function showTip(el,e){var b=bdata(el.getAttribute('data-id'));if(!b)return;
 tip.textContent=b.id+' · '+(b.height_m==null?'높이 미상 (UNKNOWN)':b.height_m+' m')+' · '+b.height_source;
 var r=$('.mapwrap').getBoundingClientRect(),br=el.getBoundingClientRect(),x=(e&&e.clientX!=null?e.clientX:br.left)-r.left+12,y=(e&&e.clientY!=null?e.clientY:br.top)-r.top+12;
 tip.style.display='block';tip.style.left=Math.max(4,Math.min(x,r.width-tip.offsetWidth-6))+'px';tip.style.top=Math.max(4,y)+'px'}
function pick(el){$$('.bld.on',svg).forEach(function(n){n.classList.remove('on')});el.classList.add('on');var b=bdata(el.getAttribute('data-id'));S.bld=b.id;
 var ca=area(b.ring);$('#bld-info').innerHTML='<dl><dt>ID</dt><dd>'+b.id+'</dd><dt>이름</dt><dd>'+b.name+'</dd><dt>바닥면적</dt><dd>'+fmt(ca)+' m² (좌표 계산)'+(b.declared_area_m2!=null?' / 자료 '+fmt(b.declared_area_m2)+' m²':'')+'</dd><dt>높이</dt><dd>'+(b.height_m==null?'<b>미상 (UNKNOWN)</b> — 0으로 쓰지 않음':b.height_m+' m')+'</dd><dt>높이 출처</dt><dd>'+b.height_source+'</dd><dt>자료 구분</dt><dd>'+b.source_class+'</dd></dl>'}
$$('.bld',svg).forEach(function(el){el.addEventListener('mouseenter',function(e){showTip(el,e)});el.addEventListener('mousemove',function(e){showTip(el,e)});el.addEventListener('mouseleave',hideTip);el.addEventListener('focus',function(){showTip(el)});el.addEventListener('blur',hideTip);
 el.addEventListener('click',function(){if(drag&&drag.moved)return;pick(el)})});
$$('[data-layer]').forEach(function(c){c.addEventListener('change',function(){var id=c.getAttribute('data-layer');$$('#'+id+',[data-copy-of="'+id+'"]').forEach(function(l){l.style.display=c.checked?'':'none'})})});
function ratio(o,pa){return o&&o.gfa_m2&&pa?o.gfa_m2/pa:null}
function bind(k,v){$$('[data-bind="'+k+'"]').forEach(function(n){n.textContent=v})}
var DM={gfa_m2:[1,' m²'],max_height_m:[1,' m'],gfa_ratio:[3,'']};
function sgn(v,d){return (v<0?'-':'+')+fmt(Math.abs(v),d)}
function dRows(opts,pa,bid){var b=opts.filter(function(o){return o.id===bid})[0]||null;
 function vals(o){var g=o.gfa_m2==null?null:o.gfa_m2;return {gfa_m2:g,max_height_m:o.max_height_m==null?null:o.max_height_m,gfa_ratio:(g!=null&&pa)?g/pa:null}}
 var bv=b?vals(b):null;
 return opts.map(function(o){var v=vals(o),d={};Object.keys(DM).forEach(function(k){var x=v[k],y=bv?bv[k]:null;
  d[k]=(x==null||y==null)?{abs:null,pct:null}:{abs:x-y,pct:y?(x-y)/y*100:null}});
  return {id:o.id,label:o.label,is_baseline:o.id===bid,values:v,delta:d}})}
function dText(r,k){if(r.is_baseline)return '기준';var d=r.delta[k];if(d.abs==null)return 'Unknown';return sgn(d.abs,DM[k][0])+DM[k][1]+(d.pct==null?'':' ('+sgn(d.pct,1)+'%)')}
function renderDelta(){if(!D.options.length)return;var rows=dRows(D.options,area(D.parcel_ring),S.base);S.rows=rows;
 rows.forEach(function(r){Object.keys(DM).forEach(function(k){var t=dText(r,k);
  $$('[data-mx-cell="'+r.id+':'+k+'"],[data-d="'+r.id+':'+k+'"]').forEach(function(c){c.textContent=t})})});
 $$('tr[data-mx-opt]').forEach(function(t){var id=t.getAttribute('data-mx-opt');t.classList.toggle('sel',id===S.opt);t.classList.toggle('base',id===S.base);
  t.querySelector('[data-badge]').textContent=(id===S.base?'기준 ':'')+(id===S.opt?'선택':'')});
 $$('tr[data-opt-id]').forEach(function(t){t.classList.toggle('base',t.getAttribute('data-opt-id')===S.base)});
 $$('input[name=base]').forEach(function(i){i.checked=i.value===S.base});
 var b=opt(S.base),sr=rows.filter(function(r){return r.id===S.opt})[0];
 bind('base-label',b?b.label:'—');
 bind('mx-summary',!sr||!b?'':(sr.is_baseline?'선택안 '+sr.label+' = 기준안: 차이 없음 (기준).':'선택안 '+sr.label+' vs 기준안 '+b.label+' — GFA '+dText(sr,'gfa_m2')+' · 최고높이 '+dText(sr,'max_height_m')+' · GFA÷면적 '+dText(sr,'gfa_ratio')+' · 산술 차이일 뿐 우열·허가 판단 아님.'));
 var st=$('#static-note');if(st)st.hidden=!D.built_option||(S.opt===D.built_option&&S.base===D.built_baseline)}
function setBase(id,persist){if(!opt(id))return;S.base=id;renderDelta();
 if(persist){try{localStorage.setItem('archigrow.site.base.'+D.project_id,S.base)}catch(x){}}}
function setOpt(id,persist){var o=opt(id);if(!o&&D.options.length)return;S.opt=o?o.id:null;var pa=area(D.parcel_ring);
 bind('sel-label',o?o.label:'안 없음');bind('sel-gfa',o?fmt(o.gfa_m2)+' m²':'—');bind('sel-height',o?fmt(o.max_height_m)+' m':'—');
 var r=ratio(o,pa);bind('sel-ratio',r==null?'—':r.toFixed(3));bind('sel-legal',o?legalLabel(o.legal_source):'—');bind('sel-tag',o?' · OPTION '+o.label:'');
 $$('tr[data-opt-id]').forEach(function(t){t.classList.toggle('sel',t.getAttribute('data-opt-id')===S.opt)});
 $$('[data-compare-opt]').forEach(function(c){var on=c.getAttribute('data-compare-opt')===S.opt;c.classList.toggle('active',on);c.setAttribute('aria-pressed',on?'true':'false')});
 $$('input[name=opt]').forEach(function(i){i.checked=i.value===S.opt});
 $$('.mass').forEach(function(g){g.style.display=g.getAttribute('data-opt')===S.opt?'':'none'});
 document.body.setAttribute('data-selected-option',S.opt||'');
 renderDelta();
 if(persist){try{localStorage.setItem('archigrow.site.opt.'+D.project_id,S.opt)}catch(x){}}}
$$('input[name=opt]').forEach(function(i){i.addEventListener('change',function(){setOpt(i.value,true)})});
$$('[data-compare-opt]').forEach(function(c){c.addEventListener('click',function(){setOpt(c.getAttribute('data-compare-opt'),true)})});
$$('input[name=base]').forEach(function(i){i.addEventListener('change',function(){setBase(i.value,true)})});
$$('tr[data-mx-opt]').forEach(function(t){t.addEventListener('click',function(e){if(e.target.closest&&e.target.closest('label,input'))return;setOpt(t.getAttribute('data-mx-opt'),true)})});
function recalc(){var pa=area(D.parcel_ring),a=D.area_ref,delta=pa-a.eum_area_m2,tol=Math.max(1,a.eum_area_m2*.005),
 known=D.buildings.filter(function(b){return b.height_m!=null}).map(function(b){return b.height_m}),
 mism=D.buildings.filter(function(b){var c=area(b.ring);return b.declared_area_m2!=null&&Math.abs(c-b.declared_area_m2)>Math.max(.5,c*.005)}).map(function(b){return b.id}),
 o=opt(S.opt),r=ratio(o,pa),P=D.recalc_python,pr=o?P.ratio_by_option[o.id]:null;
 var ok=Math.abs(pa-a.recorded_polygon_area_m2)<=Math.max(.01,pa*1e-6)&&Math.abs(delta)<=tol&&!mism.length;
 var R={parcel_area_m2:+pa.toFixed(3),eum_area_m2:a.eum_area_m2,delta_m2:+delta.toFixed(3),tolerance_m2:tol,building_count:D.buildings.length,unknown_height_count:D.buildings.length-known.length,
  tallest_known_height_m:known.length?Math.max.apply(null,known):null,footprint_area_mismatch_ids:mism,selected_option_id:o?o.id:null,gfa_to_parcel_area_ratio:r==null?null:+r.toFixed(4),outcome:ok?'PASS':'HOLD'};
 var same=Math.abs(R.parcel_area_m2-P.parcel_area_m2)<.001&&Math.abs(R.delta_m2-P.delta_m2)<.001&&R.building_count===P.building_count&&R.unknown_height_count===P.unknown_height_count&&R.tallest_known_height_m===P.tallest_known_height_m&&R.outcome===P.outcome&&(r==null?pr==null:Math.abs(R.gfa_to_parcel_area_ratio-pr)<.00011);
 R.matches_python_baseline=same;R.input_sha256=D.input_sha256;R.ratio_meaning=P.ratio_meaning;S.runs++;window.__lastRecalc=R;
 $('#recalc-out').innerHTML='<b class="'+(ok?'ok':'hold')+'">'+R.outcome+'</b> · 실행 #'+S.runs+'\n필지 면적(좌표) '+fmt(pa,3)+' m²\nEUM 면적 '+fmt(a.eum_area_m2)+' m² · Δ '+fmt(delta,3)+' m² (허용 '+fmt(tol,1)+')\n주변 건물 '+R.building_count+' · 높이 미상 '+R.unknown_height_count+(R.tallest_known_height_m!=null?' · 최고(확인분) '+R.tallest_known_height_m+' m':'')+'\n선택안 '+(o?o.label:'—')+' · GFA/면적 '+(r==null?'—':r.toFixed(3))+' (스크리닝 비율, 법정 용적률 아님)\nPython 기준값 대조: '+(same?'일치':'<b class="hold">불일치</b>')+'\n입력 sha256: '+Object.keys(D.input_sha256).map(function(k){return k+' '+String(D.input_sha256[k]).slice(0,12)}).join(', ');
 return R}
$('#recalc').onclick=recalc;
var TEST=location.search.indexOf('selftest=1')>=0;
function save(name,type,text){window.__lastExport={name:name,type:type,text:text};var u=URL.createObjectURL(new Blob([text],{type:type})),a=document.createElement('a');a.href=u;a.download=name;if(!TEST){document.body.appendChild(a);a.click();a.remove()}setTimeout(function(){URL.revokeObjectURL(u)},2000)}
function stem(){return D.project_id+'_'+(S.opt||'NO_OPTION')}
$('#exp-svg').onclick=function(){var c=svg.cloneNode(true);c.removeAttribute('id');c.removeAttribute('tabindex');var oldmeta=c.querySelector('#site-source-selection');if(oldmeta)oldmeta.remove();$$('[tabindex]',c).forEach(function(n){n.removeAttribute('tabindex');n.removeAttribute('role')});
 c.querySelector('#viewport').removeAttribute('transform');var o=opt(S.opt);
 var meta={schema:'ARCHIGROW_SITE_MAP_EXPORT_V1',project_id:D.project_id,pnu:D.pnu,crs:D.crs,synthetic:D.synthetic,selected_option:o,baseline_option:opt(S.base),input_sha256:D.input_sha256,note:'Screening geometry; no legal approval; solar not calculated'};
 var m=document.createElementNS('http://www.w3.org/2000/svg','metadata');m.textContent=JSON.stringify(meta);c.insertBefore(m,c.firstChild);
 var t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x','70');t.setAttribute('y','60');t.setAttribute('font-size','18');t.setAttribute('font-family','Arial,sans-serif');t.setAttribute('fill','#203735');t.textContent=D.project_id+' · '+(o?o.label+' ('+o.id+')':'no option')+(D.synthetic?' · SYNTHETIC':'');c.appendChild(t);
 $$('.on',c).forEach(function(n){n.classList.remove('on')});
 save('site_map_'+stem()+'.svg','image/svg+xml',new XMLSerializer().serializeToString(c))};
$('#exp-json').onclick=function(){var R=recalc();save('site_receipt_'+stem()+'.json','application/json',JSON.stringify({schema:'ARCHIGROW_SITE_STUDIO_RECEIPT_V1',project_id:D.project_id,pnu:D.pnu,selected_option:opt(S.opt),baseline_option:opt(S.base),comparison:{baseline_id:S.base,meaning:D.delta_meaning,rows:S.rows},recalc:R},null,2))};
$('#exp-print').onclick=function(){window.print()};
var px=$('#exp-pptx');px.disabled=true;
if(location.protocol.indexOf('http')===0){fetch('/api/health').then(function(r){return r.json()}).then(function(j){if(j&&j.studio==='ARCHIGROW_SITE_STUDIO'){D.bridge=true;px.disabled=false;var sn=$('#snap-state');if(sn)sn.textContent='· 서버 스냅샷 '+j.snapshot;$('#exp-note').textContent='로컬 서버 연결됨: PPTX는 현재 선택안으로 재생성됩니다.'}}).catch(function(){})}
px.onclick=function(){fetch('/api/export?format=pptx&option='+encodeURIComponent(S.opt||'')+'&baseline='+encodeURIComponent(S.base||'')).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.blob()}).then(function(b){var u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='site_analysis_'+stem()+'.pptx';document.body.appendChild(a);a.click();a.remove();window.__lastExport={name:a.download,type:'pptx',size:b.size}}).catch(function(e){$('#exp-note').textContent='PPTX 내보내기 실패: '+e.message})};
var want=null,wantB=null;try{var qs=new URLSearchParams(location.search);want=qs.get('opt')||localStorage.getItem('archigrow.site.opt.'+D.project_id);wantB=qs.get('base')||localStorage.getItem('archigrow.site.base.'+D.project_id)}catch(x){}
S.base=opt(wantB)?wantB:D.baseline;setOpt(opt(want)?want:D.selected,false);apply();
function selftest(){var C=[],ok=function(n,v,x){C.push({check:n,pass:!!v,detail:x===undefined?null:x})};
 var r=svg.getBoundingClientRect(),k0=S.k;svg.dispatchEvent(new WheelEvent('wheel',{deltaY:-400,clientX:r.left+100,clientY:r.top+100,bubbles:true,cancelable:true}));ok('wheel_zoom_in',S.k>k0,S.k);
 var tx0=S.tx;svg.dispatchEvent(new PointerEvent('pointerdown',{clientX:r.left+200,clientY:r.top+200,pointerId:7,button:0,bubbles:true}));svg.dispatchEvent(new PointerEvent('pointermove',{clientX:r.left+260,clientY:r.top+230,pointerId:7,bubbles:true}));svg.dispatchEvent(new PointerEvent('pointerup',{clientX:r.left+260,clientY:r.top+230,pointerId:7,bubbles:true}));ok('drag_pan',S.tx!==tx0,[tx0,S.tx]);
 $('#z-reset').click();ok('reset',S.k===1&&S.tx===0&&S.ty===0);
 svg.dispatchEvent(new KeyboardEvent('keydown',{key:'+',bubbles:true}));ok('keyboard_zoom',S.k>1);$('#z-reset').click();
 var lay=$('[data-layer=buildings]');lay.click();ok('layer_off',$('#buildings').style.display==='none');lay.click();ok('layer_on',$('#buildings').style.display==='');
 setTimeout(function(){var hu=$('.bld.hu',svg);if(hu){hu.dispatchEvent(new MouseEvent('click',{bubbles:true}));var t=$('#bld-info').textContent;ok('unknown_height_not_zero',t.indexOf(hu.getAttribute('data-id'))>=0&&/미상 \(UNKNOWN\)/.test(t)&&!/높이\s*0\s*m/.test(t),t)}else ok('unknown_height_not_zero',D.buildings.every(function(b){return b.height_m!=null}),'no unknown building in data');
 D.options.forEach(function(o){var inp=$('input[name=opt][value="'+o.id+'"]');inp.click();
  ok('option_'+o.id+'_kpi',$('[data-bind=sel-gfa]').textContent===fmt(o.gfa_m2)+' m²'&&$('[data-bind=sel-label]').textContent===o.label,$('[data-bind=sel-gfa]').textContent);
  ok('option_'+o.id+'_report_row',$('tr[data-opt-id="'+o.id+'"]').classList.contains('sel')&&$$('tr.sel[data-opt-id]').length===1);
  var cc=$('[data-compare-opt="'+o.id+'"]');if(cc)ok('option_'+o.id+'_comparison_selected',cc.classList.contains('active')&&cc.getAttribute('aria-pressed')==='true'&&$$('.compare-card.active').length===1);
  ok('option_'+o.id+'_header_tag',$('.seltag').textContent.indexOf(o.label)>=0);
  var vis=$$('.mass',svg).filter(function(g){return g.style.display!=='none'});if(D.massing.length)ok('option_'+o.id+'_massing_only_selected',vis.length===1&&vis[0].getAttribute('data-opt')===o.id,vis.length);
  var R=recalc();ok('option_'+o.id+'_recalc_matches_python',R.matches_python_baseline&&R.selected_option_id===o.id,R);
  $('#exp-svg').click();ok('option_'+o.id+'_svg_export_bound',window.__lastExport.text.indexOf('"id":"'+o.id+'"')>=0&&window.__lastExport.name.indexOf(o.id)>=0&&(!D.massing.length||(window.__lastExport.text.match(/class="mass"[^>]*>/g)||[]).filter(function(t){return t.indexOf('display: none')<0&&t.indexOf('display:none')<0}).length===1));
  $('#exp-json').click();ok('option_'+o.id+'_json_export_bound',JSON.parse(window.__lastExport.text).selected_option.id===o.id)});
 if(D.options.length){var cc=$('[data-compare-opt="'+D.options[D.options.length-1].id+'"]');if(cc){cc.click();ok('comparison_card_click_selects_option',S.opt===D.options[D.options.length-1].id&&cc.getAttribute('aria-pressed')==='true'&&document.body.getAttribute('data-selected-option')===S.opt)}}
 if(D.options.length>1){var o0=D.options[0].id,oN=D.options[D.options.length-1].id;$('input[name=opt][value="'+oN+'"]').click();
  D.options.forEach(function(b){$('input[name=base][value="'+b.id+'"]').click();
   ok('baseline_'+b.id+'_selected_independent',S.base===b.id&&S.opt===oN&&$$('tr[data-mx-opt].base').length===1&&$('tr[data-mx-opt].base').getAttribute('data-mx-opt')===b.id&&$$('tr[data-opt-id].base').length===1&&$$('tr[data-mx-opt].sel').length===1);
   var bad=[];D.delta_python[b.id].forEach(function(pr){var jr=S.rows.filter(function(r){return r.id===pr.id})[0];
    Object.keys(DM).forEach(function(k){var a=jr.delta[k],c=pr.delta[k],cell=$('[data-mx-cell="'+pr.id+':'+k+'"]'),pc=$('[data-d="'+pr.id+':'+k+'"]');
     if((a.abs==null)!==(c.abs==null)||(a.abs!=null&&Math.abs(a.abs-c.abs)>1e-3)||(a.pct==null)!==(c.pct==null)||(a.pct!=null&&Math.abs(a.pct-c.pct)>.011)||jr.is_baseline!==pr.is_baseline)bad.push(['num',b.id,pr.id,k,a,c]);
     if(!cell||cell.textContent!==dText(jr,k)||(pc&&pc.textContent!==cell.textContent))bad.push(['text',b.id,pr.id,k])})});
   ok('baseline_'+b.id+'_delta_matches_python',bad.length===0,bad)});
  $('input[name=base][value="'+o0+'"]').click();$('input[name=opt][value="'+o0+'"]').click();ok('option_change_keeps_baseline',S.base===o0&&S.opt===o0);
  $('input[name=base][value="'+oN+'"]').click();$('#exp-json').click();var rc=JSON.parse(window.__lastExport.text);ok('receipt_carries_baseline',rc.comparison.baseline_id===oN&&rc.baseline_option.id===oN&&rc.comparison.rows.length===D.options.length);
  $('tr[data-mx-opt="'+o0+'"]').click();ok('matrix_row_click_selects_option',S.opt===o0&&S.base===oN);
  $('input[name=base][value="'+D.baseline+'"]').click()}
 var ar=dRows([{id:'a',label:'a',gfa_m2:100,max_height_m:10},{id:'b',label:'b',gfa_m2:150,max_height_m:8}],10,'a'),bb=ar[1];
 ok('delta_arithmetic',bb.delta.gfa_m2.abs===50&&bb.delta.gfa_m2.pct===50&&bb.delta.max_height_m.abs===-2&&bb.delta.max_height_m.pct===-20&&Math.abs(bb.delta.gfa_ratio.abs-5)<1e-9&&dText(bb,'gfa_m2')==='+50.0 m² (+50.0%)'&&dText(bb,'max_height_m')==='-2.0 m (-20.0%)'&&dText(bb,'gfa_ratio')==='+5.000 (+50.0%)'&&dText(ar[0],'gfa_m2')==='기준',ar);
 var ur=dRows([{id:'a',label:'a',gfa_m2:100,max_height_m:null},{id:'b',label:'b',gfa_m2:null,max_height_m:30}],10,'a');
 ok('unknown_kpi_stays_unknown',ur[1].delta.gfa_m2.abs===null&&dText(ur[1],'gfa_m2')==='Unknown'&&dText(ur[1],'max_height_m')==='Unknown'&&ur[1].values.gfa_ratio===null&&dText(ur[1],'gfa_ratio')==='Unknown'&&ur[0].delta.max_height_m.abs===null,ur);
 ok('no_horizontal_overflow',document.documentElement.scrollWidth<=window.innerWidth+1&&$('.decision').getBoundingClientRect().right<=window.innerWidth+1,[document.documentElement.scrollWidth,window.innerWidth]);
 ok('massing_colors_distinct',new Set(D.massing.map(function(m){return m.color})).size===D.massing.length,D.massing.length);
 var a=recalc(),b=recalc();ok('recalc_repeatable',JSON.stringify(a)===JSON.stringify(b));
 ok('solar_not_rendered_as_result',!$('#studio-map [id*=shadow],#studio-map [id*=sun]')&&/미산정|미제공/.test($('#solar-note').textContent));
 var pre=document.createElement('pre');pre.id='selftest-result';pre.textContent=JSON.stringify({all_pass:C.every(function(c){return c.pass}),checks:C});document.body.appendChild(pre);document.title='SELFTEST_DONE'},30)}
if(location.search.indexOf('selftest=1')>=0)window.addEventListener('load',function(){setTimeout(selftest,50)});
})();"""


EV_CLASS = {"SYNTHETIC": "가상(합성) 자료", "VERIFIED_SCREENING": "스크리닝 일치 확인 (법적 인증 아님)",
            "SUPPLIED_UNVERIFIED": "제공됨 · 미검증", "MISSING": "자료 없음"}
EV_INTEGRITY = {"OK": "무결성 OK", "HOLD": "데이터 무결성 HOLD", "NOT_PROVIDED": "선택 자료 없음 (HOLD 아님)"}
EV_NAME = {"site_source": "site · 필지 출처", "context": "context · 주변 건물", "massing": "massing · 매스 대안", "solar": "solar · 일조"}


def _workbench_html(payload):
    """Delta matrix (initial state from the shared Python function) and evidence impact panel."""
    options, base = payload["options"], payload["baseline"]
    if options:
        rows = payload["delta_python"][base]
        body = ''.join(
            f'<tr data-mx-opt="{_esc(r["id"])}" class="{"sel " if r["id"] == payload["selected"] else ""}{"base" if r["is_baseline"] else ""}">'
            f'<th scope="row"><b>{_esc(r["label"])}</b><small>{_esc(r["id"])}</small><i class="badge" data-badge></i></th>'
            f'<td><label class="basepick"><input type="radio" name="base" value="{_esc(r["id"])}"{" checked" if r["is_baseline"] else ""} aria-label="{_esc(r["label"])}을(를) 기준안으로"> 기준</label></td>'
            + ''.join(f'<td class="num" data-mx-val="{_esc(r["id"])}:{k}">{_fmt(r["values"][k], d)}{u}</td><td class="num dl" data-mx-cell="{_esc(r["id"])}:{k}">{_esc(delta_text(r, k))}</td>'
                      for k, d, u in DELTA_METRICS) + '</tr>' for r in rows)
        matrix = ('<div class="mxwrap"><table class="mx" id="mx"><thead><tr><th>안</th><th>기준안</th><th>연면적 GFA</th><th>Δ GFA</th><th>최고높이</th><th>Δ 높이</th>'
                  '<th>GFA÷도형면적</th><th>Δ 비율</th></tr></thead><tbody id="mx-body">' + body + '</tbody></table></div>'
                  '<p class="mx-summary" id="mx-summary" data-bind="mx-summary" role="status" aria-live="polite"></p>')
    else:
        matrix = '<p class="note2">massing_result 미제공 — 비교할 대안이 없습니다 (선택 자료 없음, 오류 아님).</p>'
    ev = payload["evidence"]
    count = lambda c: sum(1 for e in ev if e["evidence_class"] == c)
    cards = ''.join(
        f'<article class="ev ev-{e["evidence_class"]}" data-ev="{e["key"]}" data-category="{e["category"]}" data-ev-class="{e["evidence_class"]}" data-integrity="{e["integrity"]}">'
        f'<header><b>{_esc(EV_NAME[e["key"]])}</b><span class="tag cls">{_esc(EV_CLASS[e["evidence_class"]])}</span>'
        f'<span class="tag int {e["integrity"]}">{_esc(EV_INTEGRITY[e["integrity"]])}</span></header>'
        f'<code class="sha" title="{_esc(e["sha256"] or "")}">{"sha256 " + e["sha256"][:16] + "…" if e["sha256"] else "sha256 없음 (자료 미제공)"}</code>'
        f'<p class="dep">영향 산출물: {_esc(" · ".join(e["outputs"]))}</p>'
        + (f'<p class="unk">미확정: {_esc(" · ".join(e["unknowns"]))}</p>' if e["unknowns"] else '') + '</article>' for e in ev)
    evidence = ('<div class="box evidence" id="evidence-impact"><h3>증거 영향</h3>'
                f'<p class="ev-sum" data-ev-summary>스크리닝 확인 {count("VERIFIED_SCREENING")} · 가상 {count("SYNTHETIC")} · 제공됨·미검증 {count("SUPPLIED_UNVERIFIED")} · 없음 {count("MISSING")}'
                ' <span id="snap-state"></span></p>'
                '<p class="note2">수집·갱신 일자는 표시하지 않습니다 (자료가 검증 가능한 일자를 제공하지 않음). 최신 공식 데이터셋이라는 뜻이 아닙니다.</p>'
                + '<div class="evgrid">' + cards + '</div></div>')
    return ('<section class="decision" id="decision" aria-label="의사결정 워크벤치"><div class="box matrix"><div class="compare-heading"><h2>시나리오 델타 비교</h2>'
            '<span>기준안 대비 공급 KPI의 산술 차이 · 우열·법정 용적률·허가 판단 아님 · 미제공 KPI는 Unknown</span></div>'
            + matrix + '</div>' + evidence + '</section>')


def _studio_html(manifest, payload, svg, sel):
    area = manifest["area"]
    live = svg.replace('<svg ', '<svg id="studio-map" tabindex="0" ', 1)
    a = payload["recalc_python"]
    opts = ''.join(f'<label class="opt"><input type="radio" name="opt" value="{_esc(o["id"])}"{" checked" if o["id"] == payload["selected"] else ""}><span><b>{_esc(o["label"])}</b><small>{_esc(o["id"])} · GFA {_fmt(o["gfa_m2"])} m² · {_fmt(o["max_height_m"])} m</small></span></label>'
                   for o in payload["options"]) or '<p class="note2">massing_result 미제공 또는 안 없음 — 안 선택 불가. 형상이 없는 안은 요약 수치만 표시합니다.</p>'
    bands = payload["bands"]
    names = ["낮음", "중간", "높음"] if len(bands) == 3 else [""]
    colors = ["#dde8e3", "#b9cec7", "#8fb0a6"]
    legend = ''.join(f'<span><i style="background:{colors[i]}"></i>{names[i]} {lo:g}–{hi:g} m</span>' for i, (lo, hi) in enumerate(bands))
    chips = (('<span class="chip warn">SYNTHETIC · 가상 자료</span>' if payload["synthetic"] else '') +
             f'<span class="chip {"ok" if manifest["source_status"] == "PASS" else "warn"}">SOURCE {manifest["source_status"]}</span>'
             f'<span class="chip">{_esc(payload["crs"])}</span><span class="chip">법적 승인 아님</span>')
    mass_legend = ''.join(f'<span><i style="background:{m["color"]}"></i>{_esc(o["label"].split()[0])}안 {_fmt(o["max_height_m"])} m</span>'
                          for m in payload["massing"] for o in payload["options"] if o["id"] == m["id"] and m["geometry_status"] != "NO_KPI_NO_GEOMETRY")
    if any(m["geometry_status"].startswith("SCHEMATIC") for m in payload["massing"]):
        mass_legend += '<span class="schem">매스 = KPI 기반 도식 (설계 형상·건폐율·이격 아님)</span>'
    solar = payload["solar"]
    if not solar["provided"]:
        solar_txt = "일조 연구 미제공 — 미산정. 지도에 그림자·일조 결과를 그리지 않습니다."
    elif not solar["calculated"]:
        solar_txt = f"일조·그림자 미산정 (상태 {_esc(solar['status'])}). 지도에는 그림자·일조 결과를 그리지 않습니다."
    else:
        solar_txt = f"일조 연구 상태 {_esc(solar['status'])} — 범위와 한계는 보고서 05쪽을 따르며 법적 일조 판정이 아닙니다. 지도 위 그림자는 그리지 않습니다 (미제공)."
    kpis = (f'<div class="kpi"><small>필지 면적 (좌표 계산)</small><strong>{_fmt(a["parcel_area_m2"])} m²</strong><span>EUM {_fmt(area["eum_area_m2"])} m² · Δ {_fmt(a["delta_m2"])} m²</span></div>'
            f'<div class="kpi"><small>주변 건물 (제공 자료)</small><strong>{a["building_count"]}동</strong><span>높이 미상 {a["unknown_height_count"]}동 · 0으로 쓰지 않음</span></div>'
            f'<div class="kpi"><small>선택안</small><strong data-bind="sel-label">{_esc(sel["label"]) if sel else "없음"}</strong><span>GFA <b data-bind="sel-gfa">—</b> · 최고 <b data-bind="sel-height">—</b></span></div>'
            f'<div class="kpi"><small>GFA ÷ 필지 면적 (스크리닝)</small><strong data-bind="sel-ratio">—</strong><span>법정 용적률 아님 · 근거 <b data-bind="sel-legal">—</b></span></div>')
    comparison = ""
    if payload["options"]:
        comparisons = []
        for o in payload["options"]:
            ratio = o["gfa_m2"] / a["parcel_area_m2"] if _number(o["gfa_m2"]) and a["parcel_area_m2"] else None
            mass_kind = next((m["geometry_status"] for m in payload["massing"] if m["id"] == o["id"]), "NO_GEOMETRY")
            legal_display = ("가상·법규 미검증" if str(o["legal_source"]).startswith("NOT_VERIFIED")
                             else str(o["legal_source"]))
            mass_display = ("KPI 기반 개념 도식" if str(mass_kind).startswith("SCHEMATIC")
                            else "제공 형상·미검증" if mass_kind == "SUPPLIED_UNVERIFIED"
                            else "형상 없음")
            comparisons.append(
                f'<button type="button" class="compare-card" data-compare-opt="{_esc(o["id"])}" '
                f'aria-pressed="{"true" if o["id"] == payload["selected"] else "false"}">'
                f'<span class="compare-head"><b>{_esc(o["label"])}</b><small>{_esc(o["id"])}</small></span>'
                f'<span>연면적 <strong>{_fmt(o["gfa_m2"])} m²</strong></span>'
                f'<span>최고높이 <strong>{_fmt(o["max_height_m"])} m</strong></span>'
                f'<span>GFA ÷ 대지 도형 면적 <strong>{_fmt(ratio,3)}</strong></span>'
                f'<small title="법규: {_esc(o["legal_source"])} / 도형: {_esc(mass_kind)}">법규 {_esc(legal_display)} · {_esc(mass_display)}</small></button>'
            )
        comparison = ('<section class="option-compare" aria-label="대안 간 비교"><div class="compare-heading">'
                      '<h2>설계 대안 비교</h2><span>개략지표 비교 · 법정 용적률/허가 가능성 판단 아님</span>'
                      '</div><div class="compare-grid">' + "".join(comparisons) + '</div></section>')
    workbench = _workbench_html(payload)
    return (f'<section class="studio" id="studio" aria-label="Site studio"><div class="topbar"><div><p class="eyebrow">ARCHI GROW · SITE STUDIO</p><h1>{_esc(manifest["project_id"])}</h1></div><div class="chips">{chips}</div></div>'
            f'<div class="kpis">{kpis}</div>{comparison}<div class="studio-grid"><div class="mapcard"><div class="toolbar">'
            '<button type="button" class="btn" id="z-in" aria-label="확대">＋</button><button type="button" class="btn" id="z-out" aria-label="축소">－</button><button type="button" class="btn" id="z-reset" aria-label="보기 초기화">초기화</button><span class="zoomlabel" id="zoomlabel">×1.00</span></div>'
            f'<div class="mapwrap">{live}<div class="tip" id="tip" role="tooltip"></div></div>'
            f'<div class="legend"><span><i style="background:#e0457f55;border-color:#c0245f"></i>필지</span>{legend}<span><i style="background:repeating-linear-gradient(45deg,#8a9893 0 2px,#eceeed 2px 6px)"></i>높이 미상</span><span>격자 {payload["grid_m"]:g} m (투영 좌표)</span>{mass_legend}</div>'
            '<p class="note2">휠/버튼/＋－0 키로 확대·초기화, 드래그 또는 방향키로 이동. 건물에 마우스·Tab 포커스 후 Enter로 선택. 도로·수목은 자료가 없어 그리지 않습니다.</p></div>'
            f'<aside class="panel"><div class="box"><h3>매스 안 선택</h3>{opts}<p class="note2" id="static-note" hidden>정적 파일(site_analysis.pptx·site_map.svg)은 빌드 시점의 선택안({_esc(sel["label"] if sel else "")})·기준안으로 만들어졌습니다. 현재 선택·기준과 같은 PPTX는 로컬 서버 내보내기를 사용하세요.</p></div>'
            '<div class="box"><h3>레이어</h3><label class="lay"><input type="checkbox" data-layer="parcel" checked> 필지</label><label class="lay"><input type="checkbox" data-layer="buildings" checked> 주변 건물</label><label class="lay"><input type="checkbox" data-layer="massing" checked> 선택안 매스 (도식)</label><label class="lay"><input type="checkbox" data-layer="heights" checked> 높이 라벨</label><label class="lay"><input type="checkbox" data-layer="grid" checked> 격자</label></div>'
            '<div class="box"><h3>선택한 건물</h3><div id="bld-info" aria-live="polite"><p class="note2">건물을 선택하세요. 높이 미상은 “미상”으로 표시됩니다.</p></div></div>'
            '<div class="box"><h3>재계산 · 내보내기</h3><div class="btnrow"><button type="button" class="btn primary" id="recalc">재계산</button><button type="button" class="btn" id="exp-svg">SVG</button><button type="button" class="btn" id="exp-json">영수증 JSON</button><button type="button" class="btn" id="exp-print">인쇄/PDF</button><button type="button" class="btn" id="exp-pptx">PPTX</button></div>'
            '<div class="out" id="recalc-out" role="status" aria-live="polite">재계산을 누르면 현재 입력 자료에서 면적·건물 수·미상 높이를 다시 계산해 Python 기준값과 대조합니다.</div>'
            '<p class="note2" id="exp-note">PPTX는 로컬 서버 없이는 현재 선택안으로 재생성할 수 없어 비활성입니다 (python TOOLS/ARCHIGROW_SITE_STUDIO.py serve …).</p></div>'
            f'<div class="box"><h3>일조</h3><p class="note2" id="solar-note">{solar_txt}</p></div></aside></div>{workbench}</section>')


def _html(manifest, site, context, solar, massing, svg, payload):
    pid, pnu = manifest["project_id"], manifest.get("pnu")
    sel_label = next((o["label"] for o in payload["options"] if o["id"] == payload["selected"]), None) if payload else None
    base_label = next((o["label"] for o in payload["options"] if o["id"] == payload["baseline"]), None) if payload else None
    page_svg = svg.replace(' tabindex="0" role="button"', '').replace(' id="', ' data-copy-of="')
    area = manifest.get("area") or {}
    sections = manifest["sections"]
    e = (site or {}).get("eum") or {}
    parcel = (site or {}).get("parcel") or {}
    pages = []
    cards = ''.join([_card("Project", pid, "Exact project binding"), _card("Parcel PNU", pnu or "Unknown"),
                     _card("EUM visible area", _fmt(area.get("eum_area_m2"))+" m²", "Web view; not a legal certificate"),
                     _card("Geometry area", _fmt(area.get("polygon_area_m2"))+" m²", "VWorld cadastral screening polygon")])
    pages.append(_page(1, "The site, as evidenced", "01 / Identity", f'<div class="hero"><div><p class="lede">A parcel level reading of available source evidence, with unresolved decisions kept visible.</p><p class="muted">{_esc(e.get("address") or "Address not evidenced")}</p></div><div class="status">SOURCE {sections["site_source"]["status"]}<br>DESIGN {manifest["design_status"]}{"<br>OPTION <span data-bind=\"sel-label\">"+_esc(sel_label)+"</span>" if sel_label else ""}</div></div><div class="cards">{cards}</div><p class="note">Available report sections: {manifest["available_section_count"]} of {len(PAGES)}. Missing source sections remain explicit on their pages.</p>'))
    map_body = f'<div class="maplayout"><div class="mapbox">{page_svg}</div><div><div class="cards one">{_card("Projected CRS", parcel.get("projected_crs") or "Unknown")}{_card("EUM area", _fmt(area.get("eum_area_m2"))+" m²")}{_card("Polygon area", _fmt(area.get("polygon_area_m2"))+" m²")}{_card("Delta / tolerance", _fmt(area.get("delta_m2"))+" / "+_fmt(area.get("tolerance_m2"))+" m²", area.get("result") or "Not comparable")}</div></div></div><p class="note">Map scale and GN (grid north) use the declared projected metre CRS. Toggle source layers in the screen controls. No surrounding streets or transit are inferred.</p>' if site and parcel else '<div class="empty">Parcel geometry is unavailable. Supply the existing site source receipt with a matched PNU and projected polygon.</div>'
    pages.append(_page(2, "Boundary and measured area", "02 / Geometry", map_body))
    source_rows = ["<tr><th>Evidence</th><th>State</th><th>Boundary</th></tr>"]
    for name, detail, limit in [
        ("EUM web view", e.get("document_status") or "Missing", "Online view only; obtain legal record separately"),
        ("VWorld cadastral polygon", parcel.get("source") or "Missing", "Screening geometry; not survey authority"),
        ("Area comparison", area.get("result") or "Unavailable", "Tolerance is a screening check, not title verification"),
        ("Parcel collector", (site or {}).get("failure_class") or (site or {}).get("status") or "Missing", "Design parameter HOLD does not invalidate a matched parcel")]:
        source_rows.append(f'<tr><td>{_esc(name)}</td><td>{_esc(detail)}</td><td>{_esc(limit)}</td></tr>')
    pages.append(_page(3, "What the sources establish", "03 / Source quality", '<table>'+''.join(source_rows)+'</table><p class="note">Input fingerprints and section status are recorded in analysis_manifest.json. The report does not certify parcel title, zoning or statutory compliance.</p>'))
    obstacles = (context or {}).get("obstacles") or []
    if context:
        comp = context.get("completeness") or {}
        rows = [f'<tr data-print-overflow="{1 if i >= 8 else 0}"><td>{_esc(o.get("id"))}</td><td>{_esc(o.get("name") or "Unnamed")}</td><td>{_fmt(o.get("footprint_area_m2"))} m²</td><td>{_fmt(o.get("height_m")) if _number(o.get("height_m")) and o["height_m"]>0 else "Unknown"}</td><td>{_esc(o.get("height_source") or "UNKNOWN")}</td></tr>' for i, o in enumerate(obstacles)]
        print_excerpt = (f'<p class="context-print-note">Print excerpt: first 8 of {len(obstacles)} building rows shown. '
                         f'The remaining {len(obstacles)-8} rows stay available in the on-screen table and source context_obstacles.json.</p>'
                         if len(obstacles) > 8 else "")
        body = f'<div class="cards">{_card("Buildings", len(obstacles))}{_card("Unknown heights", comp.get("height_unknown_count", "Unknown"))}{_card("Source", context.get("source_class") or "Unknown")}</div><table><tr><th>ID</th><th>Name</th><th>Footprint</th><th>Height m</th><th>Height basis</th></tr>{"".join(rows)}</table>{print_excerpt}<p class="note">Reported and assumed heights retain their source class. Unknown height is never shown as zero.</p>'
    else:
        body = '<div class="empty">No context_obstacles.json was supplied. Nearby buildings and heights remain unevaluated.</div>'
    pages.append(_page(4, "Buildings around the parcel", "04 / Context", body))
    if solar:
        claims = solar.get("claims") or {}
        dates = solar.get("dates") or []
        date_rows = ''.join(f'<tr><td>{_esc(d.get("id") or d.get("date"))}</td><td>{_esc(d.get("date"))}</td><td>{_esc(solar.get("result_status"))}</td></tr>' for d in dates)
        body = f'<div class="cards">{_card("Study state", solar.get("result_status") or "Unknown")}{_card("Metric", claims.get("metric_kind") or "Unknown")}{_card("Dates", len(dates))}{_card("Unknown height impact", (solar.get("context") or {}).get("unknown_height_affected_receiver_count", "Unknown"))}</div><table><tr><th>Case</th><th>Date</th><th>Study status</th></tr>{date_rows}</table><p class="note">Geometric direct sun only. Legal sunlight compliance: {_esc(claims.get("legal_sunlight_compliance") or "NOT_EVALUATED")}. Meteorological sunshine and irradiance are separate unavailable measures.</p>'
    else:
        body = '<div class="empty">No solar study report was supplied. Sun exposure and shadows are unevaluated; this page contains no calculated result.</div>'
    pages.append(_page(5, "Solar study, when supplied", "05 / Environment", body))
    if massing:
        options = massing.get("options") or []
        bound = _options(massing)
        drows = payload["delta_python"][payload["baseline"]] if payload.get("baseline") else []
        rows = ''.join(f'<tr data-opt-id="{_esc(b["id"])}"{SEL_ATTR if b["id"] == payload["selected"] else ""}><td>{_esc(b["label"])}</td><td>{_fmt(b["gfa_m2"])} m²</td><td>{_fmt(b["max_height_m"])} m</td>'
                       + ''.join(f'<td data-d="{_esc(b["id"])}:{k}">{_esc(delta_text(r, k))}</td>' for k, _, _ in DELTA_METRICS)
                       + f'<td>{_esc(b["legal_source"])}</td></tr>' for b, r in zip(bound, drows))
        body = f'<div class="cards">{_card("Options", len(options))}{_card("Rule source", massing.get("rule_source_status") or "Unknown")}{_card("Legal feasibility", "NOT AUTHORIZED")}{_card("Selected option", sel_label or "None", "Follows the studio selection; print uses it")}</div><table><tr><th>Option</th><th>GFA</th><th>Height</th><th>Δ GFA vs baseline</th><th>Δ Height</th><th>Δ GFA/area</th><th>Legal source</th></tr>{rows}</table><p class="note">Baseline: <span data-bind="base-label">{_esc(base_label or "None")}</span> · differences use supplied KPI only; Unknown stays Unknown. These are optional design outputs. Geometry and KPI checks do not establish statutory feasibility.</p>'
    else:
        body = '<div class="empty">No massing_result.json was supplied. Site analysis is available independently of design parameters.</div>'
    pages.append(_page(6, "Design evidence boundary", "06 / Optional design", body))
    gaps = [("Legal parcel record", "Obtain certified source if a legal claim is required"),
            ("Zoning and statutory controls", "Verify current project applicable law and effective date"),
            ("Survey and boundary", "Cross check cadastral screening polygon against measured CAD/survey"),
            ("Context coverage", "Verify building source coverage, date and unknown heights"),
            ("Solar", "Run or review a project bound study before environmental claims")]
    if sections["site_source"]["status"] != "PASS":
        gaps.insert(0, ("Parcel source", "Resolve source identity, area or missing evidence hold"))
    agenda = ''.join(f'<li><b>{_esc(a)}</b><span>{_esc(b)}</span></li>' for a,b in gaps)
    pages.append(_page(7, "What needs verification", "07 / Next evidence", f'<ol class="agenda">{agenda}</ol><p class="note">This report is a source projection. It makes no planning approval, legal area or design capacity claim.</p>'))
    nav = ''.join(f'<a href="#page-{i}" aria-label="Page {i}: {_esc(name)}"><b>{i:02d}</b><span>{_esc(name)}</span></a>' for i,name in enumerate(PAGES,1))
    previews = (
        "PNU " + str(pnu or "Unknown"),
        "도형 면적 " + _fmt(area.get("polygon_area_m2")) + " m²",
        "출처 상태 " + str(sections["site_source"]["status"]),
        "건물 " + str(len(obstacles)) + "동" if context else "건물 근거 없음",
        "일조 " + str((solar or {}).get("result_status") or "미산정"),
        "대안 " + str(len((massing or {}).get("options") or [])) + "개",
        "확인 필요 항목 " + str(len(gaps)) + "개",
    )
    page_previews = ('<div class="page-previews" aria-label="보고서 구성 미리보기">'
                     '<p class="preview-heading">REPORT / 7 SECTIONS</p>' +
                     "".join(f'<a class="page-preview" href="#page-{i}" title="{_esc(name)}">'
                             f'<span class="preview-sheet"><span class="preview-index">{i:02d}</span>'
                             f'<span class="preview-lines"><i></i><i></i><i></i></span></span>'
                             f'<span class="preview-caption"><b>{i:02d} {_esc(name)}</b><small>{_esc(previews[i-1])}</small></span></a>'
                             for i, name in enumerate(PAGES,1)) + '</div>')
    css = """:root{font-family:Arial,'Malgun Gothic',sans-serif;color:#183633;background:#dce5e0}*{box-sizing:border-box}body{margin:0}button,a{font:inherit}nav{position:fixed;top:0;left:0;width:230px;height:100vh;background:#123b37;color:#eaf2ed;padding:26px 16px;overflow:auto}nav h1{font-size:18px;margin:0 0 30px;letter-spacing:.12em}nav a{display:flex;gap:12px;color:#d8e9e1;text-decoration:none;padding:12px 9px;border-bottom:1px solid #38615a;font-size:13px}nav a:hover,nav a:focus{background:#27544c}nav b{color:#a5dac3}.controls{margin-top:27px;font-size:12px}.controls label{display:block;margin:12px 0}.controls input{accent-color:#a5dac3}main{margin-left:230px;padding:26px}.page{width:min(1120px,100%);min-height:720px;background:#f9faf6;margin:0 auto 28px;display:flex;flex-direction:column;box-shadow:0 12px 35px #17383225;break-after:page}.page header,.page footer{display:flex;justify-content:space-between;padding:20px 38px;color:#4b7770;font-size:11px;letter-spacing:.13em;border-bottom:1px solid #cbd8d1}.page footer{border:0;border-top:1px solid #cbd8d1;margin-top:auto}.content{padding:34px 48px 50px}.eyebrow{font-size:11px;color:#258174;letter-spacing:.22em;text-transform:uppercase}h2{font-size:38px;letter-spacing:-.04em;margin:7px 0 30px}.hero{display:flex;justify-content:space-between;gap:50px;padding:30px 0 55px}.lede{font-size:26px;line-height:1.35;max-width:600px}.muted,.note{color:#60776f}.status{background:#184c45;color:#eaf7ee;padding:22px;min-width:190px;line-height:2;font-size:13px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.cards.one{grid-template-columns:1fr}.card{background:#edf3ed;border-top:3px solid #2b8374;padding:16px;min-height:118px}.card small,.card span{display:block;color:#637b72;font-size:11px}.card strong{display:block;margin:12px 0 8px;font-size:20px;overflow-wrap:anywhere}.maplayout{display:grid;grid-template-columns:minmax(0,2fr) minmax(210px,1fr);gap:20px}.mapbox svg{width:100%;height:auto;max-height:500px}.note{font-size:12px;margin-top:25px;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:13px}td,th{text-align:left;padding:13px 10px;border-bottom:1px solid #d3dfd7;vertical-align:top}th{background:#e5eee8;color:#2e6258}.empty{padding:65px;background:#eef2ec;border-left:4px solid #9ab5a7;color:#536b61}.agenda{list-style:none;padding:0}.agenda li{display:grid;grid-template-columns:220px 1fr;gap:20px;padding:19px 0;border-bottom:1px solid #d4dfd7}.agenda span{color:#5b7269}@media(max-width:850px){nav{position:static;width:auto;height:auto}main{margin:0;padding:10px}.content{padding:24px}.cards{grid-template-columns:repeat(2,1fr)}.maplayout{grid-template-columns:1fr}h2{font-size:28px}}@media print{@page{size:A4 landscape;margin:0}html,body{background:white;print-color-adjust:exact;-webkit-print-color-adjust:exact}nav{display:none}main{margin:0;padding:0}.page{width:297mm;min-height:210mm;height:210mm;margin:0;box-shadow:none;overflow:hidden;break-inside:avoid;page-break-inside:avoid}.content{padding:5mm 10mm}.page header,.page footer{padding:3mm 10mm}h2{font-size:22px;margin-bottom:8px}.hero{padding:15px 0 24px}.lede{font-size:20px}.card{min-height:70px}.mapbox svg{max-height:70mm}.maplayout .card{min-height:28px;padding:4px}.maplayout .cards{gap:3px}.maplayout .card strong{font-size:14px;margin:3px 0}.maplayout{gap:8px}table{font-size:10px}td,th{padding:7px}.note{margin-top:3px;font-size:10px}}"""
    sel = next((o for o in payload["options"] if o["id"] == payload["selected"]), None) if payload else None
    studio = _studio_html(manifest, payload, svg, sel) if payload else ""
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c") if payload else "{}"
    js = STUDIO_JS if payload else ""
    studio_nav = '<a href="#studio" aria-label="Site studio"><b>00</b><span>Studio</span></a><a href="#decision" aria-label="Decision workbench"><b>0D</b><span>Decision</span></a>' if payload else ""
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Site analysis · {_esc(pid)}</title><style>{css}{STUDIO_CSS}{DESKTOP_CSS}</style></head><body><nav><h1>ARCHI GROW</h1>{studio_nav}{nav}{page_previews}</nav><main>{studio}{"".join(pages)}</main><script type="application/json" id="studio-data">{data}</script><script>{js}</script></body></html>'


def _pptx(path, manifest, site, context, solar, massing, selected=None, baseline=None):
    """Seven editable native-object slides; source values are never rounded."""
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    ink, green, muted = RGBColor(24, 54, 51), RGBColor(31, 111, 97), RGBColor(91, 114, 105)
    pale, paper = RGBColor(230, 239, 233), RGBColor(250, 251, 247)

    def label(slide, value, x, y, w, h=.42, size=15, color=ink, bold=False):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        frame = box.text_frame
        frame.clear(); frame.word_wrap = True
        frame.margin_left = frame.margin_right = Inches(.02)
        frame.margin_top = frame.margin_bottom = 0
        p = frame.paragraphs[0]
        p.text = str(value if value is not None else "Unknown")
        p.font.name = "Arial"; p.font.size = Pt(size)
        p.font.color.rgb = color; p.font.bold = bold
        return box

    def slide(number, title, section):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.background.fill.solid(); s.background.fill.fore_color.rgb = paper
        label(s, "ARCHI GROW  /  SITE ANALYSIS", .55, .25, 9, .3, 10, green, True)
        label(s, f"{number:02d} / 07", 11.95, .25, .8, .3, 10, green, True)
        if selected:
            label(s, f"OPTION {selected['label']} ({selected['id']})", 4.6, .25, 6.8, .3, 10, RGBColor(192, 36, 95), True)
        label(s, section.upper(), .55, .72, 9, .3, 11, green, True)
        label(s, title, .55, 1.05, 12.2, .65, 27, ink, True)
        label(s, "Source-bound screening report  /  no legal certification", .55, 7.03, 10, .26, 9, muted)
        label(s, f"{number:02d}", 12.2, 7.03, .5, .26, 9, muted)
        return s

    def fact(s, heading, value, x, y, w=5.8):
        label(s, heading.upper(), x, y, w, .26, 10, green, True)
        label(s, value, x, y+.31, w, .75, 18, ink, True)

    def table(s, headings, data, widths, y=2.45, max_rows=8):
        shown = data[:max_rows]
        row_h = min(.54, 3.85 / (len(shown)+1))
        t = s.shapes.add_table(len(shown)+1, len(headings), Inches(.55), Inches(y),
                               Inches(sum(widths)), Inches(row_h*(len(shown)+1))).table
        for j, width in enumerate(widths): t.columns[j].width = Inches(width)
        for i, row in enumerate([headings]+shown):
            for j, value in enumerate(row):
                c = t.cell(i, j); c.text = str(value if value is not None else "Unknown")
                c.fill.solid(); c.fill.fore_color.rgb = pale if i == 0 else paper
                c.margin_left = c.margin_right = Inches(.06)
                c.margin_top = c.margin_bottom = Inches(.02)
                for p in c.text_frame.paragraphs:
                    p.font.name = "Arial"; p.font.size = Pt(10 if len(c.text)>55 else 12)
                    p.font.bold = i == 0; p.font.color.rgb = ink
        if len(data)>len(shown):
            label(s, f"{len(data)-len(shown)} additional rows in source JSON; first {len(shown)} shown.",
                  .55, y+row_h*(len(shown)+1)+.1, 12, .35, 10, muted)

    area, sections = manifest.get("area") or {}, manifest["sections"]
    e, parcel = site.get("eum") or {}, site.get("parcel") or {}
    s = slide(1, "The site, as evidenced", "Identity")
    label(s, e.get("address") or "Address not evidenced", .55, 1.9, 12, .55, 20)
    fact(s, "Project ID", manifest["project_id"], .55, 2.75)
    fact(s, "Parcel PNU", manifest.get("pnu") or "Unknown", 6.7, 2.75)
    fact(s, "EUM visible area", f"{area.get('eum_area_m2', 'Unknown')} m²", .55, 4.15)
    fact(s, "Polygon area", f"{area.get('polygon_area_m2', 'Unknown')} m²", 6.7, 4.15)
    label(s, f"SOURCE {sections['site_source']['status']}  /  DESIGN {manifest['design_status']}" +
          (f"  /  OPTION {selected['label']}" if selected else ""),
          .55, 5.62, 12, .4, 15, green, True)
    label(s, "EUM online view is not a legal certificate; polygon area is cadastral screening evidence.",
          .55, 6.27, 12, .4, 12, muted)

    s = slide(2, "Boundary and measured area", "Parcel geometry")
    if parcel.get("polygon_local_m"):
        ring = _ring(parcel["polygon_local_m"])
        xs, ys = [p[0] for p in ring], [p[1] for p in ring]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        blds = []
        for o in (context or {}).get("obstacles") or []:
            r = _ring(o.get("footprint_m")); blds.append((o, r))
        allp = ring + [p for _, r in blds for p in r]
        x0, x1 = min(p[0] for p in allp), max(p[0] for p in allp)
        y0, y1 = min(p[1] for p in allp), max(p[1] for p in allp)
        scale = min(5/max(x1-x0, 1), 4.5/max(y1-y0, 1))
        for o, r in blds:
            bc = [(int(Inches(1+(x-x0)*scale)), int(Inches(6.4-(y-y0)*scale))) for x, y in r]
            bb = s.shapes.build_freeform(*bc[0], scale=1.0)
            bb.add_line_segments(bc[1:], close=True)
            bs = bb.convert_to_shape(); bs.name = "Context building " + str(o.get("id"))
            bs.fill.solid(); bs.fill.fore_color.rgb = RGBColor(207, 216, 213) if _known_height(o.get("height_m")) else RGBColor(236, 238, 237)
            bs.line.color.rgb = RGBColor(88, 115, 119); bs.line.width = Pt(1)
            label(s, f"{o['height_m']:g} m" if _known_height(o.get("height_m")) else "?", 1+(sum(p[0] for p in r)/len(r)-x0)*scale-.3, 6.4-(sum(p[1] for p in r)/len(r)-y0)*scale-.1, .6, .2, 8, ink)
        coords = [(int(Inches(1+(x-x0)*scale)), int(Inches(6.4-(y-y0)*scale))) for x,y in ring]
        builder = s.shapes.build_freeform(*coords[0], scale=1.0)
        builder.add_line_segments(coords[1:], close=True)
        shape = builder.convert_to_shape(); shape.name = "Editable parcel boundary"
        shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(246, 190, 211)
        shape.line.color.rgb = RGBColor(192, 36, 95); shape.line.width = Pt(2.5)
        mass = [m for m in (_schematic_massing(ring, massing, _options(massing)) if massing and selected else [])
                if m["id"] == selected["id"] and m.get("ring")]
        for m in mass:
            mc = [(int(Inches(1+(x-x0)*scale)), int(Inches(6.4-(y-y0)*scale))) for x, y in m["ring"]]
            mb = s.shapes.build_freeform(*mc[0], scale=1.0)
            mb.add_line_segments(mc[1:], close=True)
            ms = mb.convert_to_shape(); ms.name = "Massing " + m["geometry_status"] + " " + m["id"]
            ms.fill.solid(); ms.fill.fore_color.rgb = RGBColor.from_string(m["color"][1:].upper())
            ms.line.color.rgb = RGBColor(255, 255, 255); ms.line.width = Pt(1.5)
            label(s, f"{selected['label']} · {selected['max_height_m'] if selected['max_height_m'] is not None else '?'} m  (schematic, from KPI; not design geometry)",
                  1, 6.55, 5.6, .3, 9, RGBColor.from_string(m["color"][1:].upper()), True)
        label(s, "N ↑  (grid north)", 6.5, 2.0, 2, .4, 13, green, True)
        fact(s, "Projected CRS", parcel.get("projected_crs") or "Unknown", 8.3, 2.0, 4.4)
        fact(s, "EUM area", f"{area.get('eum_area_m2')} m²", 8.3, 3.25, 4.4)
        fact(s, "Polygon area", f"{area.get('polygon_area_m2')} m²", 8.3, 4.45, 4.4)
        label(s, f"Delta {area.get('delta_m2')} m² / tolerance {area.get('tolerance_m2')} m²",
              8.3, 5.65, 4.4, .48, 12, green, True)
        label(s, "Projected metre geometry; survey and title verification remain open.",
              8.3, 6.3, 4.4, .5, 10, muted)
    else:
        label(s, "Parcel geometry unavailable; source evidence remains on HOLD.", .55, 2.4, 12, .8, 18)

    s = slide(3, "What the sources establish", "Source quality")
    table(s, ["Evidence", "State", "Boundary"], [
        ["EUM web view", e.get("document_status") or "Missing", "Online view; obtain legal record"],
        ["VWorld cadastral polygon", parcel.get("source") or "Missing", "Screening; not survey authority"],
        ["Area comparison", area.get("result") or "Unavailable", "Tolerance is not title verification"],
        ["Parcel collector", site.get("failure_class") or site.get("status") or "Missing", "Design parameter HOLD can coexist with matched parcel"],
    ], [3, 4.4, 4.8], y=2.0)
    label(s, "Input fingerprints and section status: analysis_manifest.json. No zoning or statutory certification.",
          .55, 5.9, 12, .5, 12, muted)

    s = slide(4, "Buildings around the parcel", "Building context")
    if context:
        obstacles = context.get("obstacles") or []
        label(s, f"{len(obstacles)} buildings / unknown heights: {(context.get('completeness') or {}).get('height_unknown_count', 'Unknown')} / source: {context.get('source_class') or 'Unknown'}",
              .55, 1.83, 12, .5, 13, green, True)
        table(s, ["ID", "Name", "Footprint", "Height m", "Height basis"],
              [[o.get("id") or "Unknown", o.get("name") or "Unnamed",
                f"{o.get('footprint_area_m2', 'Unknown')} m²",
                str(o.get("height_m")) if _number(o.get("height_m")) and o["height_m"]>0 else "Unknown",
                o.get("height_source") or "UNKNOWN"] for o in obstacles],
              [1.2, 3.1, 2.2, 1.6, 4.1])
        label(s, "Unknown height is never zero. Reported and assumed heights retain their source class.",
              .55, 6.42, 12, .35, 11, muted)
    else:
        label(s, "No context_obstacles.json supplied. Nearby buildings and heights remain unevaluated.",
              .55, 2.15, 12, .7, 17)

    s = slide(5, "Solar study, when supplied", "Solar evidence")
    if solar:
        claims = solar.get("claims") or {}
        label(s, f"Study: {solar.get('result_status') or 'Unknown'} / metric: {claims.get('metric_kind') or 'Unknown'}",
              .55, 1.8, 12, .55, 13, green, True)
        table(s, ["Case", "Date", "Study status"],
              [[d.get("id") or d.get("date") or "Unknown", d.get("date") or "Unknown",
                solar.get("result_status") or "Unknown"] for d in solar.get("dates") or []],
              [3, 3, 6.2], max_rows=7)
        label(s, f"Legal sunlight compliance: {claims.get('legal_sunlight_compliance') or 'NOT_EVALUATED'}.",
              .55, 6.05, 12, .4, 12, green, True)
        label(s, "Geometric direct sun only. Meteorological sunshine and irradiance are separate measures.",
              .55, 6.45, 12, .3, 10, muted)
    else:
        label(s, "No solar study supplied. Sun exposure and shadows are unevaluated.", .55, 2.15, 12, .7, 17)

    s = slide(6, "Design evidence boundary", "Optional design")
    if massing:
        label(s, f"Rule source: {massing.get('rule_source_status') or 'Unknown'} / legal feasibility: NOT AUTHORIZED",
              .55, 1.8, 12, .5, 13, green, True)
        bound = _options(massing)
        rows6 = delta_matrix(bound, area.get("polygon_area_m2"), baseline["id"]) if baseline else []
        table(s, ["Option", "GFA", "Height", "Δ GFA vs baseline", "Δ Height", "Δ GFA/area", "Selected", "Baseline"],
              [[b["label"], f"{b['gfa_m2'] if b['gfa_m2'] is not None else 'Unknown'} m²",
                f"{b['max_height_m'] if b['max_height_m'] is not None else 'Unknown'} m",
                delta_text(r, "gfa_m2", base_word="(base)"), delta_text(r, "max_height_m", base_word="(base)"),
                delta_text(r, "gfa_ratio", base_word="(base)"),
                "SELECTED" if selected and b["id"] == selected["id"] else "",
                "BASELINE" if r["is_baseline"] else ""] for b, r in zip(bound, rows6)],
              [2.1, 1.6, 1.2, 2.2, 1.6, 1.4, 1.1, 1.0], max_rows=7)
        if baseline:
            label(s, f"Baseline {baseline['label']} ({baseline['id']}): differences use supplied KPI only; Unknown stays Unknown. "
                  "Legal source: " + "; ".join(sorted({b["legal_source"] for b in bound})),
                  .55, 5.55, 12, .4, 10, muted)
        if selected and selected["gfa_m2"] and area.get("polygon_area_m2"):
            label(s, f"Selected {selected['label']}: GFA / geometry area = {selected['gfa_m2']/area['polygon_area_m2']:.3f} (screening ratio, not statutory FAR)",
                  .55, 6.0, 12, .35, 11, green, True)
        label(s, "Geometry and KPI checks do not establish statutory feasibility.", .55, 6.4, 12, .35, 11, muted)
    else:
        label(s, "No massing result supplied. Site analysis is independent of design parameters.",
              .55, 2.15, 12, .7, 17)

    s = slide(7, "What needs verification", "Verification agenda")
    agenda = [("Legal parcel record", "Obtain certified source if a legal claim is required"),
              ("Zoning and statutory controls", "Verify applicable law and effective date"),
              ("Survey and boundary", "Cross-check screening polygon against CAD or survey"),
              ("Context coverage", "Verify building coverage, date, and unknown heights"),
              ("Solar", "Review project-bound study before environmental claims")]
    if sections["site_source"]["status"] != "PASS":
        agenda.insert(0, ("Parcel source", "Resolve source identity, area, or missing evidence"))
    for i, (name, action) in enumerate(agenda):
        y = 1.85+i*.72
        label(s, f"{i+1:02d}  {name}", .55, y, 4.1, .45, 14, ink, True)
        label(s, action, 4.8, y, 7.9, .48, 13, muted)
    label(s, "This report makes no planning approval, legal area, or design capacity claim.",
          .55, 6.35, 12, .4, 12, green, True)
    prs.save(path)


def build(project_id, site_source_receipt, out_dir, context=None, solar=None, massing=None, option=None, baseline=None):
    if not project_id or not str(project_id).strip():
        raise ReportHold("PROJECT_ID_REQUIRED")
    site, site_ref = _read(site_source_receipt, project_id, "site_source")
    optional = {}
    for key, path, schema in (("context", context, "ARCHIGROW_CONTEXT_OBSTACLES_V1"),
                              ("solar", solar, "ARCHIGROW_SOLAR_STUDY_REPORT_V1"),
                              ("massing", massing, "ARCHIGROW_MASSING_RESULT_V1")):
        if path:
            doc, ref = _read(path, project_id, key)
            if key != "solar" and doc.get("schema") != schema:
                raise ReportHold(f"SCHEMA_MISMATCH:{key}")
            if key == "solar" and not str(doc.get("schema", "")).startswith("ARCHIGROW_SOLAR"):
                raise ReportHold("SCHEMA_MISMATCH:solar")
            optional[key] = (doc, ref)
    e, parcel = site.get("eum") or {}, site.get("parcel") or {}
    pnu = site.get("pnu")
    if pnu is not None and not re.fullmatch(r"[0-9]{19}", str(pnu)):
        raise ReportHold("PNU_INVALID")
    if pnu and (e.get("pnu") not in (None, pnu) or parcel.get("pnu") not in (None, pnu)):
        raise ReportHold("PNU_MISMATCH")
    area = None
    source_state = "HOLD"
    svg = None
    payload = None
    options = _options(optional["massing"][0]) if "massing" in optional else []
    selected, selection = _select_option(options, option)
    if option not in (None, "") and not options:
        raise ReportHold("OPTION_REQUIRES_MASSING_RESULT")
    if baseline not in (None, "") and not options:
        raise ReportHold("BASELINE_REQUIRES_MASSING_RESULT")
    base_opt, base_kind = _select_option(options, baseline)
    if e and parcel:
        if not pnu or e.get("pnu") != pnu or parcel.get("pnu") != pnu:
            raise ReportHold("PNU_MISMATCH")
        if any(not re.fullmatch(r"[0-9a-fA-F]{64}", str(d.get("evidence_sha256") or "")) for d in (e, parcel)):
            raise ReportHold("SOURCE_EVIDENCE_HASH_MISSING")
        ring = _ring(parcel.get("polygon_local_m"))
        computed = _area(ring)
        official = e.get("area_m2")
        recorded = parcel.get("polygon_area_m2")
        if not _number(official) or official <= 0 or not _number(recorded) or abs(computed-recorded)>max(.01, computed*1e-6):
            raise ReportHold("AREA_EVIDENCE_INVALID")
        delta, tolerance = computed-official, max(1.0, official*.005)
        collector_ok = site.get("status") == "PASS" or (
            site.get("status") == "HOLD" and site.get("failure_class") == "DESIGN_PARAMETERS_MISSING")
        matched = (collector_ok and abs(delta) <= tolerance and
                   e.get("parcel_identity_status") == "VISIBLE_ADDRESS_MATCHES_PNU_BOUND_CADASTRAL")
        if site.get("comparison") and site["comparison"].get("result") != ("MATCH_WITHIN_SCREENING_TOLERANCE" if abs(delta)<=tolerance else "HOLD_AREA_MISMATCH"):
            raise ReportHold("AREA_COMPARISON_CONFLICT")
        source_state = "PASS" if matched else "HOLD"
        area = {"eum_area_m2": official, "polygon_area_m2": computed, "delta_m2": delta,
                "tolerance_m2": tolerance, "result": "MATCH_WITHIN_SCREENING_TOLERANCE" if matched else "HOLD_AREA_OR_IDENTITY"}
        crs = parcel.get("projected_crs")
        if crs not in ("EPSG:5186", "EPSG:5179"):
            raise ReportHold("PROJECTED_CRS_UNSUPPORTED")
        if "context" in optional:
            scene = optional["context"][0].get("scene") or {}
            if scene.get("projected_crs") and scene["projected_crs"] != crs:
                raise ReportHold("CONTEXT_CRS_MISMATCH")
            if scene.get("origin_m") and scene["origin_m"] != parcel.get("projected_origin_m"):
                raise ReportHold("CONTEXT_ORIGIN_MISMATCH")
        if "massing" in optional:
            design = optional["massing"][0]
            if design.get("site_area_basis") and design["site_area_basis"].get("pnu") != pnu:
                raise ReportHold("MASSING_PNU_MISMATCH")
            if design.get("site_polygon") and design["site_polygon"] != ring:
                raise ReportHold("MASSING_SITE_POLYGON_MISMATCH")
        if "solar" in optional:
            hashes = optional["solar"][0].get("input_hashes") or {}
            for key, label in (("context_obstacles", "context"), ("massing_result", "massing")):
                if label in optional and hashes.get(key) and hashes[key] != optional[label][1]["sha256"]:
                    raise ReportHold("SOLAR_INPUT_HASH_MISMATCH:" + label)
        mass = _schematic_massing(ring, optional["massing"][0], options) if options else []
        svg, map_meta = _map(ring, optional.get("context", (None,))[0], crs, mass=mass,
                             selected_id=selected["id"] if selected else None)
        map_meta["mass"] = mass
        hashes = {k: v[1]["sha256"] for k, v in optional.items()}
        hashes["site_source"] = site_ref["sha256"]
    if svg is None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800"><text x="70" y="400">Parcel geometry unavailable</text></svg>'
    sections = {"site_source": {"status": source_state, "source": site_ref,
                                "collector_status": site.get("status"), "failure_class": site.get("failure_class")}}
    for key in ("context", "solar", "massing"):
        doc, ref = optional.get(key, (None, None))
        sections[key] = {"status": "PRESENT" if doc else "NOT_PROVIDED", "source": ref}
    manifest = {"schema": "ARCHIGROW_SITE_ANALYSIS_MANIFEST_V1", "generator": VERSION,
                "project_id": project_id, "pnu": pnu, "source_status": source_state,
                "design_status": "PRESENT_UNVERIFIED" if massing else "NOT_REQUIRED_NOT_PROVIDED",
                "area": area, "sections": sections,
                "available_section_count": 3 + sum(key in optional for key in ("context", "solar", "massing")) if source_state == "PASS" else 2 + sum(key in optional for key in ("context", "solar", "massing")),
                "page_count": len(PAGES), "page_count_kind": "DESIGNED_SECTIONS_PRINT_PAGINATION_UNVERIFIED", "pages": list(PAGES),
                "capabilities": {"html": "AVAILABLE", "svg": "AVAILABLE", "pptx": "PENDING", "pdf": "NOT_GENERATED"},
                "claims": {"legal_parcel_certificate": False, "legal_feasibility": False, "source_independent_of_design_constraints": True}}
    ctx_doc, solar_doc, mass_doc = (optional.get(k, (None,))[0] for k in ("context", "solar", "massing"))
    if area is not None:
        evidence = evidence_impact(manifest, site, ctx_doc, solar_doc, mass_doc, hashes)
        payload = _studio_payload(manifest, site, ring, ctx_doc, solar_doc, options, selected, selection, crs, map_meta, hashes,
                                  base_opt, base_kind, evidence)
    manifest["selected_option"] = dict(selected, selection=selection) if selected else None
    manifest["comparison"] = {"baseline_option": dict(base_opt, selection=base_kind) if base_opt else None,
                              "meaning": DELTA_MEANING,
                              "rows": payload["delta_python"][base_opt["id"]] if payload and base_opt else None}
    manifest["evidence_impact"] = payload["evidence"] if payload else None
    manifest["recalc"] = payload["recalc_python"] if payload else None
    manifest["capabilities"]["interactive_studio"] = "AVAILABLE" if payload else "NOT_AVAILABLE_NO_GEOMETRY"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Preserve selected option and provenance in standalone/server SVG exports.
    # The browser replaces this static metadata when exporting a newly chosen option.
    svg_binding = {
        "schema": "ARCHIGROW_SITE_MAP_EXPORT_V1",
        "project_id": project_id,
        "pnu": pnu,
        "selected_option": manifest["selected_option"],
        "baseline_option": manifest["comparison"]["baseline_option"],
        "source_status": source_state,
        "input_sha256": {"site_source": site_ref["sha256"],
                         **{k: value[1]["sha256"] for k, value in optional.items()}},
        "legal_certification": False,
    }
    svg_meta = ('<metadata id="site-source-selection">' +
                html.escape(json.dumps(svg_binding, ensure_ascii=False, separators=(",", ":")), quote=False) +
                '</metadata>')
    svg = svg.replace(">", ">" + svg_meta, 1)
    static_svg = re.sub(r'<g class="mass" data-opt="[^"]*"[^>]*style="display:none">.*?</g><!--/mass-->', "", svg, flags=re.S)
    (out / "site_map.svg").write_text(static_svg, encoding="utf-8")
    (out / "site_analysis.html").write_text(_html(manifest, site, ctx_doc, solar_doc, mass_doc, svg, payload), encoding="utf-8")
    pptx_path = out / "site_analysis.pptx"
    try:
        _pptx(pptx_path, manifest, site, ctx_doc, solar_doc, mass_doc, selected, base_opt)
        manifest["capabilities"]["pptx"] = "AVAILABLE"
    except ModuleNotFoundError as exc:
        if exc.name != "pptx":
            manifest["capabilities"]["pptx"] = "FAILED:" + type(exc).__name__ + ":" + str(exc)
            manifest["report_status"] = "HOLD"
        else:
            manifest["capabilities"]["pptx"] = "UNAVAILABLE_PYTHON_PPTX_NOT_INSTALLED"
        pptx_path.unlink(missing_ok=True)
    except Exception as exc:
        manifest["capabilities"]["pptx"] = "FAILED:" + type(exc).__name__ + ":" + str(exc)
        manifest["report_status"] = "HOLD"
        pptx_path.unlink(missing_ok=True)
    (out / "analysis_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--site-source-receipt", required=True)
    ap.add_argument("--context")
    ap.add_argument("--solar")
    ap.add_argument("--massing")
    ap.add_argument("--option", help="massing option id, 1-based index or leading letter; default is the first option")
    ap.add_argument("--baseline", help="reference option for the delta comparison (same forms as --option); default is the first option")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    try:
        result = build(a.project_id, a.site_source_receipt, a.out_dir, a.context, a.solar, a.massing, a.option, a.baseline)
    except (ReportHold, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "HOLD", "failure_class": str(exc)}, ensure_ascii=False))
        return 2
    status = "HOLD" if result.get("report_status") == "HOLD" else result["source_status"]
    print(json.dumps({"status": status, "project_id": a.project_id,
                      "page_count": result["page_count"], "capabilities": result["capabilities"],
                      "out_dir": a.out_dir}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
