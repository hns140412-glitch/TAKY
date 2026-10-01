'use strict';
const assert=require('assert');
const Profile=require('./language-growth-profile.js');
const Policy=require('./growth-next-step-policy.js');

const profile=Profile.derive({
 learner_context:{grade:5},
 evidence:[
  {event_id:'1',observed_at:'2026-10-01T00:00:00Z',source_app:'hide-seek',verified_outcome:1,verification:{authority:'LEARNING_VERIFICATION_RECEIPT'},
   language_growth_signals:[
    {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false},
    {dimension:'GRAMMAR',outcome:'PARTIAL',assisted:true},
    {dimension:'EXPRESSION',outcome:'PARTIAL',assisted:true},
    {dimension:'THINKING',outcome:'SUCCESS',depth:3},
    {dimension:'ENGLISH_THINKING',outcome:'PARTIAL',direct_english:false}
   ]},
  {event_id:'2',observed_at:'2026-10-02T00:00:00Z',source_app:'snap-pop',
   language_growth_signals:[
    {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true},
    {dimension:'THINKING',outcome:'SUCCESS',depth:4,transfer:true}
   ]}
 ]
});
const learningIndex={
 semantic_items:[
  {
   source_ref:'official:2022-eng-g5',
   source_family:'OFFICIAL_CURRICULUM',
   authority_class:'OFFICIAL',
   learning_evidence_role:'CURRICULUM_ALIGNMENT',
   semantic_groups:{
    language_growth:{
     thinking_moves:['EXPLAIN','COMPARE'],
     question_stems:['Why do you think ...?'],
     production_targets:['USE_WORD_IN_OWN_SENTENCE']
    }
   }
  },
  {
   source_ref:'dict:accept',
   source_family:'LEXICAL_DICTIONARY',
   authority_class:'REFERENCE',
   learning_evidence_role:'LEXICAL_SEMANTICS',
   semantic_groups:{
    language_growth:{
     easy_english_definition:['accept = to say yes to something']
    }
   }
  },
  {
   source_ref:'corpus:accept',
   source_family:'LANGUAGE_CORPUS',
   authority_class:'REFERENCE',
   learning_evidence_role:'LANGUAGE_USAGE',
   semantic_groups:{
    language_growth:{
     expression_chunks:['I agree with ...','It means ...'],
     natural_collocations:['accept an idea'],
     grammar_patterns:['It means + noun/clause']
    }
   }
  },
  {
   source_ref:'pedagogy:english-thinking',
   source_family:'PEDAGOGICAL_LEARNING_RESOURCE',
   authority_class:'CURATED',
   learning_evidence_role:'PEDAGOGICAL_USAGE',
   semantic_groups:{
    language_growth:{
     english_thinking_support:['picture -> meaning -> chunk -> sentence']
    }
   }
  }
 ]
};
const p=Policy.derive({growth_profile:profile,learning_index:learningIndex});
assert.equal(p.ok,true);
assert.equal(p.curriculum_grounding.verified,true);
assert.deepEqual(p.curriculum_grounding.source_refs,['official:2022-eng-g5']);
assert.ok(p.language_support.easy_english_definitions.includes('accept = to say yes to something'));
assert.ok(p.language_support.expression_chunks.includes('I agree with ...'));
assert.ok(p.language_support.natural_collocations.includes('accept an idea'));
assert.equal(p.language_resource_provenance.easy_english_definitions[0].source_role,'LEXICAL_SEMANTICS');
assert.equal(p.language_resource_provenance.expression_chunks[0].source_role,'LANGUAGE_USAGE');
assert.equal(p.source_role_guard.curriculum_alignment_does_not_certify_lexical_semantics,true);
assert.equal(p.language_load,'SIMPLE');
assert.ok(['MEDIUM','HIGH'].includes(p.growth_control.evidence_confidence));
assert.ok(['BUILD_CONNECT','STRETCH_TRANSFER'].includes(p.growth_control.learning_intensity));
assert.ok(/^L[1-5]_/.test(p.growth_control.expression_level));
assert.equal(p.growth_control.stability_guard.low_confidence_cannot_upshift_to_transfer,true);
assert.ok(['ELICIT_PULL','TRANSFER_PUSH'].includes(p.support_phase));
assert.ok(p.question_depth.level>=3);
assert.equal(p.hide_to_snap_handoff.child_authorship_required,true);
assert.equal(p.hide_to_snap_handoff.final_answer_generation_forbidden,true);
assert.equal(p.reference_gap_candidate,null);
assert.equal(Policy.validate(p).ok,true);




const sameTargetEvidence=[];
for(let i=1;i<=3;i++){
 sameTargetEvidence.push({
  event_id:'same-'+i,observed_at:'2026-10-0'+i+'T00:00:00Z',
  source_app:i===1?'hide-seek':'snap-pop',
  verified_outcome:i===1?1:null,
  ...(i===1?{verification:{authority:'LEARNING_VERIFICATION_RECEIPT'}}:{}),
  growth_execution_context:{
   expression_level:'L3_EXPANDED_SENTENCE',question_depth:4,hint_strength:'MINIMAL_CUE'
  },
  language_growth_signals:[
   {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true,target_id:'accept'},
   {dimension:'THINKING',outcome:'SUCCESS',assisted:false,transfer:true,depth:4,target_id:'accept'}
  ]
 });
}
const sameTargetProfile=Profile.derive({learner_context:{grade:5},evidence:sameTargetEvidence});
assert.equal(sameTargetProfile.dimensions.VOCABULARY.state,'READY_TO_STRETCH');
assert.equal(sameTargetProfile.dimensions.THINKING.state,'READY_TO_STRETCH');
assert.equal(sameTargetProfile.dimensions.VOCABULARY.generalization_ready,false);
assert.equal(sameTargetProfile.dimensions.THINKING.generalization_ready,false);
const sameTargetPolicy=Policy.derive({growth_profile:sameTargetProfile,learning_index:learningIndex});
assert.notEqual(sameTargetPolicy.support_phase,'TRANSFER_PUSH');
assert.notEqual(sameTargetPolicy.growth_control.learning_intensity,'STRETCH_TRANSFER');
assert.equal(
 sameTargetPolicy.growth_control.generalization_guard
  .target_scoped_stretch_does_not_become_global_transfer_push,
 true
);

const multiTargetEvidence=[];
for(const [i,target] of [['1','accept'],['2','except'],['3','allow'],['4','receive']]){
 multiTargetEvidence.push({
  event_id:'multi-'+i,observed_at:'2026-10-0'+i+'T00:00:00Z',
  source_app:i==='1'?'hide-seek':'snap-pop',
  verified_outcome:i==='1'?1:null,
  ...(i==='1'?{verification:{authority:'LEARNING_VERIFICATION_RECEIPT'}}:{}),
  growth_execution_context:{
   expression_level:'L3_EXPANDED_SENTENCE',question_depth:4,hint_strength:'MINIMAL_CUE'
  },
  language_growth_signals:[
   {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true,target_id:target},
   {dimension:'THINKING',outcome:'SUCCESS',assisted:false,transfer:true,depth:4,target_id:target}
  ]
 });
}
const multiTargetProfile=Profile.derive({learner_context:{grade:5},evidence:multiTargetEvidence});
assert.equal(multiTargetProfile.dimensions.VOCABULARY.generalization_ready,true);
assert.equal(multiTargetProfile.dimensions.THINKING.generalization_ready,true);
const multiTargetPolicy=Policy.derive({growth_profile:multiTargetProfile,learning_index:learningIndex});
assert.equal(multiTargetPolicy.support_phase,'TRANSFER_PUSH');
assert.equal(multiTargetPolicy.growth_control.learning_intensity,'STRETCH_TRANSFER');

const curriculumCannotMasqueradeAsDictionary=Policy.growthResources({
 semantic_items:[{
  source_ref:'official:curriculum-only',
  source_family:'OFFICIAL_CURRICULUM',
  authority_class:'OFFICIAL',
  learning_evidence_role:'CURRICULUM_ALIGNMENT',
  semantic_groups:{language_growth:{
   easy_english_definition:['this must not be consumed as lexical authority'],
   expression_chunks:['this must not be consumed as usage authority'],
   natural_collocations:['accept an idea'],
   thinking_moves:['EXPLAIN']
  }}
 }]
});
assert.equal(curriculumCannotMasqueradeAsDictionary.curriculum_verified,true);
assert.deepEqual(curriculumCannotMasqueradeAsDictionary.easy_english_definitions,[]);
assert.deepEqual(curriculumCannotMasqueradeAsDictionary.expression_chunks,[]);
assert.deepEqual(curriculumCannotMasqueradeAsDictionary.natural_collocations,[]);
assert.deepEqual(curriculumCannotMasqueradeAsDictionary.thinking_moves,['EXPLAIN']);
assert.equal(
 curriculumCannotMasqueradeAsDictionary.source_role_guard
  .curriculum_content_cannot_supply_lexical_or_usage_authority_by_presence_alone,
 true
);

const noIndex=Policy.derive({growth_profile:profile,learning_index:{semantic_items:[]}});
assert.equal(noIndex.curriculum_grounding.verified,false);
assert.equal(noIndex.reference_gap_candidate.mining_request_authorized,false);
assert(noIndex.reference_gap_candidates.length>=2);
assert(noIndex.reference_gap_candidates.every(x=>x.mining_request_authorized===false));
assert(noIndex.reference_gap_candidates.every(x=>
 x.resolution_path==='INDEX_THEN_MINING_IF_INSUFFICIENT'));
assert(noIndex.reference_gap_candidates.some(x=>
 x.required_learning_evidence_role==='CURRICULUM_ALIGNMENT'));
assert(noIndex.reference_gap_candidates.some(x=>
 ['LANGUAGE_USAGE','PEDAGOGICAL_USAGE','LEXICAL_SEMANTICS']
  .includes(x.required_learning_evidence_role)));
console.log('growth-next-step-policy.test.js PASS');
