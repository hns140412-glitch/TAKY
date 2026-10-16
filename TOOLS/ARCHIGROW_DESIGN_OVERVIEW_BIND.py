#!/usr/bin/env python3
"""ARCHIGROW design overview binding: produce candidate, never overwrite approved overview."""
import argparse,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(area_json,overview_json,output_json,source_dxf=None,mapping=None):
    if Path(output_json).resolve() in {Path(area_json).resolve(),Path(overview_json).resolve()}:raise ValueError("OUTPUT_WOULD_OVERWRITE_INPUT")
    a=json.loads(Path(area_json).read_text(encoding="utf-8"))
    o=json.loads(Path(overview_json).read_text(encoding="utf-8"))
    if a.get("project_id")!=o.get("project_id"):raise ValueError("PROJECT_ID_MISMATCH")
    if a.get("schema")!="ARCHIGROW_AREA_OVERVIEW_V1":raise ValueError("AREA_SCHEMA_UNSUPPORTED")
    # Stale area evidence (source DXF/mapping changed after export) must not bind silently.
    freshness={}
    for label,path,key in (("source_dxf",source_dxf,"source_sha256"),("mapping",mapping,"mapping_sha256")):
        if path is None:freshness[label]="NOT_RECHECKED"
        else:freshness[label]="CURRENT" if sha(path)==a.get(key) else "STALE"
    candidates={}
    for r in a["totals"]:
        candidates.setdefault(r["scope"],[]).append({"level":r["level"],"area_m2":r["area_m2"]})
    if "STALE" in freshness.values():status="HOLD_STALE_AREA_EVIDENCE"
    elif a.get("geometry_status")=="HOLD":status="HOLD_GEOMETRY_ISSUES"
    else:status="HOLD_REVIEW_REQUIRED"
    out={"schema":"ARCHIGROW_DESIGN_OVERVIEW_BINDING_V1","project_id":a["project_id"],"source_overview_sha256":sha(overview_json),"source_area_sha256":sha(area_json),
         "original_overview":o,"area_candidates":candidates,"geometry_status":a["geometry_status"],"geometry_issues":a.get("issues",[]),
         "target_identity_status":a.get("target_identity_status","UNVERIFIED"),"source_freshness":freshness,
         "legal_status":"NOT_VERIFIED","binding_status":status,"reason":"Scope mapping does not prove statutory building area, GFA or FAR area. No approved overview is overwritten."}
    p=Path(output_json);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("area_json");p.add_argument("overview_json");p.add_argument("output_json")
    p.add_argument("--source-dxf");p.add_argument("--mapping")
    x=p.parse_args();print(json.dumps(bind(x.area_json,x.overview_json,x.output_json,x.source_dxf,x.mapping)["binding_status"]))
