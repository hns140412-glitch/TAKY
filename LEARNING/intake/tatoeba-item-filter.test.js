'use strict';
const assert=require('node:assert/strict');
const Filter=require('./tatoeba-item-filter.js');
const Receipt=require('../verification/reference-curation-receipt.js');

const base={
  sentence_id:'1001',text:'The island is beautiful.',language:'eng',sentence_url:'https://tatoeba.org/en/sentences/show/1001',
  owner_or_author:'alice',license:'CC-BY-2.0-FR',license_provenance:'https://api.tatoeba.org/v1/sentences/1001',retrieved_at:'2026-10-02T01:00:00Z',
  source_id:'LANGUAGE_TATOEBA_TEXT_2026',source_ref:'INDEX:LANGUAGE_TATOEBA_TEXT_2026',target_learning_id:'word:island',
  target_form:'island',context_or_sense_ref:'sense:island:land',tags:[],is_orphan:false,is_unapproved:false,context_verified:true,safety_age_fit_verified:true
};
const req={requested_language:'eng',target_form:'island',context_verified:true,requested_use:'CHILD_FACING',selected_at:'2026-10-02T01:01:00Z'};
function reviewFor(item=base,patch={}){
  const r=Receipt.issue(item,{
    receipt_id:'curation:'+item.sentence_id+':v1',reviewed_at:'2026-10-02T01:00:30Z',reviewer_role:'QUALIFIED_REVIEWER',
    naturalness_correctness:'PASS',context_sense_fit:'PASS',safety_age_fit:'PASS',license_attribution:'PASS',...patch
  });
  assert.equal(r.ok,true);
  return r.receipt;
}
function run(patch={},requestPatch={},review={}){return Filter.select({...base,...patch},{...req,...requestPatch},review);}

assert.equal(Filter.select({...base,sentence_id:''},req,{}).state,'REJECTED');
assert.equal(run({license:'UNKNOWN'}).state,'REJECTED');
assert.equal(run({owner_or_author:''}).state,'REJECTED');
assert.equal(run({tags:['@change']}).state,'REJECTED');
assert.equal(run({is_unapproved:true}).state,'REJECTED');
assert.equal(run({}, {context_verified:false}).state,'REJECTED');
assert.equal(run({language:'kor'}).state,'REJECTED');
assert.equal(run({safety_age_fit_verified:false}).state,'REJECTED');
assert.equal(run().state,'REFERENCE_ONLY');

const fake=run({}, {}, {curation_receipt:'curation:fake'});
assert.equal(fake.state,'REVIEW_REQUIRED');
assert.equal(fake.child_facing_approved,false);

const receipt=reviewFor();
const approved=run({}, {}, {curation_receipt:receipt});
assert.equal(approved.state,'CHILD_FACING_APPROVED');
assert.equal(approved.child_facing_approved,true);
assert.equal(Filter.validateSelection(approved).ok,true);

const tampered=run({text:'The island became a different reviewed text.'},{},{curation_receipt:receipt});
assert.equal(tampered.state,'REVIEW_REQUIRED');

const orphanItem={...base,is_orphan:true};
const curatedReceipt=Receipt.issue(orphanItem,{
  receipt_id:'curation:orphan:v1',reviewed_at:'2026-10-02T01:00:30Z',reviewer_role:'CURATED_REFERENCE_REVIEWER',
  naturalness_correctness:'PASS',context_sense_fit:'PASS',safety_age_fit:'PASS',license_attribution:'PASS'
}).receipt;
assert.equal(Filter.select(orphanItem,req,{curation_receipt:curatedReceipt}).state,'REVIEW_REQUIRED');

assert.equal(run({}, {requested_claims:['learner mastery']},{curation_receipt:receipt}).state,'REJECTED');
console.log('TATOEBA_ITEM_LEVEL_SELECTION_FILTER_TEST_PASS');
