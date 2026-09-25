'use strict';

const assert=require('node:assert/strict');
const Handoff=require('./indexed-evidence-handoff.js');

const ok=Handoff.prepare({
  query_context:{
    function_id:'LE-F01',
    consumer_app:'READY_SET',
    requested_behavior:'STANDARD_ALIGNMENT'
  },
  candidates:[{
    source_id:'SRC-01',
    source_ref:'INDEX:SRC-01',
    source_family:'OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS',
    source_type:'OFFICIAL_CURRICULUM',
    authority_class:'OFFICIAL',
    provenance:['OFFICIAL_STANDARD_REF'],
    detail_anchor:'DETAIL:SRC-01#standard'
  }]
});
assert.equal(ok.ok,true);
assert.deepEqual(ok.source_refs,['INDEX:SRC-01']);
assert.equal(ok.policy_requests[0].source_id,'SRC-01');
assert.equal(ok.policy_requests[0].source_ref,'INDEX:SRC-01');
assert.deepEqual(ok.policy_requests[0].provenance,['OFFICIAL_STANDARD_REF']);
assert.equal(ok.invariant,'INDEX_RETRIEVAL_METADATA_IS_CONTEXT_NOT_LEARNER_PERFORMANCE');

const noRef=Handoff.prepare({
  query_context:{
    function_id:'LE-F03',
    consumer_app:'HIDE_SEEK',
    requested_behavior:'CONTEXTUAL_SENSE_SUPPORT'
  },
  candidates:[{
    source_id:'SRC-02',
    provenance:['NIKL_SOURCE_REF','EXPLICIT_CONTEXT_BINDING']
  }]
});
assert.equal(noRef.ok,false);
assert.equal(noRef.issues.includes('SOURCE_REF_MISSING:0'),true);

const noProv=Handoff.prepare({
  query_context:{
    function_id:'LE-F06',
    consumer_app:'SNAP_POP',
    requested_behavior:'WRITING_PROCESS_SCAFFOLD'
  },
  candidates:[{
    source_id:'SRC-03',
    source_ref:'INDEX:SRC-03'
  }]
});
assert.equal(noProv.ok,false);
assert.equal(noProv.issues.includes('PROVENANCE_MISSING:0'),true);

console.log('INDEX_TO_LEARNING_EVIDENCE_HANDOFF_PASS');
