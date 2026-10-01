'use strict';
const assert=require('assert');
const C=require('./imagination-cloud-evidence-contract.js');
const Canonical=require('../adapters/canonical-evidence.js');

const made=C.create({
 event_id:'cloud-1',observed_at:'2026-10-02T08:30:00+09:00',
 member_id:'A',session_id:'S1',task_id:'T1',lap_id:'L1',
 subject:'english',concept_skill_target:'vocabulary',learning_target_id:'accept',
 invocation_reason:'CONCEPT_NOT_CLEAR',target_concept:'accept in context',
 visualization_used:'CONTEXT_SCENE',explanation_used:'EASY_ENGLISH',
 response_before:{state:'UNSURE'},response_after:{state:'PARTIAL_UNDERSTANDING'},
 additional_help_needed:true,curiosity_only:false,
 curriculum_refs:['CURR:ENG5:1'],lexical_refs:['OEWN:accept']
});
assert.equal(made.ok,true);
assert.equal(made.authority,'IMAGINATION_CLOUD_SUPPORT_OBSERVATION_ONLY');
const evidence=Canonical.normalize(made.event);
assert.equal(evidence.source_app,'imagination-cloud');
assert.equal(evidence.identity.session_id,'S1');
assert.equal(evidence.identity.task_id,'T1');
assert.deepEqual(evidence.references.curriculum_refs,['CURR:ENG5:1']);
assert.deepEqual(evidence.references.lexical_refs,['OEWN:accept']);
assert.equal(evidence.support_observation.curiosity_only,false);
assert.equal(evidence.support_observation.additional_help_needed,true);
assert.equal(evidence.support_observation.learner_state_authority,false);
assert.equal(evidence.support_observation.schedule_authority,false);
assert.equal(Canonical.validateCanonical(evidence).ok,true);

console.log('imagination-cloud-evidence-contract.test.js PASS');
