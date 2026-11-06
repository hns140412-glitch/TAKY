#!/usr/bin/env python3
"""ARCHIGROW project pipeline runtime (TKY-ARCHIPIPE-001).

Executes the stages a project manifest configures, in dependency order:
  AREA_EVIDENCE -> OVERVIEW_BIND / USE_GROUP / LAYOUT_KPI -> AREA_KPI_CROSS_CHECK
  REGULATORY / GEOMETRY_GUARD / PRODUCTION_TRACE -> CASE_CANDIDATE, COMPETITION
Each stage writes a receipt (input/tool fingerprint, output hashes, status, failure class, next route).
An unchanged stage whose last receipt is PASS is reused (restart from last PASS); a HOLD/FAIL blocks its dependents.
Claim level is mechanical only: no legal feasibility, no promotion, no canonical ledger write.
"""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/"TOOLS"
RUNTIME_VERSION="ARCHIGROW_PIPELINE_RUN/2026-10-12.1"
# stage -> (tool file, manifest input key, upstream dependencies)
STAGES={
 "REFERENCE_FORMING":("ARCHIGROW_REFERENCE_FORMING.py","reference_forming",[]),
 "SITE_SOURCE":("ARCHIGROW_PARCEL_SOURCE.py","site_source",[]),
 "SITE_ANALYSIS":("ARCHIGROW_SITE_ANALYSIS_REPORT.py","site_analysis",[]),
 "AREA_EVIDENCE":("ARCHIGROW_AREA_DXF_SVG.py","area",[]),
 "AREA_CHANGESET":("ARCHIGROW_AREA_CHANGESET.py","area_changeset",["AREA_EVIDENCE"]),
 "DESIGN_RULE_REVIEW":("ARCHIGROW_DESIGN_RULE_REVIEW.py","design_review",[]),
 "OVERVIEW_BIND":("ARCHIGROW_DESIGN_OVERVIEW_BIND.py","overview",["AREA_EVIDENCE"]),
 "USE_GROUP":("ARCHIGROW_USE_GROUP_CLASSIFIER.py","use_group",[]),
 "LAYOUT_KPI":("ARCHIGROW_LAYOUT_KPI.py","layout",[]),
 "WORKBOOK_AUDIT":("ARCHIGROW_WORKBOOK_AUDIT.py","workbook",[]),
 "MASSING":("ARCHIGROW_MASSING.py","massing",[]),
 "SITE_CONTEXT":("ARCHIGROW_BUILDING_CONTEXT.py","site_context",["MASSING"]),
 "SOLAR_STUDY":("ARCHIGROW_SOLAR_CONTEXT.py","solar_study",["MASSING"]),
 "AREA_KPI_CROSS_CHECK":(None,"cross_check",["AREA_EVIDENCE","LAYOUT_KPI"]),
 "REGULATORY":("ARCHIGROW_REGULATORY_COMPILER.py","regulatory",[]),
 "GEOMETRY_GUARD":("ARCHIGROW_VISUAL_GEOMETRY_GUARD.py","geometry_guard",[]),
 "PRODUCTION_TRACE":("ARCHIGROW_PRODUCTION_TRACE.py","production",[]),
 "CASE_CANDIDATE":(None,"case_candidate",["PRODUCTION_TRACE"]),
 "COMPETITION":("ARCHIGROW_COMPETITION_RUN.py","competition",[]),
}
ORDER=[s for s in STAGES if s not in ("REFERENCE_FORMING","SITE_ANALYSIS")]  # preserve original default lifecycle; site report is opt-in
# Learned gates from ArchiGrow review/account mining (Drive 10_DOMAINS/02_ARCHIGROW/02_RAW, 2026-09-30): runtime failure -> mined gate name.
LEARNED_GATES={"PROJECT_ID_MISMATCH":"SITE_ID_CONFLICT","CAD_MODEL_AREA_MISMATCH":"CROSS_DOC_VALUE_MISMATCH","STALE":"DRAWING_STATE_CONTRADICTION",
 "PRINT_LEGIBILITY_FAIL":"PRINT_LEGIBILITY_FAIL","SOURCE_GAPS_PRESENT":"SOURCE_VALUE_UNBOUND"}
_mods={}

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_json(v): return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write_json(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding="utf-8"); return p
def mod(tool):
    if tool not in _mods:
        spec=importlib.util.spec_from_file_location(tool[:-3],TOOLS/tool); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); _mods[tool]=m
    return _mods[tool]

class Hold(Exception):
    def __init__(self,failure_class,detail=None): super().__init__(failure_class); self.failure_class=failure_class; self.detail=detail

def identity(project_id,label,value):
    """Target project identity hard lock (ARCHITECTURE_WORK_OS 1.1)."""
    if value is not None and str(value).strip() and str(value).strip()!=project_id:
        raise Hold("PROJECT_ID_MISMATCH",{"input":label,"found":value,"expected":project_id})

# ---------- stage executors: return (status, result, output_paths) ----------
def run_reference_forming(ctx,cfg,out):
    """Actual original-SHA-grounded reference -> ArchiGrow FRONTIER review tasks.

    This is an optional non-authoritative FORMING consumer. A reference is not
    legal approval and a project lacking drawings always returns HOLD.
    """
    identity(ctx["project_id"],"reference_forming.project_id",cfg.get("project_id"))
    evidence=mod("ARCHIGROW_REFERENCE_FORMING.py").build(
        cfg["evidence_manifest"],cfg["collector_candidate_pointer"],ctx["project_id"])
    # Classify the HOLD: project evidence gaps are NOT mining failures.
    # Existing MINING_DIRECTION_DISPATCHER and Mining-V2 perform plan-only
    # intake on one separate semantic-depth request. No worker runs here.
    feedback,mining_candidate=mod("ARCHIGROW_FORMING_FEEDBACK.py").build(
        evidence,cfg["evidence_manifest"],cfg["collector_candidate_pointer"])
    # Optional local evidence relations; never claim LLM mining or legal PASS.
    local_recheck=None
    rechecked_forming=None
    if cfg.get("local_relation_recheck") is True:
        if not cfg.get("seed_text") or not cfg.get("seed_receipt"):
            raise Hold("VERIFIED_LOCAL_TEXT_REQUIRED")
        local_recheck,rechecked_forming=mod("ARCHIGROW_LOCAL_SEMANTIC_RECHECK.py").evaluate(
            evidence,feedback,cfg["evidence_manifest"],cfg["seed_text"],cfg["seed_receipt"])
    p=write_json(out/"reference_forming.json",evidence)
    f=write_json(out/"forming_feedback.json",feedback)
    files=[p,f]
    if mining_candidate is not None:
        c=write_json(out/"mining_preview_request.json",mining_candidate)
        files.append(c)
    if local_recheck is not None:
        local=write_json(out/"local_source_relation_evidence.json",local_recheck)
        again=write_json(out/"forming_reassessed_local_evidence.json",rechecked_forming)
        files.extend([local,again])
    return "HOLD",{
        "source_verified":True,"candidate_count":evidence["candidate_question_count"],
        "forming_status":evidence["forming_stage"],
        "project_source_tasks":feedback["source_project_gap_count"],
        "project_gap_mining_misroutes":feedback["misrouted_project_gaps_to_mining"],
        "semantic_research_preview_tasks":feedback["semantic_depth_gap_count"],
        "mining_plan_index_first":feedback["existing_mining_index_first_planning_performed"],
        "local_relation_recheck_performed":local_recheck is not None,
        "local_verified_source_relations":(local_recheck["source_relation_count"] if local_recheck else 0),
        "local_reference_reassessment":"HOLD_NO_PROJECT_SOURCE",
        "real_semantic_mining_completed":False,
        "live_mining_queue_writes":0,
        "learning_applied":False,"project_approved":False,
        "next_route":"PROJECT_SOURCE_ACQUISITION_AND_MINING_PREVIEW_APPROVAL_GATE"
    },files

def run_area(ctx,cfg,out):
    mapping=load_json(cfg["mapping"]); identity(ctx["project_id"],"area.mapping",mapping.get("project_id"))
    ov=mod("ARCHIGROW_AREA_DXF_SVG.py").export(cfg["dxf"],cfg["mapping"],out,reader=cfg.get("reader","auto"))
    files=[out/n for n in ("design_overview_area.json","area_evidence.svg","area_evidence.csv","stage_receipt.json")]
    return ("PASS" if ov["geometry_status"]!="HOLD" else "HOLD"),{"geometry_status":ov["geometry_status"],"totals":ov["totals"],"issues":ov["issues"]},files
def run_area_changeset(ctx,cfg,out):
    previous=cfg.get("previous_stage_dir")
    if not previous:raise Hold("PREVIOUS_AREA_STAGE_REQUIRED")
    current=ctx["outputs"]["AREA_EVIDENCE"]
    result=mod("ARCHIGROW_AREA_CHANGESET.py").compare(previous,current,out/"area_changeset.json")
    return ("HOLD" if result["status"]=="HOLD" else "PASS"),{
        "candidate_status":result["status"],"changes":len(result["changes"]),
        "area_totals_changed":sum(v["value_changed"] for v in result["area_totals"]),
        "issues":result["issues"],"legal_approved":False
    },[out/"area_changeset.json"]

def run_design_rule_review(ctx,cfg,out):
    doc=load_json(cfg["plan_json"])
    identity(ctx["project_id"],"design_review.plan_json",doc.get("project_id"))
    r=mod("ARCHIGROW_DESIGN_RULE_REVIEW.py").review(cfg["plan_json"],cfg["manual_rulepack_json"],out)
    files=[out/"design_case_review.json",out/"stage_receipt.json",out/"design_review_table.csv",out/"design_review_preview.html"]
    if (out/"alternative_overlay.svg").exists():files.append(out/"alternative_overlay.svg")
    # A rule violation is not an approved project result: keep candidate visible, stage HOLD.
    status="PASS" if r["status"]=="CANDIDATE_CHECK_CLEAR" else "HOLD"
    return status,{"review_status":r["status"],"rule_counts":r["summary"],
                   "alternative_count":len(r["alternatives"]),
                   "legal_feasibility_authorized":False,"approval":"NOT_GRANTED",
                   "failure_class":None if status=="PASS" else "MANUAL_DESIGN_REVIEW_OPEN"},files

def run_overview(ctx,cfg,out):
    approved=load_json(cfg["approved_overview"]); identity(ctx["project_id"],"overview.approved_overview",approved.get("project_id"))
    area=ctx["outputs"]["AREA_EVIDENCE"]/"design_overview_area.json"
    r=mod("ARCHIGROW_DESIGN_OVERVIEW_BIND.py").bind(area,cfg["approved_overview"],out/"overview_binding.json",ctx["inputs"]["area"]["dxf"],ctx["inputs"]["area"]["mapping"])
    # HOLD_REVIEW_REQUIRED is the normal candidate state; stale or geometry HOLD blocks.
    return ("PASS" if r["binding_status"]=="HOLD_REVIEW_REQUIRED" else "HOLD"),{"binding_status":r["binding_status"],"source_freshness":r["source_freshness"]},[out/"overview_binding.json"]
def run_use_group(ctx,cfg,out):
    d=load_json(cfg["input"]); identity(ctx["project_id"],"use_group.input",d.get("project_id"))
    U=mod("ARCHIGROW_USE_GROUP_CLASSIFIER.py")
    r=U.classify(ctx["project_id"],d.get("uses",[]),d.get("source_ref",""),d.get("effective_date",""))
    if d.get("change"):
        c=d["change"]; r["change_of_use"]=U.change_direction(c.get("from_use"),c.get("to_use"),c.get("from_sub_use",""),c.get("to_sub_use",""))
    p=write_json(out/"use_group.json",r)
    return ("PASS" if r["status"]!="HOLD" else "HOLD"),{"status":r["status"],"issues":r["issues"]},[p]
def run_site_source(ctx,cfg,out):
    """Use official EUM area + exact-PNU public cadastral boundary as source evidence."""
    source=load_json(cfg["input"])
    identity(ctx["project_id"],"site_source.input",source.get("project_id"))
    S=mod("ARCHIGROW_PARCEL_SOURCE.py")
    receipt=S.run(cfg["input"],out)
    files=[out/"site_source_receipt.json"]+[Path(p) for p in receipt.get("raw_refs",[])]
    if receipt.get("status")=="PASS":
        files.append(out/"massing_site_input.json")
    return receipt.get("status","HOLD"),{
        "source_pnu":receipt.get("pnu"),
        "eum_area_m2":(receipt.get("eum") or {}).get("area_m2"),
        "cadastral_polygon_area_m2":(receipt.get("parcel") or {}).get("polygon_area_m2"),
        "comparison":receipt.get("comparison"),
        "failure_class":receipt.get("failure_class"),
        "legal_feasibility_authorized":False,
        "source_status":"EUM_AND_VWORLD_VERIFIED" if receipt.get("status")=="PASS" else "HOLD_SOURCE_EVIDENCE",
    },files


def run_site_analysis(ctx,cfg,out):
    """Source-bound site report; design outputs are optional, never prerequisites."""
    receipt_path=cfg.get("site_source_receipt")
    source_input=cfg.get("site_source_input")
    if bool(receipt_path)==bool(source_input):
        raise Hold("SITE_SOURCE_EXACTLY_ONE_REQUIRED")
    files=[]
    if source_input:
        try: source=load_json(source_input)
        except (OSError,ValueError,json.JSONDecodeError) as exc:
            raise Hold("SITE_SOURCE_INPUT_INVALID",str(exc)) from exc
        identity(ctx["project_id"],"site_analysis.site_source_input",source.get("project_id"))
        source_out=out/"source"
        collected=mod("ARCHIGROW_PARCEL_SOURCE.py").run(source_input,source_out)
        receipt_path=source_out/"site_source_receipt.json"
        files.extend(Path(p) for p in collected.get("raw_refs",[]))
    receipt_path=Path(receipt_path)
    if not receipt_path.is_file():
        raise Hold("SITE_SOURCE_RECEIPT_MISSING",str(receipt_path))
    files.insert(0,receipt_path)
    report=mod("ARCHIGROW_SITE_ANALYSIS_REPORT.py")
    try:
        manifest=report.build(ctx["project_id"],receipt_path,out,
                              context=cfg.get("context"),solar=cfg.get("solar"),massing=cfg.get("massing"),option=cfg.get("option"))
    except (report.ReportHold,OSError,ValueError,KeyError,json.JSONDecodeError) as exc:
        raise Hold("SITE_ANALYSIS_EVIDENCE_HOLD",str(exc)) from exc
    files.extend(out/name for name in ("analysis_manifest.json","site_analysis.html","site_map.svg"))
    pptx=out/"site_analysis.pptx"
    if pptx.is_file(): files.append(pptx)
    status="PASS" if manifest.get("source_status")=="PASS" and manifest.get("report_status")!="HOLD" and manifest.get("capabilities",{}).get("pptx")=="AVAILABLE" else "HOLD"
    return status,{"source_status":manifest.get("source_status"),"report_status":manifest.get("report_status"),
                   "pptx_status":manifest.get("capabilities",{}).get("pptx"),
                   "failure_class":None if status=="PASS" else "SITE_ANALYSIS_REPORT_HOLD",
                   "legal_feasibility_authorized":False},files

def run_massing(ctx,cfg,out):
    """Project-bound mass alternatives; local geometry and existing KPI only."""
    input_path=(ctx["outputs"]["SITE_SOURCE"]/"massing_site_input.json"
                if cfg.get("source_stage")=="SITE_SOURCE" else Path(cfg["input"]))
    source=load_json(input_path)
    if cfg.get("source_stage")!="SITE_SOURCE" and source.get("site_area_basis") is not None:
        raise Hold("EUM_AREA_REQUIRES_VERIFIED_SITE_SOURCE_STAGE")
    identity(ctx["project_id"],"massing.input",source.get("project_id"))
    M=mod("ARCHIGROW_MASSING.py")
    try:
        result=M.build(input_path,out)
    except M.MassingHold as exc:
        raise Hold("MASSING_GEOMETRY_HOLD",str(exc))
    return "PASS",{
        "strategies":[{"strategy":o["strategy"],"kpi":o["kpi"]} for o in result["options"]],
        "legal_feasibility_authorized":False,
        "sample_or_project_source_status":result["rule_source_status"],
        "viewer":"massing_viewer.html"
    },[out/"massing_result.json",out/"massing_viewer.html"]

def run_site_context(ctx,cfg,out):
    """Nearby building footprints/heights (VWorld LT_C_BLDGINFO live/fixture or trusted offline GeoJSON); source evidence only."""
    massing=load_json(ctx["outputs"]["MASSING"]/"massing_result.json")
    doc=load_json(cfg["input"]); identity(ctx["project_id"],"site_context.input",doc.get("project_id"))
    cf=massing.get("coordinate_frame") or {}
    origin=cf.get("projected_origin_m") or cf.get("local_origin_projected_m")
    scene={"projected_crs":cf["projected_crs"],"origin_m":origin} if cf.get("projected_crs") in ("EPSG:5186","EPSG:5179") and origin else {"kind":"LOCAL_M"}
    if cfg.get("pages"): doc["fixture_pages"]=cfg["pages"]
    if cfg.get("geojson_file"): doc.setdefault("offline_geojson",{})["path"]=cfg["geojson_file"]
    out.mkdir(parents=True,exist_ok=True)
    eff=write_json(out/"site_context_effective_input.json",doc)
    r=mod("ARCHIGROW_BUILDING_CONTEXT.py").run(eff,out,scene=scene,site_polygon=massing["site_polygon"])
    files=[out/"site_context_receipt.json"]+[Path(x) for x in r.get("raw_refs",[])]
    if r["status"]=="PASS": files.append(out/"context_obstacles.json")
    comp=r.get("completeness") or {}
    return r["status"],{"failure_class":r.get("failure_class"),"source_class":r.get("source_class"),"source_status":r.get("source_status"),
        "building_context_status":r.get("building_context_status","AVAILABLE"),"obstacle_count":comp.get("obstacle_count"),
        "height_unknown_count":comp.get("height_unknown_count"),"legal_feasibility_authorized":False},files

def run_solar_study(ctx,cfg,out):
    """Deterministic direct-sun/shadow study over massing alternatives; geometric exposure, not a legal sunlight test."""
    solar=load_json(cfg["input"]); identity(ctx["project_id"],"solar_study.input",solar.get("project_id"))
    massing_path=ctx["outputs"]["MASSING"]/"massing_result.json"
    context=(ctx["outputs"]["SITE_CONTEXT"]/"context_obstacles.json") if cfg.get("context_stage")=="SITE_CONTEXT" else cfg.get("context_file")
    if not context: raise Hold("CONTEXT_OBSTACLES_REQUIRED")
    S=mod("ARCHIGROW_SOLAR_CONTEXT.py")
    try: report,files=S.build(cfg["input"],massing_path,context,out)
    except S.SolarHold as ex: raise Hold(ex.code,ex.detail)
    ok=report["result_status"]=="PASS"
    return ("PASS" if ok else "HOLD"),{"result_status":report["result_status"],"failure_class":report["hold_reason"],"data_class":report["data_class"],
        "unknown_height_affected_receivers":report["context"]["unknown_height_affected_receiver_count"],
        "claims":report["claims"],"legal_feasibility_authorized":False,"viewer":"solar_viewer.html"},files

def run_layout(ctx,cfg,out):
    model=load_json(cfg["model"]); identity(ctx["project_id"],"layout.model",model.get("project_id"))
    r=mod("ARCHIGROW_LAYOUT_KPI.py").evaluate(model); p=write_json(out/"layout_kpi.json",r)
    return ("PASS" if r["ok"] else "HOLD"),{"status":r["status"],"kpi":r.get("kpi"),"issues":r.get("issues",[])},[p]
def run_workbook(ctx,cfg,out):
    """Excel side of route F: read-only design-overview workbook audit (open CHECK rows, zero defaults, A3 metadata, FAR cells)."""
    r=mod("ARCHIGROW_WORKBOOK_AUDIT.py").audit(cfg["xlsx"],ctx["project_id"],cfg.get("source_role","PROVISIONAL_DERIVED"))
    p=write_json(out/"workbook_audit.json",r)
    return ("PASS" if r["release_status"]!="DRAFT_WITH_ISSUES" else "HOLD"),{"release_status":r["release_status"],"issues":r["issues"],"source_role":r["source_role"]},[p]
def run_cross_check(ctx,cfg,out):
    """Reverse check CAD -> model (playbook route F): CAD area totals vs layout KPI."""
    area=load_json(ctx["outputs"]["AREA_EVIDENCE"]/"design_overview_area.json")
    kpi=load_json(ctx["outputs"]["LAYOUT_KPI"]/"layout_kpi.json").get("kpi") or {}
    rows=[];issues=[]
    for c in cfg if isinstance(cfg,list) else [cfg]:
        tol=c.get("tolerance_m2")
        if not isinstance(tol,(int,float)) or isinstance(tol,bool) or tol<0: raise Hold("TOLERANCE_M2_REQUIRED",c)
        picked=[t["area_m2"] for t in area["totals"] if t["scope"]==c["area_scope"] and (not c.get("area_level") or t["level"]==c["area_level"])]
        if not picked: issues.append({"issue":"AREA_SCOPE_NOT_FOUND","check":c}); continue
        if c["kpi"] not in kpi or kpi[c["kpi"]] is None: issues.append({"issue":"KPI_NOT_FOUND","check":c}); continue
        cad=round(sum(picked),4); model=round(kpi[c["kpi"]],4); delta=round(model-cad,4)
        row={"area_scope":c["area_scope"],"area_level":c.get("area_level"),"kpi":c["kpi"],"cad_area_m2":cad,"model_value":model,"delta":delta,"tolerance_m2":tol,"pass":abs(delta)<=tol}
        rows.append(row)
        if not row["pass"]: issues.append({"issue":"CAD_MODEL_AREA_MISMATCH",**row})
    p=write_json(out/"area_kpi_cross_check.json",{"checks":rows,"issues":issues,"rule":"CAD layer areas and model KPI must agree within declared tolerance; agreement is not legal area approval."})
    return ("PASS" if not issues else "HOLD"),{"checks":rows,"issues":issues},[p]
def run_regulatory(ctx,cfg,out):
    d=load_json(cfg["input"]); identity(ctx["project_id"],"regulatory.project",(d.get("project") or {}).get("project_id"))
    r=mod("ARCHIGROW_REGULATORY_COMPILER.py").run_input(d); p=write_json(out/"regulatory.json",r)
    return ("PASS" if r.get("ok") else "HOLD"),{"path_status":r.get("path_status"),"rejected":r.get("rejected",[]),"feasibility_claim_authorized":False},[p]
def run_guard(ctx,cfg,out):
    d=load_json(cfg["input"])
    for k in ("base","candidate"): identity(ctx["project_id"],"geometry_guard."+k,(d.get(k) or {}).get("project_id"))
    r=mod("ARCHIGROW_VISUAL_GEOMETRY_GUARD.py").run_input(d); p=write_json(out/"geometry_guard.json",r)
    return ("PASS" if r["ok"] else "HOLD"),{"issues":r["issues"]},[p]
def run_production(ctx,cfg,out):
    d=load_json(cfg["trace"]); identity(ctx["project_id"],"production.trace",d.get("project_id"))
    r=mod("ARCHIGROW_PRODUCTION_TRACE.py").run_input(d); p=write_json(out/"production_trace.json",r)
    return ("PASS" if r["ok"] else "HOLD"),{"production_complete":r.get("production_complete"),"issues":r.get("issues",[])},[p]
def run_case(ctx,cfg,out):
    trace=load_json(ctx["outputs"]["PRODUCTION_TRACE"]/"production_trace.json")
    cand=trace.get("learning_candidate") or {"ok":False}
    cand={**cand,"ledger_write":"NOT_PERFORMED","next_route":"HUMAN_REVIEW_THEN_ARCHIGROW_PROJECT_LEARN"}
    p=write_json(out/"case_candidate.json",cand)
    return ("PASS" if cand.get("ok") else "HOLD"),{"candidate_ok":bool(cand.get("ok")),"reason":cand.get("reason")},[p]
def run_competition(ctx,cfg,out):
    cmd=[sys.executable,str(TOOLS/"ARCHIGROW_COMPETITION_RUN.py"),"--out-dir",str(out)]
    for k,flag in (("project_type","--project-type"),("delivery","--delivery"),("focus","--focus"),("brief_file","--brief-file"),("source_dir","--source-dir")):
        if cfg.get(k): cmd+=[flag,str(cfg[k])]
    if cfg.get("brief_verified"): cmd.append("--brief-verified")
    if not cfg.get("render",False): cmd.append("--no-render")
    env={**os.environ,"PYTHONIOENCODING":"utf-8","PYTHONUTF8":"1"}
    proc=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",env=env)
    if proc.returncode!=0:
        err=(proc.stderr or proc.stdout)[-1500:]
        raise Hold("DELIVERY_CONFLICT" if "DELIVERY_CONFLICT" in err else "COMPETITION_RUN_FAILED",err)
    s=load_json(out/"run-summary.json")
    # Source gaps / unrendered output are not a finished package: HOLD with the runner's own next gate.
    status="PASS" if s.get("next_gate")=="VISUAL_SOURCE_CROSS_CHECK" else "HOLD"
    return status,{"delivery":s["delivery"],"final_status":s["final_status"],"next_gate":s["next_gate"],"source_gap_count":s["source_gap_count"]},[out/"run-summary.json"]
EXEC={"REFERENCE_FORMING":run_reference_forming,"SITE_SOURCE":run_site_source,"SITE_ANALYSIS":run_site_analysis,"MASSING":run_massing,"SITE_CONTEXT":run_site_context,"SOLAR_STUDY":run_solar_study,"AREA_EVIDENCE":run_area,"AREA_CHANGESET":run_area_changeset,"DESIGN_RULE_REVIEW":run_design_rule_review,"OVERVIEW_BIND":run_overview,"USE_GROUP":run_use_group,"LAYOUT_KPI":run_layout,"WORKBOOK_AUDIT":run_workbook,
      "AREA_KPI_CROSS_CHECK":run_cross_check,"REGULATORY":run_regulatory,"GEOMETRY_GUARD":run_guard,
      "PRODUCTION_TRACE":run_production,"CASE_CANDIDATE":run_case,"COMPETITION":run_competition}
PATH_KEYS={"seed_text","seed_receipt","evidence_manifest","collector_candidate_pointer","dxf","mapping","approved_overview","input","model","trace","brief_file","source_dir","xlsx","previous_stage_dir","plan_json","manual_rulepack_json","context_file","pages","geojson_file","site_source_receipt","site_source_input","context","solar","massing"}

def resolve_inputs(manifest,base):
    def fix(v):
        if isinstance(v,dict): return {k:(str((base/x).resolve()) if k in PATH_KEYS and isinstance(x,str) and x else
                                          [str((base/y).resolve()) for y in x] if k in PATH_KEYS and isinstance(x,list) and all(isinstance(y,str) for y in x) else fix(x)) for k,x in v.items()}
        if isinstance(v,list): return [fix(x) for x in v]
        return v
    return fix(manifest.get("inputs") or {})
def unbound(v):
    """True when a router template placeholder (null) is still present."""
    if v is None: return True
    if isinstance(v,dict): return any(unbound(x) for x in v.values())
    if isinstance(v,list): return any(unbound(x) for x in v)
    return False
def fingerprint(stage,cfg,upstream):
    tool=STAGES[stage][0]
    files={}
    def walk(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k in PATH_KEYS and isinstance(x,str) and Path(x).is_file(): files[x]=sha_file(x)
                elif k in PATH_KEYS and isinstance(x,list):
                    for y in x:
                        if isinstance(y,str) and Path(y).is_file(): files[y]=sha_file(y)
                else: walk(x)
        elif isinstance(v,list): [walk(x) for x in v]
    walk(cfg)
    collector_sha=sha_file(TOOLS/"ARCHIGROW_PARCEL_SOURCE.py") if stage=="SITE_ANALYSIS" and cfg.get("site_source_input") else None
    return sha_json({"stage":stage,"runtime":RUNTIME_VERSION,"tool_sha":sha_file(TOOLS/tool) if tool else None,"collector_sha":collector_sha,"cfg":cfg,"files":files,"upstream":upstream})

def run(manifest_path,out_dir=None,force=False,only=None):
    manifest_path=Path(manifest_path).resolve(); manifest=load_json(manifest_path)
    if manifest.get("schema")!="ARCHIGROW_PIPELINE_MANIFEST_V1": raise ValueError("MANIFEST_SCHEMA_UNSUPPORTED")
    pid=str(manifest.get("project_id") or "").strip()
    if not pid: raise ValueError("PROJECT_ID_REQUIRED")
    inputs=resolve_inputs(manifest,manifest_path.parent)
    out=Path(out_dir or manifest.get("out_dir") or manifest_path.parent/"archigrow_run").resolve()
    requested=only or manifest.get("stages") or [s for s in ["SITE_ANALYSIS"]+ORDER if STAGES[s][1] in inputs or (s=="CASE_CANDIDATE" and "production" in inputs)]
    unknown=[s for s in requested if s not in STAGES]
    if unknown: raise ValueError("UNKNOWN_STAGE:"+",".join(unknown))
    ctx={"project_id":pid,"inputs":inputs,"outputs":{}}
    results={}; results_upstream={}
    def intact(r): return all(Path(o["ref"]).is_file() and sha_file(o["ref"])==o["sha256"] for o in r.get("outputs",[]))
    for stage in (["REFERENCE_FORMING"] if "REFERENCE_FORMING" in requested else []) + (["SITE_ANALYSIS"] if "SITE_ANALYSIS" in requested else []) + ORDER:
        tool,key,deps=STAGES[stage]; stage_out=out/"stages"/stage; receipt_path=out/"receipts"/f"{stage}.json"
        ctx["outputs"][stage]=stage_out
        if stage not in requested:
            # A stage outside this run may still serve as upstream through its last intact PASS receipt.
            prev=load_json(receipt_path) if receipt_path.exists() else None
            if prev and prev.get("status") in ("PASS","REUSED_LAST_PASS") and intact(prev): results_upstream[stage]=prev
            continue
        cfg=inputs.get(key,{}) if key!="case_candidate" else {}
        if stage=="SOLAR_STUDY" and cfg.get("context_stage")=="SITE_CONTEXT":
            deps=["MASSING","SITE_CONTEXT"]
        if stage=="MASSING" and cfg.get("source_stage")=="SITE_SOURCE":
            if "SITE_SOURCE" not in requested:
                raise ValueError("SITE_SOURCE_MUST_RUN_IN_SAME_PROJECT_PIPELINE")
            deps=["SITE_SOURCE"]
        avail={**results_upstream,**results}
        missing_deps=[d for d in deps if d not in avail]
        blocked=[d for d in deps if d in avail and avail[d]["status"] not in ("PASS","REUSED_LAST_PASS")]
        receipt={"schema":"ARCHIGROW_STAGE_RECEIPT_V1","rule":"TKY-ARCHIPIPE-001","pipeline_id":f"ARCHIGROW:{pid}","stage_id":stage,
                 "runtime":RUNTIME_VERSION,"tool":tool,"claim_level":"MECHANICAL_ONLY"}
        if key not in inputs and stage not in ("CASE_CANDIDATE",):
            receipt.update(status="BLOCKED",failure_class="INPUT_NOT_PROVIDED",next_route="PROVIDE_INPUT:"+key)
        elif unbound(cfg):
            receipt.update(status="BLOCKED",failure_class="INPUT_NOT_BOUND",next_route="BIND_VERIFIED_SOURCE:"+key)
        elif missing_deps or blocked:
            receipt.update(status="BLOCKED",failure_class="UPSTREAM_NOT_PASS",blocked_by=missing_deps+blocked,next_route="RESOLVE:"+",".join(missing_deps+blocked))
        else:
            # Include upstream output hashes: refreshing a public parcel must
            # invalidate cached downstream massing even with unchanged input PNU.
            fp=fingerprint(stage,cfg,{d:{
                "fingerprint":avail[d].get("fingerprint"),
                "output_hashes":[(x.get("ref"),x.get("sha256")) for x in avail[d].get("outputs",[])]
            } for d in deps})
            prev=load_json(receipt_path) if receipt_path.exists() else None
            live_context=stage=="SITE_CONTEXT" and not (cfg.get("pages") or cfg.get("geojson_file"))  # live public data: never replay a cached PASS
            live_site_analysis=stage=="SITE_ANALYSIS" and bool(cfg.get("site_source_input"))
            reusable=bool(stage!="SITE_SOURCE" and not live_context and not live_site_analysis and not force and stage not in ("AREA_CHANGESET","DESIGN_RULE_REVIEW") and prev and prev.get("fingerprint")==fp and prev.get("status") in ("PASS","REUSED_LAST_PASS") and intact(prev))
            if reusable:
                receipt={**prev,"status":"REUSED_LAST_PASS"}
            else:
                receipt["fingerprint"]=fp
                try:
                    status,summary,files=EXEC[stage](ctx,cfg,stage_out)
                    receipt.update(status=status,summary=summary,failure_class=None if status=="PASS" else summary.get("failure_class") or "STAGE_CHECKS_HOLD",
                                   outputs=[{"ref":str(f),"sha256":sha_file(f)} for f in files if Path(f).is_file()])
                except Hold as h:
                    receipt.update(status="HOLD",failure_class=h.failure_class,detail=h.detail)
                except Exception as exc:
                    receipt.update(status="FAIL",failure_class=type(exc).__name__+":"+str(exc)[:300],trace=traceback.format_exc()[-1500:])
                receipt["next_route"]="NEXT_STAGE" if receipt["status"]=="PASS" else "FIX_AND_RERUN_FROM:"+stage
        write_json(receipt_path,receipt); results[stage]=receipt
    ok=lambda s:s in results and results[s]["status"] in ("PASS","REUSED_LAST_PASS")
    # Step-specific evidence ladder instead of one generic PASS (mining P0-3 / AC-03: total PASS must not mask detail CHECK).
    site_receipt=results.get("SITE_SOURCE") or {}
    site_summary=site_receipt.get("summary") or {}
    ladder={"MASSING_GEOMETRY_KPI":ok("MASSING"),
            "EUM_AREA_OBSERVED":bool(site_summary.get("eum_area_m2")),
            "CADASTRAL_API_BOUNDARY_OBSERVED":bool(site_summary.get("cadastral_polygon_area_m2")),
            "SITE_SOURCE_AREA_AND_IDENTITY_CROSSCHECKED":ok("SITE_SOURCE"),
            "SOLAR_DIRECT_SUN_STUDY_COMPUTED":ok("SOLAR_STUDY"),
            "LEGAL_SUNLIGHT_VERIFIED":False,
            "RAW_CALC_MATCH":ok("AREA_EVIDENCE") or ok("LAYOUT_KPI") or ok("WORKBOOK_AUDIT"),
            "GEOMETRY_AGREES":ok("AREA_KPI_CROSS_CHECK"),
            "SOURCE_VERIFIED":False,"APPLICABLE_RULE_VERIFIED":False,"DRAWING_REV_REFLECTED":False,
            "OUTPUT_PRINT_QA":False,"HUMAN_REVIEW":False,"OFFICIAL_ACCEPTANCE":False}
    learned=sorted({LEARNED_GATES[k] for r in results.values() for k in LEARNED_GATES
                    if k in json.dumps([r.get("failure_class"),r.get("summary")],ensure_ascii=False)})
    statuses=[r["status"] for r in results.values()]
    overall=("FAIL" if "FAIL" in statuses else "HOLD" if "HOLD" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS")
    first_open=next((s for s,r in results.items() if r["status"] not in ("PASS","REUSED_LAST_PASS")),None)
    summary={"schema":"ARCHIGROW_PIPELINE_SUMMARY_V1","project_id":pid,"manifest":str(manifest_path),"manifest_sha256":sha_file(manifest_path),
             "runtime":RUNTIME_VERSION,"out_dir":str(out),"status":overall,
             "stages":[{"stage":s,"status":r["status"],"failure_class":r.get("failure_class")} for s,r in results.items()],
             "next_route":("RESUME_FROM:"+first_open) if first_open else "HUMAN_VISUAL_SOURCE_REVIEW",
             "evidence_ladder":ladder,"learned_gates_triggered":learned,
             "release_status":"DRAFT_WITH_ISSUES" if overall!="PASS" else "MECHANICAL_CLEAR__HUMAN_REVIEW_PENDING",
             "approval_inferred":False,
             "claim_level":"MECHANICAL_ONLY","legal_feasibility_authorized":False,"promotion_authorized":False,"ledger_write":"NOT_PERFORMED"}
    write_json(out/"pipeline_summary.json",summary)
    return summary

def main():
    p=argparse.ArgumentParser(description="Execute an ArchiGrow project pipeline manifest with stage receipts and resume.")
    p.add_argument("manifest"); p.add_argument("--out-dir"); p.add_argument("--force",action="store_true")
    p.add_argument("--stage",action="append",help="Run only these stages (dependencies must already PASS in this run).")
    a=p.parse_args(); s=run(a.manifest,a.out_dir,a.force,a.stage)
    print(json.dumps(s,ensure_ascii=False,indent=2))
    return 0 if s["status"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
