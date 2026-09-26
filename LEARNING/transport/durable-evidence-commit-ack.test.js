'use strict';
const assert=require('node:assert/strict');
const Durable=require('./durable-evidence-store-adapter.js');
const Pipeline=require('../intake/specialist-event-pipeline.js');
const packet={packet_id:'test:p1',source_app:'hide-seek',
  context:{family_id:'F1',member_id:'A',subject:'영어',concept_skill_target:'words'},
  event:{source:'hide-seek',event_id:'p1',occurred_at:'2026-09-26T13:00:00.000Z',
    payload:{member_id:'A',subject:'영어',concept_skill_target:'words',instrument_version:'V1'}}};
(async()=>{
  const noAck={async getWithMetadata(){return null},async setJSON(){return {}}};
  const missingAck=await Durable.ingestPacket(noAck,packet);
  assert.equal(missingAck.ok,false);
  assert.equal(missingAck.reason,'DURABLE_STORE_WRITE_UNCONFIRMED');

  let writes=0;
  const missingEtag={
    async getWithMetadata(){return {data:Pipeline.emptyState(),etag:null}},
    async setJSON(){writes++;return {modified:true,etag:'SHOULD_NEVER_WRITE'}}
  };
  await assert.rejects(()=>Durable.ingestPacket(missingEtag,packet),
    /EXISTING_STRONG_STATE_ETAG_REQUIRED/);
  assert.equal(writes,0);

  const conflicts={async getWithMetadata(){return null},
    async setJSON(key,value,opts){assert.equal(opts.onlyIfNew,true);return {modified:false,etag:'competing'}}};
  const conflict=await Durable.ingestPacket(conflicts,packet,{max_attempts:2});
  assert.equal(conflict.ok,false);
  assert.equal(conflict.reason,'DURABLE_STORE_CONFLICT_RETRY_EXHAUSTED');

  const valid={async getWithMetadata(){return null},
    async setJSON(key,value,opts){assert.equal(opts.onlyIfNew,true);return {modified:true,etag:'saved-strong-etag'}}};
  const success=await Durable.ingestPacket(valid,packet);
  assert.equal(success.ok,true);
  assert.equal(success.durable_store.etag,'saved-strong-etag');
  console.log('DURABLE_LEARNING_RECEIPT_ACK_PASS: no false ACK without ETag; no unconditional existing-state writes; conflict retry fail closed');
})().catch(e=>{console.error(e);process.exitCode=1});
