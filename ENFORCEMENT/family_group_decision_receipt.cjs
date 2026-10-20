'use strict';
// Original child UI contract receipt is the sole structured source of decision
// failures. Truncated stderr/stdout is not an authority source.
const fs=require('node:fs');
const path=require('node:path');

const IDS={
 USER_1001_ONDEVICE_OCR_FIRST:'P0',
 USER_0922_LINK_THREE_STATES:'P0',
 USER_0922_CATCH_SCOPE:'P1',
 QA_NOT_PARITY:'P1'
};
const SOURCE_GAPS=new Set(['USER_0922_LINK_THREE_STATES','USER_0922_CATCH_SCOPE','QA_NOT_PARITY']);
function readCurrentDecisionReceipt(file,startedMs){
 try{
  const stat=fs.statSync(file);
  // A previous failed run must never be joined to the current run.
  if(!stat.isFile()||stat.mtimeMs<startedMs-1500)return {status:'STALE_OR_MISSING'};
  const data=JSON.parse(fs.readFileSync(file,'utf8'));
  if(data.suite!=='USER_DECISION_INDEPENDENT_REGRESSION_V1'
    ||data.appCodeModified!==false||data.syntheticFixture!==true
    ||!Array.isArray(data.checks)||!Array.isArray(data.failed)
    ||!Array.isArray(data.violations)||!Array.isArray(data.sourceGaps)
    ||!Array.isArray(data.pageErrors))return {status:'BAD_RECEIPT_SCHEMA'};
  const chk=data.checks;
  if(chk.length<4||chk.length>60||chk.some(c=>!c||typeof c.id!=='string'||typeof c.pass!=='boolean'))return {status:'BAD_CHECK_SET'};
  const checkedIds=chk.map(c=>c.id);
  if(new Set(checkedIds).size!==checkedIds.length)return {status:'DUPLICATE_CHECK'};
  const categories=[...data.violations,...data.sourceGaps];
  if(categories.some(id=>typeof id!=='string')||new Set(categories).size!==categories.length)return {status:'DUPLICATE_OR_INVALID_RESULT'};
  if(data.sourceGaps.some(id=>!SOURCE_GAPS.has(id))||
     data.violations.some(id=>SOURCE_GAPS.has(id)))return {status:'FAILURE_CATEGORY_MISMATCH'};
  const failed=chk.filter(c=>!c.pass).map(c=>c.id);
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
