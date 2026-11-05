#!/usr/bin/env python3
"""ArchiGrow SITE_CONTEXT adapter: nearby building footprints + heights for the solar study.

SOURCES (each result is labelled; nothing is promoted to verified silently):
  VWORLD_LIVE              official VWorld 2D data API getFeature, layer LT_C_BLDGINFO (needs the free key;
                           honest UNAVAILABLE/HOLD without it), bbox-paged, raw page SHA preserved.
  VWORLD_RESPONSE_FIXTURE  the same parser fed with saved VWorld-shaped pages (contract test, NOT public data).
  OFFLINE_GEOJSON          trusted local GeoJSON; SHA-pinned only when the caller pins the hash.
Height policy: reported height > 0 -> REPORTED; else floors x assumed floor-to-floor range (LOW confidence,
with min/max); else UNKNOWN. Zero/negative/non-numeric height is UNKNOWN, never zero.
VWorld property names are alias-matched and NOT verified against a live response in this environment.
Not a legal sunlight test. No network call unless mode is VWORLD_LIVE and a key is configured.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("archigrow_parcel_source", HERE / "ARCHIGROW_PARCEL_SOURCE.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

VERSION = "ARCHIGROW_BUILDING_CONTEXT/2026-10-18.1"
SCHEMA_INPUT = "ARCHIGROW_SITE_CONTEXT_INPUT_V1"
SCHEMA_OBSTACLES = "ARCHIGROW_CONTEXT_OBSTACLES_V1"
VWORLD = "https://api.vworld.kr/req/data"
LAYER_BUILDINGS = "LT_C_BLDGINFO"
LAYER_PARCELS = "LP_PA_CBND_BUBUN"
# Alias lists: unverified against a live response (no key available when written).
FIELD_ALIASES = {
    "height_m": ["heit", "bld_hgt", "bldg_hgt", "bldg_height", "height", "hg"],
    "ground_floors": ["grnd_flr", "gro_flo_co", "ground_floor_count", "grndflr", "flr_co"],
    "name": ["bld_nm", "buld_nm", "bldg_nm", "name"],
    "source_id": ["gid", "bd_mgt_sn", "mgm_bld_pk", "objectid", "fid", "pk"],
    "pnu": ["pnu"],
    "approval_date": ["use_apr_day", "useaprday", "use_aprv_ymd"],
}
FIELD_MAPPING_STATUS = "ALIAS_BASED_UNVERIFIED_AGAINST_LIVE_RESPONSE"
DEFAULT_FLOOR_TO_FLOOR = {"nominal_m": 3.2, "min_m": 2.8, "max_m": 3.6,
                          "status": "SENSITIVITY_ASSUMPTION_NOT_SOURCED"}
MAX_PLAUSIBLE_HEIGHT_M = 600.0


class ContextHold(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = str(detail)[:250]


def now():
    return datetime.now(timezone.utc).isoformat()


def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(str(v).strip().replace(",", ""))
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def _first(props, aliases):
    low = {str(k).lower(): v for k, v in (props or {}).items()}
    for a in aliases:
        if a in low and low[a] not in (None, ""):
            return a, low[a]
    return None, None


def derive_height(props, ftf=None):
    """Return height record. Zero/invalid heights are UNKNOWN, never 0."""
    ftf = {**DEFAULT_FLOOR_TO_FLOOR, **(ftf or {})}
    issues = []
    name, raw = _first(props, FIELD_ALIASES["height_m"])
    reported = _num(raw) if name else None
    if name and (reported is None or reported <= 0 or reported > MAX_PLAUSIBLE_HEIGHT_M):
        issues.append("ZERO_OR_INVALID_REPORTED_HEIGHT")
        reported = None
    if reported is not None:
        return {"height_m": reported, "height_min_m": reported, "height_max_m": reported,
                "height_source": "REPORTED_HEIGHT", "confidence": "MEDIUM",
                "height_field": name, "issues": issues}
    fname, fraw = _first(props, FIELD_ALIASES["ground_floors"])
    floors = _num(fraw) if fname else None
    if fname and (floors is None or floors < 1 or floors > 150 or floors != int(floors)):
        issues.append("INVALID_FLOOR_COUNT")
        floors = None
    if floors is not None:
        return {"height_m": round(floors * ftf["nominal_m"], 3),
                "height_min_m": round(floors * ftf["min_m"], 3),
                "height_max_m": round(floors * ftf["max_m"], 3),
                "height_source": "FLOORS_X_ASSUMED_FLOOR_TO_FLOOR", "confidence": "LOW",
                "floors_ground": int(floors), "floor_to_floor_assumption": ftf,
                "height_field": fname, "issues": issues}
    return {"height_m": None, "height_min_m": None, "height_max_m": None,
            "height_source": "UNKNOWN", "confidence": "NONE", "issues": issues + ["HEIGHT_UNKNOWN"]}


# ---------------------------------------------------------------- geometry
def _transformer(src, dst):
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise ContextHold("FREE_PYPROJ_DEPENDENCY_REQUIRED") from exc
    return Transformer.from_crs(src, dst, always_xy=True)


def scene_bbox_wgs84(scene, site_polygon, radius_m):
    """WGS84 BOX around the site (+radius) for a projected scene."""
    crs, origin = scene.get("projected_crs"), scene.get("origin_m")
    if crs not in ("EPSG:5186", "EPSG:5179") or not (isinstance(origin, list) and len(origin) == 2):
        raise ContextHold("PROJECTED_SCENE_REQUIRED_FOR_PUBLIC_GIS_BBOX")
    xs = [p[0] + origin[0] for p in site_polygon]
    ys = [p[1] + origin[1] for p in site_polygon]
    corners = [(min(xs) - radius_m, min(ys) - radius_m), (max(xs) + radius_m, min(ys) - radius_m),
               (max(xs) + radius_m, max(ys) + radius_m), (min(xs) - radius_m, max(ys) + radius_m)]
    t = _transformer(crs, "EPSG:4326")
    pts = [t.transform(x, y) for x, y in corners]
    return [round(min(p[0] for p in pts), 7), round(min(p[1] for p in pts), 7),
            round(max(p[0] for p in pts), 7), round(max(p[1] for p in pts), 7)]


def _rings_to_local(rings, source_crs, scene):
    """GeoJSON ring -> scene local metres. Hole rings are returned separately."""
    crs, origin = scene.get("projected_crs"), scene.get("origin_m")
    if source_crs == "LOCAL_M":
        return [[[float(p[0]), float(p[1])] for p in r] for r in rings]
    if not crs or not origin:
        raise ContextHold("PROJECTED_SCENE_REQUIRED_FOR_GEOREFERENCED_SOURCE")
    t = None if source_crs == crs else _transformer(source_crs, crs)
    out = []
    for r in rings:
        pts = []
        for p in r:
            x, y = (p[0], p[1]) if t is None else t.transform(p[0], p[1])
            pts.append([round(x - origin[0], 4), round(y - origin[1], 4)])
        out.append(pts)
    return out


def _polygons(geometry):
    typ, coords = (geometry or {}).get("type"), (geometry or {}).get("coordinates")
    if typ == "Polygon" and isinstance(coords, list):
        return [coords]
    if typ == "MultiPolygon" and isinstance(coords, list):
        return [c for c in coords if isinstance(c, list)]
    return []


def normalize_features(features, *, source_crs, scene, site_polygon, radius_m, source_class,
                       source_status, ftf=None, id_prefix="BLD"):
    """GeoJSON features -> obstacle records in scene metres. Deterministic IDs."""
    try:
        from shapely.geometry import Polygon
        from shapely.validation import make_valid
    except ImportError as exc:
        raise ContextHold("FREE_SHAPELY_DEPENDENCY_REQUIRED") from exc
    site = Polygon(site_polygon) if site_polygon else None
    obstacles, dropped, seen = [], [], set()
    for idx, f in enumerate(features):
        props = f.get("properties") or {}
        _, sid = _first(props, FIELD_ALIASES["source_id"])
        sid = str(f.get("id") or sid or "")
        parts = _polygons(f.get("geometry"))
        if not parts:
            dropped.append({"index": idx, "source_id": sid, "reason": "NO_POLYGON_GEOMETRY"})
            continue
        h = derive_height(props, ftf)
        for pi, rings in enumerate(parts):
            if not rings or len(rings[0]) < 4:
                dropped.append({"index": idx, "source_id": sid, "reason": "RING_TOO_SHORT"})
                continue
            local = _rings_to_local(rings, source_crs, scene)
            geom = Polygon(local[0], local[1:])
            issues = list(h["issues"])
            if not geom.is_valid:
                geom = make_valid(geom)
                issues.append("GEOMETRY_REPAIRED_MAKE_VALID")
            poly = geom if geom.geom_type == "Polygon" else max(
                (g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"),
                key=lambda g: g.area, default=None)
            if poly is None or poly.area < 0.5:
                dropped.append({"index": idx, "source_id": sid, "reason": "DEGENERATE_FOOTPRINT"})
                continue
            if len(poly.interiors):
                issues.append("COURTYARD_HOLES_IGNORED_SHADOW_MAY_BE_OVERESTIMATED")
            if site is not None and poly.distance(site) > radius_m:
                dropped.append({"index": idx, "source_id": sid, "reason": "OUTSIDE_RADIUS"})
                continue
            ring = [[round(x, 3), round(y, 3)] for x, y in list(poly.exterior.coords)[:-1]]
            digest = hashlib.sha1(json.dumps(ring).encode()).hexdigest()[:10]
            base = f"{id_prefix}-{sid}" if sid else f"{id_prefix}-H{digest}"
            oid = base + (f"#p{pi}" if len(parts) > 1 else "")
            if oid in seen:
                dropped.append({"index": idx, "source_id": sid, "reason": "DUPLICATE_ID"})
                continue
            seen.add(oid)
            if site is not None and poly.intersection(site).area > 1.0:
                issues.append("OVERLAPS_SITE_EXISTING_BUILDING_REQUIRES_EXPLICIT_DEMOLITION_ASSUMPTION")
            _, name = _first(props, FIELD_ALIASES["name"])
            _, pnu = _first(props, FIELD_ALIASES["pnu"])
            _, apr = _first(props, FIELD_ALIASES["approval_date"])
            rec = {"id": oid, "source_feature_id": sid or None, "footprint_m": ring,
                   "footprint_area_m2": round(poly.area, 3), "name": name, "pnu": pnu,
                   "approval_date": apr, **{k: v for k, v in h.items() if k != "issues"},
                   "issues": issues, "source_class": source_class, "source_status": source_status}
            obstacles.append(rec)
    obstacles.sort(key=lambda o: o["id"])
    return obstacles, dropped


def completeness(obstacles, dropped, paging=None):
    total_area = sum(o["footprint_area_m2"] for o in obstacles) or 0.0
    unk = [o for o in obstacles if o["height_m"] is None]
    by_src, by_conf = {}, {}
    for o in obstacles:
        by_src[o["height_source"]] = by_src.get(o["height_source"], 0) + 1
        by_conf[o["confidence"]] = by_conf.get(o["confidence"], 0) + 1
    return {"obstacle_count": len(obstacles), "height_known_count": len(obstacles) - len(unk),
            "height_unknown_count": len(unk), "height_unknown_ids": [o["id"] for o in unk],
            "unknown_footprint_area_share": round(sum(o["footprint_area_m2"] for o in unk) / total_area, 4) if total_area else None,
            "by_height_source": by_src, "by_confidence": by_conf,
            "dropped_count": len(dropped), "dropped": dropped[:50],
            "pagination": paging, "field_mapping_status": FIELD_MAPPING_STATUS,
            "status": "COMPLETE_HEIGHTS" if obstacles and not unk else
                      ("NO_FEATURES" if not obstacles else "LIMITED_UNKNOWN_HEIGHTS")}


# ---------------------------------------------------------------- VWorld
def parse_vworld_page(data):
    resp = (data or {}).get("response") or {}
    status = resp.get("status")
    if status == "ERROR" or resp.get("error"):
        raise ContextHold("VWORLD_PROVIDER_ERROR", json.dumps(resp.get("error"), ensure_ascii=False)[:120])
    if status == "NOT_FOUND":
        return {"features": [], "total": 0, "page_total": 1, "page_current": 1, "status": "NOT_FOUND"}
    coll = (resp.get("result") or {}).get("featureCollection") or {}
    feats = coll.get("features")
    if status != "OK" or not isinstance(feats, list):
        raise ContextHold("VWORLD_FEATURE_COLLECTION_NOT_FOUND")
    rec, page = resp.get("record") or {}, resp.get("page") or {}
    total = _num(rec.get("total"))
    return {"features": feats, "total": int(total) if total is not None else None,
            "page_total": int(_num(page.get("total")) or 1), "page_current": int(_num(page.get("current")) or 1),
            "status": "OK"}


def fetch_layer(layer, bbox, key, domain="", fetch=None, raw_dir=None, size=1000, max_pages=30, tag="BBOX"):
    """Paged getFeature with GeoJSON in EPSG:4326. Key never stored/returned."""
    if not key:
        raise ContextHold("VWORLD_FREE_API_KEY_NOT_CONFIGURED")
    fetch = fetch or (lambda u: S.bounded_fetch(u, 12_000_000))
    feats, digests, refs, total, page_total, page = [], [], [], None, 1, 1
    while page <= min(page_total, max_pages):
        args = {"service": "data", "request": "GetFeature", "data": layer, "key": key,
                "geomFilter": "BOX(%s,%s,%s,%s)" % tuple(bbox), "crs": "EPSG:4326",
                "format": "json", "size": size, "page": page}
        if domain:
            args["domain"] = domain
        try:
            raw, _, status = fetch(VWORLD + "?" + urllib.parse.urlencode(args))
        except ContextHold:
            raise
        except Exception as exc:
            raise ContextHold("VWORLD_NETWORK_ERROR", type(exc).__name__) from None
        if status != 200:
            raise ContextHold("VWORLD_HTTP_ERROR", str(status))
        if raw_dir:
            refs.append(S.preserve_raw(raw, raw_dir, tag, layer + f"_p{page}", "json"))
        digests.append(S.digest(raw))
        try:
            parsed = parse_vworld_page(json.loads(raw.decode("utf-8-sig")))
        except ValueError:
            raise ContextHold("VWORLD_JSON_INVALID") from None
        feats.extend(parsed["features"])
        total = parsed["total"] if total is None else total
        page_total = parsed["page_total"]
        page += 1
    return _paged_result(layer, bbox, size, feats, total, page_total, page - 1, max_pages, digests, refs)


def _paged_result(layer, bbox, size, feats, total, page_total, fetched, max_pages, digests, refs):
    complete = fetched >= page_total and (total is None or len(feats) == total)
    return {"layer": layer, "bbox_wgs84": bbox, "crs": "EPSG:4326", "page_size": size,
            "pages_fetched": fetched, "pages_reported": page_total, "max_pages": max_pages,
            "total_records_reported": total, "records_collected": len(feats), "complete": complete,
            "page_sha256": digests, "raw_refs": refs, "features": feats, "observed_at": now()}


def read_fixture_pages(paths, layer, bbox):
    """Saved VWorld-shaped pages through the same parser (contract test; not public data)."""
    feats, digests, total, page_total = [], [], None, len(paths)
    for p in paths:
        raw = Path(p).read_bytes()
        digests.append(S.digest(raw))
        parsed = parse_vworld_page(json.loads(raw.decode("utf-8-sig")))
        feats.extend(parsed["features"])
        total = parsed["total"] if total is None else total
        page_total = max(page_total, parsed["page_total"])
    return _paged_result(layer, bbox, 1000, feats, total, page_total, len(paths), len(paths), digests, [])


# ---------------------------------------------------------------- run
def _site_polygon_from(scene_doc):
    return scene_doc.get("site_polygon_m") or []


def build(cfg, scene, site_polygon, base_dir=Path("."), raw_dir=None, fetch=None, key=None):
    """Return (obstacles_doc, receipt). Raises ContextHold for source-level HOLDs."""
    if cfg.get("schema") != SCHEMA_INPUT:
        raise ContextHold("SCHEMA_UNSUPPORTED")
    mode = cfg.get("mode")
    radius = _num(cfg.get("radius_m")) or 150.0
    ftf = cfg.get("floor_to_floor_assumption")
    base_dir = Path(base_dir)
    receipt = {"mode": mode, "radius_m": radius, "tool_version": VERSION, "observed_at": now(),
               "field_mapping_status": FIELD_MAPPING_STATUS}
    if mode in ("VWORLD_LIVE", "VWORLD_RESPONSE_FIXTURE"):
        bbox = scene_bbox_wgs84(scene, site_polygon, radius)
        if mode == "VWORLD_LIVE":
            key = key if key is not None else (os.environ.get("VWORLD_KEY") or os.environ.get("VWORLD_API_KEY") or "")
            if not key:
                raise ContextHold("VWORLD_FREE_API_KEY_NOT_CONFIGURED")
            paged = fetch_layer(LAYER_BUILDINGS, bbox, key, os.environ.get("VWORLD_DOMAIN", ""),
                                fetch=fetch, raw_dir=raw_dir, tag=str(cfg.get("pnu") or "BBOX"))
            source_class, status = "VWORLD_LT_C_BLDGINFO_OBSERVED", "OFFICIAL_API_OBSERVED_NOT_LEGAL_RECORD"
        else:
            paths = [str((base_dir / p).resolve()) for p in cfg.get("fixture_pages", [])]
            if not paths:
                raise ContextHold("FIXTURE_PAGES_REQUIRED")
            paged = read_fixture_pages(paths, LAYER_BUILDINGS, bbox)
            source_class, status = "VWORLD_SHAPED_FIXTURE", "FIXTURE_NOT_PUBLIC_DATA"
        features, src_crs = paged.pop("features"), "EPSG:4326"
        paging = {k: v for k, v in paged.items() if k != "raw_refs"}
        receipt.update(request={"layer": LAYER_BUILDINGS, "bbox_wgs84": bbox, "crs": "EPSG:4326",
                                "pnu": cfg.get("pnu"), "scene_crs": scene.get("projected_crs"),
                                "scene_origin_m": scene.get("origin_m")}, raw_refs=paged["raw_refs"])
        if not paged["complete"]:
            receipt["paging"] = paging
            raise ContextHold("VWORLD_BUILDING_PAGINATION_INCOMPLETE",
                              f"{paged['records_collected']}/{paged['total_records_reported']}")
    elif mode == "OFFLINE_GEOJSON":
        og = cfg.get("offline_geojson") or {}
        path = (base_dir / og.get("path", "")).resolve()
        if not path.is_file():
            raise ContextHold("OFFLINE_GEOJSON_NOT_FOUND")
        raw = path.read_bytes()
        sha = S.digest(raw)
        if not og.get("source_crs") or not og.get("provenance"):
            raise ContextHold("OFFLINE_GEOJSON_CRS_AND_PROVENANCE_REQUIRED")
        doc = json.loads(raw.decode("utf-8-sig"))
        features = doc.get("features") if doc.get("type") == "FeatureCollection" else None
        if not isinstance(features, list):
            raise ContextHold("OFFLINE_GEOJSON_NOT_FEATURECOLLECTION")
        pinned = bool(og.get("trusted_sha256")) and og["trusted_sha256"] == sha
        if og.get("trusted_sha256") and not pinned:
            raise ContextHold("OFFLINE_GEOJSON_SHA_PIN_MISMATCH")
        src_crs = og["source_crs"]
        source_class = og.get("source_class", "OFFLINE_GEOJSON")
        status = "SHA_PINNED_OFFLINE_FILE" if pinned else "OFFLINE_FILE_UNPINNED_NOT_VERIFIED"
        paging = {"complete": True, "records_collected": len(features), "total_records_reported": len(features)}
        receipt.update(offline={"path": str(path), "sha256": sha, "source_crs": src_crs,
                                "provenance": og["provenance"], "sha_pinned": pinned})
    else:
        raise ContextHold("SITE_CONTEXT_MODE_UNSUPPORTED")
    obstacles, dropped = normalize_features(features, source_crs=src_crs, scene=scene, site_polygon=site_polygon,
                                            radius_m=radius, source_class=source_class, source_status=status, ftf=ftf)
    comp = completeness(obstacles, dropped, paging)
    if not obstacles:
        receipt["completeness"] = comp
        raise ContextHold("NO_BUILDING_FEATURES_RETURNED")
    doc = {"schema": SCHEMA_OBSTACLES, "project_id": cfg.get("project_id"), "source_class": source_class,
           "source_status": status, "scene": scene, "completeness": comp, "obstacles": obstacles,
           "legal_use": "NOT_A_LEGAL_RECORD", "generated_by": VERSION}
    receipt.update(source_class=source_class, source_status=status, completeness=comp)
    return doc, receipt


def run(input_path, out_dir, scene=None, site_polygon=None, fetch=None, key=None):
    input_path, out = Path(input_path), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(input_path.read_text(encoding="utf-8-sig"))
    scene = scene or cfg.get("scene") or {}
    site_polygon = site_polygon or cfg.get("site_polygon_m") or []
    receipt = {"project_id": cfg.get("project_id")}
    try:
        doc, r = build(cfg, scene, site_polygon, input_path.parent, out / "RAW", fetch, key)
        receipt.update(r, status="PASS")
        (out / "context_obstacles.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    except ContextHold as ex:
        receipt.update(status="HOLD", failure_class=ex.code, detail=ex.detail,
                       building_context_status="UNAVAILABLE", mode=cfg.get("mode"))
    (out / "site_context_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt


def main():
    ap = argparse.ArgumentParser(description="Build SITE_CONTEXT obstacles (VWorld LT_C_BLDGINFO / fixture / offline GeoJSON).")
    ap.add_argument("input")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    r = run(a.input, a.out_dir)
    print(json.dumps({"status": r["status"], "failure_class": r.get("failure_class"),
                      "completeness": (r.get("completeness") or {}).get("status")}, ensure_ascii=False))
    return 0 if r["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
