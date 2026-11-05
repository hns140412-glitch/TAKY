#!/usr/bin/env python3
"""ARCHIGROW aerial raster QA: offline, fail-closed comparison of independently supplied
semantic integer-label masks (base vs AI-candidate). Evidence class: MASK_COMPARISON_ONLY /
NOT_REAL_IMAGE_GEOMETRY_PROOF. Masks are never inferred from RGB; a copied mask does not certify
AI-rendered pixels. Status is only HOLD or PROVISIONAL (never PASS).

Manifest JSON (paths relative to the manifest file):
{"schema":"archigrow.aerial_raster_qa.v1",
 "provenance":{"rights_basis":"<nonempty>","attestation":"<nonempty>"},
 "base_image":"a.png","candidate_image":"b.png","base_mask":"am.png","candidate_mask":"bm.png",
 "thresholds":{"min_iou":0.95,"max_pixel_delta_ratio":0.02,"max_centroid_px":2.0,"max_bbox_px":2},
 "output_mask_extraction_attestation":"<optional; recorded only, still PROVISIONAL>"}
Masks: 8-bit L/P images, 0=background, 1..254=object identity. Usage: manifest [--output receipt.json]
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

EVIDENCE = "MASK_COMPARISON_ONLY / NOT_REAL_IMAGE_GEOMETRY_PROOF"
DEFAULTS = {"min_iou": 0.95, "max_pixel_delta_ratio": 0.02, "max_centroid_px": 2.0, "max_bbox_px": 2}
KEYS = ("base_image", "candidate_image", "base_mask", "candidate_mask")


def _thresholds(raw):
    """Return (effective thresholds, reasons). Overrides may only tighten DEFAULTS; anything else is invalid."""
    if raw is None:
        return dict(DEFAULTS), []
    if not isinstance(raw, dict):
        return None, ["THRESHOLD_INVALID:not_object"]
    bad = ["THRESHOLD_INVALID:unknown_key:%s" % k for k in raw if k not in DEFAULTS]
    th = dict(DEFAULTS)
    for k, default in DEFAULTS.items():
        if k not in raw:
            continue
        v = raw[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            bad.append("THRESHOLD_INVALID:type_or_nonfinite:%s" % k)
        elif k == "min_iou":
            if not (default <= v <= 1.0):
                bad.append("THRESHOLD_INVALID:loosened_or_out_of_bounds:%s" % k)
            else:
                th[k] = float(v)
        elif not (0 <= v <= default):
            bad.append("THRESHOLD_INVALID:loosened_or_out_of_bounds:%s" % k)
        else:
            th[k] = float(v)
    return (None if bad else th), bad


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p, mask):
    with Image.open(p) as im:
        if mask:
            if im.mode not in ("L", "P"):
                raise ValueError("mask mode %s not integer-label (L/P)" % im.mode)
            return np.array(im, dtype=np.int64), im.size
        im.load()
        return None, im.size


def _stats(m, k):
    ys, xs = np.nonzero(m == k)
    return {"pixels": int(xs.size), "centroid": [float(xs.mean()), float(ys.mean())],
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]}


def evaluate(manifest, base_dir="."):
    base_dir = Path(base_dir)
    r = {"schema": "archigrow.aerial_raster_qa.receipt.v1", "evidence_class": EVIDENCE,
         "status": "HOLD", "reasons": [], "hashes": {}, "objects": {}, "real_output_pass": False}
    hold = r["reasons"].append
    if not isinstance(manifest, dict):
        hold("MANIFEST_INVALID")
        return r
    prov = manifest.get("provenance")
    if not isinstance(prov, dict) or not all(isinstance(prov.get(k), str) and prov[k].strip()
                                             for k in ("rights_basis", "attestation")):
        hold("PROVENANCE_UNVERIFIED")
    th, bad = _thresholds(manifest.get("thresholds"))
    if bad:
        r["reasons"].extend(bad)
        return r
    r["thresholds"] = th
    ext = manifest.get("output_mask_extraction_attestation")
    r["output_mask_extraction_attested"] = bool(isinstance(ext, str) and ext.strip())
    data, sizes = {}, {}
    for k in KEYS:
        try:
            p = base_dir / str(manifest[k])
            r["hashes"][k] = _sha(p)
            data[k], sizes[k] = _load(p, k.endswith("mask"))
        except Exception as e:
            hold("INPUT_UNREADABLE:%s:%s" % (k, type(e).__name__))
    if len(data) < 4:
        return r
    if len(set(sizes.values())) != 1:
        hold("SIZE_MISMATCH:" + json.dumps(sizes, sort_keys=True))
        return r
    ids = {}
    for k in ("base_mask", "candidate_mask"):
        a = data[k]
        if a.max() > 254 or a.min() < 0:
            hold("LABEL_RANGE_INVALID:" + k)
            return r
        ids[k] = set(int(v) for v in np.unique(a) if v != 0)
    if not ids["base_mask"] and not ids["candidate_mask"]:
        hold("NO_OBJECTS")
        return r
    if not ids["base_mask"]:
        hold("NO_OBJECTS:base_mask")
    if not ids["candidate_mask"]:
        hold("NO_OBJECTS:candidate_mask")
    if ids["base_mask"] != ids["candidate_mask"]:
        hold("LABEL_SET_MISMATCH:missing=%s:extra=%s" % (sorted(ids["base_mask"] - ids["candidate_mask"]),
                                                          sorted(ids["candidate_mask"] - ids["base_mask"])))
    if r["reasons"]:
        return r
    a, b = data["base_mask"], data["candidate_mask"]
    for k in sorted(ids["base_mask"]):
        sa, sb = _stats(a, k), _stats(b, k)
        inter = int(np.count_nonzero((a == k) & (b == k)))
        union = int(np.count_nonzero((a == k) | (b == k)))
        m = {"iou": inter / union, "pixel_delta": sb["pixels"] - sa["pixels"],
             "pixel_delta_ratio": abs(sb["pixels"] - sa["pixels"]) / sa["pixels"],
             "centroid_px": float(np.hypot(sb["centroid"][0] - sa["centroid"][0], sb["centroid"][1] - sa["centroid"][1])),
             "bbox_px": max(abs(x - y) for x, y in zip(sa["bbox"], sb["bbox"])), "base": sa, "candidate": sb}
        r["objects"][str(k)] = m
        for name, bad in (("IOU", m["iou"] < th["min_iou"]),
                          ("PIXEL_DELTA", m["pixel_delta_ratio"] > th["max_pixel_delta_ratio"]),
                          ("CENTROID", m["centroid_px"] > th["max_centroid_px"]),
                          ("BBOX", m["bbox_px"] > th["max_bbox_px"])):
            if bad:
                hold("GEOMETRY_DRIFT:%d:%s" % (k, name))
    if not r["reasons"]:
        r["status"] = "PROVISIONAL"
        r["note"] = "Mask-vs-mask agreement only; actual AI-rendered pixel geometry UNVERIFIED."
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("manifest")
    ap.add_argument("--output")
    a = ap.parse_args(argv)
    try:
        mp = Path(a.manifest)
        rec = evaluate(json.loads(mp.read_text(encoding="utf-8")), mp.parent)
    except Exception as e:
        rec = {"schema": "archigrow.aerial_raster_qa.receipt.v1", "evidence_class": EVIDENCE,
               "status": "HOLD", "reasons": ["MANIFEST_UNREADABLE:" + type(e).__name__], "real_output_pass": False}
    out = json.dumps(rec, indent=2, sort_keys=True)
    if a.output:
        Path(a.output).write_text(out, encoding="utf-8")
    print(out)
    return 0 if rec["status"] == "PROVISIONAL" else 1


if __name__ == "__main__":
    sys.exit(main())
