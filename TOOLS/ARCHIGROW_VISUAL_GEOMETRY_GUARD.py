#!/usr/bin/env python3
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/"DOMAIN"/"ARCHITECTURE_VISUAL_GEOMETRY_GUARD_SCHEMA.json").read_text(encoding="utf-8"))
LOCKED=SCHEMA["locked_geometry_fields"]

def clean(v): return str(v or "").strip()
def canonical_geometry(snapshot):
    rows=[]
    for raw in snapshot.get("objects") or []:
        row={k:raw.get(k) for k in LOCKED}
        rows.append(row)
    rows.sort(key=lambda x:clean(x.get("object_id")))
    return {"project_id":clean(snapshot.get("project_id")),"model_revision":clean(snapshot.get("model_revision")),"objects":rows}
def digest(v):
    return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
def compare(base,candidate):
    b=canonical_geometry(base); c=canonical_geometry(candidate)
    issues=[]
    if not b["project_id"] or not c["project_id"]: issues.append("PROJECT_ID_REQUIRED")
    if b["project_id"]!=c["project_id"]: issues.append("PROJECT_ID_DRIFT")
    bm={clean(x.get("object_id")):x for x in b["objects"]}; cm={clean(x.get("object_id")):x for x in c["objects"]}
    if set(bm)!=set(cm):
        issues.append("OBJECT_SET_DRIFT")
    for oid in sorted(set(bm)&set(cm)):
        for k in LOCKED:
            if k=="object_id": continue
            if bm[oid].get(k)!=cm[oid].get(k): issues.append(f"GEOMETRY_DRIFT:{oid}:{k}")
    return {
      "ok":not issues,
      "status":"PASS" if not issues else "HOLD",
      "issues":issues,
      "base_geometry_sha256":digest(b),
      "candidate_geometry_sha256":digest(c),
      "visual_changes_allowed":list(SCHEMA["allowed_visual_fields"]),
      "geometry_change_authorized":False,
      "rule":"VISUAL PASS REQUIRES LOCKED GEOMETRY IDENTITY; STYLE/CAMERA CHANGE DOES NOT AUTHORIZE GEOMETRY CHANGE"
    }
if __name__=="__main__": print(json.dumps({"schema":SCHEMA["schema"],"ok":True},ensure_ascii=False))
