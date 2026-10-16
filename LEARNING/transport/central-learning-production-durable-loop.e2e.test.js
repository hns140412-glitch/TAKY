'use strict';
const assert=require('node:assert/strict'),http=require('node:http');
const fs=require('node:fs').promises,os=require('node:os'),path=require('node:path');
const Host=require('./central-learning-production-host');
const {LocalJsonStrongStore}=require('./local-json-strong-store');
const nowMs=Date.UTC(2026,9,14,0,0,0),nowSec=nowMs/1000;
const clientId='TAKY-FORMING-DURABLE-TEST-AUDIENCE',token='local-oauth-test-token-111';
const oauth2Client={verifyIdToken:async({idToken,audience})=>{
 assert.equal(idToken,token);assert.deepEqual(audience,[clientId]);
 return {getPayload:()=>({
 iss:'https://accounts.google.com',aud:clientId,sub:'LOCAL_TEST_GUARDIAN',
 iat:nowSec-30,exp:nowSec+300
 })};
}};
const lookupMemberships=async()=>[{
 status:'ACTIVE',family_id:'TEST_FAMILY',self_member_id:'GUARDIAN',
 role:'PARENT',learning_evidence_submit_member_ids:['TEST_CHILD'],permissions:[]
}];
const endpointPaths={event:'/api/learning/evidence',
 recommendation:'/api/learning/term-recommendations'};
const term={id:'test-sci-front',term:'한랭전선',subject:'SCIENCE',
 meaning:'찬 공기의 이동에 의해 형성되는 전선',gradeBand:'5-6',hanja:'寒冷前線',
 source_ref:'CURR:TEST:SCI:FRONT',grade_alignment:{
 state:'VERIFIED',source_ref:'CURR:TEST:SCI:FRONT'
 },components:[{text:'寒',meaning:'차다'}],concept:{relations:['날씨 관계']},
 unit_tags:['날씨']};
const rec={family_id:'TEST_FAMILY',member_id:'TEST_CHILD',subject:'SCIENCE',limit:1};
const headers={'content-type':'application/json','authorization':'Bearer '+token,
 origin:'https://ready.example.test'};
(async()=>{
 const temp=await fs.mkdtemp(path.join(os.tmpdir(),'taky-prod-learning-closed-loop-'));
 let server;
 try{
  const store=await new LocalJsonStrongStore(temp).init();
  const host=Host.create({
   clientIds:[clientId],oauth2Client,lookupMemberships,store,
   verifySpecialistEvidence:async({packet})=>{
    // Server-only FIXTURE verifier. Browser verification_candidate stripped
    // before this mock. No child credentials, no actual production keys.
    assert.equal(packet.event.payload.verification_candidate,undefined);
    if(packet.event.event_id.startsWith('untrusted')){
      return {ok:false};
    }
    const copy=structuredClone(packet);
    copy.event.payload.verification_candidate={
     verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'TEST_ONLY',
     basis:'DETERMINISTIC_LOCAL_MATCH',outcome:0,
     reference_id:'test-server-answer-key:SCI_FRONT'
    };
    return {ok:true,packet:copy};
   },
   resolveIndexedEvidence:async()=>null,independentIndexOwnerVerifier:()=>null,
   resolveLearnerProfile:async()=>({school_stage:'E5'}),
   resolveCurriculumTerms:async()=>({terms:[term],source_ref:'CURR:TEST:SCI:FRONT'}),
   // Intentionally omit resolveTermEvidence: production host must use its
   // existing strong evidence store for term selection.
   allowedOrigins:['https://ready.example.test'],now:()=>nowMs
  });
  server=http.createServer(host.handler);
  await new Promise((ok,err)=>server.once('error',err).listen(0,'127.0.0.1',ok));
  const base='http://127.0.0.1:'+server.address().port;
  const post=async(route,data)=>fetch(base+route,{method:'POST',headers,body:JSON.stringify(data)});
  const getRecommendations=async()=>{const res=await post(endpointPaths.recommendation,rec);
   const data=await res.json();assert.equal(res.status,200,JSON.stringify(data));return data;};
  const before=await getRecommendations();
  assert.equal(before.trace.evidence_count,0);
  assert.equal(before.term_recommendations[0].priority,'DISCOVERY');
  const packet=id=>({
   packet_id:'hide-seek:'+id,source_app:'hide-seek',
   context:{family_id:'TEST_FAMILY',member_id:'TEST_CHILD',
    subject:'science',concept_skill_target:'vocabulary',learning_target_id:'test-sci-front'},
   event:{source:'hide-seek',event_id:id,occurred_at:'2026-10-14T00:01:00.000Z',
    event_type:'RETRIEVAL_RESULT',payload:{
      instrument_version:'TEST_HIDE_RETRIEVAL',learning_target_id:'test-sci-front',
      verification_candidate:{basis:'DETERMINISTIC_LOCAL_MATCH',verifier_type:'RETRIEVAL_EXACT_MATCH',
       outcome:1,reference_id:'FAKE_BROWSER_REFERENT'}
   }}
  });
  const observation=await post(endpointPaths.event,packet('untrusted-browser'));
  assert.equal(observation.status,200);
  assert.equal((await observation.json()).acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  assert.equal((await getRecommendations()).trace.evidence_count,0);
  for(const id of ['server-verified-wrong-1','server-verified-wrong-2']){
   const ack=await post(endpointPaths.event,packet(id));
   const body=await ack.json();assert.equal(ack.status,200,JSON.stringify(body));
   assert.equal(body.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
   assert.equal(body.storage_confirmed,true);
  }
  const after=await getRecommendations();
  assert.equal(after.trace.evidence_count,2);
  assert.equal(after.term_recommendations[0].priority,'RECOVERY');
  assert.equal(after.term_recommendations[0].evidence_summary.wrong,2);
  assert.equal(after.term_recommendations[0].learning_pattern_plan.recovery.route,
   'TARGETED_CONCEPT_REVIEW');
  const denied=await post(endpointPaths.recommendation,{...rec,member_id:'OTHER'});
  assert.equal(denied.status,403);
  const external=await fetch(base+endpointPaths.recommendation,{
   method:'POST',headers:{...headers,origin:'https://untrusted.example.test'},
   body:JSON.stringify(rec)});
  assert.equal(external.status,403);
  const fakeInjection=await post(endpointPaths.recommendation,{
   ...rec,term_evidence:[{learning_target_id:'test-sci-front',result_type:'CORRECT'}]});
  assert.equal(fakeInjection.status,400);
  console.log('CENTRAL_HOST_REAL_HTTP_DURABLE_FEEDBACK_PASS',
   JSON.stringify({before:before.term_recommendations[0].priority,
    after:after.term_recommendations[0].priority,storedVerifiedEvidence:after.trace.evidence_count,
    browserProofPromoted:false,fixtureOnly:true,network:'loopback_only',
    FORMING_approval_operational:false,app_session_not_tested:true}));
 }finally{
  if(server)await new Promise(resolve=>server.close(resolve));
  await fs.rm(temp,{recursive:true,force:true});
 }
})().catch(e=>{console.error(e);process.exitCode=1});
