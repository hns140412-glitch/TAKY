'use strict';

const VERSION='TAKY_GROWTH_OUTCOME_FEEDBACK_V1';
const AUTHORITY='LEARNING_GROWTH_CONTROL_FEEDBACK_CANDIDATE_ONLY';
const clean=v=>String(v??'').trim();

function expressionRank(level){
  const m=clean(level).toUpperCase().match(/^L([1-5])_/);
  return m?Number(m[1]):null;
}

function derive({prior_growth_next_step=null,outcome_evidence=null}={}){
  const control=prior_growth_next_step?.growth_control||null;
  if(!control)return {
    ok:true,version:VERSION,authority:AUTHORITY,
    adjustment:'NO_PRIOR_GROWTH_CONTROL',
    control_change_authorized:false,
    state_mutation_authorized:false,
    suggested_next_control:null,
    basis:[]
  };

  const signals=Array.isArray(outcome_evidence?.language_growth_signals)
    ?outcome_evidence.language_growth_signals:[];
  const evaluable=signals.filter(x=>['SUCCESS','PARTIAL','FAIL'].includes(clean(x?.outcome).toUpperCase()));
  if(!evaluable.length)return {
    ok:true,version:VERSION,authority:AUTHORITY,
    adjustment:'OBSERVE_MORE',
    control_change_authorized:false,
    state_mutation_authorized:false,
    suggested_next_control:null,
    basis:['NO_EVALUABLE_GROWTH_RESULT']
  };

  const success=evaluable.filter(x=>clean(x.outcome).toUpperCase()==='SUCCESS').length;
  const partial=evaluable.filter(x=>clean(x.outcome).toUpperCase()==='PARTIAL').length;
  const fail=evaluable.filter(x=>clean(x.outcome).toUpperCase()==='FAIL').length;
  const total=evaluable.length;
  const successRate=success/total;
  const failRate=fail/total;
  const level=expressionRank(control.expression_level);
  const minimal=clean(control.hint_strength).toUpperCase()==='MINIMAL_CUE';
  const strong=clean(control.hint_strength).toUpperCase()==='STRONG_SCAFFOLD';

  let adjustment='HOLD_LEVEL';
  const candidate={...control};

  if(failRate>=0.5){
    adjustment=strong?'KEEP_SUPPORT_AND_RECHECK':'INCREASE_SUPPORT_CANDIDATE';
    candidate.learning_intensity='SUPPORT_BUILD';
    candidate.hint_strength='STRONG_SCAFFOLD';
    candidate.hint_fade='HOLD_AND_FADE_AFTER_SUCCESS';
    candidate.challenge_direction='STABILIZE';
    if(Number.isFinite(level)&&level>1)candidate.expression_level=
      level===2?'L1_CHUNK_OR_PHRASE':
      level===3?'L2_SIMPLE_SENTENCE':
      level===4?'L3_EXPANDED_SENTENCE':'L4_REASONED_RESPONSE';
  }else if(successRate===1&&minimal){
    adjustment='PRESERVE_OR_STRETCH_CANDIDATE';
    candidate.learning_intensity='STRETCH_TRANSFER';
    candidate.challenge_direction='TRANSFER';
  }else if(successRate===1&&!minimal){
    adjustment='FADE_HINT_ONE_STEP_CANDIDATE';
    candidate.hint_strength=strong?'PARTIAL_FRAME':'MINIMAL_CUE';
    candidate.hint_fade='FADE_ONE_STEP_WHEN_SUCCESSFUL';
  }else if(partial>0){
    adjustment='HOLD_LEVEL_ADJUST_HINT_CANDIDATE';
    candidate.learning_intensity='BUILD_CONNECT';
    candidate.challenge_direction='EXTEND';
  }

  return {
    ok:true,
    version:VERSION,
    authority:AUTHORITY,
    adjustment,
    control_change_authorized:false,
    state_mutation_authorized:false,
    suggested_next_control:candidate,
    basis:[
      'PRIOR_CONTROL_APPLIED',
      'OUTCOME_SIGNAL_COUNT:'+total,
      'SUCCESS_COUNT:'+success,
      'PARTIAL_COUNT:'+partial,
      'FAIL_COUNT:'+fail
    ],
    guard:'CANDIDATE_ONLY__NEXT_RUNTIME_MUST_REDERIVE_FROM_CUMULATIVE_EVIDENCE'
  };
}

function validate(result={}){
  const issues=[];
  if(result?.ok!==true)issues.push('RESULT_NOT_OK');
  if(result.authority!==AUTHORITY)issues.push('AUTHORITY_INVALID');
  if(result.control_change_authorized!==false)issues.push('AUTO_CONTROL_CHANGE_FORBIDDEN');
  if(result.state_mutation_authorized!==false)issues.push('AUTO_STATE_MUTATION_FORBIDDEN');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,AUTHORITY,derive,validate});
