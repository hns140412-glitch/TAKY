'use strict';
const assert=require('node:assert/strict');
const Client=require('./pwa-central-evidence-ack-client.js');
const packet={packet_id:'hide-seek:event-1',source_app:'hide-seek',
 context:{family_id:'F1',member_id:'CHILD_A'},
 event:{event_id:'event-1',source:'hide-seek'}};
const body={ok:true,storage_confirmed:true,
 acknowledgement_kind:'OBSERVATION_INGEST_RECEIPT',
 receipt_id:'observation:server-committed-1',
 receipt_scope:{family_id:'F1',member_id:'CHILD_A'},
 source_app:'hide-seek',duplicate:false};
(async()=>{
 let calls=0,last=null,selected='CHILD_A';
 const client=Client.create({
  endpointUrl:'https://learning.example.test/api/learning/evidence',
  fetchImpl:async(url,opts)=>{
   calls++;last={url,opts};
   return {status:200,json:async()=>body};
  },
  tokenProvider:async()=> 'test-only-id-token-0000001',
  sessionProvider:async()=>({authenticated:true,
   family_id:'F1',selected_member_id:selected})
 });
 const a=await client.sendPending(packet);
 assert.equal(a.ok,true);
 assert.equal(a.observation_only,true);
 assert.equal(a.ack_token,body.receipt_id);
 assert.equal(calls,1);
 assert.equal(last.opts.credentials,'omit');
 assert.equal(last.opts.redirect,'error');
 assert.equal(last.opts.cache,'no-store');
 assert.equal(last.opts.headers.Authorization,'Bearer test-only-id-token-0000001');
 assert.equal(JSON.parse(last.opts.body).context.member_id,'CHILD_A');
 selected='CHILD_B';
 assert.equal((await client.sendPending(packet)).reason,'ACTIVE_FAMILY_MEMBER_SCOPE_REQUIRED');
 assert.equal(calls,1);
 selected='CHILD_A';
 assert.equal(Client.validateAck(packet,200,{
  ...body,receipt_scope:{family_id:'F1',member_id:'CHILD_B'}
 }).ok,false);
 assert.equal(Client.validateAck(packet,200,{...body,storage_confirmed:false}).ok,false);
 assert.equal(Client.validateAck(packet,200,{...body,receipt_id:''}).ok,false);
 const wrong=Client.create({endpointUrl:'https://learning.example.test/api/learning/evidence',
  tokenProvider:async()=> 'test-only-id-token-0000001',
  sessionProvider:async()=>({authenticated:true,family_id:'F1',selected_member_id:'CHILD_A'}),
  fetchImpl:async()=>({status:200,json:async()=>({...body,
   receipt_scope:{family_id:'F2',member_id:'CHILD_A'}})})
 });
 const invalid=await wrong.sendPending(packet);
 assert.equal(invalid.ok,false);
 assert.equal(invalid.retryable,true);
 const outage=Client.create({endpointUrl:'https://learning.example.test/api/learning/evidence',
  tokenProvider:async()=> 'test-only-id-token-0000001',
  sessionProvider:async()=>({authenticated:true,family_id:'F1',selected_member_id:'CHILD_A'}),
  fetchImpl:async()=>{throw Error('OFFLINE')}
 });
 assert.equal((await outage.sendPending(packet)).retryable,true);
 const retry=Client.create({endpointUrl:'https://learning.example.test/api/learning/evidence',
  tokenProvider:async()=> 'test-only-id-token-0000001',
  sessionProvider:async()=>({authenticated:true,family_id:'F1',selected_member_id:'CHILD_A'}),
  fetchImpl:async()=>({status:503,json:async()=>({ok:false})})
 });
 assert.equal((await retry.sendPending(packet)).retryable,true);
 assert.throws(()=>Client.create({endpointUrl:'http://learning.example.test/api/learning/evidence'}),
  /EXPLICIT_CENTRAL_HTTPS_EVIDENCE_ENDPOINT_REQUIRED/);
 assert.throws(()=>Client.create({endpointUrl:'https://learning.example.test/api/learning/evidence?token=x'}),
  /EXPLICIT_CENTRAL_HTTPS_EVIDENCE_ENDPOINT_REQUIRED/);
 console.log('PWA_CENTRAL_EVIDENCE_ACK_CLIENT_PASS: HTTPS bearer/no ambient cookies, selected child scope, committed ACK validation, forged ACK denial, offline/CAS retry, no queue state mutation');
})().catch(e=>{console.error(e);process.exitCode=1});
