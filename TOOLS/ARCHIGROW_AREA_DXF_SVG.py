#!/usr/bin/env python3
"""ARCHIGROW DXF layer-area evidence -> SVG, CSV, overview JSON, stage receipt.
Source read-only. No automatic statutory area classification or legal verdict.
Reader: ezdxf when installed; otherwise the built-in ASCII DXF reader (TKY-ARCHIPIPE-001 fallback route).
Geometry kernel (validity / exact overlap area) is reused from ARCHIGROW_LAYOUT_KPI.py. Python >=3.9.
"""
import argparse,csv,hashlib,importlib.util,json,math,re
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

TOOL_VERSION="ARCHIGROW_AREA_DXF_SVG/2026-10-21.1"
_spec=importlib.util.spec_from_file_location("archigrow_layout_kpi",Path(__file__).resolve().parent/"ARCHIGROW_LAYOUT_KPI.py")
K=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(K)
# $INSUNITS -> meters. 0 (unitless) and unlisted codes require an explicit meters_per_unit.
UNITS={1:.0254,2:.3048,4:.001,5:.01,6:1.,7:1000.,14:.1}
EPS=1e-6

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

# ---------- readers: both return {"insunits":int,"modelspace":[entity],"blocks":{name:set(layers)}} ----------
# entity = {type,layer,handle,closed,is_2d,vertices:[(x,y,bulge)],block}
# Pre-R2007 DXF text is stored in $DWGCODEPAGE (Korean CAD: ANSI_949 = cp949); R2007+ (AC1021+) is UTF-8.
CODEPAGES={"ANSI_949":"cp949","ANSI_932":"cp932","ANSI_936":"gbk","ANSI_950":"cp950","ANSI_1250":"cp1250","ANSI_1251":"cp1251","ANSI_1252":"cp1252","ANSI_1253":"cp1253","ANSI_1254":"cp1254","ANSI_1255":"cp1255","ANSI_1256":"cp1256","ANSI_1257":"cp1257","ANSI_1258":"cp1258","ANSI_874":"cp874"}
def detect_encoding(raw):
    head=raw[:200000].decode("ascii",errors="ignore").splitlines()
    def hv(name,code):
        for i in range(len(head)-3):
            if head[i].strip()=="9" and head[i+1].strip()==name and head[i+2].strip()==code:return head[i+3].strip()
        return ""
    ver=hv("$ACADVER","1")
    if ver[:2]=="AC" and ver[2:].isdigit() and int(ver[2:])>=1021:return "utf-8",ver,""
    page=hv("$DWGCODEPAGE","3").upper()
    if not page:
        try:raw.decode("utf-8");return "utf-8",ver,""
        except UnicodeDecodeError:return "cp949",ver,"CODEPAGE_UNDECLARED_ASSUMED_CP949"
    if page not in CODEPAGES and page not in ("UTF8","UTF-8"):return "utf-8",ver,"CODEPAGE_UNSUPPORTED:"+page
    return CODEPAGES.get(page,"utf-8"),ver,""
def unescape(v):
    return re.sub(r"\\U\+([0-9A-Fa-f]{4})",lambda m:chr(int(m.group(1),16)),v)
def _pairs(path,meta=None):
    raw=Path(path).read_bytes()
    if raw.startswith(b"AutoCAD Binary DXF"):raise ValueError("BINARY_DXF_REQUIRES_EZDXF")
    enc,ver,note=detect_encoding(raw)
    if meta is not None:meta.update(encoding=enc,acadver=ver or None,encoding_note=note or None)
    lines=raw.decode(enc,errors="replace").splitlines()
    if len(lines)%2:lines=lines[:-1]
    for i in range(0,len(lines),2):
        yield int(lines[i].strip()),unescape(lines[i+1].strip())
def read_ascii(path):
    out={"insunits":0,"modelspace":[],"blocks":defaultdict(set),"meta":{}}
    section=None;cur=None;block=None;poly=None;want_units=False
    def flush():
        nonlocal cur,poly
        if cur is None:return
        t=cur["type"]
        if t=="LWPOLYLINE":cur["vertices"]=cur["_v"]
        if section=="ENTITIES" and not cur["paperspace"]:
            if t=="VERTEX":
                if poly is not None and cur["_v"]:poly["vertices"].append(cur["_v"][0])
            elif t=="SEQEND":
                if poly is not None:out["modelspace"].append(poly);poly=None
            elif t=="POLYLINE":poly=cur
            else:out["modelspace"].append(cur)
        elif section=="BLOCKS" and block is not None and t not in ("BLOCK","ENDBLK","VERTEX","SEQEND"):
            out["blocks"][block].add(cur["layer"])
        cur=None
    for code,val in _pairs(path,out["meta"]):
        if code==0:
            flush()
            if val=="SECTION":section="?";continue
            if val in ("ENDSEC","EOF"):section=None;continue
            if section=="BLOCKS" and val=="ENDBLK":block=None;continue
            cur={"type":val,"layer":"0","handle":"","closed":False,"is_2d":True,"vertices":[],"block":"","paperspace":False,"_v":[],"extrusion":[0.,0.,1.]}
            continue
        if section=="?" and code==2:section=val;continue
        if section=="HEADER":
            if code==9:want_units=val=="$INSUNITS"
            elif want_units and code==70:out["insunits"]=int(val);want_units=False
            continue
        if cur is None:continue
        t=cur["type"]
        if code==8:cur["layer"]=val
        elif code==5:cur["handle"]=val
        elif code==2 and t=="BLOCK":block=val
        elif code==2 and t=="INSERT":cur["block"]=val
        elif code==67:cur["paperspace"]=val=="1"
        elif code in (210,220,230) and t in ("LWPOLYLINE","POLYLINE"):cur["extrusion"][(210,220,230).index(code)]=float(val)
        elif code==70 and t in ("LWPOLYLINE","POLYLINE"):
            flags=int(val);cur["closed"]=bool(flags&1)
            if t=="POLYLINE" and flags&(8|16|64):cur["is_2d"]=False
        elif t in ("LWPOLYLINE","VERTEX"):
            if code==10:cur["_v"].append((float(val),0.,0.))
            elif code==20 and cur["_v"]:x,_,b=cur["_v"][-1];cur["_v"][-1]=(x,float(val),b)
            elif code==42 and cur["_v"]:x,y,_=cur["_v"][-1];cur["_v"][-1]=(x,y,float(val))
    flush()
    return out
def read_ezdxf(path):
    import ezdxf
    doc=ezdxf.readfile(str(path))
    out={"insunits":int(doc.header.get("$INSUNITS",0)),"modelspace":[],"blocks":defaultdict(set),"meta":{"encoding":doc.encoding,"acadver":doc.dxfversion}}
    for b in doc.blocks:
        for e in b:out["blocks"][b.name].add(e.dxf.layer)
    for e in doc.modelspace():
        t=e.dxftype();rec={"type":t,"layer":e.dxf.layer,"handle":e.dxf.handle,"closed":False,"is_2d":True,"vertices":[],"block":"","extrusion":list(e.dxf.get("extrusion",(0,0,1)))}
        if t=="LWPOLYLINE":rec["closed"]=bool(e.closed);rec["vertices"]=[(float(p[0]),float(p[1]),float(p[2])) for p in e.get_points("xyb")]
        elif t=="POLYLINE":
            rec["closed"]=bool(e.is_closed);rec["is_2d"]=bool(e.is_2d_polyline)
            rec["vertices"]=[(float(v.dxf.location.x),float(v.dxf.location.y),float(v.dxf.get("bulge",0))) for v in e.vertices]
        elif t=="INSERT":rec["block"]=e.dxf.name
        out["modelspace"].append(rec)
    return out
def read_dxf(path,reader="auto"):
    if reader in ("auto","ezdxf"):
        try:return read_ezdxf(path),"ezdxf"
        except ImportError:
            if reader=="ezdxf":raise
    return read_ascii(path),"builtin-ascii"

# ---------- geometry ----------
def boundary_points(e):
    t=e["type"]
    if t not in ("LWPOLYLINE","POLYLINE"):raise ValueError("UNSUPPORTED_ENTITY_"+t)
    if not e["is_2d"]:raise ValueError("NON2D_POLYLINE")
    v=e["vertices"]
    # Community-common: visually closed (last vertex == first) but the closed flag is unset.
    coincident=len(v)>3 and abs(v[0][0]-v[-1][0])<1e-9 and abs(v[0][1]-v[-1][1])<1e-9
    if not e["closed"] and not coincident:raise ValueError("OPEN_BOUNDARY")
    if any(abs(b)>1e-10 for _,_,b in (v[:-1] if coincident and not e["closed"] else v)):raise ValueError("CURVED_BULGE_REQUIRES_EXPLICIT_TESSELLATION")
    # Polyline vertices are OCS. Plan view (+Z) is identity; a mirrored entity (-Z) flips X; anything else is not a plan boundary.
    ex=[float(c) for c in (e.get("extrusion") or (0,0,1))]
    if abs(ex[0])>1e-9 or abs(ex[1])>1e-9 or abs(abs(ex[2])-1)>1e-9:raise ValueError("NON_PLAN_EXTRUSION")
    flip=-1. if ex[2]<0 else 1.
    pts=[[flip*x,y] for x,y,_ in v]
    # CAD often repeats the first vertex as a closing vertex; drop consecutive duplicates.
    pts=[p for i,p in enumerate(pts) if not (abs(p[0]-pts[i-1][0])<1e-12 and abs(p[1]-pts[i-1][1])<1e-12)] if len(pts)>1 else pts
    # A zero-width spike (segment doubling back on itself) leaves area unchanged but signals overlaid CAD segments.
    for i in range(len(pts)):
        a,b,c=pts[i-1],pts[i],pts[(i+1)%len(pts)]
        if K.orient(a,b,c)==0 and (b[0]-a[0])*(c[0]-b[0])+(b[1]-a[1])*(c[1]-b[1])<0:raise ValueError("OVERLAID_SEGMENT_SPIKE")
    if not K.polygon_valid(pts):raise ValueError("INVALID_POLYGON")
    return pts

def export(dxf,mapping,destination,reader="auto"):
    dxf=Path(dxf);mapping=Path(mapping);destination=Path(destination)
    config=json.loads(mapping.read_text(encoding="utf-8"))
    if not config.get("project_id") or not config.get("layers"):raise ValueError("MISSING_PROJECT_OR_LAYER_MAPPING")
    data,reader_used=read_dxf(dxf,reader)
    unit=data["insunits"];declared=config.get("meters_per_unit");drawing=UNITS.get(unit)
    scale=declared if declared is not None else drawing
    if isinstance(scale,bool) or not isinstance(scale,(float,int)) or not math.isfinite(scale) or scale<=0:raise ValueError("UNVERIFIED_DRAWING_UNITS")
    rows=[];issues=[];notices=[]
    if declared is not None and drawing is not None and abs(declared-drawing)>1e-12*max(1,drawing):
        issues.append(dict(issue="UNIT_OVERRIDE_CONFLICT",drawing_insunits=unit,drawing_meters_per_unit=drawing,declared_meters_per_unit=declared))
    mapped=set(config["layers"])
    for e in data["modelspace"]:
        if e["type"]=="INSERT":
            hidden=sorted(data["blocks"].get(e["block"],set())&mapped)
            if hidden or e["layer"] in mapped:issues.append(dict(handle=e["handle"],block=e["block"],layer=e["layer"],issue="MAPPED_GEOMETRY_INSIDE_BLOCK_NOT_EXPLODED",mapped_layers=hidden))
            continue
        if e["layer"] not in mapped:continue
        rule=config["layers"][e["layer"]]
        try:
            if rule.get("operation") not in ("ADD","SUBTRACT"):raise ValueError("OPERATION_REQUIRED")
            if not rule.get("scope") or not rule.get("level"):raise ValueError("SCOPE_LEVEL_REQUIRED")
            pts=boundary_points(e)
            if not e["closed"]:notices.append(dict(handle=e["handle"],notice="CLOSED_BY_COINCIDENT_ENDPOINTS"))
            if (e.get("extrusion") or [0,0,1])[2]<0:notices.append(dict(handle=e["handle"],notice="MIRRORED_OCS_NORMALIZED"))
            rows.append(dict(handle=e["handle"],layer=e["layer"],level=rule["level"],scope=rule["scope"],operation=rule["operation"],area_m2=K.area(pts)*scale**2,points=pts))
        except (ValueError,TypeError,KeyError) as err:
            issues.append(dict(handle=e["handle"],layer=e["layer"],issue=str(err)))
    # A mapped layer with no entities usually means a renamed/garbled (encoding) layer: silent area loss, so HOLD.
    present={e["layer"] for e in data["modelspace"]}
    for layer in sorted(mapped-present):
        if config["layers"][layer].get("optional") is True:notices.append(dict(layer=layer,notice="OPTIONAL_LAYER_ABSENT"))
        else:issues.append(dict(layer=layer,issue="MAPPED_LAYER_NOT_FOUND",drawing_layer_sample=sorted(present)[:20]))
    meta=data.get("meta") or {}
    if meta.get("encoding_note"):notices.append(dict(notice=meta["encoding_note"]))
    if not rows:raise ValueError("NO_VALID_SELECTED_BOUNDARIES:"+",".join(sorted(mapped-present)))
    rows.sort(key=lambda r:(r["level"],r["scope"],r["operation"],r["layer"],r["handle"]))
    groups=defaultdict(list)
    for r in rows:groups[(r["level"],r["scope"],r["operation"])].append(r)
    # Same-operation overlaps double count (ADD) or double deduct (SUBTRACT); exact area, shared edges allowed.
    for (level,scope,op),members in groups.items():
        for i in range(len(members)):
            for j in range(i+1,len(members)):
                a,b=members[i],members[j];ov=K.intersection_area(a["points"],b["points"])*scale**2
                if ov>EPS:
                    dup=abs(ov-a["area_m2"])<EPS and abs(ov-b["area_m2"])<EPS
                    issues.append(dict(issue="DUPLICATE_BOUNDARY" if dup else ("OVERLAPPING_ADD_BOUNDARIES" if op=="ADD" else "OVERLAPPING_SUBTRACT_BOUNDARIES"),level=level,scope=scope,handles=[a["handle"],b["handle"]],overlap_m2=round(ov,4)))
    # A deduction is only mechanically valid when fully covered by the same level/scope ADD area.
    for (level,scope,op),members in groups.items():
        if op!="SUBTRACT":continue
        adds=groups.get((level,scope,"ADD"),[])
        for s in members:
            covered=sum(K.intersection_area(s["points"],a["points"]) for a in adds)*scale**2
            if abs(covered-s["area_m2"])>EPS:issues.append(dict(issue="SUBTRACT_NOT_CONTAINED_IN_ADD",level=level,scope=scope,handle=s["handle"],area_m2=round(s["area_m2"],4),covered_m2=round(covered,4)))
    totals=defaultdict(float)
    for r in rows:totals[(r["level"],r["scope"])]+=r["area_m2"]*(1 if r["operation"]=="ADD" else -1)
    for (level,scope),v in totals.items():
        if v<0:issues.append(dict(issue="NEGATIVE_TOTAL",level=level,scope=scope))
    # Distinguish expected revision metadata changes from changes in area classification logic.
    # A revision number/date must never by itself invalidate a unchanged layer/area policy.
    mapping_logic={"project_id":config["project_id"],"layers":config["layers"],"meters_per_unit":scale}
    mapping_logic_sha256=hashlib.sha256(json.dumps(mapping_logic,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
    identity={k:config.get(k) for k in ("source_project_label","source_revision","source_issue_date") if config.get(k)}
    if not identity.get("source_revision"):notices.append(dict(notice="SOURCE_REVISION_NOT_DECLARED"))
    # ---------- outputs ----------
    allx=[x for r in rows for x,y in r["points"]];ally=[y for r in rows for x,y in r["points"]]
    minx,maxx,miny,maxy=min(allx),max(allx),min(ally),max(ally)
    span=max(maxx-minx,maxy-miny) or 1;pad=span*.03;stroke=span*.001;font=span*.015
    shapes=[]
    for r in rows:
        path=" ".join(("M" if i==0 else "L")+f"{x:.6f},{-y:.6f}" for i,(x,y) in enumerate(r["points"]))+" Z"
        label=f'{r["level"]} / {r["scope"]} / {r["layer"]} / {r["handle"]}'
        cx=sum(p[0] for p in r["points"])/len(r["points"]);cy=sum(p[1] for p in r["points"])/len(r["points"])
        color="#c0392b" if r["operation"]=="SUBTRACT" else "#1663a1"
        shapes.append(f'<path id="cad-{escape(r["handle"])}" d="{path}" fill="none" stroke="{color}" stroke-width="{stroke:.6f}"><title>{escape(label)}: {r["area_m2"]:.4f} m2</title></path>'
                      f'<text x="{cx:.6f}" y="{-cy:.6f}" font-size="{font:.6f}" text-anchor="middle" fill="{color}">{escape(r["handle"])} {r["area_m2"]:.2f}m²</text>')
    w=maxx-minx+2*pad;h=maxy-miny+2*pad
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx-pad:.6f} {-maxy-pad:.6f} {w:.6f} {h:.6f}"><title>{escape(config["project_id"])} area evidence (candidate)</title>{"".join(shapes)}</svg>'
    destination.mkdir(parents=True,exist_ok=True)
    (destination/"area_evidence.svg").write_text(svg,encoding="utf-8")
    columns=["handle","layer","level","scope","operation","area_m2"]
    with (destination/"area_evidence.csv").open("w",newline="",encoding="utf-8-sig") as f:
        wr=csv.DictWriter(f,fieldnames=columns);wr.writeheader()
        for r in rows:wr.writerow({k:round(r[k],4) if k=="area_m2" else r[k] for k in columns})
    status="HOLD" if issues else "CALCULATED_REVIEW_REQUIRED"
    overview={"schema":"ARCHIGROW_AREA_OVERVIEW_V1","project_id":config["project_id"],"source_dxf":str(dxf),"source_sha256":digest(dxf),"mapping_sha256":digest(mapping),"mapping_logic_sha256":mapping_logic_sha256,
              "reader":reader_used,"tool_version":TOOL_VERSION,"source_encoding":meta.get("encoding"),"source_acadver":meta.get("acadver"),"meters_per_unit":scale,"drawing_insunits":unit,"source_identity":identity,
              "target_identity_status":"DECLARED_BY_MAPPING" if identity.get("source_revision") else "UNVERIFIED",
              "totals":[{"level":k[0],"scope":k[1],"area_m2":round(v,4)} for k,v in sorted(totals.items())],"issues":issues,"notices":notices,
              "geometry_status":status,"legal_status":"NOT_VERIFIED","design_overview_binding":"CANDIDATE_ONLY",
              "notes":"Area scope is user-mapped, not automatically legal. FAR/GFA/footprint rules, exclusions and source revisions require independent checks. Overlap/containment checks are exact planar polygon areas; curved (bulge) boundaries are refused, not approximated."}
    (destination/"design_overview_area.json").write_text(json.dumps(overview,ensure_ascii=False,indent=2),encoding="utf-8")
    receipt={"schema":"ARCHIGROW_STAGE_RECEIPT_V1","rule":"TKY-ARCHIPIPE-001","pipeline_id":"ARCHIGROW_AREA_EVIDENCE:"+config["project_id"],"stage_id":"AREA_EVIDENCE",
             "inputs":[{"ref":str(dxf),"sha256":overview["source_sha256"]},{"ref":str(mapping),"sha256":overview["mapping_sha256"]}],
             "tool":TOOL_VERSION,"reader":reader_used,
             "outputs":[{"ref":n,"sha256":digest(destination/n)} for n in ("area_evidence.svg","area_evidence.csv","design_overview_area.json")],
             "checks":["polygon_validity","unit_resolution","same_operation_overlap_exact","subtract_containment_exact","negative_total","block_hidden_geometry"],
             "status":"HOLD" if issues else "PASS","failure_class":sorted({i["issue"] for i in issues}) or None,
             "next_route":"FIX_SOURCE_OR_MAPPING" if issues else "OVERVIEW_BIND","claim_level":"MECHANICAL_GEOMETRY_ONLY"}
    (destination/"stage_receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
    return overview
def main():
    p=argparse.ArgumentParser();p.add_argument("dxf");p.add_argument("mapping");p.add_argument("output")
    p.add_argument("--reader",choices=("auto","ezdxf","builtin"),default="auto")
    a=p.parse_args();print(json.dumps(export(a.dxf,a.mapping,a.output,a.reader),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
