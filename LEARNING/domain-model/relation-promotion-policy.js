'use strict';

const VERSION='TAKY_RELATION_PROMOTION_POLICY_V1';
const clean=v=>String(v??'').trim();

const DEFAULTS=Object.freeze({
  min_personal_observation_pairs:20,
  min_distinct_days:5,
  min_effect_consistency:0.70
});

function evaluate(candidate={},evidence_summary={},options={}){
  const cfg={...DEFAULTS,...options};
  const blockers=[];
  const warnings=[];

  if(clean(candidate.authority)!=='DATA_CANDIDATE')blockers.push('DATA_CANDIDATE_REQUIRED');
  if(clean(candidate.state)!=='CANDIDATE')blockers.push('CANDIDATE_STATE_REQUIRED');
  if(candidate.can_influence_learning_sequence!==false)blockers.push('CANDIDATE_MUST_BE_NON_ACTIVE');

  const pairs=Number(evidence_summary.observation_pairs||0);
  const days=Number(evidence_summary.distinct_days||0);
  const consistency=Number(evidence_summary.effect_consistency);

  if(pairs<cfg.min_personal_observation_pairs)blockers.push('MIN_OBSERVATION_PAIRS_NOT_MET');
  if(days<cfg.min_distinct_days)blockers.push('MIN_DISTINCT_DAYS_NOT_MET');
  if(!Number.isFinite(consistency)||consistency<cfg.min_effect_consistency)blockers.push('EFFECT_CONSISTENCY_NOT_MET');

  const personalReviewAvailable=blockers.length===0;

  return {
    ok:true,
    policy_version:VERSION,
    candidate_relation_id:clean(candidate.relation_id),
    personal_advisory_review_available:personalReviewAvailable,
    personal_advisory_state:personalReviewAvailable?'HUMAN_REVIEW_AVAILABLE':'HOLD',
    domain_relation_promotion_available:false,
    domain_relation_blockers:[
      'LEARNER_DATA_ALONE_CANNOT_DEFINE_DOMAIN_PREREQUISITE',
      'EXTERNAL_OR_DECLARED_DOMAIN_EVIDENCE_REQUIRED',
      'HUMAN_DOMAIN_REVIEW_REQUIRED'
    ],
    blockers,
    warnings,
    auto_promotion:false,
    allowed_if_personally_reviewed:'PERSONAL_SEQUENCE_ADVISORY_ONLY',
    forbidden_outputs:[
      'DECLARED_DOMAIN_RELATION',
      'GLOBAL_PREREQUISITE_TRUTH',
      'SCHEDULE_DATE',
      'PLANNER_DATE'
    ]
  };
}

function validate(result={}){
  const issues=[];
  if(!result?.ok)issues.push('RESULT_NOT_OK');
  if(result.auto_promotion!==false)issues.push('AUTO_PROMOTION_FORBIDDEN');
  if(result.domain_relation_promotion_available!==false)issues.push('DOMAIN_AUTO_PROMOTION_FORBIDDEN');
  if(result.allowed_if_personally_reviewed!=='PERSONAL_SEQUENCE_ADVISORY_ONLY')issues.push('PERSONAL_SCOPE_BOUNDARY_INVALID');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,DEFAULTS,evaluate,validate});
