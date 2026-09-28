'use strict';
// Actual pinned main Learning receipt/feedback and independent V2 growth code
// are used. Independent server callbacks below are TEST-ONLY fixed registries.
const assert=require('node:assert/strict');
const Receipt=require('../../canonical-main/LEARNING/receipts/real-evidence-receipt.js');
const Feedback=require('../../canonical-main/LEARNING/lifecycle/outcome-growth-feedback.js');
const Gate=require('../trusted_outcome_growth_audit.js');
const {spawnSync}=require('node:child_process');
const path=require('node:path');

const EVENT={
 event_id:'evt-A-1',observed_at:'2026-09-28T02:00:00.000Z',
 member_id:'A',subject:'영어',concept_skill_target:'vocabulary',
 learning_target_id:'unit-1',evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
 source_app:'hide-seek',instrument_version:'HIDE_CODE_RED_V1',
 verified_outcome:1,assisted:false,assistance:'UNASSISTED',attempt_count:1,
 verification:{authority:'LEARNING_VERIFICATION_RECEIPT',
  receipt_id:'vr:server:evt-A-1',verifier_type:'RETRIEVAL_EXACT_MATCH',
  verifier_version:'server-v1'}
};
const GAP={
 owner:'LEARNING_ENGINE_CORE',gap_id:'GAP-A-1',
 gap_type:'REFERENCE_EVIDENCE_REQUIRED',
 resolution_path:'INDEX_THEN_MINING_IF_INSUFFICIENT',
 index_check_required:true,mining_request_authorized:false,
 scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
};
const ROUTE={pass:true,decision:'MINING_REQUEST',index_checked:true,
 index_sufficient:false,mining_request:{gap_id:'GAP-A-1',
  index_check:{performed:true,eligible_result_count:0,minimum_required:1},
  required_provenance:['OFFICIAL_REVIEWED_REFERENCE']}};
const SELECTOR={principal_id:'fixture-parent',family_id:'F1',member_id:'A',
 event_id:'evt-A-1',gap_id:'GAP-A-1'};
const clone=x=>JSON.parse(JSON.stringify(x));
const issued=Receipt.issueBatchReceipt([EVENT],{receipt_id:'batch-A-1',
 created_at:'2026-09-28T02:01:00.000Z'});
assert.equal(issued.ok,true);
const canonical=()=>({batch_evidence:[clone(EVENT)],
 canonical_evidence:clone(EVENT),batch_receipt:clone(issued.receipt),
 prior_decision:{execution_status:'PEDAGOGICAL_ACTION_AVAILABLE'}});
function service({evidence=canonical(),gap=clone(GAP),route=clone(ROUTE),
 identity={authenticated:true,family_id:'F1',authorized_member_ids:['A']}}={}){
 return Gate.create({
  resolveIdentity:async({principal_id})=>principal_id==='fixture-parent'?identity:null,
  loadVerifiedEvidence:async({identity,member_id,event_id})=>
   identity?.family_id==='F1'&&member_id==='A'&&event_id===EVENT.event_id?evidence:null,
  loadIndexGapRoute:async({identity,member_id,gap_id})=>
   identity?.family_id==='F1'&&member_id==='A'&&gap_id===GAP.gap_id?{gap,route}:null
 });
}
(async()=>{
 // First reproduce actual source-level concern, without pretending that this
 // caller has permission to persist or issue a trusted server receipt.
 const fake=Feedback.derive({
  outcome:{verified_outcome:1,verification:{
   authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'user-typed-string'}},
  prior_evidence_gap:clone(GAP),
  index_gap_route:clone(ROUTE)
 });
 assert.equal(fake.learning_strategy_feedback.verified_target,true);
 assert.equal(fake.mining_strategy_feedback_candidate.outcome_signal,'SUCCESS');
 const python=spawnSync('python3',['-c',[
  'import json,sys','sys.path.insert(0,sys.argv[1])',
  'from mining_run_orchestrator import orchestrate',
  'r=orchestrate({"task":{"goal":"synthetic","task_family":"REFERENCE_EVIDENCE"},',
  '"memory":{},"index_rows":[],"outcome":{"success":True,"accuracy":1,',
  '"usefulness":1,"completeness":1,"efficiency":1,"user_correction_rate":0}})',
  'print(json.dumps({"type":r["growth_proposal"]["proposal"]["type"],',
  '"promote":r["growth_proposal"]["proposal"]["promotion_allowed"]}))'
 ].join('\n'),path.resolve('mining-v2/ENFORCEMENT')],{encoding:'utf8'});
 assert.equal(python.status,0,python.stderr);
 assert.deepEqual(JSON.parse(python.stdout),{type:'STRATEGY_OBSERVATION',promote:false});

 assert.throws(()=>Gate.create({}),/EXPLICIT_INDEPENDENT_SERVER_RESOLVERS_REQUIRED/);
 const good=await service().derive(SELECTOR);
 assert.equal(good.ok,true,JSON.stringify(good));
 assert.equal(good.feedback.learning_strategy_feedback.verified_target,true);
 assert.equal(good.feedback.learning_strategy_feedback.outcome,1);
 assert.equal(good.feedback.mining_strategy_feedback_candidate.gap_id,'GAP-A-1');
 assert.equal(good.mining_growth_dispatch_authorized,false);
 assert.equal(good.learning_promotion_authorized,false);
 assert.equal(good.index_write_authorized,false);
 assert.equal(good.evidence_binding.learning_target_id,'unit-1');
 const injected=await service().derive({...SELECTOR,
  outcome:{verified_outcome:1},identity:{authenticated:true},index_gap_route:ROUTE});
 assert.equal(injected.reason,'SELECTOR_ONLY_CLIENT_REQUEST_REQUIRED');
 const changedMember=await service().derive({...SELECTOR,member_id:'B'});
 assert.equal(changedMember.ok,false);
 const changedFamily=await service().derive({...SELECTOR,family_id:'F2'});
 assert.equal(changedFamily.reason,'TRUSTED_FAMILY_MEMBER_SCOPE_REQUIRED');
 const untrusted=await service({identity:{authenticated:false,family_id:'F1',
  authorized_member_ids:['A']}}).derive(SELECTOR);
 assert.equal(untrusted.reason,'TRUSTED_FAMILY_MEMBER_SCOPE_REQUIRED');

 const changed=canonical();changed.canonical_evidence.subject='국어';
 assert.equal((await service({evidence:changed}).derive(SELECTOR)).reason,
  'INDEPENDENT_CANONICAL_EVIDENCE_RECEIPT_REQUIRED');
 const forged=canonical();forged.batch_evidence[0].verified_outcome=0;
 forged.canonical_evidence.verified_outcome=0;
 assert.equal((await service({evidence:forged}).derive(SELECTOR)).reason,
  'INDEPENDENT_CANONICAL_EVIDENCE_RECEIPT_REQUIRED');
 const tampered=canonical();tampered.batch_receipt.scope.member_id='B';
 assert.equal((await service({evidence:tampered}).derive(SELECTOR)).reason,
  'INDEPENDENT_CANONICAL_EVIDENCE_RECEIPT_REQUIRED');
 const wrongScope=clone(GAP);wrongScope.scope.member_id='B';
 assert.equal((await service({gap:wrongScope}).derive(SELECTOR)).reason,
  'CROSS_OWNER_EVIDENCE_GAP_SCOPE_MISMATCH');
 const falseIndex=clone(ROUTE);falseIndex.mining_request.index_check.performed=false;
 assert.equal((await service({route:falseIndex}).derive(SELECTOR)).reason,
  'INDEX_FIRST_SOURCE_CONSTRAINTS_REQUIRED');
 const unsupported=clone(ROUTE);unsupported.decision='UNKNOWN';
 assert.equal((await service({route:unsupported}).derive(SELECTOR)).reason,
  'UNKNOWN_INDEPENDENT_INDEX_GAP_DECISION');
 const authorityReview=clone(ROUTE);
 authorityReview.decision='INDEX_AUTHORITY_REVIEW_REQUIRED';
 const held=await service({route:authorityReview}).derive(SELECTOR);
 assert.equal(held.ok,true);
 assert.equal(held.feedback.mining_strategy_feedback_candidate,null);
 assert.equal(held.mining_growth_dispatch_authorized,false);
 const learner=clone(ROUTE);learner.decision='SPECIALIST_EVIDENCE_REQUEST';
 const specialist=await service({route:learner}).derive(SELECTOR);
 assert.equal(specialist.ok,true);
 assert.equal(specialist.feedback.mining_strategy_feedback_candidate,null);
 console.log('PASS: actual main/V2 fake-input reproduction; independent selected-scope, receipt, gap and no-growth-dispatch negative cases');
})().catch(e=>{console.error(e);process.exitCode=1});
