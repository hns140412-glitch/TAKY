#!/usr/bin/env python3
"""ARCHIGROW P9A: explicit circulation (corridor) + stair/lift shaft footprint overlay.

Reads a P8 ARCHIGROW_MASSING_RESULT_V1 model (read-only) and an explicit fixture,
validates the fixture geometry per strategy with exact polygon arithmetic, and
emits one shared model that drives a native ezdxf DXF (R2013, meters) and a local
SVG browser viewer.

Scope limits (enforced in claims/disclaimers):
  * vertical connectivity is SHAFT FOOTPRINT ALIGNMENT only - no stair, lift, landing,
    shaft section, door swing, egress or code-compliance statement is made;
  * circulation spaces are never inferred - unprogrammed area stays UNPROGRAMMED;
  * the overlay is separate from P7 walls; no room-to-corridor opening is modeled, so
    the network is UNCONNECTED_TO_PROGRAMMED_ROOMS.

Geometry: pure Python. Circulation regions are axis-aligned rectangles; room and floor
polygons may be any simple polygon (areas via Sutherland-Hodgman clip against the
rectangle, exact for this case). Native DWG conversion is NOT_DONE here.
"""
import argparse
import hashlib
import html
import json
import math
import sys
from pathlib import Path

MODULE_VERSION = "ARCHIGROW_CIRCULATION_VERTICAL/2026-10-28.1"
WORK_ID = "TAKY-ARCHI-GROW-001"
MODEL_SCHEMA = "TAKY_P9_CIRCULATION_VERTICAL_MODEL_V1"
FIXTURE_SCHEMA = "TAKY_P9_EXPLICIT_CIRCULATION_FIXTURE_V1"
RECEIPT_SCHEMA = "TAKY_P9_CIRCULATION_VERTICAL_RECEIPT_V1"
SOURCE_SCHEMA = "ARCHIGROW_MASSING_RESULT_V1"

SPACE_IDS = ("STAIR", "LIFT", "CORRIDOR")
SHAFT_IDS = ("STAIR", "LIFT")
OPENING_MODE = "EXPLICIT_FIXTURE_OPENING"
VERTICAL_MODE = "SHAFT_FOOTPRINT_ALIGNMENT"
PROVENANCE = "EXPLICIT_FIXTURE"
OPENING_WIDTH_M = 1.0
WALL_T_M = 0.15
MIN_AREA_M2 = 1.0
GEOM_TOL = 1e-6
OVERLAP_TOL_M2 = 1e-4
LEVEL_OFFSET_X_M = 50.0
APPID = "TAKY_P9"

DISCLAIMERS = (
    "SYNTHETIC PROOF-OF-CONCEPT GEOMETRY ONLY",
    "NO BUILDING_EGRESS, NO COMPLIANT_STAIR, NO COMPLIANT_LIFT, NO CODE COMPLIANCE",
    "VERTICAL LINK = SHAFT FOOTPRINT ALIGNMENT ONLY (no flight, landing, car or section)",
    "CORRIDOR HAS NO OPENING TO PROGRAMMED ROOMS: UNCONNECTED_TO_PROGRAMMED_ROOMS",
    "UNPROGRAMMED AREA IS NOT CORRIDOR; P7 WALLS ARE NOT UPDATED",
)
CLAIMS = {
    "actual_stair_function": False,
    "actual_lift_function": False,
    "room_access_established": False,
    "building_egress": False,
    "code_compliance": False,
    "programmed_rooms_connected": False,
    "residual_classified_as_corridor": False,
    "p7_walls_updated": False,
}
LAYERS = {
    "CIRC_STAIR": 5, "CIRC_LIFT": 3, "CIRC_CORRIDOR": 30, "CIRC_OPENING": 1,
    "CIRC_SHAFT_WALL": 7, "CIRC_VERTICAL_REF": 6, "CIRC_UNPROGRAMMED_REF": 8,
    "CIRC_ROOM_REF": 9, "CIRC_FLOOR_REF": 8, "CIRC_TEXT": 7,
}
SPACE_LAYER = {"STAIR": "CIRC_STAIR", "LIFT": "CIRC_LIFT", "CORRIDOR": "CIRC_CORRIDOR"}


class P9Error(Exception):
    """Fail-closed error: no outputs are produced."""


# ---------------------------------------------------------------- generic helpers
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def dumps(obj, indent=2):
    return json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=indent) + "\n"


def r6(v):
    return round(float(v) + 0.0, 6)


def require_keys(obj, required, where, optional=()):
    if not isinstance(obj, dict):
        raise P9Error(f"{where}: object expected")
    keys = set(obj)
    missing = set(required) - keys
    extra = keys - set(required) - set(optional)
    if missing or extra:
        raise P9Error(f"{where}: missing={sorted(missing)} unexpected={sorted(extra)}")


def to_point(p, where):
    if (not isinstance(p, (list, tuple)) or len(p) != 2
            or any(isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c) for c in p)):
        raise P9Error(f"{where}: bad coordinate {p!r}")
    return (float(p[0]), float(p[1]))


# ---------------------------------------------------------------- geometry
def poly_area(poly):
    s = 0.0
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def rect_from_polygon(poly, where):
    """Fixture polygon must be a 4-vertex axis-aligned rectangle with positive area."""
    pts = [to_point(p, where) for p in poly]
    if len(pts) != 4:
        raise P9Error(f"{where}: rectangle with exactly 4 vertices required")
    xs = sorted({round(p[0], 9) for p in pts})
    ys = sorted({round(p[1], 9) for p in pts})
    if len(xs) != 2 or len(ys) != 2:
        raise P9Error(f"{where}: polygon is not an axis-aligned rectangle")
    corners = {(x, y) for x in xs for y in ys}
    if {(round(p[0], 9), round(p[1], 9)) for p in pts} != corners:
        raise P9Error(f"{where}: vertices do not form a closed rectangle")
    # consecutive vertices must share an axis (rules out bow-tie order)
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        if abs(a[0] - b[0]) > 1e-9 and abs(a[1] - b[1]) > 1e-9:
            raise P9Error(f"{where}: vertex order is self-intersecting")
    return (xs[0], ys[0], xs[1], ys[1])


def rect_polygon(rect):
    x0, y0, x1, y1 = rect
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rect_area(rect):
    return (rect[2] - rect[0]) * (rect[3] - rect[1])


def clip_area(poly, rect):
    """Exact area of polygon ∩ axis-aligned rectangle (Sutherland-Hodgman, any simple subject)."""
    x0, y0, x1, y1 = rect
    out = [tuple(p) for p in poly]
    planes = (
        (lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
        (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
        (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
        (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1)),
    )
    for inside, cross in planes:
        src, out = out, []
        if not src:
            break
        prev = src[-1]
        for cur in src:
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
            prev = cur
    return poly_area(out) if len(out) >= 3 else 0.0


def rect_overlap_area(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def shared_boundary(a, b):
    """Collinear touching edge of two rectangles: (axis, const, lo, hi) or None."""
    for axis in ("x", "y"):
        i, j = (0, 1) if axis == "x" else (1, 0)
        for ca, cb in ((a[i + 2], b[i]), (a[i], b[i + 2])):
            if abs(ca - cb) <= GEOM_TOL:
                lo = max(a[j], b[j])
                hi = min(a[j + 2], b[j + 2])
                if hi - lo > GEOM_TOL:
                    return (axis, ca, lo, hi)
    return None


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def polygon_distance(pa, pb):
    """Min boundary-to-boundary distance (valid for non-overlapping simple polygons)."""
    best = float("inf")
    for A, B in ((pa, pb), (pb, pa)):
        for p in A:
            for i in range(len(B)):
                best = min(best, _seg_dist(p, B[i], B[(i + 1) % len(B)]))
    return best


# ---------------------------------------------------------------- inputs
def load_source(path, expect_project):
    raw = Path(path).read_bytes()
    try:
        model = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise P9Error(f"source model unreadable: {exc}")
    if not isinstance(model, dict) or model.get("schema") != SOURCE_SCHEMA:
        raise P9Error(f"source schema must be {SOURCE_SCHEMA}")
    if model.get("coordinate_units") != "m":
        raise P9Error("source coordinate_units must be m")
    if model.get("project_id") != expect_project:
        raise P9Error(f"project mismatch: {model.get('project_id')!r} != {expect_project!r}")
    src_sha = model.get("source_sha256")
    if not isinstance(src_sha, str) or len(src_sha) != 64:
        raise P9Error("source model has no source_sha256")
    return model, sha256_bytes(raw), src_sha


def source_levels(option):
    """level -> {floor polygon, rooms, residual} from a P8 option (read-only view)."""
    floors = {f["level"]: [tuple(p) for p in f["polygon"]] for f in option["floors"]}
    out = {}
    rg = option["program_allocation"]["room_geometry"]
    for lv in rg["levels"]:
        name = lv["level"]
        if name not in floors:
            raise P9Error(f"room_geometry level {name} has no floor polygon")
        out[name] = {
            "floor": floors[name],
            "rooms": [{"id": r["id"], "polygon": [tuple(p) for p in r["polygon"]], "area_m2": r["area_m2"]}
                      for r in lv["rooms"]],
            "residual": [tuple(p) for p in lv["residual"]["polygon"]],
            "residual_kind": lv["residual"]["kind"],
        }
    order = [lv["level"] for lv in rg["levels"]]
    return out, order


def sample_fixture(model_sha, source_sha, project_id, strategies):
    def level_block():
        return {
            "spaces": {
                "STAIR": {"function": "STAIR", "polygon": [[20, 10], [23, 10], [23, 14], [20, 14]]},
                "LIFT": {"function": "LIFT", "polygon": [[20.5, 16], [23, 16], [23, 19], [20.5, 19]]},
                "CORRIDOR": {"function": "CORRIDOR", "polygon": [[23, 10], [24.5, 10], [24.5, 19], [23, 19]]},
            },
            "openings": [
                {"id": "STAIR_CORRIDOR_OPENING", "a": "STAIR", "b": "CORRIDOR", "segment": [[23, 11.5], [23, 12.5]],
                 "center": [23, 12], "width_m": 1.0, "mode": OPENING_MODE, "provenance": PROVENANCE},
                {"id": "LIFT_CORRIDOR_OPENING", "a": "LIFT", "b": "CORRIDOR", "segment": [[23, 17], [23, 18]],
                 "center": [23, 17.5], "width_m": 1.0, "mode": OPENING_MODE, "provenance": PROVENANCE},
            ],
        }
    return {
        "schema": FIXTURE_SCHEMA, "project_id": project_id,
        "source_sha256": source_sha, "model_sha256": model_sha,
        "provenance": {"mode": PROVENANCE, "note": "synthetic hand-authored candidate; not derived from the model"},
        "options": [{
            "strategy": s, "levels": {"L01": level_block(), "L02": level_block()},
            "vertical_links": [
                {"id": f"{k}_L01_L02", "kind": k, "function": k, "from_level": "L01", "to_level": "L02",
                 "space": k, "mode": VERTICAL_MODE, "provenance": PROVENANCE} for k in SHAFT_IDS],
        } for s in strategies],
    }


def parse_fixture(fx, model_sha, source_sha, project_id, model):
    """Structural + provenance validation. Any failure is a hard P9Error."""
    require_keys(fx, ("schema", "project_id", "source_sha256", "model_sha256", "provenance", "options"), "fixture")
    if fx["schema"] != FIXTURE_SCHEMA:
        raise P9Error("fixture schema mismatch")
    if fx["project_id"] != project_id:
        raise P9Error("fixture project_id mismatch")
    if fx["source_sha256"] != source_sha:
        raise P9Error("fixture source_sha256 does not match source model")
    if fx["model_sha256"] != model_sha:
        raise P9Error("fixture model_sha256 does not match source model file")
    require_keys(fx["provenance"], ("mode", "note"), "fixture.provenance")
    if fx["provenance"]["mode"] != PROVENANCE:
        raise P9Error("fixture provenance mode must be " + PROVENANCE)
    if not isinstance(fx["options"], list) or not fx["options"]:
        raise P9Error("fixture.options must be a non-empty list")
    known = {o["strategy"]: o for o in model["options"]}
    seen = set()
    parsed = []
    for opt in fx["options"]:
        require_keys(opt, ("strategy", "levels", "vertical_links"), "fixture option")
        strat = opt["strategy"]
        if strat in seen:
            raise P9Error(f"duplicate fixture strategy {strat}")
        seen.add(strat)
        if strat not in known:
            raise P9Error(f"fixture strategy {strat} not in source model")
        _, order = source_levels(known[strat])
        if not isinstance(opt["levels"], dict) or not opt["levels"]:
            raise P9Error(f"{strat}: levels must be a non-empty object")
        levels = {}
        for lname, lv in opt["levels"].items():
            if lname not in order:
                raise P9Error(f"{strat}: level {lname} is not a room_geometry level")
            levels[lname] = _parse_level(strat, lname, lv)
        links = _parse_links(strat, opt["vertical_links"], levels, order)
        parsed.append({"strategy": strat, "levels": levels, "links": links})
    return parsed


def _parse_level(strat, lname, lv):
    where = f"{strat}/{lname}"
    require_keys(lv, ("spaces", "openings"), where)
    require_keys(lv["spaces"], SPACE_IDS, where + ".spaces")
    spaces = {}
    for sid in SPACE_IDS:
        sp = lv["spaces"][sid]
        require_keys(sp, ("function", "polygon"), f"{where}.{sid}")
        if sp["function"] != sid:
            raise P9Error(f"{where}.{sid}: function must be {sid}")
        spaces[sid] = {"rect": rect_from_polygon(sp["polygon"], f"{where}.{sid}")}
    if not isinstance(lv["openings"], list):
        raise P9Error(f"{where}.openings must be a list")
    openings, ids, pairs = [], set(), set()
    for op in lv["openings"]:
        require_keys(op, ("id", "a", "b", "segment", "center", "width_m", "mode", "provenance"), f"{where}.opening")
        if op["id"] in ids:
            raise P9Error(f"{where}: duplicate opening id {op['id']}")
        ids.add(op["id"])
        if op["a"] not in SPACE_IDS or op["b"] not in SPACE_IDS or op["a"] == op["b"]:
            raise P9Error(f"{where}.{op['id']}: endpoints must be two different circulation spaces")
        pair = frozenset((op["a"], op["b"]))
        if pair in pairs:
            raise P9Error(f"{where}: duplicate opening for pair {sorted(pair)}")
        pairs.add(pair)
        if op["mode"] != OPENING_MODE or op["provenance"] != PROVENANCE:
            raise P9Error(f"{where}.{op['id']}: mode/provenance must be {OPENING_MODE}/{PROVENANCE}")
        if (isinstance(op["width_m"], bool) or not isinstance(op["width_m"], (int, float))
                or abs(op["width_m"] - OPENING_WIDTH_M) > GEOM_TOL):
            raise P9Error(f"{where}.{op['id']}: width_m must be exactly {OPENING_WIDTH_M}")
        seg = op["segment"]
        if not isinstance(seg, list) or len(seg) != 2:
            raise P9Error(f"{where}.{op['id']}: segment needs two points")
        p, q = to_point(seg[0], op["id"]), to_point(seg[1], op["id"])
        c = to_point(op["center"], op["id"])
        vertical = abs(p[0] - q[0]) <= GEOM_TOL
        horizontal = abs(p[1] - q[1]) <= GEOM_TOL
        if vertical == horizontal:
            raise P9Error(f"{where}.{op['id']}: segment must be axis-aligned and non-degenerate")
        if abs(math.hypot(p[0] - q[0], p[1] - q[1]) - OPENING_WIDTH_M) > GEOM_TOL:
            raise P9Error(f"{where}.{op['id']}: segment length must equal width_m")
        if abs(c[0] - (p[0] + q[0]) / 2) > GEOM_TOL or abs(c[1] - (p[1] + q[1]) / 2) > GEOM_TOL:
            raise P9Error(f"{where}.{op['id']}: center is not the segment midpoint")
        openings.append({"id": op["id"], "a": op["a"], "b": op["b"], "p": p, "q": q, "center": c,
                         "axis": "x" if vertical else "y"})
    return {"spaces": spaces, "openings": openings}


def _parse_links(strat, links, levels, order):
    if not isinstance(links, list):
        raise P9Error(f"{strat}: vertical_links must be a list")
    out, ids, edges = [], set(), set()
    for ln in links:
        require_keys(ln, ("id", "kind", "function", "from_level", "to_level", "space", "mode", "provenance"),
                     f"{strat}.vertical_link")
        if ln["id"] in ids:
            raise P9Error(f"{strat}: duplicate vertical link id {ln['id']}")
        ids.add(ln["id"])
        if ln["kind"] not in SHAFT_IDS or ln["function"] != ln["kind"] or ln["space"] != ln["kind"]:
            raise P9Error(f"{strat}.{ln['id']}: kind/function/space must be one identical STAIR or LIFT")
        if ln["mode"] != VERTICAL_MODE or ln["provenance"] != PROVENANCE:
            raise P9Error(f"{strat}.{ln['id']}: mode/provenance must be {VERTICAL_MODE}/{PROVENANCE}")
        lo, hi = ln["from_level"], ln["to_level"]
        if lo not in levels or hi not in levels:
            raise P9Error(f"{strat}.{ln['id']}: endpoint level not in fixture")
        if order.index(hi) != order.index(lo) + 1:
            raise P9Error(f"{strat}.{ln['id']}: levels must be adjacent and ascending")
        key = (ln["kind"], lo, hi)
        if key in edges:
            raise P9Error(f"{strat}: duplicate vertical edge {key}")
        edges.add(key)
        ra, rb = levels[lo]["spaces"][ln["kind"]]["rect"], levels[hi]["spaces"][ln["kind"]]["rect"]
        if any(abs(a - b) > GEOM_TOL for a, b in zip(ra, rb)):
            raise P9Error(f"{strat}.{ln['id']}: forged vertical edge - plan polygons differ between {lo} and {hi}")
        out.append({"id": ln["id"], "kind": ln["kind"], "function": ln["function"], "from_level": lo,
                    "to_level": hi, "space": ln["space"], "mode": VERTICAL_MODE, "provenance": PROVENANCE})
    return sorted(out, key=lambda x: x["id"])


# ---------------------------------------------------------------- strategy evaluation
def _check(checks, level, subject, check, measured, limit, ok, **extra):
    row = {"level": level, "subject": subject, "check": check, "measured": r6(measured),
           "limit": limit, "result": "PASS" if ok else "FAIL"}
    row.update(extra)
    checks.append(row)


def _wall_pieces(rect, gaps):
    """Inward 0.15 m wall strips of a shaft with real gaps cut for explicit openings."""
    x0, y0, x1, y1 = rect
    t = WALL_T_M
    strips = [("W", (x0, y0, x0 + t, y1)), ("E", (x1 - t, y0, x1, y1)),
              ("S", (x0 + t, y0, x1 - t, y0 + t)), ("N", (x0 + t, y1 - t, x1 - t, y1))]
    pieces = []
    for side, (a0, b0, a1, b1) in strips:
        vertical = side in ("W", "E")
        const = x0 if side == "W" else x1 if side == "E" else y0 if side == "S" else y1
        cuts = sorted((lo, hi) for ax, c, lo, hi in gaps
                      if ax == ("x" if vertical else "y") and abs(c - const) <= GEOM_TOL)
        lo_all, hi_all = (b0, b1) if vertical else (a0, a1)
        cur = lo_all
        spans = []
        for lo, hi in cuts:
            if lo > cur + GEOM_TOL:
                spans.append((cur, lo))
            cur = max(cur, hi)
        if hi_all > cur + GEOM_TOL:
            spans.append((cur, hi_all))
        for s0, s1 in spans:
            pieces.append(list(rect_polygon((a0, s0, a1, s1) if vertical else (s0, b0, s1, b1))))
    return pieces


def evaluate_strategy(strat, parsed, src_levels):
    checks, rejections, levels_out = [], [], []
    for lname, lv in sorted(parsed["levels"].items()):
        src = src_levels[lname]
        rects = {sid: lv["spaces"][sid]["rect"] for sid in SPACE_IDS}
        for sid, rect in rects.items():
            area = rect_area(rect)
            _check(checks, lname, sid, "MIN_AREA_NONZERO", area, f">={MIN_AREA_M2}", area >= MIN_AREA_M2)
            inside = clip_area(src["floor"], rect)
            outside = area - inside
            _check(checks, lname, sid, "CONTAINED_IN_FLOOR_OUTSIDE_AREA_M2", max(outside, 0.0),
                   f"<={OVERLAP_TOL_M2}", outside <= OVERLAP_TOL_M2)
            for room in src["rooms"]:
                ov = clip_area(room["polygon"], rect)
                _check(checks, lname, sid, "NO_ROOM_OVERLAP_AREA_M2", ov, f"<={OVERLAP_TOL_M2}",
                       ov <= OVERLAP_TOL_M2, room=room["id"])
        ids = list(SPACE_IDS)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                ov = rect_overlap_area(rects[a], rects[b])
                _check(checks, lname, f"{a}|{b}", "PAIRWISE_NO_OVERLAP_AREA_M2", ov, f"<={OVERLAP_TOL_M2}",
                       ov <= OVERLAP_TOL_M2)
        openings, gaps, opened_pairs = [], [], set()
        for op in lv["openings"]:
            sb = shared_boundary(rects[op["a"]], rects[op["b"]])
            ok = False
            margin = 0.0
            if sb and sb[0] == op["axis"]:
                axis, const, lo, hi = sb
                idx = 0 if axis == "x" else 1
                other = 1 - idx
                s_lo, s_hi = sorted((op["p"][other], op["q"][other]))
                on_wall = abs(op["p"][idx] - const) <= GEOM_TOL and abs(op["q"][idx] - const) <= GEOM_TOL
                margin = min(s_lo - lo, hi - s_hi)
                ok = on_wall and margin >= WALL_T_M - GEOM_TOL
            _check(checks, lname, op["id"], "OPENING_ON_SHARED_WALL_WITH_WALL_STUBS_M", margin,
                   f">={WALL_T_M}", ok)
            opened_pairs.add(frozenset((op["a"], op["b"])))
            if ok:
                axis, const, lo, hi = sb
                s_lo, s_hi = sorted((op["p"][1 - (0 if axis == "x" else 1)], op["q"][1 - (0 if axis == "x" else 1)]))
                gaps.append((axis, const, s_lo, s_hi))
                half = WALL_T_M / 2
                gap_rect = ((const - half, s_lo, const + half, s_hi) if axis == "x"
                            else (s_lo, const - half, s_hi, const + half))
                openings.append({
                    "id": op["id"], "a": op["a"], "b": op["b"], "mode": OPENING_MODE, "provenance": PROVENANCE,
                    "segment": [list(map(r6, op["p"])), list(map(r6, op["q"]))],
                    "center": list(map(r6, op["center"])), "width_m": OPENING_WIDTH_M,
                    "shared_boundary_m": r6(hi - lo),
                    "gap_polygon": [list(map(r6, p)) for p in rect_polygon(gap_rect)],
                })
        touching = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                sb = shared_boundary(rects[a], rects[b])
                if sb and frozenset((a, b)) not in opened_pairs:
                    touching.append({"a": a, "b": b, "shared_boundary_m": r6(sb[3] - sb[2]),
                                     "note": "TOUCHING_WALL_NO_OPENING_INFERRED"})
        clearance = []
        for sid in SPACE_IDS:
            best = min(((polygon_distance(rect_polygon(rects[sid]), room["polygon"]), room["id"])
                        for room in src["rooms"]), default=(None, None))
            clearance.append({"space": sid, "nearest_room": best[1],
                              "clearance_m": None if best[0] is None else r6(best[0])})
        spaces = []
        for sid in SPACE_IDS:
            rect = rects[sid]
            spaces.append({
                "id": sid, "function": sid, "area_m2": r6(rect_area(rect)),
                "polygon": [list(map(r6, p)) for p in rect_polygon(rect)],
                "walls": [], "provenance": PROVENANCE,
            })
        dist = []
        for i, o1 in enumerate(openings):
            for o2 in openings[i + 1:]:
                if {o1["a"], o1["b"]} & {o2["a"], o2["b"]}:
                    dist.append({"from": o1["id"], "to": o2["id"], "straight_line_m": r6(math.hypot(
                        o1["center"][0] - o2["center"][0], o1["center"][1] - o2["center"][1])),
                        "note": "STRAIGHT_LINE_BETWEEN_OPENING_CENTERS_NOT_TRAVEL_PATH"})
        levels_out.append({
            "level": lname, "gaps": gaps,
            "floor_polygon": [list(map(r6, p)) for p in src["floor"]],
            "rooms": [{"id": r["id"], "area_m2": r["area_m2"], "polygon": [list(map(r6, p)) for p in r["polygon"]]}
                      for r in src["rooms"]],
            "unprogrammed_ref": {"kind": src["residual_kind"], "classified_as_corridor": False,
                                 "polygon": [list(map(r6, p)) for p in src["residual"]]},
            "spaces": spaces, "openings": openings, "touching_without_opening": touching,
            "clearance_to_programmed_rooms": clearance, "opening_distances": dist,
            "programmed_room_openings": 0,
            "exterior_note": "NO EXTERIOR OPENING MODELED; NO ROOM OPENING MODELED",
        })
    failed = [c for c in checks if c["result"] != "PASS"]
    status = "PASS" if not failed else "HOLD"
    rejections = [dict(c) for c in failed]
    if status == "PASS":
        for lv in levels_out:
            rects = {s["id"]: rect_from_polygon(s["polygon"], "model") for s in lv["spaces"]}
            for s in lv["spaces"]:
                if s["id"] in SHAFT_IDS:
                    s["walls"] = [[list(map(r6, p)) for p in w] for w in _wall_pieces(rects[s["id"]], lv["gaps"])]
    for lv in levels_out:
        del lv["gaps"]
    graph = None
    if status == "PASS":
        graph = build_graph(levels_out, parsed["links"])
    return {
        "strategy": strat, "status": status, "cad_published": status == "PASS",
        "levels": levels_out, "vertical_links": parsed["links"] if status == "PASS" else [],
        "graph": graph, "checks": checks, "rejections": rejections,
        "p10_constraints": p10_constraints(strat, rejections) if status == "HOLD" else [],
    }


def build_graph(levels, links):
    nodes = [f"{lv['level']}:{s['id']}" for lv in levels for s in lv["spaces"]]
    edges = []
    for lv in levels:
        for op in lv["openings"]:
            edges.append({"id": f"{lv['level']}:{op['id']}", "type": "SAME_FLOOR_OPENING", "mode": op["mode"],
                          "a": f"{lv['level']}:{op['a']}", "b": f"{lv['level']}:{op['b']}",
                          "provenance": op["provenance"]})
    for ln in links:
        edges.append({"id": ln["id"], "type": "VERTICAL_SHAFT_FOOTPRINT_ALIGNMENT", "mode": ln["mode"],
                      "a": f"{ln['from_level']}:{ln['space']}", "b": f"{ln['to_level']}:{ln['space']}",
                      "provenance": ln["provenance"]})
    parent = {n: n for n in nodes}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n
    for e in edges:
        parent[find(e["a"])] = find(e["b"])
    comps = {}
    for n in nodes:
        comps.setdefault(find(n), []).append(n)
    return {"nodes": nodes, "edges": sorted(edges, key=lambda e: e["id"]),
            "components": sorted(sorted(c) for c in comps.values()),
            "network_status": "UNCONNECTED_TO_PROGRAMMED_ROOMS",
            "vertical_meaning": "SHAFT_FOOTPRINT_ALIGNMENT_ONLY"}


def p10_constraints(strat, rejections):
    out = [f"{strat}: explicit candidate fixture rejected by measured geometry; do not fabricate access"]
    for r in rejections:
        if r["check"].startswith("NO_ROOM_OVERLAP") or r["check"].startswith("CONTAINED"):
            out.append(f"{r['level']} {r['subject']} {r['check']} measured {r['measured']} m2"
                       + (f" with {r['room']}" if "room" in r else ""))
    return out


# ---------------------------------------------------------------- build model
def build_model(model, model_sha, source_sha, fixture, fixture_sha):
    parsed = parse_fixture(fixture, model_sha, source_sha, model["project_id"], model)
    known = {o["strategy"]: o for o in model["options"]}
    strategies = []
    for p in parsed:
        src_levels, _ = source_levels(known[p["strategy"]])
        for lname in p["levels"]:
            if lname not in src_levels:
                raise P9Error(f"{p['strategy']}: level {lname} missing in room geometry")
        strategies.append(evaluate_strategy(p["strategy"], p, src_levels))
    strategies.sort(key=lambda s: s["strategy"])
    holds = [s["strategy"] for s in strategies if s["status"] == "HOLD"]
    if not holds:
        status = "PASS_SYNTHETIC_FIXTURE_ONLY"
    elif len(holds) == len(strategies):
        status = "HOLD_ALL_STRATEGIES"
    else:
        status = "PARTIAL_PASS_WITH_" + "_".join(holds) + "_HOLD"
    return {
        "schema": MODEL_SCHEMA, "module_version": MODULE_VERSION, "work_id": WORK_ID,
        "project_id": model["project_id"], "units": "m",
        "source_sha256": source_sha, "source_model_sha256": model_sha, "fixture_sha256": fixture_sha,
        "status": status, "disclaimers": list(DISCLAIMERS), "claims": dict(CLAIMS),
        "constants": {"opening_width_m": OPENING_WIDTH_M, "wall_thickness_m": WALL_T_M,
                      "min_area_m2": MIN_AREA_M2, "overlap_tol_m2": OVERLAP_TOL_M2,
                      "level_offset_x_m": LEVEL_OFFSET_X_M},
        "strategies": strategies,
    }


# ---------------------------------------------------------------- DXF
def _off(level_index):
    return level_index * LEVEL_OFFSET_X_M


def _shift(poly, dx):
    return [(r6(p[0] + dx), r6(p[1])) for p in poly]


def write_dxf(strategy, path, model_const):
    import ezdxf
    doc = ezdxf.new("R2013", setup=True)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6
    doc.appids.add(APPID)
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    doc.layers.get("CIRC_VERTICAL_REF").dxf.linetype = "DASHED"
    doc.layers.get("CIRC_UNPROGRAMMED_REF").dxf.linetype = "DASHED"
    msp = doc.modelspace()

    def poly(pts, layer, tag=None):
        e = msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        if tag:
            e.set_xdata(APPID, [(1000, tag)])
        return e

    def text(s, x, y, h=0.6):
        msp.add_text(s, dxfattribs={"layer": "CIRC_TEXT", "height": h, "insert": (x, y)})
    centers = {}
    for i, lv in enumerate(strategy["levels"]):
        dx = _off(i)
        poly(_shift(lv["floor_polygon"], dx), "CIRC_FLOOR_REF", f"FLOOR|{lv['level']}")
        for room in lv["rooms"]:
            poly(_shift(room["polygon"], dx), "CIRC_ROOM_REF", f"ROOM|{lv['level']}|{room['id']}")
        poly(_shift(lv["unprogrammed_ref"]["polygon"], dx), "CIRC_UNPROGRAMMED_REF", f"UNPROGRAMMED|{lv['level']}")
        for sp in lv["spaces"]:
            poly(_shift(sp["polygon"], dx), SPACE_LAYER[sp["id"]], f"SPACE|{lv['level']}|{sp['id']}")
            for w in sp["walls"]:
                poly(_shift(w, dx), "CIRC_SHAFT_WALL", f"WALL|{lv['level']}|{sp['id']}")
            xs = [p[0] for p in sp["polygon"]]
            ys = [p[1] for p in sp["polygon"]]
            centers[(lv["level"], sp["id"])] = ((min(xs) + max(xs)) / 2 + dx, (min(ys) + max(ys)) / 2)
            text(f"{sp['id']} {sp['area_m2']:.2f} m2 FOOTPRINT ONLY", min(xs) + dx, max(ys) + 0.4, 0.4)
        for op in lv["openings"]:
            poly(_shift(op["gap_polygon"], dx), "CIRC_OPENING",
                 f"OPENING|{lv['level']}|{op['id']}|width_m={op['width_m']:.3f}")
            a, b = op["segment"]
            ln = msp.add_line((a[0] + dx, a[1]), (b[0] + dx, b[1]), dxfattribs={"layer": "CIRC_OPENING"})
            ln.set_xdata(APPID, [(1000, f"OPENING_CHORD|{lv['level']}|{op['id']}|width_m={op['width_m']:.3f}")])
        text(f"{lv['level']}  CIRCULATION UNCONNECTED_TO_PROGRAMMED_ROOMS", 3 + dx, 1.0, 0.7)
        text("UNPROGRAMMED (NOT CORRIDOR) - REFERENCE ONLY", 30 + dx, 29.0, 0.5)
    for ln in strategy["vertical_links"]:
        a = centers[(ln["from_level"], ln["space"])]
        b = centers[(ln["to_level"], ln["space"])]
        e = msp.add_line(a, b, dxfattribs={"layer": "CIRC_VERTICAL_REF"})
        e.set_xdata(APPID, [(1000, f"VERTICAL|{ln['id']}|{ln['mode']}")])
        text(f"{ln['kind']} SHAFT FOOTPRINT ALIGNMENT (NOT FUNCTION)", (a[0] + b[0]) / 2 - 12, a[1] - 1.5, 0.4)
    text("SYNTHETIC P9A OVERLAY - NO BUILDING_EGRESS / COMPLIANT_STAIR / COMPLIANT_LIFT; P7 WALLS NOT UPDATED",
         3, -2.0, 0.6)
    doc.saveas(str(path))


def readback_dxf(path, strategy):
    """Re-open the DXF and compare closed outlines/opening objects against the model."""
    import ezdxf
    doc = ezdxf.readfile(str(path))
    problems = []
    if doc.dxfversion != "AC1027":
        problems.append(f"dxfversion {doc.dxfversion} != AC1027")
    if doc.header.get("$INSUNITS") != 6:
        problems.append("INSUNITS != 6 (meters)")
    for name in LAYERS:
        if name not in doc.layers:
            problems.append(f"missing layer {name}")

    def key(pts):
        return tuple((r6(x), r6(y)) for x, y in pts)
    got = {}
    chords = 0
    for e in doc.modelspace():
        layer = e.dxf.layer
        if e.dxftype() == "LWPOLYLINE":
            if not e.closed:
                problems.append(f"open polyline on {layer}")
            got.setdefault(layer, []).append(key(e.get_points("xy")))
        elif e.dxftype() == "LINE" and layer == "CIRC_OPENING":
            chords += 1
    want = {}

    def add(layer, pts):
        want.setdefault(layer, []).append(key(pts))
    for i, lv in enumerate(strategy["levels"]):
        dx = _off(i)
        add("CIRC_FLOOR_REF", _shift(lv["floor_polygon"], dx))
        add("CIRC_UNPROGRAMMED_REF", _shift(lv["unprogrammed_ref"]["polygon"], dx))
        for room in lv["rooms"]:
            add("CIRC_ROOM_REF", _shift(room["polygon"], dx))
        for sp in lv["spaces"]:
            add(SPACE_LAYER[sp["id"]], _shift(sp["polygon"], dx))
            for w in sp["walls"]:
                add("CIRC_SHAFT_WALL", _shift(w, dx))
        for op in lv["openings"]:
            add("CIRC_OPENING", _shift(op["gap_polygon"], dx))
    for layer in sorted(set(want) | set(got)):
        if sorted(want.get(layer, [])) != sorted(got.get(layer, [])):
            problems.append(f"layer {layer} outlines differ from model")
    n_open = sum(len(lv["openings"]) for lv in strategy["levels"])
    if chords != n_open:
        problems.append(f"opening chords {chords} != {n_open}")
    digest = sha256_bytes(json.dumps({k: sorted(v) for k, v in sorted(got.items())}, sort_keys=True).encode("ascii"))
    return {"ok": not problems, "problems": problems, "dxfversion": doc.dxfversion,
            "geometry_digest_sha256": digest,
            "closed_outline_counts": {k: len(v) for k, v in sorted(got.items())},
            "opening_objects": len(got.get("CIRC_OPENING", [])), "opening_chords": chords}


# ---------------------------------------------------------------- HTML
VIEWER_JS = r"""
(function(){
var M=JSON.parse(document.getElementById('p9-model').textContent);
var NS='http://www.w3.org/2000/svg';
var st={s:0,l:0};
function el(t,a,p,tx){var e=document.createElementNS(NS,t);for(var k in a){e.setAttribute(k,a[k]);}if(tx!==undefined){e.textContent=tx;}if(p){p.appendChild(e);}return e;}
function H(t,a,p,tx){var e=document.createElement(t);for(var k in a){e.setAttribute(k,a[k]);}if(tx!==undefined){e.textContent=tx;}if(p){p.appendChild(e);}return e;}
var X0=0,Y0=0,SC=1,HH=0,PAD=2;
function bbox(S){var a=[1e9,1e9,-1e9,-1e9];S.levels.forEach(function(L){L.floor_polygon.forEach(function(p){a[0]=Math.min(a[0],p[0]);a[1]=Math.min(a[1],p[1]);a[2]=Math.max(a[2],p[0]);a[3]=Math.max(a[3],p[1]);});});return a;}
function P(p){return ((p[0]-X0+PAD)*SC).toFixed(2)+','+((HH-(p[1]-Y0+PAD)*SC)).toFixed(2);}
function path(poly){return 'M'+poly.map(P).join(' L')+' Z';}
function cen(poly){var x=0,y=0;poly.forEach(function(p){x+=p[0];y+=p[1];});return [x/poly.length,y/poly.length];}
function txt(p,s,cls,parent){var q=P(p).split(',');return el('text',{x:q[0],y:q[1],'class':cls},parent,s);}
function draw(){
 var S=M.strategies[st.s],L=S.levels[st.l],svg=document.getElementById('plan');
 while(svg.firstChild){svg.removeChild(svg.firstChild);}
 var b=bbox(S);X0=b[0];Y0=b[1];SC=14;HH=(b[3]-b[1]+2*PAD)*SC;
 svg.setAttribute('viewBox','0 0 '+((b[2]-b[0]+2*PAD)*SC)+' '+HH);
 el('path',{d:path(L.floor_polygon),'class':'floor'},svg);
 el('path',{d:path(L.unprogrammed_ref.polygon),'class':'unprog'},svg);
 var u=cen(L.unprogrammed_ref.polygon);txt([u[0]+3,u[1]+5],'UNPROGRAMMED - NOT CORRIDOR','lab',svg);
 L.rooms.forEach(function(r){el('path',{d:path(r.polygon),'class':'room'},svg);txt(cen(r.polygon),r.id+' '+r.area_m2.toFixed(1)+' m2','lab',svg);});
 var hold=S.status!=='PASS';
 L.spaces.forEach(function(s){
  el('path',{d:path(s.polygon),'class':hold?'rej':('sp '+s.id)},svg);
  var c=cen(s.polygon);txt([c[0]-1.2,c[1]],s.id+(hold?' REJECTED':' FOOTPRINT'),'lab',svg);
  s.walls.forEach(function(w){el('path',{d:path(w),'class':'wall'},svg);});
 });
 if(!hold){L.openings.forEach(function(o){
  el('path',{d:path(o.gap_polygon),'class':'gap'},svg);
  txt([o.center[0]+0.4,o.center[1]],'OPENING '+o.width_m.toFixed(2)+' m','lab',svg);
 });}
 var dl=document.getElementById('detail');while(dl.firstChild){dl.removeChild(dl.firstChild);}
 H('h3',{},dl,S.strategy+' / '+L.level+' : '+S.status);
 if(hold){
  H('p',{'class':'hold'},dl,'HOLD: explicit candidate rejected by measured geometry. No CAD is published for this strategy and no access is claimed.');
  var ul=H('ul',{},dl);
  S.rejections.filter(function(r){return r.level===L.level;}).forEach(function(r){H('li',{},ul,r.subject+' '+r.check+' = '+r.measured+' m2'+(r.room?' (room '+r.room+')':''));});
  S.p10_constraints.forEach(function(c){H('li',{'class':'p10'},ul,'P10 constraint: '+c);});
 } else {
  H('p',{},dl,'Network: '+S.graph.network_status+'; vertical = '+S.graph.vertical_meaning+'; components='+S.graph.components.length+'; edges='+S.graph.edges.length);
  var t=H('table',{},dl);var hr=H('tr',{},t);['Item','Value'].forEach(function(h){H('th',{},hr,h);});
  function row(a,v){var r=H('tr',{},t);H('td',{},r,a);H('td',{},r,v);}
  L.opening_distances.forEach(function(d){row(d.from+' to '+d.to,d.straight_line_m.toFixed(3)+' m (straight line, not travel path)');});
  L.clearance_to_programmed_rooms.forEach(function(c){row('clearance '+c.space+' to '+c.nearest_room,c.clearance_m.toFixed(3)+' m');});
  L.openings.forEach(function(o){row(o.id,'width '+o.width_m.toFixed(2)+' m on '+o.shared_boundary_m.toFixed(2)+' m shared wall');});
  row('programmed room openings',String(L.programmed_room_openings));
  row('exterior',L.exterior_note);
  S.vertical_links.forEach(function(v){row(v.id,v.from_level+' to '+v.to_level+' '+v.mode);});
 }
}
function buttons(){
 var sb=document.getElementById('strat');M.strategies.forEach(function(S,i){var b=H('button',{type:'button','data-s':i},sb,S.strategy+' : '+S.status);b.onclick=function(){st.s=i;st.l=0;buttons2();draw();};});
 buttons2();
}
function buttons2(){
 var lb=document.getElementById('lvl');while(lb.firstChild){lb.removeChild(lb.firstChild);}
 M.strategies[st.s].levels.forEach(function(L,i){var b=H('button',{type:'button','data-l':i,'aria-pressed':i===st.l?'true':'false'},lb,L.level);b.onclick=function(){st.l=i;buttons2();draw();};});
}
H('p',{},document.getElementById('status'),'Receipt status: '+M.status+' (no total pass claimed)');
buttons();draw();
})();
"""

VIEWER_CSS = """
body{font:14px/1.45 Arial,Helvetica,sans-serif;margin:16px;color:#1b1f23;background:#fafafa}
.banner{background:#7a1f1f;color:#fff;padding:8px 12px;margin-bottom:10px}
.banner div{margin:2px 0}
button{margin:0 6px 6px 0;padding:6px 12px;border:1px solid #444;background:#fff;cursor:pointer}
button[aria-pressed=true]{background:#1b4f8a;color:#fff}
svg{width:100%;max-width:1000px;border:1px solid #bbb;background:#fff}
.floor{fill:none;stroke:#555;stroke-width:1.2}.unprog{fill:#f1f1f1;stroke:#999;stroke-dasharray:6 4}
.room{fill:#e8eef6;stroke:#6a7b90}.sp.STAIR{fill:#9ec5f0;stroke:#1b4f8a;stroke-width:1.5}
.sp.LIFT{fill:#a9dcb0;stroke:#1e6b2a;stroke-width:1.5}.sp.CORRIDOR{fill:#f6cf9a;stroke:#9a5a00;stroke-width:1.5}
.wall{fill:#222}.gap{fill:#d00;fill-opacity:.55;stroke:#d00}.rej{fill:none;stroke:#d00;stroke-width:2;stroke-dasharray:5 3}
.lab{font-size:10px;fill:#222}.hold{color:#a00;font-weight:bold}.p10{color:#555}
table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:3px 8px;text-align:left}
.legend span{display:inline-block;margin-right:14px}.legend i{display:inline-block;width:14px;height:14px;vertical-align:middle;margin-right:4px;border:1px solid #333}
"""


def render_html(model):
    payload = json.dumps(model, ensure_ascii=True, sort_keys=True).replace("</", "<\\/")
    legend = [("#9ec5f0", "STAIR shaft footprint (not a stair)"), ("#a9dcb0", "LIFT shaft footprint (not a lift)"),
              ("#f6cf9a", "CORRIDOR (explicit fixture region)"), ("#222", "0.15 m candidate shaft wall"),
              ("#d00", "1.00 m explicit opening / rejected candidate"), ("#f1f1f1", "UNPROGRAMMED (not corridor)"),
              ("#e8eef6", "programmed room (P8, reference)")]
    leg = "".join(f'<span><i style="background:{c}"></i>{html.escape(t)}</span>' for c, t in legend)
    banner = "".join(f"<div>{html.escape(d)}</div>" for d in model["disclaimers"])
    return (f"<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>P9A circulation + shaft footprint overlay ({html.escape(model['project_id'])})</title>"
            f"<style>{VIEWER_CSS}</style></head><body>\n"
            f"<div class=\"banner\">{banner}</div>\n"
            f"<h1>P9A explicit circulation and shaft footprint alignment</h1>\n"
            f"<p>{html.escape(model['module_version'])} | source {model['source_sha256'][:12]} | "
            f"input model {model['source_model_sha256'][:12]} | fixture {model['fixture_sha256'][:12]}</p>\n"
            f"<div id=\"status\"></div><div id=\"strat\"></div><div id=\"lvl\"></div>\n"
            f"<svg id=\"plan\" role=\"img\" aria-label=\"plan overlay\"></svg>\n"
            f"<div class=\"legend\">{leg}</div>\n<div id=\"detail\"></div>\n"
            f"<script type=\"application/json\" id=\"p9-model\">{payload}</script>\n"
            f"<script>{VIEWER_JS}</script>\n</body></html>\n")


def extract_embedded_model(html_text):
    start = html_text.index('id="p9-model">') + len('id="p9-model">')
    end = html_text.index("</script>", start)
    return json.loads(html_text[start:end])


# ---------------------------------------------------------------- run
def run(source_path, fixture_path, out_dir, expect_project):
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise P9Error(f"out-dir must be fresh/empty: {out}")
    model, model_sha, source_sha = load_source(source_path, expect_project)
    fx_bytes = Path(fixture_path).read_bytes()
    try:
        fixture = json.loads(fx_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise P9Error(f"fixture unreadable: {exc}")
    p9 = build_model(model, model_sha, source_sha, fixture, sha256_bytes(fx_bytes))
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    model_name = "P9_CIRCULATION_VERTICAL_MODEL.json"
    (out / model_name).write_text(dumps(p9), encoding="utf-8")
    files["model"] = model_name
    html_name = "P9_CIRCULATION_VERTICAL_VIEWER.html"
    (out / html_name).write_text(render_html(p9), encoding="utf-8")
    files["viewer"] = html_name
    strategies, readbacks = {}, {}
    for s in p9["strategies"]:
        entry = {"status": s["status"], "dxf": None, "rejection_count": len(s["rejections"])}
        if s["cad_published"]:
            dxf_name = f"P9_CIRCULATION_VERTICAL_{s['strategy']}.dxf"
            write_dxf(s, out / dxf_name, p9["constants"])
            rb = readback_dxf(out / dxf_name, s)
            if not rb["ok"]:
                raise P9Error(f"DXF readback failed for {s['strategy']}: {rb['problems']}")
            entry["dxf"] = dxf_name
            entry["dxf_file_sha256"] = sha256_file(out / dxf_name)
            entry["dxf_file_sha256_note"] = "NOT_BYTE_STABLE_ezdxf_writes_save_time_and_GUIDs"
            entry["dxf_geometry_digest_sha256"] = rb["geometry_digest_sha256"]
            readbacks[s["strategy"]] = rb
        strategies[s["strategy"]] = entry
    receipt = {
        "schema": RECEIPT_SCHEMA, "module_version": MODULE_VERSION, "work_id": WORK_ID,
        "project_id": p9["project_id"], "status": p9["status"],
        "total_pass_claimed": False, "native_dwg": "NOT_DONE",
        "hashes": {"source_sha256": source_sha, "source_model_sha256": model_sha,
                   "fixture_sha256": p9["fixture_sha256"],
                   "model_json_sha256": sha256_file(out / model_name),
                   "viewer_html_sha256": sha256_file(out / html_name)},
        "strategies": strategies, "cad_readback": readbacks, "claims": dict(CLAIMS),
        "disclaimers": list(DISCLAIMERS),
    }
    (out / "P9_CIRCULATION_VERTICAL_RECEIPT.json").write_text(dumps(receipt), encoding="utf-8")
    return p9, receipt


def main(argv=None):
    ap = argparse.ArgumentParser(description="P9A explicit circulation + shaft footprint overlay")
    ap.add_argument("source", help="P8 massing_result.json (read-only)")
    ap.add_argument("--fixture", help="explicit P9 fixture JSON")
    ap.add_argument("--out-dir", required=True, help="fresh output directory")
    ap.add_argument("--expect-project", required=True)
    ap.add_argument("--write-sample-fixture", metavar="PATH",
                    help="write the sample candidate fixture bound to the source model, then exit")
    a = ap.parse_args(argv)
    try:
        if a.write_sample_fixture:
            model, model_sha, source_sha = load_source(a.source, a.expect_project)
            target = Path(a.write_sample_fixture)
            if target.exists():
                raise P9Error(f"refusing to overwrite {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(dumps(sample_fixture(model_sha, source_sha, model["project_id"],
                                                   sorted(o["strategy"] for o in model["options"]))), encoding="utf-8")
            print(f"고정 입력 작성: {target}")
            return 0
        if not a.fixture:
            raise P9Error("--fixture is required")
        _, receipt = run(a.source, a.fixture, a.out_dir, a.expect_project)
    except P9Error as exc:
        print(f"실패(fail-closed): {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "strategies": receipt["strategies"],
                      "native_dwg": receipt["native_dwg"]}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
