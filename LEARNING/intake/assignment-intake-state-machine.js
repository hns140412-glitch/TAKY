'use strict';

const VERSION='TAKY_ASSIGNMENT_INTAKE_STATE_MACHINE_V1';
const clean=v=>String(v??'').trim();
const clone=v=>JSON.parse(JSON.stringify(v));
const validTime=v=>Number.isFinite(Date.parse(clean(v)));
const fail=reason=>({ok:false,reason});

function create({family_id,member_id,batch_id}={}){
  if(!clean(family_id)||!clean(member_id)||!clean(batch_id))return fail('ASSIGNMENT_CAPTURE_SCOPE_REQUIRED');
  return {ok:true,state:{
    schema:VERSION,family_id:clean(family_id),member_id:clean(member_id),batch_id:clean(batch_id),
    phase:'CAPTURING',captures:[],analysis:null,confirmed_assignment:null
  }};
}
function capture(stateInput={},input={}){
  const s=clone(stateInput);
  if(!['CAPTURING','RETAKE_REQUIRED'].includes(s.phase))return fail('CAPTURE_NOT_ALLOWED_IN_PHASE');
  const id=clean(input.capture_id),ref=clean(input.local_temp_ref);
  if(!id||!ref||!validTime(input.captured_at))return fail('DURABLE_LOCAL_CAPTURE_REQUIRED');
  if(s.captures.some(x=>x.capture_id===id))return fail('CAPTURE_ID_DUPLICATE');
  const order=s.captures.length?Math.max(...s.captures.map(x=>x.display_order))+1:1;
  s.captures.push({capture_id:id,local_temp_ref:ref,captured_at:new Date(Date.parse(input.captured_at)).toISOString(),display_order:order,status:'READY'});
  s.phase='CAPTURING';s.analysis=null;
  return {ok:true,state:s};
}
function requestAnalysis(stateInput={}){
  const s=clone(stateInput);
  if(s.phase!=='CAPTURING'||!s.captures.length)return fail('CAPTURE_BATCH_NOT_READY');
  s.phase='ANALYSIS_REQUESTED';
  s.analysis={requested_capture_ids:s.captures.map(x=>x.capture_id),results:null};
  return {ok:true,state:s};
}
function applyAnalysis(stateInput={},input={}){
  const s=clone(stateInput);
  if(s.phase!=='ANALYSIS_REQUESTED')return fail('ANALYSIS_NOT_REQUESTED');
  const rows=Array.isArray(input.results)?input.results:[];
  const requested=s.analysis?.requested_capture_ids||[];
  if(rows.length!==requested.length)return fail('ANALYSIS_RESULT_COVERAGE_REQUIRED');
  const ids=new Set();
  for(const r of rows){
    const id=clean(r.capture_id),quality=clean(r.quality).toUpperCase();
    if(!requested.includes(id)||ids.has(id)||!['PASS','RETAKE'].includes(quality))return fail('ANALYSIS_RESULT_INVALID');
    ids.add(id);
  }
  s.analysis={analysis_id:clean(input.analysis_id)||null,results:rows.map(r=>({
    capture_id:clean(r.capture_id),quality:clean(r.quality).toUpperCase(),reason:clean(r.reason)||null
  }))};
  s.phase=rows.some(r=>clean(r.quality).toUpperCase()==='RETAKE')?'RETAKE_REQUIRED':'REVIEW_REQUIRED';
  return {ok:true,state:s};
}
function retake(stateInput={},input={}){
  const s=clone(stateInput);
  if(s.phase!=='RETAKE_REQUIRED')return fail('RETAKE_NOT_REQUIRED');
  const target=clean(input.target_capture_id),id=clean(input.capture_id),ref=clean(input.local_temp_ref);
  const flagged=new Set((s.analysis?.results||[]).filter(x=>x.quality==='RETAKE').map(x=>x.capture_id));
  const idx=s.captures.findIndex(x=>x.capture_id===target);
  if(idx<0||!flagged.has(target))return fail('TARGETED_RETAKE_CAPTURE_REQUIRED');
  if(!id||!ref||!validTime(input.captured_at)||s.captures.some((x,i)=>i!==idx&&x.capture_id===id))
    return fail('DURABLE_LOCAL_RETAKE_REQUIRED');
  const old=s.captures[idx];
  s.captures[idx]={
    capture_id:id,local_temp_ref:ref,captured_at:new Date(Date.parse(input.captured_at)).toISOString(),
    display_order:old.display_order,status:'READY',replaces_capture_id:old.capture_id
  };
  s.phase='CAPTURING';s.analysis=null;
  return {ok:true,state:s};
}
function confirm(stateInput={},input={}){
  const s=clone(stateInput);
  if(s.phase!=='REVIEW_REQUIRED'||(s.analysis?.results||[]).some(x=>x.quality!=='PASS'))
    return fail('HUMAN_REVIEW_READY_BATCH_REQUIRED');
  const id=clean(input.assignment_id),title=clean(input.title),subject=clean(input.subject);
  if(!id||!title||!subject)return fail('CONFIRMED_ASSIGNMENT_FIELDS_REQUIRED');
  const now=validTime(input.confirmed_at)?new Date(Date.parse(input.confirmed_at)).toISOString():new Date().toISOString();
  const due=input.due_at==null?null:(validTime(input.due_at)?new Date(Date.parse(input.due_at)).toISOString():null);
  if(input.due_at!=null&&!due)return fail('ASSIGNMENT_DUE_AT_INVALID');
  const record={
    family_id:s.family_id,member_id:s.member_id,record_type:'ASSIGNMENT',record_id:id,
    source_app:'family-main',status:'CONFIRMED',recorded_at:now,due_at:due,
    payload:{
      title,subject,task_id:clean(input.task_id)||id,
      capture_batch_id:s.batch_id,
      capture_refs:s.captures.sort((a,b)=>a.display_order-b.display_order).map(x=>({
        capture_id:x.capture_id,local_temp_ref:x.local_temp_ref,display_order:x.display_order
      }))
    }
  };
  s.phase='CONFIRMED';s.confirmed_assignment={record_id:id,confirmed_at:now};
  return {ok:true,state:s,record};
}
module.exports=Object.freeze({VERSION,create,capture,requestAnalysis,applyAnalysis,retake,confirm});
