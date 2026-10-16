'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {verify}=require('./forming-approval-record-verifier');
const p=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'forming-approval-')),'receipt.json');
const good={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',artifact_id:'a',artifact_revision:'v1',evidence_ref:'decision:1',owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',approved_by:'TEST_FIXTURE',approved_at:'2026-10-12T00:00:00Z'};
try{
 assert.equal(verify(p,'a','v1'),null);
 fs.writeFileSync(p,JSON.stringify(good));
 assert.equal(verify(p,'a','v1').artifact_revision,'v1');
 assert.equal(verify(p,'a','v2'),null);
 assert.equal(verify(p,'b','v1'),null);
 for(const key of ['issuer','decision','evidence_ref','owner_namespace','target_consumer','approved_by','approved_at']){
  fs.writeFileSync(p,JSON.stringify({...good,[key]:''}));
  assert.equal(verify(p,'a','v1'),null,key);
 }
 fs.writeFileSync(p,'{broken');
 assert.equal(verify(p,'a','v1'),null);
 console.log('FORMING_APPROVAL_RECORD_VERIFIER: 12/12 PASS (fixtures only)');
}finally{fs.rmSync(path.dirname(p),{recursive:true,force:true});}
