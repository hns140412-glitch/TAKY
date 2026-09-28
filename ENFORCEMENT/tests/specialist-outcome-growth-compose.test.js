'use strict';
/** Isolated ACTUAL source composition:
 * PR159 server-assessment scorer -> main Verification.applyReceipt ->
 * main immutable batch receipt -> audit-only independent owner growth gate.
 * Fixture owns server records, not a deployed token issuer or true user result.
 */
const assert=require('node:assert/strict');
const Specialist=require('../../central-draft/LEARNING/transport/server-specialist-verifier.js');
const Verification=require('../../canonical-main/LEARNING/verification/verification-layer.js');
const Receipt=require('../../canonical-main/LEARNING/receipts/real-evidence-receipt.js');
const Gate=require('../trusted_outcome_growth_audit.js');

const MEMBER='TEST_CHILD_A',FAMILY='TEST_FAMILY_1';
const EVENT='server-outcome-1',GAP='test-reference-gap-1',REF='server-assignment-1';
const TIME=Date.UTC(2026,8,28,6,0,0);
const identity={authenticated:true,family_id:FAMILY,authorized_member_ids:[MEMBER]};
const reference={authority:'TAKY_SERVER_ASSESSMENT_REFERENCE_V1',status:'ACTIVE',
  family_id:FAMILY,member_id:MEMBER,event_id:EVENT,source_app:'hide-seek',
  subject:'english',concept_skill_target:'vocabulary',reference_id:REF,
  expected_response:'apple',match_rule:'EXACT_NFC',
  instrument_version:'HIDE_TEST_V1',
  issued_at:'2026-09-28T05:00:00.000Z',
  expires_at:'2026-09-28T07:00:00.000Z'};
const packet={packet_id:'fixture:'+EVENT,source_app:'hide-seek',
 context:{family_id:FAMILY,member_id:MEMBER,subject:'english',
  concept_skill_target:'vocabulary'},
 event:{event_id:EVENT,source:'hide-seek',occurred_at:'2026-09-28T05:30:00.000Z',
  event_type:'RETRIEVAL_RESULT',payload:{assessment_ref:REF,response_text:'apple',
   instrument_version:'HIDE_TEST_V1',
   verification_candidate:{basis:'DETERMINISTIC_LOCAL_MATCH',
    verifier_type:'RETRIEVAL_EXACT_MATCH',outcome:0,reference_id:'browser:forged'}}}};
packet.context.verification_receipt={
 authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'browser:fake-receipt'};

const scopeGap={owner:'LEARNING_ENGINE_CORE',gap_id:GAP,
 gap_type:'REFERENCE_EVIDENCE_REQUIRED',
 resolution_path:'INDEX_THEN_MINING_IF_INSUFFICIENT',
 index_check_required:true,mining_request_authorized:false,
 scope:{member_id:MEMBER,subject:'english',concept_skill_target:'vocabulary'}};
const route={pass:true,decision:'MINING_REQUEST',index_checked:true,
 index_sufficient:false,mining_request:{gap_id:GAP,
  index_check:{performed:true,eligible_result_count:0,minimum_required:1},
  required_provenance:['INDEPENDENT_SOURCE_REF']}};
const selector={principal_id:'test:parent',family_id:FAMILY,
 member_id:MEMBER,event_id:EVENT,gap_id:GAP};
(async()=>{
 const scorer=Specialist.create({
  loadAssessment:async scope=>(scope.family_id===FAMILY&&scope.member_id===MEMBER&&
    scope.event_id===EVENT&&scope.reference_id===REF)?reference:null,
  now:()=>TIME
 });
 const actual=await scorer.verifySpecialistEvidence({packet,identity});
 assert.equal(actual.ok,true,JSON.stringify(actual));
 assert.notEqual(actual.packet.context.verification_receipt.receipt_id,
  'browser:fake-receipt');
 assert.equal(actual.packet.event.payload.verification_candidate.server_reference_checked,true);
 assert.equal(actual.packet.event.payload.verification_candidate.outcome,undefined);

 const evidence={event_id:EVENT,observed_at:packet.event.occurred_at,
  member_id:MEMBER,subject:'english',concept_skill_target:'vocabulary',
  learning_target_id:'unit-1',source_app:'hide-seek',
  instrument_version:'HIDE_TEST_V1',evidence_type:'MEMORY_RETRIEVAL_EVIDENCE'};
 const applied=Verification.applyReceipt(evidence,
  actual.packet.context.verification_receipt);
 assert.equal(applied.ok,true,JSON.stringify(applied));
 assert.equal(applied.evidence.verified_outcome,1);
 const batch=Receipt.issueBatchReceipt([applied.evidence],{
  receipt_id:'fixture-immutable-batch-1',
  created_at:'2026-09-28T06:00:00.000Z'});
 assert.equal(batch.ok,true);
 const stored={canonical_evidence:applied.evidence,
  batch_evidence:[applied.evidence],batch_receipt:batch.receipt,
  prior_decision:{execution_status:'PEDAGOGICAL_ACTION_AVAILABLE'}};
 const gate=Gate.create({
  resolveIdentity:async({principal_id})=>principal_id==='test:parent'?identity:null,
  loadVerifiedEvidence:async({identity:i,member_id,event_id})=>
   i.family_id===FAMILY&&member_id===MEMBER&&event_id===EVENT?stored:null,
  loadIndexGapRoute:async({identity:i,member_id,gap_id})=>
   i.family_id===FAMILY&&member_id===MEMBER&&gap_id===GAP?
    {gap:scopeGap,route}:null
 });
 const result=await gate.derive(selector);
 assert.equal(result.ok,true,JSON.stringify(result));
 assert.equal(result.feedback.learning_strategy_feedback.verified_target,true);
 assert.equal(result.feedback.learning_strategy_feedback.outcome,1);
 assert.equal(result.feedback.mining_strategy_feedback_candidate.gap_id,GAP);
 assert.equal(result.mining_growth_dispatch_authorized,false);
 assert.equal(result.index_write_authorized,false);
 assert.equal(result.learning_promotion_authorized,false);
 assert.equal(result.evidence_binding.verification_receipt_id,
  actual.packet.context.verification_receipt.receipt_id);
 assert.equal((await gate.derive({...selector,member_id:'TEST_CHILD_B'})).ok,false);
 assert.equal((await gate.derive({...selector,
  outcome:{verified_outcome:0},verification:packet.context.verification_receipt})).ok,false);
 const cross=await scorer.verifySpecialistEvidence({
  packet:{...packet,context:{...packet.context,member_id:'TEST_CHILD_B'}},
  identity
 });
 assert.equal(cross.ok,false);
 const unissued=await Specialist.create({
  loadAssessment:async()=>null,now:()=>TIME
 }).verifySpecialistEvidence({packet,identity});
 assert.equal(unissued.ok,false);
 console.log('PASS ACTUAL_PR159_SERVER_VERIFIER_TO_MAIN_RECEIPT_TO_GROWTH_OWNER_GATE: forged browser receipt ignored; exact member and issued reference; no provider dispatch or promotion');
})().catch(e=>{console.error(e);process.exitCode=1});
