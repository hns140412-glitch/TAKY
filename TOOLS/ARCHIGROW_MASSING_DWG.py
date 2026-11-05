#!/usr/bin/env python3
"""ARCHIGROW massing DXF receipt (P3) -> native AC1032 DWG via installed AutoCAD 2024 Core Console, reopened and verified natively.

Per P3 option: accoreconsole /i <dxf> /s convert.scr  ((command "_.SAVE" <dwg>), NOT -SAVEAS) ->
header AC1032 check -> accoreconsole /i <dwg> /s verify.scr -> marker TAKY_NATIVE_DWG_POLYLINES=n CLOSED=n INSUNITS=6 DWGNAME=x.dwg
judged against the P3 entity_count. Fail closed (HOLD): bad/unpassed P3 receipt, wrong project, DXF sha drift, unsafe names/paths,
existing targets (never overwritten), missing core console, license/policy text, timeout, non-zero exit, stderr output, marker mismatch.
Script content is generated only from validated enumerations (strategy A-Z_) and a strictly checked ASCII path; no raw text reaches LISP.
Synthetic sample boundary and room area polygons only; not finished walls/doors/windows/corridors, not statutory, not a real site.
Local only: no network, no packages. Python >=3.9.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path

TOOL_VERSION="ARCHIGROW_MASSING_DWG/2026-10-27.1"
RECEIPT_SCHEMA="ARCHIGROW_MASSING_DWG_RECEIPT_V1"
P3_SCHEMA="ARCHIGROW_MASSING_DXF_RECEIPT_V1"
DEFAULT_EXE=r"C:\Program Files\Autodesk\AutoCAD 2024\accoreconsole.exe"
CALL_TIMEOUT_S=40      # hard ceiling per accoreconsole call
EXPECT_INSUNITS=6      # meters
STRATEGY=re.compile(r"^[A-Z_]+$")
SHA=re.compile(r"^[0-9a-f]{64}$")
SAFE_PATH=re.compile(r"^[A-Za-z]:[ -~]+$")   # printable ASCII only
UNSAFE_CHARS=set('"\\;()\'`%^&|<>*?')        # quotes / LISP / shell metacharacters (path is given with forward slashes)
MARKER=re.compile(r"TAKY_NATIVE_DWG_POLYLINES=(\d+) CLOSED=(\d+) INSUNITS=(-?\d+) DWGNAME=([A-Za-z0-9_]+\.dwg)")
LICENSE=re.compile(r"licen[sc]|activation|expired|subscription|unauthori[sz]ed|not authori[sz]ed|restricted|policy|sign[- ]?in|trial",re.I)
VERIFY_SCR="""(setq ss (ssget "_X" '((0 . "LWPOLYLINE"))))
(setq n (if ss (sslength ss) 0))
(setq closed 0)
(setq i 0)
(repeat n (setq en (ssname ss i)) (if (= 1 (logand 1 (cdr (assoc 70 (entget en))))) (setq closed (1+ closed))) (setq i (1+ i)))
(progn (princ (strcat "\\nTAKY_NATIVE_DWG_POLYLINES=" (itoa n) " CLOSED=" (itoa closed) " INSUNITS=" (itoa (getvar "INSUNITS")) " DWGNAME=" (getvar "DWGNAME") "\\n")) (princ))
"""
LIMITATIONS=["Synthetic sample boundary and room area polygon only; not finished wall/door/window/corridor.",
             "Not statutory, not code compliance, not a real site; geometry is a mechanical conversion of the P3 DXF.",
             "Native reopen counts LWPOLYLINE closure and INSUNITS only; no design, area or legal verification beyond P3."]

class Hold(Exception):
    pass

def hold(code):
    raise Hold(code)
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def decode(raw):
    """accoreconsole output may be UTF-16LE (NUL-rich) or ANSI/UTF-8."""
    if raw[:2] in (b"\xff\xfe",b"\xfe\xff") or (raw and raw.count(b"\0")*4>len(raw)):
        return raw.decode("utf-16",errors="replace") if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else raw.decode("utf-16le",errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949",errors="replace")
def lisp_path(p):
    s=str(p).replace("\\","/")
    if not SAFE_PATH.match(s) or UNSAFE_CHARS & set(s):hold("UNSUPPORTED_PATH:"+Path(s).name[:40].encode("ascii","replace").decode())
    return s

# ---------- P3 receipt validation (before any file is written) ----------
def validate(receipt_path,expect_project):
    receipt_path=Path(receipt_path)
    try:
        r=json.loads(receipt_path.read_bytes().decode("utf-8-sig"))
    except (ValueError,OSError):
        hold("P3_RECEIPT_UNREADABLE")
    if not isinstance(r,dict) or r.get("schema")!=P3_SCHEMA or r.get("stage_id")!="MASSING_DXF_HANDOFF" or r.get("rule")!="TKY-ARCHIPIPE-001":hold("P3_RECEIPT_SCHEMA_UNSUPPORTED")
    if r.get("status")!="PASS":hold("P3_RECEIPT_NOT_PASS:%s"%r.get("status"))
    pid=r.get("project_id")
    if not isinstance(pid,str) or not pid:hold("PROJECT_ID_REQUIRED")
    if pid!=expect_project:hold("PROJECT_MISMATCH:%s!=%s"%(pid,expect_project))
    if not SHA.match(str(r.get("source_sha256") or "")):hold("P3_SOURCE_SHA256_MISSING_OR_INVALID")
    ins=r.get("inputs")
    if not isinstance(ins,list) or not ins or not all(isinstance(i,dict) and SHA.match(str(i.get("sha256") or "")) for i in ins):hold("P3_INPUT_PROVENANCE_MISSING")
    opts=r.get("options")
    if not isinstance(opts,list) or not opts:hold("P3_OPTIONS_MISSING")
    base=receipt_path.resolve().parent;seen=set();out=[]
    for o in opts:
        if not isinstance(o,dict):hold("P3_OPTION_MALFORMED")
        s=o.get("strategy")
        if not isinstance(s,str) or not STRATEGY.match(s):hold("STRATEGY_NAME_UNSUPPORTED")
        if s in seen:hold("STRATEGY_DUPLICATE:"+s)
        seen.add(s)
        if o.get("status")!="PASS" or (o.get("area_stage_receipt") or {}).get("status")!="PASS":hold("P3_OPTION_NOT_PASS:"+s)
        n=o.get("entity_count")
        if isinstance(n,bool) or not isinstance(n,int) or n<1:hold("P3_ENTITY_COUNT_INVALID:"+s)
        lc=o.get("layer_entity_counts")
        if not isinstance(lc,dict) or sum(v for v in lc.values() if isinstance(v,int))!=n:hold("P3_ENTITY_COUNT_INCONSISTENT:"+s)
        d=o.get("dxf")
        if not isinstance(d,dict) or not isinstance(d.get("ref"),str) or not SHA.match(str(d.get("sha256") or "")):hold("P3_DXF_REF_INVALID:"+s)
        dxf=Path(d["ref"])
        try:
            rd=dxf.resolve(strict=True)
        except OSError:
            hold("P3_DXF_MISSING:"+s)
        if not rd.is_file() or rd.name!="massing_%s.dxf"%s or base not in rd.parents:hold("P3_DXF_PATH_NOT_OWNED_BY_RECEIPT:"+s)
        if sha(rd)!=d["sha256"]:hold("P3_DXF_SHA_MISMATCH:"+s)
        out.append({"strategy":s,"dxf":rd,"dxf_sha256":d["sha256"],"entity_count":n})
    return r,out

# ---------- CAD calls ----------
def run_cad(exe,args,cwd,tag,timeout):
    """One accoreconsole call. Returns (returncode,stdout_bytes,stderr_bytes); timeout -> HOLD."""
    try:
        p=subprocess.run([str(exe)]+args,cwd=str(cwd),capture_output=True,timeout=min(timeout,CALL_TIMEOUT_S),stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        hold("CAD_TIMEOUT:"+tag)
    except OSError as e:
        hold("CAD_LAUNCH_FAILED:%s:%s"%(tag,type(e).__name__))
    return p.returncode,p.stdout,p.stderr

def judge_call(tag,rc,out,err):
    text=decode(out)+"\n"+decode(err)
    if LICENSE.search(text):hold("NATIVE_CAD_LICENSE_OR_POLICY:"+tag)
    if rc!=0:hold("CAD_NONZERO_EXIT:%s:%s"%(tag,rc))
    if err.strip():hold("CAD_STDERR_OUTPUT:"+tag)
    return decode(out)

def write_new(path,data,created):
    """Create-only write (never overwrites)."""
    with open(path,"xb") as f:
        f.write(data if isinstance(data,bytes) else data.encode("utf-8"))
    created.append(Path(path))

def convert_option(exe,o,out,created,timeout):
    s=o["strategy"];d=out/s
    names={k:d/("massing_%s%s"%(s,ext)) for k,ext in {"dwg":".dwg","cscr":"_convert.scr","vscr":"_verify.scr","cout":"_convert.stdout.txt",
           "cerr":"_convert.stderr.txt","vout":"_verify.stdout.txt","verr":"_verify.stderr.txt"}.items()}
    d.mkdir(exist_ok=True)
    before={p.name for p in d.iterdir()}
    write_new(names["cscr"],'(setvar "FILEDIA" 0)\n(setvar "CMDDIA" 0)\n(command "_.SAVE" "%s")\n(princ)\n'%lisp_path(names["dwg"]),created)
    write_new(names["vscr"],VERIFY_SCR,created)
    rec={"strategy":s,"status":"HOLD","dxf":{"ref":str(o["dxf"]),"sha256":o["dxf_sha256"]},"expected_entity_count":o["entity_count"]}
    if names["dwg"].exists():hold("TARGET_DWG_EXISTS:"+s)  # re-check right before the CAD call
    rc,so,se=run_cad(exe,["/i",str(o["dxf"]),"/s",str(names["cscr"]),"/l","en-US"],d,"convert:"+s,timeout)
    write_new(names["cout"],so,created);write_new(names["cerr"],se,created)
    if names["dwg"].exists() and names["dwg"] not in created:created.append(names["dwg"])
    judge_call("convert:"+s,rc,so,se)
    if sha(o["dxf"])!=o["dxf_sha256"]:hold("P3_DXF_MODIFIED_DURING_RUN:"+s)
    if not names["dwg"].is_file():hold("DWG_NOT_WRITTEN:"+s)
    with open(names["dwg"],"rb") as f:header=f.read(6)
    if header!=b"AC1032":hold("DWG_HEADER_NOT_AC1032:"+s)
    dwg_sha=sha(names["dwg"])
    rc2,vo,ve=run_cad(exe,["/i",str(names["dwg"]),"/s",str(names["vscr"]),"/l","en-US"],d,"verify:"+s,timeout)
    write_new(names["vout"],vo,created);write_new(names["verr"],ve,created)
    text=judge_call("verify:"+s,rc2,vo,ve)
    m=MARKER.findall(text)
    if len(m)!=1:hold("VERIFY_MARKER_NOT_UNIQUE:%s:%d"%(s,len(m)))
    n,closed,units,name=int(m[0][0]),int(m[0][1]),int(m[0][2]),m[0][3]
    if name.lower()!=names["dwg"].name.lower():hold("VERIFY_DWGNAME_MISMATCH:"+s)
    if n!=o["entity_count"]:hold("NATIVE_ENTITY_COUNT_MISMATCH:%s:%d!=%d"%(s,n,o["entity_count"]))
    if closed!=n:hold("NATIVE_POLYLINE_NOT_CLOSED:%s:%d/%d"%(s,closed,n))
    if units!=EXPECT_INSUNITS:hold("NATIVE_INSUNITS_NOT_METERS:%s:%d"%(s,units))
    if sha(names["dwg"])!=dwg_sha:hold("DWG_CHANGED_BY_REOPEN:"+s)
    # only files this run created that the console itself may add next to the DWG (lock/backup) are cleaned
    for p in d.iterdir():
        if p.name not in before and p not in created and p.suffix.lower() in (".dwl",".dwl2",".bak",".sv$"):
            p.unlink(missing_ok=True)
    rec.update(status="PASS",dwg={"ref":str(names["dwg"]),"sha256":dwg_sha,"bytes":names["dwg"].stat().st_size,"header":"AC1032"},
               native_reopen={"engine":"AutoCAD_2024_accoreconsole","polylines":n,"closed_polylines":closed,"insunits":units,"dwgname":name},
               logs={k:{"ref":str(names[k]),"sha256":sha(names[k])} for k in ("cscr","vscr","cout","cerr","vout","verr")})
    return rec

def build(p3_receipt,out_dir,expect_project,exe=DEFAULT_EXE,timeout=CALL_TIMEOUT_S):
    p3=Path(p3_receipt);out=Path(out_dir)
    receipt={"schema":RECEIPT_SCHEMA,"rule":"TKY-ARCHIPIPE-001","stage_id":"MASSING_DWG_HANDOFF","tool":TOOL_VERSION,
             "work_id":"TAKY-ARCHI-GROW-001","p3_receipt":None,"project_id":None,"source_sha256":None,"p3_inputs":[],"options":[],
             "status":"HOLD","failure_class":None,"limitations":LIMITATIONS,"legal_status":"NOT_VERIFIED",
             "claim_level":"NATIVE_DWG_CONVERSION_OF_SYNTHETIC_GEOMETRY_ONLY","release_scope":"LOCAL_CAD_HANDOFF_NOT_PORTFOLIO_RELEASE"}
    created=[];dwgs=[];may_write=True
    try:
        base=p3.resolve().parent;oo=out.resolve()
        if oo==base or base in oo.parents or oo in base.parents:
            may_write=False;hold("OUT_DIR_OVERLAPS_P3_INPUT")
        try:
            receipt["p3_receipt"]={"ref":str(p3),"sha256":sha(p3)}
        except OSError:
            hold("P3_RECEIPT_UNREADABLE")
        r,opts=validate(p3,expect_project)
        receipt.update(project_id=r["project_id"],source_sha256=r["source_sha256"],p3_inputs=r["inputs"],pipeline_id="ARCHIGROW_MASSING_DWG:"+r["project_id"])
        exe=Path(exe)
        if exe.name.lower()!="accoreconsole.exe" or not exe.is_file():hold("ACCORECONSOLE_MISSING")
        receipt["cad_engine"]={"exe":str(exe),"exe_sha256":sha(exe)}
        try:
            outr=out.resolve()
        except OSError:
            hold("OUT_DIR_UNUSABLE")
        for o in opts:  # P3 inputs are read-only: output may not live beside/inside any P3 DXF directory
            dd=o["dxf"].parent
            if outr==dd or dd in outr.parents or outr in dd.parents:may_write=False;hold("OUT_DIR_OVERLAPS_P3_INPUT")
        lisp_path(outr/"x")  # path safety before anything is written
        if outr.exists() and not outr.is_dir():hold("OUT_DIR_NOT_A_DIRECTORY")
        for o in opts:  # whole-run conflict check first: nothing is overwritten, nothing is half-written
            d=outr/o["strategy"]
            for ext in (".dwg","_convert.scr","_verify.scr","_convert.stdout.txt","_convert.stderr.txt","_verify.stdout.txt","_verify.stderr.txt"):
                if (d/("massing_%s%s"%(o["strategy"],ext))).exists():hold("TARGET_EXISTS:massing_%s%s"%(o["strategy"],ext))
        outr.mkdir(parents=True,exist_ok=True)
        for o in opts:
            receipt["options"].append(convert_option(exe,o,outr,created,timeout))
            dwgs.append(Path(receipt["options"][-1]["dwg"]["ref"]))
        receipt["status"]="PASS"
    except Hold as h:
        # No partial export may stand: remove DWGs created in this run only. Scripts/logs stay as diagnostic evidence.
        for p in created:
            if p.suffix.lower()==".dwg":p.unlink(missing_ok=True)
        receipt["options"]=[];receipt["failure_class"]=str(h)
        receipt["diagnostic_files"]=sorted(str(p) for p in created if p.suffix.lower()!=".dwg")
    # the stage receipt itself is create-only too
    rp=out/"massing_dwg_receipt.json"
    if not may_write:
        receipt["receipt_ref"]=None
        return receipt
    try:
        out.mkdir(parents=True,exist_ok=True)
        with open(rp,"xb") as f:
            f.write(json.dumps(receipt,ensure_ascii=False,indent=2).encode("utf-8"))
        receipt["receipt_ref"]=str(rp)
    except FileExistsError:
        receipt["receipt_ref"]=None
        if receipt["status"]=="PASS":
            # cannot persist the evidence without overwriting: do not leave unreceipted DWGs standing
            for p in dwgs:p.unlink(missing_ok=True)
            receipt.update(status="HOLD",failure_class="RECEIPT_EXISTS",options=[])
    except OSError:
        receipt["receipt_ref"]=None
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("p3_receipt");p.add_argument("--out-dir",required=True)
    p.add_argument("--expect-project",required=True,help="fail closed unless the P3 receipt belongs to this project_id")
    p.add_argument("--accoreconsole",default=DEFAULT_EXE)
    a=p.parse_args()
    r=build(a.p3_receipt,a.out_dir,a.expect_project,a.accoreconsole)
    print(json.dumps({"status":r["status"],"project_id":r["project_id"],"failure":r["failure_class"],
                      "options":[{"strategy":o["strategy"],"dwg":o["dwg"]["ref"],"dwg_sha256":o["dwg"]["sha256"],"native_polylines":o["native_reopen"]["polylines"]} for o in r["options"]],
                      "receipt":r["receipt_ref"],"legal_status":r["legal_status"]},ensure_ascii=False))
    return 0 if r["status"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
