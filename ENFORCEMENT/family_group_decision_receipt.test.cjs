'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {readCurrentDecisionReceipt,classifyDecisionFailure}=require('./family_group_decision_receipt.cjs');
const RUN='unit-test-verified-source-run';
const IDS=[
 'USER_0922_NAV_HOME_EXPLORE_CATCH','USER_1001_ENGLISH_DEFAULT_OPTIONAL_SIX',
 'USER_1001_SIX_SUBJECTS','USER_12_24_COMPOSITION_SOURCE_PROVENANCE',
 'USER_0922_FIRST_TRACE_NEW_ONLY','FIRST_FIND_RETRIEVAL_NOT_SIMPLY_EXPOSURE',
 'USER_0922_LINK_THREE_STATES','LINK_REAL_SOURCE_COVERAGE',
 'LINK_SOURCE_BACKED_THREE_STEP_BROWSER','USER_0922_NO_MANDATORY_LINEAR_COURSE',
 'USER_0922_CATCH_SCOPE','USER_1001_ONDEVICE_OCR_FIRST',
 'ASSISTANT_MASTER_GOVERNANCE_UNVERIFIED','QA_NOT_PARITY'
];
const GAPS=['LINK_REAL_SOURCE_COVERAGE','USER_0922_CATCH_SCOPE','QA_NOT_PARITY'];
const DIRECT=['USER_1001_ONDEVICE_OCR_FIRST','USER_0922_LINK_THREE_STATES'];
function make(){
 const failed=[...DIRECT,...GAPS];
 return {
  suite:'USER_DECISION_INDEPENDENT_REGRESSION_V1',
  sourceRunId:RUN,appCodeModified:false,syntheticFixture:true,
  checks:IDS.map(id=>({id,pass:!failed.includes(id)})),
  violations:[...DIRECT],sourceGaps:[...GAPS],failed,pageErrors:[]
 };
}
function withFile(fn){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'taky-decision-proof-')),file=path.join(dir,'test.json');
 const save=(data)=>{fs.writeFileSync(file,JSON.stringify(data),'utf8');return Date.now()-100;};
 const read=(timestamp,runId=RUN)=>readCurrentDecisionReceipt(file,timestamp,runId);
 try{return fn({file,save,read});}finally{fs.rmSync(dir,{recursive:true,force:true});}
}
test('direct violations and unresolved source evidence retain separate priorities',()=>withFile(({save,read})=>{
 const r=read(save(make()));assert.equal(r.status,'FRESH_VALID');
 const issues=classifyDecisionFailure(r);
 assert.equal(issues.length,5);
 assert.equal(issues.filter(i=>i.id.startsWith('hide-user-violation-')).length,2);
 assert.equal(issues.filter(i=>i.id.startsWith('hide-source-gap-')).length,3);
 assert.equal(issues.filter(i=>i.priority==='P0').length,3);
}));
test('synthetic three-stage LINK pass never clears original-source P0 hold',()=>withFile(({save,read})=>{
 const v=make();const id='USER_0922_LINK_THREE_STATES';
 v.checks.find(c=>c.id===id).pass=true;v.violations=v.violations.filter(x=>x!==id);v.failed=v.failed.filter(x=>x!==id);
 const r=read(save(v));assert.equal(r.status,'FRESH_VALID');
 const issues=classifyDecisionFailure(r);
 assert.ok(issues.some(i=>i.id==='hide-source-gap-link-real-source-coverage'&&i.priority==='P0'));
 assert.ok(!issues.some(i=>i.id==='hide-user-violation-user-0922-link-three-states'));
}));
test('missing source coverage fails closed even when all other checks pass',()=>withFile(({save,read})=>{
 const v=make();v.checks=v.checks.filter(x=>x.id!=='LINK_REAL_SOURCE_COVERAGE');
 v.sourceGaps=v.sourceGaps.filter(x=>x!=='LINK_REAL_SOURCE_COVERAGE');
 v.failed=v.failed.filter(x=>x!=='LINK_REAL_SOURCE_COVERAGE');
 assert.equal(read(save(v)).status,'REQUIRED_CHECK_SET_MISMATCH');
}));
test('forged synthetic real-content PASS fails closed regardless of claims',()=>withFile(({save,read})=>{
 const v=make();v.checks.find(c=>c.id==='LINK_REAL_SOURCE_COVERAGE').pass=true;
 v.sourceGaps=v.sourceGaps.filter(x=>x!=='LINK_REAL_SOURCE_COVERAGE');
 v.failed=v.failed.filter(x=>x!=='LINK_REAL_SOURCE_COVERAGE');
 assert.equal(read(save(v)).status,'REAL_CONTENT_UNVERIFIED_HOLD');
}));
test('all-pass fabricated contract fails closed',()=>withFile(({save,read})=>{
 const v=make();v.checks=v.checks.map(x=>({...x,pass:true}));v.violations=[];v.sourceGaps=[];v.failed=[];
 assert.equal(read(save(v)).status,'REAL_CONTENT_UNVERIFIED_HOLD');
}));
test('unknown passing/failed check cannot hide missing required contract',()=>withFile(({save,read})=>{
 const passing=make();passing.checks=passing.checks.slice(1);
 passing.checks.push({id:'UNREGISTERED_GREEN_CHECK',pass:true});
 assert.equal(read(save(passing)).status,'REQUIRED_CHECK_SET_MISMATCH');
 const failing=make();failing.checks.push({id:'USER_UNKNOWN_RULE',pass:false});
 failing.violations.push('USER_UNKNOWN_RULE');failing.failed.push('USER_UNKNOWN_RULE');
 assert.equal(read(save(failing)).status,'REQUIRED_CHECK_SET_MISMATCH');
}));
test('recent preceding run with plausible mtime is rejected by exact run id',()=>withFile(({save,read})=>{
 const v=make();v.sourceRunId='previous-run';
 assert.equal(read(save(v)).status,'RUN_ID_MISMATCH');
}));
test('missing or nonfinite expected run provenance fails closed',()=>withFile(({save,read,file})=>{
 const stamp=save(make());
 assert.equal(readCurrentDecisionReceipt(file,stamp).status,'RUN_PROVENANCE_MISSING');
 assert.equal(read(Number.NaN).status,'RUN_PROVENANCE_MISSING');
 assert.equal(read(0).status,'RUN_PROVENANCE_MISSING');
}));
test('stale preceding test and future timestamp never count',()=>withFile(({file,save,read})=>{
 save(make());const before=new Date(Date.now()-180000);fs.utimesSync(file,before,before);
 assert.equal(read(Date.now()).status,'STALE_OR_MISSING');
 save(make());const future=new Date(Date.now()+120000);fs.utimesSync(file,future,future);
 assert.equal(read(Date.now()-100).status,'STALE_OR_MISSING');
}));
test('source gap cannot be relabeled direct user violation',()=>withFile(({save,read})=>{
 const v=make();v.violations.push('QA_NOT_PARITY');v.sourceGaps=v.sourceGaps.filter(x=>x!=='QA_NOT_PARITY');
 assert.equal(read(save(v)).status,'FAILURE_CATEGORY_MISMATCH');
}));
test('omitted and duplicate failure records fail closed',()=>withFile(({save,read})=>{
 const missing=make();missing.failed=[];
 assert.equal(read(save(missing)).status,'FAILURE_PROVENANCE_MISMATCH');
 const duplicate=make();duplicate.failed.push(missing.violations[0]);
 assert.equal(read(save(duplicate)).status,'DUPLICATE_OR_INVALID_RESULT');
 const repeated=make();repeated.checks.push(repeated.checks[0]);
 assert.equal(read(save(repeated)).status,'DUPLICATE_CHECK');
}));
test('browser errors and missing JSON remain HOLD',()=>withFile(({file,save,read})=>{
 assert.equal(read(Date.now()).status,'RECEIPT_UNREADABLE_HOLD');
 const v=make();v.pageErrors.push('browser exception');
 assert.equal(read(save(v)).status,'BROWSER_ERROR_HOLD');
}));
