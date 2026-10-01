'use strict';

const IndexedEvidence=require('../intake/indexed-evidence-handoff.js');

const VERSION='TAKY_LEARNING_INDEX_V2';
const AUTHORITY='DERIVED_NON_SOURCE_OF_TRUTH';

const GROUP_FIELDS=Object.freeze({
  curriculum:['curriculum_version','grade_band','grade','semester_optional','subject','unit_optional','achievement_standard_refs'],
  lexical:['term','term_type','surface_variants','morphemes','hanja','english_root','greek_latin_root','word_family_optional'],
  semantics:['everyday_meaning','subject_specific_meaning','semantic_transparency','morpheme_decomposition_validity','etymology_confidence'],
  concept:['concept_node','candidate_prerequisites','related_terms','contrast_terms','confusion_terms','misconception_candidates','context_examples','representation_bridge'],
  cross_domain:['cross_subject_links','transfer_targets','publisher_overlay_optional'],
  language_growth:['easy_english_definition','expression_chunks','natural_collocations','grammar_patterns','usage_example_sentences','thinking_moves','question_stems','production_targets','english_thinking_support'],
  exposure:['curriculum_grade','actual_exposure_difficulty']
});

const PROHIBITED_KEYS=new Set([
  'learner_state','mastery','mastery_boolean','mastery_estimate','memory_strength',
  'next_review_priority','review_date','schedule_date','planner_date','calendar_slot',
  'due_at','deadline','automatic_pass_fail','automatic_remediation'
]);

function clean(v){return String(v??'').trim();}

const LEARNING_EVIDENCE_ROLES=Object.freeze([
  'CURRICULUM_ALIGNMENT',
  'LEXICAL_SEMANTICS',
  'LANGUAGE_USAGE',
  'PEDAGOGICAL_USAGE',
  'GENERAL_REFERENCE'
]);

function evidenceRoleFromProvenance(provenance=[]){
  const tags=new Set((Array.isArray(provenance)?provenance:[]).map(clean).filter(Boolean));
  const matched=[];
  if(tags.has('OFFICIAL_EDUCATION_SOURCE')||tags.has('OFFICIAL_STANDARD_REF'))
    matched.push('CURRICULUM_ALIGNMENT');
  if(tags.has('LEXICAL_REFERENCE_SOURCE')||tags.has('TERM_SOURCE_REF')||tags.has('NIKL_SOURCE_REF'))
    matched.push('LEXICAL_SEMANTICS');
  if(tags.has('LANGUAGE_USAGE_SOURCE')||tags.has('WRITING_CORPUS_SOURCE_REF'))
    matched.push('LANGUAGE_USAGE');
  if(tags.has('PEDAGOGICAL_SOURCE_REF')||tags.has('GOVERNED_DERIVED_ACTIVITY_REF'))
    matched.push('PEDAGOGICAL_USAGE');
  if(matched.length===1)return {role:matched[0],ambiguous:false,tags:[...tags]};
  if(matched.length>1)return {role:null,ambiguous:true,candidates:matched,tags:[...tags]};
  return {role:'GENERAL_REFERENCE',ambiguous:false,tags:[...tags]};
}

function hasProhibitedKey(value){
  if(!value||typeof value!=='object')return false;
  for(const [key,nested] of Object.entries(value)){
    if(PROHIBITED_KEYS.has(key))return true;
    if(hasProhibitedKey(nested))return true;
  }
  return false;
}

function pickGroup(mapping,fields){
  const out={};
  for(const field of fields){
    if(mapping[field]!==undefined)out[field]=mapping[field];
  }
  return out;
}

function mappingFor(mapping,sourceId){
  if(!mapping||typeof mapping!=='object')return {};
  const bySource=mapping.by_source_id;
  if(bySource&&typeof bySource==='object'&&bySource[sourceId]&&typeof bySource[sourceId]==='object'){
    return bySource[sourceId];
  }
  return mapping.default&&typeof mapping.default==='object'?mapping.default:{};
}

function prepare(input={}, independentIndexOwnerVerifier=null){
  const indexedInput=input.indexed_evidence_handoff||input.indexed_evidence||input;
  const indexed=IndexedEvidence.prepare(indexedInput,independentIndexOwnerVerifier);
  if(!indexed.ok){
    return {ok:false,version:VERSION,reason:'MINING_INDEX_HANDOFF_INVALID',indexed_evidence:indexed};
  }

  const learningMapping=input.learning_mapping||{};
  if(hasProhibitedKey(learningMapping)){
    return {ok:false,version:VERSION,reason:'LEARNING_INDEX_PROHIBITED_LEARNER_OR_SCHEDULE_FIELD'};
  }

  const functionId=clean(indexed.query_context?.function_id);
  const semanticItems=indexed.candidates.map(row=>{
    const mapping=mappingFor(learningMapping,row.source_id);
    const groups={};
    for(const [group,fields] of Object.entries(GROUP_FIELDS)){
      const value=pickGroup(mapping,fields);
      if(Object.keys(value).length)groups[group]=value;
    }
    const evidenceRole=evidenceRoleFromProvenance(row.provenance||[]);
    return {
      learning_index_id:['LI',functionId||'FUNCTION',clean(row.source_id)||'SOURCE'].join(':'),
      source_id:row.source_id,
      source_ref:row.source_ref,
      source_family:row.source_family,
      authority_class:row.authority_class,
      learning_evidence_role:evidenceRole.role,
      learning_evidence_role_ambiguous:evidenceRole.ambiguous,
      learning_evidence_role_candidates:evidenceRole.candidates||[],
      learning_evidence_kind:row.learning_evidence_kind||null,
      provenance:[...(row.provenance||[])],
      detail_anchor:row.detail_anchor||null,
      semantic_groups:groups
    };
  });

  return {
    ok:true,
    version:VERSION,
    authority:AUTHORITY,
    query_context:indexed.query_context,
    source_refs:[...indexed.source_refs],
    semantic_items:semanticItems,
    policy_requests:[...indexed.policy_requests],
    indexed_evidence:indexed,
    guards:{
      mining_index_remains_source_authority:true,
      learning_index_is_rebuildable:true,
      learning_index_has_no_learner_state:true,
      learning_index_has_no_schedule_authority:true,
      term_match_is_not_learner_understanding:true,
      learning_evidence_role_derived_from_indexed_provenance:true,
      source_role_is_not_inferred_from_filename_or_title:true,
      learning_evidence_kind_is_index_owner_verified_metadata:true
    }
  };
}

function validate(view={}){
  const issues=[];
  if(view?.ok!==true)issues.push('LEARNING_INDEX_NOT_OK');
  if(view.authority!==AUTHORITY)issues.push('LEARNING_INDEX_AUTHORITY_INVALID');
  if(hasProhibitedKey(view.semantic_items||[]))issues.push('LEARNING_INDEX_PROHIBITED_FIELD');
  if(view.guards?.mining_index_remains_source_authority!==true)issues.push('MINING_INDEX_AUTHORITY_GUARD_MISSING');
  for(const item of (Array.isArray(view.semantic_items)?view.semantic_items:[])){
    if(item.learning_evidence_role_ambiguous===true)issues.push('LEARNING_EVIDENCE_ROLE_AMBIGUOUS');
    if(!LEARNING_EVIDENCE_ROLES.includes(item.learning_evidence_role))
      issues.push('LEARNING_EVIDENCE_ROLE_INVALID');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,AUTHORITY,LEARNING_EVIDENCE_ROLES,evidenceRoleFromProvenance,prepare,validate});
