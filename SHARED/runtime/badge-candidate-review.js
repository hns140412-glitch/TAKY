(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyBadgeCandidateReview=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='TAKY_BADGE_CANDIDATE_REVIEW_V1';
  const clean=v=>String(v??'').trim();
  const ALLOWED_STATUS=new Set(['REVIEW_REQUIRED','APPROVED_FOR_CATALOG_REVIEW','REJECTED']);

  function normalize(input={}){
    const evidence=Array.isArray(input.evidence_event_ids)
      ? [...new Set(input.evidence_event_ids.map(clean).filter(Boolean))]
      : [];
    const status=clean(input.status).toUpperCase()||'REVIEW_REQUIRED';
    return Object.freeze({
      badge_candidate_contract:VERSION,
      candidate_id:clean(input.candidate_id)||null,
      member_id:clean(input.member_id)||null,
      proposed_name:clean(input.proposed_name)||null,
      behavior_family:clean(input.behavior_family).toUpperCase()||null,
      rationale:clean(input.rationale)||null,
      evidence_event_ids:Object.freeze(evidence),
      source_app:clean(input.source_app)||null,
      status:ALLOWED_STATUS.has(status)?status:'REVIEW_REQUIRED',
      active:false,
      award_authorized:false,
      catalog_insert_authorized:false,
      trigger_activation_authorized:false,
      created_at:input.created_at||null,
      reviewed_at:input.reviewed_at||null,
      reviewed_by:clean(input.reviewed_by)||null
    });
  }

  function validate(input={}){
    const candidate=normalize(input),issues=[];
    if(!candidate.candidate_id)issues.push('CANDIDATE_ID_REQUIRED');
    if(!candidate.member_id)issues.push('MEMBER_ID_REQUIRED');
    if(!candidate.behavior_family)issues.push('BEHAVIOR_FAMILY_REQUIRED');
    if(!candidate.evidence_event_ids.length)issues.push('EVIDENCE_EVENT_IDS_REQUIRED');
    if(candidate.active)issues.push('CANDIDATE_MUST_REMAIN_INACTIVE');
    if(candidate.award_authorized)issues.push('CANDIDATE_CANNOT_AUTHORIZE_AWARD');
    return {ok:issues.length===0,issues,candidate};
  }

  function propose(input={}){
    const candidate=normalize({...input,status:'REVIEW_REQUIRED'});
    const checked=validate(candidate);
    if(!checked.ok)return checked;
    return {ok:true,candidate:checked.candidate};
  }

  function review(input={},decision={}){
    const checked=validate(input);
    if(!checked.ok)return checked;
    const action=clean(decision.action).toUpperCase();
    const reviewed_by=clean(decision.reviewed_by);
    if(!reviewed_by)return {ok:false,issues:['REVIEWER_REQUIRED'],candidate:checked.candidate};
    let status;
    if(action==='APPROVE_FOR_CATALOG_REVIEW')status='APPROVED_FOR_CATALOG_REVIEW';
    else if(action==='REJECT')status='REJECTED';
    else return {ok:false,issues:['REVIEW_ACTION_INVALID'],candidate:checked.candidate};
    return {
      ok:true,
      candidate:normalize({
        ...checked.candidate,
        status,
        reviewed_by,
        reviewed_at:decision.reviewed_at||new Date().toISOString()
      })
    };
  }

  return Object.freeze({VERSION,ALLOWED_STATUS:Object.freeze([...ALLOWED_STATUS]),normalize,validate,propose,review});
});
