'use strict';
const fs=require('node:fs');
const path=require('node:path');
const PROFILE=JSON.parse(fs.readFileSync(path.join(__dirname,'..','DOMAIN','LEARNING_GROW_COVERAGE_PROFILE.json'),'utf8'));
const clean=v=>String(v??'').trim().toLowerCase();
function subjectId(v){
  const x=clean(v);
  for(const s of PROFILE.subjects)if(s.aliases.map(clean).includes(x))return s.subject_id;
  return null;
}
function audit(rows=[],options={}){
  const minVerified=Math.max(1,Number(options.min_verified_outcomes_per_subject||PROFILE.minimum_verified_outcomes_per_subject)||1);
  const minStages=Math.max(1,Number(options.min_distinct_stages_per_subject||PROFILE.minimum_distinct_stages_per_subject)||1);
  const allowSynthetic=options.allow_synthetic===true;
  const by={};
  for(const s of PROFILE.subjects)by[s.subject_id]={verified:0,real_verified:0,stages:new Set(),sources:new Set(),rows:0};
  for(const row of rows||[]){
    if(!row||typeof row!=='object')continue;
    const sid=subjectId(row.subject); if(!sid)continue;
    const verified=Math.max(0,Number(row.verified_outcomes||row.verified_outcome_count||0)||0);
    const kind=clean(row.source_kind||row.evidence_kind||'unknown');
    const stage=String(row.learner_stage||'').trim().toUpperCase();
    const isSynthetic=kind.includes('synthetic')||kind.includes('fixture')||row.synthetic===true;
    const b=by[sid]; b.rows++; b.verified+=verified; if(!isSynthetic)b.real_verified+=verified;
    if(stage)b.stages.add(stage); if(kind)b.sources.add(kind);
  }
  const subject_coverage=[]; const gaps=[];
  for(const s of PROFILE.subjects){
    const b=by[s.subject_id];
    const counted=allowSynthetic?b.verified:b.real_verified;
    const stages=[...b.stages].sort();
    const pass=counted>=minVerified&&stages.length>=minStages;
    const reasons=[];
    if(counted<minVerified)reasons.push('VERIFIED_OUTCOMES_BELOW_MIN');
    if(stages.length<minStages)reasons.push('LEARNER_STAGE_COVERAGE_BELOW_MIN');
    subject_coverage.push({subject_id:s.subject_id,verified_outcomes:b.verified,real_verified_outcomes:b.real_verified,learner_stages:stages,source_kinds:[...b.sources].sort(),pass,reasons});
    if(!pass)gaps.push({subject_id:s.subject_id,reasons});
  }
  const stageCoverage={};
  for(const stage of PROFILE.learner_stages)stageCoverage[stage]=subject_coverage.filter(x=>x.learner_stages.includes(stage)).map(x=>x.subject_id);
  return {
    ok:true,
    complete:gaps.length===0,
    synthetic_allowed:allowSynthetic,
    minimum_verified_outcomes_per_subject:minVerified,
    minimum_distinct_stages_per_subject:minStages,
    subject_coverage,
    stage_coverage:stageCoverage,
    gaps,
    authority_transfer:false,
    rule:'COVERAGE AUDIT REPORTS EVIDENCE BREADTH ONLY; IT DOES NOT CREATE SUBJECT MASTERY OR CURRICULUM AUTHORITY'
  };
}
function validate(result={}){
  const issues=[];
  if(result.ok!==true)issues.push('RESULT_NOT_OK');
  if(result.authority_transfer!==false)issues.push('AUTHORITY_TRANSFER_FORBIDDEN');
  for(const s of result.subject_coverage||[]){
    if(!PROFILE.subjects.some(x=>x.subject_id===s.subject_id))issues.push('UNKNOWN_SUBJECT:'+s.subject_id);
    if((s.real_verified_outcomes||0)>(s.verified_outcomes||0))issues.push('REAL_VERIFIED_EXCEEDS_TOTAL:'+s.subject_id);
  }
  return {ok:issues.length===0,issues};
}
module.exports=Object.freeze({PROFILE,subjectId,audit,validate});
