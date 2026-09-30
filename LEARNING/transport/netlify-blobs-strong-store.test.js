'use strict';

const assert=require('node:assert/strict');
const Strong=require('./netlify-blobs-strong-store.js');
const Decision=require('./central-learning-decision-http-endpoint.js');

(async()=>{
  let storeArgs=null,lastReadOpts=null,lastWriteOpts=null;
  const inner={
    row:null,
    async getWithMetadata(key,opts){
      lastReadOpts=opts;
      if(!this.row)return null;
      return {data:this.row.data,etag:this.row.etag};
    },
    async setJSON(key,value,opts){
      lastWriteOpts=opts;
      this.row={key,data:value,etag:'etag-1'};
      return {modified:true,etag:'etag-1'};
    }
  };
  const store=Strong.create({
    getStore:args=>{storeArgs=args;return inner;},
    store_name:'taky-central-prod',
    region:'ap-northeast-2'
  });
  assert.deepEqual(storeArgs,{name:'taky-central-prod',consistency:'strong',region:'ap-northeast-2'});
  assert.equal(store.consistency,'strong');
  assert.equal(await store.getWithMetadata('missing',{type:'json'}),null);

  const saved=await store.setJSON('k',{hello:'world'},{onlyIfNew:true});
  assert.equal(saved.modified,true);assert.equal(saved.etag,'etag-1');
  assert.deepEqual(lastWriteOpts,{onlyIfNew:true});
  const got=await store.getWithMetadata('k',{type:'json',consistency:'strong'});
  assert.deepEqual(got,{data:{hello:'world'},etag:'etag-1',consistency:'strong',type:'json'});
  assert.equal(lastReadOpts.type,'json');

  const endpoint=Decision.create({
    verifyBearerToken:async()=>({
      authenticated:true,principal_id:'test-parent',
      families:[{family_id:'F1',self_member_id:'PARENT_A',authorized_member_ids:['PARENT_A','CHILD_A']}]
    }),
    store,
    resolveIndexedEvidence:async()=>null,
    independentIndexOwnerVerifier:()=>null
  });
  const response=await endpoint.handle({
    method:'POST',path:'/api/learning/decision',
    headers:{'Content-Type':'application/json','Authorization':'Bearer valid-test-bearer-0001'},
    body:JSON.stringify({family_id:'F1',member_id:'CHILD_A',
      subject:'math',concept_skill_target:'fractions'})
  });
  assert.equal(response.status,503);
  // The stored arbitrary row above is deliberately not a valid Learning state.
  // This proves the decision endpoint receives the wrapper's strong metadata and fails closed.

  assert.throws(()=>Strong.create({}),/GET_STORE_REQUIRED/);
  assert.throws(()=>Strong.create({getStore:()=>({})}),/NETLIFY_STRONG_STORE_INTERFACE_REQUIRED/);
  const bad=Strong.create({getStore:()=>({
    async getWithMetadata(){return {data:{}};},
    async setJSON(){return {modified:true};}
  })});
  await assert.rejects(()=>bad.getWithMetadata('x'),/NETLIFY_STRONG_READ_METADATA_INVALID/);
  await assert.rejects(()=>bad.setJSON('x',{}),/NETLIFY_STRONG_WRITE_ETAG_REQUIRED/);

  console.log('NETLIFY_BLOBS_STRONG_STORE_PASS: strong metadata wrapper, conditional write forwarding and decision fail-closed');
})().catch(e=>{console.error(e);process.exitCode=1});