'use strict';
const assert=require('assert');
const Profile=require('./language-growth-profile.js');
const Policy=require('./growth-next-step-policy.js');

const profile=Profile.derive({
 learner_context:{grade:5},
 evidence:[
  {event_id:'1',observed_at:'2026-10-01T00:00:00Z',source_app:'hide-seek',
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
 semantic_items:[{
  source_ref:'official:2022-eng-g5',
  source_family:'OFFICIAL_CURRICULUM',
  authority_class:'OFFICIAL',
  semantic_groups:{
   language_growth:{
    easy_english_definition:['accept = to say yes to something'],
    expression_chunks:['I agree with ...','It means ...'],
    natural_collocations:['accept an idea'],
    grammar_patterns:['It means + noun/clause'],
    thinking_moves:['EXPLAIN','COMPARE'],
    question_stems:['Why do you think ...?'],
    production_targets:['USE_WORD_IN_OWN_SENTENCE'],
    english_thinking_support:['picture -> meaning -> chunk -> sentence']
   }
  }
 }]
};
const p=Policy.derive({growth_profile:profile,learning_index:learningIndex});
assert.equal(p.ok,true);
assert.equal(p.curriculum_grounding.verified,true);
assert.equal(p.language_load,'SIMPLE');
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
