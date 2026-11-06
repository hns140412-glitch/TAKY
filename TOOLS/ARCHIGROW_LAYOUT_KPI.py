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
    if point_in_polygon_strict(a[0],b) or point_in_polygon_strict(b[0],a): return True
    # Collinear/coincident overlaps have no proper crossing and no strictly interior vertex.
    return intersection_area(a,b)>1e-9
def _ccw(poly):
    pts=[(float(x),float(y)) for x,y in poly]
    pts=[p for i,p in enumerate(pts) if p!=pts[i-1]] or pts
    if sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))<0: pts.reverse()
    out=[p for i,p in enumerate(pts) if orient(pts[i-1],p,pts[(i+1)%len(pts)])!=0]
    return out if len(out)>=3 else pts
def triangulate(poly):
    """Ear clipping for a valid simple polygon -> CCW triangles."""
    pts=_ccw(poly); tris=[]
    def inside_tri(p,a,b,c,strict):
        o=(orient(a,b,p),orient(b,c,p),orient(c,a,p))
        return all(x>0 for x in o) if strict else all(x>=0 for x in o)
    for strict in (False,True):
        work=list(pts); tris=[]
        while len(work)>3:
            for i in range(len(work)):
                a,b,c=work[i-1],work[i],work[(i+1)%len(work)]
                if orient(a,b,c)<=0: continue
                if any(inside_tri(p,a,b,c,strict) for p in work if p not in (a,b,c)): continue
                tris.append((a,b,c)); del work[i]; break
            else: break
        if len(work)==3: return tris+[tuple(work)]
    raise ValueError("TRIANGULATION_FAILED")
def _clip_convex(subject,clip):
    out=list(subject)
    for i in range(len(clip)):
        a,b=clip[i],clip[(i+1)%len(clip)]
        if not out: break
        inp,out=out,[]
        side=lambda p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        for j in range(len(inp)):
            p,q=inp[j],inp[(j+1)%len(inp)]; sp,sq=side(p),side(q)
            if sp>=0: out.append(p)
            if (sp>=0)!=(sq>=0):
                t=sp/(sp-sq); out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return out
def intersection_area(a,b):
    """Exact overlap area of two valid simple polygons (triangle-pair convex clipping)."""
    tb=triangulate(b); total=0.0
    for ta in triangulate(a):
        for t in tb:
            c=_clip_convex(list(ta),list(t))
            if len(c)>=3: total+=area([list(p) for p in c])
    return total
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
        # Vertex containment alone misses objects spanning a concave site notch; require full area coverage.
        if any(not point_in_polygon(p,site) for p in o["polygon"]) or abs(intersection_area(o["polygon"],site)-row["computed_area"])>1e-6:
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

def _cli(run):
    """--input JSON [--output JSON]: execute on project data; no arguments keeps the schema probe."""
    import argparse,sys
    if len(sys.argv)==1:
        print(json.dumps({"schema":SCHEMA["schema"],"ok":True},ensure_ascii=False)); return 0
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",default="")
    a=p.parse_args(); result=run(json.loads(Path(a.input).read_text(encoding="utf-8")))
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(text,encoding="utf-8")
    print(text); return 0 if result.get("ok") else 2

if __name__=="__main__":
    raise SystemExit(_cli(evaluate))
