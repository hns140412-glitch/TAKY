'use strict';
const assert=require('node:assert/strict');
const {form}=require('./forming-bridge');
const valid={ok:true,version:'TAKY_INDEX_TO_LEARNING_EVIDENCE_HANDOFF_V1',candidates:[{
 source_id:'s1',source_ref:'raw:a',provenance:['index:verified:a'],
 source_family:'REFERENCE',source_type:'DOCUMENT',authority_class:'REFERENCE_ONLY',
 detail_anchor:'RAW:line:12',index_version:'INDEX:V1',
 review_evidence_refs:['INDEX_OWNER:REVIEW:1'],
 relations:[{relation:'SUPPORTS',target:'concept:A',anchor:'RAW:line:12'}]
}]};
const opts={owner_namespace:'LEARNING_OS',forming_kind:'CONTENT_FORMING',target_consumer:'HideSeek',ruleset_revision:'v1'};
const a=form(valid,opts),b=form(valid,opts);
assert.equal(a.ok,true);
assert.equal(a.status,'DRAFT');
assert.equal(a.approval_status,'UNAPPROVED');
assert.deepEqual(a,b);
assert.equal(form({...valid,ok:false},opts).ok,false);
assert.equal(form({...valid,candidates:[{source_id:'s1',source_ref:'raw:a',provenance:[]}]},opts).ok,false);
assert.equal(form(valid,{...opts,forming_kind:'BAD'}).ok,false);
assert.equal(form(valid,{...opts,owner_namespace:''}).ok,false);
assert.equal(form(valid,{...opts,target_consumer:''}).ok,false);
assert.notEqual(form(valid,{...opts,ruleset_revision:'v2'}).artifact_revision,a.artifact_revision);
assert.notEqual(form(valid,{...opts,owner_namespace:'OTHER'}).artifact_revision,a.artifact_revision);
assert.notEqual(form(valid,{...opts,target_consumer:'Ready'}).artifact_revision,a.artifact_revision);
assert.equal(a.consumer_contract.readiness,'NOT_APPROVED');
assert.equal(a.source_refs[0],'raw:a');
assert.equal(a.index_refs[0].detail_anchor,'RAW:line:12');
assert.deepEqual(a.index_refs[0].relations,valid.candidates[0].relations);
assert.equal(form(valid,opts).artifact_revision,a.artifact_revision);
const noMeaning=form(valid,{...opts,forming_kind:'APPLICATION_FORMING'});
assert.equal(noMeaning.ok,false);
assert.ok(noMeaning.issues.includes('APPLICATION_FORMING_SEMANTIC_PLAN_REQUIRED'));
const fakeContract=structuredClone(a);
fakeContract.consumer_contract.readiness='APPROVED';
assert.equal(require('./forming-bridge').verifyArtifact(fakeContract).ok,false);
assert.equal(require('./forming-bridge').verifyArtifact(a).ok,true);
const swapped=structuredClone(valid);
swapped.candidates[0].relations[0].target='concept:B';
assert.notEqual(form(swapped,opts).artifact_revision,a.artifact_revision);
const changedAnchor=structuredClone(valid);
changedAnchor.candidates[0].detail_anchor='RAW:line:13';
assert.notEqual(form(changedAnchor,opts).artifact_revision,a.artifact_revision);
const changedAuthority=structuredClone(valid);
changedAuthority.candidates[0].authority_class='UNTRUSTED';
assert.notEqual(form(changedAuthority,opts).artifact_revision,a.artifact_revision);
const mutated=structuredClone(a);
mutated.index_refs[0].relations[0].target='INJECTED';
assert.equal(require('./forming-bridge').verifyArtifact(mutated).ok,false);
assert.equal(form({...valid,candidates:[{...valid.candidates[0],review_evidence_refs:[]}]},opts).ok,false);
console.log('FORMING BRIDGE: semantic revision + integrity checks PASS');
