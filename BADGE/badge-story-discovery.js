'use strict';

// WORKING DESIGN / DISCOVERY PROPOSAL only. Never returns ownership or an Award Ledger receipt.
const KNOWN_RANKS=new Set(['POCKET','FIELD','EXPEDITION','SECRET']);
const KNOWN_TONES=new Set(['WITTY','WARM','BRAVE','CURIOUS']);
const clean=v=>typeof v==='string'?v.trim():'';
const blocked=reason=>({ok:false,reason});
function validateStoryCatalog(catalog,source){
 const issues=[];
 if(catalog?.status!=='WORKING_PRESET_SCENES_AND_HISTORY_DISCOVERY_TEMPLATES_NOT_ACTIVE')issues.push('WORKING_STATUS_REQUIRED');
 if(!Array.isArray(source?.items)||source.items.length!==60)issues.push('EXACT_60_HISTORICAL_SOURCE_REQUIRED');
 if(!Array.isArray(catalog?.presets)||catalog.presets.length!==60)issues.push('EXACT_60_PRESETS_REQUIRED');
 if(!Array.isArray(catalog?.history_discovery_templates)||catalog.history_discovery_templates.length!==20)issues.push('INITIAL_20_DISCOVERY_TEMPLATES_REQUIRED');
 const used=new Set(),rankCount={POCKET:0,FIELD:0,EXPEDITION:0,SECRET:0};
 (catalog?.presets||[]).forEach((entry,index)=>{
  const original=source?.items?.[index];
  if(entry.slot!==index+1||entry.source_draft_id!==original?.draft_id||
    entry.stable_name!==original?.name||entry.visual_id!==original?.visual_id)
    issues.push('HISTORICAL_PRESET_ID_NAME_OR_ORDER_CHANGED:'+index);
  if(used.has(entry.source_draft_id))issues.push('DUPLICATE_PRESET_ID');
  used.add(entry.source_draft_id);
  if(!KNOWN_RANKS.has(entry.moment_rank))issues.push('INVALID_MOMENT_RANK');
  else rankCount[entry.moment_rank]++;
  if(!KNOWN_TONES.has(entry.tone)||!clean(entry.storyline)||!clean(entry.motif))
    issues.push('INCOMPLETE_SCENE:'+index);
  if(entry.catalog_status!=='PRESET_WORKING_NOT_RUNTIME_ACTIVE'||
    entry.asset_status!=='UNBOUND_NOT_APPROVED'||entry.auto_award!==false)
    issues.push('SILENT_CATALOG_ACTIVATION_OR_AWARD:'+index);
 });
 if(JSON.stringify(rankCount)!==JSON.stringify({POCKET:20,FIELD:20,EXPEDITION:14,SECRET:6}))
  issues.push('UNEXPECTED_SCENE_RANK_DISTRIBUTION');
 const templates=new Set;
 (catalog?.history_discovery_templates||[]).forEach((t,i)=>{
  if(t.slot!==i+1||t.template_id!==`HIST-DISCOVERY-${String(i+1).padStart(3,'0')}`||
    templates.has(t.template_id))issues.push('DISCOVERY_TEMPLATE_ID_INVALID');
  templates.add(t.template_id);
  if(!KNOWN_RANKS.has(t.moment_rank)||!KNOWN_TONES.has(t.tone)||
    !clean(t.suggested_title)||!clean(t.storyline)||!clean(t.motif)||
    !Array.isArray(t.required_evidence_kinds)||t.required_evidence_kinds.length!==2||
    t.required_evidence_kinds.some(x=>!clean(x))||
    new Set(t.required_evidence_kinds).size!==2)
    issues.push('DISCOVERY_EVIDENCE_PATTERN_INVALID:'+i);
  if(t.appearance!=='CHILD_SCOPED_DISCOVERY_CANDIDATE_ONLY'||
    t.award_status!=='NOT_AWARDED'||t.asset_status!=='UNBOUND_NOT_APPROVED'||
    t.auto_award!==false)issues.push('AUTO_DISCOVERY_AWARD_FORBIDDEN:'+i);
 });
 if(catalog?.architecture?.rank_axis!=='MOMENT_SIGNIFICANCE_VISUAL_ONLY'||
   catalog?.architecture?.reacquisition_axis!=='SEPARATE_VERIFIED_REAWARD_STARS_5_TO_TIER_UP')
   issues.push('RANK_AND_REAWARD_AXES_MUST_REMAIN_SEPARATE');
 if(catalog?.review_gate?.history_ai_may_suggest_not_grant!==true||
    catalog?.review_gate?.server_decision_and_award_ledger_required_for_ownership!==true||
    catalog?.review_gate?.approved_asset_required_for_runtime_art!==true)
   issues.push('DISCOVERY_FAIL_CLOSED_CONTRACT_REQUIRED');
 return {ok:issues.length===0,issues,counts:{preset:catalog?.presets?.length||0,history:catalog?.history_discovery_templates?.length||0,rankCount}};
}
/**
 * An owner-supplied trusted function MUST verify each history receipt from
 * authoritative storage. Raw browser history or an "accepted" JSON flag is not proof.
 * Pattern match produces personal discovery proposals only; the existing
 * Criteria → Review → Decision → Award Ledger flow is still the sole award authority.
 */
function suggestHistoryDiscoveries({catalog,family_id,child_id,evidence_records,verifyEvidence}={}){
 const family=clean(family_id),child=clean(child_id);
 if(!family||!child||family_id!==family||child_id!==child)
  return blocked('EXPLICIT_FAMILY_CHILD_SCOPE_REQUIRED');
 if(typeof verifyEvidence!=='function')return blocked('TRUSTED_EVIDENCE_VERIFIER_REQUIRED');
 if(!Array.isArray(evidence_records)||evidence_records.length>1000)
  return blocked('EVIDENCE_INPUT_INVALID');
 if(catalog?.status!=='WORKING_PRESET_SCENES_AND_HISTORY_DISCOVERY_TEMPLATES_NOT_ACTIVE'||
    !Array.isArray(catalog.history_discovery_templates)||catalog.history_discovery_templates.length!==20)
  return blocked('WORKING_DISCOVERY_CATALOG_REQUIRED');
 const unique=new Map;
 for(const input of evidence_records){
  let proof;
  try{proof=verifyEvidence(input,{family_id:family,child_id:child})}
  catch{return blocked('EVIDENCE_VERIFICATION_FAILED')}
  const e=proof?.receipt;
  if(proof?.ok!==true||!e||e.family_id!==family||e.child_id!==child||
    e.status!=='VERIFIED_HISTORY_EVIDENCE'||!clean(e.receipt_id)||!clean(e.kind)||
    unique.has(e.receipt_id))return blocked('UNVERIFIED_DUPLICATE_OR_CROSS_CHILD_EVIDENCE');
  unique.set(e.receipt_id,{receipt_id:e.receipt_id,kind:e.kind});
 }
 const byKind=new Map;
 for(const e of unique.values()){
  if(!byKind.has(e.kind))byKind.set(e.kind,[]);
  byKind.get(e.kind).push(e.receipt_id);
 }
 const proposals=[];
 for(const t of catalog.history_discovery_templates){
  const matched=t.required_evidence_kinds.map(kind=>byKind.get(kind)?.[0]||null);
  if(matched.some(x=>!x)||new Set(matched).size!==matched.length)continue;
  proposals.push({
    contract:'TAKY_CHILD_HISTORY_BADGE_DISCOVERY_PROPOSAL_V1',
    family_id:family,child_id:child,template_id:t.template_id,
    proposed_name:t.suggested_title,moment_rank:t.moment_rank,tone:t.tone,
    supporting_receipt_ids:matched,
    proposal_status:'REVIEW_REQUIRED_NOT_AWARD',
    ownership_state:null,award_id:null,asset_status:'UNBOUND_NOT_APPROVED'
  });
 }
 return {ok:true,scope:{family_id:family,child_id:child},proposal_count:proposals.length,proposals};
}
module.exports=Object.freeze({validateStoryCatalog,suggestHistoryDiscoveries});
