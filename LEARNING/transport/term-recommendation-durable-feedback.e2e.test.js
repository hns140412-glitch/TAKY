'use strict';
// No user records, no CURRENT or app writes. Real local filesystem CAS store.
// Trusted proof source here is a TEST-ONLY mock; must not be deployed.
const assert=require('node:assert/strict');
const fs=require('node:fs').promises,os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store');
const Evidence=require('./central-learning-http-endpoint');
const Term=require('./term-recommendation-http-endpoint');
const Durable=require('./durable-evidence-store-adapter');
const TOKEN='test-local-bearer-token-123456';
const principal={authenticated:true,principal_id:'PARENT',
 families:[{family_id:'LOCAL_FIXTURE_FAMILY',self_member_id:'PARENT',
            authorized_member_ids:['CHILD_A']}]};
const auth=async token=>{if(token!==TOKEN)throw Error('BAD_TOKEN');return principal;};
const headers={'authorization':'Bearer '+TOKEN,'content-type':'application/json'};
const term={id:'science-e5-front',term:'한랭전선',subject:'SCIENCE',
 meaning:'찬 공기와 따뜻한 공기의 경계가 형성하는 전선',gradeBand:'5-6',
 source_ref:'CURR:SCIENCE:5-6:FRONT',
 grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:5-6:FRONT'},
 components:[{text:'寒',meaning:'차다'}],hanja:'寒冷前線',
 concept:{relations:['대기의 이동']},unit_tags:['날씨']};
const recReq=member=>({
 path:Term.ENDPOINT,method:'POST',headers,
 body:JSON.stringify({family_id:'LOCAL_FIXTURE_FAMILY',member_id:member,
                      subject:'SCIENCE',unit_context:['날씨'],limit:2})});
// The REAL Hide & Seek TERM_DECODER uses "term:"+catalogId in its event.
const packet=(id,target='term:science-e5-front')=>({
 packet_id:'hide-seek:'+id,source_app:'hide-seek',
 context:{family_id:'LOCAL_FIXTURE_FAMILY',member_id:'CHILD_A',
          subject:'science',concept_skill_target:'vocabulary',
          learning_target_id:target},
 event:{source:'hide-seek',event_id:id,occurred_at:'2026-10-14T00:00:00.000Z',
  event_type:'RETRIEVAL_RESULT',payload:{
    subject:'science',concept_skill_target:'vocabulary',
    learning_target_id:target,instrument_version:'HIDE_CODE_RED_V1',
    // Client-owned declaration must be ignored:
    verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',
      verifier_version:'FORGED',basis:'DETERMINISTIC_LOCAL_MATCH',
      outcome:1,reference_id:'client:forged'}
  }}
});
const request=body=>({method:'POST',path:Evidence.ENDPOINT,headers,body:JSON.stringify(body)});
const parsed=res=>JSON.parse(res.body);
(async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'taky-learning-durable-feedback-'));
 try{
  let store=await new LocalJsonStrongStore(dir).init();
  const buildTerm=store=>Term.create({verifyBearerToken:auth,durableTermStore:store,
   resolveLearnerProfile:async()=>({school_stage:'E5'}),
   resolveCurriculumTerms:async()=>({source_ref:'CURR:SCIENCE:5-6:FRONT',terms:[term]})});
  let recommendation=buildTerm(store);
  const first=parsed(await recommendation.handle(recReq('CHILD_A')));
  assert.equal(first.ok,true);
  assert.equal(first.term_recommendations[0].priority,'DISCOVERY');
  assert.equal(first.trace.evidence_count,0);
  const ingest=Evidence.create({store,verifyBearerToken:auth,
   verifySpecialistEvidence:async({packet:p})=>{
    // TEST fixture trusted server evaluator, never browser-provided proof.
    const x=structuredClone(p);
    x.event.payload.verification_candidate={
      basis:'DETERMINISTIC_LOCAL_MATCH',verifier_type:'RETRIEVAL_EXACT_MATCH',
      verifier_version:'TEST_VERIFIER_ONLY',outcome:0,
      reference_id:'server-owned:test:science-front'
    };
    return {ok:true,packet:x};
   }});
  // Unverified browser evidence remains observation only and must not affect
  // word difficulty or be replayed as a verified failure.
  const unverified=Evidence.create({store,verifyBearerToken:auth});
  const forged=parsed(await unverified.handle(request(packet('bad-client-proof'))));
  assert.equal(forged.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  let afterForged=parsed(await recommendation.handle(recReq('CHILD_A')));
  assert.equal(afterForged.trace.evidence_count,0);
  assert.equal(afterForged.term_recommendations[0].priority,'DISCOVERY');
  for(const id of ['server-reviewed-wrong-1','server-reviewed-wrong-2']){
   const ack=parsed(await ingest.handle(request(packet(id))));
   assert.equal(ack.ok,true);
   assert.equal(ack.storage_confirmed,true);
   assert.equal(ack.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  }
  // The data actually persisted; reopen the store rather than reuse responses.
  store=await new LocalJsonStrongStore(dir).init();
  recommendation=buildTerm(store);
  const after=parsed(await recommendation.handle(recReq('CHILD_A')));
  assert.equal(after.ok,true,JSON.stringify(after));
  assert.equal(after.trace.evidence_count,2);
  assert.equal(after.term_recommendations[0].priority,'RECOVERY');
  assert.equal(after.term_recommendations[0].evidence_summary.wrong,2);
  assert.ok(after.term_recommendations[0].reasons.includes('RECOVERY_NEEDED'));
  assert.equal(after.term_recommendations[0].learning_pattern_plan.recovery.route,'TARGETED_CONCEPT_REVIEW');
  assert.equal((await recommendation.handle(recReq('CHILD_B'))).status,403);
  const key=Durable.stateKey({family_id:'LOCAL_FIXTURE_FAMILY',member_id:'CHILD_A'});
  const saved=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
  assert.equal(saved.consistency,'strong');
  const group=Object.values(saved.data.scope_receipts)[0];
  assert.equal(group.canonical_evidence.length,2);
  // Tamper a server-side record, even with a valid strong-store etag. Reject.
  const changed=structuredClone(saved.data);
  Object.values(changed.scope_receipts)[0].canonical_evidence[0].verified_outcome=1;
  const update=await store.setJSON(key,changed,{onlyIfMatch:saved.etag});
  assert.equal(update.modified,true);
  const refused=parsed(await recommendation.handle(recReq('CHILD_A')));
  assert.equal(refused.ok,false);
  assert.equal(refused.reason,'TERM_EVIDENCE_UNAVAILABLE');
  assert.throws(()=>Term.create({verifyBearerToken:auth,
    resolveLearnerProfile:async()=>({school_stage:'E5'}),
    resolveCurriculumTerms:async()=>({terms:[]}),
    durableTermStore:store,resolveTermEvidence:async()=>[]}),
    /AMBIGUOUS_TERM_EVIDENCE_AUTHORITY/);
 }finally{await fs.rm(dir,{recursive:true,force:true});}
})().then(()=>console.log('DURABLE_TERM_FEEDBACK_CLOSED_LOOP_PASS verified failure persisted/reloaded -> RECOVERY; forged/tampered/cross-member rejected; TEST AUTHORITY ONLY'))
 .catch(e=>{console.error(e);process.exitCode=1});
