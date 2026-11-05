#!/usr/bin/env python3
"""ARCHIGROW massing result (room_geometry) + explicit synthetic opening fixture -> semantic plan overlay (P7A).

Per strategy: deduplicated wall centerlines derived from the room/floor polygons, wall-thickness solids with real gaps at the
fixture's doors/windows, one semantic JSON (single authority), a native DXF R2013 (meters) and one shared browser HTML that draws
the very same JSON. Every DXF is read back with ezdxf and compared with the JSON; the HTML embedded data is compared with the JSON.
Fail closed (HOLD): a door is never inferred from TOUCHING, only drawn where the fixture names a pair that really shares a
collinear same-level segment; windows only on a proven building-outline edge of the named room. Vertical links are NOT modeled.
Mechanical geometry only: no statutory, egress, accessibility or circulation claim. Pure Python + ezdxf; no network. Python >=3.9.
"""
import argparse,hashlib,json,math,re,sys
from pathlib import Path

TOOL_VERSION="ARCHIGROW_SEMANTIC_PLAN/2026-10-28.1"
RESULT_SCHEMA="ARCHIGROW_MASSING_RESULT_V1"
FIXTURE_SCHEMA="ARCHIGROW_SEMANTIC_PLAN_FIXTURE_V1"
PLAN_SCHEMA="ARCHIGROW_SEMANTIC_PLAN_V1"
RECEIPT_SCHEMA="ARCHIGROW_SEMANTIC_PLAN_RECEIPT_V1"
APPID="ARCHIGROW_SEM"
NAME=re.compile(r"^[A-Z][A-Z0-9_]{0,39}$")
OPID=re.compile(r"^[A-Z][A-Z0-9_\-]{0,31}$")
LEVEL=re.compile(r"^[A-Za-z0-9]{1,8}$")
SHA=re.compile(r"^[0-9a-f]{64}$")
AREA_TOL_M2=0.01
COLLINEAR_TOL=1e-6
WRITE_TOL=5e-7      # coordinates are rounded to 6 decimals before they reach JSON/DXF/HTML
SIDE_PROBE_M=0.05
RANGES={"interior_thickness_m":(0.05,0.6),"exterior_thickness_m":(0.05,0.8),"end_margin_m":(0.1,1.5),"snap_tolerance_m":(0.0,0.05)}
DOOR_RANGE=(0.6,1.5)
WINDOW_RANGE=(0.4,4.0)
WALL_LAYERS=("WALL_EXT","WALL_INT","WALL_UNPROG")
LAYER_COLORS={"WALL_EXT":7,"WALL_INT":8,"WALL_UNPROG":9,"DOOR_OPENING":3,"DOOR_SWING":2,"WINDOW":4,"ROOM_REF":5,"UNPROGRAMMED_REF":1,"ANNOT":253}
CLS_LAYER={"INTERIOR":"WALL_INT","EXTERIOR":"WALL_EXT","ROOM_UNPROGRAMMED":"WALL_UNPROG","EXTERIOR_UNPROGRAMMED":None}
DISCLAIMERS=["SYNTHETIC demo geometry: no real-site, statutory, egress, accessibility, fire or structural claim.",
             "Mechanical geometry overlay on room-area polygons only; openings exist solely where the explicit fixture placed them.",
             "Unprogrammed residual is NOT a corridor. Vertical links (stairs/lifts) are NOT modeled: floors are not connected."]
LIMITATIONS=DISCLAIMERS+[
    "Door/window widths and wall thicknesses are fixture candidates, not code values; door swing is an illustrative candidate.",
    "Wall centerlines lie on room-area boundaries; wall thickness straddles them and room areas are not reduced by wall thickness.",
    "Wall solids of different runs may overlap in small end-cap squares at corners/T-junctions by design; no shared wall is drawn twice.",
    "Upstream vertices closer than snap_tolerance_m are merged for wall derivation only (listed per level); room overlay keeps original polygons.",
    "Levels without room geometry are not modeled.",
    "AutoCAD native DWG conversion: NOT_DONE in this slice (DXF R2013 only)."]

class Hold(Exception):
    pass
def hold(code):
    raise Hold(code)

# ---------- small helpers ----------
def r6(v):
    return round(float(v),6)+0.0
def pt6(p):
    return [r6(p[0]),r6(p[1])]
def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()
def sha_file(path):
    return sha_bytes(Path(path).read_bytes())
def num(v,code):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):hold(code)
    return float(v)
def _no_const(c):
    hold("JSON_NONFINITE")
def _pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d:hold("JSON_DUPLICATE_KEY")
        d[k]=v
    return d
def load_json(path,code,max_bytes=8_000_000):
    try:raw=Path(path).read_bytes()
    except OSError:hold(code+"_UNREADABLE")
    if len(raw)>max_bytes:hold(code+"_TOO_LARGE")
    try:obj=json.loads(raw.decode("utf-8"),object_pairs_hook=_pairs,parse_constant=_no_const)
    except (ValueError,UnicodeDecodeError):hold(code+"_MALFORMED")
    return obj,sha_bytes(raw)
def keys_ok(obj,allowed,required,code):
    if not isinstance(obj,dict) or set(obj)-set(allowed) or any(k not in obj for k in required):hold(code)

def poly_area(p):
    return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2)
def pip(pt,poly):
    x,y=pt;inside=False
    for i in range(len(poly)):
        x1,y1=poly[i];x2,y2=poly[(i+1)%len(poly)]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
    return inside
def seg_dist(pt,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];l2=dx*dx+dy*dy
    t=0.0 if l2==0 else max(0.0,min(1.0,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/l2))
    return math.hypot(pt[0]-a[0]-t*dx,pt[1]-a[1]-t*dy)
def poly_dist(pt,poly):
    return min(seg_dist(pt,poly[i],poly[(i+1)%len(poly)]) for i in range(len(poly)))
def inside_or_on(pt,poly,tol=1e-6):
    return poly_dist(pt,poly)<=tol or pip(pt,poly)
def _ccw(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def segs_cross(a,b,c,d):
    d1,d2,d3,d4=_ccw(c,d,a),_ccw(c,d,b),_ccw(a,b,c),_ccw(a,b,d)
    return ((d1>1e-12 and d2<-1e-12) or (d1<-1e-12 and d2>1e-12)) and ((d3>1e-12 and d4<-1e-12) or (d3<-1e-12 and d4>1e-12))
def ring(poly,code):
    if not isinstance(poly,list) or len(poly)<3 or len(poly)>400:hold(code)
    pts=[]
    for v in poly:
        if not isinstance(v,(list,tuple)) or len(v)!=2:hold(code)
        pts.append((num(v[0],code),num(v[1],code)))
    if pts[0]==pts[-1] or poly_area(pts)<1e-6:hold(code)
    n=len(pts)
    for i in range(n):
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):continue
            if segs_cross(pts[i],pts[(i+1)%n],pts[j],pts[(j+1)%n]):hold(code)
    return pts
def inner_point(poly):
    """Deterministic label point: grid sample inside the polygon maximizing distance to its boundary."""
    xs=[p[0] for p in poly];ys=[p[1] for p in poly];n=48
    best=None;bd=-1.0
    for i in range(n):
        for j in range(n):
            q=(min(xs)+(max(xs)-min(xs))*(i+0.5)/n,min(ys)+(max(ys)-min(ys))*(j+0.5)/n)
            if pip(q,poly):
                d=poly_dist(q,poly)
                if d>bd:bd=d;best=q
    return pt6(best if best else poly[0])

# ---------- input validation ----------
def validate_model(m,expect_project=None,expect_sha=None):
    """Return ({strategy:{level:{floor,rooms:{id:pts},residual,declared}}}, links-by-strategy) or raise Hold."""
    if not isinstance(m,dict) or m.get("schema")!=RESULT_SCHEMA:hold("MODEL_SCHEMA_UNSUPPORTED")
    if m.get("coordinate_units")!="m":hold("MODEL_UNITS_NOT_METERS")
    pid=m.get("project_id")
    if not isinstance(pid,str) or not pid.strip():hold("MODEL_PROJECT_ID_REQUIRED")
    if expect_project is not None and pid!=expect_project:hold("MODEL_PROJECT_MISMATCH")
    src=m.get("source_sha256")
    if not isinstance(src,str) or not SHA.match(src):hold("MODEL_SOURCE_SHA_INVALID")
    if expect_sha is not None and src!=expect_sha:hold("MODEL_SOURCE_SHA_MISMATCH")
    opts=m.get("options")
    if not isinstance(opts,list) or not opts:hold("MODEL_OPTIONS_REQUIRED")
    out={};links={}
    for o in opts:
        if not isinstance(o,dict) or not isinstance(o.get("strategy"),str) or not NAME.match(o["strategy"]) or o["strategy"] in out:hold("MODEL_STRATEGY_INVALID")
        s=o["strategy"]
        try:
            floors={}
            for f in o.get("floors") or []:
                if not isinstance(f,dict) or not isinstance(f.get("level"),str) or not LEVEL.match(f["level"]) or f["level"] in floors:hold("floor_level")
                floors[f["level"]]=ring(f.get("polygon"),"floor_polygon")
            rg=((o.get("program_allocation") or {}).get("room_geometry")) or {}
            if not isinstance(rg.get("levels"),list) or not rg["levels"]:hold("room_geometry_missing")
            lv={};seen=set()
            for L in rg["levels"]:
                name=L.get("level") if isinstance(L,dict) else None
                if not isinstance(name,str) or name not in floors or name in lv:hold("level_without_floor")
                rooms={}
                for r in L.get("rooms") or []:
                    rid=r.get("id") if isinstance(r,dict) else None
                    if not isinstance(rid,str) or not NAME.match(rid) or rid in seen:hold("room_id")
                    seen.add(rid)
                    pts=ring(r.get("polygon"),"room_polygon:"+rid)
                    if abs(poly_area(pts)-num(r.get("area_m2"),"room_area"))>AREA_TOL_M2:hold("room_area_mismatch:"+rid)
                    rooms[rid]=pts
                if not rooms:hold("level_without_rooms")
                res=None
                if isinstance(L.get("residual"),dict) and L["residual"].get("polygon"):
                    res=ring(L["residual"]["polygon"],"residual_polygon")
                lv[name]={"floor":floors[name],"rooms":rooms,"residual":res,"residual_area_declared":(L.get("residual") or {}).get("area_m2")}
            out[s]=lv
            adj=rg.get("adjacency") or {}
            links[s]=[x for x in (adj.get("links") or []) if isinstance(x,dict) and isinstance(x.get("a"),str) and isinstance(x.get("b"),str)]
        except Hold as e:
            hold("MODEL_%s:%s"%(s,e.args[0]))
    return out,links

def validate_fixture(fx,model_pid,model_src,model_file_sha):
    keys_ok(fx,{"schema","provenance","parameters","strategies"},{"schema","provenance","parameters","strategies"},"FIXTURE_KEYS")
    if fx["schema"]!=FIXTURE_SCHEMA:hold("FIXTURE_SCHEMA_UNSUPPORTED")
    pv=fx["provenance"]
    keys_ok(pv,{"project_id","source_sha256","model_sha256","note","author"},{"project_id","source_sha256"},"FIXTURE_PROVENANCE_KEYS")
    if pv["project_id"]!=model_pid:hold("FIXTURE_PROJECT_MISMATCH")
    if pv["source_sha256"]!=model_src:hold("FIXTURE_SOURCE_SHA_MISMATCH")
    if "model_sha256" in pv and pv["model_sha256"]!=model_file_sha:hold("FIXTURE_MODEL_SHA_MISMATCH")
    par=fx["parameters"]
    keys_ok(par,set(RANGES),set(RANGES),"FIXTURE_PARAMETER_KEYS")
    params={}
    for k,(lo,hi) in RANGES.items():
        v=num(par[k],"FIXTURE_PARAMETER_INVALID:"+k)
        if not lo<=v<=hi:hold("FIXTURE_PARAMETER_RANGE:"+k)
        params[k]=v
    if not isinstance(fx["strategies"],dict) or not fx["strategies"]:hold("FIXTURE_STRATEGIES_REQUIRED")
    strat={}
    for s,sv in fx["strategies"].items():
        ids=set()
        if not isinstance(s,str) or not NAME.match(s):hold("FIXTURE_STRATEGY_NAME")
        keys_ok(sv,{"levels"},{"levels"},"FIXTURE_STRATEGY_KEYS:"+s)
        if not isinstance(sv["levels"],dict) or not sv["levels"]:hold("FIXTURE_LEVELS_REQUIRED:"+s)
        lv={}
        for name,spec in sv["levels"].items():
            if not LEVEL.match(str(name)):hold("FIXTURE_LEVEL_NAME")
            keys_ok(spec,{"doors","windows"},set(),"FIXTURE_LEVEL_KEYS")
            doors=[];wins=[]
            for d in spec.get("doors",[]):
                keys_ok(d,{"id","pair","width_m","center_offset_m","swing_room","hinge","run_index"},{"id","pair","width_m","center_offset_m","swing_room","hinge"},"FIXTURE_DOOR_KEYS")
                if not isinstance(d["id"],str) or not OPID.match(d["id"]) or d["id"] in ids:hold("FIXTURE_OPENING_ID")
                ids.add(d["id"])
                pr=d["pair"]
                if not isinstance(pr,list) or len(pr)!=2 or not all(isinstance(x,str) and NAME.match(x) for x in pr) or pr[0]==pr[1]:hold("FIXTURE_DOOR_PAIR:"+d["id"])
                if d["swing_room"] not in pr or d["hinge"] not in ("start","end"):hold("FIXTURE_DOOR_SWING:"+d["id"])
                w=num(d["width_m"],"FIXTURE_DOOR_WIDTH:"+d["id"])
                if not DOOR_RANGE[0]<=w<=DOOR_RANGE[1]:hold("FIXTURE_DOOR_WIDTH_RANGE:"+d["id"])
                doors.append({**d,"pair":sorted(pr),"width_m":w,"center_offset_m":num(d["center_offset_m"],"FIXTURE_DOOR_OFFSET:"+d["id"])})
            for w_ in spec.get("windows",[]):
                keys_ok(w_,{"id","room","side","width_m","center_offset_m","run_index"},{"id","room","side","width_m","center_offset_m"},"FIXTURE_WINDOW_KEYS")
                if not isinstance(w_["id"],str) or not OPID.match(w_["id"]) or w_["id"] in ids:hold("FIXTURE_OPENING_ID")
                ids.add(w_["id"])
                if not isinstance(w_["room"],str) or not NAME.match(w_["room"]) or w_["side"] not in ("N","S","E","W"):hold("FIXTURE_WINDOW_TARGET:"+w_["id"])
                w=num(w_["width_m"],"FIXTURE_WINDOW_WIDTH:"+w_["id"])
                if not WINDOW_RANGE[0]<=w<=WINDOW_RANGE[1]:hold("FIXTURE_WINDOW_WIDTH_RANGE:"+w_["id"])
                wins.append({**w_,"width_m":w,"center_offset_m":num(w_["center_offset_m"],"FIXTURE_WINDOW_OFFSET:"+w_["id"])})
            for o in doors+wins:
                if "run_index" in o and (isinstance(o["run_index"],bool) or not isinstance(o["run_index"],int) or o["run_index"]<0):hold("FIXTURE_RUN_INDEX:"+o["id"])
            lv[str(name)]={"doors":doors,"windows":wins}
        strat[s]=lv
    return params,strat,{k:pv[k] for k in ("project_id","source_sha256")}

# ---------- wall derivation ----------
def snap_level(floor,rooms,tol):
    canon=[];snaps=[]
    def get(p,owner):
        for c in canon:
            dd=math.hypot(c[0]-p[0],c[1]-p[1])
            if dd<=tol:
                if dd>1e-9:snaps.append({"owner":owner,"from":pt6(p),"to":pt6(c),"distance_m":r6(dd)})
                return c
        canon.append(p);return p
    def clean(pts,owner):
        out=[]
        for q in pts:
            if not out or out[-1]!=q:out.append(q)
        if len(out)>1 and out[0]==out[-1]:out.pop()
        if len(out)<3 or poly_area(out)<1e-6:hold("SNAP_COLLAPSED_POLYGON:"+owner)
        return out
    sf=clean([get(p,"FLOOR") for p in floor],"FLOOR")
    sr={rid:clean([get(p,rid) for p in rooms[rid]],rid) for rid in sorted(rooms)}
    return sf,sr,canon,snaps

def split_edges(poly,canon):
    out=[]
    for i in range(len(poly)):
        p,q=poly[i],poly[(i+1)%len(poly)]
        dx,dy=q[0]-p[0],q[1]-p[1];l2=dx*dx+dy*dy;l=math.sqrt(l2)
        mids=[]
        for c in canon:
            if c==p or c==q:continue
            t=((c[0]-p[0])*dx+(c[1]-p[1])*dy)/l2
            if 1e-9<t<1-1e-9 and abs((c[0]-p[0])*dy-(c[1]-p[1])*dx)/l<=COLLINEAR_TOL:mids.append((t,c))
        chain=[p]+[c for _,c in sorted(mids)]+[q]
        out+=[(chain[k],chain[k+1]) for k in range(len(chain)-1)]
    return out

def orient(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    return (a,b) if (dx>1e-9 or (abs(dx)<=1e-9 and dy>0)) else (b,a)

def derive_runs(level,floor,rooms,params):
    """Atoms (floor+room edge pieces, deduplicated) -> classified wall runs. Raises Hold on invalid topology."""
    sf,sr,canon,snaps=snap_level(floor,rooms,params["snap_tolerance_m"])
    for rid,pts in sr.items():
        if not all(inside_or_on(p,sf) for p in pts):hold("ROOM_OUTSIDE_FLOOR:"+rid)
    atoms={}
    def add(a,b,owner):
        k=tuple(sorted((a,b)))
        atoms.setdefault(k,[]).append(owner)
    for idx,(a,b) in enumerate(split_edges(sf,canon)):add(a,b,("F","F"))
    for rid,pts in sr.items():
        for a,b in split_edges(pts,canon):add(a,b,("R",rid))
    th={"INTERIOR":params["interior_thickness_m"],"EXTERIOR":params["exterior_thickness_m"],"ROOM_UNPROGRAMMED":params["interior_thickness_m"],"EXTERIOR_UNPROGRAMMED":0.0}
    rows=[]
    for k,owners in atoms.items():
        cnt={}
        for o in owners:cnt[o]=cnt.get(o,0)+1
        keep=[o for o,c in cnt.items() if c%2]   # same owner twice on one atom = degenerate spike, cancels
        rs=sorted(o[1] for o in keep if o[0]=="R");fl=any(o[0]=="F" for o in keep)
        if len(rs)==2 and not fl:cls="INTERIOR"
        elif len(rs)==1 and fl:cls="EXTERIOR"
        elif len(rs)==1:cls="ROOM_UNPROGRAMMED"
        elif not rs and fl:cls="EXTERIOR_UNPROGRAMMED"
        elif not rs:continue
        else:hold("INVALID_TOPOLOGY:%s:%s"%(level,"+".join(rs)))
        a,b=orient(*k)
        rows.append({"a":a,"b":b,"cls":cls,"rooms":tuple(rs),"len":math.hypot(b[0]-a[0],b[1]-a[1])})
    if not rows:hold("NO_ATOMS:"+level)
    node={}
    for i,r in enumerate(rows):
        node.setdefault(r["a"],[]).append(i);node.setdefault(r["b"],[]).append(i)
    parent=list(range(len(rows)))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def unit(r):
        return ((r["b"][0]-r["a"][0])/r["len"],(r["b"][1]-r["a"][1])/r["len"])
    for n,ix in node.items():
        if len(ix)==2:
            r1,r2=rows[ix[0]],rows[ix[1]]
            u1,u2=unit(r1),unit(r2)
            if (r1["cls"],r1["rooms"])==(r2["cls"],r2["rooms"]) and abs(u1[0]*u2[1]-u1[1]*u2[0])<1e-6:parent[find(ix[0])]=find(ix[1])
    groups={}
    for i in range(len(rows)):groups.setdefault(find(i),[]).append(i)
    ext_at={}
    for n,ix in node.items():ext_at[n]=max(th[rows[i]["cls"]] for i in ix)/2
    runs=[]
    for g in groups.values():
        first=rows[g[0]];u=unit(first);o=first["a"]
        pts=[p for i in g for p in (rows[i]["a"],rows[i]["b"])]
        proj=lambda p:(p[0]-o[0])*u[0]+(p[1]-o[1])*u[1]
        a=min(pts,key=proj);b=max(pts,key=proj)
        if abs(math.hypot(b[0]-a[0],b[1]-a[1])-sum(rows[i]["len"] for i in g))>1e-6:hold("RUN_NOT_CONTIGUOUS:"+level)
        t=th[first["cls"]]
        runs.append({"cls":first["cls"],"rooms":list(first["rooms"]),"a":a,"b":b,"length":math.hypot(b[0]-a[0],b[1]-a[1]),"thickness":t,
                     "ext_a":ext_at[a] if t else 0.0,"ext_b":ext_at[b] if t else 0.0,"atoms":len(g),"u":u,"n":(-u[1],u[0])})
    runs.sort(key=lambda r:(r["cls"],r["rooms"],r["a"],r["b"]))
    cnt={}
    for r in runs:
        key=(r["cls"],tuple(r["rooms"]));k=cnt.get(key,0);cnt[key]=k+1
        r["index"]=k
        r["id"]="%s/%s/%s/%d"%(level,r["cls"],"+".join(r["rooms"]) or "FLOOR",k)
    # dedup proof: no two runs may overlap collinearly (a shared wall is one run, never two)
    for i in range(len(runs)):
        for j in range(i+1,len(runs)):
            p,q=runs[i],runs[j]
            if abs(p["u"][0]*q["u"][1]-p["u"][1]*q["u"][0])>1e-6:continue
            if abs((q["a"][0]-p["a"][0])*p["n"][0]+(q["a"][1]-p["a"][1])*p["n"][1])>COLLINEAR_TOL*10:continue
            lo=max(0.0,(q["a"][0]-p["a"][0])*p["u"][0]+(q["a"][1]-p["a"][1])*p["u"][1])
            hi=min(p["length"],(q["b"][0]-p["a"][0])*p["u"][0]+(q["b"][1]-p["a"][1])*p["u"][1])
            if hi-lo>1e-6:hold("DUPLICATE_WALL_OVERLAP:%s|%s"%(p["id"],q["id"]))
    return runs,snaps,sf

def compass(n):
    if abs(n[1])<1e-6:return "E" if n[0]>0 else "W"
    if abs(n[0])<1e-6:return "N" if n[1]>0 else "S"
    return "OBLIQUE"
def at(run,s):
    return (run["a"][0]+run["u"][0]*s,run["a"][1]+run["u"][1]*s)
def inward(run,room_poly,s):
    c=at(run,s);n=run["n"]
    p1=(c[0]+n[0]*SIDE_PROBE_M,c[1]+n[1]*SIDE_PROBE_M);p2=(c[0]-n[0]*SIDE_PROBE_M,c[1]-n[1]*SIDE_PROBE_M)
    i1,i2=pip(p1,room_poly),pip(p2,room_poly)
    if i1==i2:hold("SIDE_AMBIGUOUS")
    return n if i1 else (-n[0],-n[1])

def rect(run,s0,s1):
    h=run["thickness"]/2;u,n,a=run["u"],run["n"],run["a"]
    def P(s,k):return [r6(a[0]+u[0]*s+n[0]*k*h),r6(a[1]+u[1]*s+n[1]*k*h)]
    return [P(s0,-1),P(s1,-1),P(s1,1),P(s0,1)]

def place_openings(level,runs,orig_rooms,spec,params):
    """Validate fixture doors/windows against real run geometry; mutate runs with gaps; return door/window dicts."""
    margin=params["end_margin_m"];doors=[];wins=[]
    def pick(cands,o,what):
        cands=sorted(cands,key=lambda r:(r["a"],r["b"]))
        if not cands:hold("%s_NOT_SUPPORTED:%s"%(what,o["id"]))
        if "run_index" in o:
            if o["run_index"]>=len(cands):hold("%s_RUN_INDEX:%s"%(what,o["id"]))
            return cands[o["run_index"]]
        if len(cands)>1:hold("%s_RUN_AMBIGUOUS:%s"%(what,o["id"]))
        return cands[0]
    def interval(run,o):
        w=o["width_m"];c=o["center_offset_m"];lo,hi=c-w/2,c+w/2
        if lo<margin-1e-9 or hi>run["length"]-margin+1e-9:hold("OPENING_OUTSIDE_SEGMENT:%s(run %.4f m, need %.4f)"%(o["id"],run["length"],w+2*margin))
        return lo,hi
    for d in spec["doors"]:
        for rid in d["pair"]:
            if rid not in orig_rooms:hold("DOOR_ROOM_NOT_ON_LEVEL:%s:%s"%(d["id"],rid))
        run=pick([r for r in runs if r["cls"]=="INTERIOR" and r["rooms"]==d["pair"]],d,"DOOR")
        lo,hi=interval(run,d)
        sw=inward(run,orig_rooms[d["swing_room"]],d["center_offset_m"])
        hing=at(run,lo if d["hinge"]=="start" else hi);clo=at(run,hi if d["hinge"]=="start" else lo)
        opn=(hing[0]+sw[0]*d["width_m"],hing[1]+sw[1]*d["width_m"])
        a_c=math.degrees(math.atan2(clo[1]-hing[1],clo[0]-hing[0]));a_o=math.degrees(math.atan2(opn[1]-hing[1],opn[0]-hing[0]))
        ccw=abs(((a_o-a_c)%360)-90)<1e-6
        run.setdefault("gaps",[]).append((lo,hi,d["id"]))
        doors.append({"id":d["id"],"level":level,"kind":"DOOR","pair":d["pair"],"run":run["id"],"width_m":r6(d["width_m"]),"center_offset_m":r6(d["center_offset_m"]),
            "interval_m":[r6(lo),r6(hi)],"margin_start_m":r6(lo),"margin_end_m":r6(run["length"]-hi),"run_length_m":r6(run["length"]),"swing_room":d["swing_room"],"hinge":d["hinge"],
            "gap_polygon":rect(run,lo,hi),"hinge_point":pt6(hing),"closed_end":pt6(clo),"open_end":pt6(opn),"radius_m":r6(d["width_m"]),
            "arc_start_deg":r6(a_c if ccw else a_o),"arc_end_deg":r6(a_o if ccw else a_c),"arc_ccw_closed_to_open":ccw,
            "proof":{"basis":"collinear same-level shared wall run between both named rooms","shared_segment":[pt6(run["a"]),pt6(run["b"])],
                     "rooms_with_edge_on_segment":run["rooms"],"fixture_explicit":True,"physical_link":"DOOR_MODELED_SAME_LEVEL"}})
    for w in spec["windows"]:
        if w["room"] not in orig_rooms:hold("WINDOW_ROOM_NOT_ON_LEVEL:%s:%s"%(w["id"],w["room"]))
        cands=[]
        for r in runs:
            if r["cls"]=="EXTERIOR" and r["rooms"]==[w["room"]]:
                try:ok=compass(tuple(-x for x in inward(r,orig_rooms[w["room"]],r["length"]/2)))==w["side"]
                except Hold:ok=False
                if ok:cands.append(r)
        run=pick(cands,w,"WINDOW")
        lo,hi=interval(run,w)
        run.setdefault("gaps",[]).append((lo,hi,w["id"]))
        wins.append({"id":w["id"],"level":level,"kind":"WINDOW","room":w["room"],"side":w["side"],"run":run["id"],"width_m":r6(w["width_m"]),"center_offset_m":r6(w["center_offset_m"]),
            "interval_m":[r6(lo),r6(hi)],"margin_start_m":r6(lo),"margin_end_m":r6(run["length"]-hi),"run_length_m":r6(run["length"]),
            "gap_polygon":rect(run,lo,hi),"glaze_a":pt6(at(run,lo)),"glaze_b":pt6(at(run,hi)),
            "proof":{"basis":"run lies on the building outline (floor polygon edge) and on the named room boundary","run_class":"EXTERIOR","run_rooms":run["rooms"],
                     "shared_segment":[pt6(run["a"]),pt6(run["b"])],"outward_side":w["side"],"fixture_explicit":True}})
    for r in runs:   # opening spacing on the same run
        g=sorted(r.get("gaps",[]))
        for k in range(1,len(g)):
            if g[k][0]-g[k-1][1]<margin-1e-9:hold("OPENING_OVERLAP:%s|%s"%(g[k-1][2],g[k][2]))
    return doors,wins

def solids_for(runs):
    out=[]
    for r in runs:
        layer=CLS_LAYER[r["cls"]]
        if not layer:continue
        cur=-r["ext_a"];pieces=[]
        for lo,hi,_ in sorted(r.get("gaps",[])):
            pieces.append((cur,lo));cur=hi
        pieces.append((cur,r["length"]+r["ext_b"]))
        k=0
        for s0,s1 in pieces:
            if s1-s0<1e-6:continue
            out.append({"id":"%s#%d"%(r["id"],k),"run":r["id"],"layer":layer,"thickness_m":r6(r["thickness"]),"polygon":rect(r,s0,s1)});k+=1
    return out

def run_json(r):
    return {"id":r["id"],"class":r["cls"],"layer":CLS_LAYER[r["cls"]],"rooms":r["rooms"],"start":pt6(r["a"]),"end":pt6(r["b"]),"length_m":r6(r["length"]),
            "thickness_m":r6(r["thickness"]),"atoms_merged":r["atoms"],"openings":[g[2] for g in sorted(r.get("gaps",[]))]}

# ---------- semantic model ----------
def build_strategy(strategy,levels,links,spec,params,ctx):
    """One strategy -> semantic dict. spec: {level:{doors,windows}} from fixture."""
    for name in spec:
        if name not in levels:hold("FIXTURE_LEVEL_NOT_IN_MODEL:"+name)
    out_levels=[];all_doors=[];all_wins=[];rooms_all={}
    for name in sorted(levels):
        L=levels[name]
        runs,snaps,sf=derive_runs(name,L["floor"],L["rooms"],params)
        doors,wins=place_openings(name,runs,L["rooms"],spec.get(name,{"doors":[],"windows":[]}),params)
        solids=solids_for(runs)
        rooms=[]
        for rid in sorted(L["rooms"]):
            pts=L["rooms"][rid]
            rooms.append({"id":rid,"level":name,"polygon":[pt6(p) for p in pts],"area_m2":r6(poly_area(pts)),"label_point":inner_point(pts)})
            rooms_all[rid]=name
        res=None
        if L["residual"]:
            res={"polygon":[pt6(p) for p in L["residual"]],"area_m2":r6(poly_area(L["residual"])),"label_point":inner_point(L["residual"]),"note":"UNPROGRAMMED residual - NOT a corridor, no circulation/egress claim"}
        floor_a=poly_area(L["floor"]);room_a=sum(poly_area(p) for p in L["rooms"].values())
        by={}
        for r in runs:by[r["cls"]]=by.get(r["cls"],0)+r["length"]
        metrics={"rooms":len(rooms),"runs":len(runs),"wall_solids":len(solids),"doors":len(doors),"windows":len(wins),
                 "run_length_m_by_class":{k:r6(v) for k,v in sorted(by.items())},"wall_solid_area_m2":r6(sum(poly_area(s["polygon"]) for s in solids)),
                 "floor_area_m2":r6(floor_a),"rooms_area_m2":r6(room_a),"residual_area_derived_m2":r6(max(floor_a-room_a,0.0)),
                 "residual_area_declared_m2":L["residual_area_declared"],"snapped_vertices":len(snaps)}
        out_levels.append({"level":name,"floor_polygon":[pt6(p) for p in L["floor"]],"rooms":rooms,"runs":[run_json(r) for r in runs],"solids":solids,
                           "doors":doors,"windows":wins,"unprogrammed":res,"snaps":snaps,"metrics":metrics})
        all_doors+=doors;all_wins+=wins
    # connectivity: only modeled same-level doors; nothing is inferred
    parent={r:r for r in rooms_all}
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for d in all_doors:parent[find(d["pair"][0])]=find(d["pair"][1])
    comp={}
    for r in sorted(rooms_all):comp.setdefault(find(r),[]).append(r)
    groups=sorted(comp.values())
    doored={x for d in all_doors for x in d["pair"]}
    link_rows=[]
    for lk in links:
        a,b=lk["a"],lk["b"]
        if a not in rooms_all or b not in rooms_all:continue
        meas=None;lvl=None
        if rooms_all[a]==rooms_all[b]:
            lvl=rooms_all[a]
            lens=[r["length_m"] for L in out_levels if L["level"]==lvl for r in L["runs"] if r["class"]=="INTERIOR" and sorted(r["rooms"])==sorted([a,b])]
            meas=r6(sum(lens)) if lens else 0.0
        has=[d["id"] for d in all_doors if sorted(d["pair"])==sorted([a,b])]
        if has:st="DOOR_MODELED"
        elif rooms_all[a]!=rooms_all[b]:st="UNRESOLVED_VERTICAL_LINK_NOT_MODELED"
        elif meas and meas>0:st="TOUCHING_NO_DOOR_MODELED"
        else:st="NOT_TOUCHING"
        link_rows.append({"a":a,"b":b,"p2_status":lk.get("status"),"p2_shared_boundary_m":lk.get("shared_boundary_m"),"measured_shared_run_m":meas,"status":st,"doors":has,
                          "boundary_note":None if meas is None or lk.get("shared_boundary_m") is None or abs(meas-lk["shared_boundary_m"])<=0.05 else "MEASURED_DIFFERS_FROM_P2"})
    unresolved=[l for l in link_rows if l["status"]!="DOOR_MODELED"]
    room_status=[]
    for r in sorted(rooms_all):
        if r in doored:st="DOOR_LINKED_SAME_LEVEL_ONLY"
        else:st="UNKNOWN_NO_MODELED_DOOR_OR_VERTICAL_LINK"
        room_status.append({"room":r,"level":rooms_all[r],"status":st,"door_linked_group":next(g for g in groups if r in g),"accessible":"NOT_CLAIMED"})
    for L in out_levels:
        for rm in L["rooms"]:rm["connectivity"]=next(x["status"] for x in room_status if x["room"]==rm["id"])
    conn={"status":"UNRESOLVED_LINKS_REMAIN" if unresolved else "REQUESTED_LINKS_RESOLVED_SAME_LEVEL_DOORS_ONLY","vertical_links":"NOT_MODELED",
          "doors_modeled":len(all_doors),"door_linked_groups":groups,"links":link_rows,"unresolved_links":len(unresolved),"rooms":room_status,
          "note":"Door-linked group = rooms joined by modeled same-level doors; it is NOT an accessibility, egress or circulation claim."}
    total={"levels":len(out_levels),"rooms":len(rooms_all),"doors":len(all_doors),"windows":len(all_wins),"wall_solids":sum(len(L["solids"]) for L in out_levels),
           "runs":sum(len(L["runs"]) for L in out_levels)}
    primary=next((L["level"] for L in out_levels if L["doors"] or L["windows"]),out_levels[0]["level"])
    return {"schema":PLAN_SCHEMA,"tool_version":TOOL_VERSION,"strategy":strategy,"project_id":ctx["project_id"],"source_sha256":ctx["source_sha256"],
            "model_sha256":ctx["model_sha256"],"fixture_sha256":ctx["fixture_sha256"],"coordinate_units":"m","claim_level":"MECHANICAL_GEOMETRY_ONLY",
            "input_source_role":ctx.get("input_source_role"),"rule_source_status":ctx.get("rule_source_status"),"legal_feasibility_authorized":False,
            "parameters":params,"primary_level":primary,"disclaimers":DISCLAIMERS,"layers":list(LAYER_COLORS),"levels":out_levels,"connectivity":conn,"metrics":total,
            "limitations":LIMITATIONS}

# ---------- DXF ----------
def layer_name(base,level):
    return "%s__%s"%(base,level)
def write_dxf(sm,path):
    import ezdxf
    doc=ezdxf.new("R2013",setup=True)
    doc.units=ezdxf.units.M
    doc.header["$MEASUREMENT"]=1
    doc.appids.new(APPID)
    msp=doc.modelspace()
    def tag(e,i):
        e.set_xdata(APPID,[(1000,i)])
    for L in sm["levels"]:
        for base,col in LAYER_COLORS.items():
            ly=doc.layers.add(layer_name(base,L["level"]),color=col)
            if L["level"]!=sm["primary_level"]:ly.off()
        lay=lambda b:{"layer":layer_name(b,L["level"])}
        for s in L["solids"]:tag(msp.add_lwpolyline(s["polygon"],close=True,dxfattribs=lay(s["layer"])),s["id"])
        for d in L["doors"]:
            tag(msp.add_lwpolyline(d["gap_polygon"],close=True,dxfattribs=lay("DOOR_OPENING")),d["id"])
            tag(msp.add_line(d["hinge_point"],d["open_end"],dxfattribs=lay("DOOR_SWING")),d["id"]+":LEAF")
            tag(msp.add_arc(d["hinge_point"],d["radius_m"],d["arc_start_deg"],d["arc_end_deg"],dxfattribs=lay("DOOR_SWING")),d["id"]+":ARC")
        for w in L["windows"]:
            tag(msp.add_lwpolyline(w["gap_polygon"],close=True,dxfattribs=lay("WINDOW")),w["id"])
            tag(msp.add_line(w["glaze_a"],w["glaze_b"],dxfattribs=lay("WINDOW")),w["id"]+":GLAZE")
        for rm in L["rooms"]:
            tag(msp.add_lwpolyline(rm["polygon"],close=True,dxfattribs=lay("ROOM_REF")),rm["id"])
            t=msp.add_text("%s %.1f m2"%(rm["id"],rm["area_m2"]),dxfattribs={"height":0.5,"layer":layer_name("ROOM_REF",L["level"]),"insert":tuple(rm["label_point"])})
            tag(t,rm["id"]+":LABEL")
        u=L["unprogrammed"]
        if u:
            tag(msp.add_lwpolyline(u["polygon"],close=True,dxfattribs=lay("UNPROGRAMMED_REF")),"UNPROGRAMMED_"+L["level"])
            tag(msp.add_text("UNPROGRAMMED %.1f m2 (NOT corridor)"%u["area_m2"],dxfattribs={"height":0.5,"layer":layer_name("UNPROGRAMMED_REF",L["level"]),"insert":tuple(u["label_point"])}),"UNPROGRAMMED_%s:LABEL"%L["level"])
        ys=[p[1] for p in L["floor_polygon"]];x0=min(p[0] for p in L["floor_polygon"])
        notes=["%s | %s | level %s | SEMANTIC PLAN OVERLAY (P7A) - mechanical geometry only"%(sm["project_id"],sm["strategy"],L["level"])]+sm["disclaimers"]
        for i,txt in enumerate(notes):
            tag(msp.add_text(txt,dxfattribs={"height":0.45,"layer":layer_name("ANNOT",L["level"]),"insert":(x0,min(ys)-1.5-i*0.8)}),"ANNOT_%s_%d"%(L["level"],i))
    doc.saveas(path)

def readback_dxf(path,sm,expected_doors,expected_windows):
    """Independent re-read of the DXF; returns list of (check, ok, detail). Compares against the semantic dict."""
    import ezdxf
    checks=[]
    def chk(n,ok,d=""):checks.append((n,bool(ok),str(d)))
    try:doc=ezdxf.readfile(path)
    except Exception as e:
        chk("ezdxf.readfile",False,type(e).__name__);return checks
    chk("dxf_version_R2013",doc.dxfversion=="AC1027",doc.dxfversion)
    chk("insunits_meters",doc.header.get("$INSUNITS")==6,doc.header.get("$INSUNITS"))
    auditor=doc.audit();chk("ezdxf_audit_clean",not auditor.errors,len(auditor.errors))
    ents={}
    for e in doc.modelspace():ents.setdefault(e.dxf.layer,[]).append(e)
    expected_layers={layer_name(b,L["level"]) for L in sm["levels"] for b in LAYER_COLORS}
    chk("layers_present",all(l in doc.layers for l in expected_layers),len(expected_layers))
    chk("no_unexpected_layer",set(ents)<=expected_layers,sorted(set(ents)-expected_layers))
    def xid(e):
        x=e.get_xdata(APPID);return x[0].value if x else None
    def close(a,b):return len(a)==len(b) and all(abs(p[0]-q[0])<=WRITE_TOL and abs(p[1]-q[1])<=WRITE_TOL for p,q in zip(a,b))
    finite=True;wall_ok=True;zero=False;n_doors=n_wins=0;geom_ok=True
    for L in sm["levels"]:
        lv=L["level"]
        for base in WALL_LAYERS:
            got={xid(e):[(p[0],p[1]) for p in e.get_points("xy")] for e in ents.get(layer_name(base,lv),[]) if e.dxftype()=="LWPOLYLINE"}
            exp={s["id"]:s["polygon"] for s in L["solids"] if s["layer"]==base}
            wall_ok&=(set(got)==set(exp) and len(got)==len(ents.get(layer_name(base,lv),[])))
            for i,pg in got.items():
                if i not in exp:continue
                geom_ok&=close(pg,exp[i]) and len(pg)==4
                finite&=all(math.isfinite(c) for p in pg for c in p)
                zero|=any(math.hypot(pg[k][0]-pg[(k+1)%4][0],pg[k][1]-pg[(k+1)%4][1])<1e-6 for k in range(4))
        chk("%s_wall_solids_match_model"%lv,wall_ok,sum(len(L["solids"]) for L in sm["levels"]))
        dop=[e for e in ents.get(layer_name("DOOR_OPENING",lv),[])];leaf=[e for e in ents.get(layer_name("DOOR_SWING",lv),[]) if e.dxftype()=="LINE"]
        arc=[e for e in ents.get(layer_name("DOOR_SWING",lv),[]) if e.dxftype()=="ARC"]
        ok=len(dop)==len(leaf)==len(arc)==len(L["doors"]) and {xid(e) for e in dop}=={d["id"] for d in L["doors"]}
        dm={d["id"]:d for d in L["doors"]}
        for e in dop:
            if xid(e) in dm:geom_ok&=close([(p[0],p[1]) for p in e.get_points("xy")],dm[xid(e)]["gap_polygon"])
        for e in arc:
            d=dm.get(xid(e)[:-4]) if xid(e) else None
            if d:geom_ok&=abs(e.dxf.radius-d["radius_m"])<=WRITE_TOL and abs(e.dxf.start_angle-d["arc_start_deg"])<1e-4 and abs(e.dxf.end_angle-d["arc_end_deg"])<1e-4 and abs(e.dxf.center[0]-d["hinge_point"][0])<=WRITE_TOL
            else:ok=False
        chk("%s_door_counts_ids"%lv,ok,"%d doors"%len(dop));n_doors+=len(dop)
        wp=[e for e in ents.get(layer_name("WINDOW",lv),[]) if e.dxftype()=="LWPOLYLINE"];wl=[e for e in ents.get(layer_name("WINDOW",lv),[]) if e.dxftype()=="LINE"]
        wm={w["id"]:w for w in L["windows"]}
        chk("%s_window_counts_ids"%lv,len(wp)==len(wl)==len(L["windows"]) and {xid(e) for e in wp}==set(wm),"%d windows"%len(wp));n_wins+=len(wp)
        for e in wp:
            if xid(e) in wm:geom_ok&=close([(p[0],p[1]) for p in e.get_points("xy")],wm[xid(e)]["gap_polygon"])
        rr=[e for e in ents.get(layer_name("ROOM_REF",lv),[]) if e.dxftype()=="LWPOLYLINE"]
        rm={r["id"]:r for r in L["rooms"]}
        chk("%s_room_ref_match"%lv,len(rr)==len(rm) and {xid(e) for e in rr}==set(rm) and all(close([(p[0],p[1]) for p in e.get_points("xy")],rm[xid(e)]["polygon"]) for e in rr if xid(e) in rm),len(rr))
        up=[e for e in ents.get(layer_name("UNPROGRAMMED_REF",lv),[]) if e.dxftype()=="LWPOLYLINE"]
        chk("%s_unprogrammed_ref"%lv,len(up)==(1 if L["unprogrammed"] else 0) and all(close([(p[0],p[1]) for p in e.get_points("xy")],L["unprogrammed"]["polygon"]) for e in up),len(up))
    chk("wall_solids_exact_vs_model",wall_ok and geom_ok,"")
    chk("native_geometry_finite",finite,"")
    chk("no_zero_length_wall_edge",not zero,"")
    chk("door_total_equals_fixture",n_doors==expected_doors,"%d/%d"%(n_doors,expected_doors))
    chk("window_total_equals_fixture",n_wins==expected_windows,"%d/%d"%(n_wins,expected_windows))
    return checks

# ---------- HTML ----------
HTML_TEMPLATE=r"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ARCHIGROW 시맨틱 평면 오버레이 (P7A)</title>
<style>
:root{--bg:#f4f1ea;--ink:#1b1b1b;--mut:#6b675e;--wext:#1f1f1f;--wint:#4a4a4a;--wun:#8a7b66;--door:#0a7d3c;--win:#0b6fb8;--room:#2d6a9f;--un:#c0392b}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,"Malgun Gothic",sans-serif;background:var(--bg);color:var(--ink);display:flex;flex-direction:column;height:100vh}
header{padding:8px 14px;background:#222;color:#fff}h1{font-size:15px;margin:0 0 4px}.disc{font-size:12px;color:#ffd9a0}.disc div{margin:0}
.bar{display:flex;flex-wrap:wrap;gap:6px 18px;padding:8px 14px;background:#e6e1d6;border-bottom:1px solid #c9c2b2;align-items:center}
.bar button{border:1px solid #888;background:#fff;padding:4px 10px;border-radius:4px;cursor:pointer;font:inherit}.bar button[aria-pressed=true]{background:#222;color:#fff}
.bar label{display:inline-flex;align-items:center;gap:3px;font-size:12px}.sw{width:12px;height:12px;display:inline-block;border:1px solid #555}
main{flex:1;display:flex;min-height:0}#view{flex:1;min-width:0;background:#fff;position:relative}#svg{width:100%;height:100%;cursor:grab;touch-action:none}
aside{width:380px;overflow:auto;border-left:1px solid #c9c2b2;padding:10px 12px;background:#faf8f3;font-size:12.5px}aside h2{font-size:13px;margin:10px 0 4px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:2px 4px;text-align:left;vertical-align:top}.hold{color:#b00020;font-weight:700}.ok{color:#0a7d3c;font-weight:700}
.cap{position:absolute;left:8px;bottom:6px;font-size:11px;color:var(--mut);background:#ffffffd0;padding:2px 6px;border-radius:3px}
</style></head><body>
<header><h1>ARCHIGROW 시맨틱 평면 오버레이 (P7A) — 벽·개구부 후보 (합성 데모)</h1><div class="disc" id="disc"></div></header>
<div class="bar"><span>전략:</span><span id="strats"></span><span>층:</span><span id="levels"></span><span id="layers"></span></div>
<main><div id="view"><svg id="svg" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="semantic floor plan"></svg><div class="cap" id="cap"></div></div>
<aside id="info"></aside></main>
<script id="semantic-data" type="application/json">__DATA_JSON__</script>
<script>
"use strict";
const DATA=JSON.parse(document.getElementById("semantic-data").textContent);
const NS="http://www.w3.org/2000/svg";
const LAYERS={WALL_EXT:["외벽 WALL_EXT","#1f1f1f"],WALL_INT:["내벽 WALL_INT","#4a4a4a"],WALL_UNPROG:["미배정 접경벽 WALL_UNPROG","#8a7b66"],ROOM_REF:["실 영역 ROOM_REF","#2d6a9f"],DOOR_OPENING:["문 개구부 DOOR_OPENING","#0a7d3c"],DOOR_SWING:["문 스윙(예시) DOOR_SWING","#0a7d3c"],WINDOW:["창 WINDOW","#0b6fb8"],UNPROGRAMMED_REF:["미배정 잔여 UNPROGRAMMED_REF","#c0392b"]};
const st={s:DATA.strategies[0]?DATA.strategies[0].strategy:null,l:null,on:{},vb:null,sel:null};
Object.keys(LAYERS).forEach(k=>st.on[k]=true);
const $=id=>document.getElementById(id);
function el(tag,attrs,parent,text){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(text!==undefined)e.textContent=text;if(parent)parent.appendChild(e);return e}
function h(tag,attrs,parent,text){const e=document.createElement(tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(text!==undefined)e.textContent=text;if(parent)parent.appendChild(e);return e}
const P=(poly)=>poly.map((p,i)=>(i?"L":"M")+p[0]+","+(-p[1])).join(" ")+" Z";
const cur=()=>DATA.strategies.find(x=>x.strategy===st.s);
const lvl=()=>cur().levels.find(x=>x.level===st.l);
function setStrategy(s){st.s=s;const c=cur();if(!c.levels.find(x=>x.level===st.l))st.l=c.primary_level;st.sel=null;fit();ui();draw()}
function fit(){const L=lvl();const xs=L.floor_polygon.map(p=>p[0]),ys=L.floor_polygon.map(p=>-p[1]);const m=3;const x0=Math.min(...xs)-m,y0=Math.min(...ys)-m;st.vb=[x0,y0,Math.max(...xs)-Math.min(...xs)+2*m,Math.max(...ys)-Math.min(...ys)+2*m+4]}
function ui(){
  const D=$("disc");D.textContent="";(cur().disclaimers).forEach(t=>h("div",{},D,"⚠ "+t));
  const S=$("strats");S.textContent="";DATA.strategies.forEach(x=>{const b=h("button",{"aria-pressed":String(x.strategy===st.s),"data-strategy":x.strategy},S,x.strategy);b.onclick=()=>setStrategy(x.strategy)});
  const V=$("levels");V.textContent="";cur().levels.forEach(x=>{const b=h("button",{"aria-pressed":String(x.level===st.l),"data-level":x.level},V,x.level+(x.level===cur().primary_level?" (개구부)":""));b.onclick=()=>{st.l=x.level;st.sel=null;fit();ui();draw()}});
  const Y=$("layers");Y.textContent="";Object.keys(LAYERS).forEach(k=>{const lb=h("label",{},Y);const sw=h("span",{"class":"sw"},lb);sw.style.background=LAYERS[k][1];const cb=h("input",{type:"checkbox","data-layer":k},lb);cb.checked=st.on[k];cb.onchange=()=>{st.on[k]=cb.checked;draw()};lb.appendChild(document.createTextNode(LAYERS[k][0]))});
  info();
}
function row(t,k,v,cls){const r=h("tr",{},t);h("td",{},r,k);h("td",cls?{"class":cls}:{},r,String(v))}
function info(){
  const A=$("info");A.textContent="";const c=cur(),L=lvl();
  h("h2",{},A,"전략 "+c.strategy+" · 층 "+L.level);
  const t=h("table",{},A);const m=L.metrics;
  row(t,"문 / 창 (이 층)",m.doors+" / "+m.windows);row(t,"문 / 창 (전략 전체)",c.metrics.doors+" / "+c.metrics.windows);
  row(t,"벽 런(중복제거) / 솔리드",m.runs+" / "+m.wall_solids);row(t,"벽 솔리드 면적 m²",m.wall_solid_area_m2);
  row(t,"실 면적 합 / 층 면적 m²",m.rooms_area_m2+" / "+m.floor_area_m2);row(t,"미배정 잔여 m² (복도 아님)",m.residual_area_derived_m2);
  row(t,"외벽 두께 / 내벽 두께 m",c.parameters.exterior_thickness_m+" / "+c.parameters.interior_thickness_m);row(t,"스냅된 꼭짓점",m.snapped_vertices);
  h("h2",{},A,"연결성 (모델된 문만)");const cn=c.connectivity;const t2=h("table",{},A);
  row(t2,"상태",cn.status,"hold");row(t2,"수직 연결(계단/EV)",cn.vertical_links,"hold");
  cn.links.forEach(l=>row(t2,l.a+"–"+l.b,l.status+(l.doors.length?" ["+l.doors.join(",")+"]":""),l.status==="DOOR_MODELED"?"ok":"hold"));
  cn.rooms.forEach(r=>row(t2,r.room+" ("+r.level+")",r.status+" · accessible="+r.accessible));
  h("p",{},A,cn.note);
  h("h2",{},A,"선택 항목");const sel=h("div",{id:"sel"},A);
  if(st.sel){const t3=h("table",{},sel);for(const k in st.sel)row(t3,k,typeof st.sel[k]==="object"?JSON.stringify(st.sel[k]):st.sel[k])}else h("p",{},sel,"실/문/창을 클릭하세요.");
  h("h2",{},A,"한계");const u=h("ul",{},A);c.limitations.forEach(x=>h("li",{},u,x));
}
function draw(){
  const svg=$("svg");svg.textContent="";const L=lvl();const [x,y,w,hh]=st.vb;svg.setAttribute("viewBox",x+" "+y+" "+w+" "+hh);
  const g=(name)=>el("g",{"data-layer":name,display:st.on[name]?"inline":"none"},svg);
  const select=(o)=>()=>{st.sel=o;info()};
  const gf=el("path",{d:P(L.floor_polygon),fill:"#faf7ef",stroke:"#bbb","stroke-width":"0.05","stroke-dasharray":"0.3 0.2","data-role":"floor"},svg);
  const gu=g("UNPROGRAMMED_REF");if(L.unprogrammed){const p=el("path",{d:P(L.unprogrammed.polygon),fill:"#c0392b22",stroke:"#c0392b","stroke-width":"0.06","stroke-dasharray":"0.4 0.25","data-id":"UNPROGRAMMED_"+L.level},gu);p.onclick=select({구분:"미배정 잔여 (복도 아님)","면적 m²":L.unprogrammed.area_m2});el("text",{x:L.unprogrammed.label_point[0],y:-L.unprogrammed.label_point[1],"font-size":"0.5","text-anchor":"middle",fill:"#c0392b"},gu,"미배정 "+L.unprogrammed.area_m2+" m² (복도 아님)")}
  const gr=g("ROOM_REF");L.rooms.forEach(r=>{const p=el("path",{d:P(r.polygon),fill:"#2d6a9f26",stroke:"#2d6a9f","stroke-width":"0.05","data-id":r.id},gr);p.onclick=select({실:r.id,층:r.level,"면적 m²":r.area_m2,연결성:r.connectivity,접근성:"NOT_CLAIMED"});
    el("text",{x:r.label_point[0],y:-r.label_point[1],"font-size":"0.6","text-anchor":"middle","font-weight":"700",fill:"#123"},gr,r.id);el("text",{x:r.label_point[0],y:-r.label_point[1]+0.8,"font-size":"0.5","text-anchor":"middle",fill:"#345"},gr,r.area_m2+" m²")});
  ["WALL_UNPROG","WALL_INT","WALL_EXT"].forEach(name=>{const gw=g(name);L.solids.filter(s=>s.layer===name).forEach(s=>{const p=el("path",{d:P(s.polygon),fill:LAYERS[name][1],"data-id":s.id,"data-layer-item":name},gw);p.onclick=select({벽솔리드:s.id,런:s.run,"두께 m":s.thickness_m})})});
  const gd=g("DOOR_OPENING"),gs=g("DOOR_SWING");L.doors.forEach(d=>{const p=el("path",{d:P(d.gap_polygon),fill:"#d9f2e1",stroke:"#0a7d3c","stroke-width":"0.04","data-id":d.id},gd);p.onclick=select({문:d.id,쌍:d.pair.join("–"),"폭 m":d.width_m,"공유구간 길이 m":d.run_length_m,"여유(시작/끝) m":d.margin_start_m+" / "+d.margin_end_m,스윙측:d.swing_room,근거:d.proof.basis,물리연결:d.proof.physical_link});
    el("line",{x1:d.hinge_point[0],y1:-d.hinge_point[1],x2:d.open_end[0],y2:-d.open_end[1],stroke:"#0a7d3c","stroke-width":"0.06","data-id":d.id+":LEAF"},gs);
    el("path",{d:"M"+d.closed_end[0]+","+(-d.closed_end[1])+" A"+d.radius_m+","+d.radius_m+" 0 0 "+(d.arc_ccw_closed_to_open?1:0)+" "+d.open_end[0]+","+(-d.open_end[1]),fill:"none",stroke:"#0a7d3c","stroke-width":"0.04","stroke-dasharray":"0.2 0.12","data-id":d.id+":ARC"},gs)});
  const gw2=g("WINDOW");L.windows.forEach(w=>{const p=el("path",{d:P(w.gap_polygon),fill:"#d6ebfa",stroke:"#0b6fb8","stroke-width":"0.04","data-id":w.id},gw2);p.onclick=select({창:w.id,실:w.room,외측:w.side,"폭 m":w.width_m,"외벽 구간 길이 m":w.run_length_m,근거:w.proof.basis});
    el("line",{x1:w.glaze_a[0],y1:-w.glaze_a[1],x2:w.glaze_b[0],y2:-w.glaze_b[1],stroke:"#0b6fb8","stroke-width":"0.07","data-id":w.id+":GLAZE"},gw2)});
  $("cap").textContent="휠: 확대/축소 · 드래그: 이동 · 단위 m · "+cur().claim_level;
}
const svgEl=$("svg");
svgEl.addEventListener("wheel",e=>{e.preventDefault();const r=svgEl.getBoundingClientRect(),f=e.deltaY<0?0.85:1/0.85,[x,y,w,hh]=st.vb;const mx=x+(e.clientX-r.left)/r.width*w,my=y+(e.clientY-r.top)/r.height*hh;st.vb=[mx-(mx-x)*f,my-(my-y)*f,w*f,hh*f];svgEl.setAttribute("viewBox",st.vb.join(" "))},{passive:false});
let drag=null;svgEl.addEventListener("pointerdown",e=>{drag={x:e.clientX,y:e.clientY,vb:st.vb.slice()}});
window.addEventListener("pointermove",e=>{if(!drag)return;const r=svgEl.getBoundingClientRect();st.vb=[drag.vb[0]-(e.clientX-drag.x)/r.width*drag.vb[2],drag.vb[1]-(e.clientY-drag.y)/r.height*drag.vb[3],drag.vb[2],drag.vb[3]];svgEl.setAttribute("viewBox",st.vb.join(" "))});
window.addEventListener("pointerup",()=>{drag=null});
if(st.s){st.l=cur().primary_level;fit();ui();draw()}
</script></body></html>"""

def render_html(plans,holds):
    data={"schema":"ARCHIGROW_SEMANTIC_PLAN_VIEWER_DATA_V1","strategies":plans,"held_strategies":holds}
    blob=json.dumps(data,ensure_ascii=True,separators=(",",":"),sort_keys=True).replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    return HTML_TEMPLATE.replace("__DATA_JSON__",blob)
def html_data(text):
    m=re.search(r'<script id="semantic-data" type="application/json">(.*?)</script>',text,re.S)
    return json.loads(m.group(1)) if m else None

# ---------- main ----------
def write_json(path,obj):
    Path(path).write_text(json.dumps(obj,indent=1,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
def out_ref(path,name):
    return {"file":name,"sha256":sha_file(path),"bytes":Path(path).stat().st_size}

def run(model_path,fixture_path,out_dir,expect_project=None,expect_source_sha=None):
    out=Path(out_dir)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):hold("OUT_DIR_NOT_FRESH")
    out.mkdir(parents=True,exist_ok=True)
    receipt={"schema":RECEIPT_SCHEMA,"tool_version":TOOL_VERSION,"tool_sha256":sha_file(__file__),"claim_level":"MECHANICAL_GEOMETRY_ONLY","status":"HOLD",
             "hold_reason":None,"strategies":{},"limitations":LIMITATIONS,"dwg":{"status":"NOT_DONE","reason":"AutoCAD DWG conversion not implemented in this slice; DXF R2013 only"},
             "release_status":"DEMO_GEOMETRY_ONLY__LEGAL_AND_DESIGN_REVIEW_PENDING"}
    try:
        try:
            import ezdxf  # noqa: F401
        except ImportError:
            hold("EZDXF_MISSING")
        model,msha=load_json(model_path,"MODEL")
        fx,fsha=load_json(fixture_path,"FIXTURE")
        receipt["model"]={"file":Path(model_path).name,"sha256":msha,"source_sha256":model.get("source_sha256") if isinstance(model,dict) else None,"project_id":model.get("project_id") if isinstance(model,dict) else None}
        receipt["fixture"]={"file":Path(fixture_path).name,"sha256":fsha}
        levels_by,links_by=validate_model(model,expect_project,expect_source_sha)
        params,fxs,prov=validate_fixture(fx,model["project_id"],model["source_sha256"],msha)
        for s in fxs:
            if s not in levels_by:hold("FIXTURE_STRATEGY_NOT_IN_MODEL:"+s)
    except Hold as e:
        receipt["hold_reason"]=e.args[0]
        write_json(out/"semantic_plan_receipt.json",receipt);return receipt
    ctx={"project_id":model["project_id"],"source_sha256":model["source_sha256"],"model_sha256":msha,"fixture_sha256":fsha,
         "input_source_role":model.get("input_source_role"),"rule_source_status":model.get("rule_source_status")}
    plans=[];holds={}
    for s in sorted(levels_by):
        rec={"status":"HOLD","reasons":[],"outputs":{},"readback":[]}
        receipt["strategies"][s]=rec
        try:
            if s not in fxs:hold("NO_FIXTURE_FOR_STRATEGY")
            sm=build_strategy(s,levels_by[s],links_by.get(s,[]),fxs[s],params,ctx)
            exp_d=sum(len(v["doors"]) for v in fxs[s].values());exp_w=sum(len(v["windows"]) for v in fxs[s].values())
            jp=out/("semantic_plan_%s.json"%s);dp=out/("semantic_plan_%s.dxf"%s)
            write_json(jp,sm);write_dxf(sm,str(dp))
            loaded,_=load_json(jp,"PLAN")      # DXF is judged against the JSON as stored on disk
            checks=readback_dxf(str(dp),loaded,exp_d,exp_w)
            rec["readback"]=[{"check":n,"ok":ok,"detail":d} for n,ok,d in checks]
            bad=[n for n,ok,_ in checks if not ok]
            if bad:hold("DXF_READBACK_FAILED:"+",".join(bad))
            rec["outputs"]={"json":out_ref(jp,jp.name),"dxf":out_ref(dp,dp.name)}
            rec["counts"]={"doors":sm["metrics"]["doors"],"windows":sm["metrics"]["windows"],"wall_solids":sm["metrics"]["wall_solids"],"rooms":sm["metrics"]["rooms"]}
            rec["connectivity"]={"status":sm["connectivity"]["status"],"unresolved_links":sm["connectivity"]["unresolved_links"],"vertical_links":"NOT_MODELED",
                                 "rooms_without_modeled_door":[r["room"] for r in sm["connectivity"]["rooms"] if r["status"].startswith("UNKNOWN")]}
            rec["status"]="PASS";plans.append(loaded)
        except Hold as e:
            rec["reasons"].append(e.args[0]);holds[s]=e.args[0]
            for f in (out/("semantic_plan_%s.json"%s),out/("semantic_plan_%s.dxf"%s)):
                if f.exists():f.unlink()   # no artifact survives a HOLD
            rec["outputs"]={}
    if plans:
        hp=out/"semantic_plan_viewer.html"
        hp.write_text(render_html(plans,holds),encoding="utf-8")
        d=html_data(hp.read_text(encoding="utf-8"))
        same=d is not None and d["strategies"]==plans
        receipt["html"]={**out_ref(hp,hp.name),"embedded_data_equals_plan_json":same,"browser_render_verified":"NOT_CLAIMED_BY_TOOL"}
        if not same:
            for rec in receipt["strategies"].values():
                if rec["status"]=="PASS":rec["status"]="HOLD";rec["reasons"].append("HTML_DATA_MISMATCH")
    receipt["status"]="PASS" if receipt["strategies"] and all(r["status"]=="PASS" for r in receipt["strategies"].values()) else "HOLD"
    if receipt["status"]=="HOLD":receipt["hold_reason"]="STRATEGY_HOLD"
    write_json(out/"semantic_plan_receipt.json",receipt)
    return receipt

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("result");p.add_argument("--fixture",required=True);p.add_argument("--out-dir",required=True)
    p.add_argument("--expect-project",default=None);p.add_argument("--expect-source-sha256",default=None)
    a=p.parse_args(argv)
    try:rc=run(a.result,a.fixture,a.out_dir,a.expect_project,a.expect_source_sha256)
    except Hold as e:
        print("HOLD",e.args[0]);return 2
    print(rc["status"],rc.get("hold_reason") or "")
    for s,r in rc["strategies"].items():print(" ",s,r["status"],r.get("counts") or r["reasons"])
    return 0 if rc["status"]=="PASS" else 2

if __name__=="__main__":
    sys.exit(main())
