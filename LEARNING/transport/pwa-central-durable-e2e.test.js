'use strict';
/** Entire staged browser-queue -> authenticated HTTP -> durable server -> ACK path.
 * Local fixtures only; no real OAuth, network, product repo or deployment. */
const assert=require('node:assert/strict');
const fs=require('node:fs').promises,os=require('node:os'),path=require('node:path');
const {webcrypto}=require('node:crypto');
const Pipeline=require('./pwa-scoped-evidence-pipeline.js');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const HTTP=require('./central-learning-http-endpoint.js');
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-pwa-to-central-'));
 try{
  const centralStore=await new LocalJsonStrongStore(root).init();
  const principal={authenticated:true,principal_id:'PARENT_A',identity_provider:'FIXTURE_VERIFIER',
   families:[{family_id:'F',self_member_id:'PARENT_A',authorized_member_ids:['A']}]};
  let allowToken=true,selected='A',serverCalls=0;
  const endpoint=HTTP.create({
   store:centralStore,
   verifyBearerToken:async token=>{
    if(!allowToken||token!=='fixture-verified-bearer-00001')throw Error('INVALID_TOKEN');
    return principal;
   }
  });
  let state={entries:[]},version=0;
  const storage={
   async read(){return {version,data:structuredClone(state)}},
   async compareAndSwap(expected,next){
    if(expected!==version)return false;
    state=structuredClone(next);version++;return true;
   },
   async close(){}
  };
  const pipeline=Pipeline.create({
   storageAdapter:storage,cryptoProvider:webcrypto,
   endpointUrl:'https://central.example.test/api/learning/evidence',
   tokenProvider:async()=> 'fixture-verified-bearer-00001',
   sessionProvider:async()=>({
    authenticated:true,family_id:'F',selected_member_id:selected
   }),
   fetchImpl:async(url,options)=>{
    serverCalls++;
    assert.equal(options.credentials,'omit');
    assert.equal(options.redirect,'error');
    const result=await endpoint.handle({
     method:options.method,path:new URL(url).pathname,
     headers:options.headers,body:options.body
    });
    return {status:result.status,json:async()=>JSON.parse(result.body)};
   }
  });
  const raw=id=>({
   source:'hide-seek',event_type:'LEARNING_MEMORY_SIGNAL',type:'LEARNING_MEMORY_SIGNAL',
   event_id:id,occurred_at:'2026-09-27T01:00:00.000Z',child_id:'A',
   payload:{member_id:'A',subject:'english',concept_skill_target:'vocabulary',
    learning_target_id:'word-1',observation_only:true,global_mastery_claim:false,
    correct:true,assisted:false}
  });
  assert.equal((await pipeline.enqueueBridge('hide-seek',raw('bridge-e1'))).queued,true);
  const sent=await pipeline.flushOne('hide-seek','fixture-worker');
  assert.deepEqual({processed:sent.processed,status:sent.status,reason:sent.reason},
   {processed:true,status:'ACKED',reason:'CENTRAL_ACK_VALIDATED'});
  let rows=await pipeline.listActive('hide-seek');
  assert.equal(rows.length,1);
  assert.equal(rows[0].status,'ACKED');
  assert.equal(rows[0].receipt.kind,'OBSERVATION_INGEST_RECEIPT');
  const saved=await centralStore.getWithMetadata(
   'families/F/members/A/learning-engine/state-v1',{type:'json',consistency:'strong'});
  assert(saved?.etag);
  assert.equal(saved.data.observation_only.length,1);
  assert.equal(saved.data.observation_only[0].event_id,'bridge-e1');
  assert.equal(Object.keys(saved.data.scope_receipts||{}).length,0); // Never claim verified mastery.
  assert.equal((await pipeline.enqueueBridge('hide-seek',raw('bridge-e1'))).duplicate,true);
  assert.equal((await pipeline.flushOne('hide-seek','fixture-worker')).processed,false);
  assert.equal(serverCalls,1);
  const snap={
   source:'snap-pop',event_type:'LEARNING_OUTCOME',type:'LEARNING_OUTCOME',
   event_id:'snap-e1',occurred_at:'2026-09-27T01:01:00.000Z',
   payload:{member_id:'A',subject:'english',concept_skill_target:'vocabulary',
    contextual_evidence_only:true,global_mastery_claim:false,
    completed:true,evidence_of_improvement:true}
  };
  assert.equal((await pipeline.enqueueBridge('snap-pop',snap)).queued,true);
  assert.equal((await pipeline.flushOne('snap-pop','fixture-worker')).status,'ACKED');
  assert.equal((await pipeline.listActive('snap-pop'))[0].receipt.kind,'OBSERVATION_INGEST_RECEIPT');
  assert.equal((await pipeline.enqueueReadyObservation({
   event_id:'ready-e1',occurred_at:'2026-09-27T01:02:00.000Z',member_id:'A',
   payload:{member_id:'A',subject:'english',concept_skill_target:'vocabulary',
    observation_only:true,practice_completed:true}
  })).queued,true);
  assert.equal((await pipeline.flushOne('ready-set','fixture-worker')).status,'ACKED');
  assert.equal((await pipeline.listActive('ready-set'))[0].receipt.kind,'OBSERVATION_INGEST_RECEIPT');
  assert.equal(serverCalls,3);
  const all=await centralStore.getWithMetadata(
   'families/F/members/A/learning-engine/state-v1',{type:'json',consistency:'strong'});
  assert.deepEqual(new Set(all.data.observation_only.map(x=>x.event_id)),
   new Set(['bridge-e1','snap-e1','ready-e1']));
  assert.equal(Object.keys(all.data.scope_receipts||{}).length,0);
  await assert.rejects(()=>pipeline.enqueueBridge('hide-seek',{
   ...raw('missing-skill'),payload:{...raw('missing-skill').payload,concept_skill_target:null}
  }),/BRIDGE_LEARNING_SCOPE_MISSING_HOLD/);
  selected='B';
  await assert.rejects(()=>pipeline.enqueueBridge('hide-seek',raw('cross-member')),
   /SPECIALIST_EVENT_MEMBER_SCOPE_MISMATCH/);
  assert.equal((await pipeline.listActive('hide-seek')).length,0);
  selected='A';allowToken=false;
  assert.equal((await pipeline.enqueueBridge('hide-seek',raw('bad-token'))).queued,true);
  const denied=await pipeline.flushOne('hide-seek','fixture-worker');
  assert.equal(denied.status,'BLOCKED');
  rows=await pipeline.listActive('hide-seek');
  assert.equal(rows.find(x=>x.key==='hide-seek:hide-seek:bad-token').status,'BLOCKED');
  assert.equal((await centralStore.getWithMetadata(
   'families/F/members/A/learning-engine/state-v1',
   {type:'json',consistency:'strong'})).data.observation_only.length,3);
  await pipeline.close();
  console.log('PWA_CENTRAL_DURABLE_E2E_PASS: Hide Snap Ready events -> scoped outbox -> bearer/family HTTP -> durable observation -> exact ACK; replay, scope, missing skill and invalid-token gates');
 }finally{await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
