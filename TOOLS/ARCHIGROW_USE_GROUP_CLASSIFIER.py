#!/usr/bin/env python3
"""ARCHIGROW use-group routing candidates. Statutory classification must be evidence-confirmed."""
import json,re
# Order = rank 1..9 of Building Act Art.19(4) / Enforcement Decree Art.14(5) (smaller number = higher group).
GROUPS={
"자동차 관련 시설군":["자동차 관련 시설"],
"산업 등의 시설군":["운수시설","창고시설","공장","위험물 저장 및 처리 시설","자원순환 관련 시설","묘지 관련 시설","장례시설"],
"전기통신시설군":["방송통신시설","발전시설"],
"문화집회시설군":["문화 및 집회시설","종교시설","위락시설","관광 휴게시설"],
"영업시설군":["판매시설","운동시설","숙박시설","다중생활시설"],
"교육 및 복지시설군":["의료시설","교육연구시설","노유자시설","수련시설","야영장 시설"],
"근린생활시설군":["제1종 근린생활시설","제2종 근린생활시설"],
"주거업무시설군":["단독주택","공동주택","업무시설","교정시설","국방ㆍ군사시설"],
"그 밖의 시설군":["동물 및 식물 관련 시설"]
}
RANK={g:i+1 for i,g in enumerate(GROUPS)}
SOURCE_BASIS={"law":"건축법 제19조제4항 / 건축법 시행령 제14조제5항","index_source":"easylaw.go.kr 생활법령정보 '용도변경이란?' (retrieved 2026-10-12)",
              "status":"REVIEW_INDEX_ONLY","note":"Verify against the effective law.go.kr text and Annex 1 for the target project date before use."}
# The map is a review index, not a definitive full list of Annex 1 or Article 14.
def norm(s):return re.sub(r"\s+","",re.sub(r"[·ㆍ•・]","ㆍ",str(s or "")))
LOOKUP={norm(label):g for g,labels in GROUPS.items() for label in labels}
def resolve(label,sub_use=""):
    """Return (group, flags). 다중생활시설 is the 제2종 근린생활시설 sub-use that belongs to 영업시설군."""
    key=norm(label);flags=[]
    if key==norm("제2종 근린생활시설"):
        if norm(sub_use)==norm("다중생활시설"):return "영업시설군",flags
        if not sub_use:flags.append("CONFIRM_NOT_다중생활시설")
    return LOOKUP.get(key),flags
def classify(project_id,uses,source_ref="",effective_date=""):
    if not str(project_id).strip():raise ValueError("PROJECT_ID_REQUIRED")
    rows=[];issues=[]
    for use in uses:
        label=str(use.get("use") or "").strip()
        group,flags=resolve(label,use.get("sub_use",""))
        if not label or not group:
            issues.append({"use":label,"issue":"UNRESOLVED_OR_AMBIGUOUS_USE"});continue
        rows.append({"space_id":use.get("space_id"),"use":label,"sub_use":use.get("sub_use") or None,"candidate_group":group,"group_rank":RANK[group],"flags":flags,"classification_status":"REVIEW_REQUIRED","area_m2":use.get("area_m2")})
    if not source_ref or not effective_date:issues.append({"issue":"OFFICIAL_SOURCE_AND_EFFECTIVE_DATE_REQUIRED"})
    return {"schema":"ARCHIGROW_USE_GROUP_CANDIDATE_V1","project_id":project_id,"uses":rows,"issues":issues,"status":"HOLD" if issues else "CANDIDATE_REVIEW_REQUIRED","source_basis":SOURCE_BASIS,"legal_change_of_use_approval":"NOT_ASSESSED","notes":"Check Building Act Enforcement Decree Article 14 and Annex 1 against the applicable effective text, exceptions, local rules, and mixed-use area facts."}
def change_direction(from_use,to_use,from_sub_use="",to_sub_use=""):
    """Direction candidate only. Same-group -> building-register change (Act Art.19(3), Decree Art.14(4)) is index-verified;
    the permit (to higher group) / report (to lower group) mapping of Act Art.19(2) is NOT verified in this tool's source basis."""
    a,fa=resolve(from_use,from_sub_use);b,fb=resolve(to_use,to_sub_use)
    if not a or not b:return {"status":"HOLD","issue":"UNRESOLVED_OR_AMBIGUOUS_USE","from_group":a,"to_group":b}
    ra,rb=RANK[a],RANK[b]
    if ra==rb:direction,procedure,verified="SAME_GROUP","BUILDING_REGISTER_CHANGE_CANDIDATE","INDEX_VERIFIED"
    elif rb<ra:direction,procedure,verified="TO_HIGHER_GROUP","PERMIT_CANDIDATE","UNVERIFIED_ART_19_2"
    else:direction,procedure,verified="TO_LOWER_GROUP","REPORT_CANDIDATE","UNVERIFIED_ART_19_2"
    return {"status":"CANDIDATE_REVIEW_REQUIRED","from_group":a,"from_rank":ra,"to_group":b,"to_rank":rb,"direction":direction,"procedure_candidate":procedure,"procedure_source_status":verified,
            "flags":fa+fb,"exemptions_not_assessed":["same Annex 1 category","제1종<->제2종 근린생활시설 within land-use limits (Decree Art.14(4))"],"source_basis":SOURCE_BASIS}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("output");a=p.parse_args()
    d=json.load(open(a.input,encoding="utf-8"))
    result=classify(d["project_id"],d.get("uses",[]),d.get("source_ref",""),d.get("effective_date",""))
    if d.get("change"):c=d["change"];result["change_of_use"]=change_direction(c.get("from_use"),c.get("to_use"),c.get("from_sub_use",""),c.get("to_sub_use",""))
    with open(a.output,"w",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
