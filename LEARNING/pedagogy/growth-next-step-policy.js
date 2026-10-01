'use strict';

const VERSION='TAKY_GROWTH_NEXT_STEP_POLICY_V2';
const AUTHORITY='LEARNING_ENGINE_GROWTH_INTENT_ONLY';
const Profile=require('./language-growth-profile.js');
const clean=v=>String(v??'').trim();

function officialItems(learningIndex={}){
  const rows=Array.isArray(learningIndex?.semantic_items)?learningIndex.semantic_items:[];
  return rows.filter(x=>{
    const a=clean(x.authority_class).toUpperCase();
    const f=clean(x.source_family).toUpperCase();
    return a.includes('OFFICIAL')||f.includes('OFFICIAL')||f.includes('CURRICULUM');
  });
}

function growthResources(learningIndex={}){
  const rows=Array.isArray(learningIndex?.semantic_items)?learningIndex.semantic_items:[];
  const official=officialItems(learningIndex);
  const preferred=official.length?official:rows;
  const defs=[],chunks=[],collocations=[],grammar=[],moves=[],questions=[],production=[],englishThinking=[];
  for(const item of preferred){
    const g=item?.semantic_groups?.language_growth||{};
    const push=(arr,value)=>{
      if(Array.isArray(value))arr.push(...value);
      else if(value!==undefined&&value!==null&&clean(value))arr.push(value);
    };
    push(defs,g.easy_english_definition);
    push(chunks,g.expression_chunks);
    push(collocations,g.natural_collocations);
    push(grammar,g.grammar_patterns);
    push(moves,g.thinking_moves);
    push(questions,g.question_stems);
    push(production,g.production_targets);
    push(englishThinking,g.english_thinking_support);
  }
  const uniq=xs=>[...new Set(xs.map(x=>typeof x==='string'?x.trim():JSON.stringify(x)).filter(Boolean))]
    .map(x=>{try{return x.startsWith('{')||x.startsWith('[')?JSON.parse(x):x}catch{return x}});
  return {
    curriculum_verified:official.length>0,
    curriculum_source_refs:[...new Set(official.map(x=>x.source_ref).filter(Boolean))],
    easy_english_definitions:uniq(defs),
    expression_chunks:uniq(chunks),
    natural_collocations:uniq(collocations),
    grammar_patterns:uniq(grammar),
    thinking_moves:uniq(moves),
    question_stems:uniq(questions),
    production_targets:uniq(production),
    english_thinking_support:uniq(englishThinking)
  };
}

function stanceFor(profile={}){
  const dims=profile.dimensions||{};
  const rows=['VOCABULARY','GRAMMAR','EXPRESSION','THINKING'].map(k=>dims[k]||{});
  const needs=rows.filter(x=>x.state==='NEEDS_SUPPORT'&&x.confidence!=='LOW').length;
  const stretch=rows.filter(x=>x.state==='READY_TO_STRETCH'&&x.confidence!=='LOW').length;
  const cross=profile.cross_dimension||{};
  const evidenceReady=(cross.verified_growth_signal_count||0)>0||(cross.cross_app_dimension_count||0)>0;
  if(needs>=2)return 'SCAFFOLD_LEAD';
  if(stretch>=2&&evidenceReady)return 'TRANSFER_PUSH';
  return 'ELICIT_PULL';
}

function questionDepth(profile={},stance='ELICIT_PULL'){
  const thinking=profile.dimensions?.THINKING||{};
  const expression=profile.dimensions?.EXPRESSION||{};
  let depth=stance==='SCAFFOLD_LEAD'?1:stance==='TRANSFER_PUSH'?4:2;
  if(thinking.max_depth>=3&&thinking.state==='READY_TO_STRETCH')depth=5;
  else if(thinking.state==='READY_TO_STRETCH'||expression.state==='READY_TO_STRETCH')depth=Math.max(depth,4);
  else if(thinking.state==='DEVELOPING')depth=Math.max(depth,3);
  return Math.max(1,Math.min(5,depth));
}

function hintPolicy(stance){
  if(stance==='SCAFFOLD_LEAD')return {
    level:'STRONG_SCAFFOLD',
    sequence:['EASY_MEANING_OR_MODEL','EXPRESSION_CHUNK','PARTIAL_FRAME','ASK_CHILD_TO_COMPLETE']
  };
  if(stance==='TRANSFER_PUSH')return {
    level:'MINIMAL_CUE',
    sequence:['WAIT','SHORT_CUE','ASK_FOR_REASON_OR_NEW_CONTEXT']
  };
  return {
    level:'PARTIAL_FRAME',
    sequence:['SHORT_QUESTION','KEY_CHUNK_OR_PATTERN','ASK_CHILD_TO_FINISH']
  };
}

function growthMoves(profile={},resources={}){
  const dims=profile.dimensions||{};
  const steps=[];
  const add=(dimension,intent,reason)=>steps.push({dimension,intent,reason});
  if(['UNKNOWN','EARLY_SIGNAL','NEEDS_SUPPORT'].includes(dims.VOCABULARY?.state)){
    add('VOCABULARY','BUILD_MEANING_AND_WORD_NETWORK','VOCABULARY_NOT_STABLE');
  }else add('VOCABULARY','USE_WORD_IN_CONTEXT','VOCABULARY_READY_FOR_CONTEXT');

  if(['UNKNOWN','EARLY_SIGNAL','NEEDS_SUPPORT'].includes(dims.GRAMMAR?.state)){
    add('GRAMMAR','NOTICE_PATTERN_THROUGH_EXAMPLE','GRAMMAR_NEEDS_PATTERN_SUPPORT');
  }else add('GRAMMAR','TRANSFORM_OR_RECOMBINE_PATTERN','GRAMMAR_CAN_BE_STRETCHED');

  if(['UNKNOWN','EARLY_SIGNAL','NEEDS_SUPPORT'].includes(dims.EXPRESSION?.state)){
    add('EXPRESSION','BUILD_WITH_CHUNK_NOT_WORD_BY_WORD_TRANSLATION','EXPRESSION_NEEDS_CHUNK_SUPPORT');
  }else add('EXPRESSION','EXPAND_AND_PERSONALIZE','EXPRESSION_READY_TO_EXPAND');

  if(['UNKNOWN','EARLY_SIGNAL','NEEDS_SUPPORT'].includes(dims.THINKING?.state)){
    add('THINKING','ASK_ONE_REASON_OR_CONNECTION','THINKING_NEEDS_ONE_STEP');
  }else add('THINKING','COMPARE_EXPLAIN_INFER_OR_CREATE','THINKING_READY_FOR_DEEPER_QUESTION');

  const english=dims.ENGLISH_THINKING?.state;
  const translation=profile.cross_dimension?.translation_dependency_signal;
  if(translation==='LIKELY_TRANSLATION_DEPENDENT'||['UNKNOWN','EARLY_SIGNAL','NEEDS_SUPPORT'].includes(english)){
    add('ENGLISH_THINKING','ENGLISH_FIRST_WITH_KOREAN_FALLBACK','DIRECT_ENGLISH_PROCESSING_NEEDS_SUPPORT');
  }else{
    add('ENGLISH_THINKING','ENGLISH_FIRST_CONTEXT_AND_CHUNK','DIRECT_ENGLISH_PROCESSING_EMERGING');
  }

  return steps;
}

function overallConfidence(profile={}){
  const rows=Object.values(profile.dimensions||{});
  const high=rows.filter(x=>x?.confidence==='HIGH').length;
  const medium=rows.filter(x=>x?.confidence==='MEDIUM').length;
  const verified=Number(profile.cross_dimension?.verified_growth_signal_count||0);
  const cross=Number(profile.cross_dimension?.cross_app_dimension_count||0);
  if(verified>=2||high>=2||(cross>=2&&medium>=2))return 'HIGH';
  if(verified>=1||high>=1||medium>=2||cross>=1)return 'MEDIUM';
  return 'LOW';
}

function expressionLevel(profile={},depth=1){
  const expression=profile.dimensions?.EXPRESSION||{};
  const thinking=profile.dimensions?.THINKING||{};
  if(depth>=5&&thinking.state==='READY_TO_STRETCH')return 'L5_TRANSFER_CREATION';
  if(depth>=4)return 'L4_REASONED_RESPONSE';
  if(depth>=3&&expression.state!=='NEEDS_SUPPORT')return 'L3_EXPANDED_SENTENCE';
  if(depth>=2)return 'L2_SIMPLE_SENTENCE';
  return 'L1_CHUNK_OR_PHRASE';
}

function definitionLevel(profile={}){
  const load=profile.learner_context?.language_load||'SIMPLE';
  const direct=profile.cross_dimension?.translation_dependency_signal||'UNKNOWN';
  if(direct==='DIRECT_ENGLISH_EMERGING'&&load!=='VERY_SIMPLE')
    return 'CONTEXTUAL_EASY_ENGLISH';
  if(direct==='LIKELY_TRANSLATION_DEPENDENT')
    return 'EASY_ENGLISH_WITH_KOREAN_FALLBACK';
  return load==='VERY_SIMPLE'?'VERY_SIMPLE_ENGLISH_WITH_CONTEXT':'EASY_ENGLISH';
}

function growthControl(profile={},stance='ELICIT_PULL',depth=1,hints={}){
  const confidence=overallConfidence(profile);
  let intensity=stance==='SCAFFOLD_LEAD'?'SUPPORT_BUILD':
    stance==='TRANSFER_PUSH'?'STRETCH_TRANSFER':'BUILD_CONNECT';
  if(confidence==='LOW'&&intensity==='STRETCH_TRANSFER')intensity='BUILD_CONNECT';

  const dims=profile.dimensions||{};
  const targetDimensions=['VOCABULARY','GRAMMAR','EXPRESSION','THINKING','ENGLISH_THINKING']
    .map(d=>({dimension:d,state:dims[d]?.state||'UNKNOWN',confidence:dims[d]?.confidence||'LOW'}))
    .sort((a,b)=>{
      const rank=s=>s==='NEEDS_SUPPORT'?0:s==='EARLY_SIGNAL'?1:s==='DEVELOPING'?2:s==='UNKNOWN'?3:4;
      return rank(a.state)-rank(b.state);
    })
    .slice(0,3)
    .map(x=>x.dimension);

  return {
    evidence_confidence:confidence,
    learning_intensity:intensity,
    expression_level:expressionLevel(profile,depth),
    easy_english_level:definitionLevel(profile),
    question_depth:depth,
    hint_strength:hints.level||'PARTIAL_FRAME',
    hint_fade:stance==='SCAFFOLD_LEAD'?'HOLD_AND_FADE_AFTER_SUCCESS':
      stance==='TRANSFER_PUSH'?'MINIMAL_CUE':'FADE_ONE_STEP_WHEN_SUCCESSFUL',
    target_dimensions:targetDimensions,
    challenge_direction:stance==='SCAFFOLD_LEAD'?'STABILIZE':
      stance==='TRANSFER_PUSH'?'TRANSFER':'EXTEND',
    stability_guard:{
      low_confidence_cannot_upshift_to_transfer:true,
      one_event_cannot_raise_expression_level_by_itself:true,
      verified_or_cross_app_evidence_required_for_stretch:true
    }
  };
}

function snapHandoff(profile={},resources={},stance,depth,control=null){
  const vocab=profile.dimensions?.VOCABULARY?.state;
  const eligible=['DEVELOPING','READY_TO_STRETCH'].includes(vocab);
  return {
    from_app:'hide-seek',
    to_app:'snap-pop',
    eligible,
    authority:'LEARNING_ENGINE_HANDOFF_INTENT_ONLY',
    task_intent:!eligible?'KEEP_BUILDING_LEXICAL_BASE':
      depth>=4?'USE_AND_EXPLAIN_IN_NEW_CONTEXT':'USE_IN_OWN_SHORT_SENTENCE_OR_SPEECH',
    support_phase:stance,
    growth_control:control?JSON.parse(JSON.stringify(control)):null,
    prompt_language:'ENGLISH_FIRST_KOREAN_FALLBACK',
    material:{
      expression_chunks:resources.expression_chunks.slice(0,4),
      grammar_patterns:resources.grammar_patterns.slice(0,3),
      production_targets:resources.production_targets.slice(0,3)
    },
    child_authorship_required:true,
    final_answer_generation_forbidden:true
  };
}

function derive({growth_profile,learning_index=null}={}){
  if(!growth_profile?.ok)return {ok:false,reason:'GROWTH_PROFILE_REQUIRED'};
  const checked=Profile.validate(growth_profile);
  if(!checked.ok)return {ok:false,reason:'GROWTH_PROFILE_INVALID',issues:checked.issues};

  const resources=growthResources(learning_index||{});
  const stance=stanceFor(growth_profile);
  const depth=questionDepth(growth_profile,stance);
  const hints=hintPolicy(stance);
  const moves=growthMoves(growth_profile,resources);
  const control=growthControl(growth_profile,stance,depth,hints);

  return {
    ok:true,
    version:VERSION,
    authority:AUTHORITY,
    support_phase:stance,
    question_depth:{
      level:depth,
      scale:'1=NOTICE__2=CONNECT__3=EXPLAIN__4=APPLY_TRANSFER__5=CREATE_JUSTIFY',
      age_rule:'AGE_ADJUSTS_WORDING_LOAD_NOT_COGNITIVE_CEILING'
    },
    hint_policy:hints,
    growth_control:control,
    language_load:growth_profile.learner_context?.language_load||'SIMPLE',
    growth_moves:moves,
    language_support:{
      easy_english_definitions:resources.easy_english_definitions.slice(0,4),
      expression_chunks:resources.expression_chunks.slice(0,6),
      natural_collocations:resources.natural_collocations.slice(0,6),
      grammar_patterns:resources.grammar_patterns.slice(0,4),
      english_thinking_support:resources.english_thinking_support.slice(0,4)
    },
    curriculum_grounding:{
      verified:resources.curriculum_verified,
      source_refs:resources.curriculum_source_refs,
      achievement_or_grade_claim_allowed:resources.curriculum_verified
    },
    hide_to_snap_handoff:snapHandoff(growth_profile,resources,stance,depth,control),
    reference_gap_candidate:resources.curriculum_verified?null:{
      gap_type:'CURRICULUM_LANGUAGE_GROWTH_REFERENCE_REQUIRED',
      mining_request_authorized:false,
      reason:'NO_OFFICIAL_CURRICULUM_OR_EDUCATION_INDEX_EVIDENCE_IN_LEARNING_INDEX'
    },
    guards:{
      engine_guides_growth_not_answers:true,
      korean_to_english_word_by_word_translation_is_not_default:true,
      easy_english_definition_preferred_when_grounded:true,
      expression_chunks_preferred_over_isolated_translation:true,
      age_changes_language_load_not_thinking_ceiling:true,
      hide_prepares_language_material_snap_owns_expression_execution:true,
      planner_owns_dates:true,
      growth_intensity_and_expression_level_are_engine_intent_only:true,
      low_confidence_cannot_force_growth_upshift:true
    },
    cannot_influence:['SCHEDULE_DATE','PLANNER_DATE','DUE_AT','DEADLINE','ASSIGNMENT_FACT','FINAL_CHILD_ANSWER']
  };
}

function validate(policy={}){
  const issues=[];
  if(policy?.ok!==true)issues.push('POLICY_NOT_OK');
  if(policy.authority!==AUTHORITY)issues.push('AUTHORITY_INVALID');
  if(!['SCAFFOLD_LEAD','ELICIT_PULL','TRANSFER_PUSH'].includes(policy.support_phase))issues.push('SUPPORT_PHASE_INVALID');
  if(!Number.isInteger(policy?.question_depth?.level)||policy.question_depth.level<1||policy.question_depth.level>5)issues.push('QUESTION_DEPTH_INVALID');
  if(policy.guards?.engine_guides_growth_not_answers!==true)issues.push('GROWTH_GUARD_MISSING');
  if(!['LOW','MEDIUM','HIGH'].includes(policy?.growth_control?.evidence_confidence))issues.push('GROWTH_CONFIDENCE_INVALID');
  if(!['SUPPORT_BUILD','BUILD_CONNECT','STRETCH_TRANSFER'].includes(policy?.growth_control?.learning_intensity))issues.push('LEARNING_INTENSITY_INVALID');
  if(!/^L[1-5]_/.test(String(policy?.growth_control?.expression_level||'')))issues.push('EXPRESSION_LEVEL_INVALID');
  if(policy.hide_to_snap_handoff?.final_answer_generation_forbidden!==true)issues.push('AUTHORSHIP_GUARD_MISSING');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,AUTHORITY,growthResources,derive,validate});
