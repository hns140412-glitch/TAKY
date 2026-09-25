'use strict';
const assert=require('node:assert/strict');
const T=require('./authenticated-evidence-transport.js');

let writes=0;
const store={
  row:null,
  async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null},
  async setJSON(key,value,opts={}){
    writes++;
    this.row={data:value,etag:'e'+writes};
    return {modified:true,etag:this.row.etag};
  }
};
const packet={
  packet_id:'hide-seek:h1',
  source_app:'hide-seek',
  context:{family_id:'F1',member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary'},
  event:{source:'hide-seek',event_id:'h1',occurred_at:'2026-09-25T12:00:00.000Z',event_type:'RETRIEVAL_RESULT',payload:{
    member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary',instrument_version:'HIDE_CODE_RED_V1',
    verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',basis:'DETERMINISTIC_LOCAL_MATCH',outcome:1,reference_id:'word:h1'}
  }}
};

(async()=>{
  const denied=await T.ingestAuthenticated(store,packet,{authenticated:true,family_id:'F1',authorized_member_ids:['OTHER']});
  assert.equal(denied.ok,false);
  assert.equal(denied.reason,'TRANSPORT_NOT_AUTHORIZED');
  assert.equal(writes,0);

  const allowed=await T.ingestAuthenticated(store,packet,{authenticated:true,family_id:'F1',authorized_member_ids:['CHILD_A']});
  assert.equal(allowed.ok,true);
  assert.equal(allowed.authenticated_scope.family_id,'F1');
  assert.equal(allowed.authenticated_scope.member_id,'CHILD_A');
  assert.equal(allowed.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  assert.equal(writes,1);

  console.log('AUTHENTICATED_EVIDENCE_TRANSPORT_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
