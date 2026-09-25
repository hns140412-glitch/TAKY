'use strict';
const assert=require('node:assert/strict');
const N=require('./netlify-blobs-transport-adapter.js');

let storeArgs=null,writes=0;
const store={
  row:null,
  async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null},
  async setJSON(key,value,opts={}){
    writes++;
    const etag='e'+writes;
    this.row={key,data:value,etag};
    return {modified:true,etag};
  }
};
const getStore=args=>{storeArgs=args;return store};
const packet={
  packet_id:'hide-seek:h1',source_app:'hide-seek',
  context:{family_id:'F1',member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary'},
  event:{source:'hide-seek',event_id:'h1',occurred_at:'2026-09-25T12:00:00.000Z',event_type:'RETRIEVAL_RESULT',payload:{
    member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary',instrument_version:'HIDE_CODE_RED_V1',
    verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',basis:'DETERMINISTIC_LOCAL_MATCH',outcome:1,reference_id:'word:h1'}
  }}
};

(async()=>{
  const allowed=N.create({
    getStore,
    resolveIdentity:async()=>({authenticated:true,family_id:'F1',authorized_member_ids:['CHILD_A']})
  });
  const ok=await allowed.ingest(packet,{});
  assert.equal(ok.ok,true);
  assert.equal(ok.transport_adapter,'TAKY_NETLIFY_BLOBS_TRANSPORT_ADAPTER_V1');
  assert.equal(ok.store_consistency,'strong');
  assert.equal(storeArgs.consistency,'strong');
  assert.equal(ok.deployment_authority,false);

  const before=writes;
  const denied=N.create({
    getStore,
    resolveIdentity:async()=>({authenticated:true,family_id:'F1',authorized_member_ids:['OTHER']})
  });
  const no=await denied.ingest(packet,{});
  assert.equal(no.ok,false);
  assert.equal(no.reason,'TRANSPORT_NOT_AUTHORIZED');
  assert.equal(writes,before);

  assert.throws(()=>N.create({getStore}),/IDENTITY_RESOLVER_REQUIRED/);
  console.log('NETLIFY_BLOBS_TRANSPORT_ADAPTER_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
