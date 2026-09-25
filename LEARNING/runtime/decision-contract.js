'use strict';

const VERSION='TAKY_RUNTIME_DECISION_CONTRACT_V1';
const clean=v=>String(v??'').trim();

const PRIORITY={CRITICAL:4,HIGH:3,MEDIUM:2,LOW:1};

function normalizeIntent(x={}){
  return {
    intent:clean(x.intent),
    priority:clean(x.priority)||'LOW',
    basis:x.bases||[x.basis].filter(Boolean),
    targets:Array.isArray(x.targets)?x.targets:[]
  };
}

function derive({learner_state={},feedback_intent={},prerequisite_readiness=null}={}){
  if(!learner_state?.ok)return {ok:false,reason:'LEARNER_STATE_REQUIRED'};
  if(!feedback_intent?.ok)return {ok:false,reason:'FEEDBACK_INTENT_REQUIRED'};

  const blockers=[];
  const advisories=[];
  const state=learner_state.inferred||{};
  const suff=state.evidence_sufficiency||'NONE';

  if(suff==='NONE')blockers.push({code:'NO_EVIDENCE',priority:'HIGH'});
  else if(suff==='SPARSE')advisories.push({code:'SPARSE_EVIDENCE',priority:'MEDIUM'});

  if(state.instrument_change_detected===true)blockers.push({code:'INSTRUMENT_CHANGE_HOLD',priority:'HIGH'});
  if(prerequisite_readiness?.readiness==='PREREQUISITE_RISK'){
    advisories.push({
      code:'PREREQUISITE_RISK',
      priority:'HIGH',
      details:{
        missing:prerequisite_readiness.missing_prerequisites||[],
        at_risk:prerequisite_readiness.at_risk_prerequisites||[]
      }
    });
  }

  const intents=(feedback_intent.intents||[]).map(normalizeIntent)
    .sort((a,b)=>(PRIORITY[b.priority]||0)-(PRIORITY[a.priority]||0)||a.intent.localeCompare(b.intent));

  const seen=new Set();
  const actions=[];
  for(const i of intents){
    if(!i.intent||seen.has(i.intent))continue;
    seen.add(i.intent);
    actions.push(i);
  }

  const hold=blockers.some(b=>b.priority==='HIGH'||b.priority==='CRITICAL');
  return {
    ok:true,
    decision_contract:VERSION,
    scope:learner_state.scope,
    state_summary:{
      evidence_sufficiency:suff,
      trend:state.trend||'INSUFFICIENT_EVIDENCE',
      retention_signal:state.retention_signal||'MODEL_NOT_BOUND',
      recovery_signal:state.recovery_signal||'INSUFFICIENT_TARGET_IDENTITY',
      assistance_dependency_signal:state.assistance_dependency_signal||'UNKNOWN',
      repeated_confusion_signal:state.repeated_confusion_signal||'NONE_OBSERVED',
      prerequisite_readiness:prerequisite_readiness?.readiness||'NOT_PROVIDED'
    },
    blockers,
    advisories,
    pedagogical_actions:actions,
    execution_status:hold?'HOLD_FOR_MORE_RELIABLE_INTERPRETATION':'PEDAGOGICAL_ACTION_AVAILABLE',
    authority:'LEARNING_DECISION_INTENT_ONLY',
    can_influence:[
      'ACTIVITY_SEQUENCE',
      'CHECKPOINT_SELECTION',
      'RECOVERY_INTENSITY',
      'ASSISTANCE_FADING',
      'FEEDBACK_FOCUS',
      'SPECIALIST_ROUTING_INTENT'
    ],
    cannot_influence:[
      'SCHEDULE_DATE',
      'PLANNER_DATE',
      'DUE_AT',
      'DEADLINE',
      'ASSIGNMENT_FACT',
      'FINAL_UI_COPY'
    ],
    consumer_contract:{
      ready:'MAY_TRANSLATE_INTENT_TO_EXECUTION_PLAN',
      planner:'OWNS_DATED_ALLOCATION',
      specialist:'OWNS_INTERACTION_EXECUTION_AND_EVIDENCE'
    }
  };
}

function validate(d={}){
  const issues=[];
  if(!d?.ok)issues.push('DECISION_NOT_OK');
  if(d.authority!=='LEARNING_DECISION_INTENT_ONLY')issues.push('AUTHORITY_INVALID');
  if(d.consumer_contract?.planner!=='OWNS_DATED_ALLOCATION')issues.push('PLANNER_BOUNDARY_INVALID');
  const forbidden=['schedule_date','planner_date','due_at','due_date','deadline'];
  const walk=v=>{
    if(!v||typeof v!=='object')return false;
    for(const [k,n] of Object.entries(v)){
      if(forbidden.includes(k))return true;
      if(walk(n))return true;
    }
    return false;
  };
  if(walk(d))issues.push('SCHEDULE_AUTHORITY_LEAK');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,derive,validate});
