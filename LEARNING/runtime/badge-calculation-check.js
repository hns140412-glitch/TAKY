'use strict';

const VERSION='TAKY_LEARNING_BADGE_CALCULATION_CHECK_V1';
const SOURCE_CONTRACT_ID='LEARNING_VERIFIED_CALCULATION_CHECK_V1';
const clean=v=>String(v??'').trim();

function verifiedCalculation(row={}){
  return clean(row.learning_target_id)&&
    clean(row.domain).toUpperCase()==='CALCULATION'&&
    (row.verified_outcome===0||row.verified_outcome===1)&&
    clean(row?.verification?.authority)==='LEARNING_VERIFICATION_RECEIPT'&&
    clean(row?.verification?.receipt_id)&&
    clean(row.event_id)&&
    Number.isFinite(Date.parse(row.observed_at||''));
}

function derive(before={},after={},options={}){
  const actionRef=clean(options.child_check_action_ref);
  if(!verifiedCalculation(before)||!verifiedCalculation(after)) return null;
  if(clean(before.learning_target_id)!==clean(after.learning_target_id)) return null;
  if(before.verified_outcome!==0||after.verified_outcome!==1) return null;
  if(Date.parse(after.observed_at)<=Date.parse(before.observed_at)) return null;
  if(!actionRef) return null;
  return Object.freeze({
    contract_version:'TAKY_BADGE_SOURCE_OBSERVATION_V1',
    app_id:'LEARNING_ENGINE_CORE',
    event_family:'ERROR_CORRECTION',
    behavior_code:'CALCULATION_CHECK',
    source_contract_id:SOURCE_CONTRACT_ID,
    event_id:`learning_calc_check:${clean(after.learning_target_id)}:${clean(after.event_id)}`,
    occurred_at:after.observed_at,
    evidence_ref:`learning-calculation-check:${clean(before.event_id)}:${clean(after.event_id)}`,
    explicit_child_action:true,
    payload:Object.freeze({
      learningTargetId:clean(after.learning_target_id),
      beforeEventId:clean(before.event_id),
      afterEventId:clean(after.event_id),
      beforeReceiptId:clean(before.verification.receipt_id),
      afterReceiptId:clean(after.verification.receipt_id),
      childCheckActionRef:actionRef
    }),
    disposition:'OBSERVATION_ONLY',
    badge_award_authorized:false,
    economy_mutation_authorized:false,
    catalog_activation_allowed:false
  });
}

function validate(obs={}){
  const issues=[];
  if(obs.contract_version!=='TAKY_BADGE_SOURCE_OBSERVATION_V1')issues.push('CONTRACT_INVALID');
  if(obs.app_id!=='LEARNING_ENGINE_CORE')issues.push('APP_INVALID');
  if(obs.event_family!=='ERROR_CORRECTION')issues.push('FAMILY_INVALID');
  if(obs.behavior_code!=='CALCULATION_CHECK')issues.push('BEHAVIOR_INVALID');
  if(obs.source_contract_id!==SOURCE_CONTRACT_ID)issues.push('SOURCE_CONTRACT_INVALID');
  if(obs.explicit_child_action!==true)issues.push('EXPLICIT_CHILD_ACTION_REQUIRED');
  for(const k of ['learningTargetId','beforeEventId','afterEventId','beforeReceiptId','afterReceiptId','childCheckActionRef']){
    if(!clean(obs?.payload?.[k]))issues.push(k.toUpperCase()+'_REQUIRED');
  }
  if(obs.badge_award_authorized!==false)issues.push('AWARD_AUTHORITY_FORBIDDEN');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,SOURCE_CONTRACT_ID,derive,validate});
