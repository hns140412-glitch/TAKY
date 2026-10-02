'use strict';
const assert=require('assert');
const Adapter=require('./tatoeba-provider-item.js');

const baseItem={
  id:'1001',text:'The island is beautiful.',lang:'eng',url:'https://tatoeba.org/en/sentences/show/1001',
  owner_or_author:'alice',license:'CC-BY-2.0-FR',license_provenance:'https://tatoeba.org/',retrieved_at:'2026-10-02T01:00:00Z',
  approved:true,is_orphan:false,tags:[]
};
const baseQuery={
  requested_language:'eng',target_learning_id:'word:island',target_form:'island',context_or_sense_ref:'sense:island:land',
  context_verified:true,safety_age_fit_verified:true,requested_use:'REFERENCE_ONLY'
};
function state(itemPatch={},queryPatch={}){
  return Adapter.normalizeProviderItem({...baseItem,...itemPatch},{...baseQuery,...queryPatch}).state;
}
assert.equal(state(),'REFERENCE_ONLY_CANDIDATE');
assert.equal(state({license:null}),'PROVENANCE_INCOMPLETE');
assert.equal(state({owner_or_author:''}),'PROVENANCE_INCOMPLETE');
assert.equal(state({approved:false}),'QUALITY_HOLD');
assert.equal(state({is_orphan:true},{requested_use:'CHILD_FACING'}),'QUALITY_HOLD');
assert.equal(state({lang:'kor'}),'LANGUAGE_MISSING_OR_MISMATCH');
assert.equal(state({}, {context_verified:false}),'CONTEXT_HOLD');
assert.equal(state({}, {requested_use:'CHILD_FACING',safety_age_fit_verified:false}),'SAFETY_HOLD');
assert.equal(state({}, {curation_receipt:''}),'REFERENCE_ONLY_CANDIDATE');
const valid=Adapter.normalizeProviderItem(baseItem,{...baseQuery,curation_receipt:'review:1'});
assert.equal(valid.state,'CANDIDATE_NORMALIZED');
assert.equal(valid.normalized_item.index_owner_authority,false);
assert.equal(valid.normalized_item.normative_usage_authority,false);
assert.equal(valid.normalized_item.frequency_authority,false);
assert.equal(valid.normalized_item.mastery_authority,false);
assert.equal(Adapter.validateResult(valid).ok,true);
console.log('TATOEBA_PROVIDER_ITEM_ADAPTER_TEST_PASS');
