#!/usr/bin/env python3
"""ARCHIGROW P8 semantic shared model loop: ONE numeric target-area edit -> P6 versioned massing (P2/P3/P5/P4) -> exact-support check of the
explicit P7 opening template -> derived per-version fixture -> P7 semantic plan (JSON/DXF/HTML) -> native AutoCAD 2024 DWG (+ reopen) -> P8 receipt.

CLI:   ARCHIGROW_DESIGN_SEMANTIC_SYNC.py --seed S.json --opening-template P7_fixture.json --base-model base_massing_result.json --out-root DIR --target-area 1950
Local: same args with --serve --port 0   (127.0.0.1 only, prints READY url)
Doors/windows are NEVER inferred, moved or re-placed: the template is copied only when every opening's SUPPORT geometry (the participating rooms'
polygons, plus the level floor outline for windows) is vertex-identical to the base model the template was authored on; otherwise HOLD
OPENING_SUPPORT_CHANGED. Only then provenance.model_sha256/source_sha256 are rebound to the new P6 model. The template file is never modified.
<out-root>/<P6 version>/semantic/ is create-only and published by semantic_sync_receipt.json written LAST; a failed run removes its semantic/ dir.
Synthetic geometry only: no code compliance, no corridor/egress/vertical (core) connectivity certification, no render or click verification.
Local only, no network, no packages. Python >=3.9 with ezdxf.
"""
import argparse,copy,http.server,importlib.util,json,re,secrets,shutil,sys,threading
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
def _load(name):
    sp=importlib.util.spec_from_file_location(name.lower(),HERE/(name+".py"));m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
sync=_load("ARCHIGROW_DESIGN_SYNC");sem=_load("ARCHIGROW_SEMANTIC_PLAN");dwg=_load("ARCHIGROW_MASSING_DWG")
Hold,hold,sha_file=sync.Hold,sync.hold,sync.sha_file

TOOL_VERSION="ARCHIGROW_DESIGN_SEMANTIC_SYNC/2026-10-28.1"
SCHEMA="ARCHIGROW_SEMANTIC_SYNC_RECEIPT_V1";NATIVE_SCHEMA="ARCHIGROW_SEMANTIC_NATIVE_DWG_RECEIPT_V1"
WORK_ID="TAKY-ARCHI-GROW-001"
P6_BUILD,P6_VERIFY=sync.build,sync.verify_version      # indirection points (tests may replace stages)
COUNT_KEYS=("LWPOLYLINE","LINE","ARC","TEXT","CLOSED","INSUNITS")
MARKER=re.compile(r"TAKY_P8_READBACK LW=(\d+) LINE=(\d+) ARC=(\d+) TEXT=(\d+) CLOSED=(\d+) UNITS=(-?\d+) DWG=([A-Za-z0-9_]+\.dwg)")
CONVERT_SCR='(setvar "FILEDIA" 0)\n(setvar "CMDDIA" 0)\n(command "_.SAVE" "%s")\n(princ)\n'
VERIFY_SCR="""(defun tk (k / s) (if (setq s (ssget "_X" (list (cons 0 k)))) (sslength s) 0))
(setq lw (ssget "_X" '((0 . "LWPOLYLINE"))))
(setq cl 0 i 0)
(if lw (repeat (sslength lw) (setq en (ssname lw i)) (if (= 1 (logand 1 (cdr (assoc 70 (entget en))))) (setq cl (1+ cl))) (setq i (1+ i))))
(progn (princ (strcat "\\nTAKY_P8_READBACK LW=" (itoa (tk "LWPOLYLINE")) " LINE=" (itoa (tk "LINE")) " ARC=" (itoa (tk "ARC")) " TEXT=" (itoa (tk "TEXT")) " CLOSED=" (itoa cl) " UNITS=" (itoa (getvar "INSUNITS")) " DWG=" (getvar "DWGNAME") "\\n")) (princ))
"""
LIMITATIONS=["Synthetic geometry only; not a real site, not statutory, no code-compliance verdict.",
             "Openings exist solely where the explicit template placed them; they were carried over only because their support geometry is unchanged.",
             "No corridor, egress or vertical (core/stair/lift) connectivity is modeled or certified; floors are not connected.",
             "Verification covers hashes, stage PASS, provenance and native DWG reopen counts; viewer rendering and user clicks are not verified by this tool.",
             "Native DWG conversion is performed and verified by this P8 tool; the P7 receipt itself still reports dwg.status NOT_DONE."]

def rel(vd,p):return Path(p).resolve().relative_to(Path(vd).resolve()).as_posix()
def ref(vd,p):return {"ref":rel(vd,p),"sha256":sha_file(p)}
def write_json(p,obj):
    with open(p,"xb") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=1,sort_keys=True).encode("utf-8"))

# ---------- template / support ----------
def support_of(strat,levels,code):
    """Exact geometry that supports each fixture opening: participating rooms (+ level floor when the level has windows)."""
    out={}
    for s,lvs in sorted(strat.items()):
        for L,sp in sorted(lvs.items()):
            if not (sp["doors"] or sp["windows"]):continue
            lv=(levels.get(s) or {}).get(L)
            need=sorted({r for d in sp["doors"] for r in d["pair"]}|{w["room"] for w in sp["windows"]})
            if lv is None or any(r not in lv["rooms"] for r in need):hold("%s:%s/%s:ROOM_OR_LEVEL_MISSING"%(code,s,L),"SUPPORT")
            out["%s/%s"%(s,L)]={"rooms":{r:[list(p) for p in lv["rooms"][r]] for r in need},"floor":[list(p) for p in lv["floor"]] if sp["windows"] else None}
    return out

def check_support(strat,base_levels,new_levels):
    a=support_of(strat,base_levels,"TEMPLATE_BASE_MISMATCH");b=support_of(strat,new_levels,"OPENING_SUPPORT_CHANGED")
    for k,v in a.items():
        for r,p in v["rooms"].items():
            if b[k]["rooms"][r]!=p:hold("OPENING_SUPPORT_CHANGED:%s:%s"%(k,r),"SUPPORT")
        if v["floor"]!=b[k]["floor"]:hold("OPENING_SUPPORT_CHANGED:%s:FLOOR"%k,"SUPPORT")
    return b

def load_template(tpl,base):
    try:
        bm,bsha=sem.load_json(base,"BASE_MODEL");bl,_=sem.validate_model(bm)
        fx,tsha=sem.load_json(tpl,"TEMPLATE");_,strat,_=sem.validate_fixture(fx,bm["project_id"],bm["source_sha256"],bsha)
    except sem.Hold as e:hold("TEMPLATE_INVALID:"+e.args[0],"TEMPLATE")
    if fx["provenance"].get("model_sha256")!=bsha:hold("TEMPLATE_BASE_MODEL_SHA_MISSING_OR_MISMATCH","TEMPLATE")
    support_of(strat,bl,"TEMPLATE_BASE_MISMATCH")
    return fx,strat,bl,{"file":Path(tpl).name,"sha256":tsha,"base_model_file":Path(base).name,"base_model_sha256":bsha,
                        "base_source_sha256":bm["source_sha256"],"project_id":bm["project_id"],"rebound":"model_sha256,source_sha256"}

# ---------- stages ----------
def dxf_counts(path):
    import ezdxf
    doc=ezdxf.readfile(str(path));m=doc.modelspace();lw=list(m.query("LWPOLYLINE"))
    return dict(zip(COUNT_KEYS,(len(lw),len(m.query("LINE")),len(m.query("ARC")),len(m.query("TEXT")),sum(1 for e in lw if e.closed),int(doc.header.get("$INSUNITS",0)))))

def stage_p7(model,fixture,plan_dir,pid,src):
    try:r=sem.run(model,fixture,plan_dir,pid,src)
    except sem.Hold as e:hold("P7_"+e.args[0],"P7_SEMANTIC")
    if r.get("status")!="PASS":hold("P7_NOT_PASS:%s:%s"%(r.get("hold_reason"),{s:v.get("reasons") for s,v in r.get("strategies",{}).items() if v.get("status")!="PASS"}),"P7_SEMANTIC")
    return r

def native_one(vd,exe,s,dxf,d):
    exp=dxf_counts(dxf);dsha=sha_file(dxf);nm=lambda x:d/("semantic_plan_%s%s"%(s,x));made=[];before={p.name for p in d.iterdir()}
    if exp["INSUNITS"]!=6:hold("DXF_INSUNITS_NOT_METERS:"+s)
    dwg.write_new(nm("_convert.scr"),CONVERT_SCR%dwg.lisp_path(nm(".dwg")),made);dwg.write_new(nm("_verify.scr"),VERIFY_SCR,made)
    f=nm(".dwg")
    if f.exists():hold("TARGET_DWG_EXISTS:"+s)
    rc,so,se=dwg.run_cad(exe,["/i",str(dxf),"/s",str(nm("_convert.scr")),"/l","en-US"],d,"convert:"+s,dwg.CALL_TIMEOUT_S)
    dwg.write_new(nm("_convert.stdout.txt"),so,made);dwg.write_new(nm("_convert.stderr.txt"),se,made);dwg.judge_call("convert:"+s,rc,so,se)
    if sha_file(dxf)!=dsha:hold("DXF_MODIFIED_DURING_RUN:"+s)
    if not f.is_file() or f.read_bytes()[:6]!=b"AC1032":hold("DWG_NOT_WRITTEN_OR_NOT_AC1032:"+s)
    wsha=sha_file(f)
    rc,vo,ve=dwg.run_cad(exe,["/i",str(f),"/s",str(nm("_verify.scr")),"/l","en-US"],d,"verify:"+s,dwg.CALL_TIMEOUT_S)
    dwg.write_new(nm("_verify.stdout.txt"),vo,made);dwg.write_new(nm("_verify.stderr.txt"),ve,made);text=dwg.judge_call("verify:"+s,rc,vo,ve)
    m=MARKER.findall(text)
    if len(m)!=1:hold("VERIFY_MARKER_NOT_UNIQUE:%s:%d"%(s,len(m)))
    got=dict(zip(COUNT_KEYS,map(int,m[0][:6])))
    if got!=exp or m[0][6].lower()!=f.name.lower():hold("NATIVE_REOPEN_MISMATCH:%s:%s!=%s"%(s,got,exp))
    if sha_file(f)!=wsha:hold("DWG_CHANGED_BY_REOPEN:"+s)
    for p in d.iterdir():
        if p.name not in before and p not in made and p!=f and p.suffix.lower() in (".dwl",".dwl2",".bak",".sv$"):p.unlink(missing_ok=True)
    return {"strategy":s,"status":"PASS","dxf":ref(vd,dxf),"dwg":{**ref(vd,f),"bytes":f.stat().st_size,"header":"AC1032"},"expected_dxf_counts":exp,
            "native_reopen":{**got,"engine":"AutoCAD_2024_accoreconsole","dwgname":m[0][6]},"logs":{p.name:ref(vd,p) for p in sorted(made)}}

def stage_native(vd,sd,strategies,exe=dwg.DEFAULT_EXE):
    """P7 DXF -> native DWG (SAVE, not SAVEAS) -> reopen with accoreconsole -> separate P8 native receipt."""
    exe=Path(exe)
    if exe.name.lower()!="accoreconsole.exe" or not exe.is_file():hold("ACCORECONSOLE_MISSING","NATIVE_DWG")
    try:
        opts=[]
        for s,dxf in sorted(strategies.items()):
            d=sd/"dwg"/s;d.mkdir(parents=True);opts.append(native_one(vd,exe,s,dxf,d))
    except (dwg.Hold,sem.Hold) as e:hold(e.args[0],"NATIVE_DWG")
    except Hold as h:hold(h.failure,"NATIVE_DWG")
    write_json(sd/"native_dwg_receipt.json",{"schema":NATIVE_SCHEMA,"work_id":WORK_ID,"tool":TOOL_VERSION,"status":"PASS","options":opts,
              "p7_receipt_dwg_status":"NOT_DONE (P7 does not convert; this separate P8 receipt owns native DWG evidence)","legal_status":"NOT_VERIFIED"})

# ---------- provenance chain (build + re-verify) ----------
def collect_semantic(vd,tmeta,p6):
    vd=Path(vd);sd=vd/"semantic";P=dict(fx=sd/"fixture"/"derived_openings.json",p7=sd/"plan"/"semantic_plan_receipt.json",nat=sd/"native_dwg_receipt.json",html=sd/"plan"/"semantic_plan_viewer.html")
    for p in P.values():
        if not p.is_file():hold("MISSING_ARTIFACT:"+p.name,"VERIFY")
    mp=vd/"model"/"massing_result.json";msha=sha_file(mp);src=p6["input_sha256"];pid=p6["project_id"]
    try:
        levels,_=sem.validate_model(sem.load_json(mp,"MODEL")[0],pid,src);fx,fsha=sem.load_json(P["fx"],"FIXTURE")
        strat=sem.validate_fixture(fx,pid,src,msha)[1]
    except sem.Hold as e:hold("DERIVED_INPUT_INVALID:"+e.args[0],"P7_SEMANTIC")
    if fx["provenance"].get("model_sha256")!=msha:hold("FIXTURE_MODEL_SHA_MISMATCH","P7_SEMANTIC")
    supp=support_of(strat,levels,"OPENING_SUPPORT_CHANGED");ssha=sync.sha_bytes(json.dumps(supp,sort_keys=True).encode())
    r7=sync.read_json(P["p7"],"P7_SEMANTIC");nat=sync.read_json(P["nat"],"NATIVE_DWG")
    if r7.get("status")!="PASS" or r7.get("model",{}).get("sha256")!=msha or r7["model"].get("source_sha256")!=src or r7.get("fixture",{}).get("sha256")!=fsha:hold("P7_RECEIPT_PROVENANCE_MISMATCH","P7_SEMANTIC")
    if (r7.get("dwg") or {}).get("status")!="NOT_DONE" or set(r7["strategies"])!=set(levels):hold("P7_RECEIPT_SCOPE_MISMATCH","P7_SEMANTIC")
    plans=[];nopt={o.get("strategy"):o for o in nat.get("options",[]) if isinstance(o,dict)}
    if nat.get("schema")!=NATIVE_SCHEMA or nat.get("status")!="PASS" or set(nopt)!=set(levels):hold("NATIVE_RECEIPT_INVALID","NATIVE_DWG")
    outs=[]
    for s in sorted(levels):
        rec=r7["strategies"][s];o=rec.get("outputs") or {};jp=sd/"plan"/o["json"]["file"];dp=sd/"plan"/o["dxf"]["file"]
        if rec.get("status")!="PASS" or sha_file(jp)!=o["json"]["sha256"] or sha_file(dp)!=o["dxf"]["sha256"]:hold("P7_OUTPUT_DIGEST_MISMATCH:"+s,"P7_SEMANTIC")
        pj=json.loads(jp.read_text(encoding="utf-8"));plans.append(pj)
        if (pj.get("model_sha256"),pj.get("fixture_sha256"),pj.get("source_sha256"),pj.get("project_id"))!=(msha,fsha,src,pid):hold("PLAN_JSON_PROVENANCE_MISMATCH:"+s,"P7_SEMANTIC")
        n=nopt[s];exp=dxf_counts(dp);f=vd/n["dwg"]["ref"];nr=n.get("native_reopen") or {}
        if n.get("status")!="PASS" or n["dxf"]!=ref(vd,dp) or n["dwg"]["ref"]!=rel(vd,f) or sha_file(f)!=n["dwg"]["sha256"] or f.read_bytes()[:6]!=b"AC1032":hold("NATIVE_DWG_DIGEST_MISMATCH:"+s,"NATIVE_DWG")
        if exp["INSUNITS"]!=6 or n.get("expected_dxf_counts")!=exp or {k:nr.get(k) for k in COUNT_KEYS}!=exp:hold("NATIVE_REOPEN_MISMATCH:"+s,"NATIVE_DWG")
        outs.append({"strategy":s,"dwg":{**ref(vd,f),"bytes":f.stat().st_size,"header":"AC1032"},"dxf":ref(vd,dp),"json":ref(vd,jp),"native_counts":exp})
    h=P["html"].read_text(encoding="utf-8");d=sem.html_data(h)
    if r7.get("html",{}).get("sha256")!=sha_file(P["html"]) or d is None or d["strategies"]!=plans:hold("HTML_NOT_BOUND_TO_PLAN_JSON","P7_SEMANTIC")
    return {"schema":SCHEMA,"rule":"TKY-ARCHIPIPE-001","work_id":WORK_ID,"tool":TOOL_VERSION,"status":"PASS","version":vd.name,"project_id":pid,
            "target_area_m2":p6["target_area_m2"],"input_sha256":src,"model_sha256":msha,"template":tmeta,
            "support":{"rule":"EXACT_VERTEX_IDENTITY_OF_PARTICIPATING_ROOMS_AND_WINDOW_LEVEL_FLOOR","support_sha256":ssha,
                       "checked":[{"scope":k,"rooms":sorted(v["rooms"]),"floor":v["floor"] is not None} for k,v in supp.items()]},
            "lineage":[{"stage":"P6_DESIGN_SYNC","sha256":sha_file(vd/"design_sync_receipt.json")},{"stage":"P7_SEMANTIC_PLAN","sha256":sha_file(P["p7"])},
                       {"stage":"P8_NATIVE_DWG","sha256":sha_file(P["nat"])}],
            "files":{"derived_fixture":ref(vd,P["fx"]),"p7_receipt":ref(vd,P["p7"]),"native_receipt":ref(vd,P["nat"]),"viewer":ref(vd,P["html"])},
            "outputs":outs,"limitations":LIMITATIONS,"legal_status":"NOT_VERIFIED","claim_level":"SYNTHETIC_SEMANTIC_PLAN_GEOMETRY_ONLY",
            "render_verification":"NOT_PERFORMED","browser_click_verification":"NOT_PERFORMED_BY_TOOL","p7_own_dwg_status":"NOT_DONE",
            "release_scope":"LOCAL_P8_INTEGRATION_NOT_RELEASE"}

def verify_semantic(vd):
    vd=Path(vd);rp=vd/"semantic"/"semantic_sync_receipt.json"
    if not rp.is_file():hold("VERSION_HAS_NO_SEMANTIC_RECEIPT","VERIFY")
    stored=sync.read_json(rp,"VERIFY")
    if not isinstance(stored,dict) or stored.get("schema")!=SCHEMA or not isinstance(stored.get("template"),dict):hold("RECEIPT_SCHEMA_UNSUPPORTED","VERIFY")
    fresh=collect_semantic(vd,stored["template"],P6_VERIFY(vd))
    if {k:v for k,v in stored.items() if k!="created_utc"}!=fresh:hold("RECEIPT_DRIFT","VERIFY")
    return stored

def build_semantic(seed,out_root,tpl,base,target,exe=dwg.DEFAULT_EXE):
    """-> (receipt, reused). Raises Hold; a failed run leaves no semantic/ dir (a verified P6 version may remain, never shown as P8-current)."""
    fx,strat,bl,tmeta=load_template(tpl,base)
    p6,_=P6_BUILD(seed,out_root,target);vd=Path(out_root)/p6["version"];sd=vd/"semantic"
    if (sd/"semantic_sync_receipt.json").is_file():return verify_semantic(vd),True
    if sd.exists():shutil.rmtree(sd)       # unpublished partial from a crashed run (no final receipt)
    try:
        p6=P6_VERIFY(vd);mp=vd/"model"/"massing_result.json";msha=sha_file(mp)
        try:nl,_=sem.validate_model(sem.load_json(mp,"MODEL")[0],tmeta["project_id"],p6["input_sha256"])
        except sem.Hold as e:hold("MODEL_INVALID:"+e.args[0],"SUPPORT")
        check_support(strat,bl,nl)       # fail closed BEFORE any derived fixture exists
        sd.mkdir();(sd/"fixture").mkdir()
        dfx=copy.deepcopy(fx);dfx["provenance"].update(model_sha256=msha,source_sha256=p6["input_sha256"])
        dfx["provenance"]["note"]=(dfx["provenance"].get("note","")+" | rebound by P8 from template %s (base model %s) after exact opening-support check."%(tmeta["sha256"][:12],tmeta["base_model_sha256"][:12])).strip(" |")
        write_json(sd/"fixture"/"derived_openings.json",dfx)
        r7=stage_p7(mp,sd/"fixture"/"derived_openings.json",sd/"plan",p6["project_id"],p6["input_sha256"])
        stage_native(vd,sd,{s:sd/"plan"/v["outputs"]["dxf"]["file"] for s,v in r7["strategies"].items()},exe)
        if sha_file(tpl)!=tmeta["sha256"]:hold("TEMPLATE_MODIFIED_DURING_RUN","VERIFY")
        rc=collect_semantic(vd,tmeta,p6);rc["created_utc"]=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        write_json(sd/"semantic_sync_receipt.json",rc);verify_semantic(vd)
        return rc,False
    except BaseException:
        shutil.rmtree(sd,ignore_errors=True);raise

# ---------- local server ----------
def _sub(text,old,new):
    if old not in text:raise RuntimeError("P6 page drifted: "+old[:30])
    return text.replace(old,new)
PAGE=sync.PAGE
for _o,_n in (("ARCHIGROW 공유 모델 루프","ARCHIGROW 의미(벽·문·창) 평면 공유 모델 루프"),
              ("합성 기하 매싱 연구입니다. 실제 벽·문·창·피난 경로를 추정하지 않으며 법규 적합 판정이 아닙니다.\n(Synthetic geometric study: no actual walls or openings are inferred; no legal verdict.)",
               "합성(synthetic) 기하입니다. 문·창은 명시 fixture에서만 옮겨지며 법규 적합·코어/수직 동선 검증이 아닙니다.\n(Synthetic geometry; openings only from the explicit template with unchanged support; no code compliance, no core/vertical access verification.)"),
              ("P2 → P3 → P5 / P4가 실제로 다시 실행됩니다.","P6 → P7 → 네이티브 DWG가 실제로 다시 실행됩니다."),
              ("P2 매싱 → P3 DXF → P5 DWG, P4 뷰어","P6 매싱 → P7 시맨틱 → 네이티브 DWG 2개"),
              ('"DWG "+d.strategy','"Semantic DWG "+d.strategy'),("2D 평면 후보 뷰어","시맨틱 평면 상세 뷰어")):PAGE=_sub(PAGE,_o,_n)

class Server(http.server.ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,out_root,seed,tpl,base,port=0,exe=dwg.DEFAULT_EXE):
        self.out_root=Path(out_root);self.seed,self.tpl,self.base,self.exe=seed,tpl,base,exe;self.token=secrets.token_urlsafe(32);self.lock=threading.Lock()
        super().__init__(("127.0.0.1",port),Handler);self.port=self.server_address[1]
        self.allowed_hosts={"127.0.0.1:%d"%self.port,"localhost:%d"%self.port};self.allowed_origins={"http://"+h for h in self.allowed_hosts}
    @property
    def url(self):return "http://127.0.0.1:%d/"%self.port

class Handler(sync.Handler):
    def do_GET(self):
        if not self._host_ok():return self._json(403,{"status":"HOLD","failure":"HOST_REJECTED"})
        path=self.path.split("?",1)[0]
        if path=="/":return self._send(200,PAGE.replace("__TOKEN__",self.server.token).replace("__MIN__","%g"%sync.TARGET_MIN).replace("__MAX__","%g"%sync.TARGET_MAX).encode("utf-8"),"text/html; charset=utf-8",sync.CSP_PAGE)
        m=re.match(r"^/v/([^/]+)/(viewer|dwg/([A-Z_]+))$",path)
        if not m or not sync.VERSION_RE.match(m.group(1)):return self._json(404,{"status":"HOLD","failure":"NOT_FOUND"})
        vd=self.server.out_root/m.group(1)
        try:rec=verify_semantic(vd)         # allowlist = files named by a freshly re-verified P8 receipt
        except Hold:return self._json(404,{"status":"HOLD","failure":"VERSION_NOT_VERIFIED"})
        if m.group(2)=="viewer":return self._send(200,(vd/rec["files"]["viewer"]["ref"]).read_bytes(),"text/html; charset=utf-8",sync.CSP_VIEWER)
        for o in rec["outputs"]:
            if o["strategy"]==m.group(3):
                return self._send(200,(vd/o["dwg"]["ref"]).read_bytes(),"application/octet-stream",None,{"Content-Disposition":'attachment; filename="semantic_plan_%s_%s.dwg"'%(m.group(3),m.group(1))})
        self._json(404,{"status":"HOLD","failure":"NOT_FOUND"})
    def do_POST(self):
        s=self.server
        if not self._host_ok():return self._json(403,{"status":"HOLD","failure":"HOST_REJECTED"})
        if self.path!="/api/generate":return self._json(404,{"status":"HOLD","failure":"NOT_FOUND"})
        if self.headers.get("Origin") not in s.allowed_origins:return self._json(403,{"status":"HOLD","failure":"ORIGIN_REJECTED"})
        if not secrets.compare_digest(self.headers.get("X-CSRF-Token") or "",s.token):return self._json(403,{"status":"HOLD","failure":"CSRF_REJECTED"})
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()!="application/json":return self._json(415,{"status":"HOLD","failure":"CONTENT_TYPE_REJECTED"})
        cl=self.headers.get("Content-Length")
        if self.headers.get("Transfer-Encoding") or not cl or not cl.isdigit():return self._json(411,{"status":"HOLD","failure":"LENGTH_REQUIRED"})
        if int(cl)>sync.BODY_MAX:
            self.close_connection=True;return self._json(413,{"status":"HOLD","failure":"BODY_TOO_LARGE"})
        try:
            body=json.loads(self.rfile.read(int(cl)).decode("utf-8"),parse_constant=lambda c:hold("TARGET_NOT_FINITE","INPUT"))
            if not isinstance(body,dict) or set(body)!={"target_area_m2"}:hold("BODY_KEYS_REJECTED","INPUT")
            t=sync.normalize_target(body["target_area_m2"])
        except Hold as h:return self._json(400,{"status":"HOLD","stage":h.stage,"failure":h.failure})
        except (ValueError,UnicodeDecodeError):return self._json(400,{"status":"HOLD","stage":"INPUT","failure":"BODY_NOT_JSON"})
        try:
            with s.lock:rec,reused=build_semantic(s.seed,s.out_root,s.tpl,s.base,t,s.exe)
        except Hold as h:return self._json(422,{"status":"HOLD","stage":h.stage,"failure":h.failure})
        v=rec["version"]
        self._json(200,{"status":"PASS","semantic":True,"version":v,"target_area_m2":rec["target_area_m2"],"input_sha256":rec["input_sha256"],"model_sha256":rec["model_sha256"],
                        "fixture_sha256":rec["files"]["derived_fixture"]["sha256"],"reused":reused,"viewer_url":"/v/%s/viewer"%v,
                        "dwgs":[{"strategy":o["strategy"],"url":"/v/%s/dwg/%s"%(v,o["strategy"]),"sha256":o["dwg"]["sha256"]} for o in rec["outputs"]],
                        "render_verification":"NOT_PERFORMED","legal_status":"NOT_VERIFIED","claim_level":rec["claim_level"]})

# ---------- CLI ----------
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for a in ("seed","opening-template","base-model","out-root"):p.add_argument("--"+a,required=True)
    p.add_argument("--target-area",type=float,default=None);p.add_argument("--serve",action="store_true");p.add_argument("--port",type=int,default=0)
    p.add_argument("--accoreconsole",default=dwg.DEFAULT_EXE)
    a=p.parse_args(argv)
    if not a.serve and a.target_area is None:p.error("--target-area is required unless --serve")
    if not 0<=a.port<=65535:p.error("--port out of range")
    try:
        seed=sync.load_seed(a.seed)
        if a.target_area is not None:
            rc,reused=build_semantic(seed,a.out_root,a.opening_template,a.base_model,a.target_area,a.accoreconsole)
            print(json.dumps({"status":"PASS","version":rc["version"],"reused":reused,"target_area_m2":rc["target_area_m2"],"input_sha256":rc["input_sha256"],
                              "model_sha256":rc["model_sha256"],"dir":str(Path(a.out_root)/rc["version"]/"semantic"),"dwgs":[o["dwg"]["ref"] for o in rc["outputs"]],
                              "viewer":rc["files"]["viewer"]["ref"],"legal_status":rc["legal_status"],"render_verification":rc["render_verification"]},ensure_ascii=False),flush=True)
        if a.serve:
            srv=Server(a.out_root,seed,a.opening_template,a.base_model,a.port,a.accoreconsole);print("READY "+srv.url,flush=True)
            try:srv.serve_forever()
            except KeyboardInterrupt:pass
            finally:srv.server_close()
        return 0
    except Hold as h:
        print(json.dumps({"status":"HOLD","stage":h.stage,"failure":h.failure},ensure_ascii=False),flush=True);return 2

if __name__=="__main__":
    raise SystemExit(main())
