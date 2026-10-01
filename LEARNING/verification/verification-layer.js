'use strict';

const VerifierPolicy=require('./verifier-policy.js');
const VERSION='TAKY_LEARNING_VERIFICATION_V1';
const clean=v=>String(v??'').trim();
const GROWTH_DIMENSIONS=new Set(['VOCABULARY','GRAMMAR','EXPRESSION','THINKING','ENGLISH_THINKING']);
const GROWTH_OUTCOMES=new Set(['SUCCESS','PARTIAL','FAIL']);

function normalizeGrowthDimensions(rows=[]){
  if(!Array.isArray(rows))return [];
  return rows.slice(0,10).map(raw=>{
    const x=raw&&typeof raw==='object'?raw:{};
    const dimension=clean(x.dimension).toUpperCase();
    const outcome=clean(x.outcome).toUpperCase();
    const depth=Number.isFinite(Number(x.depth))?Math.max(0,Math.min(5,Number(x.depth))):null;
    if(!GROWTH_DIMENSIONS.has(dimension)||!GROWTH_OUTCOMES.has(outcome))return null;
    return {
      dimension,outcome,
      assisted:x.assisted===true,
      transfer:x.transfer===true,
      direct_english:x.direct_english===true?true:x.direct_english===false?false:null,
      depth,
      target_id:clean(x.target_id)||null,
      note:clean(x.note)||null
    };
  }).filter(Boolean);
}

const ALLOWED_VERIFIERS=Object.freeze({
  ANSWER_KEY_EXACT:{
    requires_reference:true,
    allowed_evidence:['MEMORY_RETRIEVAL_EVIDENCE','STRUCTURED_PRACTICE_EVIDENCE']
  },
  RETRIEVAL_EXACT_MATCH:{
    requires_reference:true,
    allowed_evidence:['MEMORY_RETRIEVAL_EVIDENCE']
  },
  HUMAN_RUBRIC_BINARY:{
    requires_reference:true,
    allowed_evidence:['LEARNER_PRODUCTION_EVIDENCE','STRUCTURED_PRACTICE_EVIDENCE']
  },
  HUMAN_GROWTH_RUBRIC:{
    requires_reference:true,
    allowed_evidence:['LEARNER_PRODUCTION_EVIDENCE']
  }
});

function validateReceipt(r={}){
  const issues=[];
  if(clean(r.authority)!=='LEARNING_VERIFICATION_RECEIPT')issues.push('AUTHORITY_INVALID');
  for(const k of ['receipt_id','target_event_id','verified_at','verifier_type','verifier_version','member_id','subject','concept_skill_target']){
    if(!clean(r[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(!Number.isFinite(Date.parse(r.verified_at||'')))issues.push('VERIFIED_AT_INVALID');
  const growthVerifier=clean(r.verifier_type)==='HUMAN_GROWTH_RUBRIC';
  if(growthVerifier){
    if(r.outcome!==null)issues.push('GROWTH_RUBRIC_GLOBAL_OUTCOME_FORBIDDEN');
    if(!Array.isArray(r.growth_dimensions)||!r.growth_dimensions.length)
      issues.push('GROWTH_DIMENSIONS_REQUIRED');
    else if(normalizeGrowthDimensions(r.growth_dimensions).length!==r.growth_dimensions.length)
      issues.push('GROWTH_DIMENSIONS_INVALID');
  }else if(r.outcome!==0&&r.outcome!==1)issues.push('OUTCOME_INVALID');
  const spec=ALLOWED_VERIFIERS[clean(r.verifier_type)];
  if(!spec)issues.push('VERIFIER_NOT_ALLOWED');
  if(spec?.requires_reference&&!clean(r.reference_id))issues.push('REFERENCE_REQUIRED');
  if(['HUMAN_RUBRIC_BINARY','HUMAN_GROWTH_RUBRIC'].includes(clean(r.verifier_type))&&
     !['PARENT','TEACHER','QUALIFIED_REVIEWER'].includes(clean(r.reviewer_role)))
    issues.push('REVIEWER_ROLE_INVALID');
  return {ok:issues.length===0,issues};
}

function issueReceipt(input={}){
  const receipt={
    authority:'LEARNING_VERIFICATION_RECEIPT',
    receipt_version:VERSION,
    receipt_id:clean(input.receipt_id),
    target_event_id:clean(input.target_event_id),
    verified_at:clean(input.verified_at),
    verifier_type:clean(input.verifier_type),
    verifier_version:clean(input.verifier_version),
    outcome:input.outcome,
    member_id:clean(input.member_id),
    subject:clean(input.subject).toLowerCase(),
    concept_skill_target:clean(input.concept_skill_target).toLowerCase(),
    reference_id:clean(input.reference_id)||null,
    reviewer_role:clean(input.reviewer_role)||null,
    growth_dimensions:clean(input.verifier_type)==='HUMAN_GROWTH_RUBRIC'
      ?normalizeGrowthDimensions(input.growth_dimensions):[],
    notes:clean(input.notes)||null
  };
  const checked=validateReceipt(receipt);
  return checked.ok?{ok:true,receipt}:{ok:false,reason:'INVALID_VERIFICATION_RECEIPT',issues:checked.issues,receipt};
}

function applyReceipt(evidence={},receipt={}){
  const checked=validateReceipt(receipt);
  if(!checked.ok)return {ok:false,reason:'INVALID_VERIFICATION_RECEIPT',issues:checked.issues};
  const issues=[];
  if(clean(evidence.event_id)!==clean(receipt.target_event_id))issues.push('EVENT_MISMATCH');
  if(clean(evidence.member_id)!==clean(receipt.member_id))issues.push('MEMBER_MISMATCH');
  if(clean(evidence.subject).toLowerCase()!==clean(receipt.subject).toLowerCase())issues.push('SUBJECT_MISMATCH');
  if(clean(evidence.concept_skill_target).toLowerCase()!==clean(receipt.concept_skill_target).toLowerCase())issues.push('SKILL_MISMATCH');
  if(clean(evidence.evidence_type)==='CHILD_SELF_REPORT')issues.push('SELF_REPORT_NOT_VERIFIABLE_TARGET');
  const spec=ALLOWED_VERIFIERS[clean(receipt.verifier_type)];
  if(spec&&!spec.allowed_evidence.includes(clean(evidence.evidence_type)))issues.push('VERIFIER_EVIDENCE_TYPE_MISMATCH');
  const policy=VerifierPolicy.canVerify({
    source_app:clean(evidence.source_app),
    evidence_type:clean(evidence.evidence_type),
    verifier_type:clean(receipt.verifier_type),
    auto:!['HUMAN_RUBRIC_BINARY','HUMAN_GROWTH_RUBRIC'].includes(clean(receipt.verifier_type))
  });
  if(!policy.ok)issues.push(policy.reason);
  if(issues.length)return {ok:false,reason:'VERIFICATION_SCOPE_MISMATCH',issues};
  const verification={
    authority:receipt.authority,
    receipt_id:receipt.receipt_id,
    receipt_version:receipt.receipt_version,
    verifier_type:receipt.verifier_type,
    verifier_version:receipt.verifier_version,
    verified_at:receipt.verified_at,
    reference_id:receipt.reference_id,
    reviewer_role:receipt.reviewer_role
  };
  if(clean(receipt.verifier_type)==='HUMAN_GROWTH_RUBRIC'){
    const growthSignals=normalizeGrowthDimensions(receipt.growth_dimensions).map(x=>({
      dimension:x.dimension,
      outcome:x.outcome,
      assisted:x.assisted,
      transfer:x.transfer,
      direct_english:x.direct_english,
      kind:'HUMAN_GROWTH_RUBRIC',
      target_id:x.target_id||clean(evidence.learning_target_id)||null,
      depth:x.depth,
      evidence_ref:'verification:'+receipt.receipt_id
    }));
    return {
      ok:true,
      evidence:{
        ...evidence,
        verified_outcome:null,
        verification,
        language_growth_signals:[
          ...(Array.isArray(evidence.language_growth_signals)?evidence.language_growth_signals:[])
            .filter(x=>clean(x?.outcome).toUpperCase()==='UNKNOWN'),
          ...growthSignals
        ]
      }
    };
  }
  return {
    ok:true,
    evidence:{
      ...evidence,
      verified_outcome:receipt.outcome,
      verification
    }
  };
}

function issueFromCandidate(evidence={},candidate={}){
  const verifierType=clean(candidate.verifier_type);
  if(!['RETRIEVAL_EXACT_MATCH','ANSWER_KEY_EXACT'].includes(verifierType))return {ok:false,reason:'CANDIDATE_VERIFIER_NOT_ALLOWED'};
  if(clean(candidate.basis)!=='DETERMINISTIC_LOCAL_MATCH')return {ok:false,reason:'CANDIDATE_BASIS_INVALID'};
  if(candidate.outcome!==0&&candidate.outcome!==1)return {ok:false,reason:'CANDIDATE_OUTCOME_INVALID'};
  const policy=VerifierPolicy.canVerify({
    source_app:clean(evidence.source_app),
    evidence_type:clean(evidence.evidence_type),
    verifier_type:verifierType,
    auto:true
  });
  if(!policy.ok)return {ok:false,reason:policy.reason};
  const issued=issueReceipt({
    receipt_id:'vr:'+clean(evidence.event_id)+':'+clean(candidate.verifier_version||'v1'),
    target_event_id:clean(evidence.event_id),
    verified_at:clean(evidence.observed_at),
    verifier_type:verifierType,
    verifier_version:clean(candidate.verifier_version),
    outcome:candidate.outcome,
    member_id:clean(evidence.member_id),
    subject:clean(evidence.subject),
    concept_skill_target:clean(evidence.concept_skill_target),
    reference_id:clean(candidate.reference_id)
  });
  if(!issued.ok)return issued;
  return applyReceipt(evidence,issued.receipt);
}

module.exports=Object.freeze({VERSION,ALLOWED_VERIFIERS,validateReceipt,issueReceipt,applyReceipt,issueFromCandidate});
