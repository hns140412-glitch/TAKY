'use strict';

const VERSION='TAKY_LEARNING_BADGE_IMPROVEMENT_COMPARISON_V1';
const AUTHORITY='LEARNING_VERIFICATION_RECEIPT_COMPARISON';
const clean=v=>String(v??'').trim();

function verifiedRow(row={}){
  return clean(row.learning_target_id)&&
    (row.verified_outcome===0||row.verified_outcome===1)&&
    clean(row?.verification?.authority)==='LEARNING_VERIFICATION_RECEIPT'&&
    clean(row?.verification?.receipt_id)&&
    Number.isFinite(Date.parse(row.observed_at||''));
}

function derive(rows=[],options={}){
  const sourceApp=clean(options.source_app||'hide-seek').toLowerCase();
  const actionRefs=options.child_action_refs&&typeof options.child_action_refs==='object'
    ?options.child_action_refs:{};
  const seq=(Array.isArray(rows)?rows:[])
    .filter(verifiedRow)
    .filter(x=>clean(x.source_app).toLowerCase()===sourceApp)
    .slice()
    .sort((a,b)=>Date.parse(a.observed_at)-Date.parse(b.observed_at)||clean(a.event_id).localeCompare(clean(b.event_id)));

  const byTarget=new Map();
  for(const row of seq){
    const id=clean(row.learning_target_id);
    if(!byTarget.has(id))byTarget.set(id,[]);
    byTarget.get(id).push(row);
  }

  const comparisons=[];
  const blockers=[];
  for(const [target,items] of byTarget.entries()){
    for(let i=0;i<items.length;i++){
      const prior=items[i];
      if(prior.verified_outcome!==0)continue;
      const current=items.slice(i+1).find(x=>x.verified_outcome===1);
      if(!current)continue;
      const priorAction=clean(actionRefs[prior.event_id]);
      const currentAction=clean(actionRefs[current.event_id]);
      if(!priorAction||!currentAction){
        blockers.push({learning_target_id:target,prior_event_id:clean(prior.event_id),current_event_id:clean(current.event_id),code:'EXPLICIT_CHILD_ACTION_REFS_REQUIRED'});
        continue;
      }
      comparisons.push(Object.freeze({
        contract_version:VERSION,
        authority:AUTHORITY,
        comparison_id:`improvement:${target}:${clean(prior.event_id)}:${clean(current.event_id)}`,
        source_app:sourceApp,
        learning_target_id:target,
        prior_event_id:clean(prior.event_id),
        current_event_id:clean(current.event_id),
        prior_receipt_id:clean(prior.verification.receipt_id),
        current_receipt_id:clean(current.verification.receipt_id),
        prior_verified_outcome:0,
        current_verified_outcome:1,
        prior_child_action_ref:priorAction,
        current_child_action_ref:currentAction,
        verified_improvement:true,
        explicit_child_action:true,
        disposition:'COMPARISON_ONLY_NO_BADGE_AUTHORITY'
      }));
    }
  }

  return Object.freeze({
    ok:true,
    contract_version:VERSION,
    authority:AUTHORITY,
    status:comparisons.length?'VERIFIED_COMPARISON_READY':blockers.length?'ACTION_LINKAGE_REQUIRED':'NO_QUALIFYING_IMPROVEMENT',
    source_app:sourceApp,
    comparisons:Object.freeze(comparisons),
    blockers:Object.freeze(blockers),
    badge_award_authorized:false,
    economy_mutation_authorized:false
  });
}

function validate(comparison={}){
  const issues=[];
  if(comparison.contract_version!==VERSION)issues.push('CONTRACT_INVALID');
  if(comparison.authority!==AUTHORITY)issues.push('AUTHORITY_INVALID');
  if(!clean(comparison.comparison_id))issues.push('COMPARISON_ID_REQUIRED');
  if(!clean(comparison.learning_target_id))issues.push('LEARNING_TARGET_REQUIRED');
  if(!clean(comparison.source_app))issues.push('SOURCE_APP_REQUIRED');
  if(comparison.prior_verified_outcome!==0||comparison.current_verified_outcome!==1)issues.push('FAIL_TO_SUCCESS_REQUIRED');
  for(const key of ['prior_event_id','current_event_id','prior_receipt_id','current_receipt_id','prior_child_action_ref','current_child_action_ref']){
    if(!clean(comparison[key]))issues.push(key.toUpperCase()+'_REQUIRED');
  }
  if(comparison.verified_improvement!==true)issues.push('VERIFIED_IMPROVEMENT_REQUIRED');
  if(comparison.explicit_child_action!==true)issues.push('EXPLICIT_CHILD_ACTION_REQUIRED');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,AUTHORITY,derive,validate});
