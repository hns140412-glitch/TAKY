'use strict';

const VERSION='TAKY_LEARNING_EVIDENCE_GAP_V3';
const clean=v=>String(v??'').trim();

function makeScope(scope={}){
  return {
    member_id:clean(scope.member_id)||null,
    subject:clean(scope.subject)||null,
    concept_skill_target:clean(scope.concept_skill_target)||null
  };
}

function candidateMatchesRequirement(row={},requirement={}){
  const fam=new Set(Array.isArray(requirement.acceptable_source_families)
    ?requirement.acceptable_source_families.filter(Boolean):[]);
  const auth=new Set(Array.isArray(requirement.acceptable_authority_classes)
    ?requirement.acceptable_authority_classes.filter(Boolean):[]);
  if(fam.size&&!fam.has(row.source_family))return false;
  if(auth.size&&!auth.has(row.authority_class))return false;

  const provenance=new Set(Array.isArray(row.provenance)?row.provenance.filter(Boolean):[]);
  const all=Array.isArray(requirement.required_provenance)
    ?requirement.required_provenance.filter(Boolean):[];
  if(all.some(x=>!provenance.has(x)))return false;

  const any=Array.isArray(requirement.required_provenance_any_of)
    ?requirement.required_provenance_any_of.filter(Boolean):[];
  if(any.length&&!any.some(x=>provenance.has(x)))return false;
  return true;
}

function derive({scope={},decision={},indexed_evidence=null,reference_requirement=null}={}){
  const normalizedScope=makeScope(scope);
  const sourceRefs=Array.isArray(indexed_evidence?.source_refs)?indexed_evidence.source_refs:[];

  if(reference_requirement&&typeof reference_requirement==='object'){
    const functionId=clean(reference_requirement.function_id);
    const requestedBehavior=clean(reference_requirement.requested_behavior);
    const gapType=clean(reference_requirement.gap_type)||'REFERENCE_EVIDENCE_REQUIRED';
    const queryTerms=Array.isArray(reference_requirement.query_terms)
      ? reference_requirement.query_terms.map(clean).filter(Boolean)
      : [
          clean(scope.subject),clean(scope.concept_skill_target),
          clean(reference_requirement.required_learning_evidence_role),
          functionId,requestedBehavior
        ].filter(Boolean);
    if(!functionId||!requestedBehavior){
      return {ok:false,version:VERSION,reason:'REFERENCE_REQUIREMENT_INCOMPLETE'};
    }
    const candidates=Array.isArray(indexed_evidence?.candidates)?indexed_evidence.candidates:[];
    const matching=candidates.filter(row=>candidateMatchesRequirement(row,reference_requirement));
    if(!matching.length){
      return {
        ok:true,
        version:VERSION,
        gap:{
          gap_id:[
            clean(scope.member_id)||'member',
            clean(scope.subject)||'subject',
            clean(scope.concept_skill_target)||'target',
            gapType,
            functionId
          ].join(':'),
          owner:'LEARNING_ENGINE_CORE',
          gap_type:gapType,
          priority:clean(reference_requirement.priority)||'MEDIUM',
          scope:normalizedScope,
          function_id:functionId,
          consumer_app:clean(reference_requirement.consumer_app)||null,
          requested_behavior:requestedBehavior,
          requested_capability:clean(reference_requirement.requested_capability)||'EXTERNAL_REFERENCE_EVIDENCE',
          required_learning_evidence_role:clean(reference_requirement.required_learning_evidence_role)||null,
          acceptable_source_families:Array.isArray(reference_requirement.acceptable_source_families)?reference_requirement.acceptable_source_families.filter(Boolean):[],
          acceptable_authority_classes:Array.isArray(reference_requirement.acceptable_authority_classes)?reference_requirement.acceptable_authority_classes.filter(Boolean):[],
          required_provenance:Array.isArray(reference_requirement.required_provenance)?reference_requirement.required_provenance.filter(Boolean):[],
          required_provenance_any_of:Array.isArray(reference_requirement.required_provenance_any_of)?reference_requirement.required_provenance_any_of.filter(Boolean):[],
          existing_source_refs:[...sourceRefs],
          matching_source_refs:[],
          index_check_required:true,
          resolution_path:'INDEX_THEN_MINING_IF_INSUFFICIENT',
          mining_request_authorized:false,
          query_terms:queryTerms,
          invariant:'LEARNING_EMITS_ROLE_SPECIFIC_REFERENCE_GAP__INDEX_CHECKS_MATCHING_ROLE__MINING_ONLY_IF_INSUFFICIENT'
        }
      };
    }
    return {
      ok:true,
      version:VERSION,
      gap:null,
      satisfied_reference_requirement:{
        gap_type:gapType,
        matching_source_refs:matching.map(x=>x.source_ref).filter(Boolean),
        required_learning_evidence_role:clean(reference_requirement.required_learning_evidence_role)||null
      }
    };
  }

  const blockers=Array.isArray(decision.blockers)?decision.blockers:[];
  const advisories=Array.isArray(decision.advisories)?decision.advisories:[];
  const suff=clean(decision?.state_summary?.evidence_sufficiency)||'NONE';
  const codes=[...blockers,...advisories].map(x=>clean(x?.code)).filter(Boolean);

  let gapType=null;
  let priority='LOW';
  if(codes.includes('NO_EVIDENCE')||suff==='NONE'){
    gapType='LEARNER_EVIDENCE_ABSENT';
    priority='HIGH';
  }else if(codes.includes('SPARSE_EVIDENCE')||suff==='SPARSE'){
    gapType='LEARNER_EVIDENCE_SPARSE';
    priority='MEDIUM';
  }else if(codes.includes('INSTRUMENT_CHANGE_HOLD')){
    gapType='COMPARABLE_EVIDENCE_REQUIRED';
    priority='HIGH';
  }else if(codes.includes('PREREQUISITE_RISK')){
    gapType='PREREQUISITE_EVIDENCE_REQUIRED';
    priority='HIGH';
  }

  if(!gapType)return {ok:true,version:VERSION,gap:null};

  return {
    ok:true,
    version:VERSION,
    gap:{
      gap_id:[clean(scope.member_id)||'member',clean(scope.subject)||'subject',clean(scope.concept_skill_target)||'target',gapType].join(':'),
      owner:'LEARNING_ENGINE_CORE',
      gap_type:gapType,
      priority,
      scope:normalizedScope,
      evidence_sufficiency:suff,
      existing_source_refs:[...sourceRefs],
      index_check_required:false,
      resolution_path:'SPECIALIST_EVIDENCE_ACQUISITION',
      mining_request_authorized:false,
      requested_capability:'LEARNER_PERFORMANCE_EVIDENCE',
      query_terms:[clean(scope.subject),clean(scope.concept_skill_target),gapType].filter(Boolean),
      invariant:'LEARNER_PERFORMANCE_GAP_NEVER_TRIGGERS_EXTERNAL_MINING'
    }
  };
}

module.exports=Object.freeze({VERSION,candidateMatchesRequirement,derive});