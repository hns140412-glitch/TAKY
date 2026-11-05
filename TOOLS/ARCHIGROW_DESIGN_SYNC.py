#!/usr/bin/env python3
"""ARCHIGROW P6 shared model loop: ONE numeric target-area edit -> P2 massing -> P3 DXF -> P5 native DWG + P4 2D viewer.

CLI:   ARCHIGROW_DESIGN_SYNC.py --seed seed.json --out-root DIR --target-area 1950
Local: ARCHIGROW_DESIGN_SYNC.py --seed seed.json --out-root DIR --serve --port 0   (127.0.0.1 only, prints the ready URL)

The seed JSON is deep-copied and ONLY constraints.target_far_counted_area_m2 is replaced (finite number, bounded). The serialized input
bytes are hashed; version dir = <out-root>/T<target>_<sha12>/ with model/ dxf/ dwg/ viewer/ and design_sync_receipt.json.
The final receipt is create-only and is written only after every stage exit/receipt/provenance digest matches (collect_chain).
A failed run removes the version directory it created, so nothing partial is ever listed as current; existing versions are never overwritten.
Server: per-process CSRF token + Host/Origin check, 2KB JSON body with the single key target_area_m2, no user paths, only receipt-allowlisted
files (viewer, DWGs) are served after their hashes are re-verified. Local only, no network, no packages. Python >=3.9.
Synthetic spatial massing study only: no actual walls/doors/windows/egress inferred, no legal or code-compliance verdict.
"""
import argparse,copy,hashlib,http.server,json,math,os,re,secrets,shutil,subprocess,sys,threading
from datetime import datetime,timezone
from pathlib import Path

TOOL_VERSION="ARCHIGROW_DESIGN_SYNC/2026-10-28.1"
RECEIPT_SCHEMA="ARCHIGROW_DESIGN_SYNC_RECEIPT_V1"
WORK_ID="TAKY-ARCHI-GROW-001"
HERE=Path(__file__).resolve().parent
GEO_PYTHON=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\.venv_archigrow_geo\Scripts\python.exe")
TARGET_MIN,TARGET_MAX=100.0,10000.0
TARGET_KEY="target_far_counted_area_m2"
SEED_MAX_BYTES=1_000_000
BODY_MAX=2048
TIMEOUTS={"P2_MASSING":120,"P3_DXF":120,"P5_DWG":300,"P4_VIEWER":60}
VERSION_RE=re.compile(r"^T[0-9p]{1,9}_[0-9a-f]{12}$")
STRATEGY_RE=re.compile(r"^[A-Z_]+$")
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
LIMITATIONS=["Synthetic spatial massing study only; no actual walls, doors, windows, corridors or egress are inferred.",
             "Not statutory, not code compliance, not a real site; no legal verdict.",
             "Viewer render and DWG visual quality are not verified by this tool; it verifies hashes, stage PASS and provenance only."]

class Hold(Exception):
    def __init__(self,failure,stage=None):
        super().__init__(failure);self.failure=failure;self.stage=stage

def hold(failure,stage=None):
    raise Hold(failure,stage)

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):return sha_bytes(Path(p).read_bytes())

# ---------- input ----------
def normalize_target(value):
    """Finite real number in range -> int when integral else float. Bool/str/NaN/inf/out-of-range -> Hold."""
    if isinstance(value,bool) or not isinstance(value,(int,float)):hold("TARGET_NOT_NUMBER","INPUT")
    v=float(value)
    if not math.isfinite(v):hold("TARGET_NOT_FINITE","INPUT")
    if not TARGET_MIN<=v<=TARGET_MAX:hold("TARGET_OUT_OF_RANGE:%g..%g"%(TARGET_MIN,TARGET_MAX),"INPUT")
    v=round(v,2)
    return int(v) if v==int(v) else v

def load_seed(seed_path):
    try:
        p=Path(seed_path);raw=p.read_bytes()
        if len(raw)>SEED_MAX_BYTES:hold("SEED_TOO_LARGE","INPUT")
        seed=json.loads(raw.decode("utf-8-sig"),parse_constant=lambda c:hold("SEED_NONFINITE_CONSTANT","INPUT"))
    except (OSError,ValueError):
        hold("SEED_UNREADABLE","INPUT")
    c=seed.get("constraints") if isinstance(seed,dict) else None
    if not isinstance(c,dict) or isinstance(c.get(TARGET_KEY),bool) or not isinstance(c.get(TARGET_KEY),(int,float)):hold("SEED_TARGET_FIELD_MISSING","INPUT")
    return seed

def prepare_input(seed,target):
    """Deep copy, change only the numeric target; return (version_id, serialized bytes, sha256)."""
    t=normalize_target(target)
    doc=copy.deepcopy(seed);doc["constraints"][TARGET_KEY]=t
    data=json.dumps(doc,ensure_ascii=False,indent=2).encode("utf-8")
    digest=sha_bytes(data)
    return "T%s_%s"%(("%g"%t).replace(".","p"),digest[:12]),t,data,digest

# ---------- stage execution ----------
def run_stage(stage,argv,py=None):
    """Bounded, argv-list-only subprocess (no shell). Non-zero exit / timeout -> Hold."""
    cmd=[str(py or sys.executable)]+[str(a) for a in argv]
    try:
        r=subprocess.run(cmd,capture_output=True,timeout=TIMEOUTS[stage],check=False,cwd=str(HERE.parent))
    except subprocess.TimeoutExpired:
        hold("STAGE_TIMEOUT:%ds"%TIMEOUTS[stage],stage)
    except OSError as e:
        hold("STAGE_LAUNCH_FAILED:%s"%type(e).__name__,stage)
    if r.returncode!=0:
        tail=(r.stdout.decode("utf-8","replace").strip()[-300:] or r.stderr.decode("utf-8","replace").strip()[-300:])
        hold("STAGE_EXIT_%d:%s"%(r.returncode,tail),stage)

def read_json(p,stage):
    try:
        return json.loads(Path(p).read_bytes().decode("utf-8-sig"))
    except (OSError,ValueError):
        hold("RECEIPT_UNREADABLE:"+Path(p).name,stage)

def same_path(ref,expected):
    try:
        return Path(ref).resolve()==Path(expected).resolve()
    except (OSError,TypeError,ValueError):
        return False

# ---------- provenance chain (used before the receipt is written AND when a stored version is re-verified) ----------
def collect_chain(vd,target):
    vd=Path(vd)
    inp=vd/"model"/"input.json";res_p=vd/"model"/"massing_result.json"
    p3_p=vd/"dxf"/"massing_dxf_receipt.json";p5_p=vd/"dwg"/"massing_dwg_receipt.json"
    html_p=vd/"viewer"/"viewer.html";vr_p=vd/"viewer"/"viewer_receipt.json"
    for p in (inp,res_p,p3_p,p5_p,html_p,vr_p):
        if not p.is_file():hold("MISSING_ARTIFACT:"+p.name,"VERIFY")
    in_bytes=inp.read_bytes();sha_in=sha_bytes(in_bytes)
    doc=json.loads(in_bytes.decode("utf-8"))
    if doc.get("constraints",{}).get(TARGET_KEY)!=target:hold("INPUT_TARGET_MISMATCH","VERIFY")
    if vd.name!="T%s_%s"%(("%g"%target).replace(".","p"),sha_in[:12]):hold("VERSION_ID_MISMATCH","VERIFY")
    res=read_json(res_p,"P2_MASSING");res_sha=sha_file(res_p)
    if res.get("source_sha256")!=sha_in:hold("P2_SOURCE_SHA_MISMATCH","P2_MASSING")
    pid=res.get("project_id")
    if not isinstance(pid,str) or not pid:hold("P2_PROJECT_ID_MISSING","P2_MASSING")
    res_strats={o.get("strategy") for o in res.get("options",[]) if isinstance(o,dict)}
    p3=read_json(p3_p,"P3_DXF")
    if p3.get("status")!="PASS" or p3.get("project_id")!=pid or p3.get("source_sha256")!=sha_in:hold("P3_NOT_PASS_OR_PROVENANCE","P3_DXF")
    ins=p3.get("inputs") or [{}]
    if ins[0].get("sha256")!=res_sha:hold("P3_INPUT_SHA_MISMATCH","P3_DXF")
    dxfs={}
    for o in p3.get("options",[]):
        s=o.get("strategy");d=o.get("dxf") or {}
        if not isinstance(s,str) or not STRATEGY_RE.match(s) or o.get("status")!="PASS":hold("P3_OPTION_INVALID","P3_DXF")
        f=vd/"dxf"/s/("massing_%s.dxf"%s)
        if not f.is_file() or not same_path(d.get("ref"),f) or d.get("sha256")!=sha_file(f):hold("P3_DXF_DIGEST_MISMATCH:"+s,"P3_DXF")
        dxfs[s]=(f,o.get("entity_count"),d["sha256"])
    if not dxfs or set(dxfs)!=res_strats:hold("P3_STRATEGY_SET_MISMATCH","P3_DXF")
    p5=read_json(p5_p,"P5_DWG")
    if p5.get("status")!="PASS" or p5.get("project_id")!=pid or p5.get("source_sha256")!=sha_in:hold("P5_NOT_PASS_OR_PROVENANCE","P5_DWG")
    if (p5.get("p3_receipt") or {}).get("sha256")!=sha_file(p3_p):hold("P5_P3_RECEIPT_SHA_MISMATCH","P5_DWG")
    dwgs=[]
    p5_opts={o.get("strategy"):o for o in p5.get("options",[]) if isinstance(o,dict)}
    if set(p5_opts)!=set(dxfs):hold("P5_STRATEGY_SET_MISMATCH","P5_DWG")
    for s,(dxf,n,dxf_sha) in sorted(dxfs.items()):
        o=p5_opts[s];d=o.get("dwg") or {};nr=o.get("native_reopen") or {}
        f=vd/"dwg"/s/("massing_%s.dwg"%s)
        if not f.is_file() or not same_path(d.get("ref"),f) or d.get("sha256")!=sha_file(f):hold("P5_DWG_DIGEST_MISMATCH:"+s,"P5_DWG")
        if f.read_bytes()[:6]!=b"AC1032":hold("P5_DWG_HEADER_NOT_AC1032:"+s,"P5_DWG")
        if nr.get("polylines")!=n or nr.get("closed_polylines")!=n or nr.get("insunits")!=6:hold("P5_NATIVE_REOPEN_MISMATCH:"+s,"P5_DWG")
        dwgs.append({"strategy":s,"dxf":{"ref":(Path("dxf")/s/dxf.name).as_posix(),"sha256":dxf_sha},
                     "dwg":{"ref":(Path("dwg")/s/f.name).as_posix(),"sha256":d["sha256"],"bytes":f.stat().st_size,"header":"AC1032"},
                     "native_polylines":n})
    vr=read_json(vr_p,"P4_VIEWER");out=vr.get("output") or {}
    if vr.get("status")!="GENERATED_UNVERIFIED_RENDER" or vr.get("project_id")!=pid or vr.get("source_sha256")!=sha_in:hold("P4_NOT_GENERATED_OR_PROVENANCE","P4_VIEWER")
    if ((vr.get("inputs") or [{}])[0]).get("sha256")!=res_sha:hold("P4_INPUT_SHA_MISMATCH","P4_VIEWER")
    if not same_path(out.get("ref"),html_p) or out.get("sha256")!=sha_file(html_p):hold("P4_HTML_DIGEST_MISMATCH","P4_VIEWER")
    if sha_in.encode() not in html_p.read_bytes():hold("P4_HTML_NOT_BOUND_TO_SOURCE","P4_VIEWER")
    return {"schema":RECEIPT_SCHEMA,"rule":"TKY-ARCHIPIPE-001","work_id":WORK_ID,"tool":TOOL_VERSION,"status":"PASS",
            "version":vd.name,"project_id":pid,"target_area_m2":target,"input_sha256":sha_in,
            "files":{"input":{"ref":"model/input.json","sha256":sha_in},"model_result":{"ref":"model/massing_result.json","sha256":res_sha},
                     "p3_receipt":{"ref":"dxf/massing_dxf_receipt.json","sha256":sha_file(p3_p)},
                     "p5_receipt":{"ref":"dwg/massing_dwg_receipt.json","sha256":sha_file(p5_p)},
                     "viewer":{"ref":"viewer/viewer.html","sha256":out["sha256"]},
                     "viewer_receipt":{"ref":"viewer/viewer_receipt.json","sha256":sha_file(vr_p)}},
            "outputs":dwgs,"shared_source":"model/input.json -> model/massing_result.json feeds both CAD (DXF/DWG) and browser viewer",
            "limitations":LIMITATIONS,"legal_status":"NOT_VERIFIED","claim_level":"SYNTHETIC_SPATIAL_MASSING_GEOMETRY_ONLY",
            "render_verification":"NOT_PERFORMED","release_scope":"LOCAL_SHARED_MODEL_LOOP_NOT_RELEASE"}

def verify_version(vd):
    """Re-verify a stored version: every digest is recomputed and must equal the stored receipt."""
    vd=Path(vd);rp=vd/"design_sync_receipt.json"
    if not rp.is_file():hold("VERSION_HAS_NO_RECEIPT","VERIFY")
    stored=read_json(rp,"VERIFY")
    if not isinstance(stored,dict) or stored.get("schema")!=RECEIPT_SCHEMA:hold("RECEIPT_SCHEMA_UNSUPPORTED","VERIFY")
    fresh=collect_chain(vd,stored.get("target_area_m2"))
    if {k:v for k,v in stored.items() if k!="created_utc"}!=fresh:hold("RECEIPT_DRIFT","VERIFY")
    return stored

# ---------- build ----------
def build(seed,out_root,target):
    """-> (receipt, reused). Raises Hold; any failed run leaves no directory behind."""
    version,t,data,sha_in=prepare_input(seed,target)
    root=Path(out_root);root.mkdir(parents=True,exist_ok=True)
    vd=root/version
    try:
        vd.mkdir()
    except FileExistsError:
        return verify_version(vd),True   # never overwrite: a verified identical version is reused, anything else holds
    try:
        (vd/"model").mkdir()
        inp=vd/"model"/"input.json";inp.write_bytes(data)
        run_stage("P2_MASSING",[HERE/"ARCHIGROW_MASSING.py",inp,"--out-dir",vd/"model"],GEO_PYTHON if GEO_PYTHON.is_file() else None)
        res=vd/"model"/"massing_result.json"
        if not res.is_file():hold("P2_RESULT_MISSING","P2_MASSING")
        pid=read_json(res,"P2_MASSING").get("project_id")
        if not isinstance(pid,str) or not pid:hold("P2_PROJECT_ID_MISSING","P2_MASSING")
        run_stage("P3_DXF",[HERE/"ARCHIGROW_MASSING_DXF.py",res,"--out-dir",vd/"dxf","--expect-project",pid])
        run_stage("P5_DWG",[HERE/"ARCHIGROW_MASSING_DWG.py",vd/"dxf"/"massing_dxf_receipt.json","--out-dir",vd/"dwg","--expect-project",pid])
        run_stage("P4_VIEWER",[HERE/"ARCHIGROW_MASSING_2D_VIEWER.py",res,"--out",vd/"viewer"/"viewer.html","--expect-project",pid,
                               "--receipt",vd/"viewer"/"viewer_receipt.json"])
        receipt=collect_chain(vd,t)
        receipt["created_utc"]=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(vd/"design_sync_receipt.json","xb") as f:
            f.write(json.dumps(receipt,ensure_ascii=False,indent=2).encode("utf-8"))
        verify_version(vd)
        return receipt,False
    except BaseException:
        shutil.rmtree(vd,ignore_errors=True)
        raise

def list_versions(out_root):
    out=[]
    for d in sorted(Path(out_root).glob("T*_*")):
        if VERSION_RE.match(d.name) and (d/"design_sync_receipt.json").is_file():out.append(d.name)
    return out

# ---------- local server ----------
PAGE="""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ARCHIGROW 공유 모델 루프</title>
<style>
:root{--bg:#fbfaff;--ink:#3b3a4a;--mut:#7a7890;--line:#e4e1f2;--p1:#e9e4ff;--p2:#dff3ec;--ok:#2f7d62;--bad:#a8445a}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font:15px/1.5 system-ui,"Malgun Gothic",sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px}
h1{font-size:20px;margin:0 0 4px}.note{background:var(--p1);border-radius:12px;padding:10px 14px;color:var(--ink);margin:10px 0 16px}
form{display:flex;gap:10px;align-items:end;flex-wrap:wrap;background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:14px}
label{display:flex;flex-direction:column;font-size:13px;color:var(--mut);gap:4px}
input{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:10px;width:180px;background:#fff;color:var(--ink)}
button{font:inherit;padding:9px 18px;border:0;border-radius:10px;background:var(--p2);color:var(--ink);cursor:pointer}
button:disabled{opacity:.55;cursor:wait}#st{margin:12px 0;min-height:1.5em}.ok{color:var(--ok)}.bad{color:var(--bad)}
#links a{display:inline-block;margin:0 10px 6px 0;padding:6px 12px;border-radius:10px;background:var(--p1);color:var(--ink);text-decoration:none}
iframe{width:100%;height:640px;border:1px solid var(--line);border-radius:14px;background:#fff;margin-top:8px}
small{color:var(--mut)}
</style></head><body><main>
<h1>ARCHIGROW 공유 모델 루프</h1>
<div class="note">합성 기하 매싱 연구입니다. 실제 벽·문·창·피난 경로를 추정하지 않으며 법규 적합 판정이 아닙니다.
(Synthetic geometric study: no actual walls or openings are inferred; no legal verdict.)</div>
<form id="f"><label>목표 면적 target_far_counted_area_m2 (m²)<input id="t" type="number" step="any" min="__MIN__" max="__MAX__" value="2000" required></label>
<button id="b" type="submit">Generate</button><small>범위 __MIN__–__MAX__ m². 입력 한 값만 바뀌고 P2 → P3 → P5 / P4가 실제로 다시 실행됩니다.</small></form>
<div id="st" role="status"></div><div id="links"></div><iframe id="v" title="2D 평면 후보 뷰어" sandbox="allow-scripts" hidden></iframe>
<script>
var TOKEN="__TOKEN__";
var f=document.getElementById("f"),st=document.getElementById("st"),lk=document.getElementById("links"),fr=document.getElementById("v"),bt=document.getElementById("b");
function say(m,c){st.textContent=m;st.className=c||""}
f.addEventListener("submit",function(e){e.preventDefault();
 var n=Number(document.getElementById("t").value);bt.disabled=true;lk.textContent="";fr.hidden=true;say("생성 중… (P2 매싱 → P3 DXF → P5 DWG, P4 뷰어; 수십 초 걸릴 수 있습니다)");
 fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":TOKEN},body:JSON.stringify({target_area_m2:n})})
 .then(function(r){return r.json()}).then(function(j){
  if(j.status!=="PASS"){say("보류(HOLD): "+(j.stage||"")+" "+(j.failure||"요청 거부"),"bad");return}
  say("PASS "+j.version+" · 입력 sha256 "+j.input_sha256.slice(0,12)+(j.reused?" · 기존 검증 버전 재사용":" · 새로 생성")+" · 렌더 검증 미수행","ok");
  j.dwgs.forEach(function(d){if(d.url.indexOf("/v/")!==0)return;var a=document.createElement("a");a.href=d.url;a.download="";a.textContent="DWG "+d.strategy+" ("+d.sha256.slice(0,8)+")";lk.appendChild(a)});
  if(j.viewer_url.indexOf("/v/")===0){fr.src=j.viewer_url;fr.hidden=false}
 }).catch(function(){say("서버 응답 실패","bad")}).then(function(){bt.disabled=false});
});
</script></main></body></html>
"""
CSP_PAGE="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-src 'self'; base-uri 'none'; form-action 'none'"
CSP_VIEWER="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"

class Server(http.server.ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,out_root,seed,port=0):
        self.out_root=Path(out_root);self.seed=seed;self.token=secrets.token_urlsafe(32);self.lock=threading.Lock()
        super().__init__(("127.0.0.1",port),Handler)
        self.port=self.server_address[1]
        self.allowed_hosts={"127.0.0.1:%d"%self.port,"localhost:%d"%self.port}
        self.allowed_origins={"http://"+h for h in self.allowed_hosts}
    @property
    def url(self):return "http://127.0.0.1:%d/"%self.port

class Handler(http.server.BaseHTTPRequestHandler):
    timeout=15
    server_version="ArchigrowSync"
    sys_version=""
    def log_message(self,*a):pass
    def _send(self,code,body,ctype,csp=None,extra=None):
        self.send_response(code)
        self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","no-referrer")
        if csp:self.send_header("Content-Security-Policy",csp)
        for k,v in (extra or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(body)
    def _json(self,code,obj):
        self._send(code,json.dumps(obj,ensure_ascii=False).encode("utf-8"),"application/json; charset=utf-8")
    def _host_ok(self):
        return self.headers.get("Host") in self.server.allowed_hosts
    def do_GET(self):
        if not self._host_ok():return self._json(403,{"status":"HOLD","failure":"HOST_REJECTED"})
        path=self.path.split("?",1)[0]
        if path=="/":
            page=PAGE.replace("__TOKEN__",self.server.token).replace("__MIN__","%g"%TARGET_MIN).replace("__MAX__","%g"%TARGET_MAX)
            return self._send(200,page.encode("utf-8"),"text/html; charset=utf-8",CSP_PAGE)
        m=re.match(r"^/v/([^/]+)/(viewer|dwg/([A-Z_]+))$",path)
        if not m or not VERSION_RE.match(m.group(1)):return self._json(404,{"status":"HOLD","failure":"NOT_FOUND"})
        try:
            rec=verify_version(self.server.out_root/m.group(1))
        except Hold:
            return self._json(404,{"status":"HOLD","failure":"VERSION_NOT_VERIFIED"})
        if m.group(2)=="viewer":
            f=self.server.out_root/m.group(1)/rec["files"]["viewer"]["ref"]
            return self._send(200,f.read_bytes(),"text/html; charset=utf-8",CSP_VIEWER)
        for o in rec["outputs"]:
            if o["strategy"]==m.group(3):
                f=self.server.out_root/m.group(1)/o["dwg"]["ref"]
                return self._send(200,f.read_bytes(),"application/octet-stream",None,
                                  {"Content-Disposition":'attachment; filename="massing_%s_%s.dwg"'%(m.group(3),m.group(1))})
        self._json(404,{"status":"HOLD","failure":"NOT_FOUND"})
    def do_POST(self):
        s=self.server
        if not self._host_ok():return self._json(403,{"status":"HOLD","failure":"HOST_REJECTED"})
        if self.path!="/api/generate":return self._json(404,{"status":"HOLD","failure":"NOT_FOUND"})
        if self.headers.get("Origin") not in s.allowed_origins:return self._json(403,{"status":"HOLD","failure":"ORIGIN_REJECTED"})
        if not secrets.compare_digest(self.headers.get("X-CSRF-Token") or "",s.token):return self._json(403,{"status":"HOLD","failure":"CSRF_REJECTED"})
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()!="application/json":return self._json(415,{"status":"HOLD","failure":"CONTENT_TYPE_REJECTED"})
        if self.headers.get("Transfer-Encoding"):return self._json(411,{"status":"HOLD","failure":"LENGTH_REQUIRED"})
        cl=self.headers.get("Content-Length")
        if not cl or not cl.isdigit():return self._json(411,{"status":"HOLD","failure":"LENGTH_REQUIRED"})
        if int(cl)>BODY_MAX:
            self.close_connection=True
            return self._json(413,{"status":"HOLD","failure":"BODY_TOO_LARGE"})
        try:
            body=json.loads(self.rfile.read(int(cl)).decode("utf-8"),parse_constant=lambda c:hold("TARGET_NOT_FINITE","INPUT"))
            if not isinstance(body,dict) or set(body)!={"target_area_m2"}:hold("BODY_KEYS_REJECTED","INPUT")
            t=normalize_target(body["target_area_m2"])
        except Hold as h:
            return self._json(400,{"status":"HOLD","stage":h.stage,"failure":h.failure})
        except (ValueError,UnicodeDecodeError):
            return self._json(400,{"status":"HOLD","stage":"INPUT","failure":"BODY_NOT_JSON"})
        try:
            with s.lock:   # one generation at a time; AutoCAD core console is not re-entrant-safe
                rec,reused=build(s.seed,s.out_root,t)
        except Hold as h:
            return self._json(422,{"status":"HOLD","stage":h.stage,"failure":h.failure})
        v=rec["version"]
        self._json(200,{"status":"PASS","version":v,"target_area_m2":rec["target_area_m2"],"input_sha256":rec["input_sha256"],"reused":reused,
                        "viewer_url":"/v/%s/viewer"%v,
                        "dwgs":[{"strategy":o["strategy"],"url":"/v/%s/dwg/%s"%(v,o["strategy"]),"sha256":o["dwg"]["sha256"]} for o in rec["outputs"]],
                        "render_verification":"NOT_PERFORMED","legal_status":"NOT_VERIFIED"})
    def do_PUT(self):self._json(405,{"status":"HOLD","failure":"METHOD_NOT_ALLOWED"})
    do_DELETE=do_PATCH=do_PUT

# ---------- CLI ----------
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--seed",required=True);p.add_argument("--out-root",required=True)
    p.add_argument("--target-area",type=float,default=None)
    p.add_argument("--serve",action="store_true");p.add_argument("--port",type=int,default=0)
    a=p.parse_args(argv)
    if not a.serve and a.target_area is None:p.error("--target-area is required unless --serve")
    if not 0<=a.port<=65535:p.error("--port out of range")
    try:
        seed=load_seed(a.seed)
        if a.target_area is not None:
            rec,reused=build(seed,a.out_root,a.target_area)
            print(json.dumps({"status":"PASS","version":rec["version"],"reused":reused,"target_area_m2":rec["target_area_m2"],
                              "input_sha256":rec["input_sha256"],"dir":str(Path(a.out_root)/rec["version"]),
                              "dwgs":[o["dwg"]["ref"] for o in rec["outputs"]],"viewer":rec["files"]["viewer"]["ref"],
                              "legal_status":rec["legal_status"],"render_verification":rec["render_verification"]},ensure_ascii=False),flush=True)
        if a.serve:
            srv=Server(a.out_root,seed,a.port)
            print("READY "+srv.url,flush=True)
            try:srv.serve_forever()
            except KeyboardInterrupt:pass
            finally:srv.server_close()
        return 0
    except Hold as h:
        print(json.dumps({"status":"HOLD","stage":h.stage,"failure":h.failure},ensure_ascii=False),flush=True)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
