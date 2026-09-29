#!/usr/bin/env python3
"""Fail-closed admission for ACTUAL independently supplied painterly badge files.

An empty, held manifest passes so draft work can continue; it admits ZERO artwork.
No semantic/style check is inferred from CI. Actual visual review must be anchored
to the approved reference binary, the exact produced art hashes, and size previews.
"""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
MANIFEST="BADGE/assets/production-art-admission.json"
CHECKS=("reference_compared","original_motif","witty_core_detail_visible",
        "approved_painterly_style","no_character_or_crew","no_baked_rim_star_tier_lock_text",
        "independent_background_interior","circular_alpha","legible_64_120_200_320")
SIZES=(64,120,200,320)

def read(root,rel):
    return json.loads((root/rel).read_text(encoding="utf-8"))

def safe_file(root,rel,prefix,extensions):
    if not isinstance(rel,str) or not rel.startswith(prefix) or Path(rel).suffix.lower() not in extensions:
        return None
    target=(root/rel).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file() or target.is_symlink():
        return None
    return target

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def exact_file(root,blob,prefix,extensions,errors,code):
    if not isinstance(blob,dict):
        errors.append(code+"_FILE_IDENTITY_REQUIRED")
        return None
    path=safe_file(root,blob.get("path"),prefix,extensions)
    sha=blob.get("sha256")
    if not path or not isinstance(sha,str) or not re.fullmatch("[a-f0-9]{64}",sha) or digest(path)!=sha:
        errors.append(code+"_MISSING_OR_HASH_MISMATCH")
        return None
    return path

def check_circle_png(path,size,errors,code):
    try:
        with Image.open(path) as im:
            if im.format!="PNG" or im.mode!="RGBA" or im.size!=(size,size):
                errors.append(code+"_SIZE_OR_RGBA")
                return
            px=im.load()
            if px[size//2,size//2][3]<8:
                errors.append(code+"_EMPTY_CENTER")
            for y in range(0,size,max(1,size//20)):
                for x in range(0,size,max(1,size//20)):
                    if ((x+.5-size/2)**2+(y+.5-size/2)**2)**.5>size*.505 and px[x,y][3]>12:
                        errors.append(code+"_OUTSIDE_CIRCLE_NOT_TRANSPARENT")
                        return
            for x,y in ((0,0),(0,size-1),(size-1,0),(size-1,size-1)):
                if px[x,y][3]>12:
                    errors.append(code+"_OPAQUE_CORNER")
                    return
    except (OSError,ValueError):
        errors.append(code+"_PNG_UNREADABLE")

def verify(root=ROOT,manifest=None):
    root=Path(root)
    errors=[]
    manifest=manifest if manifest is not None else read(root,MANIFEST)
    source=read(root,"BADGE/badge-60-story-20-history-working.json")
    copy=read(root,"BADGE/badge-wow-inspired-copyworking.json")
    direction=read(root,"BADGE/assets/individual-art-direction-60.json")
    queue=read(root,"BADGE/assets/visual-rework-queue-working.json")
    registry=read(root,"BADGE/assets/asset-registry-working.json")
    if manifest.get("schema")!="TAKY_BADGE_ART_BYTE_ADMISSION_V1" or manifest.get("deployment")!="HOLD":
        errors.append("ART_ADMISSION_SCHEMA_OR_DEPLOY_HOLD")
    items=manifest.get("items")
    if not isinstance(items,list):
        return ["ART_ADMISSION_ITEMS_REQUIRED"]
    if manifest.get("status") not in ("HOLD_NO_ART_ADMITTED","REVIEWED_ART_UNBOUND"):
        errors.append("ART_ADMISSION_INVALID_STATE")
    if not items and manifest.get("status")!="HOLD_NO_ART_ADMITTED":
        errors.append("EMPTY_ADMISSION_CANNOT_BE_REVIEWED")
    if items and manifest.get("status")!="REVIEWED_ART_UNBOUND":
        errors.append("NEW_FILES_CANNOT_BYPASS_REVIEW_STATE")
    if any(a.get("runtime_approved") is not False or a.get("runtime_bound") is not False or a.get("active") is not False for a in registry["items"]):
        errors.append("ADMISSION_IS_NOT_RUNTIME_APPROVAL")
    source_by={x["source_draft_id"]:x for x in source["presets"]}
    copy_by={x["source_draft_id"]:x for x in copy["preset_copy"]}
    art_by={x["badge_id"]:x for x in direction["items"]}
    allowed=set(queue["correction_ids"])
    seen=set()
    used_bytes=set()
    for item in items:
        bid=item.get("badge_id","")
        if bid in seen or bid not in allowed:
            errors.append("INVALID_OR_DUPLICATE_REWORK_ID")
            continue
        seen.add(bid)
        number=bid[-3:]
        src,cp,art=source_by[bid],copy_by[bid],art_by[bid]
        expected={"canonical_title":src["stable_name"],"display_title_proposal":cp["display_title_proposal"],
                  "core_detail_proposal":cp["flavor_text_proposal"],"source_motif":src["motif"],
                  "source_storyline":src["storyline"],"unlock_toast_proposal":cp["unlock_toast_proposal"],
                  "visual_id":art["visual_id"]}
        if any(item.get(k)!=v for k,v in expected.items()):
            errors.append("ART_ADMISSION_SOURCE_OR_WIT_DRIFT_"+number)
        ref=exact_file(root,item.get("approved_reference"),
                       "BADGE/assets/approved-references/",(".png",".jpg",".jpeg"),errors,number+"_REFERENCE")
        layers=item.get("layers",{})
        if not isinstance(layers,dict): layers={}
        layer_hashes=[]
        for kind in ("background","interior","composite"):
            blob=layers.get(kind)
            path=exact_file(root,blob,"BADGE/assets/individual/"+number+"/",(".png",),errors,number+"_"+kind)
            if path:
                if path.name!=kind+".png": errors.append(number+"_UNEXPECTED_LAYER_FILENAME")
                check_circle_png(path,1024,errors,number+"_"+kind)
                layer_hashes.append(digest(path))
                if digest(path) in used_bytes: errors.append("REUSED_ART_BYTES_FOR_DIFFERENT_LAYER")
                used_bytes.add(digest(path))
        if len(layer_hashes)==3 and len(set(layer_hashes))!=3:
            errors.append(number+"_FLATTENED_OR_DUPLICATED_LAYER")
        previews=item.get("previews",{})
        if not isinstance(previews,dict): previews={}
        if set(previews)!={str(s) for s in SIZES}: errors.append(number+"_PREVIEW_SET_MISSING")
        for sz in SIZES:
            path=exact_file(root,previews.get(str(sz)),"BADGE/assets/individual/"+number+"/",
                            (".png",),errors,number+"_PREVIEW_"+str(sz))
            if path:
                if path.name!="preview-"+str(sz)+".png": errors.append(number+"_PREVIEW_NAME")
                check_circle_png(path,sz,errors,number+"_PREVIEW_"+str(sz))
        evidence=exact_file(root,item.get("visual_review_evidence"),
                            "BADGE/assets/review-evidence/",(".json",),errors,number+"_REVIEW")
        if evidence:
            try: e=json.loads(evidence.read_text(encoding="utf-8"))
            except (ValueError,UnicodeDecodeError): e={}
            if e.get("badge_id")!=bid or e.get("reference_sha256")!=(digest(ref) if ref else None) or e.get("art_sha256")!=layers.get("composite",{}).get("sha256") or any(e.get("checks",{}).get(k) is not True for k in CHECKS):
                errors.append(number+"_VISUAL_EVIDENCE_INCOMPLETE_OR_UNANCHORED")
    return sorted(set(errors))

if __name__=="__main__":
    problems=verify()
    if problems: raise SystemExit("BADGE ART ADMISSION BLOCKED: "+", ".join(problems))
    print("BADGE ART ADMISSION: HOLD and 0 admitted" if not read(ROOT,MANIFEST)["items"] else "BADGE ART ADMISSION: byte-checked review evidence; runtime and release remain HOLD. Artistic meaning is NOT automatically certified by the byte gate.")
