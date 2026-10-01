'use strict';

const VERSION='TAKY_LANGUAGE_GROWTH_PROFILE_V2';
const DIMENSIONS=Object.freeze(['VOCABULARY','GRAMMAR','EXPRESSION','THINKING','ENGLISH_THINKING']);
const clean=v=>String(v??'').trim();
const finite=v=>Number.isFinite(Number(v))?Number(v):null;

function normalizeSignal(raw={}){
  const dimension=clean(raw.dimension).toUpperCase();
  if(!DIMENSIONS.includes(dimension))return null;
  const outcome=clean(raw.outcome).toUpperCase();
  const normalizedOutcome=['SUCCESS','PARTIAL','FAIL'].includes(outcome)?outcome:'UNKNOWN';
  const depth=finite(raw.depth);
  return {
    dimension,
    outcome:normalizedOutcome,
    assisted:raw.assisted===true,
    transfer:raw.transfer===true,
    direct_english:raw.direct_english===true?true:raw.direct_english===false?false:null,
    kind:clean(raw.kind).toUpperCase()||null,
    target_id:clean(raw.target_id||raw.learning_target_id)||null,
    depth:Number.isFinite(depth)?Math.max(0,Math.min(5,depth)):null,
    evidence_ref:clean(raw.evidence_ref)||null
  };
}

function signalsFromEvidence(evidence=[]){
  const out=[];
  for(const e of Array.isArray(evidence)?evidence:[]){
    const rows=Array.isArray(e?.language_growth_signals)?e.language_growth_signals:[];
    for(const raw of rows){
      const signal=normalizeSignal(raw);
      if(signal){
        const verified=e.verified_outcome===0||e.verified_outcome===1||
          e?.verification?.authority==='LEARNING_VERIFICATION_RECEIPT';
        const execution=e.growth_execution_context||{};
        out.push({
          ...signal,
          event_id:clean(e.event_id||e.evidence_id)||null,
          observed_at:clean(e.observed_at)||null,
          source_app:clean(e.source_app)||null,
          verified,
          evidence_strength:verified?'VERIFIED':'OBSERVATION',
          applied_learning_intensity:clean(execution.learning_intensity).toUpperCase()||null,
          applied_expression_level:clean(execution.expression_level).toUpperCase()||null,
          applied_question_depth:Number.isFinite(Number(execution.question_depth))
            ?Number(execution.question_depth):null,
          applied_hint_strength:clean(execution.hint_strength).toUpperCase()||null
        });
      }
    }
  }
  return out;
}

function expressionRank(level){
  const m=String(level||'').match(/^L([1-5])_/);
  return m?Number(m[1]):null;
}

function score(signal){
  const base=signal.outcome==='SUCCESS'?1:signal.outcome==='PARTIAL'?0.5:signal.outcome==='FAIL'?0:0.5;
  return signal.assisted?base*0.75:base;
}

function classify(rows=[]){
  if(!rows.length)return {
    state:'UNKNOWN',confidence:'LOW',signal_count:0,evaluable_signal_count:0,
    verified_count:0,observation_count:0,source_app_count:0,
    unassisted_count:0,transfer_count:0,average_score:null,max_depth:null,
    direct_english_ratio:null
  };

  const evaluable=rows.filter(x=>x.outcome!=='UNKNOWN');
  const verified=evaluable.filter(x=>x.verified===true);
  const observed=evaluable.filter(x=>x.verified!==true);
  const apps=[...new Set(evaluable.map(x=>clean(x.source_app)).filter(Boolean))];
  const depths=rows.map(x=>x.depth).filter(Number.isFinite);
  const english=rows.map(x=>x.direct_english).filter(x=>typeof x==='boolean');
  const directRatio=english.length?english.filter(Boolean).length/english.length:null;

  if(!evaluable.length)return {
    state:'UNKNOWN',confidence:'LOW',signal_count:rows.length,evaluable_signal_count:0,
    verified_count:0,observation_count:0,source_app_count:0,
    unassisted_count:0,transfer_count:rows.filter(x=>x.transfer===true).length,
    average_score:null,max_depth:depths.length?Math.max(...depths):null,
    direct_english_ratio:Number.isFinite(directRatio)?Math.round(directRatio*100)/100:null,
    minimal_hint_success_count:minimalHintSuccess,
    max_success_expression_level:maxSuccessExpressionLevel
  };

  const scored=evaluable.map(score);
  const avg=scored.reduce((a,b)=>a+b,0)/scored.length;
  const unassisted=evaluable.filter(x=>x.assisted!==true).length;
  const transfer=evaluable.filter(x=>x.transfer===true).length;
  const crossApp=apps.length>=2;
  const successfulChallenges=evaluable.filter(x=>x.outcome==='SUCCESS'&&x.assisted!==true);
  const minimalHintSuccess=successfulChallenges.filter(x=>
    x.applied_hint_strength==='MINIMAL_CUE'||!x.applied_hint_strength).length;
  const expressionRanks=successfulChallenges.map(x=>expressionRank(x.applied_expression_level))
    .filter(Number.isFinite);
  const maxSuccessExpressionLevel=expressionRanks.length?Math.max(...expressionRanks):null;

  let confidence='LOW';
  if(verified.length>=2||(evaluable.length>=4&&crossApp))confidence='HIGH';
  else if(verified.length>=1||evaluable.length>=2)confidence='MEDIUM';

  let state='EARLY_SIGNAL';
  if(evaluable.length>=2){
    if(avg<0.40)state='NEEDS_SUPPORT';
    else state='DEVELOPING';
  }

  const dimension=clean(rows[0]?.dimension).toUpperCase();
  const challengeSensitive=['EXPRESSION','THINKING','ENGLISH_THINKING'].includes(dimension);
  const challengeReady=!challengeSensitive||verified.length>=1||
    minimalHintSuccess>=1||Number(maxSuccessExpressionLevel)>=2;
  const stretchEvidence=
    avg>=0.80 &&
    unassisted>=2 &&
    challengeReady &&
    (
      verified.length>=1 ||
      (evaluable.length>=3&&crossApp&&transfer>=1)
    );
  if(stretchEvidence)state='READY_TO_STRETCH';

  return {
    state,
    confidence,
    signal_count:rows.length,
    evaluable_signal_count:evaluable.length,
    verified_count:verified.length,
    observation_count:observed.length,
    source_app_count:apps.length,
    unassisted_count:unassisted,
    transfer_count:transfer,
    average_score:Math.round(avg*100)/100,
    max_depth:depths.length?Math.max(...depths):null,
    direct_english_ratio:Number.isFinite(directRatio)?Math.round(directRatio*100)/100:null
  };
}
function ageLanguageLoad(context={}){
  const grade=finite(context.grade);
  const age=finite(context.age);
  if(Number.isFinite(grade)){
    if(grade<=2)return 'VERY_SIMPLE';
    if(grade<=6)return 'SIMPLE';
    return 'STANDARD';
  }
  if(Number.isFinite(age)){
    if(age<=8)return 'VERY_SIMPLE';
    if(age<=12)return 'SIMPLE';
    return 'STANDARD';
  }
  return 'SIMPLE';
}

function derive({evidence=[],learner_context={}}={}){
  const signals=signalsFromEvidence(evidence);
  const dimensions={};
  for(const dimension of DIMENSIONS){
    dimensions[dimension]=classify(signals.filter(x=>x.dimension===dimension));
  }
  const directDim=dimensions.ENGLISH_THINKING;
  const direct=directDim.direct_english_ratio;
  const directEvidence=directDim.signal_count||0;
  const allSignals=Object.values(dimensions);
  const crossAppDimensions=allSignals.filter(x=>(x.source_app_count||0)>=2).length;
  const verifiedGrowthSignals=allSignals.reduce((n,x)=>n+(x.verified_count||0),0);
  return {
    ok:true,
    version:VERSION,
    authority:'LEARNING_ENGINE_DERIVED_GROWTH_STATE',
    learner_context:{
      grade:Number.isFinite(finite(learner_context.grade))?finite(learner_context.grade):null,
      age:Number.isFinite(finite(learner_context.age))?finite(learner_context.age):null,
      language_load:ageLanguageLoad(learner_context)
    },
    dimensions,
    cross_dimension:{
      translation_dependency_signal:directEvidence<2||!Number.isFinite(direct)
        ?'UNKNOWN'
        :(direct<0.4?'LIKELY_TRANSLATION_DEPENDENT':direct>=0.7?'DIRECT_ENGLISH_EMERGING':'MIXED'),
      direct_english_evidence_count:directEvidence,
      transfer_evidence_count:signals.filter(x=>x.transfer===true).length,
      cross_app_dimension_count:crossAppDimensions,
      verified_growth_signal_count:verifiedGrowthSignals
    },
    evidence_ids:[...new Set(signals.map(x=>x.event_id).filter(Boolean))],
    signal_count:signals.length,
    guards:{
      age_changes_language_load_not_thinking_ceiling:true,
      one_success_is_not_growth_mastery:true,
      missing_dimension_is_unknown_not_failure:true,
      app_score_is_not_growth_state:true,
      observation_only_cannot_self_promote_to_high_confidence:true,
      cross_app_or_verified_evidence_required_for_stretch:true,
      sparse_direct_english_signal_does_not_create_translation_dependency:true,
      applied_challenge_context_is_evidence_not_authority:true,
      scaffolded_success_does_not_auto_upshift_expression_level:true
    }
  };
}

function validate(profile={}){
  const issues=[];
  if(profile?.ok!==true)issues.push('PROFILE_NOT_OK');
  if(profile.authority!=='LEARNING_ENGINE_DERIVED_GROWTH_STATE')issues.push('AUTHORITY_INVALID');
  if(profile.guards?.age_changes_language_load_not_thinking_ceiling!==true)issues.push('AGE_GUARD_MISSING');
  for(const d of DIMENSIONS){
    if(!profile.dimensions?.[d])issues.push('DIMENSION_MISSING:'+d);
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,DIMENSIONS,normalizeSignal,signalsFromEvidence,derive,validate});
