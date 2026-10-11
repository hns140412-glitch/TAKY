'use strict';

const fs=require('node:fs');
const path=require('node:path');
const Engine=require('../runtime/learning-engine-runtime.js');
const AcademicVocab=require('../pedagogy/academic-vocab-overlay.js');

const VERSION='TAKY_HIDE_PRELEARNED_TERM_PACK_BUILDER_V2';
const hideRepo=path.resolve(process.env.HIDE_REPO||'D:\\Git PWA\\Hide & Seek');
const universePath=path.resolve(process.env.TAKY_PRELEARNED_TERM_UNIVERSE||
  path.join(__dirname,'..','data','prelearned','subject-term-universe-elementary-v1.json'));
const outPath=path.join(hideRepo,'data','learning-term-recommendation-packs-v1.json');

const universe=JSON.parse(fs.readFileSync(universePath,'utf8').replace(/^\uFEFF/,''));
if(universe?.schema!=='TAKY_SUBJECT_TERM_UNIVERSE_ELEMENTARY_V1'||!Array.isArray(universe.terms))
  throw new Error('ELEMENTARY_PRELEARNED_TERM_UNIVERSE_INVALID');

const stages=['E1','E2','E3','E4','E5','E6'];
const preferredSubjectOrder=[
  'KOREAN','MATH','RIGHT_LIFE','WISE_LIFE','JOYFUL_LIFE',
  'SOCIAL','SCIENCE','ENGLISH','MORAL','ART','MUSIC','PE','PRACTICAL'
];

function subjectsFor(stage){
  const set=new Set(universe.terms.filter(t=>t.school_stages?.includes(stage)).map(t=>String(t.subject||'')).filter(Boolean));
  return [...set].sort((a,b)=>{
    const ai=preferredSubjectOrder.indexOf(a),bi=preferredSubjectOrder.indexOf(b);
    return (ai<0?999:ai)-(bi<0?999:bi)||a.localeCompare(b);
  });
}
function subjectPack(stage,subject){
  const result=Engine.deriveTermRecommendations({
    learner_profile:{school_stage:stage},
    subject,
    curriculum_terms:universe.terms,
    term_evidence:[],
    consumer_app:'HIDE_SEEK',
    limit:36,
    allow_provisional:false
  });
  if(!result.ok)throw new Error('TERM_RECOMMENDATION_FAILED:'+stage+':'+subject+':'+result.reason);
  const decorated=AcademicVocab.decorate(result.term_recommendations,result.cards,stage);
  return {
    school_stage:stage,
    subject,
    recommendation_state:result.recommendation_state,
    available_term_count:universe.terms.filter(t=>t.subject===subject&&t.school_stages?.includes(stage)).length,
    cards:decorated.cards,
    recommendations:decorated.recommendations.map(x=>({
      term_id:x.term_id,term:x.term,priority:x.priority,score:x.score,reasons:x.reasons,
      grade_alignment_tier:x.grade_alignment_tier,source_ref:x.source_ref,
      academic_vocabulary:x.academic_vocabulary
    })),
    academic_vocabulary_stage_policy:decorated.stage_policy,
    trace:result.trace
  };
}

const byStage={};
const stageSubjects={};
for(const stage of stages){
  const subjects=subjectsFor(stage);
  stageSubjects[stage]=subjects;
  byStage[stage]={};
  for(const subject of subjects)byStage[stage][subject]=subjectPack(stage,subject);
  const cards=subjects.flatMap(s=>byStage[stage][s].cards);
  const recommendations=subjects.flatMap(s=>byStage[stage][s].recommendations);
  byStage[stage].ALL={
    school_stage:stage,subject:'ALL',
    recommendation_state:cards.length?'READY':'NO_ELIGIBLE_GRADE_TERMS',
    cards,recommendations
  };
}

fs.mkdirSync(path.dirname(outPath),{recursive:true});
fs.writeFileSync(outPath,JSON.stringify({
  schema:'TAKY_HIDE_TERM_RECOMMENDATION_PACKS_V1',
  projection_version:'2026-10-07.4-all-elementary-profile',
  generated_at:new Date().toISOString(),
  generated_by:'TAKY_LEARNING_ENGINE_CORE',
  builder_version:VERSION,
  selector_version:require('../pedagogy/grade-aware-term-selector.js').VERSION,
  runtime_version:require('../runtime/term-recommendation-runtime.js').VERSION,
  source_ref:'TAKY:LEARNING:data/prelearned/subject-term-universe-elementary-v1.json',
  authority_class:'OFFICIAL_ELEMENTARY_STANDARD_GRADE_BAND+NIKL_LEXICAL_ENRICHMENT',
  source_universe:{
    schema:universe.schema,
    counts:universe.counts,
    source_provenance:universe.source_provenance,
    guards:universe.guards
  },
  stage_subjects:stageSubjects,
  by_stage:byStage
},null,2)+'\n','utf8');

console.log(JSON.stringify({
  ok:true,builder:VERSION,out_path:outPath,
  stage_subjects:stageSubjects,
  cards_by_stage:Object.fromEntries(stages.map(stage=>[stage,byStage[stage].ALL.cards.length])),
  terms_by_stage:Object.fromEntries(stages.map(stage=>[
    stage,universe.terms.filter(t=>t.school_stages?.includes(stage)).length
  ]))
},null,2));
