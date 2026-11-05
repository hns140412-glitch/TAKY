#!/usr/bin/env python3
"""ARCHIGROW panel source extractor: one lightweight import adapter for unfamiliar boards (native PDF / PPTX / raster).

Not a render engine. It reads a source file read-only and emits located regions with coordinate provenance so that
ARCHIGROW_PANEL_WORKFLOW.py can consume human-reviewed blocks:

  PDF   PyMuPDF   text blocks (text layer), embedded images, vector drawing clusters   -> bbox in the VISUAL page frame
  PPTX  python-pptx   shapes / pictures / tables / charts / native groups (EMU)           -> bbox in the slide frame
  PNG/JPEG   whole-page image-bound UNKNOWN region, NEEDS_REVIEW (OCR / vision is HOLD, not implemented)

Honesty contract: extraction is local and deterministic. Geometry is measured; MEANING is not. Every region's semantic
type is UNKNOWN until a human saves a correction. Nothing is silently accepted. Corrections are bound to the source
sha256; a changed source marks them STALE instead of applying them.
"""
import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "DOMAIN" / "ARCHITECTURE_COMPETITION_ARTIFACT_SCHEMA.json"

EXTRACT_VERSION = "ARCHIGROW_PANEL_SOURCE_REGIONS_V1"
CORRECTIONS_VERSION = "ARCHIGROW_PANEL_CORRECTIONS_V1"
DISCLOSURE = (
    "LOCAL_DETERMINISTIC_EXTRACTION: geometry comes from the native file (PDF text/image/vector objects, PPTX shapes); "
    "semantic_type is UNKNOWN until a human correction is saved. This is NOT a multimodal AI reading of the board and "
    "does not OCR raster images (image OCR/vision = HOLD)."
)
FALLBACK_MODES = ["CONTEXT", "CIRCULATION", "CONCEPT", "PROGRAM", "PERFORMANCE", "PLAN", "SECTION", "ELEVATION",
                  "AXONOMETRIC", "TECHNICAL", "EXPERIENCE"]
EXTRA_TYPES = ["UNKNOWN", "OTHER"]
IMAGE_SUFFIX = {".png", ".jpg", ".jpeg"}
MAX_DRAWINGS = 6000
MAX_MEMBER_IDS = 200


# ---------------------------------------------------------------- helpers

def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def drawing_modes():
    """All drawing_mode values of the existing artifact schema (fallback: the 11 known modes)."""
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return list(FALLBACK_MODES)

    def find(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "drawing_mode" and isinstance(value, dict):
                    if isinstance(value.get("enum"), list):
                        return value["enum"]
                    items = value.get("items")
                    if isinstance(items, dict) and isinstance(items.get("enum"), list):
                        return items["enum"]
                found = find(value)
                if found:
                    return found
        elif isinstance(node, list):
            for value in node:
                found = find(value)
                if found:
                    return found
        return None

    modes = find(schema)
    return [str(m) for m in modes] if modes else list(FALLBACK_MODES)


def semantic_types():
    return drawing_modes() + [t for t in EXTRA_TYPES if t not in drawing_modes()]


def norm_bbox(x0, y0, x1, y1, width, height):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    return {"x": round(x0 / width, 6), "y": round(y0 / height, 6),
            "w": round((x1 - x0) / width, 6), "h": round((y1 - y0) / height, 6)}


def native_bbox(x0, y0, x1, y1):
    return {"x0": round(min(x0, x1), 3), "y0": round(min(y0, y1), 3), "x1": round(max(x0, x1), 3), "y1": round(max(y0, y1), 3)}


def rect_id_for(page_no, kind, nb):
    """Geometry-derived id (no source hash): the same rectangle keeps its id across source revisions."""
    key = f"{page_no}|{kind}|{nb['x']:.3f}|{nb['y']:.3f}|{nb['w']:.3f}|{nb['h']:.3f}"
    return "R" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


class RegionSink:
    """Collects regions of one page and keeps rect ids unique and stable."""

    def __init__(self, page_no, width, height, unit, source_sha):
        self.page_no, self.width, self.height, self.unit, self.source_sha = page_no, width, height, unit, source_sha
        self.regions, self._seen = [], {}

    def add(self, kind, bbox, object_id, method, geometry_conf, text=None, native_ref=None, extra=None,
            bbox_native_extra=None):
        x0, y0, x1, y1 = bbox
        nb = norm_bbox(x0, y0, x1, y1, self.width, self.height)
        rid = rect_id_for(self.page_no, kind, nb)
        n = self._seen.get(rid, 0)
        self._seen[rid] = n + 1
        if n:
            rid = f"{rid}-{n + 1}"
        rec = {
            "rect_id": rid, "object_id": object_id, "page": self.page_no, "kind": kind,
            "bbox_native": native_bbox(x0, y0, x1, y1), "native_unit": self.unit, "bbox_norm": nb,
            "extractor": method["extractor"], "method": method["method"],
            "confidence": {"geometry": geometry_conf, "semantic": 0.0},
            "semantic_type": "UNKNOWN", "label": "", "review_state": "PROPOSED",
            "native_ref": native_ref, "source_sha256": self.source_sha,
        }
        if text is not None:
            rec["text"] = text[:400]
            rec["text_length"] = len(text)
        if bbox_native_extra:
            rec.update(bbox_native_extra)
        if extra:
            rec.update(extra)
        self.regions.append(rec)
        return rec


# ---------------------------------------------------------------- PDF (PyMuPDF)

def _load_fitz():
    try:
        import pymupdf as fitz  # type: ignore
    except ImportError:
        import fitz  # type: ignore
    return fitz


def _union_find_clusters(rects, tol):
    """Cluster rect tuples whose tolerance-inflated boxes overlap. Sweep on x keeps typical boards near O(n log n)."""
    n = len(rects)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    order = sorted(range(n), key=lambda i: rects[i][0])
    for a_pos, i in enumerate(order):
        ri = rects[i]
        for j in order[a_pos + 1:]:
            rj = rects[j]
            if rj[0] > ri[2] + tol:
                break
            if rj[1] <= ri[3] + tol and ri[1] <= rj[3] + tol:
                parent[find(i)] = find(j)
    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)
    return list(clusters.values())


def extract_pdf(path, source_sha):
    fitz = _load_fitz()
    method_text = {"extractor": "pymupdf", "method": "PDF_TEXT_LAYER"}
    method_img = {"extractor": "pymupdf", "method": "PDF_EMBEDDED_IMAGE"}
    method_vec = {"extractor": "pymupdf", "method": "PDF_VECTOR_CLUSTER"}
    method_page = {"extractor": "pymupdf", "method": "PDF_WHOLE_PAGE_FALLBACK"}
    doc = fitz.open(str(path))
    pages = []
    try:
        for index in range(doc.page_count):
            page = doc[index]
            page_no = index + 1
            rect = page.rect  # visual frame: rotation + cropbox applied, origin top-left, PDF points
            width, height = float(rect.width), float(rect.height)
            derot = page.derotation_matrix
            rot = page.rotation_matrix
            sink = RegionSink(page_no, width, height, "pt", source_sha)

            def visual_bbox(b):
                # PyMuPDF returns PDF object rectangles in unrotated coordinates;
                # only Page.rect uses the displayed (rotated) page frame.
                q = fitz.Rect(*b) * rot
                return (q.x0, q.y0, q.x1, q.y1)

            def unrotated(b):
                return {"bbox_unrotated_pdf_pt": native_bbox(*b)}

            # text layer
            for bi, block in enumerate(page.get_text("dict").get("blocks", [])):
                if block.get("type") != 0:
                    continue
                text = "\n".join("".join(span.get("text", "") for span in line.get("spans", []))
                                 for line in block.get("lines", [])).strip()
                if not text:
                    continue
                bb = block["bbox"]
                sink.add("TEXT", visual_bbox(bb), f"P{page_no}-TXT-{block.get('number', bi)}", method_text, 0.95, text=text,
                         native_ref={"text_block": block.get("number", bi)}, bbox_native_extra=unrotated(bb))
            # embedded images
            for ii, info in enumerate(page.get_image_info(xrefs=True)):
                bb = info["bbox"]
                sink.add("IMAGE", visual_bbox(bb), f"P{page_no}-IMG-{info.get('xref') or ii}-{ii}", method_img, 0.95,
                         native_ref={"xref": info.get("xref"), "pixel_width": info.get("width"), "pixel_height": info.get("height")},
                         bbox_native_extra=unrotated(bb))
            # vector drawings -> clusters (extent measured, meaning unknown)
            drawings = page.get_drawings()
            truncated = len(drawings) > MAX_DRAWINGS
            drawings = drawings[:MAX_DRAWINGS]
            tol = 0.004 * max(width, height)
            small = 0.5
            items = []
            skipped_background = 0
            for di, d in enumerate(drawings):
                r = fitz.Rect(d["rect"]) * rot
                x0, y0, x1, y1 = float(r.x0), float(r.y0), float(r.x1), float(r.y1)
                if (x1 - x0) * (y1 - y0) > 0.8 * width * height:
                    skipped_background += 1  # page-size frame/background would swallow every other drawing
                    continue
                if x1 - x0 < small:
                    x0, x1 = x0 - small / 2, x1 + small / 2
                if y1 - y0 < small:
                    y0, y1 = y0 - small / 2, y1 + small / 2
                items.append((di, (x0, y0, x1, y1)))
            if items:
                clusters = _union_find_clusters([r for _, r in items], tol)
                for ci, members in enumerate(sorted(clusters, key=lambda m: min(items[k][1][0] for k in m))):
                    rs = [items[k][1] for k in members]
                    bb = (min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs))
                    nb = norm_bbox(*bb, width, height)
                    if nb["w"] * nb["h"] < 1e-5 and len(members) < 3:
                        continue  # specks are not regions
                    ids = [f"P{page_no}-DRW-{items[k][0]}" for k in members]
                    sink.add("DRAWING", bb, f"P{page_no}-DRWC-{ci}", method_vec, 0.7,
                             native_ref={"primitive_count": len(ids), "primitive_ids": ids[:MAX_MEMBER_IDS]},
                             bbox_native_extra=unrotated(bb))
            if not sink.regions:
                sink.add("PAGE_UNKNOWN", (0.0, 0.0, width, height), f"P{page_no}-PAGE", method_page, 0.2,
                         extra={"needs_review": True, "needs_review_reason": "NO_NATIVE_OBJECTS_FOUND_ON_PAGE"})
            pages.append({
                "page_no": page_no, "width": width, "height": height, "unit": "pt", "rotation_deg": int(page.rotation),
                "coordinate_frame": "VISUAL_TOP_LEFT_ORIGIN_ROTATION_AND_CROPBOX_APPLIED",
                "mediabox": [round(v, 3) for v in tuple(page.mediabox)], "cropbox": [round(v, 3) for v in tuple(page.cropbox)],
                "box_note": "mediabox/cropbox as reported by PyMuPDF (unrotated page space)",
                "derotation_matrix": [round(v, 6) for v in tuple(derot)],
                "stats": {"drawing_count": len(drawings), "drawings_truncated": truncated,
                          "page_size_drawings_skipped": skipped_background},
                "regions": sink.regions,
            })
        version = getattr(fitz, "__version__", None) or getattr(fitz, "VersionBind", "unknown")
    finally:
        doc.close()
    return pages, {"name": "pymupdf", "version": str(version)}


# ---------------------------------------------------------------- PPTX (python-pptx)

def _group_transform(shape, parent):
    """child-space -> slide EMU affine (sx, sy, ox, oy) composed with the parent transform."""
    from pptx.oxml.ns import qn
    sx, sy, ox, oy = parent
    try:
        xfrm = shape._element.grpSpPr.find(qn("a:xfrm"))
        off, ext = xfrm.find(qn("a:off")), xfrm.find(qn("a:ext"))
        ch_off, ch_ext = xfrm.find(qn("a:chOff")), xfrm.find(qn("a:chExt"))
        gx, gy, gw, gh = (int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy")))
        cx, cy, cw, chh = (int(ch_off.get("x")), int(ch_off.get("y")), int(ch_ext.get("cx")), int(ch_ext.get("cy")))
        if not cw or not chh:
            return parent, "GROUP_CHILD_EXTENT_ZERO_IDENTITY_USED"
        lsx, lsy = gw / cw, gh / chh
        # point p in child space -> group space (g + (p-c)*l) -> parent transform
        nsx, nsy = sx * lsx, sy * lsy
        nox = ox + sx * (gx - cx * lsx)
        noy = oy + sy * (gy - cy * lsy)
        return (nsx, nsy, nox, noy), None
    except Exception as exc:  # BLOCKED != FAILED: keep the exact reason visible
        return parent, f"GROUP_TRANSFORM_UNRESOLVED:{type(exc).__name__}"


def _rotated_aabb(x, y, w, h, deg):
    import math
    if not deg:
        return x, y, x + w, y + h
    cx, cy, a = x + w / 2.0, y + h / 2.0, math.radians(deg)
    ew = abs(w * math.cos(a)) + abs(h * math.sin(a))
    eh = abs(w * math.sin(a)) + abs(h * math.cos(a))
    return cx - ew / 2.0, cy - eh / 2.0, cx + ew / 2.0, cy + eh / 2.0


def extract_pptx(path, source_sha, asset_dir=None):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    import pptx as pptx_mod
    method = {"extractor": "python-pptx", "method": "PPTX_NATIVE_SHAPE"}
    prs = Presentation(str(path))
    sw, sh = int(prs.slide_width), int(prs.slide_height)
    pages, native_groups = [], []
    if asset_dir:
        Path(asset_dir).mkdir(parents=True, exist_ok=True)
    for sno, slide in enumerate(prs.slides, 1):
        sink = RegionSink(sno, float(sw), float(sh), "EMU", source_sha)
        unresolved, group_notes = [], []

        def walk(shapes, tf, group_chain):
            for shp in shapes:
                try:
                    stype = shp.shape_type
                except NotImplementedError:
                    stype = None
                if stype == MSO_SHAPE_TYPE.GROUP:
                    child_tf, note = _group_transform(shp, tf)
                    if note:
                        group_notes.append({"shape_id": shp.shape_id, "note": note})
                    before = len(sink.regions)
                    walk(shp.shapes, child_tf, group_chain + [shp.shape_id])
                    members = [r["object_id"] for r in sink.regions[before:]]
                    if members:
                        native_groups.append({"page": sno, "native_group_shape_id": shp.shape_id, "name": shp.name,
                                              "member_object_ids": members})
                    continue
                if shp.left is None or shp.top is None or shp.width is None or shp.height is None:
                    unresolved.append({"shape_id": shp.shape_id, "name": shp.name, "reason": "INHERITED_POSITION_NOT_RESOLVED"})
                    continue
                sx, sy, ox, oy = tf
                x, y = ox + sx * int(shp.left), oy + sy * int(shp.top)
                w, h = sx * int(shp.width), sy * int(shp.height)
                rot = float(getattr(shp, "rotation", 0.0) or 0.0)
                x0, y0, x1, y1 = _rotated_aabb(x, y, w, h, rot)
                text = None
                if stype == MSO_SHAPE_TYPE.PICTURE:
                    kind = "IMAGE"
                elif getattr(shp, "has_table", False) and shp.has_table:
                    kind = "TABLE"
                    text = " | ".join(c.text for r in shp.table.rows for c in r.cells if c.text.strip())
                elif getattr(shp, "has_chart", False) and shp.has_chart:
                    kind = "CHART"
                elif getattr(shp, "has_text_frame", False) and shp.has_text_frame and shp.text_frame.text.strip():
                    kind = "TEXT"
                    text = shp.text_frame.text.strip()
                else:
                    kind = "SHAPE"
                if (x1 - x0) * (y1 - y0) > 0.9 * sw * sh and kind == "SHAPE":
                    continue  # full-slide background rectangle
                extra = {"rotation_deg": rot, "unrotated_frame_emu": {"x": round(x), "y": round(y), "w": round(w), "h": round(h)},
                         "group_chain": group_chain}
                ref = {"shape_id": shp.shape_id, "name": shp.name}
                if kind == "IMAGE":
                    try:
                        ref.update({"image_sha1": shp.image.sha1, "image_ext": shp.image.ext,
                                    "pixel_size": list(shp.image.size)})
                        if asset_dir:
                            fname = f"s{sno}-{shp.shape_id}.{shp.image.ext}"
                            (Path(asset_dir) / fname).write_bytes(shp.image.blob)
                            ref["asset"] = fname
                    except Exception as exc:
                        ref["image_error"] = type(exc).__name__
                sink.add(kind, (x0, y0, x1, y1), f"S{sno}-{shp.shape_id}", method, 1.0, text=text, native_ref=ref, extra=extra)

        walk(slide.shapes, (1.0, 1.0, 0.0, 0.0), [])
        if not sink.regions:
            sink.add("PAGE_UNKNOWN", (0.0, 0.0, float(sw), float(sh)), f"S{sno}-PAGE",
                     {"extractor": "python-pptx", "method": "PPTX_WHOLE_PAGE_FALLBACK"}, 0.2,
                     extra={"needs_review": True, "needs_review_reason": "NO_RESOLVABLE_SHAPES_ON_SLIDE"})
        pages.append({
            "page_no": sno, "width": float(sw), "height": float(sh), "unit": "EMU", "rotation_deg": 0,
            "coordinate_frame": "SLIDE_TOP_LEFT_ORIGIN", "mediabox": [0, 0, sw, sh], "cropbox": [0, 0, sw, sh],
            "derotation_matrix": [1, 0, 0, 1, 0, 0],
            "stats": {"unresolved_objects": unresolved, "group_transform_notes": group_notes},
            "regions": sink.regions,
        })
    return pages, {"name": "python-pptx", "version": str(getattr(pptx_mod, "__version__", "unknown"))}, native_groups


# ---------------------------------------------------------------- raster

def extract_image(path, source_sha):
    from PIL import Image, ImageOps
    with Image.open(str(path)) as im:
        exif_orientation = None
        try:
            exif_orientation = im.getexif().get(274)
        except Exception:
            pass
        upright = ImageOps.exif_transpose(im)
        width, height = upright.size
        dpi = im.info.get("dpi")
    sink = RegionSink(1, float(width), float(height), "px", source_sha)
    sink.add("IMAGE_PAGE_UNKNOWN", (0.0, 0.0, float(width), float(height)), "P1-IMGPAGE",
             {"extractor": "pillow", "method": "IMAGE_BOUND_WHOLE_PAGE"}, 0.2,
             extra={"needs_review": True, "needs_review_reason": "RASTER_SOURCE_NO_NATIVE_OBJECTS_OCR_VISION_HOLD"})
    page = {"page_no": 1, "width": float(width), "height": float(height), "unit": "px",
            "rotation_deg": {1: 0, 3: 180, 6: 270, 8: 90}.get(exif_orientation, 0),
            "coordinate_frame": "IMAGE_TOP_LEFT_ORIGIN_EXIF_UPRIGHT", "mediabox": [0, 0, width, height],
            "cropbox": [0, 0, width, height], "derotation_matrix": [1, 0, 0, 1, 0, 0],
            "dpi": list(dpi) if dpi else None, "exif_orientation": exif_orientation,
            "stats": {}, "regions": sink.regions}
    return [page], {"name": "pillow", "version": getattr(__import__("PIL"), "__version__", "unknown")}


# ---------------------------------------------------------------- groups + corrections

def propose_groups(pages, native_groups=None):
    """Many-to-many anchors: a group lists several primitives; a primitive may sit in several groups.

    AUTO_PROXIMITY: a non-text region plus the text blocks right below it (caption/legend candidates).
    NATIVE_GROUP:   PPTX group shapes as authored. Nothing is asserted about meaning (semantic_type UNKNOWN).
    """
    groups, n = [], 0
    for page in pages:
        regions = page["regions"]
        texts = [r for r in regions if r["kind"] == "TEXT"]
        others = [r for r in regions if r["kind"] not in ("TEXT",)]
        taken_captions = set()
        for r in others:
            rb = r["bbox_norm"]
            members = [r]
            for t in texts:
                if t["rect_id"] in taken_captions:
                    continue
                tb = t["bbox_norm"]
                gap = tb["y"] - (rb["y"] + rb["h"])
                overlap = min(rb["x"] + rb["w"], tb["x"] + tb["w"]) - max(rb["x"], tb["x"])
                if -0.005 <= gap <= 0.04 and tb["w"] > 0 and overlap / tb["w"] >= 0.5:
                    members.append(t)
                    taken_captions.add(t["rect_id"])
            n += 1
            groups.append(_group_record(f"G-AUTO-{n}", "AUTO_PROXIMITY", page["page_no"], members))
    by_obj = {r["object_id"]: r for p in pages for r in p["regions"]}
    for ng in native_groups or []:
        members = [by_obj[o] for o in ng["member_object_ids"] if o in by_obj]
        if members:
            n += 1
            rec = _group_record(f"G-NATIVE-{n}", "NATIVE_GROUP", ng["page"], members)
            rec["native_group_shape_id"] = ng["native_group_shape_id"]
            groups.append(rec)
    return groups


def _union_bbox(members):
    x0 = min(m["bbox_norm"]["x"] for m in members)
    y0 = min(m["bbox_norm"]["y"] for m in members)
    x1 = max(m["bbox_norm"]["x"] + m["bbox_norm"]["w"] for m in members)
    y1 = max(m["bbox_norm"]["y"] + m["bbox_norm"]["h"] for m in members)
    return {"x": round(x0, 6), "y": round(y0, 6), "w": round(x1 - x0, 6), "h": round(y1 - y0, 6)}


def _group_record(group_id, source, page_no, members):
    return {"group_id": group_id, "source": source, "page": page_no,
            "member_object_ids": [m["object_id"] for m in members], "member_rect_ids": [m["rect_id"] for m in members],
            "bbox_norm": _union_bbox(members), "semantic_type": "UNKNOWN", "label": "", "review_state": "PROPOSED"}


def apply_corrections(doc, corrections):
    """Apply saved human corrections. Source sha mismatch => STALE, nothing applied, remap candidates listed."""
    result = {"status": "NONE", "applied": 0, "stale": 0, "orphaned": [], "rejected": [], "remap_candidates": []}
    if not corrections:
        doc["corrections"] = result
        return doc
    items = corrections.get("corrections", []) if isinstance(corrections, dict) else []
    if not isinstance(corrections, dict) or corrections.get("version") != CORRECTIONS_VERSION:
        result.update({"status": "INVALID", "rejected": [{"reason": "BAD_VERSION"}]})
        doc["corrections"] = result
        return doc
    regions = {r["rect_id"]: r for p in doc["pages"] for r in p["regions"]}
    if corrections.get("source_sha256") != doc["source"]["sha256"]:
        result.update({"status": "STALE", "stale": len(items), "stale_for_sha256": corrections.get("source_sha256"),
                       "remap_candidates": [c.get("rect_id") for c in items if c.get("rect_id") in regions]})
        doc["corrections"] = result
        return doc
    allowed = set(semantic_types())
    human_groups = {}
    for c in items:
        region = regions.get(c.get("rect_id"))
        if region is None:
            result["orphaned"].append(c.get("rect_id"))
            continue
        stype = c.get("semantic_type", "UNKNOWN")
        if stype not in allowed:
            result["rejected"].append({"rect_id": c.get("rect_id"), "reason": "INVALID_SEMANTIC_TYPE:" + str(stype)})
            continue
        region["semantic_type"] = stype
        region["label"] = str(c.get("label") or "")
        region["ignored"] = bool(c.get("ignored"))
        region["review_state"] = "HUMAN_IGNORED" if region["ignored"] else "HUMAN_CORRECTED"
        gid = str(c.get("group_id") or "").strip()
        if gid and not region["ignored"]:
            human_groups.setdefault(gid, []).append(region)
        result["applied"] += 1
    for gid, members in human_groups.items():
        rec = _group_record("G-HUMAN-" + re.sub(r"[^A-Za-z0-9_-]", "_", gid), "HUMAN", members[0]["page"], members)
        types = [m["semantic_type"] for m in members if m["semantic_type"] != "UNKNOWN"]
        rec["semantic_type"] = types[0] if types else "UNKNOWN"
        rec["member_type_conflict"] = len(set(types)) > 1
        labels = [m["label"] for m in members if m["label"]]
        rec["label"] = labels[0] if labels else ""
        rec["review_state"] = "HUMAN_CORRECTED"
        moved = set(rec["member_rect_ids"])
        for g in doc["groups"]:
            if g["source"] != "HUMAN" and moved & set(g["member_rect_ids"]) and g["review_state"] == "PROPOSED":
                g["review_state"] = "SUPERSEDED_BY_HUMAN"
        doc["groups"] = [g for g in doc["groups"] if g["group_id"] != rec["group_id"]] + [rec]
    result["status"] = "APPLIED"
    doc["corrections"] = result
    return doc


# ---------------------------------------------------------------- top-level import

def import_source(source, out_dir, corrections_path=None, dpi=110):
    source = Path(source)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        raise SystemExit(f"SOURCE_NOT_FOUND:{source}")
    sha_before = sha256_file(source)
    suffix = source.suffix.lower()
    native_groups = []
    asset_dir = out_dir / "assets"
    if suffix == ".pdf":
        kind = "PDF"
        pages, extractor = extract_pdf(source, sha_before)
    elif suffix == ".pptx":
        kind = "PPTX"
        pages, extractor, native_groups = extract_pptx(source, sha_before, asset_dir)
    elif suffix in IMAGE_SUFFIX:
        kind = "IMAGE"
        pages, extractor = extract_image(source, sha_before)
    else:
        raise SystemExit(f"UNSUPPORTED_SOURCE_KIND:{suffix}")
    backgrounds = render_backgrounds(source, kind, pages, out_dir, dpi)
    doc = {
        "version": EXTRACT_VERSION, "ai_disclosure": DISCLOSURE,
        "source": {"path": str(source), "name": source.name, "kind": kind, "sha256": sha_before, "bytes": source.stat().st_size},
        "extractor": extractor, "semantic_types": semantic_types(), "pages": pages,
        "groups": propose_groups(pages, native_groups), "backgrounds": backgrounds,
        "imported_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hold": ["Raster OCR / vision-based block discovery is not implemented (whole-page UNKNOWN + NEEDS_REVIEW).",
                 "Semantic types are never inferred; they come only from saved human corrections."],
    }
    corrections = None
    if corrections_path:
        corrections = json.loads(Path(corrections_path).read_text(encoding="utf-8"))
    apply_corrections(doc, corrections)
    if backgrounds.get("error"):
        doc["hold"].append("BACKGROUND_RENDER_UNAVAILABLE:" + str(backgrounds["error"]))
    doc["source"]["sha256_after_import"] = sha256_file(source)
    doc["source"]["source_unchanged"] = doc["source"]["sha256_after_import"] == sha_before
    write_json(out_dir / "source-regions.json", doc)
    write_review_html(doc, out_dir / "review.html")
    return doc


def render_backgrounds(source, kind, pages, out_dir, dpi):
    """Page PNGs for the overlay. Failures are reported per page (BLOCKED != FAILED), never raised."""
    result = {}
    pages_dir = Path(out_dir) / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    if kind == "IMAGE":
        from PIL import Image, ImageOps
        dest = pages_dir / "page-1.png"
        try:
            with Image.open(str(source)) as im:
                ImageOps.exif_transpose(im).convert("RGB").save(str(dest))
            result[1] = {"file": "pages/page-1.png", "method": "PIL_COPY_UPRIGHT"}
        except (OSError, ValueError) as exc:
            dest.unlink(missing_ok=True)
            result["error"] = "IMAGE_RENDER_FAILED:" + type(exc).__name__
    elif kind == "PDF":
        try:
            fitz = _load_fitz()
            doc = fitz.open(str(source))
            try:
                for p in pages:
                    pix = doc[p["page_no"] - 1].get_pixmap(dpi=dpi)
                    pix.save(str(pages_dir / f"page-{p['page_no']}.png"))
                    result[p["page_no"]] = {"file": f"pages/page-{p['page_no']}.png", "method": f"PYMUPDF_PIXMAP_{dpi}DPI",
                                            "pixel_width": pix.width, "pixel_height": pix.height}
            finally:
                doc.close()
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {str(exc)[-300:]}"
    return result


# ---------------------------------------------------------------- review HTML

def write_review_html(doc, path):
    data = json.dumps({"doc": {k: doc[k] for k in ("version", "source", "extractor", "semantic_types", "pages", "groups",
                                                    "backgrounds", "corrections", "ai_disclosure")},
                       "corrections_version": CORRECTIONS_VERSION}, ensure_ascii=False).replace("</", "<\\/")
    Path(path).write_text(REVIEW_TEMPLATE.replace("__TITLE__", html.escape(doc["source"]["name"])).replace("__DATA__", data),
                          encoding="utf-8")


REVIEW_TEMPLATE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ARCHIGROW 소스 영역 검토 · __TITLE__</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:'Noto Sans KR','Malgun Gothic',Arial,sans-serif;font-size:13px;background:#e9e7e1;color:#151515}
header{background:#151515;color:#fff;padding:10px 16px}
header small{display:block;color:#cfcab8;margin-top:4px}
#banner{padding:8px 16px;font-weight:700}
#banner.stale{background:#f4d9d4;color:#7d2a22}
#banner.ok{background:#dcebdc;color:#25502b}
main{display:grid;grid-template-columns:minmax(360px,1fr) 520px;gap:12px;padding:12px;align-items:start}
.page{position:relative;background:#fff;border:1px solid #bbb;margin-bottom:12px;width:100%}
.page img.bg{position:absolute;inset:0;width:100%;height:100%;display:block}
.page .nobg{position:absolute;left:6px;top:4px;font-size:11px;color:#999}
.box{position:absolute;border:1.5px solid rgba(200,100,53,.85);cursor:pointer;overflow:hidden}
.box.k-TEXT{border-color:rgba(31,122,140,.9)}.box.k-IMAGE{border-color:rgba(90,60,160,.9)}.box.k-DRAWING{border-color:rgba(200,100,53,.9)}
.box.ign{opacity:.25}.box.sel{background:rgba(200,100,53,.28);border-width:3px}
.box.hv{background:rgba(31,122,140,.18)}
.box img{width:100%;height:100%;object-fit:fill;opacity:.55;pointer-events:none}
.box b{position:absolute;left:0;top:0;background:#c86435;color:#fff;font-size:10px;padding:0 3px}
section.side{background:#fff;border:1px solid #d7d4cb;padding:8px;position:sticky;top:8px;max-height:96vh;overflow:auto}
table{border-collapse:collapse;width:100%}
td,th{border-bottom:1px solid #eee;padding:3px 4px;text-align:left;vertical-align:top;font-size:12px}
tr.sel{background:#fbe9df}
td input[type=text]{width:84px}td select{max-width:110px}
.snip{color:#555;max-width:130px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
button{border:1px solid #151515;background:#fff;padding:5px 10px;cursor:pointer;margin:4px 4px 4px 0}
button.primary{background:#c86435;color:#fff;border-color:#c86435}
textarea{width:100%;height:120px;font-size:11px}
.hint{color:#555;font-size:11px;margin:4px 0}
</style></head><body>
<header><b>ARCHIGROW 소스 영역 검토</b> · __TITLE__<small id="disc"></small><small id="meta"></small></header>
<div id="banner"></div>
<main><div id="pages"></div>
<section class="side"><div class="hint">영역은 자동 제안일 뿐입니다. 의미 유형·그룹은 사람이 지정하고 "수정 저장(JSON 내보내기)"을 눌러야 기록됩니다. 같은 그룹 ID를 가진 영역은 하나의 의미 그룹이 됩니다.</div>
<button class="primary" id="exportBtn">수정 저장(JSON 내보내기)</button><button id="clearBtn">입력 초기화</button>
<table id="tbl"><thead><tr><th>#</th><th>종류</th><th>내용</th><th>의미 유형</th><th>라벨</th><th>그룹 ID</th><th>무시</th></tr></thead><tbody></tbody></table>
<div class="hint">내보내기 결과(원본 SHA 결합):</div><textarea id="exportOut" readonly></textarea></section></main>
<script id="data" type="application/json">__DATA__</script>
<script>
const P=JSON.parse(document.getElementById('data').textContent);const D=P.doc;
const $=id=>document.getElementById(id);
function el(t,c,x){const e=document.createElement(t);if(c)e.className=c;if(x!==undefined)e.textContent=x;return e}
const state={sel:null,edits:{}};
const regions=[];D.pages.forEach(p=>p.regions.forEach(r=>regions.push(r)));
regions.forEach((r,i)=>{r._no=i+1;
  if(r.review_state==='HUMAN_CORRECTED'||r.review_state==='HUMAN_IGNORED'){
    const g=D.groups.find(g=>g.source==='HUMAN'&&g.member_rect_ids.includes(r.rect_id));
    state.edits[r.rect_id]={semantic_type:r.semantic_type,label:r.label||'',group_id:g?g.group_id.replace(/^G-HUMAN-/,''):'',ignored:!!r.ignored}}});
function select(id,scroll){state.sel=id;render(false);if(scroll){const row=document.querySelector('tr[data-rect="'+id+'"]');if(row)row.scrollIntoView({block:'center'})}}
function touch(r,field,value){const e=state.edits[r.rect_id]||(state.edits[r.rect_id]={semantic_type:r.semantic_type,label:r.label||'',group_id:'',ignored:false});e[field]=value;render(false)}
function render(full){
  $('disc').textContent=D.ai_disclosure;
  $('meta').textContent='원본 '+D.source.name+' · '+D.source.kind+' · SHA256 '+D.source.sha256+' · 추출기 '+D.extractor.name+' '+D.extractor.version;
  const c=D.corrections||{status:'NONE'};const b=$('banner');
  if(c.status==='STALE'){b.className='stale';b.textContent='저장된 수정이 STALE입니다: 원본 SHA가 달라져 적용하지 않았습니다 ('+c.stale+'건). 재매핑 후보 '+c.remap_candidates.length+'건을 확인하세요.'}
  else if(c.status==='APPLIED'){b.className='ok';b.textContent='저장된 수정 '+c.applied+'건 적용됨 (고아 '+c.orphaned.length+'건, 거부 '+c.rejected.length+'건)'}
  else{b.className='';b.textContent='저장된 수정 없음 — 모든 영역은 UNKNOWN / PROPOSED 상태입니다.'}
  if(full){const pg=$('pages');pg.textContent='';
    D.pages.forEach(p=>{const w=el('div','page');w.dataset.page=p.page_no;w.style.aspectRatio=p.width+' / '+p.height;
      const bg=(D.backgrounds||{})[p.page_no];
      if(bg&&bg.file){const im=el('img','bg');im.src=bg.file;im.alt='page '+p.page_no;w.appendChild(im)}else w.appendChild(el('div','nobg','배경 렌더 없음(영역 윤곽만 표시)'));
      p.regions.forEach(r=>{const n=r.bbox_norm;const bx=el('div','box k-'+r.kind);bx.dataset.rect=r.rect_id;
        bx.style.left=(Math.max(0,n.x)*100)+'%';bx.style.top=(Math.max(0,n.y)*100)+'%';bx.style.width=(Math.min(1,n.w)*100)+'%';bx.style.height=(Math.min(1,n.h)*100)+'%';
        if(r.native_ref&&r.native_ref.asset){const im=el('img');im.src='assets/'+r.native_ref.asset;bx.appendChild(im)}
        bx.appendChild(el('b',null,String(r._no)));bx.onclick=()=>select(r.rect_id,true);w.appendChild(bx)});
      pg.appendChild(w)})}
  document.querySelectorAll('.box').forEach(bx=>{const e=state.edits[bx.dataset.rect];bx.classList.toggle('sel',bx.dataset.rect===state.sel);bx.classList.toggle('ign',!!(e&&e.ignored))});
  const tb=document.querySelector('#tbl tbody');tb.textContent='';
  regions.forEach(r=>{const e=state.edits[r.rect_id]||{semantic_type:r.semantic_type,label:r.label||'',group_id:'',ignored:false};
    const tr=el('tr',r.rect_id===state.sel?'sel':'');tr.dataset.rect=r.rect_id;
    tr.appendChild(el('td',null,String(r._no)));tr.appendChild(el('td',null,r.kind+(r.needs_review?' ⚠':'')));
    tr.appendChild(el('td','snip',r.text?r.text.replace(/\s+/g,' '):(r.needs_review_reason||r.object_id)));
    const td3=el('td');const sel=el('select');D.semantic_types.forEach(t=>{const o=el('option',null,t);o.value=t;if(t===e.semantic_type)o.selected=true;sel.appendChild(o)});
    sel.onchange=()=>touch(r,'semantic_type',sel.value);td3.appendChild(sel);tr.appendChild(td3);
    const td4=el('td');const li=el('input');li.type='text';li.value=e.label;li.onchange=()=>touch(r,'label',li.value);td4.appendChild(li);tr.appendChild(td4);
    const td5=el('td');const gi=el('input');gi.type='text';gi.value=e.group_id;gi.onchange=()=>touch(r,'group_id',gi.value);td5.appendChild(gi);tr.appendChild(td5);
    const td6=el('td');const ci=el('input');ci.type='checkbox';ci.checked=e.ignored;ci.onchange=()=>touch(r,'ignored',ci.checked);td6.appendChild(ci);tr.appendChild(td6);
    tr.onclick=ev=>{if(ev.target.tagName==='TR'||ev.target.tagName==='TD')select(r.rect_id,false)};tb.appendChild(tr)})}
function exportCorrections(){
  const out={version:P.corrections_version,source_sha256:D.source.sha256,source_name:D.source.name,
    exported_at:new Date().toISOString(),review_state:'HUMAN_CORRECTED',corrections:[]};
  regions.forEach(r=>{const e=state.edits[r.rect_id];if(!e)return;
    out.corrections.push({rect_id:r.rect_id,object_id:r.object_id,page:r.page,semantic_type:e.semantic_type,label:e.label,group_id:e.group_id,ignored:!!e.ignored,review_state:'HUMAN_CORRECTED'})});
  const text=JSON.stringify(out,null,2);$('exportOut').value=text;return out}
$('exportBtn').onclick=()=>{const out=exportCorrections();
  const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);a.download='corrections-'+D.source.sha256.slice(0,12)+'.json';document.body.appendChild(a);a.click();a.remove()};
$('clearBtn').onclick=()=>{state.edits={};$('exportOut').value='';render(false)};
window.PANEL_SOURCE_REVIEW={state,regions,select,touch,exportCorrections,data:D};
render(true);
</script></body></html>
"""


# ---------------------------------------------------------------- bridge to the panel workflow

def export_panel_blocks(doc_or_path, out_dir, page=1):
    """panel-blocks.json for ARCHIGROW_PANEL_WORKFLOW (recompose) from HUMAN-labelled groups of one page only.

    Auto proposals are never exported: a block needs a human-assigned drawing mode. The original source stays untouched;
    source_sha256 is the sha256 of the ORIGINAL file, crop_path is a derived region image when a page render exists.
    """
    out_dir = Path(out_dir)
    doc = json.loads(Path(doc_or_path).read_text(encoding="utf-8")) if not isinstance(doc_or_path, dict) else doc_or_path
    modes = set(drawing_modes())
    pg = next((p for p in doc["pages"] if p["page_no"] == page), None)
    if pg is None:
        raise SystemExit(f"PAGE_NOT_FOUND:{page}")
    backgrounds = doc.get("backgrounds") or {}
    bg = backgrounds.get(page) or backgrounds.get(str(page))  # int keys in memory, str keys after JSON round trip
    blocks, counters = [], {}
    for g in doc["groups"]:
        if g["source"] != "HUMAN" or g["page"] != page or g["semantic_type"] not in modes or g.get("member_type_conflict"):
            continue
        mode = g["semantic_type"]
        counters[mode] = counters.get(mode, 0) + 1
        block_id = f"{mode}:{counters[mode]}"
        crop_path = None
        if bg and bg.get("file") and (out_dir / bg["file"]).exists():
            from PIL import Image
            with Image.open(str(out_dir / bg["file"])) as im:
                n = g["bbox_norm"]
                box = (max(0, int(n["x"] * im.width)), max(0, int(n["y"] * im.height)),
                       min(im.width, int((n["x"] + n["w"]) * im.width) + 1), min(im.height, int((n["y"] + n["h"]) * im.height) + 1))
                if box[2] > box[0] and box[3] > box[1]:
                    crop_file = out_dir / "crops" / (re.sub(r"[^A-Za-z0-9_-]", "_", block_id) + ".png")
                    crop_file.parent.mkdir(parents=True, exist_ok=True)
                    im.convert("RGB").crop(box).save(str(crop_file))
                    crop_path = str(crop_file)
        blocks.append({
            "block_id": block_id, "order": len(blocks) + 1, "mode": mode, "stage": None, "role": None,
            "title_ko": g["label"] or mode, "question": None, "source_required": None,
            "source_path": doc["source"]["path"], "source_exists": True, "source_kind": doc["source"]["kind"],
            "source_sha256": doc["source"]["sha256"], "binding_status": "BOUND",
            "board_anchor": g["group_id"], "board_position": len(blocks) + 1, "board_link": f"review.html#{g['group_id']}",
            "board_rect_norm": g["bbox_norm"], "rect_method": f"SOURCE_EXTRACT:{doc['extractor']['name']}:HUMAN_GROUP",
            "source_page": page, "member_object_ids": g["member_object_ids"], "crop_path": crop_path,
            "semantic_state": "HUMAN_CORRECTED",
        })
    unit_mm = {"pt": 25.4 / 72.0, "px": 25.4 / 96.0, "EMU": 1.0 / 36000.0}.get(pg["unit"], 1.0)
    review = out_dir / "review.html"
    panel = {
        "version": "ARCHIGROW_PANEL_BLOCKS_V1",
        "board": {
            "style_id": "SOURCE_EXTRACT_REVIEW", "style_label": "소스 추출 검토 보드", "style_intent": "Human-reviewed regions of an imported source.",
            "title": Path(doc["source"]["name"]).stem, "delivery": "A1_BOARD",
            "width_mm": round(pg["width"] * unit_mm, 2), "height_mm": round(pg["height"] * unit_mm, 2),
            "html": "review.html", "html_sha256": sha256_file(review) if review.exists() else None, "pdf": None, "pdf_sha256": None,
            "manifest_status": "SOURCE_EXTRACT_HUMAN_REVIEWED" if blocks else "SOURCE_EXTRACT_NO_HUMAN_LABELLED_BLOCKS",
            "demo_sources": False, "stage_labels": [],
        },
        "segmentation": {"method": "SOURCE_EXTRACT_HUMAN_REVIEWED",
                         "note": "Rects are measured from the native source (not authored by this generator); meaning comes from human labels."},
        "ai_disclosure": DISCLOSURE,
        "source_gaps": [], "blocks": blocks,
    }
    write_json(out_dir / "panel-blocks.json", panel)
    return panel


# ---------------------------------------------------------------- CLI

def main():
    p = argparse.ArgumentParser(description="ARCHIGROW panel source extractor (native PDF / PPTX / raster).")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("import", help="Extract located regions + review HTML. Source file is only read.")
    i.add_argument("--source", required=True)
    i.add_argument("--out-dir", required=True)
    i.add_argument("--corrections", default="", help="saved corrections JSON exported from review.html")
    i.add_argument("--dpi", type=int, default=110)
    i.add_argument("--export-blocks", action="store_true", help="also write panel-blocks.json from HUMAN-labelled groups")
    i.add_argument("--page", type=int, default=1)
    args = p.parse_args()
    doc = import_source(args.source, args.out_dir, args.corrections or None, args.dpi)
    if args.export_blocks:
        export_panel_blocks(doc, args.out_dir, args.page)
    summary = {
        "source": doc["source"]["name"], "sha256": doc["source"]["sha256"], "source_unchanged": doc["source"]["source_unchanged"],
        "extractor": doc["extractor"], "pages": [{"page": pg["page_no"], "regions": len(pg["regions"])} for pg in doc["pages"]],
        "groups": len(doc["groups"]), "corrections": doc["corrections"]["status"],
        "review_html": str(Path(args.out_dir) / "review.html"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
