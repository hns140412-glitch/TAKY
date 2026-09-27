'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Evidence=require('./central-learning-http-endpoint.js');
const Decision=require('./central-learning-decision-http-endpoint.js');
const Durable=require('./durable-evidence-store-adapter.js');

const family='F1',member='CHILD_A';
const scope={family_id:family,member_id:member,subject:'english',
 concept_skill_target:'vocabulary'};
const principal={authenticated:true,principal_id:'P1',families:[
 {family_id:family,self_member_id:'PARENT',authorized_member_ids:[member]}]};
const verify=async token=>{if(token!=='verified-bearer-token-0001')throw Error('INVALID');return principal;};
const headers={Authorization:'Bearer verified-bearer-token-0001','Content-Type':'application/json'};
const request=(path,input)=>({method:'POST',path,headers,body:JSON.stringify(input)});
const parse=r=>JSON.parse(r.body);
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-ready-hide-observe-'));
 try{
  const store=await new LocalJsonStrongStore(root).init();
  const evidence=Evidence.create({store,verifyBearerToken:verify});
  const decision=Decision.create({store,verifyBearerToken:verify});
  const summary={authority:'SPECIALIST_MEMORY_ADVISORY_ONLY',
   prioritySemantics:'ADVISORY_SIGNAL_NOT_DATE',
   averageMemoryStrength:41,reviewAdvisories:[
    {lexicalId:'word-a',nextReviewPriority:80,advisoryOnly:true}]};
  const packet={packet_id:'ready-set:ready-observation-1',source_app:'ready-set',
   context:scope,event:{source:'ready-set',event_id:'ready-observation-1',
    type:'READY_LEARNING_OBSERVATION',occurred_at:'2026-09-27T01:00:00.000Z',
    payload:{...scope,source_task_id:'task-1',observation_only:true,
     global_mastery_claim:false,evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
     instrument_version:'HIDE_SPECIALIST_RESULT_V1',
     forwarded_source_app:'hide-seek',ready_state:'COMPLETED',
     memorySummary:summary}}};
  const ack=await evidence.handle(request(Evidence.ENDPOINT,packet));
  assert.equal(ack.status,200,JSON.stringify(parse(ack)));
  assert.equal(parse(ack).acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  const entry=await store.getWithMetadata(Durable.stateKey({context:scope}),
   {type:'json',consistency:'strong'});
  assert.equal(entry.data.observation_only.length,1);
  const observed=entry.data.observation_only[0];
  assert.equal(observed.evidence_type,'MEMORY_RETRIEVAL_EVIDENCE');
  assert.equal(observed.memory.average_strength,41);
  assert.equal(observed.memory.review_advisories[0].lexicalId,'word-a');
  assert.equal(observed.raw_app_signals.forwarded_hide_observation,true);
  assert.equal(observed.verified_outcome,null);
  assert.equal(Object.keys(entry.data.scope_receipts).length,0);
  const result=await decision.handle(request(Decision.ENDPOINT,scope));
  assert.equal(result.status,200,JSON.stringify(parse(result)));
  assert.equal(parse(result).runtime_result.trace.verified_evidence_count,0);
  assert.equal(parse(result).runtime_result.decision.execution_status,
   'HOLD_FOR_MORE_RELIABLE_INTERPRETATION');
  const replay=await evidence.handle(request(Evidence.ENDPOINT,packet));
  assert.equal(parse(replay).duplicate,true);
  console.log('READY_HIDE_CENTRAL_OBSERVATION_PASS: memory evidence remains lossless observation without verified promotion or Planner dates');
 }finally{await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
