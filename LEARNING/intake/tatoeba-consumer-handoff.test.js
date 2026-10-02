'use strict';
const assert=require('node:assert/strict');
const Adapter=require('../adapters/tatoeba-provider-item.js');
const Filter=require('./tatoeba-item-filter.js');
const Receipt=require('../verification/reference-curation-receipt.js');
const Handoff=require('./tatoeba-consumer-handoff.js');

const raw={
  id:'1001',text:'The island is beautiful.',lang:'eng',owner_or_author:'alice',
  license:'CC-BY-2.0-FR',license_provenance:'https://api.tatoeba.org/v1/sentences/1001',
  retrieved_at:'2026-10-02T02:00:00Z',approved:true,is_orphan:false,tags:[]
};
const query={
  requested_language:'eng',target_learning_id:'word:island',target_form:'island',
  context_or_sense_ref:'sense:island:land',context_verified:true,safety_age_fit_verified:true,
  requested_use:'CHILD_FACING'
};
const adapted=Adapter.normalizeProviderItem(raw,query);
assert.equal(adapted.ok,true);

const review=Receipt.issue(adapted.normalized_item,{
  receipt_id:'curation:1001:v1',reviewed_at:'2026-10-02T02:01:00Z',reviewer_role:'QUALIFIED_REVIEWER',
  naturalness_correctness:'PASS',context_sense_fit:'PASS',safety_age_fit:'PASS',license_attribution:'PASS'
});
assert.equal(review.ok,true);

const selected=Filter.select(adapted.normalized_item,{
  requested_language:'eng',target_form:'island',context_verified:true,requested_use:'CHILD_FACING',
  selected_at:'2026-10-02T02:02:00Z'
},{curation_receipt:review.receipt});
assert.equal(selected.state,'CHILD_FACING_APPROVED');

const hide=Handoff.prepare(selected,{consumer_app:'HIDE_SEEK',purpose:'MEANING_IN_CONTEXT_SUPPORT'});
assert.equal(hide.ok,true);
assert.equal(hide.guards.learner_performance_credit,false);
assert.equal(hide.consumer_guards.recall_evidence_credit,false);
assert.equal(Handoff.validate(hide).ok,true);

const snap=Handoff.prepare(selected,{consumer_app:'SNAP_POP',purpose:'WRITING_PREPARATION_REFERENCE'});
assert.equal(snap.ok,true);
assert.equal(snap.consumer_guards.learner_authorship_required,true);
assert.equal(snap.consumer_guards.auto_insert_into_learner_output,false);
assert.equal(Handoff.validate(snap).ok,true);

const fakeString=Filter.select(adapted.normalized_item,{
  requested_language:'eng',target_form:'island',context_verified:true,requested_use:'CHILD_FACING'
},{curation_receipt:'fake-receipt'});
assert.notEqual(fakeString.state,'CHILD_FACING_APPROVED');

const tampered={...adapted.normalized_item,text:'A different sentence about an island.'};
const tamperedSelected=Filter.select(tampered,{
  requested_language:'eng',target_form:'island',context_verified:true,requested_use:'CHILD_FACING'
},{curation_receipt:review.receipt});
assert.notEqual(tamperedSelected.state,'CHILD_FACING_APPROVED');

assert.equal(Handoff.prepare({...selected,state:'REFERENCE_ONLY'},{consumer_app:'HIDE_SEEK',purpose:'CONTEXT_EXPOSURE'}).ok,false);
assert.equal(Handoff.prepare(selected,{consumer_app:'SNAP_POP',purpose:'AUTO_COMPLETE'}).ok,false);
console.log('TATOEBA_CONSUMER_HANDOFF_E2E_TEST_PASS');
