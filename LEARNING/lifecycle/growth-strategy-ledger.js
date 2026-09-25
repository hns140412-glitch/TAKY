'use strict';

const crypto=require('node:crypto');

const VERSION='TAKY_GROWTH_STRATEGY_LEDGER_V1';
const clean=v=>String(v??'').trim();

function stable(value){
  if(Array.isArray(value))return value.map(stable);
  if(value&&typeof value==='object'){
    const out={};
    for(const k of Object.keys(value).sort())out[k]=stable(value[k]);
    return out;
  }
  return value;
}

function digest(value){
  return crypto.createHash('sha256').update(JSON.stringify(stable(value))).digest('hex');
}

function emptyLedger(){
  return {
    ledger_version:VERSION,
    append_only:true,
    entries:[],
    receipt_bindings:{}
  };
}

function validateReceipt(receipt={}){
  const issues=[];
  if(clean(receipt.authority)!=='REAL_LEARNING_EVIDENCE_RECEIPT')issues.push('REAL_EVIDENCE_RECEIPT_REQUIRED');
  if(!clean(receipt.receipt_id))issues.push('REAL_EVIDENCE_RECEIPT_ID_REQUIRED');
  if(receipt.raw_evidence_immutable!==true)issues.push('RAW_EVIDENCE_IMMUTABILITY_REQUIRED');
  if(!receipt.scope||!clean(receipt.scope.member_id)||!clean(receipt.scope.subject)||!clean(receipt.scope.concept_skill_target))issues.push('REAL_EVIDENCE_SCOPE_REQUIRED');
  return {ok:issues.length===0,issues};
}

function validateFeedback(feedback={}){
  const issues=[];
  if(feedback?.ok!==true)issues.push('OUTCOME_FEEDBACK_NOT_OK');
  if(feedback.learning_strategy_feedback?.authority!=='LEARNING_OUTCOME_FEEDBACK_ONLY')issues.push('LEARNING_FEEDBACK_AUTHORITY_INVALID');
  const mining=feedback.mining_strategy_feedback_candidate;
  if(mining){
    if(mining.authority!=='MINING_STRATEGY_FEEDBACK_CANDIDATE_ONLY')issues.push('MINING_FEEDBACK_AUTHORITY_INVALID');
    if(mining.acquisition_strategy_change_authorized!==false)issues.push('MINING_AUTO_CHANGE_FORBIDDEN');
    if(mining.canonical_classification_change_authorized!==false)issues.push('INDEXING_AUTHORITY_LEAK');
    if(mining.promotion_authorized!==false)issues.push('MINING_AUTO_PROMOTION_FORBIDDEN');
  }
  return {ok:issues.length===0,issues};
}

function append(ledgerInput={},packet={}){
  const ledger=JSON.parse(JSON.stringify(ledgerInput?.ledger_version?ledgerInput:emptyLedger()));
  if(ledger.ledger_version!==VERSION||ledger.append_only!==true)return {ok:false,reason:'GROWTH_LEDGER_INVALID'};

  const receipt=packet.real_evidence_receipt||{};
  const feedback=packet.outcome_feedback||{};
  const receiptCheck=validateReceipt(receipt);
  if(!receiptCheck.ok)return {ok:false,reason:'REAL_EVIDENCE_RECEIPT_INVALID',issues:receiptCheck.issues};
  const feedbackCheck=validateFeedback(feedback);
  if(!feedbackCheck.ok)return {ok:false,reason:'OUTCOME_FEEDBACK_INVALID',issues:feedbackCheck.issues};

  const scope=receipt.scope;
  const scopeKey=[
    clean(scope.member_id),
    clean(scope.subject).toLowerCase(),
    clean(scope.concept_skill_target).toLowerCase()
  ].join('::');

  const content={
    receipt_id:receipt.receipt_id,
    evidence_digest_sha256:receipt.evidence_digest_sha256||null,
    scope_key:scopeKey,
    learning_strategy_feedback:feedback.learning_strategy_feedback,
    mining_strategy_feedback_candidate:feedback.mining_strategy_feedback_candidate||null,
    prior_gap_id:packet.prior_gap_id||null,
    index_gap_decision:packet.index_gap_decision||null
  };
  const feedbackDigest=digest(content);
  const existing=ledger.receipt_bindings[receipt.receipt_id];
  if(existing){
    if(existing.feedback_digest_sha256!==feedbackDigest){
      return {ok:false,reason:'RECEIPT_FEEDBACK_CONFLICT',receipt_id:receipt.receipt_id};
    }
    return {
      ok:true,
      idempotent:true,
      ledger,
      entry:ledger.entries.find(x=>x.entry_id===existing.entry_id)||null
    };
  }

  const entry={
    entry_id:'growth:'+feedbackDigest.slice(0,24),
    ledger_version:VERSION,
    recorded_at:clean(packet.recorded_at)||new Date(0).toISOString(),
    scope:{
      member_id:clean(scope.member_id),
      subject:clean(scope.subject).toLowerCase(),
      concept_skill_target:clean(scope.concept_skill_target).toLowerCase()
    },
    source_evidence:{
      authority:'REAL_LEARNING_EVIDENCE_RECEIPT',
      receipt_id:receipt.receipt_id,
      evidence_digest_sha256:receipt.evidence_digest_sha256||null,
      raw_evidence_immutable:true
    },
    learning_strategy_feedback:JSON.parse(JSON.stringify(feedback.learning_strategy_feedback)),
    mining_strategy_feedback_candidate:feedback.mining_strategy_feedback_candidate
      ?JSON.parse(JSON.stringify(feedback.mining_strategy_feedback_candidate))
      :null,
    prior_gap_id:packet.prior_gap_id||null,
    index_gap_decision:packet.index_gap_decision||null,
    promotion_state:'CANDIDATE_ONLY',
    promotion_authority:false,
    raw_evidence_copied:false
  };

  ledger.entries.push(entry);
  ledger.receipt_bindings[receipt.receipt_id]={
    entry_id:entry.entry_id,
    feedback_digest_sha256:feedbackDigest
  };

  return {ok:true,idempotent:false,ledger,entry};
}

function evaluate(ledgerInput={},scope={},options={}){
  const ledger=ledgerInput?.ledger_version?ledgerInput:emptyLedger();
  const key=[
    clean(scope.member_id),
    clean(scope.subject).toLowerCase(),
    clean(scope.concept_skill_target).toLowerCase()
  ].join('::');
  const rows=(ledger.entries||[]).filter(x=>[
    clean(x?.scope?.member_id),
    clean(x?.scope?.subject).toLowerCase(),
    clean(x?.scope?.concept_skill_target).toLowerCase()
  ].join('::')===key);

  const verifiedTargets=rows.filter(x=>x.learning_strategy_feedback?.verified_target===true);
  const success=verifiedTargets.filter(x=>x.learning_strategy_feedback?.outcome===1).length;
  const failure=verifiedTargets.filter(x=>x.learning_strategy_feedback?.outcome===0).length;
  const miningCandidates=rows.filter(x=>x.mining_strategy_feedback_candidate).length;
  const minReceipts=Math.max(1,Number(options.min_receipts)||5);

  return {
    ok:true,
    scope_key:key,
    receipt_count:rows.length,
    verified_outcome_count:verifiedTargets.length,
    success_count:success,
    failure_count:failure,
    mining_candidate_count:miningCandidates,
    eligible_for_human_strategy_review:verifiedTargets.length>=minReceipts,
    promotion_authority:false,
    strategy_change_authorized:false,
    invariant:'LONGITUDINAL_EVIDENCE_SUPPORTS_REVIEW__NEVER_AUTOMATIC_PROMOTION'
  };
}

function selfValidate(ledger={}){
  const issues=[];
  if(ledger.ledger_version!==VERSION)issues.push('LEDGER_VERSION_INVALID');
  if(ledger.append_only!==true)issues.push('APPEND_ONLY_REQUIRED');
  if(!Array.isArray(ledger.entries))issues.push('ENTRIES_INVALID');
  for(const [i,e] of (ledger.entries||[]).entries()){
    if(e.promotion_authority!==false)issues.push('PROMOTION_AUTHORITY_FORBIDDEN:'+i);
    if(e.raw_evidence_copied!==false)issues.push('RAW_EVIDENCE_COPY_FORBIDDEN:'+i);
    if(e.source_evidence?.raw_evidence_immutable!==true)issues.push('RAW_IMMUTABILITY_REQUIRED:'+i);
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,digest,emptyLedger,validateReceipt,validateFeedback,append,evaluate,selfValidate});
