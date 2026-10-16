'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {verifyBoundApproval}=require('./forming-bound-approval');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'taky-forming-bound-'));
try{
 const approvals=path.join(root,'approved'),evidence=path.join(root,'evidence');
 fs.mkdirSync(approvals);fs.mkdirSync(evidence);
 const ev=path.join(evidence,'proof.txt');fs.writeFileSync(ev,'fixture-evidence');
 const sha=crypto.createHash('sha256').update(fs.readFileSync(ev)).digest('hex');
 const r={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',artifact_id:'A',artifact_revision:'R1',owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',approved_by:'FIXTURE',approved_at:'2026-10-12',evidence_ref:'proof.txt',evidence_sha256:sha};
 const f=path.join(approvals,'r.json'), opts={authorityRoot:approvals,evidenceRoot:evidence,independentAuthorityCheck:()=>true};
 fs.writeFileSync(f,JSON.stringify(r));
 assert.equal(verifyBoundApproval(f,'A','R1',opts).ok,true);
 assert.equal(verifyBoundApproval(f,'A','R2',opts).ok,false);
 assert.equal(verifyBoundApproval(f,'A','R1',{...opts,independentAuthorityCheck:null}).ok,false);
 assert.equal(verifyBoundApproval(f,'A','R1',{...opts,independentAuthorityCheck:()=>false}).ok,false);
 assert.equal(verifyBoundApproval(f,'A','R1',{...opts,authorityRoot:evidence}).ok,false);
 fs.writeFileSync(ev,'tampered');
 assert.equal(verifyBoundApproval(f,'A','R1',opts).ok,false);
 console.log('FORMING_BOUND_APPROVAL 6/6 PASS (fixture evidence, not production authority)');
}finally{fs.rmSync(root,{recursive:true,force:true});}
