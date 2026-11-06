'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Sources=require('./server-specialist-reference-store.js');
const Specialist=require('./server-specialist-verifier.js');
const Central=require('./central-learning-http-endpoint.js');
const family_id='F1',member_id='CHILD_A',subject='english',concept_skill_target='vocabulary';
const assessmentScope={family_id,member_id,event_id:'reference-h1',
 source_app:'hide-seek',reference_id:'ref-h1'};
const reviewScope={family_id,member_id,event_id:'review-s1',source_app:'snap-pop'};
const assignment={
 ...assessmentScope,authority:'TAKY_SERVER_ASSESSMENT_REFERENCE_V1',
 version:1,issuer_service:'CENTRAL_ASSESSMENT_ISSUER',issuer_authorized:true,
 status:'ACTIVE',subject,concept_skill_target,match_rule:'EXACT_NFC',
 expected_response:'apple',instrument_version:'HIDE_V1',
 issued_at:'2026-09-26T11:00:00.000Z',expires_at:'2026-09-26T14:00:00.000Z'
};
const review={
 ...reviewScope,authority:'TAKY_SERVER_HUMAN_REVIEW_V1',
 version:1,issuer_service:'CENTRAL_REVIEW_GATE',issuer_authorized:true,
 status:'APPROVED',subject,concept_skill_target,
 reviewer_subject:'SERVER_AUTHORIZED_PARENT_SUB',reviewer_role:'PARENT',
 reviewer_authorization_receipt_id:'server-review-grant-1',
 reviewer_permission_checked:true,reference_id:'rubric:server:1',
 rubric_version:'SNAP_V1',outcome:1,reviewed_at:'2026-09-26T12:30:00.000Z'
};
const parent={authenticated:true,principal_id:'google:SERVER_PARENT',families:[{
 family_id,self_member_id:'PARENT_A',authorized_member_ids:[member_id]
}]};
const packet=(source_app,id,payload)=>({
 packet_id:source_app+':'+id,source_app,
 context:{family_id,member_id,subject,concept_skill_target},
 event:{source:source_app,event_id:id,
  occurred_at:'2026-09-26T12:00:00.000Z',event_type:'RETRIEVAL_RESULT',
  payload:{member_id,subject,concept_skill_target,...payload}}
});
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-server-ref-'));
 try{
  const store=await new LocalJsonStrongStore(root).init();
  const sources=Sources.create({store});
  await store.setJSON(Sources.assessmentKey(assessmentScope),assignment,{onlyIfNew:true});
  await store.setJSON(Sources.humanReviewKey(reviewScope),review,{onlyIfNew:true});
  assert(!Sources.assessmentKey(assessmentScope).includes(member_id));
  assert.equal((await sources.loadAssessment(assessmentScope)).expected_response,'apple');
  assert.equal((await sources.loadHumanReview(reviewScope)).reviewer_role,'PARENT');
  assert.equal(await sources.loadAssessment({...assessmentScope,member_id:'CHILD_B'}),null);
  assert.equal(await sources.loadHumanReview({...reviewScope,event_id:'different'}),null);
  const evidence=await new LocalJsonStrongStore(path.join(root,'evidence')).init();
  const specialist=Specialist.create({
   loadAssessment:sources.loadAssessment,loadHumanReview:sources.loadHumanReview,
   now:()=>Date.UTC(2026,8,26,13)
  });
  const endpoint=Central.create({store:evidence,verifyBearerToken:async()=>parent,
   verifySpecialistEvidence:specialist.verifySpecialistEvidence});
  const send=async p=>{
   const result=await endpoint.handle({
    method:'POST',path:Central.ENDPOINT,
    headers:{Authorization:'Bearer fixture-token-not-real-00001',
     'Content-Type':'application/json'},body:JSON.stringify(p)
   });return {status:result.status,body:JSON.parse(result.body)};
  };
  const h=await send(packet('hide-seek','reference-h1',{
   assessment_ref:'ref-h1',response_text:'apple',instrument_version:'HIDE_V1'
  }));
  assert.equal(h.status,200,JSON.stringify(h.body));
  assert.equal(h.body.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  const snap=await send(packet('snap-pop','review-s1',{child_authored:true}));
  assert.equal(snap.status,200,JSON.stringify(snap.body));
  assert.equal(snap.body.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  const missing=await send(packet('hide-seek','unissued-h2',{
   assessment_ref:'ref-h1',response_text:'apple',instrument_version:'HIDE_V1'
  }));
  assert.equal(missing.body.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  // Provider refuses a forged server-origin record, even if shape is plausible.
  const scope2={...assessmentScope,event_id:'reference-h2'};
  await store.setJSON(Sources.assessmentKey(scope2),{...assignment,
   event_id:'reference-h2',issuer_authorized:false},{onlyIfNew:true});
  await assert.rejects(()=>sources.loadAssessment(scope2),/REFERENCE_SERVER_PROVENANCE_INVALID/);
  const before=await store.getWithMetadata(Sources.humanReviewKey(reviewScope),
   {type:'json',consistency:'strong'});
  await store.setJSON(Sources.humanReviewKey(reviewScope),{
   ...review,reviewer_authorization_receipt_id:''},{onlyIfMatch:before.etag});
  await assert.rejects(()=>sources.loadHumanReview(reviewScope),
   /REVIEWER_AUTHORIZATION_RECEIPT_REQUIRED/);
  assert.throws(()=>Sources.create({store:{}}),/SERVER_ONLY_REFERENCE_STORE_REQUIRED/);
  console.log('SERVER_SPECIALIST_REFERENCE_STORE_PASS: strong scoped server-issued Hide/Snap references, unissued observation-only, forged issuer/reviewer provenance denied');
 }finally{await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
