'use strict';

const assert=require('node:assert/strict');
const Runtime=require('./learning-engine-runtime.js');

const scope={member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'};
const evidence=[{
  event_id:'policy-runtime-1',
  observed_at:'2026-09-25T12:00:00.000Z',
  member_id:'A',
  subject:'영어',
  concept_skill_target:'VOCABULARY',
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:'hide-seek',
  instrument_version:'hide-v1',
  assisted:false,
  verified_outcome:1,
  verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-policy-runtime-1'}
}];

const denied=Runtime.derive({
  scope,
  evidence,
  evidence_policy_requests:[{
    function_id:'LE-H01',
    consumer_app:'READY_SET',
    requested_behavior:'AUTOMATIC_PREREQUISITE_ENFORCEMENT'
  }]
});
assert.equal(denied.ok,false);
assert.equal(denied.reason,'EVIDENCE_POLICY_DENIED');
assert.equal(denied.evidence_policy.denied[0].reason,'DENY_HOLD');

const allowed=Runtime.derive({
  scope,
  evidence,
  evidence_policy_requests:[{
    function_id:'LE-F01',
    consumer_app:'READY_SET',
    requested_behavior:'STANDARD_ALIGNMENT',
    provenance:['OFFICIAL_STANDARD_REF']
  }]
});
assert.equal(allowed.ok,true);
assert.equal(allowed.evidence_policy.ok,true);
assert.equal(allowed.evidence_policy.results[0].decision,'ALLOW');
assert.equal(allowed.trace.evidence_policy_ids.includes('P-F01-READY'),true);
assert.equal(Runtime.validate(allowed).ok,true);

const missingProvenance=Runtime.derive({
  scope,
  evidence,
  evidence_policy_requests:[{
    function_id:'LE-F03',
    consumer_app:'HIDE_SEEK',
    requested_behavior:'CONTEXTUAL_SENSE_SUPPORT',
    provenance:['NIKL_SOURCE_REF']
  }]
});
assert.equal(missingProvenance.ok,false);
assert.equal(missingProvenance.evidence_policy.denied[0].reason,'DENY_PROVENANCE_REQUIRED');

console.log('LEARNING_RUNTIME_POLICY_INTEGRATION_PASS');
