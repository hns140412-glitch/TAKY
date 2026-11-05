#!/usr/bin/env python3
"""ARCHIGROW massing result (room_geometry) -> single self-contained 2D floor-plan candidate viewer (HTML) + stage receipt.

Consumes ARCHIGROW_MASSING_RESULT_V1 only; fail closed (HOLD, nothing written) on wrong schema/project, missing provenance,
missing room geometry, malformed polygons, area-accounting mismatch or inconsistent link status.
Shows measured geometry only: floor outer polygon, room polygons, UNPROGRAMMED_NOT_CORRIDOR residual, measured shared-boundary
link statuses. No walls, doors, circulation, egress or legal claim is drawn or implied. Standard library only. Python >=3.9.
"""
import argparse,hashlib,json,math,os,re
from pathlib import Path

TOOL_VERSION="ARCHIGROW_MASSING_2D_VIEWER/2026-10-27.1"
RESULT_SCHEMA="ARCHIGROW_MASSING_RESULT_V1"
RECEIPT_SCHEMA="ARCHIGROW_MASSING_2D_VIEWER_RECEIPT_V1"
AREA_TOL_M2=0.05
SHA=re.compile(r"^[0-9a-f]{64}$")
LINK_STATUSES=("TOUCHING","SAME_LEVEL_NOT_TOUCHING","DIFFERENT_LEVEL_NO_PLAN_CONTACT")
LIMITATIONS=["Geometrical draft only: no walls, doors, openings, circulation path, egress or building-code assertion.",
             "TOUCHING means a measured shared plan boundary (shared wall line only); it is NOT a door or passage.",
             "UNPROGRAMMED_NOT_CORRIDOR is the unallocated floor remainder, not a corridor and not egress.",
             "CIRCULATION category, if present, is a user-specified space, not a verified corridor.",
             "Generated HTML has not been opened in a browser by this tool: render, interaction and visual QA are NOT performed.",
             "No DWG/DXF QA is performed by this stage. Input data are user-explicit and unverified."]

class Hold(Exception):
    pass

def hold(code):
    raise Hold(code)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def num(v,code):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):hold(code)
    return float(v)

def ring(p,code):
    if not isinstance(p,list) or len(p)<3:hold(code)
    pts=[]
    for q in p:
        if not isinstance(q,(list,tuple)) or len(q)!=2:hold(code)
        pts.append([num(q[0],code),num(q[1],code)])
    if pts[0]==pts[-1]:pts.pop()
    if len(pts)<3 or abs(shoelace(pts))<1e-6:hold(code)
    return pts

def rings(p,code):
    """One ring or a list of rings -> list of rings."""
    if isinstance(p,list) and p and isinstance(p[0],(list,tuple)) and p[0] and isinstance(p[0][0],(list,tuple)):
        return [ring(r,code) for r in p]
    return [ring(p,code)]

def shoelace(r):
    return sum(r[i][0]*r[(i+1)%len(r)][1]-r[(i+1)%len(r)][0]*r[i][1] for i in range(len(r)))/2

def area(rs):
    return sum(abs(shoelace(r)) for r in rs)

def validate(result,expect_project):
    """Returns (project_id, strategies payload list). Raises Hold(code)."""
    if not isinstance(result,dict) or result.get("schema")!=RESULT_SCHEMA:hold("SCHEMA_UNSUPPORTED")
    pid=result.get("project_id")
    if not isinstance(pid,str) or not pid:hold("PROJECT_ID_MISSING")
    if pid!=expect_project:hold("PROJECT_MISMATCH")
    if not isinstance(result.get("source_sha256"),str) or not SHA.match(result["source_sha256"]):hold("SOURCE_SHA_MISSING")
    options=result.get("options")
    if not isinstance(options,list) or not options:hold("OPTIONS_MISSING")
    sp=result.get("spatial_program") if isinstance(result.get("spatial_program"),dict) else {}
    entrance=sp.get("entrance_space_id")
    ranking={r.get("strategy"):r for r in sp.get("ranking",[]) if isinstance(r,dict)}
    out=[];seen=set()
    for idx,opt in enumerate(options):
        if not isinstance(opt,dict) or not isinstance(opt.get("strategy"),str) or not opt["strategy"]:hold("STRATEGY_MISSING")
        s=opt["strategy"]
        if s in seen:hold("STRATEGY_DUPLICATE")
        seen.add(s)
        pa=opt.get("program_allocation");rg=pa.get("room_geometry") if isinstance(pa,dict) else None
        if not isinstance(rg,dict) or not isinstance(rg.get("levels"),list) or not rg["levels"]:hold("ROOM_GEOMETRY_MISSING")
        if rg.get("project_id",pid)!=pid:hold("PROJECT_MISMATCH")
        if rg.get("building_code_compliance") is True:hold("LEGAL_CLAIM_UNEXPECTED")
        spaces={}
        for sp_ in pa.get("spaces") or []:
            if not isinstance(sp_,dict) or not isinstance(sp_.get("id"),str):hold("SPACES_MALFORMED")
            spaces[sp_["id"]]={"name":str(sp_.get("name") or sp_["id"]),"category":str(sp_.get("category") or "UNSPECIFIED"),"level":sp_.get("level")}
        floors={}
        for f in opt.get("floors") or []:
            if isinstance(f,dict) and isinstance(f.get("level"),str):floors[f["level"]]=f
        levels=[];ids=set();nrooms=0
        for L in rg["levels"]:
            if not isinstance(L,dict) or not isinstance(L.get("level"),str):hold("ROOM_GEOMETRY_MISSING")
            lv=L["level"]
            if lv not in floors:hold("FLOOR_POLYGON_MISSING")
            fr=[ring(floors[lv].get("polygon"),"FLOOR_POLYGON_INVALID")]
            fa=area(fr)
            if abs(fa-num(L.get("floor_area_m2"),"FLOOR_AREA_INVALID"))>AREA_TOL_M2:hold("AREA_MISMATCH")
            rooms=[];rsum=0.0
            if not isinstance(L.get("rooms"),list) or not L["rooms"]:hold("ROOM_GEOMETRY_MISSING")
            for r in L["rooms"]:
                if not isinstance(r,dict) or not isinstance(r.get("id"),str):hold("ROOM_MALFORMED")
                rid=r["id"]
                if rid in ids:hold("ROOM_DUPLICATE")
                if rid not in spaces:hold("ROOM_SPACE_REF_UNKNOWN")
                ids.add(rid)
                rr=rings(r.get("polygon"),"ROOM_POLYGON_INVALID");ra=area(rr)
                if abs(ra-num(r.get("area_m2"),"ROOM_AREA_INVALID"))>AREA_TOL_M2:hold("AREA_MISMATCH")
                rsum+=ra;nrooms+=1
                rooms.append({"id":rid,"name":spaces[rid]["name"],"category":spaces[rid]["category"],"rings":rr,
                              "area_m2":round(ra,4),"requested_area_m2":r.get("requested_area_m2")})
            res=L.get("residual") if isinstance(L.get("residual"),dict) else {}
            resr=rings(res["polygon"],"RESIDUAL_POLYGON_INVALID") if res.get("polygon") else []
            resa=area(resr)
            if abs(resa-float(res.get("area_m2") or 0))>AREA_TOL_M2:hold("AREA_MISMATCH")
            if abs(rsum+resa-fa)>AREA_TOL_M2:hold("AREA_MISMATCH")
            levels.append({"level":lv,"floor_rings":fr,"floor_area_m2":round(fa,4),"rooms":rooms,"rooms_area_m2":round(rsum,4),
                           "residual_rings":resr,"residual_area_m2":round(resa,4),"residual_kind":"UNPROGRAMMED_NOT_CORRIDOR",
                           "stated":L.get("accounting") if isinstance(L.get("accounting"),dict) else {}})
        if not nrooms:hold("ROOM_GEOMETRY_MISSING")
        adj=rg.get("adjacency") if isinstance(rg.get("adjacency"),dict) else {}
        links=[];lk=set()
        for src,flag in ((adj.get("links") or [],False),(adj.get("unmet") or [],True)):
            for l in src:
                if not isinstance(l,dict) or l.get("a") not in spaces or l.get("b") not in spaces:hold("LINK_REF_UNKNOWN")
                st=l.get("status")
                if st not in LINK_STATUSES:hold("LINK_STATUS_UNKNOWN")
                sb=num(l.get("shared_boundary_m",0.0),"LINK_BOUNDARY_INVALID")
                if (st=="TOUCHING")!=(sb>0):hold("LINK_STATUS_INCONSISTENT")
                if (st=="DIFFERENT_LEVEL_NO_PLAN_CONTACT")==(spaces[l["a"]]["level"]==spaces[l["b"]]["level"]):hold("LINK_STATUS_INCONSISTENT")
                key=(tuple(sorted((l["a"],l["b"]))),st)
                if key in lk:continue
                lk.add(key)
                links.append({"a":l["a"],"b":l["b"],"status":st,"shared_boundary_m":round(sb,4),"weight":l.get("weight"),"listed_as_unmet":flag})
        if entrance is not None and entrance not in spaces:hold("ENTRANCE_REF_UNKNOWN")
        rk=ranking.get(s,{})
        out.append({"strategy":s,"rank":rk.get("rank",pa.get("rank")),"score":rk.get("score",pa.get("score")),"tied":rk.get("tied",pa.get("tied")),
                    "spaces":spaces,"levels":levels,"links":links,"_idx":idx})
    out.sort(key=lambda o:(o["rank"] if isinstance(o["rank"],(int,float)) and not isinstance(o["rank"],bool) else 1e9,o["_idx"]))
    for o in out:o.pop("_idx")
    return pid,entrance,out

def embed(payload):
    """JSON safe inside <script type=application/json>: no raw '<', '>', '&' or U+2028/9."""
    s=json.dumps(payload,ensure_ascii=True,separators=(",",":"))
    return s.replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")

def sha_str(b):
    return hashlib.sha256(b).hexdigest()

def render_html(pid,entrance,strategies,source_sha,input_sha):
    payload={"project_id":pid,"entrance_space_id":entrance,"source_sha256":source_sha,"input_file_sha256":input_sha,
             "tool":TOOL_VERSION,"strategies":strategies}
    return TEMPLATE.replace("__VIEWER_DATA__",embed(payload))

def build(result_path,out_html,expect_project,receipt_path=None):
    result_path=Path(result_path);out_html=Path(out_html)
    receipt={"schema":RECEIPT_SCHEMA,"rule":"TKY-ARCHIPIPE-001","stage_id":"MASSING_2D_VIEWER","tool":TOOL_VERSION,
             "inputs":[{"ref":str(result_path),"sha256":None}],"source_sha256":None,"project_id":None,"output":None,
             "status":"HOLD","failure_class":None,"strategies":[],"limitations":LIMITATIONS,"legal_status":"NOT_VERIFIED",
             "claim_level":"MECHANICAL_GEOMETRY_ONLY","render_verification":"NOT_PERFORMED","dwg_qa":"NOT_PERFORMED",
             "acceptance":"NOT_CLAIMED","release_scope":"LOCAL_EXPLORATION_VIEWER_NOT_RELEASE"}
    try:
        try:
            raw=result_path.read_bytes()
            receipt["inputs"][0]["sha256"]=sha_str(raw)
            result=json.loads(raw.decode("utf-8-sig"))
        except (ValueError,OSError):
            hold("RESULT_JSON_UNREADABLE")
        pid,entrance,strategies=validate(result,expect_project)
        html=render_html(pid,entrance,strategies,result["source_sha256"],receipt["inputs"][0]["sha256"]).encode("utf-8")
        out_html.parent.mkdir(parents=True,exist_ok=True)
        tmp=out_html.with_name(out_html.name+".tmp")
        tmp.write_bytes(html);os.replace(tmp,out_html)
        receipt.update(status="GENERATED_UNVERIFIED_RENDER",project_id=pid,source_sha256=result["source_sha256"],
                       output={"ref":str(out_html),"sha256":sha_str(html),"bytes":len(html)},
                       strategies=[{"strategy":o["strategy"],"rank":o["rank"],"floors":[l["level"] for l in o["levels"]],
                                    "rooms":sum(len(l["rooms"]) for l in o["levels"]),
                                    "link_status_counts":{k:sum(1 for x in o["links"] if x["status"]==k) for k in LINK_STATUSES}} for o in strategies])
    except Hold as h:
        receipt["failure_class"]=str(h)
    if receipt_path:
        rp=Path(receipt_path);rp.parent.mkdir(parents=True,exist_ok=True)
        rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("result");p.add_argument("--out",required=True,help="output viewer.html")
    p.add_argument("--expect-project",required=True,help="fail closed unless the result belongs to this project_id")
    p.add_argument("--receipt",default=None,help="optional stage receipt JSON path")
    a=p.parse_args()
    r=build(a.result,a.out,a.expect_project,a.receipt)
    print(json.dumps({"status":r["status"],"failure":r["failure_class"],"project_id":r["project_id"],
                      "output":r["output"],"receipt":a.receipt,"render_verification":r["render_verification"],
                      "legal_status":r["legal_status"]},ensure_ascii=False))
    return 0 if r["output"] else 2

TEMPLATE=r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ARCHIGROW 2D 평면 후보 뷰어</title>
<style>
:root{--bg:#f6f8fc;--card:#fff;--ink:#27324a;--mut:#6b7794;--line:#dfe5f1;--acc:#6c8cff;--warn:#fff1f0;--warnl:#e5484d}
*{box-sizing:border-box}body{margin:0;font:13px/1.45 system-ui,"Malgun Gothic",sans-serif;background:var(--bg);color:var(--ink)}
header{padding:10px 14px;background:#fff;border-bottom:1px solid var(--line)}h1{margin:0;font-size:15px}
.sub{color:var(--mut);font-size:11px;word-break:break-all}
.banner{margin:8px 14px 0;padding:8px 12px;border:2px solid var(--warnl);background:var(--warn);color:#b42318;font-weight:700;border-radius:8px;text-align:center;font-size:14px}
.banner small{display:block;font-weight:600;font-size:11px}
main{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(280px,1fr);gap:10px;padding:10px 14px}
@media(max-width:820px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:10px}
.card h2{margin:0 0 6px;font-size:12px;color:var(--mut);letter-spacing:.02em}
.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:6px}
select,button{font:inherit;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:#f2f5ff;color:var(--ink)}
button{cursor:pointer}button:hover{background:#e4eaff}
#stage{width:100%;height:min(62vh,560px);min-height:300px;background:#fbfcff;border:1px solid var(--line);border-radius:8px;touch-action:none;cursor:grab;display:block}
table{width:100%;border-collapse:collapse;font-size:12px}th,td{text-align:left;padding:3px 5px;border-bottom:1px solid var(--line)}
tr.sel td{background:#eef2ff}tr.click{cursor:pointer}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;border:1px solid #8a94ad;margin-right:4px;vertical-align:-1px}
.hatch{background:repeating-linear-gradient(45deg,#c9cfdd 0 2px,#fff 2px 5px)}
.tag{display:inline-block;padding:0 6px;border-radius:9px;font-size:11px;border:1px solid var(--line)}
.t-TOUCHING{background:#e6f6ec;color:#1e6b3a}.t-SAME_LEVEL_NOT_TOUCHING{background:#fff4e0;color:#8a5a00}.t-DIFFERENT_LEVEL_NO_PLAN_CONTACT{background:#eceff5;color:#4a5570}
.note{color:var(--mut);font-size:11px;margin:4px 0}.k{color:var(--mut)}
.split{display:flex;height:10px;border-radius:5px;overflow:hidden;border:1px solid var(--line);margin:4px 0}
#info div{margin:2px 0}
</style></head><body>
<header><h1>ARCHIGROW 2D 평면 후보 뷰어 <span class="tag">탐색용 기하 초안</span></h1>
<div class="sub" id="prov"></div></header>
<div class="banner" id="banner">문 없음 · 피난(탈출) 없음 · 법규 검토 없음<small>NO DOORS, NO EGRESS, NO LEGAL CHECK</small></div>
<main>
<section>
<div class="card"><div class="bar">
<label>전략 <select id="selS"></select></label><label>층 <select id="selL"></select></label>
<button id="bFit" type="button">화면 맞춤</button><button id="bIn" type="button">확대 +</button><button id="bOut" type="button">축소 -</button><button id="bReset" type="button">줌 초기화</button>
</div>
<svg id="stage" role="img" aria-label="2D 평면 후보"></svg>
<div class="note">휠/버튼: 확대·축소, 드래그: 이동, 마우스 올림/탭: 실 정보. 실선은 측정된 폴리곤 경계이며 벽체·문이 아닙니다.</div>
<div id="legend" class="note"></div></div>
<div class="card"><h2>전략 비교 (폴리곤 데이터에서 계산)</h2><table id="cmp"></table></div>
</section>
<section>
<div class="card"><h2>선택 정보</h2><div id="info"></div></div>
<div class="card"><h2>층 면적 회계</h2><div id="acct"></div></div>
<div class="card"><h2>실 목록</h2><table id="rooms"></table></div>
<div class="card"><h2>실 연결(링크) 측정 결과</h2><div class="note">TOUCHING = 평면상 공유 경계 측정됨(공유 벽선만, 문 아님). 실제 동선·통로를 의미하지 않습니다.</div><div id="links"></div></div>
</section></main>
<script type="application/json" id="viewer-data">__VIEWER_DATA__</script>
<script>
(function(){
"use strict";
var NS="http://www.w3.org/2000/svg";
var D=JSON.parse(document.getElementById("viewer-data").textContent);
var S={si:0,li:0,sel:null,hov:null,hl:null,vb:null,fit:null,moved:false};
var svg=document.getElementById("stage");
var STX={TOUCHING:"TOUCHING - 공유 경계만 측정(문 아님)",SAME_LEVEL_NOT_TOUCHING:"SAME_LEVEL_NOT_TOUCHING - 같은 층, 경계 접촉 없음",DIFFERENT_LEVEL_NO_PLAN_CONTACT:"DIFFERENT_LEVEL_NO_PLAN_CONTACT - 다른 층, 평면 접촉 없음"};
function $(i){return document.getElementById(i)}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function sv(t,a){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);return e}
function f2(n){return Number(n).toFixed(2)}
function hue(s){var h=0;for(var i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))>>>0;return h%360}
function col(c){return "hsl("+hue(c)+",70%,86%)"}
function rp(r){return "M"+r.map(function(p){return p[0]+" "+(-p[1])}).join("L")+"Z"}
function rsp(rs){return rs.map(rp).join("")}
function bbox(rs){var x0=1e300,y0=1e300,x1=-1e300,y1=-1e300;rs.forEach(function(r){r.forEach(function(p){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,-p[1]);y1=Math.max(y1,-p[1])})});return [x0,y0,x1-x0,y1-y0]}
function cen(r){var a=0,cx=0,cy=0,n=r.length;for(var i=0;i<n;i++){var p=r[i],q=r[(i+1)%n],c=p[0]*q[1]-q[0]*p[1];a+=c;cx+=(p[0]+q[0])*c;cy+=(p[1]+q[1])*c}if(Math.abs(a)<1e-9){var b=bbox([r]);return [b[0]+b[2]/2,-(b[1]+b[3]/2)]}return [cx/(3*a),cy/(3*a)]}
function cur(){return D.strategies[S.si]}
function flr(){return cur().levels[S.li]}
function roomMap(st){var m={};st.levels.forEach(function(L){L.rooms.forEach(function(r){m[r.id]=L.level})});return m}
function catNote(c){return c==="CIRCULATION"?" (사용자 지정 공간 - 검증된 복도 아님)":""}
function setVB(x,y,w,h){S.vb=[x,y,w,h];svg.setAttribute("viewBox",x+" "+y+" "+w+" "+h)}
function fit(){var b=bbox(flr().floor_rings),p=Math.max(b[2],b[3])*0.06;S.fit=[b[0]-p,b[1]-p,b[2]+2*p,b[3]+2*p];setVB.apply(null,S.fit)}
function zoom(f,cx,cy){var v=S.vb;if(cx==null){cx=v[0]+v[2]/2;cy=v[1]+v[3]/2}var w=v[2]*f;if(w>S.fit[2]*8||w<S.fit[2]/40)return;setVB(cx-(cx-v[0])*f,cy-(cy-v[1])*f,w,v[3]*f)}
function toUser(e){var pt=svg.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;var m=svg.getScreenCTM();return m?pt.matrixTransform(m.inverse()):{x:0,y:0}}
function activeRoom(){return S.hov||S.sel}
function draw(){
  var st=cur(),L=flr(),ent=D.entrance_space_id,fs=Math.max(S.fit[2],S.fit[3])/38;
  while(svg.firstChild)svg.removeChild(svg.firstChild);
  var defs=sv("defs",{}),pat=sv("pattern",{id:"hz",width:fs/2,height:fs/2,patternUnits:"userSpaceOnUse",patternTransform:"rotate(45)"});
  pat.appendChild(sv("rect",{width:fs/2,height:fs/2,fill:"#fff"}));pat.appendChild(sv("line",{x1:0,y1:0,x2:0,y2:fs/2,stroke:"#aab2c8","stroke-width":fs/10}));
  defs.appendChild(pat);svg.appendChild(defs);
  svg.appendChild(sv("path",{d:rsp(L.floor_rings),fill:"#fff",stroke:"#27324a","stroke-width":2.2,"vector-effect":"non-scaling-stroke","fill-rule":"evenodd"}));
  if(L.residual_rings.length){var rs=sv("path",{d:rsp(L.residual_rings),fill:"url(#hz)",stroke:"#8a94ad","stroke-width":1,"stroke-dasharray":"5 3","vector-effect":"non-scaling-stroke","data-kind":"residual"});
    rs.addEventListener("mouseover",function(){S.hov="__RES__";info()});rs.addEventListener("mouseout",function(){S.hov=null;info()});
    rs.addEventListener("click",function(){if(!S.moved){S.sel="__RES__";info()}});svg.appendChild(rs);
    var big=L.residual_rings.slice().sort(function(a,b){return Math.abs(b.length)-Math.abs(a.length)})[0],c=cen(big);
    var t=sv("text",{x:c[0],y:-c[1],"font-size":fs*0.8,"text-anchor":"middle","fill":"#6b7794","pointer-events":"none"});t.textContent="UNPROGRAMMED_NOT_CORRIDOR";svg.appendChild(t)}
  var hl=S.hl||[],ar=activeRoom();
  L.rooms.forEach(function(r){
    var on=ar===r.id||hl.indexOf(r.id)>=0;
    var p=sv("path",{d:rsp(r.rings),fill:col(r.category),stroke:on?"#e5484d":"#27324a","stroke-width":on?3:1.4,"vector-effect":"non-scaling-stroke","fill-rule":"evenodd","data-room":r.id,"fill-opacity":0.9});
    if(r.category==="CIRCULATION")p.setAttribute("stroke-dasharray","2 2");
    p.addEventListener("mouseover",function(){S.hov=r.id;info()});p.addEventListener("mouseout",function(){S.hov=null;info()});
    p.addEventListener("click",function(){if(!S.moved){S.sel=r.id;info();syncRows()}});
    svg.appendChild(p);
    var big=r.rings.slice().sort(function(a,b){return b.length-a.length})[0],c=cen(big);
    var t=sv("text",{x:c[0],y:-c[1],"text-anchor":"middle","font-size":fs,"pointer-events":"none",fill:"#27324a"});
    var a=sv("tspan",{x:c[0],dy:-fs*0.1,"font-weight":"700"});a.textContent=r.id+(r.id===ent?" *":"");t.appendChild(a);
    var b=sv("tspan",{x:c[0],dy:fs*1.05,"font-size":fs*0.8});b.textContent=f2(r.area_m2)+" m2";t.appendChild(b);svg.appendChild(t)})
}
function info(){
  var box=$("info");while(box.firstChild)box.removeChild(box.firstChild);
  var id=activeRoom(),L=flr(),st=cur();
  if(!id){box.appendChild(el("div","k","실 위에 마우스를 올리거나 탭하세요."));return}
  if(id==="__RES__"){box.appendChild(el("div",null,"UNPROGRAMMED_NOT_CORRIDOR"));box.appendChild(el("div",null,"면적 "+f2(L.residual_area_m2)+" m2"));
    box.appendChild(el("div","k","미배정 층 잔여면적입니다. 복도·동선·피난 공간이 아닙니다."));return}
  var r=L.rooms.filter(function(x){return x.id===id})[0];if(!r)return;
  box.appendChild(el("div",null,r.id+" - "+r.name));
  box.appendChild(el("div",null,"분류 "+r.category+catNote(r.category)));
  box.appendChild(el("div",null,"면적 "+f2(r.area_m2)+" m2 (폴리곤 측정)"+(r.requested_area_m2!=null?" / 요청 "+f2(r.requested_area_m2)+" m2":"")));
  box.appendChild(el("div",null,"층 "+L.level+" / 꼭짓점 "+r.rings.reduce(function(n,x){return n+x.length},0)));
  if(r.id===D.entrance_space_id)box.appendChild(el("div","k","사용자 지정 입구 실(문 위치 아님)"));
  st.links.filter(function(l){return l.a===r.id||l.b===r.id}).forEach(function(l){var o=l.a===r.id?l.b:l.a;
    box.appendChild(el("div","k",o+": "+l.status+(l.status==="TOUCHING"?" "+f2(l.shared_boundary_m)+" m":"")))})
}
function acct(){
  var b=$("acct");while(b.firstChild)b.removeChild(b.firstChild);var L=flr(),s=L.stated||{};
  [["층 외곽 면적 (폴리곤)",L.floor_area_m2],["실 합계",L.rooms_area_m2],["미배정 잔여 (UNPROGRAMMED_NOT_CORRIDOR)",L.residual_area_m2],
   ["폐합 오차 (외곽 - 실 - 잔여)",L.floor_area_m2-L.rooms_area_m2-L.residual_area_m2]].forEach(function(x){
    var d=el("div");d.appendChild(el("span","k",x[0]+": "));d.appendChild(document.createTextNode(f2(x[1])+" m2"));b.appendChild(d)});
  if(s.programmed_requested_m2!=null){var d=el("div","k","입력 요청면적 합 "+f2(s.programmed_requested_m2)+" m2 / 입력 기록 폐합오차 "+f2(s.closure_error_m2||0)+" m2");b.appendChild(d)}
  var bar=el("div","split");L.rooms.forEach(function(r){var i=el("i");i.style.cssText="display:block;height:100%;width:"+(100*r.area_m2/L.floor_area_m2)+"%;background:"+col(r.category);bar.appendChild(i)});
  if(L.residual_area_m2>0){var h=el("i","hatch");h.style.cssText="display:block;height:100%;width:"+(100*L.residual_area_m2/L.floor_area_m2)+"%";bar.appendChild(h)}
  b.appendChild(bar)
}
function roomsTable(){
  var t=$("rooms");while(t.firstChild)t.removeChild(t.firstChild);var L=flr();
  var h=el("tr");["ID","이름","분류","m2"].forEach(function(x){h.appendChild(el("th",null,x))});t.appendChild(h);
  L.rooms.forEach(function(r){var tr=el("tr","click");tr.setAttribute("data-room",r.id);
    var c0=el("td");var sw=el("span","sw");sw.style.background=col(r.category);c0.appendChild(sw);c0.appendChild(document.createTextNode(r.id));tr.appendChild(c0);
    tr.appendChild(el("td",null,r.name));tr.appendChild(el("td",null,r.category+(r.category==="CIRCULATION"?" - 사용자 지정, 검증된 복도 아님":"")));tr.appendChild(el("td",null,f2(r.area_m2)));
    tr.addEventListener("click",function(){S.sel=r.id;draw();info();syncRows()});t.appendChild(tr)});
  if(L.residual_area_m2>0){var tr=el("tr");var c0=el("td");c0.appendChild(el("span","sw hatch"));c0.appendChild(document.createTextNode("잔여"));tr.appendChild(c0);
    tr.appendChild(el("td",null,"미배정"));tr.appendChild(el("td",null,"UNPROGRAMMED_NOT_CORRIDOR"));tr.appendChild(el("td",null,f2(L.residual_area_m2)));t.appendChild(tr)}
  syncRows()
}
function syncRows(){Array.prototype.forEach.call($("rooms").querySelectorAll("tr[data-room]"),function(tr){tr.className="click"+(tr.getAttribute("data-room")===S.sel?" sel":"")})}
function links(){
  var b=$("links");while(b.firstChild)b.removeChild(b.firstChild);var st=cur(),lv=roomMap(st);
  ["TOUCHING","SAME_LEVEL_NOT_TOUCHING","DIFFERENT_LEVEL_NO_PLAN_CONTACT"].forEach(function(k){
    var g=st.links.filter(function(l){return l.status===k});
    var h=el("div");h.appendChild(el("span","tag t-"+k,STX[k]));h.appendChild(document.createTextNode(" "+g.length+"건"));h.style.marginTop="6px";b.appendChild(h);
    g.forEach(function(l){var d=el("div","click");d.style.cssText="cursor:pointer;padding:2px 4px";
      d.textContent=l.a+" ("+(lv[l.a]||"-")+") - "+l.b+" ("+(lv[l.b]||"-")+")"+(k==="TOUCHING"?"  공유 경계 "+f2(l.shared_boundary_m)+" m (벽선만, 문 아님)":"  공유 경계 0 m");
      d.addEventListener("click",function(){S.hl=[l.a,l.b];draw();info()});b.appendChild(d)})})
}
function compare(){
  var t=$("cmp");while(t.firstChild)t.removeChild(t.firstChild);var h=el("tr");
  ["전략","순위","점수","실","TOUCHING","미배정 m2","외곽 m2 합"].forEach(function(x){h.appendChild(el("th",null,x))});t.appendChild(h);
  D.strategies.forEach(function(s,i){var tr=el("tr","click"+(i===S.si?" sel":""));
    var rooms=0,res=0,fl=0;s.levels.forEach(function(L){rooms+=L.rooms.length;res+=L.residual_area_m2;fl+=L.floor_area_m2});
    [s.strategy,(s.rank==null?"-":s.rank)+(s.tied?" (동점)":""),s.score==null?"-":f2(s.score),rooms,s.links.filter(function(l){return l.status==="TOUCHING"}).length,f2(res),f2(fl)].forEach(function(x){tr.appendChild(el("td",null,String(x)))});
    tr.addEventListener("click",function(){S.si=i;$("selS").value=String(i);onStrategy()});t.appendChild(tr)})
}
function legend(){
  var b=$("legend");while(b.firstChild)b.removeChild(b.firstChild);var seen={};
  flr().rooms.forEach(function(r){if(seen[r.category])return;seen[r.category]=1;var s=el("span",null);var w=el("span","sw");w.style.background=col(r.category);s.appendChild(w);
    s.appendChild(document.createTextNode(r.category+catNote(r.category)+"  "));b.appendChild(s)});
  var s2=el("span");s2.appendChild(el("span","sw hatch"));s2.appendChild(document.createTextNode("UNPROGRAMMED_NOT_CORRIDOR (복도 아님)  "));b.appendChild(s2);
  if(D.entrance_space_id)b.appendChild(document.createTextNode(" * = 사용자 지정 입구 실 "+D.entrance_space_id+" (문 아님)"))
}
function fillLevels(){
  var sel=$("selL"),keep=null;if(S.li>=0&&sel.options.length&&sel.value)keep=sel.value;
  while(sel.firstChild)sel.removeChild(sel.firstChild);
  cur().levels.forEach(function(L,i){var o=document.createElement("option");o.value=String(i);o.textContent=L.level+" ("+f2(L.floor_area_m2)+" m2)";sel.appendChild(o)});
  var prev=D.strategies[S.si].levels.length;S.li=Math.min(S.li,prev-1);sel.value=String(S.li)
}
function onStrategy(){S.sel=null;S.hl=null;fillLevels();onLevel()}
function onLevel(){S.sel=S.sel&&flr().rooms.some(function(r){return r.id===S.sel})?S.sel:null;fit();draw();info();acct();roomsTable();links();compare();legend()}
function init(){
  $("prov").textContent="project "+D.project_id+" | source sha256 "+D.source_sha256+" | result file sha256 "+D.input_file_sha256+" | "+D.tool;
  var ss=$("selS");D.strategies.forEach(function(s,i){var o=document.createElement("option");o.value=String(i);o.textContent=s.strategy+(s.rank!=null?" (순위 "+s.rank+")":"");ss.appendChild(o)});
  ss.addEventListener("change",function(){S.si=+ss.value;onStrategy()});
  $("selL").addEventListener("change",function(){S.li=+$("selL").value;S.sel=null;S.hl=null;onLevel()});
  $("bFit").addEventListener("click",fit);$("bReset").addEventListener("click",fit);
  $("bIn").addEventListener("click",function(){zoom(0.7)});$("bOut").addEventListener("click",function(){zoom(1/0.7)});
  svg.addEventListener("wheel",function(e){e.preventDefault();var p=toUser(e);zoom(e.deltaY<0?0.85:1/0.85,p.x,p.y)},{passive:false});
  var drag=null;
  svg.addEventListener("pointerdown",function(e){drag={x:e.clientX,y:e.clientY};S.moved=false});
  window.addEventListener("pointermove",function(e){if(!drag)return;var dx=e.clientX-drag.x,dy=e.clientY-drag.y;
    if(!S.moved&&Math.abs(dx)+Math.abs(dy)<4)return;S.moved=true;var m=svg.getScreenCTM();if(!m)return;
    setVB(S.vb[0]-dx/m.a,S.vb[1]-dy/m.d,S.vb[2],S.vb[3]);drag={x:e.clientX,y:e.clientY}});
  window.addEventListener("pointerup",function(){drag=null;setTimeout(function(){S.moved=false},0)});
  fillLevels();onLevel()
}
init();
})();
</script></body></html>
"""

if __name__=="__main__":
    raise SystemExit(main())
