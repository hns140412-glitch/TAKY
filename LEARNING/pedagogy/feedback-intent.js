'use strict';

const VERSION='TAKY_PEDAGOGICAL_FEEDBACK_INTENT_V1';

function derive(state={}){
  if(!state?.ok)return {ok:false,reason:'LEARNER_STATE_REQUIRED'};

  const intents=[];
  const inferred=state.inferred||{};
  const observed=state.observed||{};

  if(inferred.repeated_confusion_signal==='REPEATED_SELF_REPORTED_CONFUSION'){
    intents.push({
      intent:'DISAMBIGUATE_CONFUSION',
      priority:'HIGH',
      basis:'REPEATED_SELF_REPORTED_CONFUSION',
      targets:(observed.self_reflection?.repeated_confusions||[]).map(x=>x.target)
    });
  }

  if(inferred.metacognitive_recall_signal==='KNEW_BUT_RECALL_FAILED_REPORTED'){
    intents.push({
      intent:'SHORT_DELAY_RETRIEVAL',
      priority:'MEDIUM',
      basis:'KNEW_BUT_RECALL_FAILED_REPORTED'
    });
  }

  if(inferred.assistance_dependency_signal==='ASSISTANCE_DOMINANT'){
    intents.push({
      intent:'REDUCE_ASSISTANCE_GRADUALLY',
      priority:'MEDIUM',
      basis:'ASSISTANCE_DOMINANT'
    });
  }

  if(inferred.retention_signal==='RETENTION_AT_RISK'){
    intents.push({
      intent:'RETRIEVAL_CHECKPOINT',
      priority:'HIGH',
      basis:'RETENTION_AT_RISK'
    });
  }

  if(inferred.trend==='DECLINING'){
    intents.push({
      intent:'RETRIEVAL_CHECKPOINT',
      priority:'HIGH',
      basis:'DECLINING_MEMORY_TREND'
    });
  }else if(inferred.trend==='IMPROVING'){
    intents.push({
      intent:'MAINTAIN_CHALLENGE',
      priority:'LOW',
      basis:'IMPROVING_MEMORY_TREND'
    });
  }

  if(!intents.length){
    intents.push({
      intent:'CONTINUE_OBSERVATION',
      priority:'LOW',
      basis:'NO_STRONG_PEDAGOGICAL_SIGNAL'
    });
  }

  return {
    ok:true,
    intent_contract:VERSION,
    scope:state.scope,
    intents,
    authority:'PEDAGOGICAL_INTENT_ONLY',
    can_influence:['ACTIVITY_SEQUENCE','CHECKPOINT_SELECTION','FEEDBACK_FOCUS','RECOVERY_INTENSITY'],
    cannot_influence:['SCHEDULE_DATE','PLANNER_DATE','DUE_AT','DEADLINE','ASSIGNMENT_FACT'],
    ui_copy_owned_by:'CONSUMER_APP'
  };
}

function validate(result={}){
  const issues=[];
  if(!result?.ok)issues.push('RESULT_NOT_OK');
  if(result.authority!=='PEDAGOGICAL_INTENT_ONLY')issues.push('AUTHORITY_INVALID');
  if(result.ui_copy_owned_by!=='CONSUMER_APP')issues.push('UI_COPY_OWNERSHIP_INVALID');
  const forbidden=['schedule_date','planner_date','due_at','due_date','deadline'];
  const hasForbidden=(v)=>{
    if(!v||typeof v!=='object')return false;
    for(const [k,n] of Object.entries(v)){
      if(forbidden.includes(k))return true;
      if(hasForbidden(n))return true;
    }
    return false;
  };
  if(hasForbidden(result))issues.push('SCHEDULE_AUTHORITY_LEAK');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,derive,validate});
