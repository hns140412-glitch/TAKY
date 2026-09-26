'use strict';

const ASSET_STATES=new Set(['UNBOUND','REVIEWED_ASSET','APPROVED_RUNTIME_ASSET']);
const APPROVED='APPROVED_RUNTIME_ASSET';

function clean(v){ return typeof v==='string'?v.trim():''; }

function validateEntry(entry={}){
  const issues=[];
  if(!clean(entry.draft_id))issues.push('DRAFT_ID_REQUIRED');
  if(!clean(entry.visual_id))issues.push('VISUAL_ID_REQUIRED');
  if(!ASSET_STATES.has(clean(entry.asset_state)))issues.push('ASSET_STATE_INVALID');

  const approved=entry.asset_state===APPROVED || entry.approval_status===APPROVED;
  if(approved){
    if(entry.asset_state!==APPROVED || entry.approval_status!==APPROVED)issues.push('APPROVAL_STATE_MISMATCH');
    if(!clean(entry.asset_path))issues.push('APPROVED_ASSET_PATH_REQUIRED');
    if(!Array.isArray(entry.approval_evidence_refs)||entry.approval_evidence_refs.length===0)issues.push('APPROVAL_EVIDENCE_REQUIRED');
  }

  if(entry.active===true && !approved)issues.push('UNAPPROVED_VISUAL_CANNOT_ACTIVATE');
  if(entry.renderer_binding===true && !approved)issues.push('UNAPPROVED_VISUAL_CANNOT_BIND_RENDERER');

  return {ok:issues.length===0,issues};
}

function resolveApproved(registry={},badgeId=''){
  const id=clean(badgeId);
  const item=(registry.items||[]).find(x=>x.draft_id===id||x.visual_id===id);
  if(!item)return {ok:false,reason:'BADGE_VISUAL_NOT_FOUND'};
  const checked=validateEntry(item);
  if(!checked.ok)return {ok:false,reason:'BADGE_VISUAL_INVALID',issues:checked.issues};
  if(item.active!==true || item.asset_state!==APPROVED || item.approval_status!==APPROVED || item.renderer_binding!==true){
    return {ok:false,reason:'BADGE_VISUAL_NOT_APPROVED_OR_ACTIVE'};
  }
  return {ok:true,visual_id:item.visual_id,asset_path:item.asset_path,asset_version:item.asset_version||null};
}

function validateRegistry(registry={}){
  const issues=[];
  if(registry.status!=='WORKING_DRAFT_VISUAL_REGISTRY_NOT_ACTIVE')issues.push('REGISTRY_STATUS_INVALID');
  if(registry.hard_locks?.catalog_activation!==false)issues.push('CATALOG_ACTIVATION_GUARD_MISSING');
  if(registry.hard_locks?.auto_asset_binding!==false)issues.push('AUTO_BINDING_GUARD_MISSING');
  if(registry.visual_contract?.grade_stars?.meaning!=='GRADE_CLASSIFICATION')issues.push('STAR_MEANING_INVALID');
  if(registry.visual_contract?.grade_stars?.gem_currency!==false)issues.push('STAR_GEM_COUPLING_FORBIDDEN');
  if(registry.visual_contract?.grade_stars?.progress_counter!==false)issues.push('STAR_PROGRESS_COUPLING_FORBIDDEN');
  for(const item of registry.items||[]){
    const checked=validateEntry(item);
    if(!checked.ok)issues.push(...checked.issues.map(code=>`${item.draft_id||'UNKNOWN'}:${code}`));
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({validateEntry,validateRegistry,resolveApproved});
