'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const crypto=require('node:crypto');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Probe=require('./central-store-conformance.js');
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-cas-probe-'));
 try{
  const store=await new LocalJsonStrongStore(root).init();
  const result=await Probe.probe({
   store,key:'validation/'+crypto.randomUUID(),parallel:12});
  assert.equal(result.ok,true);
  assert.equal(result.cas_winners,1);
  assert.equal(result.operational_certification,false);
  const broken={getWithMetadata:async()=>null,
   setJSON:async()=>({modified:true,etag:'bad'})};
  await assert.rejects(()=>Probe.probe({
   store:broken,key:'validation/broken123',parallel:4
  }),/CREATE_READBACK_NOT_STRONG/);
  await assert.rejects(()=>Probe.probe({store,key:'families/F1/members/A'}),
   /DISPOSABLE_VALIDATION_KEY_REQUIRED/);
  console.log('CENTRAL_STORE_CONFORMANCE_PASS: 12 competing CAS writers yield exactly one winner, strong readback, stale and duplicate write rejection; local fixture only');
 }finally{await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
