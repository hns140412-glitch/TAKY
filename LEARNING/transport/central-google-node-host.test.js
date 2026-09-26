'use strict';
const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Host=require('./central-google-node-host.js');
const Registry=require('./server-family-registry-provider.js');
const References=require('./server-specialist-reference-store.js');
const now=Date.UTC(2026,8,26,13),nowSec=Math.floor(now/1000);
const sub='GOOGLE_PARENT_SUB',clientId='TEST_WEB_CLIENT_ID';
const subjectHash=crypto.createHash('sha256').update('GOOGLE_OIDC:'+sub).digest('hex');
const baseRecord={
 authority:Registry.REGISTRY_AUTHORITY,version:1,identity_provider:'GOOGLE_OIDC',
 subject_sha256:subjectHash,status:'ACTIVE',
 expires_at:new Date(now+3600000).toISOString(),
 memberships:[{status:'ACTIVE',family_id:'F1',self_member_id:'PARENT_A',
  role:'PARENT',active_family_member_ids:['PARENT_A','CHILD_A','CHILD_B'],
  learning_evidence_submit_member_ids:['CHILD_A'],permissions:[]}]
};
const packet=(id,member='CHILD_A')=>({
 packet_id:'hide-seek:'+id,source_app:'hide-seek',
 context:{family_id:'F1',member_id:member,subject:'영어',concept_skill_target:'vocabulary'},
 event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-26T12:00:00.000Z',
  event_type:'RETRIEVAL_RESULT',payload:{member_id:member,subject:'영어',
  concept_skill_target:'vocabulary',instrument_version:'HIDE_CODE_RED_V1',
  memorySummary:{averageMemoryStrength:0.4}}}
});
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-host-composition-'));
 let server;
 try{
  const registryStore=await new LocalJsonStrongStore(path.join(root,'identity')).init();
  const evidenceStore=await new LocalJsonStrongStore(path.join(root,'evidence')).init();
  const referenceStore=await new LocalJsonStrongStore(path.join(root,'references')).init();
  const refScope={family_id:'F1',member_id:'CHILD_A',event_id:'host-ref-1',
   source_app:'hide-seek',reference_id:'server-assignment-host-ref-1'};
  await referenceStore.setJSON(References.assessmentKey(refScope),{
   ...refScope,authority:'TAKY_SERVER_ASSESSMENT_REFERENCE_V1',version:1,
   issuer_service:'CENTRAL_ASSESSMENT_ISSUER',issuer_authorized:true,
   status:'ACTIVE',subject:'영어',concept_skill_target:'vocabulary',
   expected_response:'apple',match_rule:'EXACT_NFC',
   instrument_version:'HIDE_CODE_RED_V1',
   issued_at:'2026-09-26T11:00:00.000Z',
   expires_at:'2026-09-26T14:00:00.000Z'
  },{onlyIfNew:true});
  const key=Registry.subjectRecordKey(sub);
  await registryStore.setJSON(key,baseRecord,{onlyIfNew:true});
  const host=Host.create({
   clientIds:[clientId],allowedOrigins:['https://hide.example.test'],
   registryStore,evidenceStore,referenceStore,now:()=>now,
   // TEST-ONLY ticket. Production must supply real google-auth-library.
   oauth2Client:{verifyIdToken:async()=>({getPayload:()=>({
    iss:'https://accounts.google.com',aud:clientId,sub,
    iat:nowSec-10,exp:nowSec+3600})})}
  });
  server=http.createServer(host.handler);
  await new Promise((resolve,reject)=>{server.once('error',reject);
   server.listen(0,'127.0.0.1',resolve)});
  const url='http://127.0.0.1:'+server.address().port+'/api/learning/evidence';
  const send=async p=>fetch(url,{method:'POST',headers:{
   'Authorization':'Bearer test-only-ticket-0001','Content-Type':'application/json',
   'Origin':'https://hide.example.test'},body:JSON.stringify(p)});
  const good=await send(packet('host-1'));
  const ack=await good.json();
  assert.equal(good.status,200,JSON.stringify(ack));
  assert.equal(ack.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  assert.equal(ack.storage_confirmed,true);
  assert.equal(ack.receipt_scope.member_id,'CHILD_A');
  const saved=await evidenceStore.getWithMetadata(
   'families/F1/members/CHILD_A/learning-engine/state-v1',{consistency:'strong',type:'json'});
  assert(saved?.etag);
  assert.equal(saved.data.observation_only.length,1);
  const p=packet('host-ref-1');
  p.event.payload.assessment_ref='server-assignment-host-ref-1';
  p.event.payload.response_text='apple';
  const verified=await send(p);
  const receipt=await verified.json();
  assert.equal(verified.status,200,JSON.stringify(receipt));
  assert.equal(receipt.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  assert.equal(receipt.packet_id,p.packet_id);
  assert.equal(receipt.event_id,p.event.event_id);
  const unknown=packet('host-unissued-1');
  unknown.event.payload.assessment_ref='server-assignment-host-ref-1';
  unknown.event.payload.response_text='apple';
  const unissued=await send(unknown);
  assert.equal((await unissued.json()).acknowledgement_kind,
   'OBSERVATION_INGEST_RECEIPT');
  const sibling=await send(packet('host-sibling-1','CHILD_B'));
  assert.equal(sibling.status,403);
  const old=await registryStore.getWithMetadata(key,{consistency:'strong',type:'json'});
  await registryStore.setJSON(key,{...baseRecord,status:'REVOKED'},{onlyIfMatch:old.etag});
  const revoked=await send(packet('host-revoked-1'));
  assert.equal(revoked.status,401);
  const unavailable=Host.create.bind(null,{clientIds:[clientId],registryStore,evidenceStore,
   allowedOrigins:[],oauth2Client:{verifyIdToken:async()=>null}});
  assert.throws(unavailable,/HOST_EXPLICIT_BROWSER_ORIGINS_REQUIRED/);
  assert(!JSON.stringify(ack).includes(sub));
  console.log('CENTRAL_GOOGLE_NODE_HOST_PASS: real loopback routing with server registry, durable observation ACK, sibling rejection, immediate registry revocation');
 }finally{
  if(server)await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));
  await fs.rm(root,{recursive:true,force:true});
 }
})().catch(e=>{console.error(e);process.exitCode=1});
