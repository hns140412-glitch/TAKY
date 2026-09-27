'use strict';
const assert=require('node:assert/strict');
const Review=require('./observation-review-intent.js');
const Runtime=require('./learning-engine-runtime.js');
const scope={member_id:'CHILD_A',subject:'english',
 concept_skill_target:'vocabulary'};
const base={event_id:'e1',observed_at:'2026-09-27T01:00:00Z',
 ...scope,evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',source_app:'ready-set',
 instrument_version:'HIDE_SPECIALIST_RESULT_V1',verified_outcome:null,
 raw_app_signals:{forwarded_hide_observation:true},
 memory:{average_strength:41,next_review_semantics:'ADVISORY_SIGNAL_NOT_DATE',
 review_advisories:[{lexicalId:'word-a',advisoryOnly:true,
  evidenceBasis:'HIDE_MEMORY_EVIDENCE',nextReviewPriority:80,
  needsUnassistedRecall:true}]}};
const prepared=Review.prepare([base],scope);
assert.equal(prepared.ok,true);
assert.equal(prepared.actionable,true);
assert.equal(prepared.evidence[0].verified_outcome,null);
assert.equal(prepared.evidence[0].verified_performance,false);
assert.equal(prepared.evidence[0].memory.average_strength,41);
assert.match(prepared.basis_digest_sha256,/^[a-f0-9]{64}$/);
assert.deepEqual(Review.prepare([base,base],{...scope,member_id:'CHILD_B'}).evidence,[]);
for(const invalid of [
 {...base,verified_outcome:1},
 {...base,raw_app_signals:{forwarded_hide_observation:false}},
 {...base,memory:{...base.memory,review_advisories:[
  {lexicalId:'word-a',advisoryOnly:false,evidenceBasis:'HIDE_MEMORY_EVIDENCE',nextReviewPriority:80}]}},
 {...base,memory:{...base.memory,next_review_semantics:'SCHEDULE_DATE'}},
 {...base,source_app:'snap-pop'}
])assert.equal(Review.prepare([invalid],scope).actionable,false);
const derived=Runtime.derive({scope,evidence:[],observation_only:[base]});
assert.equal(derived.ok,true,JSON.stringify(derived));
assert.equal(Runtime.validate(derived).ok,true);
assert.equal(derived.learner_state.model.mastery_estimate,null);
assert.equal(derived.learner_state.observed.verified_performance_count,0);
assert.equal(derived.decision.authority,'LEARNING_DECISION_INTENT_ONLY');
assert.equal(derived.decision.execution_status,'PEDAGOGICAL_ACTION_AVAILABLE');
assert.equal(derived.decision.adaptive_plan.add_retrieval_checkpoint,true);
assert(derived.decision.pedagogical_actions.some(x=>
 x.intent==='RETRIEVAL_CHECKPOINT'&&x.basis.includes('HIDE_MEMORY_ADVISORY_ONLY')));
assert.equal(derived.trace.observation_review_digest_sha256,prepared.basis_digest_sha256);
const empty=Runtime.derive({scope,evidence:[],observation_only:[]});
assert.equal(empty.ok,true);
assert.equal(empty.decision.execution_status,'HOLD_FOR_MORE_RELIABLE_INTERPRETATION');
console.log('OBSERVATION_REVIEW_INTENT_PASS: durable child-scoped Hide signals influence central checkpoint only; zero verified mastery/receipt and no date');
