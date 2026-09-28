'use strict';
// Isolated source-composition gate, not a deployed credential provider or policy
// promotion. Trusted callback implementations MUST live on the server and read
// independently controlled identity, immutable evidence and Index decision.
const Receipt=require('../canonical-main/LEARNING/receipts/real-evidence-receipt.js');
const Feedback=require('../canonical-main/LEARNING/lifecycle/outcome-growth-feedback.js');
const clean=v=>typeof v==='string'?v.trim():'';
const norm=v=>clean(v).toLowerCase();
const fail=reason=>({ok:false,reason,verified_outcome_authorized:false,
  mining_growth_dispatch_authorized:false,learning_promotion_authorized:false,
  index_write_authorized:false});
function create({resolveIdentity,loadVerifiedEvidence,loadIndexGapRoute}={}){
 if([resolveIdentity,loadVerifiedEvidence,loadIndexGapRoute].some(f=>typeof f!=='function'))
  throw Error('EXPLICIT_INDEPENDENT_SERVER_RESOLVERS_REQUIRED');
 async function derive(request={}){
  if(!['principal_id','family_id','member_id','event_id','gap_id'].every(
      k=>clean(request[k]))||
     ['outcome','verification','real_evidence_receipt','prior_evidence_gap',
      'index_gap_route','identity','verified_outcome','mining_success'].some(
      k=>Object.prototype.hasOwnProperty.call(request,k)))
   return fail('SELECTOR_ONLY_CLIENT_REQUEST_REQUIRED');
  let identity,stored,bound;
  try{
   identity=await resolveIdentity({principal_id:request.principal_id});
  }catch{return fail('INDEPENDENT_IDENTITY_RESOLUTION_FAILED')}
  if(identity?.authenticated!==true||identity.family_id!==request.family_id||
     !Array.isArray(identity.authorized_member_ids)||
     !identity.authorized_member_ids.includes(request.member_id))
   return fail('TRUSTED_FAMILY_MEMBER_SCOPE_REQUIRED');
  try{
   stored=await loadVerifiedEvidence({identity,member_id:request.member_id,event_id:request.event_id});
  }catch{return fail('SERVER_OWNED_EVIDENCE_LOOKUP_FAILED')}
  const event=stored?.canonical_evidence,receipt=stored?.batch_receipt;
  if(!event||!receipt||!Array.isArray(stored?.batch_evidence)||
     stored.batch_evidence.length!==1||
     stored.batch_evidence[0]?.event_id!==request.event_id||
     Receipt.validateBatchReceipt(receipt,stored.batch_evidence).ok!==true||
     event.event_id!==request.event_id||event.member_id!==request.member_id||
     event.event_id!==stored.batch_evidence[0].event_id||
     event.verification?.receipt_id!==stored.batch_evidence[0]?.verification?.receipt_id||
     receipt.scope?.member_id!==request.member_id||
     !receipt.verification_receipt_ids?.includes(event.verification?.receipt_id)||
     ![0,1].includes(event.verified_outcome)||
     event.verified_outcome!==stored.batch_evidence[0].verified_outcome)
   return fail('INDEPENDENT_CANONICAL_EVIDENCE_RECEIPT_REQUIRED');
  try{
   bound=await loadIndexGapRoute({
    identity,member_id:request.member_id,gap_id:request.gap_id});
  }catch{return fail('INDEPENDENT_INDEX_GAP_LOOKUP_FAILED')}
  const gap=bound?.gap,route=bound?.route;
  if(!gap||gap.owner!=='LEARNING_ENGINE_CORE'||gap.gap_id!==request.gap_id||
     gap.scope?.member_id!==event.member_id||
     norm(gap.scope?.subject)!==norm(event.subject)||
     norm(gap.scope?.concept_skill_target)!==norm(event.concept_skill_target)||
     !route||route.pass!==true)
   return fail('CROSS_OWNER_EVIDENCE_GAP_SCOPE_MISMATCH');
  const mining=route.decision==='MINING_REQUEST';
  if(mining&&(
     gap.resolution_path!=='INDEX_THEN_MINING_IF_INSUFFICIENT'||
     gap.index_check_required!==true||gap.mining_request_authorized===true||
     route.index_checked!==true||route.index_sufficient!==false||
     route.mining_request?.gap_id!==request.gap_id||
     route.mining_request?.index_check?.performed!==true||
     !Array.isArray(route.mining_request?.required_provenance)||
     !route.mining_request.required_provenance.length))
   return fail('INDEX_FIRST_SOURCE_CONSTRAINTS_REQUIRED');
  if(!mining&&!['INDEX_REQUERY','INDEX_AUTHORITY_REVIEW_REQUIRED',
      'SPECIALIST_EVIDENCE_REQUEST'].includes(route.decision))
   return fail('UNKNOWN_INDEPENDENT_INDEX_GAP_DECISION');
  const feedback=Feedback.derive({
   outcome:{verified_outcome:event.verified_outcome,verification:{
     authority:event.verification.authority,receipt_id:event.verification.receipt_id},
     assistance:event.assistance||null,assisted:event.assisted,
     attempt_count:event.attempt_count,source_app:event.source_app,
     learning_target_id:event.learning_target_id||null},
   prior_decision:stored.prior_decision||{},
   prior_evidence_gap:gap,
   index_gap_route:mining?route:null
  });
  if(!feedback.ok||!Feedback.validate(feedback).ok||
     feedback.learning_strategy_feedback.verified_target!==true||
     (mining&&feedback.mining_strategy_feedback_candidate?.gap_id!==request.gap_id)||
     (!mining&&feedback.mining_strategy_feedback_candidate))
   return fail('GROWTH_FEEDBACK_CONTRACT_INVALID');
  return {ok:true,authority:'INDEPENDENT_EVIDENCE_AND_INDEX_FIXTURE_ONLY',
    verified_outcome_authorized:true,feedback,
    evidence_binding:{event_id:event.event_id,receipt_id:receipt.receipt_id,
      evidence_digest_sha256:receipt.evidence_digest_sha256,
      verification_receipt_id:event.verification.receipt_id,
      member_id:event.member_id,learning_target_id:event.learning_target_id||null},
    index_gap_id:request.gap_id,index_gap_decision:route.decision,
    mining_growth_dispatch_authorized:false,learning_promotion_authorized:false,
    index_write_authorized:false,
    invariant:'INDEPENDENT_RECORD_LOOKUP_NOT_CLIENT_CLAIM__NO_MINING_RUN_OUTCOME_SYNTHESIS'};
 }
 return Object.freeze({derive});
}
module.exports=Object.freeze({create});
