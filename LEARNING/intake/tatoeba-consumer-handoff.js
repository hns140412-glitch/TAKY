'use strict';

const VERSION='TAKY_TATOEBA_CONSUMER_HANDOFF_V1';
const clean=v=>String(v??'').trim();

const PURPOSES=Object.freeze({
  HIDE_SEEK:new Set(['CONTEXT_EXPOSURE','MEANING_IN_CONTEXT_SUPPORT','CONTRAST_REFERENCE']),
  SNAP_POP:new Set(['CONTEXT_EXPOSURE','WRITING_PREPARATION_REFERENCE','CONTRAST_REFERENCE'])
});

function prepare(selectionResult={},request={}){
  const consumer=clean(request.consumer_app);
  const purpose=clean(request.purpose);
  if(!PURPOSES[consumer])return {ok:false,reason:'CONSUMER_NOT_ALLOWED',version:VERSION};
  if(!PURPOSES[consumer].has(purpose))return {ok:false,reason:'PURPOSE_NOT_ALLOWED',version:VERSION};
  if(selectionResult?.ok!==true||selectionResult?.state!=='CHILD_FACING_APPROVED'){
    return {ok:false,reason:'CHILD_FACING_APPROVED_SELECTION_REQUIRED',version:VERSION};
  }
  const s=selectionResult.selection||{};
  if(!clean(s.review_receipt))return {ok:false,reason:'CURATION_RECEIPT_REQUIRED',version:VERSION};

  const reference={
    sentence_id:clean(s.sentence_id),
    text:String(s.text??''),
    language:clean(s.language),
    source_id:clean(s.source_id),
    source_ref:clean(s.source_ref),
    sentence_url:clean(s.sentence_url),
    owner_or_author:s.owner_or_author||null,
    license:clean(s.license),
    license_provenance:clean(s.license_provenance),
    attribution_text_or_components:s.attribution_text_or_components||null,
    target_learning_id:clean(s.target_learning_id),
    target_form:clean(s.target_form),
    context_or_sense_ref:clean(s.context_or_sense_ref),
    curation_receipt_id:clean(s.review_receipt)
  };
  for(const [k,v] of Object.entries(reference)){
    if(['owner_or_author','attribution_text_or_components'].includes(k))continue;
    if(k==='text'?v.length===0:!clean(v))return {ok:false,reason:'REFERENCE_FIELD_MISSING:'+k,version:VERSION};
  }

  const guards={
    reference_only:true,
    learner_performance_credit:false,
    mastery_delta_allowed:false,
    memory_strength_delta_allowed:false,
    schedule_authority:false,
    auto_answer_allowed:false,
    normative_usage_claim_allowed:false,
    frequency_claim_allowed:false
  };

  const consumer_guards=consumer==='HIDE_SEEK'?{
    recall_evidence_credit:false,
    exposure_is_not_retrieval:true,
    example_cannot_mark_correctness:true
  }:{
    learner_authorship_required:true,
    auto_insert_into_learner_output:false,
    example_cannot_become_completed_answer:true
  };

  return {
    ok:true,
    handoff_contract:VERSION,
    handoff_id:'tatoeba:'+consumer.toLowerCase()+':'+reference.sentence_id+':'+reference.target_learning_id,
    consumer_app:consumer,
    purpose,
    display_permission:'CHILD_FACING_APPROVED_REFERENCE_ONLY',
    reference,
    guards,
    consumer_guards,
    invariant:'REFERENCE_EXPOSURE_IS_CONTEXT_SUPPORT_NOT_LEARNER_PERFORMANCE'
  };
}

function validate(handoff={}){
  const issues=[];
  if(handoff?.handoff_contract!==VERSION)issues.push('VERSION_INVALID');
  if(!PURPOSES[handoff?.consumer_app])issues.push('CONSUMER_INVALID');
  if(handoff?.guards?.reference_only!==true)issues.push('REFERENCE_ONLY_GUARD_MISSING');
  if(handoff?.guards?.learner_performance_credit!==false)issues.push('LEARNER_PERFORMANCE_LEAK');
  if(handoff?.guards?.mastery_delta_allowed!==false)issues.push('MASTERY_LEAK');
  if(handoff?.guards?.memory_strength_delta_allowed!==false)issues.push('MEMORY_STRENGTH_LEAK');
  if(handoff?.guards?.schedule_authority!==false)issues.push('SCHEDULE_AUTHORITY_LEAK');
  if(handoff?.consumer_app==='HIDE_SEEK'&&handoff?.consumer_guards?.recall_evidence_credit!==false)issues.push('HIDE_RECALL_EVIDENCE_LEAK');
  if(handoff?.consumer_app==='SNAP_POP'&&handoff?.consumer_guards?.learner_authorship_required!==true)issues.push('SNAP_AUTHORSHIP_GUARD_MISSING');
  if(handoff?.invariant!=='REFERENCE_EXPOSURE_IS_CONTEXT_SUPPORT_NOT_LEARNER_PERFORMANCE')issues.push('INVARIANT_MISSING');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,PURPOSES,prepare,validate});
