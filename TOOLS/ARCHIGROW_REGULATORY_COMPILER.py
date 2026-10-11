#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/"DOMAIN"/"ARCHITECTURE_REGULATORY_RULE_SCHEMA.json").read_text(encoding="utf-8"))
import importlib.util
spec=importlib.util.spec_from_file_location("sources",ROOT/"TOOLS"/"ARCHIGROW_SOURCE_REGISTRY.py")
S=importlib.util.module_from_spec(spec); spec.loader.exec_module(S)

def clean(v): return str(v or "").strip()

def _iso_date(value):
    try:
        datetime.fromisoformat(clean(value).replace("Z","+00:00"))
        return True
    except Exception:
        return False

def validate_applicability_evidence(rule):
    status=clean(rule.get("applicability_status"))
    required=set(SCHEMA.get("applicability_evidence_required_when",[]))
    if status not in required:
        return {"ok":True,"issues":[]}
    ev=rule.get("applicability_evidence")
    if not isinstance(ev,dict):
        return {"ok":False,"issues":["APPLICABILITY_EVIDENCE_REQUIRED"]}
    issues=[]
    authority=clean(ev.get("authority"))
    if authority not in set(SCHEMA.get("applicability_evidence_authorities",[])):
        issues.append("APPLICABILITY_EVIDENCE_AUTHORITY_INVALID")
    for k in ["evidence_ref","decided_at","decision","rule_id","source_id","target_project_id"]:
        if not clean(ev.get(k)): issues.append("APPLICABILITY_EVIDENCE_"+k.upper()+"_REQUIRED")
    if clean(ev.get("decision"))!=status: issues.append("APPLICABILITY_EVIDENCE_DECISION_MISMATCH")
    if clean(ev.get("rule_id"))!=clean(rule.get("rule_id")): issues.append("APPLICABILITY_EVIDENCE_RULE_MISMATCH")
    if clean(ev.get("source_id"))!=clean(rule.get("source_id")): issues.append("APPLICABILITY_EVIDENCE_SOURCE_MISMATCH")
    if clean(ev.get("target_project_id"))!=clean(rule.get("target_project_id")): issues.append("APPLICABILITY_EVIDENCE_PROJECT_MISMATCH")
    if clean(ev.get("decided_at")) and not _iso_date(ev.get("decided_at")):
        issues.append("APPLICABILITY_EVIDENCE_TIME_INVALID")
    return {"ok":not issues,"issues":issues}

def validate_rule(rule):
    issues=[]
    for k in SCHEMA["required_rule_fields"]:
        v=rule.get(k)
        if k=="design_variables":
            if not isinstance(v,list) or not [x for x in v if clean(x)]: issues.append("DESIGN_VARIABLES_REQUIRED")
        elif not clean(v): issues.append("MISSING_"+k.upper())
    if clean(rule.get("rule_class")) not in SCHEMA["rule_classes"]: issues.append("RULE_CLASS_INVALID")
    if clean(rule.get("applicability_status")) not in SCHEMA["applicability_status"]: issues.append("APPLICABILITY_STATUS_INVALID")
    source=S.source(clean(rule.get("source_id")))
    if not source: issues.append("SOURCE_NOT_REGISTERED")
    elif source.get("target_fact_eligible") is not True: issues.append("SOURCE_NOT_TARGET_FACT_ELIGIBLE")
    if clean(rule.get("rule_class"))=="OPPORTUNITY_RULE":
        if not clean(rule.get("approval_route")):
            issues.append("OPPORTUNITY_APPROVAL_ROUTE_REQUIRED")
        targets=rule.get("related_rule_ids")
        if not isinstance(targets,list) or not [clean(x) for x in targets if clean(x)]:
            issues.append("OPPORTUNITY_RELATION_TARGET_REQUIRED")
    if rule.get("feasible") is True or clean(rule.get("path_status"))=="FEASIBLE":
        issues.append("AUTOMATIC_FEASIBLE_FORBIDDEN")
    applicability=validate_applicability_evidence(rule)
    issues.extend(applicability["issues"])
    return {"ok":not issues,"issues":issues}

def compile_rules(project, rules):
    pid=clean(project.get("project_id"))
    if not pid: return {"ok":False,"reason":"TARGET_PROJECT_ID_REQUIRED","blockers":["TARGET_PROJECT_ID_REQUIRED"]}
    compiled=[]; rejected=[]
    for raw in rules or []:
        rule=json.loads(json.dumps(raw,ensure_ascii=False))
        check=validate_rule(rule)
        if not check["ok"]:
            rejected.append({"rule_id":clean(rule.get("rule_id")) or None,"issues":check["issues"]}); continue
        bound=clean(rule.get("target_project_id"))
        if bound and bound!=pid:
            rejected.append({"rule_id":rule["rule_id"],"issues":["TARGET_PROJECT_MISMATCH"]}); continue
        if rule["applicability_status"]!="APPLICABLE":
            compiled.append({**rule,"usable_as_design_constraint":False,"review_state":"HOLD_APPLICABILITY"})
            continue
        qualified=S.qualify_target_fact(
            clean(rule.get("source_id")),
            target_project_id=pid,
            evidence_ref=clean(rule.get("evidence_ref")),
            observed_as_of=clean(rule.get("source_as_of")),
            applicability_status="APPLICABLE"
        )
        if not qualified.get("ok"):
            rejected.append({"rule_id":rule["rule_id"],"issues":["SOURCE_FACT_QUALIFICATION_FAILED",*qualified.get("blockers",[])]})
            continue
        compiled.append({**rule,"target_project_id":pid,"usable_as_design_constraint":True,"review_state":"EVIDENCE_BOUND_APPLICABLE","source_fact_qualification":qualified})
    applicable=[r for r in compiled if r.get("usable_as_design_constraint")]
    opportunities=[r for r in applicable if r["rule_class"]=="OPPORTUNITY_RULE"]
    constraints=[r for r in applicable if r["rule_class"]!="OPPORTUNITY_RULE"]
    path_status="CONDITIONAL" if applicable else "UNVERIFIED"
    return {
      "ok":not rejected,
      "project_id":pid,
      "compiled_rules":compiled,
      "rejected":rejected,
      "constraint_count":len(constraints),
      "opportunity_count":len(opportunities),
      "path_status":path_status,
      "feasibility_claim_authorized":False,
      "approval_authority":"PROJECT_LEGAL_ADMINISTRATIVE_REVIEW",
      "rule":"COMPILED APPLICABILITY != LEGAL FEASIBILITY APPROVAL"
    }



def build_relation_graph(compilation):
    rows=[r for r in compilation.get("compiled_rules",[]) if r.get("usable_as_design_constraint")]
    by_id={clean(r.get("rule_id")):r for r in rows if clean(r.get("rule_id"))}
    edges=[]; issues=[]
    seen=set()
    for r in rows:
        rid=clean(r.get("rule_id"))
        rels=[]
        if r.get("rule_class")=="OPPORTUNITY_RULE":
            rels.extend(("OPPORTUNITY_RELATES_TO",clean(x)) for x in (r.get("related_rule_ids") or []) if clean(x))
        rels.extend(("CONFLICTS_WITH",clean(x)) for x in (r.get("conflicts_with") or []) if clean(x))
        rels.extend(("DEPENDS_ON",clean(x)) for x in (r.get("depends_on") or []) if clean(x))
        for relation,target in rels:
            if target not in by_id:
                issues.append(f"RELATION_TARGET_NOT_COMPILED:{rid}:{target}")
                continue
            key=(rid,relation,target)
            if key in seen: continue
            seen.add(key)
            edges.append({
              "from_rule_id":rid,"relation":relation,"to_rule_id":target,
              "authority":"EXPLICIT_EVIDENCE_BOUND_RULE_RELATION",
              "inferred":False
            })
    return {
      "ok":not issues,
      "nodes":[{"rule_id":rid,"rule_class":r["rule_class"],"design_variables":list(r.get("design_variables") or [])} for rid,r in by_id.items()],
      "edges":edges,"issues":issues,
      "feasibility_claim_authorized":False,
      "rule":"NO RELATION EDGE MAY BE INFERRED FROM SHARED VARIABLES OR OPTIMISTIC INTERPRETATION"
    }

if __name__=="__main__":
    print(json.dumps({"schema":SCHEMA["schema"],"ok":True},ensure_ascii=False))
