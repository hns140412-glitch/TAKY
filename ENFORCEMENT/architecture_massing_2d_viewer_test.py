#!/usr/bin/env python3
"""Fast regression for TOOLS/ARCHIGROW_MASSING_2D_VIEWER.py (synthetic fixture; no browser, no network)."""
import copy,hashlib,importlib.util,json,re,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"TOOLS"/"ARCHIGROW_MASSING_2D_VIEWER.py"
spec=importlib.util.spec_from_file_location("viewer",TOOL);V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
SAMPLE=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\10_PROJECTS\TAKY_ARCHI-GROW\_scratch\TOPOGENESIS_P2_CONCAVE_RECOVERY_OUTPUT_20261027\massing_result.json")
PID="VIEWER_TEST"

def rect(x0,y0,x1,y1):return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
def room(i,poly,a):return {"id":i,"polygon":poly,"requested_area_m2":a,"area_m2":a}
def link(a,b,st,sb,same):return {"a":a,"b":b,"weight":1.0,"same_level":same,"shared_boundary_m":sb,"status":st,"opening":"NOT_MODELED"}
def spaces():
    return [{"id":"LOBBY","name":"Lobby","category":"PUBLIC","level":"L01"},{"id":"OFFICE","name":"Office","category":"OFFICE","level":"L01"},
            {"id":"STORE","name":"Store","category":"SERVICE","level":"L01"},{"id":"CORE","name":"Core","category":"CIRCULATION","level":"L02"}]
def l02():
    return {"level":"L02","floor_area_m2":200.0,"rooms":[room("CORE",rect(0,0,10,10),100.0)],
            "residual":{"kind":"UNPROGRAMMED_NOT_CORRIDOR","polygon":rect(10,0,20,10),"area_m2":100.0},
            "accounting":{"programmed_requested_m2":100.0,"rooms_area_m2":100.0,"residual_area_m2":100.0,"closure_error_m2":0.0}}
def option(strategy,rank):
    if strategy=="A":
        fpoly=rect(0,0,20,10)
        l01={"level":"L01","floor_area_m2":200.0,"rooms":[room("LOBBY",rect(0,0,8,10),80.0),room("OFFICE",rect(8,0,14,10),60.0),room("STORE",rect(16,0,20,10),40.0)],
             "residual":{"kind":"UNPROGRAMMED_NOT_CORRIDOR","polygon":rect(14,0,16,10),"area_m2":20.0},"accounting":{}}
        links=[link("LOBBY","OFFICE","TOUCHING",10.0,True),link("OFFICE","STORE","SAME_LEVEL_NOT_TOUCHING",0.0,True)]
    else:  # L-shaped floor, no residual
        fpoly=[[0,0],[20,0],[20,5],[10,5],[10,10],[0,10]]
        l01={"level":"L01","floor_area_m2":150.0,"rooms":[room("LOBBY",rect(0,0,10,5),50.0),room("OFFICE",rect(10,0,20,5),50.0),room("STORE",rect(0,5,10,10),50.0)],
             "residual":{"kind":"UNPROGRAMMED_NOT_CORRIDOR","polygon":None,"area_m2":0.0},"accounting":{}}
        links=[link("LOBBY","OFFICE","TOUCHING",5.0,True),link("LOBBY","STORE","TOUCHING",10.0,True),link("OFFICE","STORE","SAME_LEVEL_NOT_TOUCHING",0.0,True)]
    return {"strategy":strategy,"floors":[{"level":"L01","polygon":fpoly,"area_m2":l01["floor_area_m2"]},
            {"level":"L02","polygon":rect(0,0,20,10),"area_m2":200.0},{"level":"L03","polygon":rect(0,0,20,10),"area_m2":200.0}],
            "program_allocation":{"spaces":spaces(),"rank":rank,"score":1.0-0.1*rank,"tied":False,
              "room_geometry":{"project_id":PID,"building_code_compliance":False,"levels":[l01,l02()],
                "adjacency":{"links":links,"unmet":[link("CORE","LOBBY","DIFFERENT_LEVEL_NO_PLAN_CONTACT",0.0,False)]}}}}
def fixture():
    return {"schema":"ARCHIGROW_MASSING_RESULT_V1","project_id":PID,"source_sha256":"ab"*32,
            "spatial_program":{"entrance_space_id":"LOBBY","ranking":[{"rank":1,"strategy":"A","score":0.9,"tied":False},{"rank":2,"strategy":"B","score":0.8,"tied":False}]},
            "options":[option("A",1),option("B",2)]}

def run(data,tmp,name="v",expect=PID,receipt=True):
    src=tmp/(name+".json");src.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    out=tmp/(name+".html");rc=tmp/(name+"_receipt.json") if receipt else None
    r=V.build(src,out,expect,rc);return r,src,out,rc

def payload(html):
    m=re.search(r'<script type="application/json" id="viewer-data">(.*?)</script>',html,re.S);assert m,"data script missing"
    return json.loads(m.group(1))

def holds(tmp,data,code,name,expect=PID):
    r,_,out,_=run(data,tmp,name,expect)
    assert r["status"]=="HOLD" and r["failure_class"]==code,(name,r["failure_class"])
    assert not out.exists() and r["output"] is None,name+" wrote a file"

def main():
    with tempfile.TemporaryDirectory() as t:
        tmp=Path(t)
        # 1. both strategies, actual 2D geometry, links, labels
        r,src,out,rc=run(fixture(),tmp)
        assert r["status"]=="GENERATED_UNVERIFIED_RENDER" and out.exists(),r
        html=out.read_text(encoding="utf-8");P=payload(html)
        assert [s["strategy"] for s in P["strategies"]]==["A","B"]
        A,B=P["strategies"]
        a1=A["levels"][0];b1=B["levels"][0]
        assert a1["floor_rings"][0]==rect(0,0,20,10) and b1["floor_rings"][0]==[[0,0],[20,0],[20,5],[10,5],[10,10],[0,10]]
        assert a1["rooms"][0]["rings"][0]==rect(0,0,8,10) and b1["rooms"][0]["rings"][0]==rect(0,0,10,5)
        assert a1["residual_rings"]==[rect(14,0,16,10)] and b1["residual_rings"]==[] and a1["residual_kind"]=="UNPROGRAMMED_NOT_CORRIDOR"
        assert (a1["floor_area_m2"],b1["floor_area_m2"])==(200.0,150.0) and abs(a1["rooms_area_m2"]+a1["residual_area_m2"]-200)<1e-9
        assert a1["floor_rings"]!=b1["floor_rings"] and [x["rings"] for x in a1["rooms"]]!=[x["rings"] for x in b1["rooms"]],"strategy must differ in geometry"
        assert [l["level"] for l in A["levels"]]==["L01","L02"],"L03 has no room geometry and must not be offered"
        sa={l["status"] for l in A["links"]};assert sa=={"TOUCHING","SAME_LEVEL_NOT_TOUCHING","DIFFERENT_LEVEL_NO_PLAN_CONTACT"},sa
        assert sum(l["status"]=="TOUCHING" for l in B["links"])==2 and P["entrance_space_id"]=="LOBBY"
        for s in ("NO DOORS, NO EGRESS, NO LEGAL CHECK","문 없음","피난(탈출) 없음","법규 검토 없음","UNPROGRAMMED_NOT_CORRIDOR","공유 벽선만","문 아님",
                  "검증된 복도 아님","사용자 지정"):
            assert s in html,s
        assert any(x["category"]=="CIRCULATION" for x in A["levels"][1]["rooms"])
        assert P["source_sha256"]=="ab"*32 and P["input_file_sha256"]==hashlib.sha256(src.read_bytes()).hexdigest()
        # 2. self-contained, no external requests, no untrusted innerHTML
        for pat in (r"https?://(?!www\.w3\.org/2000/svg)",r"<link\b",r"@import",r"\bsrc\s*=",r"\bhref\s*=",r"url\(\s*['\"]?https?",r"\bfetch\(",r"XMLHttpRequest",
                    r"WebSocket",r"\binnerHTML\b",r"\bouterHTML\b",r"insertAdjacentHTML",r"document\.write",r"\beval\(",r"new Function"):
            assert not re.search(pat,html),pat
        assert len(re.findall(r"<script\b",html))==2 and len(re.findall(r"</script",html))==2
        # 3. receipt
        R=json.loads(rc.read_text(encoding="utf-8"))
        assert R["inputs"][0]["sha256"]==hashlib.sha256(src.read_bytes()).hexdigest() and R["output"]["sha256"]==hashlib.sha256(out.read_bytes()).hexdigest()
        assert R["claim_level"]=="MECHANICAL_GEOMETRY_ONLY" and R["render_verification"]=="NOT_PERFORMED" and R["dwg_qa"]=="NOT_PERFORMED"
        assert R["acceptance"]=="NOT_CLAIMED" and R["legal_status"]=="NOT_VERIFIED" and R["source_sha256"]=="ab"*32 and R["limitations"]
        assert "PASS" not in R["status"] and "ACCEPT" not in R["status"].upper().replace("NOT_CLAIMED","")
        # 4. HOLD paths: never write
        holds(tmp,fixture(),"PROJECT_MISMATCH","pm",expect="OTHER")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["project_id"]="OTHER";holds(tmp,d,"PROJECT_MISMATCH","pm2")
        d=fixture();del d["options"][1]["program_allocation"]["room_geometry"];holds(tmp,d,"ROOM_GEOMETRY_MISSING","nogeo")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["levels"][0]["rooms"]=[];holds(tmp,d,"ROOM_GEOMETRY_MISSING","norooms")
        d=fixture();d["schema"]="X";holds(tmp,d,"SCHEMA_UNSUPPORTED","schema")
        d=fixture();d["source_sha256"]="zz";holds(tmp,d,"SOURCE_SHA_MISSING","sha")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["levels"][0]["rooms"][0]["polygon"]=[[0,0],[1,0]];holds(tmp,d,"ROOM_POLYGON_INVALID","poly")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["levels"][0]["rooms"][0]["polygon"]=[[0,0],[1,"x"],[1,1]];holds(tmp,d,"ROOM_POLYGON_INVALID","poly2")
        d=fixture();d["options"][0]["floors"][0]["polygon"]=None;holds(tmp,d,"FLOOR_POLYGON_INVALID","fpoly")
        d=fixture();d["options"][0]["floors"]=[];holds(tmp,d,"FLOOR_POLYGON_MISSING","nofloor")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["levels"][0]["rooms"][0]["area_m2"]=70.0;holds(tmp,d,"AREA_MISMATCH","area")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["adjacency"]["links"][0]["status"]="WALKABLE";holds(tmp,d,"LINK_STATUS_UNKNOWN","lst")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["adjacency"]["links"][0]["shared_boundary_m"]=0.0;holds(tmp,d,"LINK_STATUS_INCONSISTENT","lincons")
        d=fixture();d["spatial_program"]["entrance_space_id"]="GHOST";holds(tmp,d,"ENTRANCE_REF_UNKNOWN","ent")
        d=fixture();d["options"][0]["program_allocation"]["room_geometry"]["building_code_compliance"]=True;holds(tmp,d,"LEGAL_CLAIM_UNEXPECTED","legal")
        bad=tmp/"bad.json";bad.write_text("{nope",encoding="utf-8");o=tmp/"bad.html"
        rb=V.build(bad,o,PID);assert rb["failure_class"]=="RESULT_JSON_UNREADABLE" and not o.exists()
        rb=V.build(tmp/"missing.json",o,PID);assert rb["failure_class"]=="RESULT_JSON_UNREADABLE" and not o.exists()
        # 5. script-injection safety: hostile ids/names stay inert data
        evil='</script><img src=x onerror=alert(1)>&amp;\u2028'
        d=fixture()
        for o_ in d["options"]:
            sp=o_["program_allocation"]["spaces"][0];sp["name"]=evil
        r,_,out,_=run(d,tmp,"evil");assert r["status"]=="GENERATED_UNVERIFIED_RENDER"
        h=out.read_text(encoding="utf-8")
        assert "<img" not in h and "onerror=alert" in h and len(re.findall(r"</script",h))==2 and "\u2028" not in h
        assert payload(h)["strategies"][0]["levels"][0]["rooms"][0]["name"]==evil
        # 6. CLI: exit codes + receipt
        cmd=[sys.executable,"-I",str(TOOL),str(src),"--out",str(tmp/"cli.html"),"--expect-project",PID,"--receipt",str(tmp/"cli_receipt.json")]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr
        o=json.loads(p.stdout);assert o["status"]=="GENERATED_UNVERIFIED_RENDER" and o["render_verification"]=="NOT_PERFORMED"
        assert (tmp/"cli.html").read_bytes()==out_bytes(tmp/"v.html")
        cmd[-3]="WRONG";cmd[cmd.index("--out")+1]=str(tmp/"cli2.html")
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=20);assert p.returncode==2 and not (tmp/"cli2.html").exists()
        assert json.loads(p.stdout)["failure"]=="PROJECT_MISMATCH"
        # 7. optional: real pre-verified synthetic result
        if SAMPLE.exists():
            r=V.build(SAMPLE,tmp/"real.html",json.loads(SAMPLE.read_text(encoding="utf-8-sig"))["project_id"])
            assert r["status"]=="GENERATED_UNVERIFIED_RENDER",r["failure_class"]
            assert len(r["strategies"])==2
    print("architecture_massing_2d_viewer_test: PASS")

def out_bytes(p):return Path(p).read_bytes()

if __name__=="__main__":
    main()
