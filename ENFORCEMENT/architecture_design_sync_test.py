#!/usr/bin/env python3
"""ARCHIGROW_DESIGN_SYNC (P6) regression: one live native CLI case (1950), everything else mocked or served from that case."""
import copy,hashlib,http.client,importlib.util,json,os,subprocess,sys,tempfile,threading
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SPEC=importlib.util.spec_from_file_location("sync",ROOT/"TOOLS"/"ARCHIGROW_DESIGN_SYNC.py")
sync=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(sync)
SEED=Path(os.environ.get("ARCHIGROW_SYNC_SEED",r"D:\Git PWA\TAKY_AI_WORKBENCH\10_PROJECTS\TAKY_ARCHI-GROW\_scratch\TOPOGENESIS_P2_CONCAVE_RECOVERED_INPUT_20261027.json"))
if not SEED.is_file():
    print("architecture_design_sync_test: BLOCKED seed missing: %s"%SEED);raise SystemExit(2)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raises(fn,*a):
    try:fn(*a)
    except sync.Hold as h:return h
    raise AssertionError("expected Hold from %s%r"%(getattr(fn,"__name__",fn),a))

seed=sync.load_seed(SEED)

# ---- input handling (no subprocess): only the numeric target changes, versions are distinct ----
v50,t50,d50,s50=sync.prepare_input(seed,1950)
v00,t00,d00,s00=sync.prepare_input(seed,2000)
assert v50!=v00 and s50!=s00 and v50.startswith("T1950_") and v00.startswith("T2000_")
a,b=json.loads(d50),json.loads(d00)
assert a["constraints"][sync.TARGET_KEY]==1950 and b["constraints"][sync.TARGET_KEY]==2000
a["constraints"][sync.TARGET_KEY]=b["constraints"][sync.TARGET_KEY]=None
assert a==b, "only the target may differ"
assert seed["constraints"][sync.TARGET_KEY]==2000, "seed deep-copied, not mutated"
for bad in (True,"1950",None,float("nan"),float("inf"),-5,0,99,10001,[1950]):
    raises(sync.normalize_target,bad)
assert sync.normalize_target(1950.0)==1950 and sync.normalize_target(1950.5)==1950.5
raises(sync.load_seed,ROOT/"no_such_seed.json")

with tempfile.TemporaryDirectory(prefix="adsync_") as tmp:
    tmp=Path(tmp)

    # ---- mocked stage failure: nothing partial left, nothing listed as current ----
    real_run=sync.run_stage
    calls=[]
    def failing(stage,argv,py=None):
        calls.append(stage)
        # mocked P2 exits 0 but writes no massing_result.json -> build must hold at P2 and clean up
    sync.run_stage=failing
    h=raises(sync.build,seed,tmp/"mock",1950)
    assert h.stage=="P2_MASSING" and calls==["P2_MASSING"], (h.failure,calls)
    assert sync.list_versions(tmp/"mock")==[] and not any((tmp/"mock").iterdir()), "failed run must leave no directory"
    sync.run_stage=real_run
    # bounded subprocess: timeout and non-zero exit both hold
    real_sub=subprocess.run
    def to(*a,**k):raise subprocess.TimeoutExpired(a[0],1)
    subprocess.run=to
    assert raises(sync.run_stage,"P4_VIEWER",["-c","pass"]).failure.startswith("STAGE_TIMEOUT")
    subprocess.run=real_sub
    assert raises(sync.run_stage,"P4_VIEWER",["-c","raise SystemExit(3)"]).failure.startswith("STAGE_EXIT_3")
    # existing unreceipted directory is never overwritten
    (tmp/"keep"/v50).mkdir(parents=True);(tmp/"keep"/v50/"marker.txt").write_text("old")
    raises(sync.build,seed,tmp/"keep",1950)
    assert (tmp/"keep"/v50/"marker.txt").read_text()=="old"

    # ---- ONE live native case through the real CLI ----
    out=tmp/"out"
    r=subprocess.run([sys.executable,str(ROOT/"TOOLS"/"ARCHIGROW_DESIGN_SYNC.py"),"--seed",str(SEED),"--out-root",str(out),"--target-area","1950"],
                     capture_output=True,text=True,timeout=600)
    assert r.returncode==0,(r.stdout,r.stderr)
    cli=json.loads(r.stdout.strip().splitlines()[-1])
    assert cli["status"]=="PASS" and cli["version"]==v50 and not cli["reused"] and len(cli["dwgs"])==2
    vd=out/v50;rec=json.loads((vd/"design_sync_receipt.json").read_text(encoding="utf-8"))
    assert rec["input_sha256"]==s50==sha(vd/"model"/"input.json")
    assert json.loads((vd/"model"/"massing_result.json").read_text(encoding="utf-8"))["source_sha256"]==s50
    assert len(rec["outputs"])==2
    for o in rec["outputs"]:
        f=vd/o["dwg"]["ref"];assert f.read_bytes()[:6]==b"AC1032" and sha(f)==o["dwg"]["sha256"]
        assert sha(vd/o["dxf"]["ref"])==o["dxf"]["sha256"]
    # browser HTML is bound to the same model and the same stage receipts
    assert s50.encode() in (vd/"viewer"/"viewer.html").read_bytes()
    vr=json.loads((vd/"viewer"/"viewer_receipt.json").read_text(encoding="utf-8"))
    assert vr["source_sha256"]==s50 and vr["output"]["sha256"]==sha(vd/"viewer"/"viewer.html")
    assert json.loads((vd/"dwg"/"massing_dwg_receipt.json").read_text(encoding="utf-8"))["source_sha256"]==s50
    assert rec["legal_status"]=="NOT_VERIFIED" and rec["render_verification"]=="NOT_PERFORMED"
    sync.verify_version(vd)
    # re-run: no overwrite, identical bytes, reused
    before=sha(vd/"design_sync_receipt.json")
    again,reused=sync.build(seed,out,1950)
    assert reused and sha(vd/"design_sync_receipt.json")==before
    # tamper -> verification fails closed
    dwg0=vd/rec["outputs"][0]["dwg"]["ref"];orig=dwg0.read_bytes()
    dwg0.write_bytes(orig+b"x");assert raises(sync.verify_version,vd)
    dwg0.write_bytes(orig);sync.verify_version(vd)

    # ---- local server over the live version (Generate 1950 -> verified reuse; hostile requests rejected before any build) ----
    srv=sync.Server(out,seed,0);threading.Thread(target=srv.serve_forever,daemon=True).start()
    port=srv.port;assert srv.server_address[0]=="127.0.0.1"
    def req(method,path,body=None,headers=None,host=None):
        c=http.client.HTTPConnection("127.0.0.1",port,timeout=30)
        h={"Host":host or "127.0.0.1:%d"%port};h.update(headers or {})
        c.putrequest(method,path,skip_host=True,skip_accept_encoding=True)
        for k,v in h.items():c.putheader(k,v)
        if body is not None:c.putheader("Content-Length",str(len(body)))
        c.endheaders(body)
        resp=c.getresponse();data=resp.read();c.close();return resp.status,resp.getheaders(),data
    try:
        st,hd,page=req("GET","/");page=page.decode()
        assert st==200 and "합성 기하" in page and "Generate" in page and 'type="number"' in page
        assert "http://" not in page.replace("http://127.0.0.1","") and "https://" not in page, "no external requests"
        tok=page.split('var TOKEN="')[1].split('"')[0];assert len(tok)>=32
        ok={"Origin":"http://127.0.0.1:%d"%port,"X-CSRF-Token":tok,"Content-Type":"application/json"}
        body=lambda o:json.dumps(o).encode()
        st,_,d=req("POST","/api/generate",body({"target_area_m2":1950}),ok);j=json.loads(d)
        assert st==200 and j["status"]=="PASS" and j["version"]==v50 and j["reused"] and len(j["dwgs"])==2,j
        st,hd,html=req("GET",j["viewer_url"]);assert st==200 and s50.encode() in html
        assert "default-src 'none'" in dict(hd)["Content-Security-Policy"]
        for dw,o in zip(j["dwgs"],rec["outputs"]):
            st,_,blob=req("GET",dw["url"]);assert st==200 and hashlib.sha256(blob).hexdigest()==dw["sha256"] and blob[:6]==b"AC1032"
        # hostile / malformed POSTs
        n0=sorted(p.name for p in out.iterdir())
        cases=[("no token",body({"target_area_m2":1950}),{k:v for k,v in ok.items() if k!="X-CSRF-Token"},None,403),
               ("bad token",body({"target_area_m2":1950}),{**ok,"X-CSRF-Token":"x"*43},None,403),
               ("no origin",body({"target_area_m2":1950}),{k:v for k,v in ok.items() if k!="Origin"},None,403),
               ("evil origin",body({"target_area_m2":1950}),{**ok,"Origin":"http://evil.example"},None,403),
               ("evil host",body({"target_area_m2":1950}),ok,"evil.example",403),
               ("wrong ctype",body({"target_area_m2":1950}),{**ok,"Content-Type":"text/plain"},None,415),
               ("oversize",b'{"target_area_m2":1950,"x":"'+b"a"*3000+b'"}',ok,None,413),
               ("path key",body({"target_area_m2":1950,"out_dir":"C:/x"}),ok,None,400),
               ("path only",body({"path":"C:/x"}),ok,None,400),
               ("string",body({"target_area_m2":"1950"}),ok,None,400),
               ("bool",body({"target_area_m2":True}),ok,None,400),
               ("NaN",b'{"target_area_m2":NaN}',ok,None,400),
               ("range",body({"target_area_m2":1e9}),ok,None,400),
               ("not json",b"nope",ok,None,400)]
        for name,b_,h_,host,want in cases:
            st,_,d=req("POST","/api/generate",b_,h_,host);assert st==want,(name,st,d)
            assert json.loads(d)["status"]=="HOLD",name
        assert sorted(p.name for p in out.iterdir())==n0, "rejected POSTs must not build anything"
        # no arbitrary files / traversal / unknown methods
        for path in ("/v/%s/../../etc/passwd"%v50,"/v/..%2f..%2fx/viewer","/v/"+v50+"/model/input.json","/v/"+v50+"/dwg/..","/v/T1_000000000000/viewer",
                     "/design_sync_receipt.json","/api/generate"):
            st,_,d=req("GET",path);assert st==404,(path,st)
        assert req("GET","/",host="evil.example")[0]==403
        assert req("PUT","/api/generate",b"{}",ok)[0]==405
    finally:
        srv.shutdown();srv.server_close()
print("architecture_design_sync_test: PASS")
