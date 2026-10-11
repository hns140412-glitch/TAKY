'use strict';

const Policy=require('./verifier-policy.js');

const VERSION='TAKY_SERVER_SPECIALIST_EVIDENCE_VERIFIER_V1';
const clean=v=>String(v??'').trim();
const object=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
const ALLOWED_REVIEWERS=new Set(['PARENT','TEACHER','QUALIFIED_REVIEWER']);
const MATCH_RULES=new Set(['EXACT_STRING','TRIM','CASEFOLD_TRIM','NUMERIC_EQUAL']);

function clone(v){return JSON.parse(JSON.stringify(v));}
function scalar(v){
  if(typeof v==='string'||typeof v==='number'||typeof v==='boolean')return v;
  return null;
}
function targetId(packet={}){
  const p=packet?.event?.payload||{},c=packet.context||{};
  return clean(c.learning_target_id||p.learning_target_id||p.lexical_id||p.word_id||p.item_id);
}
function scope(packet={}){
  const c=packet.context||{},p=packet?.event?.payload||{};
  return {
    family_id:clean(c.family_id),
    member_id:clean(c.member_id),
    subject:clean(c.subject||p.subject).toLowerCase(),
    concept_skill_target:clean(c.concept_skill_target||p.concept_skill_target).toLowerCase(),
    learning_target_id:targetId(packet),
    event_id:clean(packet?.event?.event_id),
    source_app:clean(packet.source_app)
  };
}
function identityMatches(s,identity={}){
  return clean(identity.family_id)===s.family_id&&
    Array.isArray(identity.authorized_member_ids)&&identity.authorized_member_ids.includes(s.member_id);
}
function referenceMatches(ref={},s={},verifierType=''){
  if(!object(ref)||clean(ref.authority)!=='SERVER_OWNED_LEARNING_REFERENCE')return false;
  if(!clean(ref.reference_id)||!clean(ref.verifier_version))return false;
  if(clean(ref.source_app)!==s.source_app)return false;
  if(clean(ref.subject).toLowerCase()!==s.subject)return false;
  if(clean(ref.concept_skill_target).toLowerCase()!==s.concept_skill_target)return false;
  if(clean(ref.learning_target_id)!==s.learning_target_id)return false;
  if(clean(ref.verifier_type)!==verifierType)return false;
  if(!MATCH_RULES.has(clean(ref.match_rule)))return false;
  const values=Array.isArray(ref.expected_values)?ref.expected_values:[ref.expected_value];
  return values.length>0&&values.every(v=>scalar(v)!==null);
}
function normalize(v,rule){
  if(rule==='NUMERIC_EQUAL'){
    if(typeof v==='boolean'||v===null||v===undefined)return null;
    if(typeof v==='number')return Number.isFinite(v)?v:null;
    if(typeof v!=='string'||!v.trim()||!/^[-+]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(v.trim()))return null;
    const n=Number(v.trim());
    return Number.isFinite(n)?n:null;
  }
  const s=String(v??'');
  if(rule==='EXACT_STRING')return s;
  if(rule==='TRIM')return s.trim();
  if(rule==='CASEFOLD_TRIM')return s.trim().toLocaleLowerCase('en-US');
  return null;
}
function exactOutcome(response,ref){
  const rule=clean(ref.match_rule);
  const actual=normalize(response,rule);
  if(actual===null)return null;
  const values=Array.isArray(ref.expected_values)?ref.expected_values:[ref.expected_value];
  const expected=values.map(v=>normalize(v,rule));
  if(expected.some(v=>v===null))return null;
  return expected.some(v=>Object.is(v,actual))?1:0;
}
function autoEvidenceType(source,payload={}){
  if(source==='hide-seek')return 'MEMORY_RETRIEVAL_EVIDENCE';
  if(source==='ready-set')return clean(payload.evidence_type);
  return '';
}
function trustedReviewMatches(review={},s={}){
  if(!object(review)||clean(review.authority)!=='SERVER_OWNED_HUMAN_RUBRIC_REVIEW')return false;
  if(!clean(review.receipt_id)||!clean(review.reference_id)||!clean(review.verifier_version))return false;
  if(clean(review.target_event_id)!==s.event_id)return false;
  if(clean(review.family_id)!==s.family_id||clean(review.member_id)!==s.member_id)return false;
  if(clean(review.subject).toLowerCase()!==s.subject)return false;
  if(clean(review.concept_skill_target).toLowerCase()!==s.concept_skill_target)return false;
  if(review.outcome!==0&&review.outcome!==1)return false;
  if(!Number.isFinite(Date.parse(review.verified_at||'')))return false;
  if(!ALLOWED_REVIEWERS.has(clean(review.reviewer_role)))return false;
  return true;
}

function create({resolveReference,resolveHumanReview}={}){
  if(typeof resolveReference!=='function')throw Error('SERVER_REFERENCE_RESOLVER_REQUIRED');
  if(typeof resolveHumanReview!=='function')throw Error('SERVER_HUMAN_REVIEW_RESOLVER_REQUIRED');

  return async function verifySpecialistEvidence({packet,identity}={}){
    if(!object(packet)||!object(identity))return {ok:false,reason:'VERIFICATION_INPUT_INVALID'};
    const s=scope(packet),payload=packet?.event?.payload||{};
    if(!s.family_id||!s.member_id||!s.subject||!s.concept_skill_target||!s.event_id||!s.source_app)
      return {ok:false,reason:'VERIFICATION_SCOPE_INCOMPLETE'};
    if(!identityMatches(s,identity))return {ok:false,reason:'VERIFIED_IDENTITY_SCOPE_MISMATCH'};

    if(s.source_app==='hide-seek'||s.source_app==='ready-set'){
      const verifierType=s.source_app==='hide-seek'?'RETRIEVAL_EXACT_MATCH':'ANSWER_KEY_EXACT';
      const evidenceType=autoEvidenceType(s.source_app,payload);
      if(s.source_app==='ready-set'&&evidenceType==='CHILD_SELF_REPORT')
        return {ok:false,reason:'SELF_REPORT_NOT_VERIFIABLE'};
      const policy=Policy.canVerify({
        source_app:s.source_app,evidence_type:evidenceType,verifier_type:verifierType,auto:true
      });
      if(!policy.ok)return {ok:false,reason:policy.reason};
      if(!s.learning_target_id)return {ok:false,reason:'LEARNING_TARGET_REQUIRED'};
      const observation=object(payload.verification_observation)?payload.verification_observation:null;
      const response=observation?scalar(observation.response_value):null;
      if(response===null)return {ok:false,reason:'RAW_RESPONSE_REQUIRED'};

      const ref=await resolveReference(Object.freeze({...s,verifier_type:verifierType}));
      if(!referenceMatches(ref,s,verifierType))
        return {ok:false,reason:'SERVER_REFERENCE_NOT_AVAILABLE'};
      const outcome=exactOutcome(response,ref);
      if(outcome===null)return {ok:false,reason:'DETERMINISTIC_MATCH_RULE_INVALID'};

      const verified=clone(packet);
      verified.event.payload={
        ...(verified.event.payload||{}),
        verification_candidate:{
          verifier_type:verifierType,
          verifier_version:clean(ref.verifier_version),
          basis:'DETERMINISTIC_LOCAL_MATCH',
          outcome,
          reference_id:clean(ref.reference_id)
        }
      };
      return {ok:true,packet:verified,authority:'SERVER_OWNED_REFERENCE_VERIFIED'};
    }

    if(s.source_app==='snap-pop'){
      const policy=Policy.canVerify({
        source_app:'snap-pop',evidence_type:'LEARNER_PRODUCTION_EVIDENCE',
        verifier_type:'HUMAN_RUBRIC_BINARY',auto:false
      });
      if(!policy.ok)return {ok:false,reason:policy.reason};
      const review=await resolveHumanReview(Object.freeze({...s}));
      if(!trustedReviewMatches(review,s))
        return {ok:false,reason:'AUTHORIZED_HUMAN_REVIEW_NOT_AVAILABLE'};
      const verified=clone(packet);
      verified.verification_input={
        receipt_id:clean(review.receipt_id),
        target_event_id:s.event_id,
        verified_at:clean(review.verified_at),
        verifier_type:'HUMAN_RUBRIC_BINARY',
        verifier_version:clean(review.verifier_version),
        outcome:review.outcome,
        member_id:s.member_id,
        subject:s.subject,
        concept_skill_target:s.concept_skill_target,
        reference_id:clean(review.reference_id),
        reviewer_role:clean(review.reviewer_role)
      };
      return {ok:true,packet:verified,authority:'SERVER_OWNED_HUMAN_REVIEW_VERIFIED'};
    }

    return {ok:false,reason:'SOURCE_APP_NOT_VERIFIABLE'};
  };
}

module.exports=Object.freeze({VERSION,MATCH_RULES,create,scope,exactOutcome});
