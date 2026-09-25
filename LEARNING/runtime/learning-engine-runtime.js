'use strict';

const Core=require('./learner-state-core.js');
const Feedback=require('../pedagogy/feedback-intent.js');
const Graph=require('../domain-model/concept-dependency-graph.js');
const Decision=require('./decision-contract.js');

const VERSION='TAKY_LEARNING_ENGINE_RUNTIME_V1';

function derive(input={}){
  const evidence=Array.isArray(input.evidence)?input.evidence:[];
  const scope=input.scope||{};
  const learnerState=Core.deriveSkillState(evidence,scope,input.state_options||{});
  if(!learnerState.ok)return {ok:false,reason:'LEARNER_STATE_FAILED',detail:learnerState};

  const feedback=Feedback.derive(learnerState);
  if(!feedback.ok)return {ok:false,reason:'FEEDBACK_INTENT_FAILED',detail:feedback};

  let readiness=null;
  if(input.prerequisite_graph){
    readiness=Graph.deriveReadiness(
      input.prerequisite_graph,
      Array.isArray(input.prerequisite_skill_states)?input.prerequisite_skill_states:[],
      scope.subject,
      scope.concept_skill_target
    );
    const readinessCheck=Graph.validateReadiness(readiness);
    if(!readinessCheck.ok)return {ok:false,reason:'PREREQUISITE_READINESS_INVALID',issues:readinessCheck.issues};
  }

  const decision=Decision.derive({
    learner_state:learnerState,
    feedback_intent:feedback,
    prerequisite_readiness:readiness
  });
  if(!decision.ok)return {ok:false,reason:'RUNTIME_DECISION_FAILED',detail:decision};

  return {
    ok:true,
    engine_runtime:VERSION,
    authority:'TAKY_LEARNING_ENGINE_CORE',
    scope:learnerState.scope,
    learner_state:learnerState,
    feedback_intent:feedback,
    prerequisite_readiness:readiness,
    decision,
    trace:{
      evidence_ids:learnerState.observed?.evidence_ids||[],
      learner_state_version:learnerState.core_version||null,
      feedback_contract:feedback.intent_contract||null,
      graph_version:readiness?.graph_version||null,
      decision_contract:decision.decision_contract||null
    },
    cannot_influence:[
      'SCHEDULE_DATE',
      'PLANNER_DATE',
      'DUE_AT',
      'DEADLINE',
      'ASSIGNMENT_FACT',
      'FINAL_UI_COPY'
    ]
  };
}

function validate(result={}){
  const issues=[];
  if(result?.ok!==true)issues.push('RUNTIME_NOT_OK');
  if(result.authority!=='TAKY_LEARNING_ENGINE_CORE')issues.push('AUTHORITY_INVALID');
  if(result.learner_state&&!Core.selfValidate(result.learner_state).ok)issues.push('LEARNER_STATE_INVALID');
  if(result.feedback_intent&&!Feedback.validate(result.feedback_intent).ok)issues.push('FEEDBACK_INVALID');
  if(result.prerequisite_readiness&&!Graph.validateReadiness(result.prerequisite_readiness).ok)issues.push('READINESS_INVALID');
  if(result.decision&&!Decision.validate(result.decision).ok)issues.push('DECISION_INVALID');

  const forbidden=['schedule_date','planner_date','due_at','due_date','deadline'];
  const walk=v=>{
    if(!v||typeof v!=='object')return false;
    for(const [k,n] of Object.entries(v)){
      if(forbidden.includes(k))return true;
      if(walk(n))return true;
    }
    return false;
  };
  if(walk(result))issues.push('SCHEDULE_AUTHORITY_LEAK');

  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,derive,validate});
