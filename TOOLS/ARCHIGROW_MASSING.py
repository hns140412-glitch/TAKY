#!/usr/bin/env python3
"""ArchiGrow site -> parametric floor masses -> existing layout KPI -> local viewer.

This is an architecture exploration generator. NOT a cadastral, statutory
setback, zoning, approval, or buildability checker. No network/API calls.
Geometry verification uses ARCHIGROW_LAYOUT_KPI (single existing authority).
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("archigrow_layout_kpi", HERE / "ARCHIGROW_LAYOUT_KPI.py")
K = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K)
VERSION = "ARCHIGROW_MASSING/2026-10-18.2"
STRATEGIES = ("BALANCED", "SCULPTURAL")
# Optional free dependencies, installed in the ArchiGrow workbench venv.
# Existing rectangle-only path remains available for plain Python operation.
try:
    from shapely.geometry import Polygon as ShapelyPolygon
    from shapely.affinity import translate as shapely_translate
    from shapely.geometry import box as shapely_box
    from shapely.geometry.polygon import orient as shapely_orient
except ImportError:
    ShapelyPolygon = None
    shapely_translate = None
    shapely_box = None
    shapely_orient = None


class MassingHold(Exception):
    pass


def finite(v, lower=None, upper=None):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise MassingHold("INVALID_NUMERIC_PARAMETER")
    if lower is not None and v < lower or upper is not None and v > upper:
        raise MassingHold("NUMERIC_PARAMETER_OUT_OF_RANGE")
    return float(v)


def rectangle(cx, cy, width, depth):
    return [[round(cx-width/2, 8), round(cy-depth/2, 8)],
            [round(cx+width/2, 8), round(cy-depth/2, 8)],
            [round(cx+width/2, 8), round(cy+depth/2, 8)],
            [round(cx-width/2, 8), round(cy+depth/2, 8)]]


def within(poly, site):
    return (all(K.point_in_polygon(p, site) for p in poly)
            and abs(K.intersection_area(poly, site)-K.area(poly)) <= max(1e-5, K.area(poly)*1e-8))


def _dominant_polygon(geom):
    if geom.is_empty:
        return None
    parts = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
    polys = [p for p in parts if p.geom_type == "Polygon" and p.area > 1e-6]
    return max(polys, key=lambda p: p.area) if polys else None


def _offset_to_area(geom, required):
    """Fit a polygon by inward buffer while retaining irregular site outline."""
    if required > geom.area + 1e-5 or required <= 0:
        raise MassingHold("OFFSET_AREA_OUT_OF_RANGE")
    if abs(geom.area-required) < 1e-6:
        return geom
    x0,y0,x1,y1=geom.bounds
    low, high=0.0, max(x1-x0, y1-y0)
    result=geom
    for _ in range(65):
        mid=(low+high)/2
        part=_dominant_polygon(geom.buffer(-mid,join_style=2))
        a=part.area if part is not None else 0.0
        if a>required:
            low=mid
        else:
            high=mid
            if part is not None:
                result=part
    if abs(result.area-required)>max(0.005,required*1e-6):
        raise MassingHold("SITE_OFFSET_AREA_PRECISION_FAILED")
    return result


def _ring(geom):
    return [[round(x,7),round(y,7)] for x,y in list(geom.exterior.coords)[:-1]]


def site_offset_footprint(site,max_area,clearance):
    """True polygon buffering, instead of substituting a rectangle for an irregular lot."""
    if ShapelyPolygon is None:
        raise MassingHold("FREE_SHAPELY_DEPENDENCY_REQUIRED")
    source=ShapelyPolygon(site)
    if not source.is_valid or source.area<=0:
        raise MassingHold("SITE_POLYGON_INVALID")
    candidate=_dominant_polygon(source.buffer(-clearance,join_style=2))
    if candidate is None:
        raise MassingHold("NO_SITE_OFFSET_ENVELOPE")
    if candidate.area>max_area:
        candidate=_offset_to_area(candidate,max_area)
    poly=_ring(candidate)
    if not K.polygon_valid(poly) or not within(poly,site):
        raise MassingHold("SITE_OFFSET_GEOMETRY_VALIDATION_FAILED")
    return {"mode":"SITE_OFFSET","geometry":candidate,
            "area_m2":K.area(poly),"polygon":poly}


def find_footprint(site, max_area, clearance):
    """Largest tested axis-aligned rectangle; clearance is a conservative demo buffer.

    The rectangle enlarged on each side by 'clearance' must remain within the
    exact site boundary. This is NOT a legal or polygon-offset setback solver.
    """
    x0, x1 = min(p[0] for p in site), max(p[0] for p in site)
    y0, y1 = min(p[1] for p in site), max(p[1] for p in site)
    sw, sh = x1-x0, y1-y0
    if sw <= 0 or sh <= 0:
        raise MassingHold("SITE_EXTENT_INVALID")
    ratio = sw/sh
    best = None
    for rfactor in (1.0, 0.78, 1.28, 0.55, 1.8):
        aspect = ratio*rfactor
        for frac in range(100, 7, -4):
            req_area = max_area*frac/100
            w, h = math.sqrt(req_area*aspect), math.sqrt(req_area/aspect)
            if w + 2*clearance >= sw or h + 2*clearance >= sh:
                continue
            mx = (sw-w)/2
            my = (sh-h)/2
            for fx in (0, -0.3, 0.3, -0.6, 0.6):
                for fy in (0, -0.3, 0.3, -0.6, 0.6):
                    cx = (x0+x1)/2 + fx*mx
                    cy = (y0+y1)/2 + fy*my
                    expanded = rectangle(cx, cy, w+2*clearance, h+2*clearance)
                    if within(expanded, site):
                        candidate = (req_area, cx, cy, w, h)
                        if best is None or req_area > best[0]:
                            best = candidate
                        break
                if best and best[0] >= req_area:
                    break
            if best and best[0] >= max_area-1e-6:
                return best
    if best is None:
        raise MassingHold("NO_INTERIOR_MASS_FOUND")
    return best


def tier_weights(floors, strategy):
    if strategy == "BALANCED":
        return [1.0 if i < 2 else (0.65 if i < math.ceil(floors*0.70)
                    else max(0.22, 0.59-0.075*(i-math.ceil(floors*0.70))))
                for i in range(floors)]
    if strategy == "SCULPTURAL":
        # Gradual tier reduction with a shifting plan centre; no alternating
        # floor-area spikes that would visually produce disconnected slabs.
        return [max(0.20, 1.0-0.045*i) for i in range(floors)]
    raise MassingHold("UNKNOWN_MASS_STRATEGY")


def allocate_areas(target, maximum, weights):
    if target > maximum*len(weights)+1e-5:
        raise MassingHold("TARGET_AREA_EXCEEDS_ALL_FLOORS_CAPACITY")
    low, high = 0.0, maximum/max(min(weights), 1e-5)*2
    for _ in range(90):
        scale = (low+high)/2
        total = sum(min(maximum, w*scale) for w in weights)
        if total < target:
            low = scale
        else:
            high = scale
    result = [min(maximum, w*high) for w in weights]
    if abs(sum(result)-target) > max(0.001, target*1e-7):
        raise MassingHold("AREA_ALLOCATOR_PRECISION_FAILURE")
    return result


def floor_polygon(area_m2, base, i, floors, strategy):
    if isinstance(base,dict) and base.get("mode")=="SITE_OFFSET":
        geom=_offset_to_area(base["geometry"],area_m2)
        if strategy=="SCULPTURAL":
            x0,y0,x1,y1=base["geometry"].bounds
            dx=0.045*(x1-x0)*math.sin(i*0.79)
            dy=0.035*(y1-y0)*math.cos(i*0.51)
            for factor in (1.0,0.5,0.25,0.0):
                shifted=shapely_translate(geom,xoff=dx*factor,yoff=dy*factor)
                if base["geometry"].covers(shifted):
                    geom=shifted
                    break
        return _ring(geom)
    _, cx, cy, maxw, maxh = base
    scale = math.sqrt(area_m2/(maxw*maxh))
    w, h = maxw*scale, maxh*scale
    if strategy == "SCULPTURAL":
        # Both shifts stay inside the verified base rectangle.
        amplitude = min((maxw-w)/2, (maxh-h)/2)
        phase = math.sin(i*0.79)
        # Limit eccentricity so successive floors retain substantial overlap.
        cx += amplitude*0.35*phase
        cy += amplitude*0.25*math.cos(i*0.51)
    return rectangle(cx,cy,w,h)


def _normalize_site_coordinates(source):
    """Convert explicit WGS84 parcel vertices into local projected meters.

    Every point is provided by the caller; this function does not obtain or
    fabricate a parcel boundary. Projection metadata preserves the original
    coordinate frame for future verified cadastral/source binding.
    """
    raw=source.get("site_polygon")
    if not isinstance(raw,list):
        raise MassingHold("SITE_POLYGON_REQUIRED")
    if source.get("coordinate_units")=="m":
        return raw, {"input_units":"m","working_units":"m",
                     "projected_crs":source.get("projected_crs","USER_LOCAL_METERS")}
    if source.get("coordinate_units")!="degrees" or source.get("source_crs")!="EPSG:4326":
        raise MassingHold("PROJECTED_METER_COORDINATES_REQUIRED")
    target=source.get("target_crs")
    if target not in ("EPSG:5179","EPSG:5186"):
        raise MassingHold("EXPLICIT_KOREAN_PROJECTED_CRS_REQUIRED")
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise MassingHold("FREE_PYPROJ_DEPENDENCY_REQUIRED") from exc
    if len(raw)<3 or any(not isinstance(p,list) or len(p)!=2 or
                         not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in p)
                         for p in raw):
        raise MassingHold("SITE_WGS84_COORDINATES_INVALID")
    if any(not (-180<=p[0]<=180 and -90<=p[1]<=90) for p in raw):
        raise MassingHold("SITE_WGS84_COORDINATES_OUT_OF_RANGE")
    trans=Transformer.from_crs("EPSG:4326",target,always_xy=True)
    projected=[trans.transform(p[0],p[1]) for p in raw]
    if any(not (math.isfinite(x) and math.isfinite(y)) for x,y in projected):
        raise MassingHold("CRS_PROJECTION_FAILED")
    ox,oy=projected[0]
    metric=[[round(x-ox,7),round(y-oy,7)] for x,y in projected]
    return metric,{"input_units":"degrees","source_crs":"EPSG:4326",
                   "projected_crs":target,"local_origin_projected_m":[ox,oy],
                   "working_units":"m"}


PROGRAM_LABEL = "FLOOR_ZONE_ASSIGNMENT_NOT_ROOM_GEOMETRY"
PROGRAM_CATEGORIES = ("RESIDENTIAL", "COMMERCIAL", "OFFICE", "PUBLIC", "SERVICE", "CIRCULATION", "PARKING", "OTHER")
VERTICAL_PREFERENCES = (None, "SAME_LEVEL", "ADJACENT_LEVEL", "ANY")
MAX_PROGRAM_SPACES = 60
MAX_IMPROVE_PASSES = 20
ROOM_GEOMETRY_MODES = ("POLYGON_PARTITION_V1",)
ROOM_GEOMETRY_LABEL = "GEOMETRICAL_DRAFT_2D_PARTITION_NOT_CODE_COMPLIANCE"
ROOM_AREA_TOL_M2 = 0.01          # required room/closure area accuracy
ROOM_OVERLAP_TOL_M2 = 1e-4       # allowance for 7-decimal coordinate rounding
ROOM_CONTAIN_TOL_M = 1e-6
ROOM_RESIDUAL_MIN_M2 = 1e-6
ROOM_TOUCH_MIN_M = 1e-3          # numerical floor: shorter contact is a point/corner touch
ROOM_BISECT_ITERATIONS = 64
ROOM_CUT_BUDGET = 600            # axis-cut attempts per floor, then HOLD


def _hold(code):
    raise MassingHold(code)


def validate_program(sp, pid, floors, target):
    """Strict explicit-input check; every defect rejects, nothing is dropped."""
    if not isinstance(sp, dict):
        _hold("SPATIAL_PROGRAM_INVALID")
    if set(sp) - {"spaces", "links", "entrance_space_id", "project_id", "room_geometry_mode"}:
        _hold("SPATIAL_PROGRAM_UNSUPPORTED_FIELD")
    mode = None
    if "room_geometry_mode" in sp:
        mode = sp["room_geometry_mode"]
        if not isinstance(mode, str) or mode not in ROOM_GEOMETRY_MODES:
            _hold("SPATIAL_PROGRAM_ROOM_GEOMETRY_MODE_UNSUPPORTED")
        if ShapelyPolygon is None:
            _hold("ROOM_GEOMETRY_SHAPELY_REQUIRED")
    if "project_id" in sp and str(sp["project_id"]).strip() != pid:
        _hold("SPATIAL_PROGRAM_PROJECT_ID_MISMATCH")
    spaces, links = sp.get("spaces"), sp.get("links", [])
    if not isinstance(spaces, list) or not spaces or not isinstance(links, list):
        _hold("SPATIAL_PROGRAM_SPACES_REQUIRED")
    if len(spaces) > MAX_PROGRAM_SPACES:
        _hold("SPATIAL_PROGRAM_TOO_MANY_SPACES")
    nodes = {}
    for s in spaces:
        if not isinstance(s, dict) or set(s) - {"id", "name", "area_m2", "category", "level_preference"}:
            _hold("SPATIAL_PROGRAM_SPACE_INVALID")
        sid = s.get("id")
        if not isinstance(sid, str) or not sid.strip():
            _hold("SPATIAL_PROGRAM_SPACE_ID_INVALID")
        if sid in nodes:
            _hold("SPATIAL_PROGRAM_DUPLICATE_SPACE_ID")
        if not isinstance(s.get("name"), str) or not s["name"].strip():
            _hold("SPATIAL_PROGRAM_SPACE_NAME_INVALID")
        if s.get("category") not in PROGRAM_CATEGORIES:
            _hold("SPATIAL_PROGRAM_CATEGORY_UNSUPPORTED")
        pref = s.get("level_preference")
        if pref is not None and (isinstance(pref, bool) or not isinstance(pref, int) or not 1 <= pref <= floors):
            _hold("SPATIAL_PROGRAM_LEVEL_PREFERENCE_INVALID")
        nodes[sid] = {"id": sid, "name": s["name"], "category": s["category"],
                      "area_m2": finite(s.get("area_m2"), 0.0001), "level_preference": pref}
    if sum(n["area_m2"] for n in nodes.values()) > target + 1e-6:
        _hold("SPATIAL_PROGRAM_AREA_EXCEEDS_TARGET_GFA")
    entrance = sp.get("entrance_space_id")
    if entrance not in nodes:
        _hold("SPATIAL_PROGRAM_ENTRANCE_MISSING")
    edges, seen = [], set()
    for l in links:
        if not isinstance(l, dict) or set(l) - {"a", "b", "weight", "vertical_preference"}:
            _hold("SPATIAL_PROGRAM_LINK_INVALID")
        a, b = l.get("a"), l.get("b")
        if a not in nodes or b not in nodes:
            _hold("SPATIAL_PROGRAM_LINK_ENDPOINT_MISSING")
        if a == b:
            _hold("SPATIAL_PROGRAM_SELF_LINK")
        if frozenset((a, b)) in seen:
            _hold("SPATIAL_PROGRAM_DUPLICATE_LINK")
        seen.add(frozenset((a, b)))
        vp = l.get("vertical_preference")
        if vp not in VERTICAL_PREFERENCES:
            _hold("SPATIAL_PROGRAM_VERTICAL_PREFERENCE_UNSUPPORTED")
        edges.append({"a": a, "b": b, "weight": finite(l.get("weight"), 0.0001, 100), "vp": vp})
    adj = {sid: [] for sid in nodes}
    for e in edges:
        adj[e["a"]].append((e["b"], e["weight"]))
        adj[e["b"]].append((e["a"], e["weight"]))
    depth, queue = {entrance: 0}, [entrance]
    for cur in queue:                      # BFS: access depth in hops from entrance
        for nxt, _ in sorted(adj[cur]):
            if nxt not in depth:
                depth[nxt] = depth[cur]+1
                queue.append(nxt)
    if len(depth) != len(nodes):
        _hold("SPATIAL_PROGRAM_DISCONNECTED_FROM_ENTRANCE:"+",".join(sorted(set(nodes)-set(depth))[:5]))
    for sid, n in nodes.items():
        n["depth"], n["degree"] = depth[sid], len(adj[sid])
        n["weighted_degree"] = round(sum(w for _, w in adj[sid]), 6)
    return {"nodes": nodes, "edges": edges, "adj": adj, "entrance": entrance, "room_geometry_mode": mode}


def _link_cost(d, vp):
    if vp == "ANY":
        return 0
    if vp == "ADJACENT_LEVEL":
        return max(0, d-1)
    return d


def _program_cost(g, level, pref_w):
    cost = sum(e["weight"]*_link_cost(abs(level[e["a"]]-level[e["b"]]), e["vp"])
               for e in g["edges"] if e["a"] in level and e["b"] in level)
    return cost+sum(pref_w*abs(level[s]-(n["level_preference"]-1))
                    for s, n in g["nodes"].items() if s in level and n["level_preference"])


def allocate_program(g, caps):
    """Greedy placement, bounded feasibility fallback, then local improvement."""
    nodes, entrance = g["nodes"], g["entrance"]
    for s, node in nodes.items():
        area = node["area_m2"]
        if (isinstance(area, bool) or not isinstance(area, (int, float))
                or not 0 < area < float("inf")):
            _hold("SPATIAL_PROGRAM_INVALID_AREA:"+s)

    pref_w = max([e["weight"] for e in g["edges"]] or [1.0])
    free, level = list(caps), {}

    def fits(s, l):
        return nodes[s]["area_m2"] <= free[l]+1e-9

    if not free or not fits(entrance, 0):
        _hold("SPATIAL_PROGRAM_INSUFFICIENT_FLOOR_CAPACITY:ENTRANCE_LEVEL")
    level[entrance] = 0
    free[0] -= nodes[entrance]["area_m2"]

    while len(level) < len(nodes):
        def tie(s):
            return (-sum(w for t, w in g["adj"][s] if t in level),
                    nodes[s]["depth"], -nodes[s]["area_m2"], s)

        s = min((x for x in nodes if x not in level), key=tie)
        scored = []
        for l in range(len(caps)):
            if fits(s, l):
                level[s] = l
                scored.append((_program_cost(g, level, pref_w), l))
                del level[s]
        if not scored:
            # Restore the entrance-only state; greedy decisions are reversible.
            free, level = list(caps), {entrance: 0}
            free[0] -= nodes[entrance]["area_m2"]
            order = sorted((x for x in nodes if x != entrance),
                           key=lambda x: (-nodes[x]["area_m2"], x))

            def choices(depth):
                area = nodes[order[depth]]["area_m2"]
                seen = set()
                result = []
                for floor, remaining in enumerate(free):
                    if area <= remaining+1e-9 and remaining not in seen:
                        seen.add(remaining)
                        result.append(floor)
                return iter(result)

            # Iterative DFS avoids a recursion limit for large programs.
            # Equal residual capacities are equivalent for feasibility only.
            stack = [choices(0)]
            depth, states = 0, 0
            while stack:
                floor = next(stack[-1], None)
                if floor is None:
                    stack.pop()
                    if depth == 0:
                        _hold("SPATIAL_PROGRAM_INSUFFICIENT_FLOOR_CAPACITY:"+s)
                    depth -= 1
                    previous = order[depth]
                    old = level.pop(previous)
                    free[old] += nodes[previous]["area_m2"]
                    continue

                if states >= 50000:
                    _hold("SPATIAL_PROGRAM_SEARCH_BUDGET_EXHAUSTED")
                states += 1
                current = order[depth]
                level[current] = floor
                free[floor] -= nodes[current]["area_m2"]
                depth += 1
                if depth == len(order):
                    break
                stack.append(choices(depth))
            break

        l = min(scored)[1]
        level[s] = l
        free[l] -= nodes[s]["area_m2"]

    movable = sorted(s for s in nodes if s != entrance)
    for _ in range(MAX_IMPROVE_PASSES):
        improved = False
        base = _program_cost(g, level, pref_w)
        for s in movable:
            for l in range(len(caps)):
                if l == level[s] or not fits(s, l):
                    continue
                old = level[s]
                level[s] = l
                c = _program_cost(g, level, pref_w)
                if c < base-1e-9:
                    free[old] += nodes[s]["area_m2"]
                    free[l] -= nodes[s]["area_m2"]
                    base, improved = c, True
                else:
                    level[s] = old
        for i, a in enumerate(movable):
            for b in movable[i+1:]:
                la, lb = level[a], level[b]
                aa, ab = nodes[a]["area_m2"], nodes[b]["area_m2"]
                if la == lb or aa > free[lb]+ab+1e-9 or ab > free[la]+aa+1e-9:
                    continue
                level[a], level[b] = lb, la
                c = _program_cost(g, level, pref_w)
                if c < base-1e-9:
                    free[la] += aa-ab
                    free[lb] += ab-aa
                    base, improved = c, True
                else:
                    level[a], level[b] = la, lb
        if not improved:
            break
    return level, pref_w

def program_result(g, level, level_rows, gfa):
    nodes, floors = g["nodes"], len(level_rows)
    num = den = 0.0
    for e in g["edges"]:
        num += e["weight"]*_link_cost(abs(level[e["a"]]-level[e["b"]]), e["vp"])
        den += e["weight"]*(max(0, floors-2) if e["vp"] == "ADJACENT_LEVEL" else floors-1)
    adjacency = 1.0 if den == 0 else 1-num/den
    prefs = [(s, n) for s, n in nodes.items() if n["level_preference"]]
    met = sum(1 for s, n in prefs if level[s] == n["level_preference"]-1)
    pref_ratio = met/len(prefs) if prefs else None
    score = adjacency if pref_ratio is None else 0.8*adjacency+0.2*pref_ratio
    per_level = []
    for i, row in enumerate(level_rows):
        ids = sorted(s for s in nodes if level[s] == i)
        used = sum(nodes[s]["area_m2"] for s in ids)
        per_level.append({"level": row["level"], "capacity_m2": row["area_m2"],
                          "assigned_area_m2": round(used, 6),
                          "utilization_pct": round(used/row["area_m2"]*100, 4), "space_ids": ids})
    total = sum(n["area_m2"] for n in nodes.values())
    return {"representation": PROGRAM_LABEL,
            "spaces": [{"id": s, "name": n["name"], "category": n["category"], "area_m2": n["area_m2"],
                        "level": level_rows[level[s]]["level"], "access_depth": n["depth"],
                        "degree": n["degree"], "weighted_degree": n["weighted_degree"],
                        "level_preference": n["level_preference"],
                        "preference_met": None if not n["level_preference"] else level[s] == n["level_preference"]-1}
                       for s, n in sorted(nodes.items())],
            "levels": per_level,
            "metrics": {"adjacency_score": round(adjacency, 6),
                        "level_preference_met_ratio": None if pref_ratio is None else round(pref_ratio, 6),
                        "weighted_level_distance": round(num, 6),
                        "assigned_area_m2": round(total, 6),
                        "unassigned_gfa_m2": round(gfa-total, 6),
                        "max_access_depth": max(n["depth"] for n in nodes.values()),
                        "entrance_level": level_rows[level[g["entrance"]]]["level"]},
            "score": round(score, 6),
            "score_method": "adjacency=1-sum(w*level_distance)/sum(w*max_distance); score=0.8*adjacency+0.2*preference_ratio when preferences exist",
            "limitations": ["Whole-space floor-zone assignment only; no 2D room boundaries are generated.",
                            "Greedy placement plus bounded local search; not a global optimum.",
                            "Explicit user program; not legal or code compliance verification."]}


def _single_polygon(geom):
    """The one polygon of a clip result, or None when empty/multipart (disconnected)."""
    parts = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
    polys = [p for p in parts if p.geom_type == "Polygon" and p.area > 1e-9]
    return polys[0] if len(polys) == 1 else None


def _axis_cut(region, axis, target):
    """Axis-aligned cut: bisect the line so the low side has area `target`. None if a side is multipart."""
    x0, y0, x1, y1 = region.bounds
    lo, hi = (x0, x1) if axis == 0 else (y0, y1)

    def sides(t):
        if axis == 0:
            return shapely_box(x0-1, y0-1, t, y1+1), shapely_box(t, y0-1, x1+1, y1+1)
        return shapely_box(x0-1, y0-1, x1+1, t), shapely_box(x0-1, t, x1+1, y1+1)
    for _ in range(ROOM_BISECT_ITERATIONS):
        mid = (lo+hi)/2
        if region.intersection(sides(mid)[0]).area < target:
            lo = mid
        else:
            hi = mid
    t = (lo+hi)/2
    low_box, high_box = sides(t)
    low, high = _single_polygon(region.intersection(low_box)), _single_polygon(region.intersection(high_box))
    if low is None or high is None or abs(low.area-target) > ROOM_AREA_TOL_M2/10:
        return None
    return low, high


def _partition_region(region, items, budget):
    """Recursive axis-aligned bisection with backtracking; items=[(key, area)] in plan order."""
    if len(items) == 1:
        return {items[0][0]: region}
    total = sum(a for _, a in items)
    prefix = [sum(a for _, a in items[:k]) for k in range(len(items)+1)]
    x0, y0, x1, y1 = region.bounds
    axes = (0, 1) if x1-x0 >= y1-y0 else (1, 0)
    for k in sorted(range(1, len(items)), key=lambda k: (abs(prefix[k]-total/2), k)):
        for axis in axes:
            if budget[0] <= 0:
                _hold("ROOM_PARTITION_BUDGET_EXHAUSTED")
            budget[0] -= 1
            cut = _axis_cut(region, axis, prefix[k])
            if cut is None:
                continue
            left = _partition_region(cut[0], items[:k], budget)
            right = left and _partition_region(cut[1], items[k:], budget)
            if left and right:
                return {**left, **right}
    return None


def partition_floor(floor, items):
    """Partition one floor polygon (coordinate ring or shapely Polygon) into exact-area pieces.

    items=[(key, area_m2)] in plan order; returns {key: shapely Polygon}. Fail-closed HOLD.
    """
    if ShapelyPolygon is None:
        _hold("ROOM_GEOMETRY_SHAPELY_REQUIRED")
    if isinstance(floor, (list, tuple)):
        if len(floor) < 3:
            _hold("ROOM_PARTITION_FLOOR_GEOMETRY_NOT_MATERIALIZED")
        floor = ShapelyPolygon(floor)
    if floor is None or not hasattr(floor, "geom_type"):
        _hold("ROOM_PARTITION_FLOOR_GEOMETRY_NOT_MATERIALIZED")
    if floor.geom_type != "Polygon":
        _hold("ROOM_PARTITION_FLOOR_NOT_SINGLE_POLYGON")
    if floor.is_empty or not floor.is_valid or floor.area <= 0:
        _hold("ROOM_PARTITION_FLOOR_GEOMETRY_INVALID")
    if sum(a for _, a in items) > floor.area+ROOM_AREA_TOL_M2:
        _hold("ROOM_PARTITION_AREA_EXCEEDS_FLOOR")
    result = _partition_region(floor, items, [ROOM_CUT_BUDGET])
    if result is None:
        _hold("ROOM_PARTITION_IMPOSSIBLE_AXIS_ALIGNED")
    return result


def _room_order(g, ids):
    """Greedy plan order: strongest on-floor links stay consecutive (touching candidates)."""
    idset = set(ids)
    wdeg = {s: sum(w for t, w in g["adj"][s] if t in idset) for s in ids}
    first = g["entrance"] if g["entrance"] in idset else min(ids, key=lambda s: (-wdeg[s], s))
    order = [first]
    while len(order) < len(ids):
        placed = set(order)
        order.append(min((s for s in ids if s not in placed),
                         key=lambda s: (-sum(w for t, w in g["adj"][s] if t in placed), -wdeg[s], s)))
    return order


def _ring_out(poly):
    return [[round(x, 7), round(y, 7)] for x, y in list(shapely_orient(poly, 1.0).exterior.coords)[:-1]]


def _shared_length(a, b):
    return round(b.boundary.intersection(a.boundary.buffer(1e-5)).length, 6)


def room_geometry(g, level, level_rows, pid):
    """Opt-in true 2D rooms: partition each assigned floor polygon; residual stays UNPROGRAMMED."""
    if ShapelyPolygon is None:
        _hold("ROOM_GEOMETRY_SHAPELY_REQUIRED")
    nodes = g["nodes"]
    rooms, level_out = {}, []
    for i, row in enumerate(level_rows):
        ids = sorted(s for s in nodes if level[s] == i)
        if not ids:
            continue
        ring = row.get("polygon")
        if not isinstance(ring, list) or len(ring) < 3:
            _hold("ROOM_PARTITION_FLOOR_GEOMETRY_NOT_MATERIALIZED")
        floor = ShapelyPolygon(ring)
        items = [(s, nodes[s]["area_m2"]) for s in _room_order(g, ids)]
        programmed = sum(a for _, a in items)
        residual_area = max(0.0, floor.area-programmed)
        if residual_area > ROOM_RESIDUAL_MIN_M2:
            items.append((None, residual_area))
        parts = partition_floor(floor, items)
        # Verify the rounded output geometry, not the intermediate exact clip.
        out = {k: ShapelyPolygon(_ring_out(p)) for k, p in parts.items()}
        guard = floor.buffer(ROOM_CONTAIN_TOL_M)
        for k, p in out.items():
            want = nodes[k]["area_m2"] if k else residual_area
            if p.geom_type != "Polygon" or not p.is_valid:
                _hold("ROOM_PARTITION_POLYGON_INVALID:%s" % (k or "RESIDUAL"))
            if abs(p.area-want) > ROOM_AREA_TOL_M2:
                _hold("ROOM_PARTITION_AREA_TOLERANCE_FAILED:%s" % (k or "RESIDUAL"))
            if not guard.covers(p):
                _hold("ROOM_PARTITION_OUTSIDE_FLOOR:%s" % (k or "RESIDUAL"))
        keys = sorted(out, key=lambda k: (k is None, k or ""))
        for n, a in enumerate(keys):
            for b in keys[n+1:]:
                if out[a].intersection(out[b]).area > ROOM_OVERLAP_TOL_M2:
                    _hold("ROOM_PARTITION_OVERLAP:%s,%s" % (a or "RESIDUAL", b or "RESIDUAL"))
        closure = floor.area-sum(p.area for p in out.values())
        if abs(closure) > ROOM_AREA_TOL_M2:
            _hold("ROOM_PARTITION_AREA_CLOSURE_FAILED")
        rooms.update({s: out[s] for s in ids})
        room_rows = []
        for s in ids:
            x0, y0, x1, y1 = out[s].bounds
            room_rows.append({"id": s, "polygon": _ring_out(out[s]), "requested_area_m2": nodes[s]["area_m2"],
                              "area_m2": round(out[s].area, 6),
                              "area_error_m2": round(out[s].area-nodes[s]["area_m2"], 6),
                              "bbox_m": [round(x1-x0, 4), round(y1-y0, 4)]})
        residual = None
        if None in out:
            residual = {"kind": "UNPROGRAMMED_NOT_CORRIDOR", "polygon": _ring_out(out[None]),
                        "area_m2": round(out[None].area, 6),
                        "note": "Unallocated floor remainder; NOT circulation, corridor, or egress."}
        level_out.append({"level": row["level"], "floor_area_m2": round(floor.area, 6), "rooms": room_rows,
                          "residual": residual,
                          "accounting": {"programmed_requested_m2": round(programmed, 6),
                                         "rooms_area_m2": round(sum(out[s].area for s in ids), 6),
                                         "residual_area_m2": 0.0 if residual is None else residual["area_m2"],
                                         "closure_error_m2": round(closure, 6)}})
    links, unmet = [], []
    for e in sorted(g["edges"], key=lambda e: tuple(sorted((e["a"], e["b"])))):
        a, b = sorted((e["a"], e["b"]))
        same = level[a] == level[b]
        length = _shared_length(rooms[a], rooms[b]) if same else 0.0
        touching = same and length >= ROOM_TOUCH_MIN_M
        status = "TOUCHING" if touching else ("SAME_LEVEL_NOT_TOUCHING" if same else "DIFFERENT_LEVEL_NO_PLAN_CONTACT")
        row = {"a": a, "b": b, "weight": e["weight"], "vertical_preference": e["vp"],
               "same_level": same, "shared_boundary_m": length, "status": status,
               "opening": "NOT_MODELED"}
        links.append(row)
        if not touching:
            unmet.append(row)
    return {"representation": ROOM_GEOMETRY_LABEL, "mode": "POLYGON_PARTITION_V1", "project_id": pid,
            "source_status": "USER_EXPLICIT_INPUT_UNVERIFIED", "building_code_compliance": False,
            "geometry_engine": "shapely",
            "method": "recursive axis-aligned bisection of each floor polygon, bounded backtracking, exact-area cuts",
            "tolerances": {"room_area_m2": ROOM_AREA_TOL_M2, "overlap_m2": ROOM_OVERLAP_TOL_M2,
                           "touch_min_length_m": ROOM_TOUCH_MIN_M, "cut_budget_per_floor": ROOM_CUT_BUDGET},
            "levels": level_out,
            "adjacency": {"links": links, "unmet": unmet,
                          "metrics": {"linked_pairs": len(links),
                                      "same_level_pairs": sum(1 for l in links if l["same_level"]),
                                      "touching_pairs": sum(1 for l in links if l["status"] == "TOUCHING"),
                                      "unmet_pairs": len(unmet),
                                      "unmet_weight": round(sum(l["weight"] for l in unmet), 6)},
                          "note": "Same level is not wall adjacency; only measured shared boundary counts. Doors/openings/egress are not modeled."},
            "limitations": ["Geometrical draft only; not building-code, egress, or circulation compliance.",
                            "Axis-aligned slicing partitions only; rooms may be elongated and no minimum dimension is enforced.",
                            "Unprogrammed remainder is not a corridor; no circulation/egress is claimed.",
                            "Multipart or non-sliceable concave floors HOLD."]}


def generate(source):
    if source.get("schema") != "ARCHIGROW_MASSING_INPUT_V1":
        raise MassingHold("SCHEMA_UNSUPPORTED")
    pid = str(source.get("project_id") or "").strip()
    if not pid:
        raise MassingHold("PROJECT_ID_REQUIRED")
    site,coordinate_frame=_normalize_site_coordinates(source)
    if isinstance(source.get("coordinate_frame"),dict):
        coordinate_frame={**coordinate_frame,**source["coordinate_frame"]}
    if len(site) > 3 and site[0] == site[-1]:
        site = site[:-1]
    if source.get("site_holes"):
        raise MassingHold("SITE_HOLES_NOT_SUPPORTED_BY_EXISTING_LAYOUT_KPI")
    if not K.polygon_valid(site):
        raise MassingHold("SITE_POLYGON_INVALID")
    area_geometry = K.area(site)
    area_basis=source.get("site_area_basis")
    area_site=area_geometry
    if area_basis is not None:
        if not isinstance(area_basis,dict) or area_basis.get("source")!="LAND_USE_EUM":
            raise MassingHold("SITE_AREA_BASIS_SOURCE_INVALID")
        pnu=str(area_basis.get("pnu") or "")
        sha=str(area_basis.get("evidence_sha256") or "")
        official=finite(area_basis.get("area_m2"),0.0001)
        if len(pnu)!=19 or not pnu.isdecimal() or len(sha)!=64:
            raise MassingHold("SITE_AREA_BASIS_EVIDENCE_INCOMPLETE")
        if abs(official-area_geometry)>max(1.0,official*0.005):
            raise MassingHold("OFFICIAL_AREA_VS_GEOMETRY_MISMATCH")
        area_site=official
    c = source.get("constraints") or {}
    coverage = finite(c.get("max_coverage_pct"), 0.01, 100)
    far = finite(c.get("max_far_pct"), 0.01, 10000)
    target = finite(c.get("target_far_counted_area_m2"), 0.01)
    floors = c.get("floor_count")
    if not isinstance(floors,int) or isinstance(floors,bool) or not 1 <= floors <= 80:
        raise MassingHold("FLOOR_COUNT_INVALID")
    floor_height = finite(c.get("floor_to_floor_m"), 1.5, 20)
    clearance = finite(c.get("demo_clearance_m"), 0, 50)
    if not source.get("rule_source_status") in ("UNVERIFIED_DEMO","VERIFIED_DESIGN_INPUT"):
        raise MassingHold("RULE_SOURCE_STATUS_REQUIRED")
    legal_status = source.get("rule_source_status")
    if target > area_site*far/100+1e-6:
        raise MassingHold("TARGET_EXCEEDS_DECLARED_FAR_CAP")
    if target > area_site*coverage/100*floors+1e-6:
        raise MassingHold("TARGET_EXCEEDS_DECLARED_COVERAGE_FLOOR_CAP")
    strategies = source.get("strategies") or list(STRATEGIES)
    if not isinstance(strategies,list) or not strategies or any(x not in STRATEGIES for x in strategies):
        raise MassingHold("STRATEGIES_INVALID")
    if len(set(strategies)) != len(strategies):
        raise MassingHold("DUPLICATE_STRATEGY")
    footprint_mode=source.get("footprint_mode","RECTANGLE")
    if footprint_mode=="SITE_OFFSET":
        base=site_offset_footprint(site,area_site*coverage/100,clearance)
        max_floor_area=base["area_m2"]
    elif footprint_mode=="RECTANGLE":
        base=find_footprint(site,area_site*coverage/100,clearance)
        max_floor_area=base[0]
    else:
        raise MassingHold("FOOTPRINT_MODE_UNSUPPORTED")
    if target > max_floor_area*floors+1e-6:
        raise MassingHold("TARGET_EXCEEDS_GEOMETRIC_ENVELOPE")
    program=None
    if source.get("spatial_program") is not None:
        program=validate_program(source["spatial_program"],pid,floors,target)
    options=[]
    for strategy in strategies:
        weights=tier_weights(floors,strategy)
        # Ground podium uses the available footprint before the tower steps back.
        # Keep sufficient residual area to give every remaining level real geometry.
        preferred=2 if strategy=="BALANCED" else 1
        fixed=min(preferred,max(0,floors-1))
        if target-fixed*max_floor_area <= 0.1*(floors-fixed):
            fixed=0
        requested=([max_floor_area]*fixed+
                   allocate_areas(target-fixed*max_floor_area,max_floor_area,weights[fixed:]))
        level_rows=[]
        objects=[]
        for i, requested_area in enumerate(requested):
            poly=floor_polygon(requested_area,base,i,floors,strategy)
            actual_area=K.area(poly)
            if not within(poly,site):
                raise MassingHold("FLOOR_OUTSIDE_SITE")
            level=f"L{i+1:02d}"
            objects.append({"object_id":f"{strategy}-{level}-GFA","object_type":"PROGRAM",
                            "area_scope":"GFA","level":level,"polygon":poly})
            if i==0:
                objects.append({"object_id":f"{strategy}-{level}-FOOTPRINT","object_type":"PROGRAM",
                                "area_scope":"FOOTPRINT","level":level,"polygon":poly})
            level_rows.append({"level":level,"elevation_m":round(i*floor_height,4),
                               "height_m":floor_height,"polygon":poly,"area_m2":actual_area})
        layout={"project_id":pid,"site_polygon":site,"objects":objects}
        verdict=K.evaluate(layout)
        if not verdict["ok"]:
            raise MassingHold("EXISTING_LAYOUT_KPI_FAILED:"+",".join(verdict.get("issues",[])[:3]))
        k=verdict["kpi"]
        gfa=k["gfa_area"]
        if abs(gfa-target)>0.005:
            raise MassingHold("LAYOUT_KPI_TARGET_MISMATCH")
        coverage_pct=k["footprint_area"]/area_site*100
        far_pct=gfa/area_site*100
        if coverage_pct>coverage+1e-5 or far_pct>far+1e-5:
            raise MassingHold("DECLARED_NUMERIC_CAP_EXCEEDED")
        program_alloc=None
        if program:
            assigned,_=allocate_program(program,[r["area_m2"] for r in level_rows])
            program_alloc=program_result(program,assigned,level_rows,gfa)
            if program["room_geometry_mode"]:
                program_alloc["room_geometry"]=room_geometry(program,assigned,level_rows,pid)
                program_alloc["limitations"][0]="Whole-space floor-zone assignment is primary; room_geometry polygons are an opt-in geometrical draft, not building-code compliance."
        options.append({
            "strategy":strategy,
            "footprint_mode":footprint_mode,
            "floors":level_rows,
            "kpi":{"site_area_m2":area_site,"geometry_area_m2":area_geometry,
                   "site_area_source":"LAND_USE_EUM" if area_basis else "GEOMETRY_ONLY_DEMO",
                   "footprint_area_m2":k["footprint_area"],
                   "gross_floor_area_m2":gfa,"far_counted_area_m2":gfa,
                   "coverage_pct":coverage_pct,"far_pct":far_pct,
                   "max_height_m":floor_height*floors},
            "layout_model":layout,
            "validation":{"geometry_kpi":"PASS","source_law":"NOT_VERIFIED",
                          "cross_check_method":"EXISTING_ARCHIGROW_LAYOUT_KPI",
                          "claim_level":"MECHANICAL_ONLY"}
        })
        if program_alloc:
            options[-1]["program_allocation"]=program_alloc
    extra={}
    if program:
        score_of=lambda i:options[i]["program_allocation"]["score"]
        by_score=sorted(range(len(options)),key=lambda i:-score_of(i))
        # Equal scores (within 1e-9) share a competition rank (1,1,3); tied options keep generation order, no invented tiebreak.
        groups=[]
        for i in by_score:
            if groups and abs(score_of(i)-score_of(groups[-1][0]))<=1e-9:
                groups[-1].append(i)
            else:
                groups.append([i])
        order=[]; ranks={}
        for g in groups:
            g.sort()
            for i in g:
                ranks[i]=len(order)+1
            order.extend(g)
        for i in order:
            pa=options[i]["program_allocation"]
            pa["rank"]=ranks[i]
            pa["tied"]=sum(1 for j in order if ranks[j]==ranks[i])>1
        extra["spatial_program"]={
            "representation":PROGRAM_LABEL,"source_status":"USER_EXPLICIT_INPUT_UNVERIFIED",
            "entrance_space_id":program["entrance"],"space_count":len(program["nodes"]),
            "link_count":len(program["edges"]),"legal_claim":False,
            **({"room_geometry_mode":program["room_geometry_mode"]} if program["room_geometry_mode"] else {}),
            "ranking":[{"rank":ranks[i],"strategy":options[i]["strategy"],
                        "score":options[i]["program_allocation"]["score"],
                        "tied":options[i]["program_allocation"]["tied"]} for i in order],
            "tie_note":"Equal spatial_program scores share a rank; this score does not rank site or geometric performance."}
    return {**extra,"schema":"ARCHIGROW_MASSING_RESULT_V1","project_id":pid,"generator":VERSION,
            "input_source_role":source.get("source_role","UNDECLARED"),
            "rule_source_status":legal_status,"coordinate_units":"m",
            "coordinate_frame":coordinate_frame,
            "site_polygon":site,"constraints":c,"options":options,
            "site_area_basis":area_basis,
            "geometry_method":"EXACT_SITE_OFFSET_SHAPELY_WITH_EXISTING_LAYOUT_KPI" if footprint_mode=="SITE_OFFSET" else "RECTANGULAR_SCREENING_WITH_EXISTING_LAYOUT_KPI",
            "legal_feasibility_authorized":False,
            "clearance_note":"Geometric clearance only; not statutory setback verification.",
            "release_status":"DEMO_GEOMETRY_ONLY__LEGAL_AND_DESIGN_REVIEW_PENDING"}


def viewer_html(data):
    compact=json.dumps({k:v for k,v in data.items() if k!="options"},ensure_ascii=False,separators=(",",":"))
    option_data=json.dumps([{k:v for k,v in o.items() if k!="layout_model"} for o in data["options"]],
                           ensure_ascii=False,separators=(",",":"))
    # Escape any user data that could terminate a script element.
    compact=compact.replace("<","\\u003c")
    option_data=option_data.replace("<","\\u003c")
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Archi Grow | Massing Study</title><style>
:root{font:14px/1.5 system-ui,'Malgun Gothic',sans-serif;color:#edf2fa;background:#0b1119}
*{box-sizing:border-box}body{margin:0}.app{min-height:100vh;display:grid;grid-template-columns:300px 1fr}
aside{background:#101b27;border-right:1px solid #223548;padding:28px 22px}
.kicker{font-size:11px;letter-spacing:.18em;color:#86c5d7}h1{font-size:24px;margin:7px 0 5px;letter-spacing:-.035em}
.small{font-size:12px;color:#98aaba}.warning{background:#302a19;color:#f1d7a0;padding:12px;border:1px solid #665330;border-radius:10px;margin:20px 0}
label{display:block;color:#a7bdcd;margin:15px 0 5px;font-size:12px}
select,input{width:100%;background:#182b3b;color:white;border:1px solid #345165;border-radius:8px;padding:10px}
input{padding:8px 0;accent-color:#6acbc4}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:22px}
.metric{padding:13px;background:#162534;border:1px solid #284152;border-radius:10px}
.metric span{display:block;color:#9eb1c0;font-size:11px}.metric strong{font-size:18px}
main{display:flex;flex-direction:column;min-width:0;position:relative}
header{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #223548;padding:20px 25px}
header span{color:#7fc8c2}.viewport{height:calc(100vh - 156px);min-height:380px;position:relative}
canvas{width:100%;height:100%;display:block;touch-action:none}
.legend{position:absolute;left:20px;bottom:20px;padding:12px 15px;color:#a8bccb;background:#10202cdd;border:1px solid #2d4859;border-radius:10px}
footer{padding:16px 25px;border-top:1px solid #223548;color:#89a3b8;font-size:12px}
@media(max-width:760px){.app{grid-template-columns:1fr}aside{padding:16px;order:2}.metrics{grid-template-columns:repeat(2,1fr)}main{order:1}.viewport{height:54vh;min-height:320px}header{padding:15px}footer{padding:12px}}
</style></head><body><div class="app"><aside>
<div class="kicker">ARCHI GROW / LOCAL STUDY</div><h1>Parametric Massing</h1>
<div class="small" id="project"></div>
<div class="warning">샘플 형상 검토용 · 실제 대지 경계·건축법규·인허가 적합성 미확인</div>
<label for="strategy">매스 생성 전략</label><select id="strategy"></select>
<label for="levels">표시 층수 <output id="floorsLabel"></output></label>
<input id="levels" type="range" min="1" step="1">
<div class="small">상부 층을 제외하여 면적·높이가 바뀌는 검토 모드입니다.</div>
<label for="angle">3D 회전 <output id="angleLabel"></output></label>
<input id="angle" type="range" min="-180" max="180" value="-35">
<div class="metrics" id="metrics"></div></aside>
<main><header><div><b id="strategyName">Massing Option</b><div class="small">부지 경계 · 층별 적층 · 자동 면적 갱신</div></div>
<span>LOCAL / NO API</span></header>
<div class="viewport"><canvas id="model"></canvas><div class="legend">드래그하여 회전 · 전략 변경 · 층수 조절</div></div>
<footer>검산: 기존 ArchiGrow Layout KPI · 법규/좌표계 실무 검증 별도 · 시안 승인 전 후보</footer></main></div>
<script>
"use strict";
const project=__META__, options=__OPTIONS__;
const site=project.site_polygon, selection=document.getElementById('strategy'),
levels=document.getElementById('levels'),angle=document.getElementById('angle'),
canvas=document.getElementById('model'),ctx=canvas.getContext('2d');
document.getElementById('project').textContent=project.project_id;
options.forEach((o,i)=>{let x=document.createElement('option');x.value=i;x.textContent=o.strategy;selection.appendChild(x)});
levels.max=options[0].floors.length;levels.value=levels.max;
let yaw=-35, dragging=false,lastX=0;angle.value=yaw;
function polygonArea(poly){let n=poly.length,sum=0;for(let i=0;i<n;i++){let p=poly[i],q=poly[(i+1)%n];sum+=p[0]*q[1]-q[0]*p[1]}return Math.abs(sum)/2}
function update(){let o=options[Number(selection.value)||0],count=Number(levels.value);
if(count>o.floors.length){count=o.floors.length;levels.value=count}
let shown=o.floors.slice(0,count),gfa=shown.reduce((s,f)=>s+polygonArea(f.polygon),0),
area=project.site_area_basis?Number(project.site_area_basis.area_m2):polygonArea(site),foot=polygonArea(shown[0].polygon),height=shown[shown.length-1].elevation_m+shown[shown.length-1].height_m;
document.getElementById('floorsLabel').textContent=count+'F';
document.getElementById('angleLabel').textContent=yaw+'°';
document.getElementById('strategyName').textContent=o.strategy+' · '+count+' FLOOR';
let vals=[['대지면적'+(project.site_area_basis?' (토지이음)':''),area,'㎡'],['건축면적',foot,'㎡'],['표시층 연면적',gfa,'㎡'],['용적률(단순)',100*gfa/area,'%'],['건폐율(단순)',100*foot/area,'%'],['표시 최고높이',height,'m']];
document.getElementById('metrics').replaceChildren(...vals.map(([name,val,unit])=>{let box=document.createElement('div');box.className='metric';
let t=document.createElement('span'),v=document.createElement('strong');t.textContent=name;v.textContent=val.toLocaleString('ko-KR',{maximumFractionDigits:1})+unit;box.append(t,v);return box}));
draw(shown,o.strategy)}
function draw(floors,strategy){let rect=canvas.getBoundingClientRect(),ratio=Math.min(2,window.devicePixelRatio||1);
canvas.width=Math.max(1,Math.floor(rect.width*ratio));canvas.height=Math.max(1,Math.floor(rect.height*ratio));ctx.setTransform(ratio,0,0,ratio,0,0);
let W=rect.width,H=rect.height;ctx.clearRect(0,0,W,H);
let xs=site.map(p=>p[0]),ys=site.map(p=>p[1]),mx=(Math.min(...xs)+Math.max(...xs))/2,my=(Math.min(...ys)+Math.max(...ys))/2;
let maxz=floors[floors.length-1].elevation_m+floors[floors.length-1].height_m,extent=Math.max(Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys),maxz*.9);
let scale=Math.min(W,H)*0.7/Math.max(extent,1);let rad=yaw*Math.PI/180;
function point(p,z){let x=p[0]-mx,y=p[1]-my;let a=x*Math.cos(rad)-y*Math.sin(rad),b=x*Math.sin(rad)+y*Math.cos(rad);
return [W/2+a*scale,H*.71+(b*.49-z*.84)*scale,b]}
function polygon(pts,fill,stroke,width=1){ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();
ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.stroke()}
ctx.fillStyle='#0c1824';ctx.fillRect(0,0,W,H);
ctx.strokeStyle='#183042';ctx.lineWidth=1;
for(let i=0;i<20;i++){let a=i*Math.max(1,W/16);ctx.beginPath();ctx.moveTo(a,0);ctx.lineTo(a,H);ctx.stroke();
ctx.beginPath();ctx.moveTo(0,a);ctx.lineTo(W,a);ctx.stroke()}
polygon(site.map(p=>point(p,0)),'#12334055','#72aeb2',1.7);
let faces=[];
floors.forEach((f,idx)=>{let p=f.polygon,z=f.elevation_m,zt=z+f.height_m;
for(let j=0;j<p.length;j++){let q=(j+1)%p.length,pts=[point(p[j],z),point(p[q],z),point(p[q],zt),point(p[j],zt)];
let dep=pts.reduce((s,v)=>s+v[2],0)/4;
faces.push({pts,dep,fill:strategy==='BALANCED'?(j%2?'#6e98a7':'#a1bcc6'):(j%2?'#8b9aa7':'#c5bcaa'),edge:'#243849'})}
let pts=p.map(x=>point(x,zt));faces.push({pts,dep:pts.reduce((s,v)=>s+v[2],0)/pts.length,fill:'#d8ded6',edge:'#2d4551'})});
faces.sort((a,b)=>b.dep-a.dep);faces.forEach(f=>polygon(f.pts,f.fill,f.edge,.85));
ctx.fillStyle='#9cccd1';ctx.font='12px system-ui';ctx.fillText('SITE  ·  '+Math.round(polygonArea(site))+'m²',20,30)}
selection.addEventListener('change',()=>{levels.max=options[selection.value].floors.length;levels.value=levels.max;update()});
levels.addEventListener('input',update);angle.addEventListener('input',()=>{yaw=Number(angle.value);update()});
canvas.addEventListener('pointerdown',e=>{dragging=true;lastX=e.clientX;canvas.setPointerCapture(e.pointerId)});
canvas.addEventListener('pointermove',e=>{if(!dragging)return;yaw=Math.max(-180,Math.min(180,yaw+(e.clientX-lastX)*.7));lastX=e.clientX;angle.value=yaw;update()});
canvas.addEventListener('pointerup',()=>dragging=false);window.addEventListener('resize',update);update();
</script></body></html>""".replace("__META__",compact).replace("__OPTIONS__",option_data)


def build(input_path, output_dir):
    source_bytes=Path(input_path).read_bytes()
    source=json.loads(source_bytes.decode("utf-8-sig"))
    result=generate(source)
    result["source_sha256"]=hashlib.sha256(source_bytes).hexdigest()
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    result_file=out/"massing_result.json"
    result_file.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"massing_viewer.html").write_text(viewer_html(result),encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--out-dir",required=True)
    a=p.parse_args()
    try:
        r=build(a.input,a.out_dir)
        out={"status":"PASS_GEOMETRY_ONLY","project_id":r["project_id"],
              "strategies":[{ "name":o["strategy"],"kpi":o["kpi"]} for o in r["options"]],
              "legal_feasibility_authorized":False}
        if "spatial_program" in r:
            out["spatial_program"]={"label":PROGRAM_LABEL,"ranking":r["spatial_program"]["ranking"],
                "tradeoff":"greedy+bounded local search, whole spaces per level, no room geometry, no legal claim"
                    if "room_geometry_mode" not in r["spatial_program"] else
                    "greedy+bounded local search; geometrical-draft 2D room partition, no opening/egress, no legal claim"}
        print(json.dumps(out,ensure_ascii=False))
        return 0
    except (MassingHold,ValueError) as e:
        print(json.dumps({"status":"HOLD","failure":str(e)},ensure_ascii=False))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
