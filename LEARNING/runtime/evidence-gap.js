'use strict';

const VERSION='TAKY_LEARNING_EVIDENCE_GAP_V1';
const clean=v=>String(v??'').trim();

function derive({scope={},decision={},indexed_evidence=null}={}){
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

  const sourceRefs=Array.isArray(indexed_evidence?.source_refs)?indexed_evidence.source_refs:[];
  return {
    ok:true,
    version:VERSION,
    gap:{
      gap_id:[
        clean(scope.member_id)||'member',
        clean(scope.subject)||'subject',
        clean(scope.concept_skill_target)||'target',
        gapType
      ].join(':'),
      owner:'LEARNING_ENGINE_CORE',
      gap_type:gapType,
      priority,
      scope:{
        member_id:clean(scope.member_id)||null,
        subject:clean(scope.subject)||null,
        concept_skill_target:clean(scope.concept_skill_target)||null
      },
      evidence_sufficiency:suff,
      existing_source_refs:[...sourceRefs],
      index_check_required:true,
      mining_request_authorized:false,
      requested_capability:'LEARNING_EVIDENCE_SUPPORT',
      query_terms:[
        clean(scope.subject),
        clean(scope.concept_skill_target),
        gapType
      ].filter(Boolean),
      invariant:'LEARNING_EMITS_GAP__INDEX_CHECKS_EXISTENCE__MINING_ONLY_IF_INSUFFICIENT'
    }
  };
}

module.exports=Object.freeze({VERSION,derive});
