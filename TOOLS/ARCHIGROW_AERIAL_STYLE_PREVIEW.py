#!/usr/bin/env python3
"""ARCHI-D5 styled-output preview: SYNTHETIC fixture only, NOT a real aerial image.

render(): SVG footprints -> base raster -> mask-constrained styled candidate PNG.
verify(): re-reads candidate RGB pixels, derives its own building mask by a fixed color rule,
          then delegates all geometry metrics to ARCHIGROW_AERIAL_RASTER_QA.evaluate.
"""
import argparse, hashlib, importlib.util, json, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw

BANNER = "ILLUSTRATIVE SYNTHETIC / NOT REAL AERIAL"
DISCLAIMER = ("Styled texture over supplied synthetic footprints; no inference about real roofs, ground cover, "
              "or aerial imagery. Real project aerial and real drone photo: NOT VERIFIED.")
METHOD = "ROOF_VS_GREEN_FIELD_RGB_RULE_v1"
RULE = "field iff (G-R>=10 and G-B>=10); building = not field; 4-connected components; min_area=0 (extras HOLD)"
SEED = 20261031
SIZE = 800
_NUM = r"-?\d+(?:\.\d+)?"
_TOK = re.compile(r"[\s,]*(?:([MLZ])|(%s))" % _NUM)
ROOFS = [(168, 92, 78), (100, 100, 112), (172, 170, 164)]
BG = (232, 236, 233)
_QA = Path(__file__).with_name("ARCHIGROW_AERIAL_RASTER_QA.py")


def _qa():
    s = importlib.util.spec_from_file_location("archigrow_aerial_raster_qa", _QA)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _poly(d):
    """Strict single-subpath 'M x,y L x,y ... Z' parser; anything else raises ValueError."""
    pos, cmds, nums = 0, [], []
    d = d.strip()
    while pos < len(d):
        m = _TOK.match(d, pos)
        if not m:
            raise ValueError("unsupported path data at %d: %r" % (pos, d[pos:pos + 12]))
        pos = m.end()
        if m.group(1): cmds.append((m.group(1), len(nums)))
        else: nums.append(float(m.group(2)))
    letters = [c for c, _ in cmds]
    if not letters or letters[0] != "M" or letters[-1] != "Z" or letters.count("M") != 1 or letters.count("Z") != 1:
        raise ValueError("path must be one M..L..Z subpath")
    pts = nums
    if len(pts) % 2 or len(pts) < 6 or len(pts) // 2 != len(letters) - 1:
        raise ValueError("path needs one coordinate pair per M/L and at least 3 points")
    return [(pts[i], pts[i + 1]) for i in range(0, len(pts), 2)]


def parse_svg(svg_path):
    raw = Path(svg_path).read_bytes()
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise ValueError("DOCTYPE/ENTITY rejected")
    root = ET.fromstring(raw)
    vb = [float(v) for v in re.split(r"[ ,]+", root.get("viewBox", "").strip())] if root.get("viewBox") else []
    if len(vb) != 4 or vb[0] != 0 or vb[1] != 0 or vb[2] != vb[3] or vb[2] <= 0:
        raise ValueError("viewBox must be square and origin-anchored")
    ns = "{http://www.w3.org/2000/svg}"
    groups = [g for g in root.iter(ns + "g") if g.get("id") == "buildings"]
    if len(groups) != 1:
        raise ValueError("expected exactly one g#buildings")
    polys = []
    for el in groups[0]:
        if el.tag != ns + "path":
            raise ValueError("unsupported element in buildings: %s" % el.tag)
        pts = _poly(el.get("d", ""))
        if any(not (0 <= x <= vb[2] and 0 <= y <= vb[3]) for x, y in pts):
            raise ValueError("footprint outside viewBox")
        polys.append(pts)
    if not polys:
        raise ValueError("no building footprints")
    return polys, vb[2]


def _base_mask(polys, extent):
    m = Image.new("L", (SIZE, SIZE), 0)
    dr, k = ImageDraw.Draw(m), SIZE / extent
    for i, p in enumerate(polys, 1):
        dr.polygon([(x * k, y * k) for x, y in p], fill=i)
    return np.array(m)


def _style(mask):
    rng = np.random.default_rng(SEED)
    noise = rng.integers(-5, 6, (SIZE, SIZE)).astype(np.int16)[..., None]
    img = np.empty((SIZE, SIZE, 3), np.int16)
    img[:] = (96, 134, 92)
    bld = mask > 0
    shadow = np.roll(bld, (5, 5), (0, 1)) & ~bld  # ground only; never touches footprints
    img[shadow] = (img[shadow] * 0.75).astype(np.int16)
    xs = np.arange(SIZE)[None, :, None] % 16
    for lab in np.unique(mask[bld]):
        sel = mask == lab
        img[sel] = np.array(ROOFS[int(lab) % 3]) + (xs[0, :, 0][np.nonzero(sel)[1]] < 2)[:, None] * -14  # ridge lines
    # 1px field-coloured joint where distinct footprint labels abut (source footprints 10/18 overlap)
    seam = np.zeros(bld.shape, bool)
    for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1)):
        nb = np.roll(mask, sh, ax)
        seam |= bld & (nb > 0) & (nb != mask) & (mask < nb)
    img[seam] = (96, 134, 92)
    return np.clip(img + noise, 0, 255).astype(np.uint8)


def render(svg_path, out_dir):
    polys, extent = parse_svg(svg_path)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    mask = _base_mask(polys, extent)
    if len(np.unique(mask)) - 1 != len(polys):
        raise ValueError("footprints overlap or vanish when rasterised")
    base = np.empty((SIZE, SIZE, 3), np.uint8); base[:] = BG; base[mask > 0] = (183, 196, 197)
    cand = _style(mask)
    P = {k: out / v for k, v in dict(base_image="site_map_base.png", candidate_image="styled_preview.png",
                                       base_mask="base_mask.png", candidate_mask="candidate_mask.png",
                                       comparison="comparison.png", receipt="receipt.json").items()}
    Image.fromarray(base).save(P["base_image"]); Image.fromarray(mask, "L").save(P["base_mask"])
    Image.fromarray(cand).save(P["candidate_image"])
    side = Image.new("RGB", (2 * SIZE, SIZE + 24), (255, 255, 255))
    side.paste(Image.fromarray(base), (0, 24)); side.paste(Image.fromarray(cand), (SIZE, 24))
    ImageDraw.Draw(side).text((6, 6), BANNER + "  |  left: base footprints  right: styled (mask-constrained)", fill=(160, 0, 0))
    side.save(P["comparison"])
    return P, len(polys)


def extract_mask(cand_path, base_mask):
    """Derive labelled building mask from candidate RGB only; base labels used solely to name regions."""
    with Image.open(cand_path) as im:
        rgb = np.array(im.convert("RGB"), np.int16)
    field = ((rgb[..., 1] - rgb[..., 0]) >= 10) & ((rgb[..., 1] - rgb[..., 2]) >= 10)
    n, cc = cv2.connectedComponents((~field).astype(np.uint8), connectivity=4)
    out, holds, seen = np.zeros(cc.shape, np.uint8), [], {}
    for c in range(1, n):
        reg = cc == c
        labs = [int(v) for v in np.unique(base_mask[reg]) if v]
        if not labs: holds.append("EXTRA_REGION:%d" % c)
        elif len(labs) > 1: holds.append("MERGED_REGION:%s" % labs)
        else:
            seen.setdefault(labs[0], []).append(c)
            out[reg] = labs[0]
    for lab in (int(v) for v in np.unique(base_mask) if v):
        k = len(seen.get(lab, []))
        if k != 1: holds.append("OBJECT_%d_REGIONS:%d" % (lab, k))
    return out, holds


def verify(P, source_svg, n_expected):
    base_mask = np.array(Image.open(P["base_mask"]))
    cm, holds = extract_mask(P["candidate_image"], base_mask)
    rec = {"schema": "archigrow.aerial_style_preview.receipt.v1", "banner": BANNER, "disclaimer": DISCLAIMER,
           "provenance": "SYNTHETIC_URBAN_BLOCK_01 owned fixture only", "real_aerial_status": "NOT_VERIFIED",
           "real_drone_photo_status": "NOT_VERIFIED", "source_svg": str(source_svg), "source_sha256": sha(source_svg),
           "footprint_count": n_expected, "seed": SEED, "segmentation": {"method": METHOD, "rule": RULE},
           "extraction_holds": holds, "styling_note": "1px joint seam drawn where abutting footprints touch", "status": "HOLD", "qa": None}
    Image.fromarray(cm, "L").save(P["candidate_mask"])
    if not holds:
        man = {k: P[k].name for k in ("base_image", "candidate_image", "base_mask", "candidate_mask")}
        man["provenance"] = {"rights_basis": "owner-authored synthetic fixture",
                             "attestation": "SYNTHETIC_URBAN_BLOCK_01; not a real aerial"}
        man["output_mask_extraction_attestation"] = "%s from candidate RGB (independent of base mask)" % METHOD
        rec["qa"] = _qa().evaluate(man, P["receipt"].parent)
        rec["status"] = rec["qa"]["status"]
    rec["files"] = {k: {"path": str(p), "sha256": sha(p)} for k, p in P.items() if k != "receipt" and p.exists()}
    P["receipt"].write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")
    return rec


def run(svg_path, out_dir):
    P, n = render(svg_path, out_dir)
    return verify(P, svg_path, n)


# ---- PHOTO mode: strict pixelwise tone correction of a supplied real photograph (no spatial operation) ----
PHOTO_MODE = "PHOTO_PIXELWISE_TONE_ONLY"
PHOTO_PROOF = "PIXELWISE_TRANSFORM_VERIFIED"
PHOTO_TRANSFORM = ("per-pixel integer: L=(299R+587G+114B)//1000; c=L+(c-L)*118//100 (saturation x1.18); "
                   "c=clip((c-118)*115//100+118,0,255) (contrast x1.15 about 118)")
PHOTO_DISCLAIMERS = ["NOT_REAL_IMAGE_GEOMETRY_PROOF", "NOT_GENERATIVE_PHOTO", "NO_REAL_DRONE_TRUTH",
                     "NOT_FINISHED_PRODUCT", "NOT_MAP_TO_PHOTOREAL_CONVERSION"]
_RECEIPT_KEYS = ("source", "service", "bytes", "sha256", "image_size", "rights_basis")
_SCHEMA = "archigrow.aerial_style_preview.photo_receipt.v1"


def _tone_scalar(r, g, b):
    """Reference transform for ONE pixel (pure Python ints) - used by the independent read-back."""
    lum = (299 * r + 587 * g + 114 * b) // 1000
    out = []
    for c in (r, g, b):
        c = min(255, max(0, lum + (c - lum) * 118 // 100))
        out.append(min(255, max(0, (c - 118) * 115 // 100 + 118)))
    return tuple(out)


def _tone_vector(rgb):
    """Fast whole-image implementation of the same transform (writer path)."""
    a = rgb.astype(np.int32)
    lum = (299 * a[..., 0] + 587 * a[..., 1] + 114 * a[..., 2]) // 1000
    a = np.clip(lum[..., None] + (a - lum[..., None]) * 118 // 100, 0, 255)
    return np.clip((a - 118) * 115 // 100 + 118, 0, 255).astype(np.uint8)


def _expected_per_pixel(rgb):
    """Recompute the expected output for every pixel (scalar reference applied per distinct colour)."""
    flat = rgb.reshape(-1, 3).astype(np.int64)
    packed = (flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]
    uniq, inv = np.unique(packed, return_inverse=True)
    table = np.array([_tone_scalar(int(v) >> 16, (int(v) >> 8) & 255, int(v) & 255) for v in uniq], np.uint8)
    return table[inv.reshape(-1)].reshape(rgb.shape)


def _load_rgb(path):
    """Open a supported photo (JPEG/PNG) as RGB; any other format raises ValueError."""
    with Image.open(path) as im:
        if im.format not in ("JPEG", "PNG"):
            raise ValueError("unsupported source format: %r" % im.format)
        return np.array(im.convert("RGB")), im.format


def check_source_receipt(src, receipt_path):
    """Return (receipt|None, holds). Missing/invalid receipt or SHA/byte mismatch -> holds."""
    try:
        rc = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        raw = Path(src).read_bytes()
    except (OSError, ValueError) as e:
        return None, ["INPUT_UNREADABLE:%s" % type(e).__name__]
    if not isinstance(rc, dict):
        return None, ["RECEIPT_NOT_OBJECT"]
    holds = ["RECEIPT_FIELD_MISSING:%s" % k for k in _RECEIPT_KEYS if not rc.get(k)]
    if rc.get("sha256") and rc["sha256"] != hashlib.sha256(raw).hexdigest(): holds.append("SOURCE_SHA256_MISMATCH")
    if rc.get("bytes") and rc["bytes"] != len(raw): holds.append("SOURCE_BYTES_MISMATCH")
    return rc, holds


def verify_photo(src, out_png, receipt_path, rec_path=None):
    """Independent read-back: reopen original + saved PNG, recompute the expected output per pixel, require zero residual."""
    rc, holds = check_source_receipt(src, receipt_path)
    rec = {"schema": _SCHEMA, "mode": PHOTO_MODE, "transform": PHOTO_TRANSFORM, "proof_label": None, "status": "HOLD",
           "holds": holds, "disclaimers": PHOTO_DISCLAIMERS, "source_file": str(src), "source_receipt": rc,
           "attribution": (rc or {}).get("rights_basis"), "result_file": str(out_png), "result_sha256": None,
           "max_pixel_residual": None, "changed_pixel_fraction": None, "residual_pixel_count": None,
           "scope_note": "Proves only that the saved PNG equals the declared pixelwise tone transform of the source; "
                         "nothing about real geometry, drone truth or generative realism."}
    try:
        rec["source_sha256"] = sha(src)
        a, rec["source_format"] = _load_rgb(src)
        rec["result_sha256"] = sha(out_png)
        with Image.open(out_png) as im:
            if im.format != "PNG" or im.mode != "RGB": holds.append("RESULT_NOT_RGB_PNG:%s/%s" % (im.format, im.mode))
            b = np.array(im.convert("RGB"))
        if rc and list(rc.get("image_size") or []) != [a.shape[1], a.shape[0]]: holds.append("RECEIPT_SIZE_MISMATCH")
        if a.shape != b.shape:
            holds.append("SIZE_CHANGED:%s->%s" % (a.shape[:2], b.shape[:2]))
        else:
            res = np.abs(_expected_per_pixel(a).astype(np.int16) - b.astype(np.int16)).max(axis=2)
            rec["max_pixel_residual"], rec["residual_pixel_count"] = int(res.max()), int(np.count_nonzero(res))
            rec["changed_pixel_fraction"] = float(np.count_nonzero((a != b).any(axis=2)) / (a.shape[0] * a.shape[1]))
            if rec["max_pixel_residual"] != 0: holds.append("PIXEL_RESIDUAL_NONZERO:%d" % rec["residual_pixel_count"])
    except (OSError, ValueError) as e:
        holds.append("READBACK_FAILED:%s:%s" % (type(e).__name__, e))
    if not holds:
        rec["status"], rec["proof_label"] = "PROVISIONAL", PHOTO_PROOF
    if rec_path:
        Path(rec_path).write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")
    return rec


def run_photo(src, out_dir, receipt_path):
    """Write photo_enhanced.png, photo_comparison.png, photo_receipt.json into out_dir; the source is never modified."""
    out = Path(out_dir)
    _, holds = check_source_receipt(src, receipt_path)
    if holds:  # fail closed before producing any image
        out.mkdir(parents=True, exist_ok=True)
        rec = {"schema": _SCHEMA, "mode": PHOTO_MODE, "status": "HOLD", "holds": holds,
               "disclaimers": PHOTO_DISCLAIMERS, "source_file": str(src)}
        (out / "photo_receipt.json").write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")
        return rec
    a, _fmt = _load_rgb(src)  # unsupported format raises ValueError -> CLI HOLD exit 2
    out.mkdir(parents=True, exist_ok=True)
    b = _tone_vector(a)
    Image.fromarray(b).save(out / "photo_enhanced.png")
    h, w = a.shape[:2]
    side = Image.new("RGB", (2 * w, h + 24), (255, 255, 255))
    side.paste(Image.fromarray(a), (0, 24)); side.paste(Image.fromarray(b), (w, 24))
    ImageDraw.Draw(side).text((6, 6), "PUBLIC-DOMAIN USGS NAIP, tone-only (no geometry change) | left: original  right: enhanced",
                              fill=(160, 0, 0))
    side.save(out / "photo_comparison.png")
    return verify_photo(src, out / "photo_enhanced.png", receipt_path, out / "photo_receipt.json")


def main(argv=None):
    ap = argparse.ArgumentParser(description=BANNER)
    ap.add_argument("--photo", nargs=2, metavar=("SOURCE_IMAGE", "OUT_DIR"))
    ap.add_argument("--source-receipt")
    ap.add_argument("svg", nargs="?"); ap.add_argument("out", nargs="?")
    a = ap.parse_args(argv)
    if a.photo:
        if not a.source_receipt or a.svg or a.out:
            print("실패: --photo SOURCE_IMAGE OUT_DIR requires --source-receipt and no SVG args", file=sys.stderr)
            return 2
        try:
            rec = run_photo(a.photo[0], a.photo[1], a.source_receipt)
        except (OSError, ValueError) as e:
            print("실패: %s: %s" % (type(e).__name__, e), file=sys.stderr)
            return 2
        print("%s | status=%s | holds=%s | max_residual=%s" % (PHOTO_MODE, rec["status"], rec["holds"], rec.get("max_pixel_residual")))
        return 0 if rec["status"] == "PROVISIONAL" else 1
    if not (a.svg and a.out):
        ap.error("svg and out are required unless --photo is used")
    try:
        rec = run(a.svg, a.out)
    except (OSError, ValueError, ET.ParseError) as e:
        print("실패: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    print("%s | status=%s | holds=%s" % (BANNER, rec["status"], rec["extraction_holds"]))
    return 0 if rec["status"] == "PROVISIONAL" else 1


if __name__ == "__main__":
    sys.exit(main())
