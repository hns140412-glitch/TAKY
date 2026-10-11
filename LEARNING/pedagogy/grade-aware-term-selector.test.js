'use strict';

const assert=require('node:assert/strict');
const Selector=require('./grade-aware-term-selector.js');
const Engine=require('../runtime/learning-engine-runtime.js');

const terms=[
  {
    id:'science-e3-evaporation',subject:'SCIENCE',term:'증발',hanja:'蒸發',reading:'증발',
    meaning:'액체가 기체로 변하는 현상',gradeBand:'3-4',
    source_ref:'CURR:SCIENCE:3-4:EVAPORATION',
    grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:3-4:EVAPORATION'},
    components:[{text:'蒸',meaning:'찌다'},{text:'發',meaning:'나오다'}],
    concept:{relations:['액체 → 기체']}
  },
  {
    id:'science-e5-front',subject:'SCIENCE',term:'한랭전선',hanja:'寒冷前線',reading:'한랭전선',
    meaning:'찬 공기가 따뜻한 공기 아래로 파고들며 만들어지는 전선',gradeBand:'5-6',
    source_ref:'CURR:SCIENCE:5-6:WEATHER_FRONT',
    grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:5-6:WEATHER_FRONT'},
    components:[{text:'寒',meaning:'차갑다'},{text:'冷',meaning:'차다'},{text:'前',meaning:'앞'},{text:'線',meaning:'선'}],
    concept:{compare:['한랭전선=찬 공기가 전진','온난전선=따뜻한 공기가 전진']},
    unit_tags:['날씨','전선']
  },
  {
    id:'science-e5-solar-system',subject:'SCIENCE',term:'태양계',hanja:'太陽系',reading:'태양계',
    meaning:'태양과 그 둘레를 도는 여러 천체로 이루어진 체계',gradeBand:'5-6',
    source_ref:'CURR:SCIENCE:5-6:SOLAR_SYSTEM',
    grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:5-6:SOLAR_SYSTEM'},
    components:[{text:'太',meaning:'크다'},{text:'陽',meaning:'태양'},{text:'系',meaning:'체계'}],
    concept:{hierarchy:['우주','은하계','태양계','지구']},
    unit_tags:['우주','태양계']
  },
  {
    id:'science-e5-unverified',subject:'SCIENCE',term:'임의용어',meaning:'검증 전 용어',gradeBand:'5-6',
    source_ref:'',
    grade_alignment:{state:'CURATED',source_ref:''}
  },
  {
    id:'social-e5-consumer',subject:'SOCIAL',term:'소비자',hanja:'消費者',meaning:'물건이나 서비스를 사용하는 사람',gradeBand:'5-6',
    source_ref:'CURR:SOCIAL:5-6:ECONOMY',
    grade_alignment:{state:'VERIFIED',source_ref:'CURR:SOCIAL:5-6:ECONOMY'}
  }
];

const evidence=[
  {learning_target_id:'science-e5-front',interaction_mode:'CORE',result_type:'WRONG',observed_at:'2026-10-07T01:00:00Z'},
  {learning_target_id:'science-e5-front',interaction_mode:'LINK',result_type:'WRONG',observed_at:'2026-10-07T01:00:30Z'},
  {learning_target_id:'science-e5-front',interaction_mode:'LINK',result_type:'HINT_USED',assisted:true,observed_at:'2026-10-07T01:01:00Z'},
  {learning_target_id:'science-e5-solar-system',interaction_mode:'RECALL',result_type:'CORRECT',observed_at:'2026-10-06T01:00:00Z'},
  {learning_target_id:'science-e5-solar-system',interaction_mode:'RECALL',result_type:'CORRECT',observed_at:'2026-10-07T01:00:00Z'}
];

const result=Engine.deriveTermRecommendations({
  learner_profile:{schoolStage:'E5'},
  subject:'SCIENCE',
  unit_context:['날씨','전선'],
  curriculum_terms:terms,
  term_evidence:evidence,
  consumer_app:'HIDE_SEEK',
  limit:12
});

assert.equal(result.ok,true);
assert.equal(result.authority,'TAKY_LEARNING_ENGINE_CORE');
assert.equal(result.learner_context.school_stage,'E5');
assert.equal(result.term_recommendations.length,2);
assert.deepEqual(result.term_recommendations.map(x=>x.term_id),['science-e5-front','science-e5-solar-system']);
assert.equal(result.term_recommendations[0].priority,'RECOVERY');
assert.ok(result.term_recommendations[0].reasons.includes('UNIT_CONTEXT_MATCH'));
assert.ok(result.term_recommendations[0].reasons.includes('RECOVERY_NEEDED'));
assert.ok(result.term_recommendations[0].reasons.includes('MINING_PATTERN_CONCEPT_GAP'));
assert.equal(result.term_recommendations[0].learning_pattern_plan.recovery.route,'TARGETED_CONCEPT_REVIEW');
assert.ok(result.cards[0].miningLearningPattern.source_refs.includes('INDEX:REF-081'));
assert.equal(result.term_recommendations[1].priority,'REINFORCE');
assert.ok(result.term_recommendations[1].reasons.includes('RECALL_STABLE_DEPRIORITIZE'));
assert.equal(result.cards.length,2);
assert.ok(result.cards[0].concept.compare.length);
assert.ok(result.cards[1].concept.hierarchy.length);
assert.ok(result.trace.source_refs.every(Boolean));
assert.ok(result.cannot_influence.includes('SCHEDULE_DATE'));
assert.equal(Object.prototype.hasOwnProperty.call(result,'schedule_date'),false);

const low=Selector.select({
  learner_profile:{schoolStage:'E3'},
  subject:'SCIENCE',
  candidate_terms:terms,
  term_evidence:[]
});
assert.equal(low.ok,true);
assert.deepEqual(low.recommendations.map(x=>x.term_id),['science-e3-evaporation']);

const missingGrade=Engine.deriveTermRecommendations({
  learner_profile:{},
  subject:'SCIENCE',
  curriculum_terms:terms
});
assert.equal(missingGrade.ok,false);
assert.equal(missingGrade.reason,'SUPPORTED_SCHOOL_STAGE_REQUIRED');

console.log('GRADE_AWARE_TERM_SELECTOR_TEST: PASS');
console.log(JSON.stringify({
  e5:selectedSummary(result),
  e3:low.recommendations.map(x=>({term:x.term,priority:x.priority,grade_band:x.grade_band}))
},null,2));

function selectedSummary(x){
  return x.term_recommendations.map(r=>({
    term:r.term,
    priority:r.priority,
    score:r.score,
    reasons:r.reasons,
    source_ref:r.source_ref
  }));
}
