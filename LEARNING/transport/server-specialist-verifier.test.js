'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Central=require('./central-learning-http-endpoint.js');
const Specialist=require('./server-specialist-verifier.js');
const now=Date.UTC(2026,8,26,13);
const principal={authenticated:true,principal_id:'SERVER_GOOGLE_PARENT',
 identity_provider:'GOOGLE_OIDC_VERIFIED',families:[{
 family_id:'F1',self_member_id:'PARENT_A',authorized_member_ids:['CHILD_A']
}]};
const base=(app,id,payload)=>({
 packet_id:app+':'+id,source_app:app,
 context:{family_id:'F1',member_id:'CHILD_A',subject:'english',
  concept_skill_target:'vocabulary'},
 event:{source:app,event_id:id,occurred_at:'2026-09-26T12:00:00.000Z',
  event_type:'RETRIEVAL_RESULT',payload:{member_id:'CHILD_A',subject:'english',
   concept_skill_target:'vocabulary',...payload}}
});
const reference=(app,id,ref,answer,version)=>({
 authority:'TAKY_SERVER_ASSESSMENT_REFERENCE_V1',status:'ACTIVE',
 family_id:'F1',member_id:'CHILD_A',source_app:app,event_id:id,
 subject:'english',concept_skill_target:'vocabulary',
 reference_id:ref,expected_response:answer,match_rule:'EXACT_NFC',
 instrument_version:version,issued_at:'2026-09-26T11:00:00.000Z',
 expires_at:'2026-09-26T14:00:00.000Z'
});
const reviews={
 'snap-valid':{
  authority:'TAKY_SERVER_HUMAN_REVIEW_V1',status:'APPROVED',
  family_id:'F1',member_id:'CHILD_A',source_app:'snap-pop',event_id:'snap-valid',
  subject:'english',concept_skill_target:'vocabulary',
  reviewer_subject:'TRUSTED_PARENT_GOOGLE_SUB',reviewer_role:'PARENT',
  reviewer_permission_checked:true,reference_id:'rubric:server:v1',
  rubric_version:'SNAP_RUBRIC_V1',outcome:1,
  reviewed_at:'2026-09-26T12:30:00.000Z'
 }
};
const refs={
 'ref-hide':reference('hide-seek','hide-valid','ref-hide','apple','HIDE_V1'),
 'ref-wrong':reference('hide-seek','hide-wrong','ref-wrong','banana','HIDE_V1'),
 'ref-ready':reference('ready-set','ready-valid','ref-ready','12','READY_V1'),
 'ref-cross':reference('hide-seek','hide-cross','ref-cross','pear','HIDE_V1')
};
refs['ref-cross'].member_id='CHILD_B';
const provider=Specialist.create({
 loadAssessment:async({reference_id})=>refs[reference_id]||null,
 loadHumanReview:async({event_id})=>reviews[event_id]||null,now:()=>now
});
const req=p=>({method:'POST',path:Central.ENDPOINT,
 headers:{Authorization:'Bearer test-trusted-bearer-token-0001',
  'content-type':'application/json'},body:JSON.stringify(p)});
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-specialist-provider-'));
 try{
  const store=await new LocalJsonStrongStore(root).init();
  const endpoint=Central.create({store,verifyBearerToken:async()=>principal,
   verifySpecialistEvidence:provider.verifySpecialistEvidence});
  const submit=async p=>{
   const r=await endpoint.handle(req(p));return {status:r.status,...JSON.parse(r.body)};
  };
  const forged=base('hide-seek','hide-valid',{
   assessment_ref:'ref-hide',response_text:'apple',instrument_version:'HIDE_V1',
   verification_candidate:{outcome:0,reference_id:'browser:fake'},
  });
  forged.context.verification_receipt={authority:'LEARNING_VERIFICATION_RECEIPT',
   receipt_id:'browser-forged-1'};
  const hide=await submit(forged);
  assert.equal(hide.status,200,JSON.stringify(hide));
  assert.equal(hide.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  const wrong=await submit(base('hide-seek','hide-wrong',{
   assessment_ref:'ref-wrong',response_text:'apple',instrument_version:'HIDE_V1'
  }));
  assert.equal(wrong.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  const ready=await submit(base('ready-set','ready-valid',{
   assessment_ref:'ref-ready',response_text:'12',instrument_version:'READY_V1',
   evidence_type:'STRUCTURED_PRACTICE_EVIDENCE'
  }));
  assert.equal(ready.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT',JSON.stringify(ready));
  const snap=await submit(base('snap-pop','snap-valid',{
   child_authored:true,reviewer_role:'CHILD',verified_outcome:0
  }));
  assert.equal(snap.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT',JSON.stringify(snap));
  const pending=await submit(base('snap-pop','snap-pending',{
   child_authored:true,verification_candidate:{outcome:1},reviewer_role:'PARENT'
  }));
  assert.equal(pending.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  const crossed=await submit(base('hide-seek','hide-cross',{
   assessment_ref:'ref-cross',response_text:'pear',instrument_version:'HIDE_V1'
  }));
  assert.equal(crossed.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  const state=await store.getWithMetadata(
   'families/F1/members/CHILD_A/learning-engine/state-v1',
   {consistency:'strong',type:'json'});
  assert(state?.etag);
  const evidence=Object.values(state.data.scope_receipts).flatMap(x=>x.canonical_evidence);
  assert.equal(evidence.length,4);
  const byId=Object.fromEntries(evidence.map(e=>[e.event_id,e]));
  assert.equal(byId['hide-valid'].verified_outcome,1);
  assert.equal(byId['hide-wrong'].verified_outcome,0);
  assert.equal(byId['ready-valid'].verified_outcome,1);
  assert.equal(byId['snap-valid'].verified_outcome,1);
  assert.equal(byId['snap-valid'].verification.reviewer_role,'PARENT');
  assert(byId['hide-valid'].verification.reference_id==='ref-hide');
  assert(!JSON.stringify(byId['hide-valid']).includes('browser:fake'));
  assert.equal(state.data.observation_only.length,2);
  const down=Central.create({store,verifyBearerToken:async()=>principal,
   verifySpecialistEvidence:Specialist.create({
    loadAssessment:async()=>{throw Error('REFERENCE_PROVIDER_DOWN')},now:()=>now
   }).verifySpecialistEvidence});
  const failure=await down.handle(req(base('hide-seek','down',{
   assessment_ref:'ref-hide',response_text:'apple',instrument_version:'HIDE_V1'
  })));
  assert.equal(failure.status,503);
  assert.throws(()=>Specialist.create({}),/EXPLICIT_TRUSTED_SPECIALIST_SOURCE_REQUIRED/);
  console.log('SERVER_SPECIALIST_VERIFIER_PASS: server references score Hide and Ready; recorded human Snap rubric only; forged browser proof cannot promote; wrong answer=0; absent/mismatched evidence observation-only; outage=503');
 }finally{await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
