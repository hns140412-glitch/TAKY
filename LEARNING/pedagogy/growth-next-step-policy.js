'use strict';

const VERSION='TAKY_GROWTH_NEXT_STEP_POLICY_V2';
const AUTHORITY='LEARNING_ENGINE_GROWTH_INTENT_ONLY';
const Profile=require('./language-growth-profile.js');
const clean=v=>String(v??'').trim();

function sourceRole(item={}){
  const role=clean(item.learning_evidence_role).toUpperCase();
  return ['CURRICULUM_ALIGNMENT','LEXICAL_SEMANTICS','LANGUAGE_USAGE','PEDAGOGICAL_USAGE','GENERAL_REFERENCE']
    .includes(role)?role:'GENERAL_REFERENCE';
}
function officialItems(learningIndex={}){
  const rows=Array.isArray(learningIndex?.semantic_items)?learningIndex.semantic_items:[];
  return rows.filter(x=>sourceRole(x)==='CURRICULUM_ALIGNMENT');
}

function growthResources(learningIndex={}){
  const rows=Array.isArray(learningIndex?.semantic_items)?learningIndex.semantic_items:[];
  const official=officialItems(learningIndex);
  const buckets={
    easy_english_definitions:[],
    expression_chunks:[],
    natural_collocations:[],
    grammar_patterns:[],
    thinking_moves:[],
    question_stems:[],
    production_targets:[],
    english_thinking_support:[]
  };
  const provenance=Object.fromEntries(Object.keys(buckets).map(k=>[k,[]]));

  const allowed={
    easy_english_definitions:new Set(['LEXICAL_SEMANTICS','PEDAGOGICAL_USAGE','CURRICULUM_ALIGNMENT','GENERAL_REFERENCE']),
    expression_chunks:new Set(['LANGUAGE_USAGE','PEDAGOGICAL_USAGE','CURRICULUM_ALIGNMENT','GENERAL_REFERENCE']),
    natural_collocations:new Set(['LANGUAGE_USAGE','PEDAGOGICAL_USAGE','GENERAL_REFERENCE']),
    grammar_patterns:new Set(['LANGUAGE_USAGE','PEDAGOGICAL_USAGE','CURRICULUM_ALIGNMENT','GENERAL_REFERENCE']),
    thinking_moves:new Set(['CURRICULUM_ALIGNMENT','PEDAGOGICAL_USAGE','GENERAL_REFERENCE']),
    question_stems:new Set(['CURRICULUM_ALIGNMENT','PEDAGOGICAL_USAGE','GENERAL_REFERENCE']),
    production_targets:new Set(['CURRICULUM_ALIGNMENT','PEDAGOGICAL_USAGE','GENERAL_REFERENCE']),
    english_thinking_support:new Set(['PEDAGOGICAL_USAGE','CURRICULUM_ALIGNMENT','GENERAL_REFERENCE'])
  };

  const fieldMap={
    easy_english_definitions:'easy_english_definition',
    expression_chunks:'expression_chunks',
    natural_collocations:'natural_collocations',
    grammar_patterns:'grammar_patterns',
    thinking_moves:'thinking_moves',
    question_stems:'question_stems',
    production_targets:'production_targets',
    english_thinking_support:'english_thinking_support'
  };

  const push=(arr,value)=>{
    if(Array.isArray(value))arr.push(...value);
    else if(value!==undefined&&value!==null&&clean(value))arr.push(value);
  };
  const uniq=xs=>[...new Set(xs.map(x=>typeof x==='string'?x.trim():JSON.stringify(x)).filter(Boolean))]
    .map(x=>{try{return x.startsWith('{')||x.startsWith('[')?JSON.parse(x):x}catch{return x}});

  for(const item of rows){
    const role=sourceRole(item);
    const g=item?.semantic_groups?.language_growth||{};
    for(const [bucket,field] of Object.entries(fieldMap)){
      if(!allowed[bucket].has(role))continue;
      const before=buckets[bucket].length;
      push(buckets[bucket],g[field]);
      if(buckets[bucket].length>before){
        provenance[bucket].push({
          source_ref:item.source_ref||null,
          source_role:role,
          source_family:item.source_family||null,
          authority_class:item.authority_class||null
        });
      }
    }
  }

  for(const key of Object.keys(buckets))buckets[key]=uniq(buckets[key]);

  return {
    curriculum_verified:official.length>0,
    curriculum_source_refs:[...new Set(official.map(x=>x.source_ref).filter(Boolean))],
    ...buckets,
    resource_provenance:provenance,
    source_role_guard:{
      curriculum_alignment_does_not_certify_lexical_semantics:true,
      lexical_semantics_does_not_certify_grade_alignment:true,
      language_usage_does_not_certify_curriculum_alignment:true,
      source_role_consumed_from_learning_index_contract:true,
      filename_or_title_role_inference_forbidden:true
    }
  };
}

function stanceFor(profile={}){
  const dims=profile.dimensions||{};
  const rows=['VOCABULARY','GRAMMAR','EXPRESSION','THINKING'].map(k=>dims[k]||{});
  const needs=rows.filter(x=>x.state==='NEEDS_SUPPORT'&&x.confidence!=='LOW').length;
  const stretchStable=rows.filter(x=>
    x.state==='READY_TO_STRETCH' &&
    x.stable_state==='READY_TO_STRETCH' &&
    x.confidence!=='LOW'
  ).length;
  const cross=profile.cross_dimension||{};
  const evidenceReady=(cross.verified_growth_signal_count||0)>0||(cross.cross_app_dimension_count||0)>0;
  if(needs>=2)return 'SCAFFOLD_LEAD';
  if(stretchStable>=2&&evidenceReady)return 'TRANSFER_PUSH';
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
  const dims=profile.dimensions||{};
  const temporarySupport=Object.values(dims).some(x=>
    x?.stability_signal==='TEMPORARY_SUPPORT_WITHOUT_LONG_TERM_DEMOTION');
  const promotionHeld=Object.values(dims).some(x=>
    x?.stability_signal==='PROMOTION_CANDIDATE_NOT_STABLE');
  let intensity=stance==='SCAFFOLD_LEAD'?'SUPPORT_BUILD':
    stance==='TRANSFER_PUSH'?'STRETCH_TRANSFER':'BUILD_CONNECT';
  if(confidence==='LOW'&&intensity==='STRETCH_TRANSFER')intensity='BUILD_CONNECT';

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
    longitudinal_stability:{
      temporary_support_without_long_term_demotion:temporarySupport,
      promotion_held_until_stable:promotionHeld,
      recent_window_drives_support:true,
      stability_window_required_for_transfer_push:true
    },
    stability_guard:{
      low_confidence_cannot_upshift_to_transfer:true,
      one_event_cannot_raise_expression_level_by_itself:true,
      verified_or_cross_app_evidence_required_for_stretch:true,
      stability_window_required_for_transfer_push:true
    }
  };
}

function referenceRequirements(control={},resources={}){
  const dims=new Set(Array.isArray(control.target_dimensions)?control.target_dimensions:[]);
  const out=[];
  const add=(gap_type,priority,role,provenance,reason)=>out.push({
    gap_type,
    owner:'LEARNING_ENGINE_CORE',
    priority,
    function_id:'LE-GROWTH-01',
    consumer_app:'LEARNING_ENGINE',
    requested_behavior:'CURRICULUM_GROUNDED_LANGUAGE_GROWTH',
    requested_capability:role,
    required_learning_evidence_role:role,
    required_provenance_any_of:[...provenance],
    index_check_required:true,
    resolution_path:'INDEX_THEN_MINING_IF_INSUFFICIENT',
    mining_request_authorized:false,
    reason
  });

  if(!resources.curriculum_verified){
    add(
      'CURRICULUM_ALIGNMENT_REFERENCE_REQUIRED','HIGH','CURRICULUM_ALIGNMENT',
      ['OFFICIAL_EDUCATION_SOURCE'],
      'OFFICIAL_CURRICULUM_ALIGNMENT_MISSING'
    );
  }
  if((dims.has('VOCABULARY')||dims.has('ENGLISH_THINKING')) &&
     resources.easy_english_definitions.length===0){
    add(
      'LEXICAL_SEMANTICS_REFERENCE_REQUIRED','MEDIUM','LEXICAL_SEMANTICS',
      ['LEXICAL_REFERENCE_SOURCE'],
      'EASY_ENGLISH_LEXICAL_SEMANTICS_MISSING'
    );
  }
  if((dims.has('GRAMMAR')||dims.has('EXPRESSION')) &&
     resources.expression_chunks.length===0 &&
     resources.grammar_patterns.length===0 &&
     resources.natural_collocations.length===0){
    add(
      'LANGUAGE_USAGE_REFERENCE_REQUIRED','MEDIUM','LANGUAGE_USAGE',
      ['LANGUAGE_USAGE_SOURCE','PEDAGOGICAL_SOURCE_REF'],
      'EXPRESSION_CHUNK_OR_USAGE_SUPPORT_MISSING'
    );
  }
  if(dims.has('ENGLISH_THINKING') && resources.english_thinking_support.length===0){
    add(
      'PEDAGOGICAL_LANGUAGE_SUPPORT_REFERENCE_REQUIRED','LOW','PEDAGOGICAL_USAGE',
      ['PEDAGOGICAL_SOURCE_REF'],
      'ENGLISH_THINKING_PEDAGOGICAL_SUPPORT_MISSING'
    );
  }
  return out;
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
  const referenceGaps=referenceRequirements(control,resources);

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
    language_resource_provenance:resources.resource_provenance,
    source_role_guard:resources.source_role_guard,
    hide_to_snap_handoff:snapHandoff(growth_profile,resources,stance,depth,control),
    reference_gap_candidates:referenceGaps,
    reference_gap_candidate:referenceGaps[0]||null,
    guards:{
      engine_guides_growth_not_answers:true,
      korean_to_english_word_by_word_translation_is_not_default:true,
      easy_english_definition_preferred_when_grounded:true,
      expression_chunks_preferred_over_isolated_translation:true,
      age_changes_language_load_not_thinking_ceiling:true,
      hide_prepares_language_material_snap_owns_expression_execution:true,
      planner_owns_dates:true,
      growth_intensity_and_expression_level_are_engine_intent_only:true,
      low_confidence_cannot_force_growth_upshift:true,
      curriculum_and_language_resource_authorities_are_separate:true,
      missing_resource_role_emits_index_first_gap:true,
      learning_engine_never_authorizes_mining:true
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
  for(const gap of (Array.isArray(policy.reference_gap_candidates)?policy.reference_gap_candidates:[])){
    if(gap.mining_request_authorized!==false)issues.push('GROWTH_GAP_MINING_AUTHORIZATION_FORBIDDEN');
    if(gap.resolution_path!=='INDEX_THEN_MINING_IF_INSUFFICIENT')issues.push('GROWTH_GAP_PATH_INVALID');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,AUTHORITY,growthResources,derive,validate});
