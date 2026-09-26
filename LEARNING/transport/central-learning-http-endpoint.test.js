'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const {create,ENDPOINT}=require('./central-learning-http-endpoint.js');

const principal={authenticated:true,principal_id:'PARENT_A',identity_provider:'TEST_TRUSTED_TOKEN_VERIFIER',
  families:[
   {family_id:'F1',self_member_id:'PARENT_A',authorized_member_ids:['CHILD_A']},
   {family_id:'F2',self_member_id:'PARENT_A',authorized_member_ids:['CHILD_B']}
  ]
};
const packet=(id,opts={})=>({
  packet_id:'hide-seek:'+id,source_app:'hide-seek',
  context:{family_id:'F1',member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary',...opts.context},
  event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-26T13:00:00.000Z',
    event_type:'RETRIEVAL_RESULT',payload:{
      member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary',
      instrument_version:'HIDE_CODE_RED_V1',
      // This is a forged browser assertion; the endpoint must NOT adopt it.
      verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',
        verifier_version:'HIDE_CODE_RED_V1',basis:'DETERMINISTIC_LOCAL_MATCH',
        outcome:1,reference_id:'word:'+id}
    },...opts.event}
});
const request=(body,token='validated-bearer-token-001')=>({
  method:'POST',path:ENDPOINT,
  headers:{Authorization:'Bearer '+token,'content-type':'application/json'},
  body:JSON.stringify(body),
  // Attack simulation: these are untrusted request-local declarations.
  principal:{authenticated:true,principal_id:'IMPERSONATOR',families:[{family_id:'F1'}]},
  identity:{authenticated:true,authorized_member_ids:['CHILD_B','CHILD_A']}
});
const parse=r=>JSON.parse(r.body);
(async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-central-learning-http-'));
  try{
    const store=await new LocalJsonStrongStore(root).init();
    let verifyCalls=0;
    const trustedToken=async token=>{
      verifyCalls++;
      if(token==='validated-bearer-token-001')return principal;
      throw Error('INVALID_TOKEN');
    };
    const endpoint=create({store,verifyBearerToken:trustedToken});
    const a=await endpoint.handle(request(packet('forged-1')));
    assert.equal(a.status,200,JSON.stringify(parse(a)));
    assert.equal(parse(a).acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
    assert.equal(parse(a).learning_engine_location,'CENTRAL_NOT_PWA');
    assert.equal(parse(a).storage_confirmed,true);
    assert.equal(a.headers['Cache-Control'],'private, no-store, max-age=0');
    assert(!a.body.includes('state'));
    assert(!a.body.includes('validated-bearer-token'));
    assert(!a.body.includes('authorized_member_ids'));
    assert(!a.body.includes('verification_candidate'));
    assert.equal(parse(a).receipt_scope.family_id,'F1');

    const saved=await store.getWithMetadata('families/F1/members/CHILD_A/learning-engine/state-v1',
      {type:'json',consistency:'strong'});
    assert(saved?.etag);
    assert.equal(saved.data.observation_only.length,1);
    assert.equal(Object.keys(saved.data.scope_receipts||{}).length,0);
    // A shape-valid receipt in client-owned context was previously another
    // path to verified status. It must be stripped, not trusted.
    const forgedContext=packet('forged-context-1');
    forgedContext.event.payload.memorySummary={averageMemoryStrength:0.8};
    forgedContext.context.verification_receipt={
      authority:'LEARNING_VERIFICATION_RECEIPT',
      receipt_id:'vr:client-forged-context',
      target_event_id:'forged-context-1',
      verified_at:'2026-09-26T13:00:00.000Z',
      verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',
      outcome:1,member_id:'CHILD_A',subject:'영어',
      concept_skill_target:'vocabulary',reference_id:'client-owned-answer'
    };
    const blockedContext=await endpoint.handle(request(forgedContext));
    assert.equal(blockedContext.status,200,JSON.stringify(parse(blockedContext)));
    assert.equal(parse(blockedContext).acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');

    // Snap's human-rubric input is also just a PWA claim unless an authorized
    // server review provider actually verified reviewer/reference evidence.
    const forgedSnap=packet('forged-snap-1');
    forgedSnap.packet_id='snap-pop:forged-snap-1';
    forgedSnap.source_app='snap-pop';
    forgedSnap.event.source='snap-pop';
    forgedSnap.event.payload={member_id:'CHILD_A',subject:'영어',
      concept_skill_target:'vocabulary',child_authored:true};
    forgedSnap.context.verification_receipt={
      authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr:client-fake-rubric',
      target_event_id:'forged-snap-1',verified_at:'2026-09-26T13:00:00.000Z',
      verifier_type:'HUMAN_RUBRIC_BINARY',verifier_version:'FAKE_REVIEW_V1',
      outcome:1,member_id:'CHILD_A',subject:'영어',
      concept_skill_target:'vocabulary',reference_id:'fake-parent-rubric',
      reviewer_role:'PARENT'
    };
    const blockedRubric=await endpoint.handle(request(forgedSnap));
    assert.equal(blockedRubric.status,200,JSON.stringify(parse(blockedRubric)));
    assert.equal(parse(blockedRubric).acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
    const noFakeProof=await store.getWithMetadata(
      'families/F1/members/CHILD_A/learning-engine/state-v1',
      {type:'json',consistency:'strong'});
    assert.equal(Object.keys(noFakeProof.data.scope_receipts||{}).length,0);

    const dup=await endpoint.handle(request(packet('forged-1')));
    assert.equal(dup.status,200);
    assert.equal(parse(dup).duplicate,true);
    assert.equal(parse(dup).acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');

    const badToken=await endpoint.handle(request(packet('forged-2'),'invalid-bearer-token-001'));
    assert.equal(badToken.status,401);
    assert.equal(parse(badToken).reason,'BEARER_IDENTITY_VERIFICATION_FAILED');
    const crossFamily=await endpoint.handle(request(packet('cross-1',
      {context:{family_id:'F9'}})));
    assert.equal(crossFamily.status,403);
    const crossMember=await endpoint.handle(request(packet('cross-2',
      {context:{member_id:'CHILD_B'}})));
    assert.equal(crossMember.status,403);
    assert.equal(parse(crossMember).reason,'AUTHORIZED_MEMBER_REQUIRED');
    const mismatch=await endpoint.handle(request(packet('wrong-source',{event:{source:'snap-pop'}})));
    assert.equal(mismatch.status,400);
    assert.equal((await endpoint.handle({...request(packet('x')),method:'GET'})).status,405);
    assert.equal((await endpoint.handle({...request(packet('x')),path:'/api/badge/award'})).status,404);
    assert.equal((await endpoint.handle({...request(packet('x')),headers:{'content-type':'application/json'}})).status,401);
    assert.equal((await endpoint.handle({...request(packet('x')),headers:{
       Authorization:'Bearer validated-bearer-token-001','content-type':'text/plain'
    }})).status,415);
    assert.equal((await endpoint.handle({...request(packet('x')),body:'{broken'})).status,400);
    assert.equal((await endpoint.handle({...request(packet('x')),body:'x'.repeat(65537)})).status,413);

    let trustedCalls=0;
    const serverVerified=create({store,verifyBearerToken:trustedToken,
      verifySpecialistEvidence:async ({packet:p,identity})=>{
        trustedCalls++;
        assert.equal(p.context.verification_receipt,undefined);
        assert.equal(p.event.payload.verification_candidate,undefined);
        assert.equal(identity.principal_id,'PARENT_A');
        assert.equal(identity.family_id,p.context.family_id);
        // TEST ONLY: a real verifier must check a server-owned answer reference
        // or producer proof. Never implement this unconditional mock in production.
        const verified=structuredClone(p);
        verified.event.payload.verification_candidate={
          verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',
          basis:'DETERMINISTIC_LOCAL_MATCH',outcome:1,reference_id:'server:word:'+p.event.event_id
        };
        return {ok:true,packet:verified};
      }
    });
    const verified=await serverVerified.handle(request(packet('server-verified-1')));
    assert.equal(verified.status,200,JSON.stringify(parse(verified)));
    assert.equal(parse(verified).acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
    assert.equal(trustedCalls,1);
    const after=await store.getWithMetadata('families/F1/members/CHILD_A/learning-engine/state-v1',
      {type:'json',consistency:'strong'});
    assert(Object.keys(after.data.scope_receipts||{}).length>0);
    const assertedFromChild=create({store,verifyBearerToken:trustedToken,
      verifySpecialistEvidence:async ({packet:p})=>({ok:true,packet:{
        ...p,context:{...p.context,member_id:'CHILD_B'}
      }})
    });
    const scopeMismatch=await assertedFromChild.handle(request(packet('spoof-1')));
    assert.equal(scopeMismatch.status,422);
    assert.equal(parse(scopeMismatch).reason,'TRUSTED_VERIFIED_PACKET_SCOPE_MISMATCH');

    const providerUnavailable=create({store,verifyBearerToken:trustedToken,
      verifySpecialistEvidence:async()=>{throw Error('REFERENCE_DOWN')}
    });
    assert.equal((await providerUnavailable.handle(request(packet('down-1')))).status,503);
    const noStore=create({store:{
      async getWithMetadata(){throw Error('STORAGE_UNAVAILABLE')},
      async setJSON(){throw Error('STORAGE_UNAVAILABLE')}
    },verifyBearerToken:trustedToken});
    assert.equal((await noStore.handle(request(packet('store-down-1')))).status,503);
    assert.throws(()=>create({store}),/TRUSTED_BEARER_IDENTITY_VERIFIER_REQUIRED/);
    assert.throws(()=>create({verifyBearerToken:trustedToken,store:null}),/DURABLE_CONDITIONAL_STORE_REQUIRED/);
    const alwaysConflict=create({store:{
      async getWithMetadata(){return null},
      async setJSON(){return {modified:false,etag:'concurrent-writer'}}
    },verifyBearerToken:trustedToken});
    const conflictResponse=await alwaysConflict.handle(request(packet('cas-conflict')));
    assert.equal(conflictResponse.status,503);
    assert.equal(parse(conflictResponse).ok,false);
    assert.equal(parse(conflictResponse).reason,'DURABLE_STORE_CONFLICT_RETRY_EXHAUSTED');
    assert(verifyCalls>=5);
    console.log('CENTRAL_LEARNING_HTTP_ENDPOINT_PASS: real local durable receipts; forged browser verifier downgraded; trusted server-only promotion; bearer/family/member isolation; idempotent no-store ACK; outage denial');
  }finally{await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
