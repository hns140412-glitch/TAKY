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

const noIndex=Policy.derive({growth_profile:profile,learning_index:{semantic_items:[]}});
assert.equal(noIndex.curriculum_grounding.verified,false);
assert.equal(noIndex.reference_gap_candidate.mining_request_authorized,false);
console.log('growth-next-step-policy.test.js PASS');
