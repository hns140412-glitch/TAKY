'use strict';
const assert=require('node:assert/strict');
const Receipt=require('./reference-curation-receipt.js');

const item={
  sentence_id:'1001',text:'The island is beautiful.',source_id:'LANGUAGE_TATOEBA_TEXT_2026',
  source_ref:'INDEX:LANGUAGE_TATOEBA_TEXT_2026',target_learning_id:'word:island',
  context_or_sense_ref:'sense:island:land',license:'CC-BY-2.0-FR',owner_or_author:'alice'
};
const review={
  receipt_id:'curation:1001:v1',reviewed_at:'2026-10-02T02:00:00Z',reviewer_role:'QUALIFIED_REVIEWER',
  naturalness_correctness:'PASS',context_sense_fit:'PASS',safety_age_fit:'PASS',license_attribution:'PASS'
};
const issued=Receipt.issue(item,review);
assert.equal(issued.ok,true);
assert.equal(Receipt.validate(issued.receipt,item).ok,true);
assert.equal(Receipt.validate(issued.receipt,{...item,text:'Tampered text.'}).ok,false);
assert.equal(Receipt.issue(item,{...review,safety_age_fit:'FAIL'}).ok,false);
assert.equal(Receipt.issue(item,{...review,reviewer_role:'UNKNOWN'}).ok,false);
console.log('REFERENCE_CURATION_RECEIPT_TEST_PASS');
