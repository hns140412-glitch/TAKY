'use strict';
const assert=require('node:assert/strict');
const A=require('./durable-evidence-store-adapter.js');

const store={
  row:null,seq:0,conflict:false,
  async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null},
  async setJSON(key,value,opts={}){
    if(this.conflict){this.conflict=false;this.row={data:this.row.data,etag:'e'+(++this.seq)};return {modified:false}}
    if(opts.onlyIfNew&&this.row)return {modified:false};
    if(opts.onlyIfMatch&&this.row?.etag!==opts.onlyIfMatch)return {modified:false};
    const etag='e'+(++this.seq);this.row={key,data:value,etag};return {modified:true,etag};
  }
};
const packet=id=>({
  packet_id:'hide-seek:'+id,source_app:'hide-seek',
  context:{family_id:'F1',member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-25T12:00:00.000Z',event_type:'RETRIEVAL_RESULT',payload:{
    member_id:'A',subject:'영어',concept_skill_target:'vocabulary',instrument_version:'HIDE_CODE_RED_V1',
    verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',basis:'DETERMINISTIC_LOCAL_MATCH',outcome:1,reference_id:'word:'+id}
  }}
});
(async()=>{
  assert.equal(A.stateKey(packet('e1')),'families/F1/members/A/learning-engine/state-v1');
  const first=await A.ingestPacket(store,packet('e1'));
  assert.equal(first.ok,true);
  assert.equal(first.durable_store.conditional_write,'onlyIfNew');
  store.conflict=true;
  const second=await A.ingestPacket(store,packet('e2'));
  assert.equal(second.ok,true);
  assert.equal(second.durable_store.attempt,2);
  assert.equal(second.durable_store.conditional_write,'onlyIfMatch');
  assert.equal(A.selfValidate(second).ok,true);
  assert.equal((await A.ingestPacket(store,{packet_id:'x',context:{member_id:'A'}})).reason,'FAMILY_MEMBER_SCOPE_REQUIRED');
  console.log('DURABLE_EVIDENCE_STORE_ADAPTER_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
