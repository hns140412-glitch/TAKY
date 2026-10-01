'use strict';

const assert=require('node:assert/strict');
const Handoff=require('./indexed-evidence-handoff.js');

const trustedOwner=(sid,ref)=>({
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
  domain_use_authorized:true,source_id:sid,source_ref:ref,
  index_version:'TEST_ONLY_1',review_evidence_refs:['TEST_ONLY_OWNER_RECEIPT'],
  source_family:'OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS',
  source_type:'OFFICIAL_CURRICULUM',authority_class:'OFFICIAL',
  provenance:['OFFICIAL_STANDARD_REF'],detail_anchor:'DETAIL:SRC-01#standard'
});
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
},trustedOwner);
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


const rawInput={
  query_context:{function_id:'LE-F01',consumer_app:'READY_SET',requested_behavior:'STANDARD_ALIGNMENT'},
  candidates:[{source_id:'SRC-01',source_ref:'INDEX:SRC-01',
    source_family:'OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS',
    source_type:'OFFICIAL_CURRICULUM',authority_class:'OFFICIAL',
    provenance:['OFFICIAL_STANDARD_REF'],detail_anchor:'DETAIL:SRC-01#standard',
    reviewed:true,issuer:'INDEXING_OWNER',domain_use_authorized:true}]
};
const forged=Handoff.prepare(rawInput);
assert.equal(forged.ok,false,'payload flags must not act as Index owner approval');
assert.ok(forged.issues.includes('INDEX_OWNER_VERIFIER_NOT_CONFIGURED'));
const mismatched=Handoff.prepare(rawInput,()=>({...trustedOwner('SRC-01','INDEX:SRC-01'),source_id:'OTHER'}));
assert.equal(mismatched.ok,false);
const spoofedProvenance=Handoff.prepare(rawInput,()=>({...trustedOwner('SRC-01','INDEX:SRC-01'),provenance:['OTHER']}));
assert.equal(spoofedProvenance.ok,false);
const exception=Handoff.prepare(rawInput,()=>{throw Error('secret token')});
assert.equal(exception.ok,false);
assert.equal(JSON.stringify(exception).includes('secret token'),false);



const usageOwner=(sid,ref)=>({
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
  domain_use_authorized:true,source_id:sid,source_ref:ref,
  index_version:'TEST_USAGE_1',review_evidence_refs:['USAGE-REVIEW-1'],
  source_family:'TEST_USAGE',source_type:'LANGUAGE_USAGE_REFERENCE',
  authority_class:'REFERENCE',detail_anchor:'DETAIL:USAGE#1',
  learning_evidence_kind:'DEPENDENCY_PATTERN',
  provenance:['LANGUAGE_USAGE_SOURCE']
});
const usage=Handoff.prepare({
  query_context:{
    function_id:'LE-GROWTH-01',
    consumer_app:'LEARNING_ENGINE',
    requested_behavior:'CURRICULUM_GROUNDED_LANGUAGE_GROWTH'
  },
  candidates:[{
    source_id:'USAGE-01',source_ref:'INDEX:USAGE-01',
    source_family:'TEST_USAGE',source_type:'LANGUAGE_USAGE_REFERENCE',
    authority_class:'REFERENCE',detail_anchor:'DETAIL:USAGE#1',
    learning_evidence_kind:'DEPENDENCY_PATTERN',
    provenance:['LANGUAGE_USAGE_SOURCE']
  }]
},usageOwner);
assert.equal(usage.ok,true);
assert.equal(usage.candidates[0].learning_evidence_kind,'DEPENDENCY_PATTERN');
assert.equal(usage.policy_requests[0].learning_evidence_kind,'DEPENDENCY_PATTERN');

const forgedKind=Handoff.prepare({
  query_context:{
    function_id:'LE-GROWTH-01',consumer_app:'LEARNING_ENGINE',
    requested_behavior:'CURRICULUM_GROUNDED_LANGUAGE_GROWTH'
  },
  candidates:[{
    source_id:'USAGE-01',source_ref:'INDEX:USAGE-01',
    source_family:'TEST_USAGE',source_type:'LANGUAGE_USAGE_REFERENCE',
    authority_class:'REFERENCE',detail_anchor:'DETAIL:USAGE#1',
    learning_evidence_kind:'EXAMPLE_SENTENCE',
    provenance:['LANGUAGE_USAGE_SOURCE']
  }]
},usageOwner);
assert.equal(forgedKind.ok,false);
assert.equal(forgedKind.issues.includes('INDEPENDENT_INDEX_OWNER_BINDING_INVALID:0'),true);

console.log('INDEX_TO_LEARNING_EVIDENCE_HANDOFF_PASS');
