'use strict';

/*
  TAKY canonical server transport kernel.
  Semantic authority remains LEARNING_ENGINE_CORE.
  Consumer repositories may vendor this file byte-for-byte with provenance.
*/
const crypto=require('node:crypto');

const VERSION='TAKY_LEARNING_EVIDENCE_TRANSPORT_KERNEL_V1';
const clean=v=>String(v??'').trim();
const stable=v=>{
  if(Array.isArray(v))return v.map(stable);
  if(v&&typeof v==='object'){
    const out={};
    for(const k of Object.keys(v).sort())out[k]=stable(v[k]);
    return out;
  }
  return v;
};
const digest=v=>crypto.createHash('sha256').update(JSON.stringify(stable(v))).digest('hex');

function emptyState(){
  return {
    kernel_version:VERSION,
    verified_by_scope:{},
    observations_by_id:{}
  };
}
function scopeKey(e={}){
  return [clean(e.member_id),clean(e.subject).toLowerCase(),clean(e.concept_skill_target).toLowerCase()].join('::');
}
function base(packet={}){
  const event=packet.event||{};
  const payload=event.payload||packet.evidence||{};
  const context=packet.context||{};
  return {
    event_id:clean(event.event_id||packet?.evidence?.event_id),
    observed_at:clean(event.occurred_at||event.at||packet?.evidence?.observed_at||packet?.created_at),
    member_id:clean(context.member_id||payload.member_id||packet?.evidence?.member_id),
    subject:clean(context.subject||payload.subject||packet?.evidence?.subject).toLowerCase(),
    concept_skill_target:clean(context.concept_skill_target||payload.concept_skill_target||packet?.evidence?.concept_skill_target).toLowerCase(),
    learning_target_id:clean(context.learning_target_id||payload.learning_target_id||payload.lexical_id||payload.word_id||payload.item_id||packet?.evidence?.learning_target_id)||null,
    source_app:clean(packet.source_app||event.source||event.app||packet?.evidence?.source_app),
    instrument_version:clean(payload.instrumentVersion||payload.instrument_version||packet?.evidence?.instrument_version)||'UNSPECIFIED',
    evidence_type:clean(packet?.evidence?.evidence_type)||'SPECIALIST_OUTCOME_UNKNOWN',
    verified_outcome:null,
    verification:null
  };
}
function candidateFor(packet={}){
  return packet?.event?.payload?.verification_candidate||packet?.evidence?.verification_candidate||null;
}
function canonicalize(packet={}){
  const e=base(packet);
  const source=e.source_app;
  const candidate=candidateFor(packet);
  const verificationInput=packet.verification_input||null;

  if(source==='hide-seek'){
    e.evidence_type='MEMORY_RETRIEVAL_EVIDENCE';
    if(candidate?.basis==='DETERMINISTIC_LOCAL_MATCH'&&candidate?.verifier_type==='RETRIEVAL_EXACT_MATCH'&&(candidate.outcome===0||candidate.outcome===1)&&clean(candidate.reference_id)){
      e.verified_outcome=candidate.outcome;
      e.verification={
        authority:'LEARNING_VERIFICATION_RECEIPT',
        receipt_id:'vr:'+e.event_id+':'+clean(candidate.verifier_version||'v1'),
        verifier_type:'RETRIEVAL_EXACT_MATCH',
        verifier_version:clean(candidate.verifier_version||'v1'),
        reference_id:clean(candidate.reference_id)
      };
    }
  }else if(source==='ready-set'){
    if(e.evidence_type==='SPECIALIST_OUTCOME_UNKNOWN')e.evidence_type='STRUCTURED_PRACTICE_EVIDENCE';
    if(candidate?.basis==='DETERMINISTIC_LOCAL_MATCH'&&candidate?.verifier_type==='ANSWER_KEY_EXACT'&&(candidate.outcome===0||candidate.outcome===1)&&clean(candidate.reference_id)){
      e.verified_outcome=candidate.outcome;
      e.verification={
        authority:'LEARNING_VERIFICATION_RECEIPT',
        receipt_id:'vr:'+e.event_id+':'+clean(candidate.verifier_version||'v1'),
        verifier_type:'ANSWER_KEY_EXACT',
        verifier_version:clean(candidate.verifier_version||'v1'),
        reference_id:clean(candidate.reference_id)
      };
    }
  }else if(source==='snap-pop'){
    e.evidence_type='LEARNER_PRODUCTION_EVIDENCE';
    if(verificationInput?.verifier_type==='HUMAN_RUBRIC_BINARY'&&(verificationInput.outcome===0||verificationInput.outcome===1)&&
      ['PARENT','TEACHER','QUALIFIED_REVIEWER'].includes(clean(verificationInput.reviewer_role))&&
      clean(verificationInput.reference_id)&&clean(verificationInput.receipt_id)&&clean(verificationInput.verified_at)&&
      clean(verificationInput.target_event_id)===e.event_id&&
      clean(verificationInput.member_id)===e.member_id&&
      clean(verificationInput.subject).toLowerCase()===e.subject&&
      clean(verificationInput.concept_skill_target).toLowerCase()===e.concept_skill_target){
      e.verified_outcome=verificationInput.outcome;
      e.verification={
        authority:'LEARNING_VERIFICATION_RECEIPT',
        receipt_id:clean(verificationInput.receipt_id),
        verifier_type:'HUMAN_RUBRIC_BINARY',
        verifier_version:clean(verificationInput.verifier_version),
        reference_id:clean(verificationInput.reference_id),
        reviewer_role:clean(verificationInput.reviewer_role)
      };
    }
  }

  const issues=[];
  for(const k of ['event_id','observed_at','member_id','subject','concept_skill_target','source_app','instrument_version','evidence_type']){
    if(!clean(e[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(!Number.isFinite(Date.parse(e.observed_at||'')))issues.push('INVALID_TIME');
  if(!['hide-seek','ready-set','snap-pop'].includes(e.source_app))issues.push('SOURCE_APP_NOT_ALLOWED');
  return issues.length?{ok:false,reason:'CANONICAL_INVALID',issues}:{ok:true,evidence:e};
}
function verifiedReceipt(scopeRows=[]){
  const rows=scopeRows.slice().sort((a,b)=>Date.parse(a.observed_at)-Date.parse(b.observed_at)||a.event_id.localeCompare(b.event_id));
  const payload=rows.map(r=>({
    event_id:r.event_id,observed_at:r.observed_at,member_id:r.member_id,subject:r.subject,
    concept_skill_target:r.concept_skill_target,learning_target_id:r.learning_target_id,
    evidence_type:r.evidence_type,source_app:r.source_app,instrument_version:r.instrument_version,
    verified_outcome:r.verified_outcome,verification_receipt_id:r.verification?.receipt_id,
    verifier_type:r.verification?.verifier_type,verifier_version:r.verification?.verifier_version
  }));
  const d=digest(payload);
  return {
    authority:'REAL_LEARNING_EVIDENCE_RECEIPT',
    receipt_id:'real-evidence:'+d.slice(0,24),
    evidence_digest_sha256:d,
    event_count:rows.length,
    event_ids:rows.map(x=>x.event_id),
    scope:rows.length?{member_id:rows[0].member_id,subject:rows[0].subject,concept_skill_target:rows[0].concept_skill_target}:null,
    raw_evidence_immutable:true
  };
}
function observationReceipt(packet,e){
  const d=digest({
    packet_id:packet.packet_id,event_id:e.event_id,observed_at:e.observed_at,member_id:e.member_id,
    subject:e.subject,concept_skill_target:e.concept_skill_target,learning_target_id:e.learning_target_id,
    evidence_type:e.evidence_type,source_app:e.source_app,instrument_version:e.instrument_version
  });
  return {
    authority:'OBSERVATION_INGEST_RECEIPT',
    receipt_id:'observation:'+d.slice(0,24),
    evidence_digest_sha256:d,
    event_id:e.event_id,
    immutable:true
  };
}
function ingest(stateInput={},packet={}){
  const state=JSON.parse(JSON.stringify(stateInput?.kernel_version?stateInput:emptyState()));
  const normalized=canonicalize(packet);
  if(!normalized.ok)return normalized;
  const e=normalized.evidence;

  if(e.verified_outcome===0||e.verified_outcome===1){
    const key=scopeKey(e);
    const current=Array.isArray(state.verified_by_scope[key])?state.verified_by_scope[key]:[];
    if(!current.some(x=>x.event_id===e.event_id))current.push(e);
    current.sort((a,b)=>Date.parse(a.observed_at)-Date.parse(b.observed_at)||a.event_id.localeCompare(b.event_id));
    state.verified_by_scope[key]=current;
    const receipt=verifiedReceipt(current);
    const retrievalCount=current.filter(x=>x.evidence_type==='MEMORY_RETRIEVAL_EVIDENCE').length;
    return {
      ok:true,state,
      acknowledgement_kind:'REAL_EVIDENCE_RECEIPT',
      receipt_id:receipt.receipt_id,
      receipt,
      readiness:{
        verified_retrieval_target_count:retrievalCount,
        remaining_to_30:Math.max(0,30-retrievalCount),
        promotion_data_ready:retrievalCount>=30,
        promotion_authority:false
      }
    };
  }

  if(!state.observations_by_id[e.event_id])state.observations_by_id[e.event_id]=e;
  const receipt=observationReceipt(packet,e);
  return {
    ok:true,state,
    acknowledgement_kind:'OBSERVATION_INGEST_RECEIPT',
    receipt_id:receipt.receipt_id,
    receipt,
    readiness:{promotion_authority:false}
  };
}
function selfValidate(result={}){
  const issues=[];
  if(!result.ok)issues.push('RESULT_NOT_OK');
  if(!['REAL_EVIDENCE_RECEIPT','OBSERVATION_INGEST_RECEIPT'].includes(result.acknowledgement_kind))issues.push('ACK_KIND_INVALID');
  if(!clean(result.receipt_id))issues.push('RECEIPT_ID_REQUIRED');
  if(result.readiness?.promotion_authority!==false)issues.push('PROMOTION_AUTHORITY_FORBIDDEN');
  return {ok:issues.length===0,issues};
}
module.exports=Object.freeze({VERSION,digest,emptyState,scopeKey,canonicalize,verifiedReceipt,observationReceipt,ingest,selfValidate});
