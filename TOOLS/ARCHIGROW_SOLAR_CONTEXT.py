#!/usr/bin/env python3
"""ArchiGrow SOLAR_STUDY: deterministic neighbourhood shadow / direct-sun exposure study.

Inputs : verified-or-declared lat/lon + scene frame, massing alternatives (ARCHIGROW_MASSING result),
         context obstacles (ARCHIGROW_BUILDING_CONTEXT output or declared fixture), receiver definitions.
Engine : pvlib (NREL SPA) solar position in Asia/Seoul civil time (or local apparent solar time); exact prism /
         stacked-slab shadow sweeps with Shapely evaluated per receiver height; no sampling of the sun disc.
Outputs: JSON report with provenance + standalone interactive HTML viewer (no network, no external script).

CLAIM BOUNDARY (kept in every output):
  * "direct sun exposure" = geometric line-of-sight to the sun centre. It is NOT meteorological sunshine
    (KMA ASOS actual sunshine hours), NOT irradiance, and NOT a statutory sunlight test
    (Building Act Enforcement Decree Art. 86 is project/ordinance specific; no auto-approval from shadow hours).
  * Missing / zero / invalid heights are UNKNOWN, never zero. Receivers touched by them report MIN/MAX bounds.
  * Terrain is flat unless per-obstacle ground elevation is supplied; NGII DEM / KMA are contracts, not connected.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "ARCHIGROW_SOLAR_CONTEXT/2026-10-18.1"
SCHEMA_INPUT = "ARCHIGROW_SOLAR_STUDY_INPUT_V1"
SCHEMA_REPORT = "ARCHIGROW_SOLAR_STUDY_REPORT_V1"
DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
LOCATION_VERIFICATIONS = ("DERIVED_FROM_PROJECTED_PARCEL_FRAME", "SYNTHETIC_DECLARED", "USER_DECLARED_UNVERIFIED")
DEFAULT_WINDOWS = [{"id": "W0900_1500", "start": "09:00", "end": "15:00"},
                   {"id": "W0900_1700", "start": "09:00", "end": "17:00"}]
DEFAULT_INDICATORS = [
    {"id": "IND_CONT_120_W0900_1500", "window_id": "W0900_1500", "metric": "longest_continuous_min", "threshold_min": 120},
    {"id": "IND_TOTAL_240_W0900_1700", "window_id": "W0900_1700", "metric": "total_min", "threshold_min": 240}]
FUTURE_ADAPTERS = [
    {"id": "KMA_ASOS_SUNSHINE", "status": "NOT_CONNECTED",
     "source": "https://apihub.kma.go.kr/specialApiList.do",
     "purpose": "observed meteorological sunshine duration by station/date (climatic reduction, never geometric access)",
     "contract": {"inputs": ["station_id", "date_range", "host-held free service key"],
                  "expected_outputs_UNVERIFIED": ["station_id", "date", "sunshine_hours"],
                  "joins_to": "report.dates[*].id via calendar date; reported next to, never merged into, direct-sun minutes"}},
    {"id": "NGII_DEM", "status": "NOT_CONNECTED",
     "source": "https://www.data.go.kr/data/15059920/fileData.do",
     "purpose": "ground elevation per obstacle/receiver/proposal base (replaces flat-terrain assumption)",
     "contract": {"inputs": ["raster file with declared CRS + vintage + SHA-256", "obstacle footprints"],
                  "outputs": ["ground_elevation_m per obstacle id (already consumed by this engine)"],
                  "status_when_missing": "FLAT_TERRAIN_ASSUMED flag stays in report"}},
    {"id": "KR_ZONING_WFS", "status": "NOT_CONNECTED", "source": "https://www.data.go.kr/data/15123895/openapi.do",
     "purpose": "zoning / adjacent-parcel overlay for sourced setback and use-zone context"},
    {"id": "KR_BUILDING_ENFORCEMENT_DECREE_ART86", "status": "NOT_EVALUATED",
     "source": "https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1022720617",
     "purpose": "legal sunlight height limits are project/ordinance specific; informational thresholds in this "
                "report are NOT a legal test and never imply compliance"}]


class SolarHold(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = str(detail)[:300]


def _need():
    try:
        import numpy, pandas, pvlib, shapely, pyproj  # noqa: F401
    except ImportError as exc:
        raise SolarHold("FREE_GEO_DEPENDENCY_REQUIRED", str(exc))
    import numpy as np, pandas as pd, pvlib
    import shapely
    from shapely.geometry import Polygon, Point, box
    from shapely.affinity import translate
    from shapely.ops import unary_union
    return np, pd, pvlib, shapely, Polygon, Point, box, translate, unary_union


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(Path(p).read_bytes())


def hhmm(s):
    try:
        h, m = str(s).split(":")
        v = int(h) * 60 + int(m)
    except ValueError:
        raise SolarHold("TIME_FORMAT_INVALID", s)
    if not 0 <= v <= 24 * 60:
        raise SolarHold("TIME_FORMAT_INVALID", s)
    return v


# ------------------------------------------------------------------ frame / location
def build_frame(cfg, massing, context):
    """Scene frame: lat/lon, east/north unit vectors in scene coordinates, honest verification label."""
    np, pd, pvlib, shapely, Polygon, *_ = _need()
    cf = (massing or {}).get("coordinate_frame") or {}
    crs = cf.get("projected_crs")
    origin = cf.get("projected_origin_m") or cf.get("local_origin_projected_m")
    cscene = (context or {}).get("scene") or {}
    site = (massing or {}).get("site_polygon") or []
    cx, cy = (Polygon(site).centroid.x, Polygon(site).centroid.y) if site else (0.0, 0.0)
    loc = cfg.get("location") or {}
    if crs in ("EPSG:5186", "EPSG:5179") and origin:
        if cscene.get("projected_crs") and (cscene.get("projected_crs") != crs or
                                            any(abs(a - b) > 1e-6 for a, b in zip(cscene.get("origin_m", [0, 0]), origin))):
            raise SolarHold("SCENE_FRAME_MISMATCH", "context scene differs from massing coordinate frame")
        from pyproj import Transformer
        inv = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        fwd = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        lon, lat = inv.transform(origin[0] + cx, origin[1] + cy)
        e = fwd.transform(lon + 1e-5, lat)
        n = fwd.transform(lon, lat + 1e-5)
        ev = np.array([e[0] - (origin[0] + cx), e[1] - (origin[1] + cy)])
        nv = np.array([n[0] - (origin[0] + cx), n[1] - (origin[1] + cy)])
        ev, nv = ev / np.linalg.norm(ev), nv / np.linalg.norm(nv)
        verification = ("DERIVED_FROM_PROJECTED_PARCEL_FRAME" if (massing or {}).get("site_area_basis")
                        else "PROJECTED_FRAME_DECLARED_NOT_SOURCE_BOUND")
        if loc.get("lat") is not None and abs(float(loc["lat"]) - lat) + abs(float(loc["lon"]) - lon) > 0.002:
            raise SolarHold("LOCATION_FRAME_CONFLICT", "declared lat/lon differs from parcel frame by >~200 m")
        kind = crs
    else:
        if cscene.get("projected_crs"):
            raise SolarHold("SCENE_FRAME_MISMATCH", "context is georeferenced but massing frame is local")
        for k in ("lat", "lon", "verification"):
            if loc.get(k) in (None, ""):
                raise SolarHold("LOCATION_REQUIRED", k)
        if loc["verification"] not in LOCATION_VERIFICATIONS:
            raise SolarHold("LOCATION_VERIFICATION_LABEL_INVALID", loc["verification"])
        lat, lon, verification = float(loc["lat"]), float(loc["lon"]), loc["verification"]
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise SolarHold("LOCATION_OUT_OF_RANGE")
        ax = (cfg.get("scene") or {}).get("y_axis_true_azimuth_deg")
        if ax is None:
            raise SolarHold("SCENE_NORTH_REQUIRED", "scene.y_axis_true_azimuth_deg must be declared for local axes")
        a = math.radians(float(ax))
        nv, ev = np.array([-math.sin(a), math.cos(a)]), np.array([math.cos(a), math.sin(a)])
        kind = "LOCAL_M"
    return {"lat": float(lat), "lon": float(lon), "kind": kind, "origin_m": origin,
            "east": [float(ev[0]), float(ev[1])], "north": [float(nv[0]), float(nv[1])],
            "location_verification": verification,
            "scene_y_axis_true_azimuth_deg": round(math.degrees(math.atan2(-nv[0], nv[1])) % 360, 6)}


def sun_steps(frame, date_str, tz, basis, start_min, end_min, step, min_elev):
    np, pd, pvlib, *_ = _need()
    base = pd.Timestamp(date_str).tz_localize(tz)
    std = base.utcoffset().total_seconds() / 3600.0 * 15.0
    lat, lon = frame["lat"], frame["lon"]
    noon = pd.DatetimeIndex([base + pd.Timedelta(hours=12)])
    eot = float(pvlib.solarposition.get_solarposition(noon, lat, lon, method="nrel_numpy")["equation_of_time"].iloc[0])
    delta = 4.0 * (lon - std) + eot if basis == "LOCAL_APPARENT_SOLAR" else 0.0
    n = int(math.ceil((end_min - start_min) / step))
    mins = [start_min + k * step for k in range(n)]
    times = pd.DatetimeIndex([base + pd.Timedelta(minutes=m - delta) for m in mins])
    sp = pvlib.solarposition.get_solarposition(times, lat, lon, altitude=0.0, method="nrel_numpy")
    ev, nv = frame["east"], frame["north"]
    steps = []
    for k, m in enumerate(mins):
        az, el = float(sp["azimuth"].iloc[k]), float(sp["elevation"].iloc[k])
        a = math.radians(az)
        h = (math.sin(a) * ev[0] + math.cos(a) * nv[0], math.sin(a) * ev[1] + math.cos(a) * nv[1])
        steps.append({"k": k, "minute": m, "label": "%02d:%02d" % (m // 60, m % 60), "civil_time": times[k].isoformat(),
                      "azimuth_deg": round(az, 3), "elevation_deg": round(el, 3),
                      "apparent_elevation_deg": round(float(sp["apparent_elevation"].iloc[k]), 3),
                      "up": bool(el >= min_elev), "h": h, "tan": math.tan(math.radians(max(el, 0.01)))})
    return steps, {"equation_of_time_min": round(eot, 3), "standard_meridian_deg": std,
                   "solar_minus_civil_offset_min": round(delta, 3) if basis == "LOCAL_APPARENT_SOLAR" else 0.0,
                   "longitude_correction_min": round(4.0 * (lon - std), 3)}


# ------------------------------------------------------------------ shadow geometry
def _sweep(poly, v0, v1, translate, Polygon):
    parts = [translate(poly, v0[0], v0[1])]
    if v0 == v1:
        return parts
    parts.append(translate(poly, v1[0], v1[1]))
    ring = list(poly.exterior.coords)
    for (ax, ay), (bx, by) in zip(ring[:-1], ring[1:]):
        q = Polygon([(ax + v0[0], ay + v0[1]), (bx + v0[0], by + v0[1]), (bx + v1[0], by + v1[1]), (ax + v1[0], ay + v1[1])])
        if q.area > 1e-9:
            parts.append(q)
    return parts


class Shadow:
    """Exact shadow of vertical slabs on a horizontal plane at height zr (Minkowski sweep of each slab)."""

    def __init__(self, reach_m):
        _, _, _, self.shapely, self.Polygon, self.Point, self.box, self.translate, self.union = _need()
        self.reach = reach_m
        self.truncated = 0

    def parts(self, slabs, step, zr):
        out = []
        s, tan = step["h"], step["tan"]
        for poly, z0, z1 in slabs:
            if z1 <= zr:
                continue
            t0 = max(0.0, z0 - zr) / tan
            t1 = (math.inf if math.isinf(z1) else (z1 - zr) / tan)
            if t1 > self.reach:
                t1 = self.reach
                self.truncated += 1
            t0 = min(t0, self.reach)
            if t1 < t0:
                continue
            if t1 == t0 and z1 > z0:
                t1 = t0 + 1e-6
            out += _sweep(poly, (-s[0] * t0, -s[1] * t0), (-s[0] * t1, -s[1] * t1), self.translate, self.Polygon)
        return out

    def union_of(self, slabs, step, zr):
        p = self.parts(slabs, step, zr)
        return self.union(p) if p else self.Polygon()


def longest_run(row):
    best = cur = 0
    for v in row:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def rings_of(geom, clip=None):
    if geom is None or geom.is_empty:
        return []
    if clip is not None:
        geom = geom.intersection(clip)
    polys = [geom] if geom.geom_type == "Polygon" else [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]
    out = []
    for p in polys:
        if p.area < 0.05:
            continue
        p = p.simplify(0.05)
        for r in [p.exterior] + list(p.interiors):
            out.append([round(c, 1) for xy in list(r.coords)[:-1] for c in xy])
    return out


# ------------------------------------------------------------------ model assembly
def load_proposals(massing, only):
    np, pd, pvlib, shapely, Polygon, *_ = _need()
    alts = []
    for o in massing.get("options") or []:
        if only and o["strategy"] not in only:
            continue
        slabs, fps = [], []
        for f in o["floors"]:
            p = Polygon(f["polygon"])
            if not p.is_valid or p.area <= 0:
                raise SolarHold("PROPOSAL_FLOOR_POLYGON_INVALID", f.get("level"))
            slabs.append((p, float(f["elevation_m"]), float(f["elevation_m"]) + float(f["height_m"])))
            fps.append(p)
        if not slabs:
            raise SolarHold("PROPOSAL_HAS_NO_FLOORS", o["strategy"])
        alts.append({"id": o["strategy"], "slabs": slabs, "kpi": o["kpi"], "floors": o["floors"],
                     "footprint": shapely.union_all(fps)})
    if not alts:
        raise SolarHold("NO_MASSING_ALTERNATIVES")
    return alts


def prepare_context(ctx_doc, demolition_ids, proposals, site, ground_default=0.0):
    np, pd, pvlib, shapely, Polygon, *_ = _need()
    rows, demolished, issues = [], [], []
    for o in (ctx_doc or {}).get("obstacles", []):
        poly = Polygon(o["footprint_m"])
        if not poly.is_valid or poly.area <= 0:
            issues.append({"id": o["id"], "issue": "CONTEXT_FOOTPRINT_INVALID"})
            continue
        if o["id"] in demolition_ids:
            demolished.append(o["id"])
            continue
        for a in proposals:
            if poly.intersection(a["footprint"]).area > 1.0:
                raise SolarHold("CONTEXT_OVERLAPS_PROPOSAL", f"{o['id']} vs {a['id']}: add id to demolition_assumed_ids only as a design decision")
        h = o.get("height_m")
        valid = isinstance(h, (int, float)) and not isinstance(h, bool) and math.isfinite(h) and h > 0
        row = {"id": o["id"], "poly": poly, "ground": float(o.get("ground_elevation_m") or 0.0),
               "known": bool(valid), "name": o.get("name"),
               "height_source": o.get("height_source") if valid else "UNKNOWN",
               "confidence": o.get("confidence") if valid else "NONE",
               "h_nom": float(h) if valid else None,
               "h_min": float(o.get("height_min_m") if valid and o.get("height_min_m") else h) if valid else None,
               "h_max": float(o.get("height_max_m") if valid and o.get("height_max_m") else h) if valid else None,
               "issues": list(o.get("issues") or []), "footprint": o["footprint_m"]}
        if valid and not (row["h_min"] <= row["h_nom"] <= row["h_max"]):
            raise SolarHold("CONTEXT_HEIGHT_RANGE_INCONSISTENT", o["id"])
        rows.append(row)
    return rows, demolished, issues


def ctx_slabs(rows, run):
    out, unk = [], []
    for r in rows:
        if r["known"]:
            h = {"NOM": r["h_nom"], "MIN": r["h_max"], "MAX": r["h_min"]}[run]  # MIN-sun run uses tallest neighbours
            out.append((r["poly"], r["ground"], r["ground"] + h))
        else:
            unk.append((r["poly"], r["ground"], math.inf))
    return out, unk


def gen_receivers(spec, rows, frame, site_ground):
    np, pd, pvlib, shapely, Polygon, Point, box, *_ = _need()
    from shapely.geometry.polygon import orient
    by_id = {r["id"]: r for r in rows}
    out = []
    for fs in (spec.get("facade_sets") or []):
        b = by_id.get(fs.get("building_id"))
        if b is None:
            raise SolarHold("RECEIVER_BUILDING_NOT_IN_CONTEXT", fs.get("building_id"))
        poly = orient(b["poly"], 1.0)
        spacing = float(fs.get("spacing_m", 4.0))
        heights = [float(z) for z in fs.get("heights_above_ground_m", [1.5, 4.5, 7.5])]
        if b["known"]:
            heights = [z for z in heights if z < b["h_min"] - 0.3]
        flt = fs.get("facing_filter")
        ring = list(poly.exterior.coords)
        for ei, ((ax, ay), (bx, by)) in enumerate(zip(ring[:-1], ring[1:])):
            L = math.hypot(bx - ax, by - ay)
            if L < 1.0:
                continue
            n = (( by - ay) / L, -(bx - ax) / L)
            naz = math.degrees(math.atan2(n[0] * frame["east"][0] + n[1] * frame["east"][1],
                                          n[0] * frame["north"][0] + n[1] * frame["north"][1])) % 360
            if flt and abs((naz - flt["azimuth_deg"] + 180) % 360 - 180) > flt.get("tolerance_deg", 75):
                continue
            m = max(1, int(round(L / spacing)))
            for k in range(m):
                t = (k + 0.5) / m
                x, y = ax + (bx - ax) * t + n[0] * 0.1, ay + (by - ay) * t + n[1] * 0.1
                for zi, z in enumerate(heights):
                    out.append({"id": f"RCV-{b['id']}-E{ei}-S{k}-Z{zi}", "set": fs["id"], "building": b["id"], "kind": "FACADE",
                                "x": round(x, 4), "y": round(y, 4), "z": b["ground"] + z, "height_above_ground_m": z,
                                "normal": [n[0], n[1]], "facing_true_azimuth_deg": round(naz, 2)})
    for p in (spec.get("points") or []):
        nz = None
        if p.get("facing_true_azimuth_deg") is not None:
            a = math.radians(float(p["facing_true_azimuth_deg"]))
            nz = [math.sin(a) * frame["east"][0] + math.cos(a) * frame["north"][0],
                  math.sin(a) * frame["east"][1] + math.cos(a) * frame["north"][1]]
        out.append({"id": "RCV-" + p["id"], "set": p.get("set", "POINTS"), "building": p.get("building"), "kind": "POINT",
                    "x": float(p["x"]), "y": float(p["y"]), "z": site_ground + float(p.get("z_above_ground_m", 1.5)),
                    "height_above_ground_m": float(p.get("z_above_ground_m", 1.5)), "normal": nz,
                    "facing_true_azimuth_deg": p.get("facing_true_azimuth_deg"), "label": p.get("label")})
    for g in (spec.get("grids") or []):
        poly = Polygon(g["polygon_m"])
        sp = float(g.get("spacing_m", 5.0))
        x0, y0, x1, y1 = poly.bounds
        i = 0
        y = y0 + sp / 2
        while y < y1:
            x = x0 + sp / 2
            while x < x1:
                if poly.contains(Point(x, y)):
                    out.append({"id": f"RCV-{g['id']}-G{i}", "set": g["id"], "building": None, "kind": "GRID",
                                "x": round(x, 4), "y": round(y, 4), "z": site_ground + float(g.get("z_above_ground_m", 0.0)),
                                "height_above_ground_m": float(g.get("z_above_ground_m", 0.0)), "normal": None,
                                "facing_true_azimuth_deg": None})
                    i += 1
                x += sp
            y += sp
    ids = [r["id"] for r in out]
    if len(set(ids)) != len(ids):
        raise SolarHold("RECEIVER_IDS_NOT_UNIQUE")
    if not out:
        raise SolarHold("NO_RECEIVERS_DEFINED")
    return out


# ------------------------------------------------------------------ core evaluation
def evaluate_date(date_spec, frame, rows, alts, receivers, tparams, windows, grid, shadow, clip, want_frames=True):
    np, pd, pvlib, shapely, Polygon, Point, box, translate, unary_union = _need()
    start_min = min(hhmm(w["start"]) for w in windows)
    end_min = max(hhmm(w["end"]) for w in windows)
    step = tparams["step_minutes"]
    steps, timeinfo = sun_steps(frame, date_spec["date"], tparams["tz"], tparams["basis"], start_min, end_min, step, tparams["min_sun_elevation_deg"])
    K, R = len(steps), len(receivers)
    wmask = {w["id"]: np.array([hhmm(w["start"]) <= s["minute"] < hhmm(w["end"]) for s in steps]) for w in windows}
    X = np.array([r["x"] for r in receivers]); Y = np.array([r["y"] for r in receivers]); Z = np.array([r["z"] for r in receivers])
    NRM = np.array([r["normal"] if r["normal"] else [0.0, 0.0] for r in receivers])
    HASN = np.array([r["normal"] is not None for r in receivers])
    zs = sorted(set(round(float(z), 3) for z in Z))
    zidx = {z: np.where(np.abs(Z - z) < 5e-4)[0] for z in zs}
    runs = ["NOM"] + (["MIN", "MAX"] if any(r["known"] and (r["h_min"] != r["h_nom"] or r["h_max"] != r["h_nom"]) for r in rows) else [])
    slabs = {run: ctx_slabs(rows, run) for run in ["NOM", "MIN", "MAX"]}
    scen = ["BASE"] + [a["id"] for a in alts]
    LIT = {run: {s: np.zeros((R, K), bool) for s in scen} for run in ["NOM", "MIN", "MAX"]}
    UNK = np.zeros((R, K), bool)
    POT = np.zeros((R, K), bool)
    # solids: receivers inside a footprint below its roof are excluded (not "lit")
    SOLID = np.zeros(R, bool)
    for r in rows:
        if r["known"]:
            inside = shapely.contains_xy(r["poly"], X, Y) & (Z < r["ground"] + r["h_nom"])
        else:
            inside = shapely.contains_xy(r["poly"], X, Y)
        SOLID |= inside
    for a in alts:
        for poly, z0, z1 in a["slabs"]:
            SOLID |= shapely.contains_xy(poly, X, Y) & (Z >= z0) & (Z < z1)
    frames = []
    directional = {a["id"]: {"minutes": {d: 0 for d in DIRECTIONS}, "max_reach_m": 0.0, "shadow_steps": 0} for a in alts}
    gx = gy = None
    GRID = {}
    if grid:
        gx, gy = grid["xs"], grid["ys"]
        GRID = {s: {"lit": np.zeros(len(gx), int), "unc": np.zeros(len(gx), bool)} for s in scen}
    gmask = wmask[grid["window_id"]] if grid else None
    ground_z = min(a["slabs"][0][1] for a in alts)  # proposal base plane (flat site)
    unknown_slabs = slabs["NOM"][1]
    for k, st in enumerate(steps):
        frame_rec = None
        if not st["up"]:
            if want_frames:
                frames.append({"ctx": [], "prop": {a["id"]: [] for a in alts}})
            continue
        h = np.array(st["h"])
        facing = np.where(HASN, NRM @ h > 1e-6, True)
        POT[:, k] = facing & ~SOLID
        ctx_rings, prop_rings = [], {}
        for z in zs:
            idx = zidx[z]
            xs, ys = X[idx], Y[idx]
            u_unk = shadow.union_of(unknown_slabs, st, z) if unknown_slabs else None
            if u_unk is not None:
                UNK[idx, k] = shapely.contains_xy(u_unk, xs, ys)
            c = {run: (shadow.union_of(slabs[run][0], st, z) if run in runs else None) for run in ["NOM", "MIN", "MAX"]}
            if "MIN" not in runs:
                c["MIN"] = c["MAX"] = c["NOM"]
            inc = {run: shapely.contains_xy(c[run], xs, ys) for run in c}
            props = {a["id"]: shadow.union_of(a["slabs"], st, z) for a in alts}
            inp = {a["id"]: shapely.contains_xy(props[a["id"]], xs, ys) for a in alts}
            base_ok = facing[idx] & ~SOLID[idx]
            for run in ["NOM", "MIN", "MAX"]:
                LIT[run]["BASE"][idx, k] = base_ok & ~inc[run]
                for a in alts:
                    LIT[run][a["id"]][idx, k] = base_ok & ~inc[run] & ~inp[a["id"]]
        # ground-plane geometry for viewer/directional/grid (z = proposal ground, flat)
        zg = ground_z
        cg = shadow.union_of(slabs["NOM"][0], st, zg)
        if want_frames:
            ctx_rings = rings_of(cg, clip)
        ug = shadow.union_of(unknown_slabs, st, zg) if unknown_slabs else None
        for a in alts:
            pg = shadow.union_of(a["slabs"], st, zg)
            if want_frames:
                prop_rings[a["id"]] = rings_of(pg, clip)
            sh = pg.difference(a["footprint"])
            if not sh.is_empty and sh.area > 0.5:
                c0 = a["footprint"].centroid
                cc = sh.centroid
                dx, dy = cc.x - c0.x, cc.y - c0.y
                az = math.degrees(math.atan2(dx * frame["east"][0] + dy * frame["east"][1],
                                             dx * frame["north"][0] + dy * frame["north"][1])) % 360
                sec = DIRECTIONS[int(((az + 22.5) % 360) // 45)]
                directional[a["id"]]["minutes"][sec] += step
                directional[a["id"]]["shadow_steps"] += 1
                reach = max(a["footprint"].distance(Point(x, y)) for g in ([sh] if sh.geom_type == "Polygon" else sh.geoms)
                            if g.geom_type == "Polygon" for x, y in g.exterior.coords)
                directional[a["id"]]["max_reach_m"] = max(directional[a["id"]]["max_reach_m"], reach)
        if want_frames:
            frames.append({"ctx": ctx_rings, "prop": prop_rings})
        if grid and gmask[k]:
            gin = shapely.contains_xy(cg, gx, gy)
            gun = shapely.contains_xy(ug, gx, gy) if ug is not None else np.zeros(len(gx), bool)
            for s in scen:
                inpr = np.zeros(len(gx), bool) if s == "BASE" else shapely.contains_xy(shadow.union_of(
                    next(a for a in alts if a["id"] == s)["slabs"], st, zg), gx, gy)
                lit = ~gin & ~inpr & grid["open"]
                GRID[s]["lit"] += (lit & ~gun).astype(int) * step
                GRID[s]["unc"] |= lit & gun
    # ---- aggregate
    res = {"steps": [{k: v for k, v in s.items() if k not in ("h", "tan")} for s in steps], "time_info": timeinfo,
           "windows": {w["id"]: int(wmask[w["id"]].sum() * step) for w in windows}, "scenarios": {}}
    for sc in scen:
        recs = {}
        for i, r in enumerate(receivers):
            if SOLID[i]:
                recs[r["id"]] = {"state": "INSIDE_SOLID_EXCLUDED"}
                continue
            def met(lit_row):
                return {w["id"]: {"total_min": int(lit_row[wmask[w["id"]]].sum() * step),
                                  "longest_min": int(longest_run(lit_row[wmask[w["id"]]]) * step)} for w in windows}
            nom_lit = LIT["NOM"][sc][i]
            unk_hits = int((nom_lit & UNK[i]).sum())
            blocked_min = LIT["MIN"][sc][i] & ~UNK[i]
            valid = unk_hits == 0
            bits = "".join("-" if not POT[i, k] else ("x" if (nom_lit[k] and UNK[i, k]) else ("1" if nom_lit[k] else "0")) for k in range(K))
            recs[r["id"]] = {"state": "EVALUATED", "nominal_valid": valid,
                             "nominal": met(nom_lit & ~UNK[i]) if valid else None,
                             "bound_min": met(blocked_min), "bound_max": met(LIT["MAX"][sc][i]),
                             "potential": {w["id"]: int(POT[i][wmask[w["id"]]].sum() * step) for w in windows},
                             "unknown_height_affected_steps": unk_hits, "lit_bits": bits}
        res["scenarios"][sc] = recs
    if grid:
        res["grid"] = {s: {"minutes": GRID[s]["lit"].tolist(), "uncertain": GRID[s]["unc"].astype(int).tolist()} for s in scen}
    res["directional_shadow"] = directional
    return res, frames, POT, SOLID


# ------------------------------------------------------------------ indicators
def geometry_indicators(massing, alts, site_poly, rows):
    np, pd, pvlib, shapely, Polygon, *_ = _need()
    kpi_src = (massing.get("site_area_basis") or {})
    out = {}
    for a in alts:
        k = a["kpi"]
        gfa = sum(p.area for p, _, _ in a["slabs"])
        fp = a["slabs"][0][0].area
        site_area = k["site_area_m2"]
        sep = min((a["footprint"].distance(r["poly"]) for r in rows), default=None)
        clearance = a["footprint"].distance(site_poly.exterior)
        floors = len(a["floors"])
        ftf = {round(f["height_m"], 6) for f in a["floors"]}
        top = a["slabs"][-1][2]
        out[a["id"]] = {
            "site_area_official_or_declared_m2": site_area, "site_area_source": k.get("site_area_source"),
            "site_polygon_area_m2": round(site_poly.area, 4),
            "official_vs_polygon_delta_m2": round(site_area - site_poly.area, 4),
            "official_vs_polygon_status": "OFFICIAL_AREA_BOUND" if kpi_src else "GEOMETRY_ONLY_NO_OFFICIAL_AREA",
            "gfa_m2": round(gfa, 4), "footprint_m2": round(fp, 4), "bcr_pct": round(fp / site_area * 100, 4),
            "far_pct": round(gfa / site_area * 100, 4), "story_count": floors,
            "floor_to_floor_m": sorted(ftf), "max_height_m": round(top, 4),
            "kpi_recomputed_matches_reported": bool(abs(gfa - k["gross_floor_area_m2"]) < 0.01 and abs(fp - k["footprint_area_m2"]) < 0.01
                                                   and abs(top - k["max_height_m"]) < 1e-6),
            "min_clearance_to_site_boundary_m": round(clearance, 3),
            "clearance_status": "GEOMETRIC_ONLY_NOT_STATUTORY_SETBACK", "statutory_setback_m": None,
            "statutory_setback_status": "NOT_SOURCED",
            "min_separation_to_context_footprint_m": None if sep is None else round(sep, 3)}
    return out


def evaluate_indicators(spec, res, receivers, scenarios):
    out = {}
    for sc in scenarios:
        cnt = {i["id"]: {"PASS_ALL_BOUNDS": 0, "FAIL_ALL_BOUNDS": 0, "INDETERMINATE": 0} for i in spec}
        for r in receivers:
            rec = res["scenarios"][sc].get(r["id"])
            if not rec or rec.get("state") != "EVALUATED":
                continue
            for ind in spec:
                lo = rec["bound_min"][ind["window_id"]][_m(ind["metric"])]
                hi = rec["bound_max"][ind["window_id"]][_m(ind["metric"])]
                if rec["nominal_valid"]:
                    nv = rec["nominal"][ind["window_id"]][_m(ind["metric"])]
                    lo, hi = min(lo, nv), max(hi, nv)
                cls = "PASS_ALL_BOUNDS" if lo >= ind["threshold_min"] else ("FAIL_ALL_BOUNDS" if hi < ind["threshold_min"] else "INDETERMINATE")
                cnt[ind["id"]][cls] += 1
        out[sc] = cnt
    return out


def _m(metric):
    return {"longest_continuous_min": "longest_min", "total_min": "total_min"}[metric]


# ------------------------------------------------------------------ run
def make_grid(cfg_grid, alts, rows, receivers, site_poly, shadow):
    np, pd, pvlib, shapely, Polygon, Point, box, *_ = _need()
    g = cfg_grid or {}
    geoms = [site_poly] + [r["poly"] for r in rows] + [a["footprint"] for a in alts]
    x0, y0, x1, y1 = shapely.union_all(geoms).bounds
    m = float(g.get("margin_m", 12.0))
    x0, y0, x1, y1 = x0 - m, y0 - m, x1 + m, y1 + m
    sp = float(g.get("spacing_m", 3.0))
    sp = max(sp, math.sqrt((x1 - x0) * (y1 - y0) / 12000.0))
    nx, ny = int((x1 - x0) // sp) + 1, int((y1 - y0) // sp) + 1
    xs = np.array([x0 + (i + 0.5) * sp for j in range(ny) for i in range(nx)])
    ys = np.array([y0 + (j + 0.5) * sp for j in range(ny) for i in range(nx)])
    solid = np.zeros(len(xs), bool)
    for r in rows:
        solid |= shapely.contains_xy(r["poly"], xs, ys)
    for a in alts:
        solid |= shapely.contains_xy(a["footprint"], xs, ys)
    return {"xs": xs, "ys": ys, "open": ~solid, "x0": x0, "y0": y0, "sp": sp, "nx": nx, "ny": ny, "window_id": g.get("window_id")}


def run_study(cfg, massing, context, *, input_paths=None, out_dir=None):
    np, pd, pvlib, shapely, Polygon, Point, box, translate, unary_union = _need()
    if cfg.get("schema") != SCHEMA_INPUT:
        raise SolarHold("SCHEMA_UNSUPPORTED")
    pid = str(cfg.get("project_id") or "").strip()
    if not pid:
        raise SolarHold("PROJECT_ID_REQUIRED")
    for label, d in (("massing", massing), ("context", context)):
        if d and d.get("project_id") not in (None, pid):
            raise SolarHold("PROJECT_ID_MISMATCH", f"{label}:{d.get('project_id')}")
    tcfg = cfg.get("time") or {}
    tp = {"tz": tcfg.get("tz", "Asia/Seoul"), "basis": tcfg.get("basis", "CIVIL_KST"),
          "step_minutes": int(tcfg.get("step_minutes", 10)), "min_sun_elevation_deg": float(tcfg.get("min_sun_elevation_deg", 3.0)),
          "max_reach_m": float(tcfg.get("max_reach_m", 400.0))}
    if tp["basis"] not in ("CIVIL_KST", "LOCAL_APPARENT_SOLAR"):
        raise SolarHold("TIME_BASIS_UNSUPPORTED", tp["basis"])
    if not 1 <= tp["step_minutes"] <= 30:
        raise SolarHold("STEP_MINUTES_OUT_OF_RANGE")
    windows = tcfg.get("windows") or DEFAULT_WINDOWS
    dates = tcfg.get("dates") or []
    if not dates:
        raise SolarHold("DATES_REQUIRED")
    frame = build_frame(cfg, massing, context)
    site_local = massing["site_polygon"]
    site_poly = Polygon(site_local)
    alts = load_proposals(massing, (cfg.get("proposal") or {}).get("alternatives"))
    p_ground = float((cfg.get("proposal") or {}).get("ground_elevation_m", 0.0))
    if p_ground:
        for a in alts:
            a["slabs"] = [(p, z0 + p_ground, z1 + p_ground) for p, z0, z1 in a["slabs"]]
    rows, demolished, ctx_issues = prepare_context(context, set(cfg.get("demolition_assumed_ids") or []), alts, site_poly)
    receivers = gen_receivers(cfg.get("receivers") or {}, rows, frame, p_ground)
    shadow = Shadow(tp["max_reach_m"])
    allg = shapely.union_all([site_poly] + [r["poly"] for r in rows] + [a["footprint"] for a in alts])
    bx0, by0, bx1, by1 = allg.bounds
    mg = float(cfg.get("view_margin_m", 25.0))
    clip = box(bx0 - mg, by0 - mg, bx1 + mg, by1 + mg)
    grid = make_grid(cfg.get("ground_grid") or {"window_id": windows[0]["id"]}, alts, rows, receivers, site_poly, shadow) \
        if cfg.get("ground_grid", {}) is not None else None
    if grid and not grid["window_id"]:
        grid["window_id"] = windows[0]["id"]
    date_results, all_frames = {}, {}
    scen = ["BASE"] + [a["id"] for a in alts]
    for d in dates:
        res, frames, POT, SOLID = evaluate_date(d, frame, rows, alts, receivers, tp, windows, grid, shadow, clip)
        date_results[d["id"]] = {"date": d["date"], **res}
        all_frames[d["id"]] = frames
    wids = {w["id"] for w in windows}
    if cfg.get("indicators"):
        bad = [i["id"] for i in cfg["indicators"] if i.get("window_id") not in wids]
        if bad:
            raise SolarHold("INDICATOR_WINDOW_UNKNOWN", ",".join(bad))
        spec = cfg["indicators"]
    else:
        spec = [i for i in DEFAULT_INDICATORS if i["window_id"] in wids]
    # indicators + impact per date
    impact = {}
    for did, dr in date_results.items():
        ind = evaluate_indicators(spec, dr, receivers, scen)
        loss = {}
        for a in alts:
            per, byb = {}, {}
            for r in receivers:
                b, s = dr["scenarios"]["BASE"][r["id"]], dr["scenarios"][a["id"]][r["id"]]
                if b.get("state") != "EVALUATED":
                    continue
                row = {}
                for w in windows:
                    wid = w["id"]
                    lo = b["bound_min"][wid]["total_min"] - s["bound_min"][wid]["total_min"]
                    hi = b["bound_max"][wid]["total_min"] - s["bound_max"][wid]["total_min"]
                    nom = (b["nominal"][wid]["total_min"] - s["nominal"][wid]["total_min"]) if (b["nominal_valid"] and s["nominal_valid"]) else None
                    row[wid] = {"loss_total_nominal_min": nom, "loss_total_min_run": lo, "loss_total_max_run": hi}
                per[r["id"]] = row
                key = r["building"] or r["set"]
                byb.setdefault(key, []).append((r["id"], row))
            summ = {}
            for key, lst in byb.items():
                summ[key] = {"receiver_count": len(lst)}
                for w in windows:
                    vals = [x[1][w["id"]]["loss_total_nominal_min"] for x in lst if x[1][w["id"]]["loss_total_nominal_min"] is not None]
                    summ[key][w["id"]] = {"mean_loss_nominal_min": round(sum(vals) / len(vals), 2) if vals else None,
                                          "max_loss_nominal_min": max(vals) if vals else None,
                                          "receivers_with_loss": sum(1 for v in vals if v > 0), "nominal_valid_receivers": len(vals)}
            loss[a["id"]] = {"per_receiver": per, "by_building_or_set": summ}
        impact[did] = {"indicators": ind, "loss_vs_baseline": loss}
    affected = sorted({r["id"] for dr in date_results.values() for sc in scen for r in receivers
                       if dr["scenarios"][sc][r["id"]].get("unknown_height_affected_steps", 0) > 0})
    unknown_rows = [r["id"] for r in rows if not r["known"]]
    src_classes = sorted({str((context or {}).get("source_class", "UNDECLARED"))})
    synthetic = (any(("SYNTHETIC" in c or "FIXTURE" in c) for c in src_classes) or frame["location_verification"] == "SYNTHETIC_DECLARED"
                 or any(t in str(massing.get("input_source_role", "")).upper() for t in ("SYNTHETIC", "FIXTURE")))
    status = "LIMITED" if affected else "PASS"
    hold_reason = "CONTEXT_HEIGHT_UNKNOWN_LIMITED_RESULT" if affected else None
    ctx_comp = (context or {}).get("completeness") or {}
    report = {
        "schema": SCHEMA_REPORT, "project_id": pid, "generator": VERSION, "result_status": status, "hold_reason": hold_reason,
        "data_class": "SYNTHETIC_OR_FIXTURE_NOT_PUBLIC_DATA" if synthetic else "SOURCE_BOUND_PUBLIC_CONTEXT",
        "claims": {"legal_sunlight_compliance": "NOT_EVALUATED", "meteorological_sunshine": "NOT_CONNECTED_KMA_ASOS_CONTRACT_ONLY",
                   "irradiance_or_energy": "NOT_COMPUTED", "terrain_dem": "NOT_CONNECTED_NGII_CONTRACT_ONLY",
                   "metric_kind": "GEOMETRIC_DIRECT_SUN_EXPOSURE_LINE_OF_SIGHT",
                   "informational_thresholds_note": "indicator thresholds are user-set screening values, not Article 86 tests"},
        "location": {"lat": frame["lat"], "lon": frame["lon"], "verification": frame["location_verification"],
                     "frame_kind": frame["kind"], "scene_origin_m": frame["origin_m"],
                     "scene_y_axis_true_azimuth_deg": frame["scene_y_axis_true_azimuth_deg"],
                     "east_unit_in_scene": frame["east"], "north_unit_in_scene": frame["north"]},
        "time": {**tp, "windows": windows, "dates": dates, "sample_rule": "each sample at interval start represents step_minutes",
                 "library": {"pvlib": pvlib.__version__, "method": "nrel_numpy (NREL SPA)", "elevation_used": "geometric"}},
        "terrain": {"mode": "FLAT_TERRAIN_ASSUMED" if not any(r["ground"] for r in rows) and not p_ground else "PER_OBSTACLE_ELEVATION_INPUT",
                    "proposal_ground_elevation_m": p_ground},
        "context": {"source_classes": src_classes, "source_status": (context or {}).get("source_status"),
                    "obstacle_count": len(rows), "height_unknown_ids": unknown_rows, "demolition_assumed_ids": demolished,
                    "unknown_height_affected_receiver_count": len(affected), "unknown_height_affected_receivers": affected[:100],
                    "source_completeness": ctx_comp, "issues": ctx_issues,
                    "unknown_height_policy": "UNKNOWN_NEVER_ZERO; receivers report MIN/MAX bounds, nominal withheld when affected",
                    "obstacles": [{"id": r["id"], "name": r["name"], "footprint_m": r["footprint"], "height_m": r["h_nom"],
                                   "height_min_m": r["h_min"], "height_max_m": r["h_max"], "height_source": r["height_source"],
                                   "confidence": r["confidence"], "issues": r["issues"]} for r in rows]},
        "shadow_reach_cap": {"max_reach_m": tp["max_reach_m"], "truncated_slab_steps": shadow.truncated,
                             "note": "slab sweeps beyond the cap are truncated; unknown-height obstacles are swept to the cap"},
        "receivers": [{k: v for k, v in r.items() if k != "normal"} for r in receivers],
        "indicators_geometry": geometry_indicators(massing, alts, site_poly, rows),
        "dates": date_results, "impact": impact, "indicator_spec": spec,
        "ground_grid": ({"spacing_m": grid["sp"], "nx": grid["nx"], "ny": grid["ny"], "x0": grid["x0"], "y0": grid["y0"],
                         "window_id": grid["window_id"], "open_cells": int(grid["open"].sum())} if grid else None),
        "future_adapters": FUTURE_ADAPTERS, "adjacent_parcels": {"status": "READINESS_ONLY",
            "note": "ARCHIGROW_BUILDING_CONTEXT.fetch_layer supports LP_PA_CBND_BUBUN; not executed in this study"},
        "input_hashes": input_paths or {}, "limitations": [
            "Geometric line-of-sight only; no atmosphere, cloud, diffuse light or reflections.",
            "Context heights are source/assumption dependent; see context.obstacles[*].height_source/confidence.",
            "Courtyard holes and roof forms are ignored (prism footprints), flat terrain unless elevations supplied.",
            "Sun position uses geometric elevation with a minimum-elevation cut-off; below it receivers are 'no sun'.",
            "Not a statutory sunlight / Article 86 evaluation; ordinance and project use must be confirmed by a human reviewer."],
    }
    viewer = build_viewer_data(report, frame, rows, alts, receivers, date_results, all_frames, grid, site_local, windows)
    return report, viewer


# ------------------------------------------------------------------ viewer
def build_viewer_data(report, frame, rows, alts, receivers, date_results, all_frames, grid, site_local, windows):
    V = {"project_id": report["project_id"], "status": report["result_status"], "data_class": report["data_class"],
         "claims": report["claims"], "location": report["location"], "north": frame["north"], "east": frame["east"],
         "site": [[round(x, 2), round(y, 2)] for x, y in site_local], "windows": windows,
         "context": [{"id": r["id"], "ring": r["footprint"], "h": r["h_nom"], "hmin": r["h_min"], "hmax": r["h_max"],
                      "src": r["height_source"], "conf": r["confidence"], "unknown": not r["known"]} for r in rows],
         "alts": [{"id": a["id"], "kpi": report["indicators_geometry"][a["id"]],
                   "levels": [{"ring": [[round(c, 2) for c in xy] for xy in list(p.exterior.coords)[:-1]], "z0": round(z0, 2), "z1": round(z1, 2)}
                              for p, z0, z1 in a["slabs"]]} for a in alts],
         "receivers": [{"id": r["id"], "x": r["x"], "y": r["y"], "z": round(r["z"], 2), "b": r["building"] or r["set"], "kind": r["kind"]}
                       for r in receivers],
         "dates": [], "grid": None, "limitations": report["limitations"]}
    for did, dr in date_results.items():
        bits = {sc: [recs[r["id"]].get("lit_bits", "") if recs[r["id"]].get("state") == "EVALUATED" else "s" * len(dr["steps"]) for r in receivers]
                for sc, recs in dr["scenarios"].items()}
        summ = {}
        for sc, recs in dr["scenarios"].items():
            summ[sc] = []
            for r in receivers:
                x = recs[r["id"]]
                if x.get("state") != "EVALUATED":
                    summ[sc].append(None)
                    continue
                w0 = windows[0]["id"]
                summ[sc].append({"nom": x["nominal"][w0] if x["nominal_valid"] else None,
                                 "lo": x["bound_min"][w0], "hi": x["bound_max"][w0], "valid": x["nominal_valid"]})
        V["dates"].append({"id": did, "date": dr["date"], "steps": [{"label": s["label"], "az": s["azimuth_deg"], "el": s["elevation_deg"], "up": s["up"]} for s in dr["steps"]],
                           "ctx_shadow": [f["ctx"] for f in all_frames[did]], "prop_shadow": {a["id"]: [f["prop"].get(a["id"], []) for f in all_frames[did]] for a in alts},
                           "bits": bits, "summary": summ, "time_info": dr["time_info"],
                           "directional": dr["directional_shadow"],
                           "grid": dr.get("grid")})
    if grid:
        V["grid"] = {"x0": grid["x0"], "y0": grid["y0"], "sp": grid["sp"], "nx": grid["nx"], "ny": grid["ny"],
                     "open": grid["open"].astype(int).tolist(), "window_id": grid["window_id"]}
    return V


def viewer_html(V):
    data = json.dumps(V, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return VIEWER_TEMPLATE.replace("__DATA__", data)


VIEWER_TEMPLATE = r"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Archi Grow | Solar / Shadow Study</title><style>
:root{font:13px/1.45 system-ui,'Malgun Gothic',sans-serif;color:#e9eef6;background:#0b1119}*{box-sizing:border-box}body{margin:0}
.app{display:grid;grid-template-columns:320px 1fr 330px;min-height:100vh}
aside{background:#101b27;padding:18px 16px;overflow:auto;max-height:100vh}aside.r{border-left:1px solid #223548}aside.l{border-right:1px solid #223548}
h1{font-size:19px;margin:4px 0}.k{font-size:10px;letter-spacing:.16em;color:#86c5d7}.sm{font-size:11px;color:#98aaba}
.banner{padding:9px 10px;border-radius:8px;margin:10px 0;border:1px solid}.b-pass{background:#142b22;border-color:#2c6b4c;color:#bfe7d0}.b-lim{background:#392416;border-color:#8a5427;color:#f5cfa0}
.warn{background:#302a19;color:#f1d7a0;border:1px solid #665330;border-radius:8px;padding:9px;margin:8px 0;font-size:11px}
label{display:block;color:#a7bdcd;margin:11px 0 4px;font-size:11px}select,input[type=range]{width:100%}select{background:#182b3b;color:#fff;border:1px solid #345165;border-radius:6px;padding:7px}
.row{display:flex;gap:8px;align-items:center}.row label{margin:0;display:flex;gap:5px;align-items:center}button{background:#1d3a50;color:#fff;border:1px solid #3a6076;border-radius:6px;padding:6px 10px;cursor:pointer}
main{display:flex;flex-direction:column;min-width:0}.cv{flex:1;position:relative;min-height:440px}canvas{position:absolute;inset:0;width:100%;height:100%}
table{width:100%;border-collapse:collapse;font-size:11px}td,th{padding:3px 4px;border-bottom:1px solid #223548;text-align:left}th{color:#8fb4c7;font-weight:600}
.leg span{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px;vertical-align:-1px}#sunInfo{font-size:15px;font-weight:600}
@media(max-width:1100px){.app{grid-template-columns:1fr}aside{max-height:none}}
</style></head><body><div class="app">
<aside class="l"><div class="k">ARCHI GROW / SOLAR CONTEXT</div><h1>일조 · 그림자 검토</h1><div class="sm" id="project"></div>
<div id="statusBanner" class="banner"></div>
<div class="warn" id="claims"></div>
<label>대안</label><select id="alt"></select>
<label>일자</label><select id="date"></select>
<label>시각 <output id="timeOut"></output></label><input type="range" id="time" min="0" max="0" value="0">
<div class="row" style="margin-top:8px"><button id="play">▶ 재생</button><button id="prev">◀</button><button id="next">▶</button></div>
<label>격자 표시</label><select id="gridMode"><option value="off">끄기</option><option value="alt">누적 직사 시간(선택 대안)</option><option value="base">누적 직사 시간(기존 상태)</option><option value="loss">손실(기존-대안)</option></select>
<div class="row" style="flex-wrap:wrap;margin-top:8px"><label><input type="checkbox" id="tCtx" checked>주변 그림자</label><label><input type="checkbox" id="tProp" checked>대안 그림자</label><label><input type="checkbox" id="tRcv" checked>수광점</label><label><input type="checkbox" id="tBase">기존 상태 기준 수광</label></div>
<div class="leg" style="margin-top:12px"><div><span style="background:#ffd86b"></span>직사</div><div><span style="background:#4a6f95"></span>차폐</div><div><span style="background:#ff8c3a"></span>높이 미상 영향(불확정)</div><div><span style="background:#394552"></span>태양 반대면/무일사</div></div>
<div id="limits" class="sm" style="margin-top:14px"></div></aside>
<main><div class="cv"><canvas id="cv"></canvas></div><div class="sm" style="padding:8px 14px" id="foot"></div></main>
<aside class="r"><div id="sunInfo"></div><div class="sm" id="timeInfo"></div><h3>대안 지표</h3><table id="kpi"></table><h3>방향별 그림자 지속(분)</h3><table id="dir"></table>
<h3>수광점 영향 상위</h3><table id="top"></table><h3 id="hoverH">선택 수광점</h3><div class="sm" id="hover">마우스를 수광점 위에 올리세요.</div></aside></div>
<script>
"use strict";
const V=__DATA__;
const $=id=>document.getElementById(id);const cv=$('cv'),ctx=cv.getContext('2d');
const S={alt:V.alts[0].id,di:0,k:0,play:null,hover:-1};
$('project').textContent=V.project_id+' · '+V.data_class;
$('statusBanner').className='banner '+(V.status==='PASS'?'b-pass':'b-lim');
$('statusBanner').textContent=V.status==='PASS'?'기계 계산 완료 (법적 판단 아님)':'제한 결과: 높이 미상 건물이 수광점에 영향 → 최소/최대 구간만 유효';
$('claims').textContent='직사 일조 = 기하학적 시선 기준. 기상청 실측 일조·일사량·법정 일조 검토(건축법 시행령 제86조)와 다름. 지형 평지 가정.';
$('limits').textContent=V.limitations.join(' ');
V.alts.forEach(a=>{const o=document.createElement('option');o.value=a.id;o.textContent=a.id;$('alt').appendChild(o)});
V.dates.forEach((d,i)=>{const o=document.createElement('option');o.value=i;o.textContent=d.id+' '+d.date;$('date').appendChild(o)});
const ex=(()=>{let xs=[],ys=[];V.site.forEach(p=>{xs.push(p[0]);ys.push(p[1])});V.context.forEach(c=>c.ring.forEach(p=>{xs.push(p[0]);ys.push(p[1])}));const m=25;return[Math.min(...xs)-m,Math.min(...ys)-m,Math.max(...xs)+m,Math.max(...ys)+m]})();
function D(){return V.dates[S.di]}
function setupTime(){const n=D().steps.length;$('time').max=n-1;if(S.k>n-1)S.k=n-1;$('time').value=S.k}
function xf(W,H){const sx=W/(ex[2]-ex[0]),sy=H/(ex[3]-ex[1]),s=Math.min(sx,sy);const ox=(W-s*(ex[2]-ex[0]))/2,oy=(H-s*(ex[3]-ex[1]))/2;return{s,p:(x,y)=>[ox+(x-ex[0])*s,H-oy-(y-ex[1])*s]}}
function poly(T,flat,fill,stroke,lw){if(flat.length<6)return;ctx.beginPath();for(let i=0;i<flat.length;i+=2){const q=T.p(flat[i],flat[i+1]);i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1])}ctx.closePath();if(fill){ctx.fillStyle=fill;ctx.fill('evenodd')}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=lw||1;ctx.stroke()}}
const flat=r=>r.flat();
function ramp(v,mx){const t=Math.max(0,Math.min(1,v/mx));return`rgba(${Math.round(30+225*t)},${Math.round(60+160*t)},${Math.round(110-60*t)},.62)`}
function gridMinutes(d){const g=d.grid;if(!g)return null;const m=$('gridMode').value;if(m==='off')return null;const a=g[S.alt].minutes,b=g.BASE.minutes;
 return m==='alt'?a:m==='base'?b:a.map((v,i)=>b[i]-v)}
function draw(){const r=cv.getBoundingClientRect(),dpr=Math.min(2,devicePixelRatio||1);cv.width=r.width*dpr;cv.height=r.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);
 const W=r.width,H=r.height,T=xf(W,H),d=D(),st=d.steps[S.k];ctx.fillStyle='#0c1824';ctx.fillRect(0,0,W,H);
 const gm=gridMinutes(d);if(gm&&V.grid){const g=V.grid,wmax=Math.max(...Object.values(gm).filter(v=>v>0),1),mode=$('gridMode').value;
  for(let j=0;j<g.ny;j++)for(let i=0;i<g.nx;i++){const n=j*g.nx+i;if(!g.open[n])continue;const p=T.p(g.x0+i*g.sp,g.y0+(j+1)*g.sp);const unc=d.grid[S.alt].uncertain[n];
   ctx.fillStyle=mode==='loss'?`rgba(255,90,90,${Math.min(.8,gm[n]/Math.max(wmax,1))})`:ramp(gm[n],360);ctx.fillRect(p[0],p[1],g.sp*T.s+.5,g.sp*T.s+.5);if(unc){ctx.fillStyle='rgba(255,140,58,.35)';ctx.fillRect(p[0],p[1],g.sp*T.s+.5,g.sp*T.s+.5)}}}
 if($('tCtx').checked)d.ctx_shadow[S.k].forEach(rg=>poly(T,rg,'rgba(20,28,45,.5)',null));
 if($('tProp').checked)(d.prop_shadow[S.alt][S.k]||[]).forEach(rg=>poly(T,rg,'rgba(10,15,40,.62)',null));
 poly(T,flat(V.site),null,'#72aeb2',1.6);
 V.context.forEach(c=>{poly(T,flat(c.ring),c.unknown?'rgba(255,140,58,.18)':'#2c3e50',c.unknown?'#ff8c3a':'#6f8aa0',c.unknown?1.6:1);const q=T.p(c.ring[0][0],c.ring[0][1]);ctx.fillStyle='#9fb6c8';ctx.font='10px system-ui';ctx.fillText(c.unknown?'H?':Math.round(c.h)+'m',q[0]+3,q[1]-3)});
 const A=V.alts.find(a=>a.id===S.alt);A.levels.forEach((l,i)=>poly(T,flat(l.ring),i===A.levels.length-1?'rgba(216,222,214,.9)':'rgba(120,160,175,.12)','#a1bcc6',.8));
 if($('tRcv').checked){const bits=d.bits[$('tBase').checked?'BASE':S.alt];V.receivers.forEach((rc,i)=>{const ch=bits[i][S.k]||'-',q=T.p(rc.x,rc.y);ctx.beginPath();ctx.arc(q[0],q[1],i===S.hover?5:3,0,7);
  ctx.fillStyle=ch==='1'?'#ffd86b':ch==='0'?'#4a6f95':ch==='x'?'#ff8c3a':'#394552';ctx.fill();if(i===S.hover){ctx.strokeStyle='#fff';ctx.stroke()}})}
 const n=V.north;const nx=n[0],ny=n[1],a0=[W-50,50];ctx.strokeStyle='#e8c46a';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(a0[0],a0[1]);ctx.lineTo(a0[0]+nx*28,a0[1]-ny*28);ctx.stroke();ctx.fillStyle='#e8c46a';ctx.fillText('N',a0[0]+nx*34-4,a0[1]-ny*34+4);
 if(st.up){const h=sunVec(st.az);ctx.strokeStyle='#ffd86b';ctx.beginPath();ctx.moveTo(a0[0],a0[1]+60);ctx.lineTo(a0[0]+h[0]*28,a0[1]+60-h[1]*28);ctx.stroke();ctx.fillStyle='#ffd86b';ctx.fillText('☀',a0[0]+h[0]*34-4,a0[1]+60-h[1]*34+4)}
 ctx.fillStyle='#9cccd1';ctx.font='12px system-ui';ctx.fillText('SITE '+(V.alts[0].kpi.site_area_official_or_declared_m2)+'㎡ · '+S.alt+' · '+d.date+' '+st.label,14,22)}
function sunVec(az){const a=az*Math.PI/180;return[Math.sin(a)*V.east[0]+Math.cos(a)*V.north[0],Math.sin(a)*V.east[1]+Math.cos(a)*V.north[1]]}
function fmt(s){return s?(s.valid?s.nom.total_min+'분 (연속 '+s.nom.longest_min+')':s.lo.total_min+'–'+s.hi.total_min+'분 (구간)'):'-'}
function panels(){const d=D(),st=d.steps[S.k];$('timeOut').textContent=st.label;
 $('sunInfo').textContent=(st.up?'방위 '+st.az.toFixed(1)+'° · 고도 '+st.el.toFixed(1)+'°':'태양 고도 부족 ('+st.el.toFixed(1)+'°)');
 const ti=d.time_info;$('timeInfo').textContent='EoT '+ti.equation_of_time_min+'분 · 경도보정 '+ti.longitude_correction_min+'분 · '+V.location.lat.toFixed(4)+'N '+V.location.lon.toFixed(4)+'E ('+V.location.verification+')';
 const A=V.alts.find(a=>a.id===S.alt),k=A.kpi;const rows=[['대지(공식/선언)',k.site_area_official_or_declared_m2+'㎡'],['폴리곤 면적',k.site_polygon_area_m2+'㎡ (Δ '+k.official_vs_polygon_delta_m2+')'],['연면적',k.gfa_m2+'㎡'],['건폐율/용적률',k.bcr_pct.toFixed(1)+'% / '+k.far_pct.toFixed(1)+'%'],['층수 · 층고',k.story_count+'F · '+k.floor_to_floor_m.join('/')+'m'],['최고높이',k.max_height_m+'m'],['대지경계 이격(기하)',k.min_clearance_to_site_boundary_m+'m'],['인접건물 이격(기하)',k.min_separation_to_context_footprint_m+'m'],['법정 이격','미확인 (NOT_SOURCED)'],['지표 재계산 일치',k.kpi_recomputed_matches_reported?'일치':'불일치']];
 $('kpi').innerHTML=rows.map(r=>`<tr><th>${r[0]}</th><td>${r[1]}</td></tr>`).join('');
 const dd=d.directional[S.alt];$('dir').innerHTML='<tr>'+Object.keys(dd.minutes).map(x=>`<th>${x}</th>`).join('')+'</tr><tr>'+Object.values(dd.minutes).map(x=>`<td>${x}</td>`).join('')+'</tr><tr><td colspan=8 class="sm">최대 그림자 도달 '+dd.max_reach_m.toFixed(1)+'m (창 전체)</td></tr>';
 const base=d.summary.BASE,alt=d.summary[S.alt];const items=V.receivers.map((r,i)=>({i,r,loss:(base[i]&&alt[i]&&base[i].valid&&alt[i].valid)?base[i].nom.total_min-alt[i].nom.total_min:(base[i]&&alt[i]?base[i].lo.total_min-alt[i].hi.total_min:0)})).sort((a,b)=>b.loss-a.loss).slice(0,8);
 $('top').innerHTML='<tr><th>수광점</th><th>기존</th><th>대안</th><th>손실</th></tr>'+items.map(o=>`<tr data-i="${o.i}"><td>${o.r.id.replace('RCV-','')}</td><td>${fmt(base[o.i])}</td><td>${fmt(alt[o.i])}</td><td>${o.loss}</td></tr>`).join('');
 $('foot').textContent='창 '+V.windows[0].id+' 기준 (참고용) · 표본은 구간 시작 시각 · 확인 전 법적 판단 금지';
 window.__solar={date:d.id,alt:S.alt,time:st.label,az:st.az,el:st.el,up:st.up,litCount:V.receivers.filter((r,i)=>(d.bits[S.alt][i][S.k]||'-')==='1').length,
  ctxShadowRings:d.ctx_shadow[S.k].length,propShadowRings:(d.prop_shadow[S.alt][S.k]||[]).length,status:V.status};}
function all(){setupTime();panels();draw()}
$('alt').onchange=e=>{S.alt=e.target.value;all()};$('date').onchange=e=>{S.di=+e.target.value;S.k=0;all()};$('time').oninput=e=>{S.k=+e.target.value;all()};
['gridMode','tCtx','tProp','tRcv','tBase'].forEach(id=>$(id).onchange=draw);
$('next').onclick=()=>{S.k=Math.min(S.k+1,D().steps.length-1);all()};$('prev').onclick=()=>{S.k=Math.max(S.k-1,0);all()};
$('play').onclick=()=>{if(S.play){clearInterval(S.play);S.play=null;$('play').textContent='▶ 재생';return}$('play').textContent='❚❚ 정지';S.play=setInterval(()=>{S.k=(S.k+1)%D().steps.length;all()},180)};
cv.onmousemove=e=>{const r=cv.getBoundingClientRect(),T=xf(r.width,r.height);let b=-1,bd=64;V.receivers.forEach((rc,i)=>{const q=T.p(rc.x,rc.y),dx=q[0]-(e.clientX-r.left),dy=q[1]-(e.clientY-r.top),dd=dx*dx+dy*dy;if(dd<bd){bd=dd;b=i}});
 if(b!==S.hover){S.hover=b;const d=D();if(b>=0){const rc=V.receivers[b];$('hover').innerHTML=rc.id+'<br>높이 z='+rc.z+'m<br>기존: '+fmt(d.summary.BASE[b])+'<br>'+S.alt+': '+fmt(d.summary[S.alt][b])+(d.summary[S.alt][b]&&!d.summary[S.alt][b].valid?'<br><b style="color:#ff8c3a">높이 미상 건물 영향: 공칭값 보류</b>':'')}else $('hover').textContent='마우스를 수광점 위에 올리세요.';draw()}};
window.addEventListener('resize',draw);all();
</script></body></html>"""


def write_outputs(report, viewer, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rp = out / "solar_study_report.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    vp = out / "solar_viewer.html"
    vp.write_text(viewer_html(viewer), encoding="utf-8")
    return [rp, vp]


def build(input_path, massing_path, context_path, out_dir):
    input_path = Path(input_path)
    cfg = json.loads(input_path.read_bytes().decode("utf-8-sig"))
    massing = json.loads(Path(massing_path).read_bytes().decode("utf-8-sig"))
    context = json.loads(Path(context_path).read_bytes().decode("utf-8-sig")) if context_path else None
    hashes = {"solar_input": sha_file(input_path), "massing_result": sha_file(massing_path),
              "context_obstacles": sha_file(context_path) if context_path else None, "tool": sha_file(__file__)}
    report, viewer = run_study(cfg, massing, context, input_paths=hashes)
    return report, write_outputs(report, viewer, out_dir)


def main():
    ap = argparse.ArgumentParser(description="Run an ArchiGrow solar/shadow context study.")
    ap.add_argument("input")
    ap.add_argument("--massing", required=True)
    ap.add_argument("--context")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    try:
        report, files = build(a.input, a.massing, a.context, a.out_dir)
    except SolarHold as ex:
        print(json.dumps({"status": "HOLD", "failure": ex.code, "detail": ex.detail}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": report["result_status"], "data_class": report["data_class"],
                      "files": [str(f) for f in files]}, ensure_ascii=False))
    return 0 if report["result_status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
