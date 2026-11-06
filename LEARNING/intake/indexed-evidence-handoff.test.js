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

// Relations must match independent INDEX owner; caller cannot introduce facts.
const relation={type:'SUPPORTS',target:'concept:water',anchor:'DETAIL:SRC-01#standard'};
const ownerWithRelation=(sid,ref)=>({...trustedOwner(sid,ref),relations:[relation]});
const authorizedCandidate={...rawInput.candidates[0],relations:[relation]};
const relationGood=Handoff.prepare({...rawInput,candidates:[authorizedCandidate]},ownerWithRelation);
assert.equal(relationGood.ok,true);
assert.deepEqual(relationGood.candidates[0].relations,[relation]);
assert.equal(relationGood.candidates[0].index_version,'TEST_ONLY_1');
const fakeRelation=Handoff.prepare(
  {...rawInput,candidates:[{...authorizedCandidate,relations:[{...relation,target:'INJECTED'}]}]},
  ownerWithRelation);
assert.equal(fakeRelation.ok,false);
assert.ok(fakeRelation.issues.includes('INDEPENDENT_INDEX_OWNER_BINDING_INVALID:0'));
const omittedOwnerRelation=Handoff.prepare(
  {...rawInput,candidates:[authorizedCandidate]},trustedOwner);
assert.equal(omittedOwnerRelation.ok,false);
console.log('INDEX_TO_LEARNING_EVIDENCE_HANDOFF_PASS: owner-bound relations and spoof rejection');

// Candidate identity must be unique before any policy request is emitted.
const identityCases=[
  {row:{...rawInput.candidates[0]},issues:['SOURCE_ID_DUPLICATE:1','SOURCE_REF_DUPLICATE:1']},
  {row:{...rawInput.candidates[0],source_ref:'INDEX:OTHER'},issues:['SOURCE_ID_DUPLICATE:1']},
  {row:{...rawInput.candidates[0],source_id:'OTHER'},issues:['SOURCE_REF_DUPLICATE:1']}
];
for(const {row,issues} of identityCases){
  const result=Handoff.prepare({...rawInput,candidates:[rawInput.candidates[0],row]},trustedOwner);
  assert.equal(result.ok,false,'duplicate candidate identity must fail closed');
  assert.deepEqual(result.issues,issues);
  assert.deepEqual(result.policy_requests,[]);
}
const distinctRows=[rawInput.candidates[0],{...rawInput.candidates[0],source_id:'SRC-02',source_ref:'INDEX:SRC-02'}];
const distinct=Handoff.prepare({...rawInput,candidates:distinctRows},trustedOwner);
assert.equal(distinct.ok,true);
assert.deepEqual(distinct.source_refs,distinctRows.map(row=>row.source_ref));
assert.deepEqual(distinct.policy_requests.map(row=>row.source_id),['SRC-01','SRC-02']);
assert.deepEqual(distinct.candidates.map(row=>row.source_id),['SRC-01','SRC-02']);
const duplicateSpoof=Handoff.prepare({...rawInput,candidates:[rawInput.candidates[0],{...rawInput.candidates[0],provenance:['FORGED'],relations:[relation]}]},trustedOwner);
assert.equal(duplicateSpoof.ok,false);
assert.deepEqual(duplicateSpoof.issues,['SOURCE_ID_DUPLICATE:1','SOURCE_REF_DUPLICATE:1','INDEPENDENT_INDEX_OWNER_BINDING_INVALID:1','PROVENANCE_MISSING:1']);
assert.deepEqual(duplicateSpoof.policy_requests,[]);
console.log('INDEX_IDENTITY_UNIQUENESS: fail-closed duplicates and ordered distinct candidates PASS');
