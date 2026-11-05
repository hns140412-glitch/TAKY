#!/usr/bin/env python3
"""ARCHIGROW_DESIGN_SEMANTIC_SYNC (P8) regression: ONE live native CLI case (1950); everything else is pure, tamper-in-place, mocked or served from that case.
Outputs live only under a new workbench scratch folder. Existing inputs are read-only."""
import copy,hashlib,http.client,importlib.util,json,os,re,shutil,subprocess,sys,tempfile,threading
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SPEC=importlib.util.spec_from_file_location("p8",ROOT/"TOOLS"/"ARCHIGROW_DESIGN_SEMANTIC_SYNC.py")
p8=importlib.util.module_from_spec(SPEC);sys.modules["p8"]=p8;SPEC.loader.exec_module(p8)
WB=Path(os.environ.get("ARCHIGROW_P8_SCRATCH",r"D:\Git PWA\TAKY_AI_WORKBENCH\10_PROJECTS\TAKY_ARCHI-GROW\_scratch"))
SEED=WB/"TOPOGENESIS_P2_CONCAVE_RECOVERED_INPUT_20261027.json"
TPL=WB/"TOPOGENESIS_P7_SEMANTIC_PLAN_20261028"/"fixture"/"explicit_synthetic_openings.json"
BASE=WB/"TOPOGENESIS_P6_SHARED_MODEL_20261028"/"T1975_384429dcdaa6"/"model"/"massing_result.json"
OUT=WB/"TOPOGENESIS_P8_SEMANTIC_SYNC_20261028"
for f in (SEED,TPL,BASE):
    if not f.is_file():print("architecture_design_semantic_sync_test: BLOCKED missing %s"%f);raise SystemExit(2)
OUT.mkdir(exist_ok=True);LIVE=OUT/"live_root"
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raises(code,fn,*a,**k):
    try:fn(*a,**k)
    except p8.Hold as h:
        assert code in h.failure,(code,h.failure);return h
    raise AssertionError("expected Hold %s"%code)
tmp=Path(tempfile.mkdtemp(dir=str(OUT),prefix="tmp_"))
tpl_sha0,base_sha0,seed_sha0=sha(TPL),sha(BASE),sha(SEED)
raw_tpl=json.loads(TPL.read_text(encoding="utf-8"))
def tpl_with(name,fn):
    d=copy.deepcopy(raw_tpl);fn(d);p=tmp/(name+".json");p.write_text(json.dumps(d),encoding="utf-8");return p

# ---- template + exact-support logic (pure) ----
fx,strat,bl,tmeta=p8.load_template(TPL,BASE)
assert tmeta["sha256"]==tpl_sha0 and tmeta["base_model_sha256"]==base_sha0 and tmeta["project_id"]=="SYNTHETIC_TOPO_P1"
raises("TEMPLATE_INVALID",p8.load_template,tpl_with("badsha",lambda d:d["provenance"].update(model_sha256="0"*64)),BASE)
raises("TEMPLATE_BASE_MODEL_SHA_MISSING",p8.load_template,tpl_with("nosha",lambda d:d["provenance"].pop("model_sha256")),BASE)
raises("TEMPLATE_INVALID",p8.load_template,tpl_with("dupid",lambda d:d["strategies"]["BALANCED"]["levels"]["L01"]["doors"][1].update(id="D_LOBBY_RETAIL")),BASE)
raises("TEMPLATE_INVALID",p8.load_template,tpl_with("width",lambda d:d["strategies"]["BALANCED"]["levels"]["L01"]["doors"][0].update(width_m=5)),BASE)
raises("TEMPLATE_BASE_MISMATCH",p8.load_template,tpl_with("room",lambda d:d["strategies"]["BALANCED"]["levels"]["L01"]["windows"][0].update(room="NOPE")),BASE)
raises("TEMPLATE_BASE_MISMATCH",p8.load_template,tpl_with("lvl",lambda d:d["strategies"]["BALANCED"]["levels"].update(L09={"doors":[],"windows":[{"id":"W9","room":"LOBBY","side":"W","width_m":1,"center_offset_m":1}]})),BASE)
raises("TEMPLATE_INVALID",p8.load_template,tmp/"absent.json",BASE)
assert p8.check_support(strat,bl,copy.deepcopy(bl))
nl=copy.deepcopy(bl)
for r in nl["BALANCED"]["L02"]["rooms"]:nl["BALANCED"]["L02"]["rooms"][r]=[(x+0.2,y) for x,y in nl["BALANCED"]["L02"]["rooms"][r]]
p8.check_support(strat,bl,nl)    # level without openings may move: support unchanged
for s,room in (("BALANCED","LOBBY"),("SCULPTURAL","RETAIL")):
    nl=copy.deepcopy(bl);nl[s]["L01"]["rooms"][room]=[(x+0.001,y) for x,y in nl[s]["L01"]["rooms"][room]]
    raises("OPENING_SUPPORT_CHANGED",p8.check_support,strat,bl,nl)
nl=copy.deepcopy(bl);nl["BALANCED"]["L01"]["floor"][0]=(nl["BALANCED"]["L01"]["floor"][0][0]+0.01,nl["BALANCED"]["L01"]["floor"][0][1])
raises("OPENING_SUPPORT_CHANGED",p8.check_support,strat,bl,nl)           # window level floor outline is part of the support
nl=copy.deepcopy(bl);del nl["SCULPTURAL"]["L01"]["rooms"]["RETAIL"]
raises("OPENING_SUPPORT_CHANGED",p8.check_support,strat,bl,nl)
nl=copy.deepcopy(bl);del nl["SCULPTURAL"]
raises("OPENING_SUPPORT_CHANGED",p8.check_support,strat,bl,nl)
for bad in (True,"1950",None,float("nan"),float("inf"),-5,99,10001):raises("TARGET",p8.sync.normalize_target,bad)
assert p8.main(["--seed",str(SEED),"--opening-template",str(TPL),"--base-model",str(BASE),"--out-root",str(tmp/"bad"),"--target-area","5"])==2
assert not (tmp/"bad").exists() or not any((tmp/"bad").iterdir())

# ---- the ONE live case: CLI 1950 -> P6 -> support check -> P7 -> 2 native DWG (+reopen) -> P8 receipt ----
cmd=[sys.executable,str(ROOT/"TOOLS"/"ARCHIGROW_DESIGN_SEMANTIC_SYNC.py"),"--seed",str(SEED),"--opening-template",str(TPL),"--base-model",str(BASE),"--out-root",str(LIVE),"--target-area","1950"]
r=subprocess.run(cmd,capture_output=True,timeout=900);res=json.loads(r.stdout.decode("utf-8").strip().splitlines()[-1])
assert r.returncode==0 and res["status"]=="PASS" and res["version"].startswith("T1950_") and len(res["dwgs"])==2,res
vd=LIVE/res["version"];rec=p8.verify_semantic(vd);print("live case reused=%s version=%s"%(res["reused"],res["version"]))
assert (sha(TPL),sha(BASE),sha(SEED))==(tpl_sha0,base_sha0,seed_sha0),"inputs must stay untouched"
assert rec["template"]["sha256"]==tpl_sha0 and rec["model_sha256"]!=base_sha0 and rec["input_sha256"]!=tmeta["base_source_sha256"]
dfx=json.loads((vd/rec["files"]["derived_fixture"]["ref"]).read_text(encoding="utf-8"))
assert dfx["provenance"]["model_sha256"]==rec["model_sha256"]==sha(vd/"model"/"massing_result.json") and dfx["provenance"]["source_sha256"]==rec["input_sha256"]
assert rec["files"]["derived_fixture"]["sha256"]!=tpl_sha0 and {k:v for k,v in dfx.items() if k!="provenance"}=={k:v for k,v in raw_tpl.items() if k!="provenance"}
assert rec["support"]["checked"] and rec["p7_own_dwg_status"]=="NOT_DONE" and rec["legal_status"]=="NOT_VERIFIED" and rec["render_verification"]=="NOT_PERFORMED"
assert json.loads((vd/rec["files"]["p7_receipt"]["ref"]).read_text(encoding="utf-8"))["dwg"]["status"]=="NOT_DONE"
assert [o["strategy"] for o in rec["outputs"]]==["BALANCED","SCULPTURAL"]
plans=p8.sem.html_data((vd/rec["files"]["viewer"]["ref"]).read_text(encoding="utf-8"))["strategies"]
for o,pl in zip(rec["outputs"],plans):
    f=vd/o["dwg"]["ref"];c=o["native_counts"]
    assert f.read_bytes()[:6]==b"AC1032" and sha(f)==o["dwg"]["sha256"] and c["LWPOLYLINE"]>0 and c["CLOSED"]==c["LWPOLYLINE"] and c["INSUNITS"]==6
    assert pl["strategy"]==o["strategy"] and pl["model_sha256"]==rec["model_sha256"] and pl["source_sha256"]==rec["input_sha256"]   # browser viewer == CAD model
    nat=json.loads((vd/rec["files"]["native_receipt"]["ref"]).read_text(encoding="utf-8"))
    assert {k:v for k,v in next(x for x in nat["options"] if x["strategy"]==o["strategy"])["native_reopen"].items() if k in c}==c
html=(vd/rec["files"]["viewer"]["ref"]).read_text(encoding="utf-8")
assert not re.search(r"(src|href)\s*=\s*[\"']https?:|url\(\s*https?:|@import",html)
r2=subprocess.run(cmd,capture_output=True,timeout=300);assert r2.returncode==0 and json.loads(r2.stdout.decode().strip().splitlines()[-1])["reused"] is True

# ---- tamper in place (restored in finally): every change must be rejected by re-verification ----
def tamper(rel,fn):
    p=vd/rel;orig=p.read_bytes()
    try:
        p.write_bytes(fn(orig));raises("",p8.verify_semantic,vd)
    finally:p.write_bytes(orig)
flip=lambda b:b[:100]+bytes([b[100]^1])+b[101:]
for o in rec["outputs"]:
    tamper(o["dwg"]["ref"],flip);tamper(o["dxf"]["ref"],lambda b:b+b"\n");tamper(o["json"]["ref"],lambda b:b.replace(b"BALANCED",b"BALANCEX") if b"BALANCED" in b else b+b" ")
tamper(rec["files"]["viewer"]["ref"],lambda b:b+b"<!--x-->")
tamper(rec["files"]["derived_fixture"]["ref"],lambda b:b.replace(b'"width_m": 0.9',b'"width_m": 1.0') if b'"width_m": 0.9' in b else b+b" ")
tamper(rec["files"]["native_receipt"]["ref"],lambda b:b.replace(b'"PASS"',b'"HOLD"',1))
tamper("semantic/semantic_sync_receipt.json",lambda b:b.replace(b'"PASS"',b'"HOLD"',1))
tamper("semantic/plan/semantic_plan_receipt.json",lambda b:b.replace(b'"PASS"',b'"HOLD"',1))
assert p8.verify_semantic(vd)==rec

# ---- mocked stages on a copy of the live model (no CAD): a failed stage leaves no semantic/ dir and no receipt ----
p6rec=json.loads((vd/"design_sync_receipt.json").read_text(encoding="utf-8"))
def mock_root(name,mut=None):
    root=tmp/name;d=root/p6rec["version"];shutil.copytree(vd/"model",d/"model");shutil.copy(vd/"design_sync_receipt.json",d/"design_sync_receipt.json")
    if mut:
        m=json.loads((d/"model"/"massing_result.json").read_text(encoding="utf-8"));mut(m);(d/"model"/"massing_result.json").write_text(json.dumps(m),encoding="utf-8")
    return root,d
saved=(p8.P6_BUILD,p8.P6_VERIFY,p8.stage_p7,p8.stage_native)
p8.P6_BUILD=lambda s,o,t:(p6rec,True);p8.P6_VERIFY=lambda v:p6rec
def run(root,**k):return p8.build_semantic({},root,TPL,BASE,1950,**k)
def boom(*a,**k):raise p8.Hold("INJECTED","STAGE")
try:
    root,d=mock_root("m_native");p8.stage_native=boom;raises("INJECTED",run,root);assert not (d/"semantic").exists()
    p8.stage_native=saved[3];root,d=mock_root("m_p7");p8.stage_p7=boom;raises("INJECTED",run,root);assert not (d/"semantic").exists()
    p8.stage_p7=saved[2];root,d=mock_root("m_exe");raises("ACCORECONSOLE_MISSING",run,root,exe=str(tmp/"accoreconsole.exe"));assert not (d/"semantic").exists()
    def move(m):
        for o in m["options"]:
            if o["strategy"]=="BALANCED":
                for L in o["program_allocation"]["room_geometry"]["levels"]:
                    for rm in L["rooms"]:
                        if rm["id"]=="LOBBY" and L["level"]=="L01":rm["polygon"]=[[x+0.5,y] for x,y in rm["polygon"]]
    root,d=mock_root("m_support",move);raises("OPENING_SUPPORT_CHANGED",run,root);assert not (d/"semantic").exists()
    root,d=mock_root("m_dirty");(d/"semantic").mkdir();(d/"semantic"/"stale.txt").write_text("x");p8.stage_native=boom   # unpublished partial is not reused
    raises("INJECTED",run,root);assert not (d/"semantic").exists()
finally:p8.P6_BUILD,p8.P6_VERIFY,p8.stage_p7,p8.stage_native=saved

# ---- local server on the live root: CSRF/Host/Origin/body limits and allowlisted downloads ----
srv=p8.Server(LIVE,p8.sync.load_seed(SEED),TPL,BASE,0);threading.Thread(target=srv.serve_forever,daemon=True).start()
def http_(method,path,body=None,hdr=None,host=None):
    c=http.client.HTTPConnection("127.0.0.1",srv.port,timeout=300);h={"Host":host or "127.0.0.1:%d"%srv.port}
    h.update(hdr or {});c.request(method,path,body=body,headers=h);x=c.getresponse();return x.status,x.read(),dict(x.getheaders())
try:
    st,page,_=http_("GET","/");tok=re.search(rb'var TOKEN="([^"]+)"',page).group(1).decode();text=page.decode("utf-8")
    assert st==200 and "Semantic DWG" in text and "코어/수직" in text and "code compliance" in text and not re.search(r"https?://(?!127)",text.replace("http://www.w3.org","")) and 'type="number"' in text
    ok={"Origin":"http://127.0.0.1:%d"%srv.port,"X-CSRF-Token":tok,"Content-Type":"application/json"};good=json.dumps({"target_area_m2":1950})
    assert http_("GET","/",host="evil.test")[0]==403 and http_("POST","/api/generate",good,{**ok,"Host":"x"},host="evil.test")[0]==403
    assert http_("POST","/api/generate",good,{**ok,"X-CSRF-Token":"bad"})[0]==403 and http_("POST","/api/generate",good,{**ok,"Origin":"http://evil.test"})[0]==403
    assert http_("POST","/api/generate",good,{**ok,"Content-Type":"text/plain"})[0]==415 and http_("POST","/api/generate","x"*3000,ok)[0]==413
    assert http_("POST","/api/generate",json.dumps({"target_area_m2":1950,"path":"C:/x"}),ok)[0]==400 and http_("POST","/api/generate",json.dumps({"target_area_m2":5}),ok)[0]==400
    assert http_("POST","/api/generate","{not json",ok)[0]==400 and http_("PUT","/api/generate",good,ok)[0]==405
    st,body,_=http_("POST","/api/generate",good,ok);j=json.loads(body)
    assert st==200 and j["status"]=="PASS" and j["semantic"] is True and j["version"]==res["version"] and j["reused"] is True and len(j["dwgs"])==2 and j["fixture_sha256"]==rec["files"]["derived_fixture"]["sha256"]
    for dw in j["dwgs"]:
        st,data,h=http_("GET",dw["url"]);assert st==200 and data[:6]==b"AC1032" and hashlib.sha256(data).hexdigest()==dw["sha256"] and "attachment" in h["Content-Disposition"]
    st,data,h=http_("GET",j["viewer_url"]);assert st==200 and data==(vd/rec["files"]["viewer"]["ref"]).read_bytes() and "connect-src 'none'" in h["Content-Security-Policy"]
    v=res["version"]
    for bad in ("/v/%s/dwg/NOPE"%v,"/v/%s/model/massing_result.json"%v,"/v/%s/semantic/native_dwg_receipt.json"%v,"/v/..%%2f..%%2fsecret/viewer","/v/T1950_000000000000/viewer","/v/%s/dwg/../../x"%v,"/etc/passwd","/api/generate"):
        assert http_("GET",bad)[0]==404,bad
    f0=vd/rec["outputs"][0]["dwg"]["ref"];orig=f0.read_bytes()
    try:
        f0.write_bytes(flip(orig));assert http_("GET",j["dwgs"][0]["url"])[0]==404       # tampered file is never served
    finally:f0.write_bytes(orig)
finally:srv.shutdown();srv.server_close();shutil.rmtree(tmp,ignore_errors=True)
assert (sha(TPL),sha(BASE),sha(SEED))==(tpl_sha0,base_sha0,seed_sha0)
print("architecture_design_semantic_sync_test: PASS")
