'use strict';
const assert=require('node:assert/strict');
const Outbox=require('./scoped-evidence-outbox.js');
const Client=require('./pwa-central-evidence-ack-client.js');
let state={entries:[]},version=0,now=1000,selected='A',offline=true;
const storage={
 async read(){return {version,data:structuredClone(state)}},
 async compareAndSwap(expected,next){
  if(expected!==version)return false;
  state=structuredClone(next);version++;return true;
 }
};
const packet=id=>({packet_id:'hide-seek:'+id,source_app:'hide-seek',
 context:{family_id:'F',member_id:'A'},
 event:{source:'hide-seek',event_id:id}});
const scope=['F','A','hide-seek'];
(async()=>{
 const q=Outbox.create({storage,clock:()=>now,leaseMs:1000});
 const p=packet('one');
 assert.equal((await q.enqueue(p)).queued,true);
 assert.equal((await q.enqueue(p)).duplicate,true);
 await assert.rejects(()=>q.enqueue({...p,event:{...p.event,event_id:'changed'}}),
  /OUTBOX_PACKET_ID_CONTENT_CONFLICT/);
 const c1=await q.claim(scope,'worker-1');
 assert.equal((await q.claim(scope,'worker-2')),null);
 assert.equal((await q.settle({...c1,owner:'worker-2'},{ok:true})).updated,false);
 const client=Client.create({
  endpointUrl:'https://learning.example.test/api/learning/evidence',
  tokenProvider:async()=> 'fixture-token-000000001',
  sessionProvider:async()=>({authenticated:true,family_id:'F',selected_member_id:selected}),
  fetchImpl:async()=>{
   if(offline)throw Error('OFFLINE');
   return {status:200,json:async()=>({
    ok:true,storage_confirmed:true,acknowledgement_kind:'OBSERVATION_INGEST_RECEIPT',
    receipt_id:'central:one',receipt_scope:{family_id:'F',member_id:'A'},
    source_app:'hide-seek',packet_id:p.packet_id,event_id:p.event.event_id,
    duplicate:false
   })};
  }
 });
 const failure=await client.sendPending(c1.packet);
 assert.equal(failure.retryable,true);
 assert.equal((await q.settle(c1,failure)).status,'PENDING');
 const c2=await q.claim(scope,'worker-2');
 offline=false;selected='B';
 const switched=await client.sendPending(c2.packet);
 assert.equal(switched.ok,false);
 assert.equal((await q.settle(c2,switched)).status,'BLOCKED');
 selected='A';
 // Explicit resumption after authenticated member selection, not automatic
 // cross-account flush. A blocked record requires owner-scoped recovery.
 assert.equal((await q.claim(scope,'worker-3')),null);
 assert.equal((await q.list(scope))[0].status,'BLOCKED');
 const p2=packet('two');await q.enqueue(p2);
 const c3=await q.claim(scope,'worker-3');
 const forged={ok:true,ack_token:'forged',acknowledgement_kind:'REAL_EVIDENCE_RECEIPT',
  packet_id:p.packet_id,event_id:p.event.event_id};
 assert.equal((await q.settle(c3,forged)).reason,'UNBOUND_ACK_DENIED');
 const valid2=Client.validateAck(p2,200,{
  ok:true,storage_confirmed:true,acknowledgement_kind:'REAL_EVIDENCE_RECEIPT',
  receipt_id:'central:two',receipt_scope:{family_id:'F',member_id:'A'},
  source_app:'hide-seek',packet_id:p2.packet_id,event_id:p2.event.event_id,duplicate:false
 });
 assert.equal(valid2.ok,true);
 assert.equal((await q.settle(c3,valid2)).status,'ACKED');
 assert.equal((await q.list(scope))[1].receipt.receipt_id,'central:two');
 assert.equal((await q.list(['F','B','hide-seek'])).length,0);
 const p3=packet('three');await q.enqueue(p3);
 const old=await q.claim(scope,'old');now+=1001;
 const replacement=await q.claim(scope,'replacement');
 assert.equal((await q.settle(old,valid2)).updated,false);
 assert.equal(replacement.owner,'replacement');
 console.log('SCOPED_EVIDENCE_OUTBOX_PASS: atomic enqueue/dedupe, exclusive lease, offline retry, account switch block, mismatched ACK denial, exact ACK commit, expired lease takeover');
})().catch(e=>{console.error(e);process.exitCode=1});
