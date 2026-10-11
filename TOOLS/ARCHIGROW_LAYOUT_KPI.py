#!/usr/bin/env python3
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/"DOMAIN"/"ARCHITECTURE_LAYOUT_OBJECT_SCHEMA.json").read_text(encoding="utf-8"))

def clean(v): return str(v or "").strip()
def pt(v):
    return isinstance(v,(list,tuple)) and len(v)==2 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in v)
def polygon_valid(poly):
    if not isinstance(poly,list) or len(poly)<3 or not all(pt(x) for x in poly): return False
    return abs(area(poly))>1e-9 and not self_intersects(poly)
def area(poly):
    return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))/2.0)
def orient(a,b,c):
    v=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    return 0 if abs(v)<1e-9 else (1 if v>0 else -1)
def onseg(a,b,p):
    return orient(a,b,p)==0 and min(a[0],b[0])-1e-9<=p[0]<=max(a[0],b[0])+1e-9 and min(a[1],b[1])-1e-9<=p[1]<=max(a[1],b[1])+1e-9
def segments_intersect(a,b,c,d,allow_touch=True):
    o1,o2,o3,o4=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    if o1*o2<0 and o3*o4<0: return True
    if allow_touch and ((o1==0 and onseg(a,b,c)) or (o2==0 and onseg(a,b,d)) or (o3==0 and onseg(c,d,a)) or (o4==0 and onseg(c,d,b))): return True
    return False
def self_intersects(poly):
    n=len(poly)
    for i in range(n):
        a,b=poly[i],poly[(i+1)%n]
        for j in range(i+1,n):
            if j in {i,(i+1)%n} or (j+1)%n in {i,(i+1)%n}: continue
            if i==0 and j==n-1: continue
            if segments_intersect(a,b,poly[j],poly[(j+1)%n]): return True
    return False
def point_in_polygon(p,poly):
    if any(onseg(poly[i],poly[(i+1)%len(poly)],p) for i in range(len(poly))): return True
    inside=False; x,y=p
    j=len(poly)-1
    for i in range(len(poly)):
        xi,yi=poly[i]; xj,yj=poly[j]
        if ((yi>y)!=(yj>y)):
            xcross=(xj-xi)*(y-yi)/(yj-yi)+xi
            if x<xcross: inside=not inside
        j=i
    return inside
def point_in_polygon_strict(p,poly):
    if any(onseg(poly[i],poly[(i+1)%len(poly)],p) for i in range(len(poly))): return False
    inside=False; x,y=p
    j=len(poly)-1
    for i in range(len(poly)):
        xi,yi=poly[i]; xj,yj=poly[j]
        if ((yi>y)!=(yj>y)):
            xcross=(xj-xi)*(y-yi)/(yj-yi)+xi
            if x<xcross: inside=not inside
        j=i
    return inside
def polygons_overlap(a,b):
    for i in range(len(a)):
        for j in range(len(b)):
            if segments_intersect(a[i],a[(i+1)%len(a)],b[j],b[(j+1)%len(b)],allow_touch=False): return True
    return point_in_polygon_strict(a[0],b) or point_in_polygon_strict(b[0],a)
def validate_object(o):
    issues=[]
    for k in SCHEMA["required"]:
        if k=="polygon":
            if not polygon_valid(o.get(k)): issues.append("POLYGON_INVALID")
        elif not clean(o.get(k)): issues.append("MISSING_"+k.upper())
    if clean(o.get("object_type")) not in SCHEMA["object_types"]: issues.append("OBJECT_TYPE_INVALID")
    if clean(o.get("area_scope")) not in SCHEMA["area_scopes"]: issues.append("AREA_SCOPE_INVALID")
    if o.get("object_type")=="PARKING":
        c=o.get("parking_count")
        if not isinstance(c,int) or c<0: issues.append("PARKING_COUNT_INVALID")
    return {"ok":not issues,"issues":issues}
def evaluate(model):
    site=model.get("site_polygon")
    if not polygon_valid(site): return {"ok":False,"status":"HOLD","issues":["SITE_POLYGON_INVALID"]}
    rows=[]; issues=[]
    for o in model.get("objects") or []:
        c=validate_object(o)
        if not c["ok"]:
            issues.extend(f'{clean(o.get("object_id")) or "UNKNOWN"}:{x}' for x in c["issues"]); continue
        row={**o,"computed_area":area(o["polygon"])}
        if any(not point_in_polygon(p,site) for p in o["polygon"]):
            issues.append(f'{o["object_id"]}:OUTSIDE_SITE_BOUNDARY')
        rows.append(row)
    ids=[r["object_id"] for r in rows]
    if len(ids)!=len(set(ids)): issues.append("OBJECT_ID_DUPLICATE")
    for i,a in enumerate(rows):
        if a["area_scope"]=="NONE": continue
        for b in rows[i+1:]:
            if b["area_scope"]!=a["area_scope"] or b["level"]!=a["level"] or b["area_scope"]=="NONE": continue
            if polygons_overlap(a["polygon"],b["polygon"]):
                issues.append(f'OVERLAP:{a["object_id"]}:{b["object_id"]}:{a["area_scope"]}')
    if issues: return {"ok":False,"status":"HOLD","issues":issues,"objects":rows,"feasibility_claim_authorized":False}
    gfa=sum(r["computed_area"] for r in rows if r["area_scope"]=="GFA")
    footprints={}
    for r in rows:
        if r["area_scope"]=="FOOTPRINT": footprints[r["object_id"]]=r["computed_area"]
    parking=sum(r.get("parking_count",0) for r in rows if r["object_type"]=="PARKING")
    site_area=area(site)
    return {
      "ok":True,"status":"PASS","objects":rows,
      "kpi":{"site_area":site_area,"gfa_area":gfa,"footprint_area":sum(footprints.values()),"parking_count":parking,
             "gfa_to_site_ratio":(gfa/site_area if site_area else None)},
      "feasibility_claim_authorized":False,
      "rule":"DETERMINISTIC GEOMETRY/KPI PASS != LEGAL/ADMINISTRATIVE FEASIBILITY"
    }

if __name__=="__main__":
    print(json.dumps({"schema":SCHEMA["schema"],"ok":True},ensure_ascii=False))
