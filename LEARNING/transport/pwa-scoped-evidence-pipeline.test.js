'use strict';
const assert=require('node:assert/strict');
const Pipeline=require('./pwa-scoped-evidence-pipeline.js');
let data={entries:[]},version=0,selected='A',offline=true;
const storage={
 async read(){return {version,data:structuredClone(data)}},
 async compareAndSwap(v,next){if(v!==version)return false;
  data=structuredClone(next);version++;return true},
 async close(){}
};
const packet=id=>({packet_id:'hide-seek:'+id,source_app:'hide-seek',
 context:{family_id:'F',member_id:'A',subject:'english',concept_skill_target:'vocabulary'},
 event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-27T01:00:00Z',
 event_type:'RETRIEVAL_RESULT',payload:{member_id:'A'}}});
let calls=0;
const pipeline=Pipeline.create({
 storageAdapter:storage,endpointUrl:'https://central.example.test/api/learning/evidence',
 tokenProvider:async()=> 'test-bearer-1234567890',
 sessionProvider:async()=>({authenticated:true,family_id:'F',selected_member_id:selected}),
 fetchImpl:async(url,options)=>{
  calls++;assert.equal(options.credentials,'omit');
  if(offline)throw Error('OFFLINE');
  const p=JSON.parse(options.body);
  selected='B'; // Change during await: central ACK must not settle old member.
  return {status:200,json:async()=>({ok:true,storage_confirmed:true,
   acknowledgement_kind:'OBSERVATION_INGEST_RECEIPT',receipt_id:'central:'+p.event.event_id,
   receipt_scope:{family_id:'F',member_id:'A'},source_app:'hide-seek',
   packet_id:p.packet_id,event_id:p.event.event_id,duplicate:false})};
 }
});
(async()=>{
 assert.equal((await pipeline.enqueue(packet('one'))).queued,true);
 assert.equal((await pipeline.enqueue(packet('one'))).duplicate,true);
 await assert.rejects(()=>pipeline.enqueue({...packet('two'),context:{
  ...packet('two').context,member_id:'B'}}),/EVIDENCE_ENQUEUE_SESSION_SCOPE_MISMATCH/);
 assert.equal((await pipeline.flushOne('hide-seek','worker')).status,'PENDING');
 assert.equal((await pipeline.listActive('hide-seek'))[0].status,'PENDING');
 offline=false;
 assert.equal((await pipeline.flushOne('hide-seek','worker')).status,'PENDING');
 assert.equal((await pipeline.listActive('hide-seek')).length,0);
 await assert.rejects(()=>pipeline.enqueue(packet('two')),/EVIDENCE_ENQUEUE_SESSION_SCOPE_MISMATCH/);
 selected='A';
 assert.equal((await pipeline.listActive('hide-seek'))[0].status,'PENDING');
 assert.equal(calls,2);
 await pipeline.close();
 console.log('PWA_SCOPED_EVIDENCE_PIPELINE_PASS: authenticated enqueue, offline retry, member-switch no ACK, isolated active-member listing');
})().catch(e=>{console.error(e);process.exitCode=1});
