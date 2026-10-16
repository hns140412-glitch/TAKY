'use strict';
const assert=require('node:assert/strict');
const {prepare}=require('./index-forming-learning-consumption');
const {consume}=require('./approved-forming-consumer');
const c={source_id:'A',source_ref:'IDX:A',source_family:'DOC',source_type:'REF',authority_class:'REFERENCE',detail_anchor:'DETAIL:A',provenance:['RAW:A']};
const i={query_context:{consumer_app:'HIDE_SEEK',function_id:'F',requested_behavior:'SUPPORT'},candidates:[c]};
const v=(id,ref)=>({issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',domain_use_authorized:true,source_id:id,source_ref:ref,index_version:'1',review_evidence_refs:['EVIDENCE'],source_family:c.source_family,source_type:c.source_type,authority_class:c.authority_class,detail_anchor:c.detail_anchor,provenance:c.provenance});
const f=prepare(i,v,{owner_namespace:'LEARNING_OS',forming_kind:'CONTENT_FORMING',target_consumer:'HIDE_SEEK',ruleset_revision:'1'});
const approved=(id,rev)=>({issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',artifact_id:id,artifact_revision:rev,evidence_ref:'APPROVAL:1',owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK'});
assert.equal(f.ok,true);
assert.equal(consume(f,approved,'HIDE_SEEK').ok,true);
assert.equal(consume(f,approved,'HIDE_SEEK').eligible_for_projection,true);
assert.equal(consume(f,approved,'HIDE_SEEK').learning_engine_decision,null);
assert.equal(consume(f,null,'HIDE_SEEK').ok,false);
assert.equal(consume(f,approved,'READY_SET').ok,false);
assert.equal(consume(f,()=>({...approved(f.formed.artifact_id,'BAD')}),'HIDE_SEEK').ok,false);
assert.equal(consume(f,()=>({...approved(f.formed.artifact_id,f.formed.artifact_revision),evidence_ref:''}),'HIDE_SEEK').ok,false);
assert.equal(consume({...f,ok:false},approved,'HIDE_SEEK').ok,false);
assert.equal(consume(f,()=>{throw Error('private')},'HIDE_SEEK').ok,false);
const tampered=structuredClone(f);
tampered.formed.index_refs.push({
 source_id:'FORGED',source_ref:'INDEX:FORGED',source_family:'REFERENCE',
 source_type:'DOCUMENT',authority_class:'REFERENCE',detail_anchor:'LINE:1',
 relations:[],index_version:'V1',review_evidence_refs:['FAKE'],
 provenance:['INJECTED']
});
const blocked=consume(tampered,approved,'HIDE_SEEK');
assert.equal(blocked.ok,false);
assert.ok(blocked.issues.includes('ARTIFACT_REVISION_MISMATCH'));
const relationTampered=structuredClone(f);
relationTampered.formed.index_refs[0].relations.push({target:'INJECTED'});
assert.equal(consume(relationTampered,approved,'HIDE_SEEK').ok,false);
const digestTampered=structuredClone(f);
digestTampered.formed.output_fingerprint='0'.repeat(64);
assert.equal(consume(digestTampered,approved,'HIDE_SEEK').ok,false);
console.log('APPROVED_FORMING_CONSUMER: post-approval tamper rejection PASS');
