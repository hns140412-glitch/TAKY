#!/usr/bin/env python3
"""TAKY Visual Compare V2.

Compares only hash-pinned BOUND Golden references against deterministic browser
renders at identical pixel dimensions. No implicit resize/crop is allowed.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance, ImageStat

MANIFEST_SCHEMA="TAKY_DESIGN_TO_UI_PIPELINE_V1"
RENDER_SCHEMA="TAKY_RENDER_MANIFEST_V1"
EVIDENCE_SCHEMA="TAKY_DESIGN_EVIDENCE_V1"

def sha256(p: Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def safe(root: Path, rel: str)->Path:
    p=(root/rel).resolve()
    p.relative_to(root.resolve())
    return p

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def mean_abs(diff: Image.Image)->float:
    stat=ImageStat.Stat(diff)
    return sum(stat.mean)/(len(stat.mean)*255.0)

def changed_ratio(diff: Image.Image, threshold: int)->float:
    rgb=diff.convert("RGB")
    px=rgb.load(); w,h=rgb.size; changed=0
    for y in range(h):
        for x in range(w):
            if max(px[x,y]) >= threshold:
                changed += 1
    return changed/max(1,w*h)

def crop_norm(im: Image.Image, r: dict)->Image.Image:
    x=float(r["x"]); y=float(r["y"]); w=float(r["w"]); h=float(r["h"])
    if min(x,y,w,h)<0 or x+w>1 or y+h>1 or w<=0 or h<=0:
        raise ValueError("ROI_OUT_OF_RANGE")
    iw,ih=im.size
    box=(round(x*iw),round(y*ih),round((x+w)*iw),round((y+h)*ih))
    if box[2]<=box[0] or box[3]<=box[1]:
        raise ValueError("ROI_EMPTY")
    return im.crop(box)

def screen_contract(root: Path, screen: dict)->dict:
    cfg=screen["screen_contract"]
    p=safe(root,cfg["path"])
    if sha256(p).lower()!=cfg["sha256"].lower():
        raise ValueError("SCREEN_CONTRACT_SHA_MISMATCH")
    return load_json(p)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True,type=Path)
    ap.add_argument("--render-manifest",required=True,type=Path)
    ap.add_argument("--root",type=Path,default=Path.cwd())
    ap.add_argument("--out",type=Path,default=Path("ui-audit/visual-result.json"))
    ap.add_argument("--diff-dir",type=Path,default=Path("ui-audit/diff"))
    args=ap.parse_args()
    root=args.root.resolve()
    manifest=load_json(args.manifest)
    render=load_json(args.render_manifest)
    errors=[]; results=[]; coverage=[]

    manifest_hash=sha256(args.manifest)
    if manifest.get("schema")!=MANIFEST_SCHEMA: errors.append("MANIFEST_SCHEMA_INVALID")
    if render.get("schema")!=RENDER_SCHEMA: errors.append("RENDER_SCHEMA_INVALID")
    if render.get("manifest_sha256")!=manifest_hash: errors.append("RENDER_MANIFEST_HASH_MISMATCH")
    if render.get("source_commit")!=manifest.get("source_commit"): errors.append("SOURCE_COMMIT_MISMATCH")
    if render.get("project")!=manifest.get("project"): errors.append("PROJECT_MISMATCH")

    screens={s["id"]:s for s in manifest.get("screens",[])}
    seen=set()
    diff_root=(root/args.diff_dir).resolve()
    diff_root.mkdir(parents=True,exist_ok=True)

    for entry in render.get("entries",[]):
        sid=str(entry.get("screen_id",""))
        stid=str(entry.get("state_id",""))
        vid=str(entry.get("viewport_id",""))
        key=f"{sid}:{stid}:{vid}"
        if key in seen:
            errors.append(f"{key}:DUPLICATE_RENDER_ENTRY"); continue
        seen.add(key)
        screen=screens.get(sid)
        if not screen:
            errors.append(f"{key}:SCREEN_UNKNOWN"); continue
        state=next((s for s in screen.get("states",[]) if s.get("id")==stid),None)
        viewport=next((v for v in screen.get("viewports",[]) if v.get("id")==vid),None)
        if not state: errors.append(f"{key}:STATE_UNKNOWN"); continue
        if not viewport: errors.append(f"{key}:VIEWPORT_UNKNOWN"); continue
        visual_policy=state.get("visual_policy","GOLDEN_PARITY")
        if visual_policy!="GOLDEN_PARITY":
            errors.append(f"{key}:VISUAL_POLICY_NOT_GOLDEN_PARITY"); continue

        golden=screen.get("golden",{})
        if golden.get("status")!="BOUND":
            errors.append(f"{key}:GOLDEN_NOT_BOUND"); continue
        try:
            ref=safe(root,golden["path"]); actual=safe(root,entry["actual_path"])
        except Exception:
            errors.append(f"{key}:PATH_INVALID"); continue
        if not ref.is_file() or not actual.is_file():
            errors.append(f"{key}:REFERENCE_OR_RENDER_MISSING"); continue
        if sha256(ref).lower()!=golden.get("sha256","").lower():
            errors.append(f"{key}:GOLDEN_SHA_MISMATCH"); continue
        if sha256(actual).lower()!=str(entry.get("actual_sha256","")).lower():
            errors.append(f"{key}:ACTUAL_SHA_MISMATCH"); continue
        try:
            r=Image.open(ref).convert("RGB")
            a=Image.open(actual).convert("RGB")
        except Exception:
            errors.append(f"{key}:IMAGE_DECODE_FAILED"); continue
        if r.size!=a.size:
            results.append({"coverage_key":key,"pass":False,"error":"DIMENSION_MISMATCH","reference_size":list(r.size),"actual_size":list(a.size)})
            coverage.append(key); continue

        cfg=screen_contract(root,screen).get("visual_compare",{})
        try:
            mae_max=float(cfg["mae_max"])
            ratio_max=float(cfg["changed_ratio_max"])
            px_threshold=int(cfg.get("pixel_delta_threshold",24))
        except Exception:
            errors.append(f"{key}:VISUAL_COMPARE_THRESHOLDS_MISSING"); continue

        diff=ImageChops.difference(r,a)
        mae=mean_abs(diff); ratio=changed_ratio(diff,px_threshold)
        full_ok=mae<=mae_max and ratio<=ratio_max
        roi_rows=[]; roi_ok=True
        for region in cfg.get("regions",[]):
            try:
                rd=ImageChops.difference(crop_norm(r,region),crop_norm(a,region))
                rmae=mean_abs(rd); rratio=changed_ratio(rd,int(region.get("pixel_delta_threshold",px_threshold)))
                r_mae_max=float(region.get("mae_max",mae_max))
                r_ratio_max=float(region.get("changed_ratio_max",ratio_max))
                ok=rmae<=r_mae_max and rratio<=r_ratio_max
                if region.get("critical",True) and not ok: roi_ok=False
                roi_rows.append({"id":region["id"],"pass":ok,"critical":bool(region.get("critical",True)),
                                 "mae":round(rmae,6),"mae_max":r_mae_max,
                                 "changed_ratio":round(rratio,6),"changed_ratio_max":r_ratio_max})
            except Exception as e:
                roi_ok=False
                roi_rows.append({"id":region.get("id","<unknown>"),"pass":False,"critical":True,"error":str(e)})

        diff_name=(key.replace(":","__")+".png")
        diff_path=diff_root/diff_name
        ImageEnhance.Contrast(diff).enhance(3.0).save(diff_path)
        ok=full_ok and roi_ok
        results.append({
            "coverage_key":key,"pass":ok,
            "reference":str(ref.relative_to(root)),"actual":str(actual.relative_to(root)),
            "reference_sha256":sha256(ref),"actual_sha256":sha256(actual),
            "pixel_size":list(r.size),
            "mae":round(mae,6),"mae_max":mae_max,
            "changed_ratio":round(ratio,6),"changed_ratio_max":ratio_max,
            "pixel_delta_threshold":px_threshold,
            "regions":roi_rows,
            "diff_path":str(diff_path.relative_to(root))
        })
        coverage.append(key)

    expected={
        f"{s['id']}:{st['id']}:{v['id']}"
        for s in manifest.get("screens",[])
        for st in s.get("states",[])
        if st.get("visual_policy","GOLDEN_PARITY")=="GOLDEN_PARITY"
        for v in s.get("viewports",[])
    }
    missing=sorted(expected-set(coverage))
    if missing: errors.append("VISUAL_COVERAGE_MISSING:"+",".join(missing))
    passed=(not errors and all(r.get("pass") is True for r in results) and set(coverage)==expected)
    payload={
        "schema":EVIDENCE_SCHEMA,"kind":"VISUAL","pass":passed,
        "project":manifest.get("project"),"manifest_sha256":manifest_hash,
        "source_commit":manifest.get("source_commit"),"coverage":sorted(set(coverage)),
        "results":results,"errors":errors
    }
    out=(root/args.out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    return 0 if passed else 1

if __name__=="__main__":
    raise SystemExit(main())
