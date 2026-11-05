#!/usr/bin/env python3
"""ARCHIGROW massing result (room_geometry) -> per-strategy native DXF R2013 + area mapping + compact stage receipt.

Consumes ARCHIGROW_MASSING_RESULT_V1 only; fail closed (HOLD) on missing provenance, wrong project, no rooms or malformed polygons.
Every DXF is read back with ezdxf (audit, closure, exact area, containment, overlap, closure sum) and then judged by the
existing ARCHIGROW_AREA_DXF_SVG.export() consumer. Geometrical draft only: no statutory GFA, corridor, egress or law assertion.
Requires ezdxf (already installed). Python >=3.9.
"""
import argparse,hashlib,importlib.util,json,math,re,shutil
from pathlib import Path

TOOL_VERSION="ARCHIGROW_MASSING_DXF/2026-10-27.1"
HERE=Path(__file__).resolve().parent
RESULT_SCHEMA="ARCHIGROW_MASSING_RESULT_V1"
RECEIPT_SCHEMA="ARCHIGROW_MASSING_DXF_RECEIPT_V1"
APPID="ARCHIGROW"
AREA_TOL_M2=0.01      # area / closure tolerance required by the handoff contract
OVERLAP_TOL_M2=1e-4   # shared edges are allowed, any area overlap above this is a HOLD
COORD_TOL=1e-9        # DXF doubles must round-trip
KINDS=("ENVELOPE","PROGRAM","UNPROGRAMMED")  # kind == area QA scope, one layer per option+floor+kind
COLORS={"ENVELOPE":8,"PROGRAM":5,"UNPROGRAMMED":1}
NAME=re.compile(r"^[A-Z][A-Z0-9_]*$")
LEVEL=re.compile(r"^[A-Za-z0-9]+$")
SHA=re.compile(r"^[0-9a-f]{64}$")
LIMITATIONS=["Geometrical draft only; no building-code, statutory GFA, FAR, egress or circulation assertion.",
             "UNPROGRAMMED is the unallocated floor remainder, not a corridor and not egress.",
             "ENVELOPE is geometric context in its own scope; it is never added to PROGRAM/UNPROGRAMMED totals.",
             "Floors without room geometry are not exported.",
             "Input data are user-explicit and unverified; not a portfolio-level release."]

class Hold(Exception):
    pass

def _load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
K=_load("archigrow_layout_kpi","ARCHIGROW_LAYOUT_KPI.py")
AREA=_load("archigrow_area_dxf_svg","ARCHIGROW_AREA_DXF_SVG.py")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def hold(code):
    raise Hold(code)
def ring(poly,code):
    if not K.polygon_valid(poly):hold(code)
    pts=[(float(x),float(y)) for x,y in poly]
    if len(pts)>3 and pts[0]==pts[-1]:hold(code)  # closing vertex repeated: ambiguous, refuse rather than reinterpret
    return pts
def num(v,code):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):hold(code)
    return float(v)

# ---------- input validation (everything is checked before any file is written) ----------
def validate(result,expect_project=None):
    """Return [{strategy, levels:[{level,floor,rooms:[(id,pts)],residual:pts|None}]}] or raise Hold."""
    if not isinstance(result,dict) or result.get("schema")!=RESULT_SCHEMA:hold("SCHEMA_UNSUPPORTED")
    pid=str(result.get("project_id") or "").strip()
    if not pid:hold("PROJECT_ID_REQUIRED")
    if expect_project is not None and pid!=expect_project:hold("PROJECT_MISMATCH:%s!=%s"%(pid,expect_project))
    if not SHA.match(str(result.get("source_sha256") or "")):hold("SOURCE_SHA256_MISSING_OR_INVALID")
    if result.get("coordinate_units")!="m":hold("COORDINATE_UNITS_NOT_METERS")
    options=result.get("options")
    if not isinstance(options,list) or not options:hold("OPTIONS_MISSING")
    out=[];seen=set()
    for o in options:
        if not isinstance(o,dict):hold("OPTION_MALFORMED")
        strategy=o.get("strategy")
        if not isinstance(strategy,str) or not NAME.match(strategy):hold("STRATEGY_NAME_INVALID")
        if strategy in seen:hold("DUPLICATE_STRATEGY:"+strategy)
        seen.add(strategy)
        pa=o.get("program_allocation")
        rg=pa.get("room_geometry") if isinstance(pa,dict) else None
        if not isinstance(rg,dict):hold("ROOM_GEOMETRY_MISSING:"+strategy)
        if rg.get("project_id")!=pid:hold("ROOM_GEOMETRY_PROJECT_MISMATCH:"+strategy)
        lm=o.get("layout_model")
        if isinstance(lm,dict) and lm.get("project_id") not in (None,pid):hold("LAYOUT_MODEL_PROJECT_MISMATCH:"+strategy)
        if rg.get("mode")!="POLYGON_PARTITION_V1" or not rg.get("source_status") or not rg.get("representation"):hold("ROOM_GEOMETRY_PROVENANCE_MISSING:"+strategy)
        if rg.get("building_code_compliance") is not False:hold("BUILDING_CODE_CLAIM_NOT_ALLOWED:"+strategy)
        floors={}
        for f in o.get("floors") or []:
            if not isinstance(f,dict) or not isinstance(f.get("level"),str) or not LEVEL.match(f["level"]) or f["level"] in floors:hold("FLOOR_MALFORMED:"+strategy)
            floors[f["level"]]=f
        levels=rg.get("levels")
        if not isinstance(levels,list) or not levels:hold("NO_ROOM_LEVELS:"+strategy)
        ids=set();rows=[]
        for lv in levels:
            if not isinstance(lv,dict) or lv.get("level") not in floors:hold("LEVEL_WITHOUT_FLOOR:%s"%strategy)
            L=lv["level"]
            where="%s:%s"%(strategy,L)
            floor=ring(floors[L].get("polygon"),"FLOOR_POLYGON_INVALID:"+where)
            if abs(K.area(floor)-num(lv.get("floor_area_m2"),"FLOOR_AREA_INVALID:"+where))>AREA_TOL_M2:hold("FLOOR_AREA_MISMATCH:"+where)
            rooms=lv.get("rooms")
            if not isinstance(rooms,list) or not rooms:hold("NO_ROOMS:"+where)
            parts=[]
            for r in rooms:
                rid=r.get("id") if isinstance(r,dict) else None
                if not isinstance(rid,str) or not rid.strip():hold("ROOM_ID_MISSING:"+where)
                if rid in ids:hold("DUPLICATE_ROOM_ID:"+rid)
                ids.add(rid)
                pts=ring(r.get("polygon"),"ROOM_POLYGON_INVALID:"+rid)
                if abs(K.area(pts)-num(r.get("area_m2"),"ROOM_AREA_INVALID:"+rid))>AREA_TOL_M2:hold("ROOM_AREA_TAMPERED:"+rid)
                parts.append((rid,pts))
            res=lv.get("residual");residual=None
            if res is not None:
                if not isinstance(res,dict) or res.get("kind")!="UNPROGRAMMED_NOT_CORRIDOR":hold("RESIDUAL_KIND_INVALID:"+where)
                residual=ring(res.get("polygon"),"RESIDUAL_POLYGON_INVALID:"+where)
                if abs(K.area(residual)-num(res.get("area_m2"),"RESIDUAL_AREA_INVALID:"+where))>AREA_TOL_M2:hold("RESIDUAL_AREA_TAMPERED:"+where)
            check_geometry(floor,parts,residual,where)
            rows.append({"level":L,"floor":floor,"rooms":parts,"residual":residual})
        rows.sort(key=lambda r:r["level"])
        out.append({"strategy":strategy,"levels":rows,"floors_without_rooms":sorted(set(floors)-{r["level"] for r in rows})})
    return pid,out

def check_geometry(floor,parts,residual,where):
    """Containment, no overlap, closure; used for input and again on DXF read-back points."""
    members=[(k,p) for k,p in parts]+([("RESIDUAL",residual)] if residual else [])
    for k,p in members:
        if abs(K.intersection_area(p,floor)-K.area(p))>OVERLAP_TOL_M2:hold("POLYGON_OUTSIDE_FLOOR:%s:%s"%(where,k))
    for i in range(len(members)):
        for j in range(i+1,len(members)):
            if K.intersection_area(members[i][1],members[j][1])>OVERLAP_TOL_M2:hold("POLYGON_OVERLAP:%s:%s,%s"%(where,members[i][0],members[j][0]))
    if abs(K.area(floor)-sum(K.area(p) for _,p in members))>AREA_TOL_M2:hold("AREA_CLOSURE_FAILED:"+where)

# ---------- writer ----------
def layer_of(strategy,level,kind):
    return "%s_%s_%s"%(strategy,level,kind)
def level_key(strategy,level):
    return "%s_%s"%(strategy,level)

def write_dxf(pid,opt,path):
    import ezdxf
    from ezdxf import units
    doc=ezdxf.new("R2013",setup=False)
    doc.units=units.M
    doc.header["$MEASUREMENT"]=1
    doc.appids.add(APPID)
    msp=doc.modelspace()
    s=opt["strategy"]
    def add(layer,pts,kind,level,design_id,design_label):
        if layer not in doc.layers:doc.layers.add(layer,color=COLORS[kind])
        e=msp.add_lwpolyline(pts,format="xy",close=True,dxfattribs={"layer":layer})
        # AREA_QA_SCOPE is the only value the area consumer may use; DESIGN_* are labels without legal meaning.
        e.set_xdata(APPID,[(1000,"AREA_QA_SCOPE="+kind),(1000,"OPTION="+s),(1000,"LEVEL="+level),
                           (1000,"DESIGN_ID="+design_id),(1000,"DESIGN_LABEL="+design_label),(1000,"LEGAL_AREA_CLASS=NONE")])
    for lv in opt["levels"]:
        L=lv["level"]
        add(layer_of(s,L,"ENVELOPE"),lv["floor"],"ENVELOPE",L,"FLOOR_"+L,"ACTIVE_FLOOR_ENVELOPE_CONTEXT")
        for rid,pts in lv["rooms"]:add(layer_of(s,L,"PROGRAM"),pts,"PROGRAM",L,rid,"PROGRAM_ROOM")
        if lv["residual"]:add(layer_of(s,L,"UNPROGRAMMED"),lv["residual"],"UNPROGRAMMED",L,"UNPROGRAMMED_"+L,"UNPROGRAMMED_NOT_CORRIDOR")
    doc.saveas(str(path))

def mapping_for(pid,opt,result_sha):
    layers={}
    for lv in opt["levels"]:
        for kind in KINDS:
            if kind=="UNPROGRAMMED" and not lv["residual"]:continue
            layers[layer_of(opt["strategy"],lv["level"],kind)]={"level":level_key(opt["strategy"],lv["level"]),"scope":kind,"operation":"ADD"}
    return {"project_id":pid,"source_project_label":"ARCHIGROW_MASSING:"+opt["strategy"],"source_revision":"massing_result_sha256:"+result_sha[:16],
            "layers":layers,"note":"scope is AREA QA scope only (geometric draft); not a statutory area class"}

# ---------- read-back ----------
def read_back(dxf,opt):
    """Independent re-read of the written DXF; returns (layer_counts, totals{(level_key,kind):m2}) or raises Hold."""
    import ezdxf
    try:
        doc=ezdxf.readfile(str(dxf))
    except Exception as err:
        hold("DXF_READ_FAILED:%s"%type(err).__name__)
    aud=doc.audit()
    if aud.errors:hold("DXF_AUDIT_ERRORS:%d"%len(aud.errors))
    if doc.dxfversion!="AC1027":hold("DXF_VERSION_NOT_R2013")
    if int(doc.header.get("$INSUNITS",0))!=6:hold("DXF_INSUNITS_NOT_METERS")
    s=opt["strategy"]
    found={}
    for e in doc.modelspace():
        if e.dxftype()!="LWPOLYLINE" or not e.closed:hold("DXF_ENTITY_NOT_CLOSED_LWPOLYLINE")
        xd=dict(v[1].split("=",1) for v in e.get_xdata(APPID))
        found.setdefault(e.dxf.layer,[]).append(([(float(x),float(y)) for x,y in e.get_points("xy")],xd))
    expected={}
    for lv in opt["levels"]:
        L=lv["level"]
        expected[layer_of(s,L,"ENVELOPE")]=[("FLOOR_"+L,lv["floor"])]
        expected[layer_of(s,L,"PROGRAM")]=list(lv["rooms"])
        if lv["residual"]:expected[layer_of(s,L,"UNPROGRAMMED")]=[("UNPROGRAMMED_"+L,lv["residual"])]
    if set(found)!=set(expected):hold("DXF_LAYER_SET_MISMATCH")
    for layer,want in expected.items():
        got=found[layer]
        if len(got)!=len(want):hold("DXF_ENTITY_COUNT_MISMATCH:"+layer)
        for (rid,pts),(rpts,xd) in zip(want,got):
            if len(pts)!=len(rpts) or any(abs(a[0]-b[0])>COORD_TOL or abs(a[1]-b[1])>COORD_TOL for a,b in zip(pts,rpts)):hold("DXF_VERTEX_MISMATCH:%s:%s"%(layer,rid))
            if abs(K.area(pts)-K.area(rpts))>AREA_TOL_M2:hold("DXF_AREA_MISMATCH:%s:%s"%(layer,rid))
            if xd.get("DESIGN_ID")!=rid or xd.get("AREA_QA_SCOPE")!=layer.rsplit("_",1)[1]:hold("DXF_XDATA_MISMATCH:%s:%s"%(layer,rid))
    # geometry checks on the polygons actually read from the file
    totals={}
    for lv in opt["levels"]:
        L=lv["level"];where="%s:%s"%(s,L)
        floor=found[layer_of(s,L,"ENVELOPE")][0][0]
        rooms=[(xd["DESIGN_ID"],p) for p,xd in found[layer_of(s,L,"PROGRAM")]]
        resl=found.get(layer_of(s,L,"UNPROGRAMMED"))
        check_geometry(floor,rooms,resl[0][0] if resl else None,where)
        k=level_key(s,L)
        totals[(k,"ENVELOPE")]=K.area(floor)
        totals[(k,"PROGRAM")]=sum(K.area(p) for _,p in rooms)
        if resl:totals[(k,"UNPROGRAMMED")]=K.area(resl[0][0])
    return {l:len(v) for l,v in sorted(found.items())},totals

def consume(pid,opt,dxf,mapping_path,dest,totals):
    """Judge the DXF with the existing area evidence consumer; its stage receipt must be PASS with no issues."""
    try:
        overview=AREA.export(dxf,mapping_path,dest,"ezdxf")
    except Exception as err:
        hold("AREA_CONSUMER_FAILED:%s:%s"%(type(err).__name__,err))
    receipt=json.loads((Path(dest)/"stage_receipt.json").read_text(encoding="utf-8"))
    if receipt.get("status")!="PASS" or overview.get("issues"):hold("AREA_CONSUMER_NOT_PASS:%s"%",".join(receipt.get("failure_class") or ["ISSUES"]))
    if overview.get("reader")!="ezdxf" or overview.get("meters_per_unit")!=1.0:hold("AREA_CONSUMER_UNITS_OR_READER")
    got={(t["level"],t["scope"]):t["area_m2"] for t in overview["totals"]}
    if set(got)!=set(totals):hold("AREA_CONSUMER_TOTAL_KEYS_MISMATCH")
    for key,want in totals.items():
        if abs(got[key]-want)>AREA_TOL_M2:hold("AREA_CONSUMER_TOTAL_MISMATCH:%s/%s"%key)
    for lv in opt["levels"]:
        k=level_key(opt["strategy"],lv["level"])
        if abs(got[(k,"ENVELOPE")]-got[(k,"PROGRAM")]-got.get((k,"UNPROGRAMMED"),0.0))>AREA_TOL_M2:hold("AREA_CONSUMER_CLOSURE_FAILED:"+k)
    return receipt["status"],overview["geometry_status"],got

# ---------- orchestration ----------
OWNED_FILES=lambda s:{"massing_%s.dxf"%s,"massing_%s_area_mapping.json"%s,"area_evidence"}
def prepare_dir(d,s):
    if d.exists():
        if not d.is_dir() or {p.name for p in d.iterdir()}-OWNED_FILES(s):hold("OUTPUT_DIR_NOT_GENERATOR_OWNED:"+d.name)
        shutil.rmtree(d)
    d.mkdir(parents=True)

def build(result_path,out_dir,expect_project=None):
    result_path=Path(result_path);out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    input_sha=sha(result_path)
    receipt={"schema":RECEIPT_SCHEMA,"rule":"TKY-ARCHIPIPE-001","stage_id":"MASSING_DXF_HANDOFF","tool":TOOL_VERSION,
             "inputs":[{"ref":str(result_path),"sha256":input_sha}],"source_sha256":None,"project_id":None,"options":[],
             "status":"HOLD","failure_class":None,"limitations":LIMITATIONS,"legal_status":"NOT_VERIFIED",
             "claim_level":"MECHANICAL_GEOMETRY_ONLY","release_scope":"LOCAL_GEOMETRY_HANDOFF_NOT_PORTFOLIO_RELEASE"}
    made=[]
    try:
        try:
            result=json.loads(result_path.read_bytes().decode("utf-8-sig"))
        except (ValueError,OSError):
            hold("RESULT_JSON_UNREADABLE")
        pid,options=validate(result,expect_project)
        receipt.update(project_id=pid,source_sha256=result["source_sha256"],pipeline_id="ARCHIGROW_MASSING_DXF:"+pid)
        for opt in options:
            s=opt["strategy"];d=out/s
            prepare_dir(d,s);made.append(d)
            dxf=d/("massing_%s.dxf"%s);mp=d/("massing_%s_area_mapping.json"%s)
            write_dxf(pid,opt,dxf)
            mp.write_text(json.dumps(mapping_for(pid,opt,input_sha),ensure_ascii=False,indent=2),encoding="utf-8")
            counts,totals=read_back(dxf,opt)
            area_status,geom_status,got=consume(pid,opt,dxf,mp,d/"area_evidence",totals)
            receipt["options"].append({"strategy":s,"status":"PASS","dxf":{"ref":str(dxf),"sha256":sha(dxf)},
                "mapping":{"ref":str(mp),"sha256":sha(mp)},
                "area_stage_receipt":{"ref":str(d/"area_evidence"/"stage_receipt.json"),"sha256":sha(d/"area_evidence"/"stage_receipt.json"),"status":area_status,"geometry_status":geom_status},
                "layer_entity_counts":counts,"entity_count":sum(counts.values()),"floors_without_rooms":opt["floors_without_rooms"],
                "totals":[{"level":k[0],"scope":k[1],"area_m2":round(v,4)} for k,v in sorted(got.items())],
                "checks":["ezdxf_audit_0_errors","insunits_6_r2013","closed_lwpolyline","vertex_roundtrip","area_le_0.01","inside_floor","no_overlap","closure_le_0.01","xdata_room_id","area_consumer_PASS"]})
        receipt["status"]="PASS"
    except Hold as h:
        # No partial export may stand: remove everything generated in this run.
        for d in made:shutil.rmtree(d,ignore_errors=True)
        receipt["options"]=[];receipt["failure_class"]=str(h)
    (out/"massing_dxf_receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("result");p.add_argument("--out-dir",required=True)
    p.add_argument("--expect-project",default=None,help="fail closed unless the result belongs to this project_id")
    a=p.parse_args()
    r=build(a.result,a.out_dir,a.expect_project)
    print(json.dumps({"status":r["status"],"project_id":r["project_id"],"failure":r["failure_class"],
                      "options":[{"strategy":o["strategy"],"entities":o["entity_count"],"dxf":o["dxf"]["ref"],"dxf_sha256":o["dxf"]["sha256"]} for o in r["options"]],
                      "receipt":str(Path(a.out_dir)/"massing_dxf_receipt.json"),"legal_status":r["legal_status"]},ensure_ascii=False))
    return 0 if r["status"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
