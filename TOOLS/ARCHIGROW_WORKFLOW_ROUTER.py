#!/usr/bin/env python3
"""ARCHIGROW portfolio-wide capability router (non-mutating plan).
Never promotes candidate outputs to approved evidence.
"""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODULES={
"REFERENCE_EVIDENCE":{"script":"ARCHIGROW_REFERENCE_FORMING.py","stage":"REFERENCE_FORMING"},
"SOURCE":{"script":"ARCHIGROW_SOURCE_REGISTRY.py","stage":"SOURCE_LOCK"},
"SITE_LAW":{"script":"ARCHIGROW_REGULATORY_COMPILER.py","stage":"REGULATORY_CANDIDATE"},
"LAYOUT_KPI":{"script":"ARCHIGROW_LAYOUT_KPI.py","stage":"DESIGN_KPI"},
"CAD_AREA_SVG":{"script":"ARCHIGROW_AREA_DXF_SVG.py","stage":"AREA_EVIDENCE"},
"OVERVIEW_BIND":{"script":"ARCHIGROW_DESIGN_OVERVIEW_BIND.py","stage":"OVERVIEW_CANDIDATE"},
"USE_GROUP":{"script":"ARCHIGROW_USE_GROUP_CLASSIFIER.py","stage":"USE_GROUP_CANDIDATE"},
"PRODUCTION":{"script":"ARCHIGROW_PRODUCTION_TRACE.py","stage":"PRODUCTION_TRACE"},
"GEOMETRY_GUARD":{"script":"ARCHIGROW_VISUAL_GEOMETRY_GUARD.py","stage":"GEOMETRY_GUARD"},
"COMPETITION":{"script":"ARCHIGROW_COMPETITION_RUN.py","stage":"REPORT_PACKAGE"},
"CASE_LEARNING":{"script":"ARCHIGROW_PROJECT_LEARN.py","stage":"CASE_CANDIDATE"}
}
ROUTES={
"REFERENCE_REVIEW":["REFERENCE_EVIDENCE"],
"PURSUIT":["SOURCE","SITE_LAW","LAYOUT_KPI","GEOMETRY_GUARD","COMPETITION","CASE_LEARNING"],
"PRODUCTION":["SOURCE","CAD_AREA_SVG","OVERVIEW_BIND","USE_GROUP","SITE_LAW","PRODUCTION","CASE_LEARNING"],
"REPORT":["SOURCE","GEOMETRY_GUARD","COMPETITION","CASE_LEARNING"],
"FULL":["SOURCE","SITE_LAW","LAYOUT_KPI","CAD_AREA_SVG","OVERVIEW_BIND","USE_GROUP","GEOMETRY_GUARD","PRODUCTION","COMPETITION","CASE_LEARNING"]
}
# Router capability -> executable stage(s) of ARCHIGROW_PIPELINE_RUN.py (SOURCE is a registry gate, not a project stage).
PIPELINE_STAGES={"REFERENCE_EVIDENCE":["REFERENCE_FORMING"],"SITE_LAW":["REGULATORY"],"LAYOUT_KPI":["LAYOUT_KPI"],"CAD_AREA_SVG":["AREA_EVIDENCE"],"OVERVIEW_BIND":["OVERVIEW_BIND"],
 "USE_GROUP":["USE_GROUP"],"PRODUCTION":["PRODUCTION_TRACE"],"GEOMETRY_GUARD":["GEOMETRY_GUARD"],"COMPETITION":["COMPETITION"],"CASE_LEARNING":["CASE_CANDIDATE"]}
INPUT_TEMPLATES={"REFERENCE_FORMING":("reference_forming",{"evidence_manifest":None,"collector_candidate_pointer":None}),"REGULATORY":("regulatory",{"input":None}),"LAYOUT_KPI":("layout",{"model":None}),"AREA_EVIDENCE":("area",{"dxf":None,"mapping":None}),
 "OVERVIEW_BIND":("overview",{"approved_overview":None}),"USE_GROUP":("use_group",{"input":None}),"PRODUCTION_TRACE":("production",{"trace":None}),
 "GEOMETRY_GUARD":("geometry_guard",{"input":None}),"COMPETITION":("competition",{"delivery":None,"brief_file":None,"source_dir":None,"render":False})}
def manifest_template(project_id,route):
    """Executable skeleton for ARCHIGROW_PIPELINE_RUN.py; null inputs must be bound to verified project sources before running."""
    stages=[s for name in plan(project_id,route)["steps"] for s in name["pipeline_stages"]]
    inputs={INPUT_TEMPLATES[s][0]:dict(INPUT_TEMPLATES[s][1]) for s in stages if s in INPUT_TEMPLATES}
    if "AREA_EVIDENCE" in stages and "LAYOUT_KPI" in stages:
        stages.insert(stages.index("LAYOUT_KPI")+1,"AREA_KPI_CROSS_CHECK")
        inputs["cross_check"]=[{"area_scope":None,"area_level":None,"kpi":"gfa_area","tolerance_m2":None}]
    return {"schema":"ARCHIGROW_PIPELINE_MANIFEST_V1","project_id":project_id,"route":route,"stages":stages,"inputs":inputs,
            "binding_status":"UNBOUND_TEMPLATE","rule":"Bind every null input to a verified target-project source; reference-project data is not target evidence."}
def plan(project_id,route):
    if not project_id or not project_id.strip():raise ValueError("PROJECT_ID_REQUIRED")
    if route not in ROUTES:raise ValueError("UNKNOWN_ROUTE")
    steps=[]
    for name in ROUTES[route]:
        m=MODULES[name];script=ROOT/"TOOLS"/m["script"]
        steps.append({"capability":name,"stage":m["stage"],"script":str(script),"script_exists":script.is_file(),"pipeline_stages":PIPELINE_STAGES.get(name,[]),"execution":"NOT_RUN","input_contract":"PROJECT_SPECIFIC_BINDING_REQUIRED","output_status":"CANDIDATE"})
    return {"schema":"ARCHIGROW_WORKFLOW_ROUTER_V1","project_id":project_id,"route":route,"authority":"DOMAIN/ARCHITECTURE_WORK_OS.md","executor":"TOOLS/ARCHIGROW_PIPELINE_RUN.py","steps":steps,"status":"ROUTING_ONLY_NOT_EXECUTED","deployment":"NOT_AUTHORIZED","legal_approval":"NOT_INFERRED"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("project_id");p.add_argument("--route",choices=ROUTES,default="FULL");p.add_argument("--output");p.add_argument("--manifest-template",action="store_true",help="Emit an ARCHIGROW_PIPELINE_RUN manifest skeleton instead of the plan.")
    a=p.parse_args();result=manifest_template(a.project_id,a.route) if a.manifest_template else plan(a.project_id,a.route);payload=json.dumps(result,ensure_ascii=False,indent=2)
    if a.output:Path(a.output).write_text(payload,encoding="utf-8")
    else:print(payload)
