'use strict';

const assert=require('assert');
const Bridge=require('./evidence-policy-bridge.js');

const allow=Bridge.evaluate({
  function_id:'LE-F01',
  consumer_app:'READY_SET',
  requested_behavior:'STANDARD_ALIGNMENT',
  provenance:['OFFICIAL_STANDARD_REF']
});
assert.equal(allow.ok,true);
assert.equal(allow.decision,'ALLOW');

const conditional=Bridge.evaluate({
  function_id:'LE-F03',
  consumer_app:'HIDE_SEEK',
  requested_behavior:'CONTEXTUAL_SENSE_SUPPORT',
  provenance:['NIKL_SOURCE_REF','EXPLICIT_CONTEXT_BINDING']
});
assert.equal(conditional.ok,true);
assert.equal(conditional.decision,'ALLOW_CONDITIONAL');

const hold=Bridge.evaluate({
  function_id:'LE-H01',
  consumer_app:'READY_SET',
  requested_behavior:'AUTOMATIC_PREREQUISITE_ENFORCEMENT'
});
assert.equal(hold.ok,false);
assert.equal(hold.reason,'DENY_HOLD');

const missingProv=Bridge.evaluate({
  function_id:'LE-F04',
  consumer_app:'READY_SET',
  requested_behavior:'INFERENCE_CONSTRUCT_REFERENCE',
  provenance:['SOURCE_SPECIFIC_REF']
});
assert.equal(missingProv.ok,false);
assert.equal(missingProv.reason,'DENY_PROVENANCE_REQUIRED');

const forbiddenClaim=Bridge.evaluate({
  function_id:'LE-F01',
  consumer_app:'READY_SET',
  requested_behavior:'STANDARD_ALIGNMENT',
  provenance:['OFFICIAL_STANDARD_REF'],
  requested_claims:['MASTERY_FROM_STANDARD_MEMBERSHIP']
});
assert.equal(forbiddenClaim.ok,false);
assert.equal(forbiddenClaim.reason,'DENY_CLAIM_BOUNDARY');

const unknown=Bridge.evaluate({
  function_id:'LE-UNKNOWN',
  consumer_app:'READY_SET',
  requested_behavior:'STANDARD_LOOKUP'
});
assert.equal(unknown.ok,false);
assert.equal(unknown.reason,'DENY_UNKNOWN_POLICY');

const batch=Bridge.evaluateBatch([
  {
    function_id:'LE-F06',
    consumer_app:'SNAP_POP',
    requested_behavior:'WRITING_PROCESS_SCAFFOLD',
    provenance:['WRITING_CORPUS_SOURCE_REF']
  },
  {
    function_id:'LE-H02',
    consumer_app:'READY_SET',
    requested_behavior:'NUMERIC_THRESHOLD_CLASSIFICATION'
  }
]);
assert.equal(batch.ok,false);
assert.equal(batch.results[0].decision,'ALLOW_CONDITIONAL');
assert.equal(batch.results[1].reason,'DENY_HOLD');

console.log('LEARNING_EVIDENCE_POLICY_BRIDGE_PASS');
