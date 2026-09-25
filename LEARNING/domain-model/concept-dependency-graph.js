'use strict';

const VERSION='TAKY_CONCEPT_DEPENDENCY_GRAPH_V1';
const clean=v=>String(v??'').trim();

function validateRelation(r={}){
  const issues=[];
  for(const k of ['relation_id','subject','from_concept','to_concept','relation_type','source_ref']){
    if(!clean(r[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(!['PREREQUISITE','SUPPORTS','CONFUSABLE_WITH'].includes(clean(r.relation_type)))issues.push('RELATION_TYPE_INVALID');
  if(clean(r.from_concept)===clean(r.to_concept))issues.push('SELF_RELATION_FORBIDDEN');
  if(r.inferred_from_learner_data===true)issues.push('LEARNER_DATA_AUTO_INFERENCE_FORBIDDEN');
  return {ok:issues.length===0,issues};
}

function build(relations=[]){
  const accepted=[],rejected=[],ids=new Set();
  for(const r of Array.isArray(relations)?relations:[]){
    const v=validateRelation(r);
    if(!v.ok){rejected.push({relation_id:r?.relation_id||null,issues:v.issues});continue;}
    if(ids.has(r.relation_id)){rejected.push({relation_id:r.relation_id,issues:['DUPLICATE_RELATION_ID']});continue;}
    ids.add(r.relation_id);
    accepted.push({
      relation_id:clean(r.relation_id),
      subject:clean(r.subject).toLowerCase(),
      from_concept:clean(r.from_concept).toLowerCase(),
      to_concept:clean(r.to_concept).toLowerCase(),
      relation_type:clean(r.relation_type),
      source_ref:clean(r.source_ref),
      source_version:clean(r.source_version)||null,
      authority:clean(r.authority)||'DECLARED_DOMAIN_RELATION',
      inferred_from_learner_data:false
    });
  }
  return {
    ok:true,
    graph_version:VERSION,
    relations:accepted,
    rejected,
    authority:'DECLARED_RELATIONS_ONLY'
  };
}

function prerequisitesFor(graph={},subject='',concept=''){
  const s=clean(subject).toLowerCase(),c=clean(concept).toLowerCase();
  return (graph.relations||[]).filter(r=>r.subject===s&&r.to_concept===c&&r.relation_type==='PREREQUISITE');
}

function deriveReadiness(graph={},skillStates=[],subject='',concept=''){
  const prereqs=prerequisitesFor(graph,subject,concept);
  const byConcept=new Map((Array.isArray(skillStates)?skillStates:[]).map(s=>[clean(s?.scope?.concept_skill_target).toLowerCase(),s]));
  const missing=[],atRisk=[],ready=[];
  for(const r of prereqs){
    const state=byConcept.get(r.from_concept);
    if(!state){missing.push(r.from_concept);continue;}
    const suff=state?.inferred?.evidence_sufficiency||'NONE';
    const retention=state?.inferred?.retention_signal||'MODEL_NOT_BOUND';
    const trend=state?.inferred?.trend||'INSUFFICIENT_EVIDENCE';
    if(['NONE','SPARSE'].includes(suff)||retention==='RETENTION_AT_RISK'||trend==='DECLINING'){
      atRisk.push({concept:r.from_concept,evidence_sufficiency:suff,retention_signal:retention,trend});
    }else ready.push(r.from_concept);
  }
  return {
    ok:true,
    graph_version:graph.graph_version||VERSION,
    subject:clean(subject).toLowerCase(),
    concept_skill_target:clean(concept).toLowerCase(),
    prerequisite_count:prereqs.length,
    readiness:prereqs.length===0?'NO_DECLARED_PREREQUISITE'
      :(missing.length||atRisk.length)?'PREREQUISITE_RISK':'READY_SIGNAL',
    missing_prerequisites:missing,
    at_risk_prerequisites:atRisk,
    ready_prerequisites:ready,
    authority:'PEDAGOGICAL_READINESS_SIGNAL_ONLY',
    scheduling_authority:false,
    cannot_influence:['SCHEDULE_DATE','PLANNER_DATE','DUE_AT','DEADLINE']
  };
}

function validateReadiness(r={}){
  const issues=[];
  if(r.scheduling_authority!==false)issues.push('SCHEDULING_AUTHORITY_FORBIDDEN');
  if(r.authority!=='PEDAGOGICAL_READINESS_SIGNAL_ONLY')issues.push('AUTHORITY_INVALID');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,validateRelation,build,prerequisitesFor,deriveReadiness,validateReadiness});
