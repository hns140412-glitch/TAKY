'use strict';
const assert=require('assert');
const Filter=require('./tatoeba-item-filter.js');

const base={
  sentence_id:'1001',text:'The island is beautiful.',language:'eng',sentence_url:'https://tatoeba.org/en/sentences/show/1001',
  owner_or_author:'alice',license:'CC-BY-2.0-FR',license_provenance:'https://tatoeba.org/',retrieved_at:'2026-10-02T01:00:00Z',
  source_id:'LANGUAGE_TATOEBA_TEXT_2026',source_ref:'INDEX:LANGUAGE_TATOEBA_TEXT_2026',target_learning_id:'word:island',
  target_form:'island',context_or_sense_ref:'sense:island:land',tags:[],is_orphan:false,is_unapproved:false,context_verified:true,safety_age_fit_verified:true
};
const req={requested_language:'eng',target_form:'island',context_verified:true,requested_use:'CHILD_FACING',selected_at:'2026-10-02T01:01:00Z'};
function run(patch={},requestPatch={},review={}){return Filter.select({...base,...patch},{...req,...requestPatch},review);}
assert.equal(Filter.select({...base,sentence_id:''},req,{}).state,'REJECTED');
assert.equal(run({license:'UNKNOWN'}).state,'REJECTED');
assert.equal(run({owner_or_author:''}).state,'REJECTED');
assert.equal(run({tags:['@change']}).state,'REJECTED');
assert.equal(run({is_unapproved:true}).state,'REJECTED');
assert.equal(run({is_orphan:true}).state,'REVIEW_REQUIRED');
assert.equal(run({}, {context_verified:false}).state,'REJECTED');
assert.equal(run({language:'kor'}).state,'REJECTED');
assert.equal(run({safety_age_fit_verified:false}).state,'REJECTED');
assert.equal(run().state,'REFERENCE_ONLY');
const approved=run({}, {}, {curation_receipt:'curation:1',human_reviewed:true});
assert.equal(approved.state,'CHILD_FACING_APPROVED');
assert.equal(approved.child_facing_approved,true);
assert.equal(Filter.validateSelection(approved).ok,true);
assert.equal(run({}, {requested_claims:['learner mastery']},{curation_receipt:'curation:1',human_reviewed:true}).state,'REJECTED');
console.log('TATOEBA_ITEM_LEVEL_SELECTION_FILTER_TEST_PASS');
