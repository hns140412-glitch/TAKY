'use strict';

const VERSION='TAKY_HIDE_VOCABULARY_ROUTING_POLICY_V1';
const AUTHORITY='LEARNING_ENGINE_SPECIALIST_POLICY_INTENT_ONLY';
const MODES=new Set(['TRACE','LINK','CORE','RECALL']);
const clean=v=>String(v??'').trim();
const finite=v=>Number.isFinite(Number(v))?Number(v):null;

function targetId(e={}){
  return clean(e.learning_target_id||e?.memory?.item_signal?.item_id||e?.memory?.item_signal?.word);
}
function outcomeOf(e={}){
  if(e.verified_outcome===0||e.verified_outcome===1)return e.verified_outcome;
  const observed=e?.memory?.item_signal?.correct;
  return typeof observed==='boolean'?(observed?1:0):null;
}
function modeOf(e={}){
  const m=clean(e.interaction_mode||e?.memory?.item_signal?.mode).toUpperCase();
  return MODES.has(m)?m:'UNKNOWN';
}
function weaknessTokens(e={}){
  const raw=e?.memory?.item_signal?.weakness;
  const list=Array.isArray(raw)?raw:[raw];
  return list.map(clean).filter(Boolean).map(x=>x.toUpperCase());
}
function confusionPresent(e={}){
  const v=e?.memory?.item_signal?.confusion;
  if(Array.isArray(v))return v.length>0;
  return !!clean(v);
}
function dayKey(e={}){
  const t=clean(e.observed_at);
  return Number.isFinite(Date.parse(t))?new Date(t).toISOString().slice(0,10):null;
}
function sortRows(rows=[]){
  return [...rows].sort((a,b)=>Date.parse(a.observed_at||0)-Date.parse(b.observed_at||0));
}

function classifyWord(rows=[]){
  const ordered=sortRows(rows);
  if(!ordered.length){
    return {
      memory_state:'NEW_OR_UNOBSERVED',
      recommended_mode:'TRACE',
      priority:'HIGH',
      delayed_recall:null,
      reasons:['NO_WORD_EVIDENCE']
    };
  }

  const latest=ordered.at(-1);
  const latestMode=modeOf(latest);
  const latestOutcome=outcomeOf(latest);
  const anyConfusion=ordered.some(confusionPresent);
  const weaknesses=new Set(ordered.flatMap(weaknessTokens));
  const assisted=ordered.filter(e=>e.assisted===true||clean(e.assistance)==='ASSISTED').length;
  const unassistedCorrect=ordered.filter(e=>
    (e.assisted===false||clean(e.assistance)==='UNASSISTED')&&outcomeOf(e)===1).length;
  const failed=ordered.filter(e=>outcomeOf(e)===0).length;
  const observedDays=new Set(ordered.map(dayKey).filter(Boolean)).size;
  const explicitSpaced=ordered.some(e=>e?.memory?.item_signal?.spaced_evidence===true);
  const orthographic=weaknesses.has('ORTHOGRAPHIC')||weaknesses.has('SPELLING')||
    weaknesses.has('CORE')||(latestMode==='CORE'&&latestOutcome===0);
  const needsDelayed=latestOutcome===1 && unassistedCorrect<2;

  if(anyConfusion){
    return {
      memory_state:'CONFUSION_LINK_WEAK',
      recommended_mode:'LINK',
      priority:'HIGH',
      delayed_recall:{
        kind:'AFTER_INTERVENING_ITEMS',
        min_intervening_items:3,
        max_intervening_items:5,
        reason:'CONFUSION_REQUIRES_RETRIEVAL_RECHECK'
      },
      reasons:['CONFUSION_SIGNAL']
    };
  }
  if(orthographic){
    return {
      memory_state:'ORTHOGRAPHIC_WEAK',
      recommended_mode:'CORE',
      priority:failed>1?'HIGH':'MEDIUM',
      delayed_recall:{
        kind:'AFTER_INTERVENING_ITEMS',
        min_intervening_items:3,
        max_intervening_items:5,
        reason:'SPELLING_RETRIEVAL_RECHECK'
      },
      reasons:['ORTHOGRAPHIC_OR_CORE_FAILURE']
    };
  }
  if(latestOutcome===0){
    return {
      memory_state:latestMode==='TRACE'?'TRACE_RECOGNITION_WEAK':'RETRIEVAL_WEAK',
      recommended_mode:latestMode==='TRACE'?'TRACE':'RECALL',
      priority:'HIGH',
      delayed_recall:{
        kind:'AFTER_RECOVERY',
        min_intervening_items:3,
        max_intervening_items:5,
        reason:'FAILED_RETRIEVAL_NEEDS_RECOVERY_THEN_DELAY'
      },
      reasons:['LATEST_FAILURE']
    };
  }
  if(assisted>0 && unassistedCorrect===0){
    return {
      memory_state:'ASSISTED_ONLY',
      recommended_mode:'RECALL',
      priority:'HIGH',
      delayed_recall:{
        kind:'AFTER_INTERVENING_ITEMS',
        min_intervening_items:3,
        max_intervening_items:5,
        reason:'ASSISTED_SUCCESS_NEEDS_UNASSISTED_RECALL'
      },
      reasons:['ASSISTED_WITHOUT_UNASSISTED_SUCCESS']
    };
  }
  if((observedDays>=2||explicitSpaced)&&unassistedCorrect>=2){
    return {
      memory_state:'SPACED_UNASSISTED_STABLE',
      recommended_mode:'RECALL',
      priority:'LOW',
      delayed_recall:{
        kind:'NEXT_SESSION_SPACED_RECALL',
        reason:'MAINTENANCE_ONLY'
      },
      reasons:['MULTI_DAY_UNASSISTED_SUCCESS']
    };
  }
  if(needsDelayed||unassistedCorrect>0){
    return {
      memory_state:'RECENT_UNASSISTED_SUCCESS',
      recommended_mode:'RECALL',
      priority:'MEDIUM',
      delayed_recall:{
        kind:'AFTER_INTERVENING_ITEMS',
        min_intervening_items:3,
        max_intervening_items:5,
        reason:'SHORT_DELAY_RECALL_CONFIRMATION'
      },
      reasons:['UNASSISTED_SUCCESS_NOT_YET_SPACED']
    };
  }
  return {
    memory_state:'OBSERVED_UNCERTAIN',
    recommended_mode:'TRACE',
    priority:'MEDIUM',
    delayed_recall:null,
    reasons:['EVIDENCE_PRESENT_BUT_STATE_UNRESOLVED']
  };
}

function currentSetSignal(wordPolicies=[]){
  const current=wordPolicies.filter(x=>x.origin==='CURRENT');
  if(!current.length)return {level:'UNKNOWN',reason:'NO_CURRENT_WORD_SIGNAL'};
  const high=current.filter(x=>x.priority==='HIGH').length;
  const stable=current.filter(x=>['SPACED_UNASSISTED_STABLE','RECENT_UNASSISTED_SUCCESS'].includes(x.memory_state)).length;
  const traceWeak=current.filter(x=>x.memory_state==='TRACE_RECOGNITION_WEAK').length;
  const strongRate=stable/current.length;
  const highRate=high/current.length;
  if(strongRate>=0.8&&highRate<=0.2)return {level:'STRONG',reason:'CURRENT_WORDS_RECALLING_WELL'};
  if(highRate>=0.4||traceWeak/current.length>=0.3)return {level:'WEAK',reason:'CURRENT_WORDS_NEED_MORE_FOCUS'};
  return {level:'BALANCED',reason:'CURRENT_WORDS_MIXED'};
}

function pastMix(signal){
  // 12 current + 24 past is the established baseline => 2/3 past exposure.
  // This changes prompt mix only. Current assignment words are never dropped.
  if(signal.level==='STRONG')return {
    past_word_share:0.75,current_word_share:0.25,
    baseline_past_word_share:2/3,current_words_mandatory:true,
    reason:'CURRENT_TRACE_AND_RECALL_SIGNAL_STRONG__ALLOW_MORE_PAST_WORD_EXPOSURE'
  };
  if(signal.level==='WEAK')return {
    past_word_share:0.50,current_word_share:0.50,
    baseline_past_word_share:2/3,current_words_mandatory:true,
    reason:'CURRENT_WORDS_WEAK__PROTECT_CURRENT_ASSIGNMENT_FOCUS'
  };
  return {
    past_word_share:2/3,current_word_share:1/3,
    baseline_past_word_share:2/3,current_words_mandatory:true,
    reason:'KEEP_ESTABLISHED_12_NEW_24_PAST_BASELINE'
  };
}

function derive({evidence=[],current_word_ids=[],past_word_ids=[]}={}){
  const current=new Set((Array.isArray(current_word_ids)?current_word_ids:[]).map(clean).filter(Boolean));
  const past=new Set((Array.isArray(past_word_ids)?past_word_ids:[]).map(clean).filter(Boolean));
  const ids=[...new Set([...current,...past])];
  const byId=new Map(ids.map(id=>[id,[]]));
  for(const row of Array.isArray(evidence)?evidence:[]){
    const id=targetId(row);
    if(!id||!byId.has(id))continue;
    byId.get(id).push(row);
  }

  const wordPolicies=ids.map(id=>{
    const base=classifyWord(byId.get(id)||[]);
    return {
      learning_target_id:id,
      origin:current.has(id)?'CURRENT':'PAST',
      ...base
    };
  }).sort((a,b)=>{
    const p={HIGH:3,MEDIUM:2,LOW:1};
    return (p[b.priority]||0)-(p[a.priority]||0)||a.learning_target_id.localeCompare(b.learning_target_id);
  });

  const signal=currentSetSignal(wordPolicies);
  const mix=pastMix(signal);
  const delayed=wordPolicies.filter(x=>x.delayed_recall).map(x=>({
    learning_target_id:x.learning_target_id,
    origin:x.origin,
    priority:x.priority,
    recommended_mode:'RECALL',
    ...x.delayed_recall
  }));

  return {
    ok:true,
    version:VERSION,
    authority:AUTHORITY,
    word_policies:wordPolicies,
    past_word_mix:mix,
    current_set_signal:signal,
    delayed_recall_queue:delayed,
    guards:{
      current_words_never_dropped:true,
      ratio_is_prompt_mix_not_assignment_mutation:true,
      delayed_recall_has_no_calendar_date:true,
      planner_owns_dated_allocation:true,
      hide_executes_interaction_only:true,
      no_mastery_claim:true
    },
    cannot_influence:['SCHEDULE_DATE','PLANNER_DATE','DUE_AT','DEADLINE','ASSIGNMENT_FACT']
  };
}

function validate(policy={}){
  const issues=[];
  if(policy?.ok!==true)issues.push('POLICY_NOT_OK');
  if(policy.authority!==AUTHORITY)issues.push('AUTHORITY_INVALID');
  if(!Number.isFinite(policy?.past_word_mix?.past_word_share))issues.push('PAST_WORD_SHARE_REQUIRED');
  if(policy?.past_word_mix?.current_words_mandatory!==true)issues.push('CURRENT_WORD_MANDATORY_GUARD_REQUIRED');
  const forbidden=['schedule_date','planner_date','due_at','due_date','deadline'];
  const walk=v=>{
    if(!v||typeof v!=='object')return false;
    for(const [k,n] of Object.entries(v)){
      if(forbidden.includes(k))return true;
      if(walk(n))return true;
    }
    return false;
  };
  if(walk(policy))issues.push('SCHEDULE_AUTHORITY_LEAK');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,AUTHORITY,derive,validate});
