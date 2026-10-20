'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {readCurrentDecisionReceipt,classifyDecisionFailure}=require('./family_group_decision_receipt.cjs');
const make=()=>({suite:'USER_DECISION_INDEPENDENT_REGRESSION_V1',appCodeModified:false,syntheticFixture:true,
 checks:[{id:'USER_1001_ONDEVICE_OCR_FIRST',pass:false},{id:'USER_0922_LINK_THREE_STATES',pass:false},
         {id:'USER_0922_CATCH_SCOPE',pass:false},{id:'QA_NOT_PARITY',pass:false}],
 violations:['USER_1001_ONDEVICE_OCR_FIRST'],
 sourceGaps:['USER_0922_LINK_THREE_STATES','USER_0922_CATCH_SCOPE','QA_NOT_PARITY'],
 failed:['USER_1001_ONDEVICE_OCR_FIRST','USER_0922_LINK_THREE_STATES','USER_0922_CATCH_SCOPE','QA_NOT_PARITY'],pageErrors:[]});
function withFile(cb){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'taky-decision-proof-')),file=path.join(dir,'test.json');
 try{const save=x=>{fs.writeFileSync(file,JSON.stringify(x));return Date.now()-300;};return cb(file,save);}
 finally{fs.rmSync(dir,{recursive:true,force:true})}
}
test('fresh source differentiates 1 direct violation from 3 source-gaps without inventing approval',()=>withFile((file,save)=>{
 const stamp=save(make()),x=readCurrentDecisionReceipt(file,stamp);
 assert.equal(x.status,'FRESH_VALID');
 const gaps=classifyDecisionFailure(x);
 assert.equal(gaps.length,4);
 assert.equal(gaps.filter(v=>v.id.startsWith('hide-user-violation-')).length,1);
 assert.equal(gaps.filter(v=>v.id.startsWith('hide-source-gap-')).length,3);
 assert.equal(gaps.filter(v=>v.priority==='P0').length,2);
}));
test('stale preceding test never counts as this run',()=>withFile((file,save)=>{
 save(make());const then=new Date(Date.now()-180000);
 fs.utimesSync(file,then,then);
 const v=readCurrentDecisionReceipt(file,Date.now());
 assert.equal(v.status,'STALE_OR_MISSING');
 assert.equal(classifyDecisionFailure(v)[0].priority,'P0');
}));
test('source-gap cannot be moved into direct user violation bucket',()=>withFile((file,save)=>{
 const v=make();v.violations=['USER_1001_ONDEVICE_OCR_FIRST','QA_NOT_PARITY'];v.sourceGaps=v.sourceGaps.filter(x=>x!=='QA_NOT_PARITY');
 assert.equal(readCurrentDecisionReceipt(file,save(v)).status,'FAILURE_CATEGORY_MISMATCH');
}));
test('a passing test with omitted failures does not produce a verified receipt',()=>withFile((file,save)=>{
 const v=make();v.failed=[];
 assert.equal(readCurrentDecisionReceipt(file,save(v)).status,'FAILURE_PROVENANCE_MISMATCH');
}));
test('unknown failed ID cannot be dropped from QA',()=>withFile((file,save)=>{
 const v=make();v.violations.push('USER_UNKNOWN_RULE');
 v.failed.push('USER_UNKNOWN_RULE');v.checks.push({id:'USER_UNKNOWN_RULE',pass:false});
 const val=readCurrentDecisionReceipt(file,save(v));
 assert.equal(val.status,'FRESH_VALID');
 assert.equal(classifyDecisionFailure(val)[0].id,'hide-user-decision-unknown-contract-hold');
}));
test('duplicate missing bad JSON and browser errors all fail closed',()=>withFile((file,save)=>{
 assert.equal(readCurrentDecisionReceipt(file,Date.now()).status,'RECEIPT_UNREADABLE_HOLD');
 const v=make();v.failed.push('USER_1001_ONDEVICE_OCR_FIRST');
 assert.equal(readCurrentDecisionReceipt(file,save(v)).status,'FAILURE_PROVENANCE_MISMATCH');
 const w=make();w.checks.push(w.checks[0]);
 assert.equal(readCurrentDecisionReceipt(file,save(w)).status,'DUPLICATE_CHECK');
 const u=make();u.pageErrors=['browser crash'];
 assert.equal(readCurrentDecisionReceipt(file,save(u)).status,'BROWSER_ERROR_HOLD');
}));
