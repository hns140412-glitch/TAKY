#!/usr/bin/env python3
"""TAKY Work OS productive router: idea discovery -> source-grounded case comparison.

Discovery is an executable research specification, NOT a claim that searches,
original-source review, model calls, implementation or QA have run.
The existing original-source independent-review standard remains authoritative.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

PIPELINE=["GOAL","DISCOVER","BUILD","VERIFY","SHIP","LEARN"]
VIS={
    "comparison":"TABLE",
    "process_flow":"FLOW_DIAGRAM",
    "numeric_relation":"CHART",
    "interface_structure":"WIREFRAME",
    "spatial_location":"MAP",
    "simple_explanation":"TEXT",
}
EVIDENCE={"OBSERVED","INFERRED","EXPERIMENTAL","UNVERIFIED"}

# Search lanes are complementary evidence routes, not a mandatory fixed count.
# No arbitrary cap may shrink the search when the task warrants more evidence.
DISCOVERY_LANES={
    "EXISTING_ASSETS":"CURRENT, approved designs, working source code, failed earlier attempts",
    "DOMESTIC_DIRECT":"local practitioners, commercial products, creators, public examples",
    "INTERNATIONAL_DIRECT":"international practitioners, products, creator demos, forums",
    "OPEN_SOURCE":"GitHub repositories, packages, implementation files, tests, licenses",
    "RESEARCH_STANDARDS":"papers, patents, standards, official implementation manuals",
    "ADJACENT_DOMAIN":"transferable techniques from another profession or application",
    "FAILURES_COUNTEREXAMPLES":"negative reviews, known limitations, misleading demos, failed approaches",
    "OFFICIAL_AUTHORITIES":"authoritative laws, regulatory data, versioning, technical source data"
}
ANALYSIS_FIELDS=(
    "source_ref","claim_vs_observation","inputs","processing_logic",
    "algorithm_or_code","dependencies","outputs","failure_modes",
    "license_cost","reproduction_steps","verification_evidence"
)
METHODS=(
    "REUSE_EXISTING","ADAPT_OPEN_SOURCE","NATIVE_TOOL_OR_MCP",
    "LOCAL_DETERMINISTIC_BUILD","PAID_EXTERNAL_OPTION","HYBRID"
)
REVIEW_STANDARD="TAKY_AI_WORKBENCH/00_CONTROL/MINING_AND_REVIEW_STANDARD_CURRENT.json"


def explore_idea(record:dict)->dict:
    idea=str(record.get("idea") or record.get("intent_text") or "").strip()
    if not idea:
        return {"pass":False,"detected":["IDEA_REQUIRED"]}
    required=record.get("required_lanes")
    if required is None:
        required=list(DISCOVERY_LANES)
    if not isinstance(required,list) or any(x not in DISCOVERY_LANES for x in required):
        return {"pass":False,"detected":["INVALID_REQUIRED_DISCOVERY_LANE"]}
    required=list(dict.fromkeys(required))
    known=record.get("known_source_refs",[])
    if not isinstance(known,list) or any(not isinstance(x,str) or not x.strip() for x in known):
        return {"pass":False,"detected":["INVALID_KNOWN_SOURCE_REFS"]}
    return {
        "pass":True,
        "schema":"TAKY_IDEA_EXPLORATION_ROUTE_V1",
        "intent":idea,
        "locked_constraints":record.get("locked_constraints",[]),
        "source_review_authority":REVIEW_STANDARD,
        "discovery_lanes":[
            {"lane":lane,"targets":DISCOVERY_LANES[lane],"state":"RESEARCH_NOT_EXECUTED"}
            for lane in required
        ],
        "known_source_refs":known,
        "required_case_analysis_fields":list(ANALYSIS_FIELDS),
        "method_candidates":[{"method":m,"evaluation":"NOT_YET_COMPARED"} for m in METHODS],
        "method_compare_dimensions":[
            "result_quality","input_fidelity","accuracy","reproducibility",
            "reuse_of_existing_work","cost_and_permissions","editability",
            "maintainability","integration_and_regression","observable_user_value"
        ],
        "selection_rule":"Compare methods using source-backed outcomes and project constraints; no automatic winner.",
        "execution_sequence":[
            "REUSE_AND_CURRENT_REBIND",
            "PARALLEL_BREADTH_DISCOVERY",
            "SOURCE_ORIGINAL_CAPTURE_AND_INDEPENDENT_REVIEW",
            "FUNCTION_LEVEL_CASE_DECOMPOSITION",
            "ALTERNATIVE_METHOD_AND_FAILURE_COMPARISON",
            "CHOOSE_TESTABLE_IMPLEMENTATION_SLICE",
            "EXECUTE_WITH_EXISTING_ASSETS",
            "COMPARE_ACTUAL_RESULT_TO_SOURCES_AND_INTENT",
            "IMPROVE_OR_CHANGE_METHOD_AND_RETEST"
        ],
        "no_arbitrary_case_limit":True,
        "needs_source_execution":True,
        "source_analysis_is_separate_from_taky_application":True,
        "paid_api_push_merge_deploy_requires_approval":True,
        "status":"EXPLORATION_PLANNED_NOT_EXECUTED"
    }


def compare_cases(record:dict)->dict:
    cases=record.get("cases")
    if not isinstance(cases,list) or not cases:
        return {"pass":False,"detected":["CASES_REQUIRED"]}
    rows=[]
    seen=set()
    for i,c in enumerate(cases):
        if not isinstance(c,dict):
            return {"pass":False,"detected":[f"CASE_NOT_OBJECT:{i}"]}
        source=str(c.get("source_ref") or "").strip()
        if not source:
            return {"pass":False,"detected":[f"CASE_SOURCE_REF_REQUIRED:{i}"]}
        if source in seen:
            return {"pass":False,"detected":[f"DUPLICATE_SOURCE_REF:{source}"]}
        seen.add(source)
        lane=str(c.get("lane") or "").strip()
        if lane and lane not in DISCOVERY_LANES:
            return {"pass":False,"detected":[f"INVALID_CASE_LANE:{source}"]}
        gaps=[k for k in ANALYSIS_FIELDS if not c.get(k)]
        rows.append({
            "source_ref":source,
            "lane":lane or "UNCLASSIFIED",
            "analysis":{k:c.get(k) for k in ANALYSIS_FIELDS if k!="source_ref"},
            "implementation_trace":{
                "inputs":c.get("inputs"),
                "processing_logic":c.get("processing_logic"),
                "algorithm_or_code":c.get("algorithm_or_code"),
                "dependencies":c.get("dependencies"),
                "outputs":c.get("outputs"),
                "reproduction_steps":c.get("reproduction_steps"),
                "failure_modes":c.get("failure_modes"),
            },
            "missing_analysis_fields":gaps,
            "code_or_runtime_evidence_declared":bool(c.get("verification_evidence")),
            "evidence_type":"CLAIMED_REFERENCE_NOT_INDEPENDENTLY_VALIDATED",
            "review_state":"NEEDS_SOURCE_OR_DEPTH" if gaps else "READY_FOR_INDEPENDENT_REVIEW",
        })
    requested=record.get("required_lanes",[])
    if not isinstance(requested,list) or any(x not in DISCOVERY_LANES for x in requested):
        return {"pass":False,"detected":["INVALID_REQUIRED_DISCOVERY_LANE"]}
    present={r["lane"] for r in rows}
    missing=[lane for lane in dict.fromkeys(requested) if lane not in present]
    unresolved=[r["source_ref"] for r in rows if r["missing_analysis_fields"]]
    return {
        "pass":True,
        "schema":"TAKY_CASE_COMPARISON_COVERAGE_V1",
        "cases":rows,
        "uncovered_requested_lanes":missing,
        "depth_gaps":unresolved,
        "independent_analysis_status":"NOT_PROVEN_BY_METADATA",
        "cross_model_comparison_status":"NOT_EXECUTED",
        "implementation_quality_status":"NOT_TESTED",
        "candidate_method_status":"NOT_SELECTED",
        "review_standard":REVIEW_STANDARD,
        "next_action":(
            "ACQUIRE_MISSING_SOURCES_AND_DECOMPOSE" if missing or unresolved
            else "INDEPENDENT_ORIGINAL_REVIEW_THEN_METHOD_COMPARISON"
        ),
        "status":"EVIDENCE_REVIEW_OPEN"
    }


def route(record: dict) -> dict:
    kind=str(record.get("kind","")).upper()
    if kind=="PIPELINE":
        stage=str(record.get("stage","")).upper()
        if stage not in PIPELINE:
            return {"pass":False,"detected":["INVALID_PIPELINE_STAGE"]}
        i=PIPELINE.index(stage)
        return {"pass":True,"route":{"stage":stage,"next_stage":PIPELINE[i+1] if i+1<len(PIPELINE) else None}}
    if kind=="IDEA":
        for k in ("idea","novelty","usefulness","cost","evidence_state"):
            if k not in record or record.get(k) in ("",None):
                return {"pass":False,"detected":[f"MISSING:{k}"]}
        if str(record["evidence_state"]).upper() not in EVIDENCE:
            return {"pass":False,"detected":["INVALID_EVIDENCE_STATE"]}
        exploration=explore_idea(record)
        if not exploration["pass"]:
            return exploration
        return {
            "pass":True,
            "route":{
                "destination":"_LAB",
                "canonical":False,
                "idea":record["idea"],
                "novelty":record["novelty"],
                "usefulness":record["usefulness"],
                "cost":record["cost"],
                "evidence_state":str(record["evidence_state"]).upper(),
                "exploration":exploration,
            }
        }
    if kind=="IDEA_EXPLORE":
        return explore_idea(record)
    if kind=="CASE_COMPARE":
        return compare_cases(record)
    if kind=="VISUALIZATION":
        relation=str(record.get("relation_type","")).strip().lower()
        return {"pass":True,"route":{"visualization":VIS.get(relation,"TEXT"),"relation_type":relation or "unspecified"}}
    return {"pass":False,"detected":["UNKNOWN_ROUTE_KIND"]}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("record",type=Path)
    a=ap.parse_args()
    rec=json.loads(a.record.read_text(encoding="utf-8"))
    out=route(rec)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
