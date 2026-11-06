'use strict';
// Original child UI contract receipt is the sole structured source of decision
// failures. Truncated stderr/stdout is not an authority source.
const fs=require('node:fs');
const path=require('node:path');

const IDS={
 USER_1001_ONDEVICE_OCR_FIRST:'P0',
 USER_0922_LINK_THREE_STATES:'P0',
 LINK_REAL_SOURCE_COVERAGE:'P0',
 USER_0922_CATCH_SCOPE:'P1',
 QA_NOT_PARITY:'P1'
};
// LINK three-step touch flow was explicitly directed in 2026-09-22 user turns.
// A synthetic browser path may validate interaction logic, not actual source relations.
// Original chat-export SHA and real teaching content remain HOLD; never invent roots/scenes.
const SOURCE_GAPS=new Set(['USER_0922_CATCH_SCOPE','QA_NOT_PARITY','LINK_REAL_SOURCE_COVERAGE']);
const REQUIRED_IDS=new Set([
 'USER_0922_NAV_HOME_EXPLORE_CATCH','USER_1001_ENGLISH_DEFAULT_OPTIONAL_SIX',
 'USER_1001_SIX_SUBJECTS','USER_12_24_COMPOSITION_SOURCE_PROVENANCE',
 'USER_0922_FIRST_TRACE_NEW_ONLY','FIRST_FIND_RETRIEVAL_NOT_SIMPLY_EXPOSURE',
 'USER_0922_LINK_THREE_STATES','LINK_REAL_SOURCE_COVERAGE',
 'LINK_SOURCE_BACKED_THREE_STEP_BROWSER','USER_0922_NO_MANDATORY_LINEAR_COURSE',
 'USER_0922_CATCH_SCOPE','USER_1001_ONDEVICE_OCR_FIRST',
 'ASSISTANT_MASTER_GOVERNANCE_UNVERIFIED','QA_NOT_PARITY'
]);
function readCurrentDecisionReceipt(file,startedMs,expectedRunId){
 try{
  const stat=fs.statSync(file);
  // Receipt identity, not mtime proximity, must match the exact invoking QA run.
  if(!Number.isFinite(startedMs)||startedMs<=0||!expectedRunId||typeof expectedRunId!=='string')
   return {status:'RUN_PROVENANCE_MISSING'};
  if(!stat.isFile()||!Number.isFinite(stat.mtimeMs)||stat.mtimeMs<startedMs||
     stat.mtimeMs>Date.now()+2000)return {status:'STALE_OR_MISSING'};
  const data=JSON.parse(fs.readFileSync(file,'utf8'));
  if(data.sourceRunId!==expectedRunId)return {status:'RUN_ID_MISMATCH'};
  if(data.suite!=='USER_DECISION_INDEPENDENT_REGRESSION_V1'
    ||data.appCodeModified!==false||data.syntheticFixture!==true
    ||!Array.isArray(data.checks)||!Array.isArray(data.failed)
    ||!Array.isArray(data.violations)||!Array.isArray(data.sourceGaps)
    ||!Array.isArray(data.pageErrors))return {status:'BAD_RECEIPT_SCHEMA'};
  const chk=data.checks;
  if(chk.length<4||chk.length>60||chk.some(c=>!c||typeof c.id!=='string'||typeof c.pass!=='boolean'))return {status:'BAD_CHECK_SET'};
  const checkedIds=chk.map(c=>c.id);
  if(new Set(checkedIds).size!==checkedIds.length)return {status:'DUPLICATE_CHECK'};
  if(checkedIds.length!==REQUIRED_IDS.size||checkedIds.some(id=>!REQUIRED_IDS.has(id)))
   return {status:'REQUIRED_CHECK_SET_MISMATCH'};
  // This suite is explicitly synthetic, so it cannot certify real original LINK relations.
  const relation=chk.find(c=>c.id==='LINK_REAL_SOURCE_COVERAGE');
  if(relation.pass!==false||!data.sourceGaps.includes('LINK_REAL_SOURCE_COVERAGE'))
   return {status:'REAL_CONTENT_UNVERIFIED_HOLD'};
  const categories=[...data.violations,...data.sourceGaps];
  if(categories.some(id=>typeof id!=='string')||new Set(categories).size!==categories.length)return {status:'DUPLICATE_OR_INVALID_RESULT'};
  if(data.sourceGaps.some(id=>!SOURCE_GAPS.has(id))||
     data.violations.some(id=>SOURCE_GAPS.has(id)))return {status:'FAILURE_CATEGORY_MISMATCH'};
  const failed=chk.filter(c=>!c.pass).map(c=>c.id);
  if(new Set(data.failed).size!==data.failed.length)return {status:'DUPLICATE_OR_INVALID_RESULT'};
  const eq=(a,b)=>a.length===b.length&&a.every(v=>b.includes(v));
  if(!eq(data.failed,failed)||!eq(categories,failed))return {status:'FAILURE_PROVENANCE_MISMATCH'};
  if(data.pageErrors.length)return {status:'BROWSER_ERROR_HOLD'};
  return {status:'FRESH_VALID',violations:data.violations,sourceGaps:data.sourceGaps,
    unrecognized:failed.filter(id=>!Object.hasOwn(IDS,id))};
 }catch{return {status:'RECEIPT_UNREADABLE_HOLD'};}
}
function classifyDecisionFailure(receipt){
 if(receipt.status!=='FRESH_VALID')return [{id:'hide-user-decision-evidence-'+receipt.status.toLowerCase().replaceAll('_','-'),priority:'P0',area:'HIDE',why:'독립검증 결과 영수증 최신성/구조 불명 · 재검토 필요'}];
 if(receipt.unrecognized.length)return [{id:'hide-user-decision-unknown-contract-hold',priority:'P0',area:'HIDE',why:'등록되지 않은 실패 계약 ID 발견 · 소스 대조 필수'}];
 return [
  ...receipt.violations.map(id=>({id:'hide-user-violation-'+id.toLowerCase().replaceAll('_','-'),priority:IDS[id],area:'HIDE',why:'현재 화면·코드와 사용자 원본 결정 직접 불일치: '+id})),
  ...receipt.sourceGaps.map(id=>({id:'hide-source-gap-'+id.toLowerCase().replaceAll('_','-'),priority:IDS[id],area:'HIDE',why:'원문·시안 세부 승인 근거 부족; 구현 실패나 사용자 거부로 단정 금지: '+id}))
 ];
}
module.exports={readCurrentDecisionReceipt,classifyDecisionFailure};
