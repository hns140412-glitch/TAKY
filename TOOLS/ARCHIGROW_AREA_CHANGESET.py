#!/usr/bin/env python3
"""Compare two existing ARCHIGROW_AREA_DXF_SVG stage outputs without modifying source drawings.

Detects CAD area-boundary changes by handle, source geometry (SVG path) and area/scope.
XREF notifications may trigger a re-run but are never trusted as area changes themselves.
This is a document-refresh candidate, NOT statutory area approval.
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

SCHEMA="ARCHIGROW_AREA_CHANGESET_V1"
FILES=("area_evidence.csv","area_evidence.svg","design_overview_area.json","stage_receipt.json")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _read(directory):
    directory=Path(directory)
    files={name:directory/name for name in FILES}
    if not all(p.is_file() for p in files.values()):
        raise ValueError("AREA_EVIDENCE_FILES_MISSING")
    evidence=json.loads(files["design_overview_area.json"].read_text(encoding="utf-8"))
    receipt=json.loads(files["stage_receipt.json"].read_text(encoding="utf-8"))
    expected={item["ref"]:item["sha256"] for item in receipt.get("outputs",[])}
    for filename in ("area_evidence.csv","area_evidence.svg","design_overview_area.json"):
        if expected.get(filename)!=sha(files[filename]):
            raise ValueError("AREA_EVIDENCE_HASH_MISMATCH:"+filename)
    if evidence.get("schema")!="ARCHIGROW_AREA_OVERVIEW_V1":
        raise ValueError("AREA_EVIDENCE_SCHEMA_UNSUPPORTED")
    with files["area_evidence.csv"].open(encoding="utf-8-sig",newline="") as stream:
        rows=list(csv.DictReader(stream))
    if not all(set(("handle","layer","level","scope","operation","area_m2"))<=set(r) for r in rows):
        raise ValueError("AREA_CSV_COLUMNS_INVALID")
    tree=ET.parse(files["area_evidence.svg"])
    paths={}
    for p in tree.getroot().iter():
        if p.tag.rsplit("}",1)[-1]=="path":
            obj_id=p.attrib.get("id","")
            if obj_id.startswith("cad-"):
                handle=obj_id[4:]
                if handle in paths: raise ValueError("DUPLICATE_SVG_HANDLE")
                paths[handle]=p.attrib.get("d","")
    result={}
    for r in rows:
        handle=r["handle"]
        if handle in result:raise ValueError("DUPLICATE_CSV_HANDLE")
        if handle not in paths:raise ValueError("SVG_CSV_HANDLE_MISMATCH:"+handle)
        try:area=float(r["area_m2"])
        except ValueError as exc:raise ValueError("AREA_NONNUMERIC:"+handle) from exc
        result[handle]={k:r[k] for k in ("handle","layer","level","scope","operation")}
        result[handle].update(area_m2=area,geometry=paths[handle])
    if set(paths)!=set(result):raise ValueError("SVG_CSV_HANDLE_MISMATCH")
    return evidence,receipt,result

def _properties(r):
    return {k:r[k] for k in ("layer","level","scope","operation")}

def _signature(r):
    return (r["geometry"],r["layer"],r["level"],r["scope"],r["operation"],round(r["area_m2"],4))

def _public(r):
    if r is None:return None
    return {k:v for k,v in r.items() if k!="geometry"}

def _key(row):
    return (row["level"],row["scope"])

def _totals(rows):
    total=defaultdict(float)
    for r in rows.values():
        total[_key(r)]+=r["area_m2"]*(1 if r["operation"]=="ADD" else -1)
    return total

def compare(previous_dir,current_dir,output_path):
    previous_dir=Path(previous_dir).resolve();current_dir=Path(current_dir).resolve()
    output_path=Path(output_path).resolve()
    if output_path.is_relative_to(previous_dir) or output_path.is_relative_to(current_dir):
        raise ValueError("OUTPUT_MUST_NOT_OVERWRITE_SOURCE_STAGE")
    old,old_receipt,prev=_read(previous_dir)
    new,new_receipt,cur=_read(current_dir)
    if old.get("project_id")!=new.get("project_id"):
        raise ValueError("PROJECT_ID_MISMATCH")
    if old.get("meters_per_unit")!=new.get("meters_per_unit"):
        raise ValueError("DRAWING_UNIT_CHANGED_REVIEW_REQUIRED")
    issues=[]
    if old.get("geometry_status")=="HOLD" or new.get("geometry_status")=="HOLD" or old_receipt.get("status")!="PASS" or new_receipt.get("status")!="PASS":
        issues.append("SOURCE_AREA_STAGE_NOT_PASS")
    # The mapping file includes source_revision/source_issue_date: those should change
    # between drawing versions. Hold only when the geometry/area classification policy changes.
    if not old.get("mapping_logic_sha256") or not new.get("mapping_logic_sha256"):
        issues.append("MAPPING_POLICY_FINGERPRINT_MISSING")
    elif old["mapping_logic_sha256"]!=new["mapping_logic_sha256"]:
        issues.append("LAYER_MAPPING_CHANGED_REVIEW_REQUIRED")
    if old.get("target_identity_status")!="DECLARED_BY_MAPPING" or new.get("target_identity_status")!="DECLARED_BY_MAPPING":
        issues.append("REVISION_UNVERIFIED")

    changes=[]
    shared=set(prev)&set(cur)
    for handle in sorted(shared):
        a,b=prev[handle],cur[handle]
        diff=[]
        if a["geometry"]!=b["geometry"]:diff.append("GEOMETRY")
        if abs(a["area_m2"]-b["area_m2"])>0.00009:diff.append("AREA")
        diff.extend(k.upper() for k in ("layer","level","scope","operation") if a[k]!=b[k])
        if diff:
            changes.append({"kind":"MODIFIED","previous_handle":handle,"current_handle":handle,"fields":diff,"before":_public(a),"after":_public(b)})
    removed=set(prev)-shared
    added=set(cur)-shared
    # Reassignments are reviewable even when geometries are identical: CAD handles may change.
    signature_to_new=defaultdict(list)
    for handle in sorted(added):signature_to_new[_signature(cur[handle])].append(handle)
    for handle in sorted(removed):
        a=prev[handle]
        candidates=signature_to_new[_signature(a)]
        if candidates:
            replacement=candidates.pop(0)
            added.remove(replacement)
            changes.append({"kind":"HANDLE_REASSIGNED","previous_handle":handle,"current_handle":replacement,"fields":["HANDLE"],"before":_public(a),"after":_public(cur[replacement])})
        else:
            changes.append({"kind":"REMOVED","previous_handle":handle,"current_handle":None,"fields":["REMOVED"],"before":_public(a),"after":None})
    for handle in sorted(added):
        changes.append({"kind":"ADDED","previous_handle":None,"current_handle":handle,"fields":["ADDED"],"before":None,"after":_public(cur[handle])})
    changes.sort(key=lambda c:(c["kind"],c["previous_handle"] or "",c["current_handle"] or ""))

    before=_totals(prev);after=_totals(cur)
    sums=[]
    changed_scopes=[]
    for level,scope in sorted(set(before)|set(after)):
        a=round(before.get((level,scope),0),4)
        b=round(after.get((level,scope),0),4)
        changed=abs(a-b)>0.00009
        sums.append({"level":level,"scope":scope,"previous_m2":a,"current_m2":b,"delta_m2":round(b-a,4),"value_changed":changed})
        if changed:changed_scopes.append({"level":level,"scope":scope})
    status="HOLD" if issues else ("NO_CHANGE" if not changes else "CANDIDATE_REVIEW_REQUIRED")
    doc={
      "schema":SCHEMA,"project_id":new["project_id"],"status":status,
      "previous":{"area_sha256":sha(previous_dir/"design_overview_area.json"),"source_dxf_sha256":old.get("source_sha256"),"source_identity":old.get("source_identity")},
      "current":{"area_sha256":sha(current_dir/"design_overview_area.json"),"source_dxf_sha256":new.get("source_sha256"),"source_identity":new.get("source_identity")},
      "changes":changes,"area_totals":sums,
      "downstream_candidate":{"excel_rows_to_rebind":changed_scopes,"ppt_area_fields_to_rebind":changed_scopes,
         "drawing_vector_changed":any(c["kind"] not in ("HANDLE_REASSIGNED",) for c in changes)},
      "issues":issues,
      "approval":"NOT_GRANTED","legal_area_status":"NOT_VERIFIED",
      "note":"Updated numbers are mechanical layer-scope totals. Do not promote to statutory design overview or overwrite approved Excel/PPT without binding and review."
    }
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8")
    return doc

def main():
    p=argparse.ArgumentParser()
    p.add_argument("previous_stage_dir");p.add_argument("current_stage_dir");p.add_argument("output_json")
    a=p.parse_args()
    r=compare(a.previous_stage_dir,a.current_stage_dir,a.output_json)
    print(json.dumps({"status":r["status"],"changes":len(r["changes"]),"affected_totals":sum(v["value_changed"] for v in r["area_totals"]),"issues":r["issues"]},ensure_ascii=False))
    return 2 if r["status"]=="HOLD" else 0

if __name__=="__main__":
    raise SystemExit(main())
