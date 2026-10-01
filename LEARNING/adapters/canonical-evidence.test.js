'use strict';
const assert=require('node:assert/strict');
const A=require('./canonical-evidence.js');
const V=require('../verification/verification-layer.js');

const ctx={member_id:'A',session_id:'S1',task_id:'T1',lap_id:'L1',subject:'영어',concept_skill_target:'VOCABULARY',instrument_version:'bridge-v1',curriculum_refs:['CURR:ENG5:1'],lexical_refs:['OEWN:accept'],usage_refs:['USAGE:accept-an-idea']};

const hide=A.fromHide({
  event_id:'h1',source:'hide-seek',event_type:'TASK_COMPLETED',occurred_at:'2026-09-25T07:00:00.000Z',
  payload:{word_id:'w1',caseMastery:84,validWordCount:12,sheetStatus:'COMPLETED',memorySummary:{averageMemoryStrength:67,reviewAdvisories:[{lexicalId:'w1',nextReviewPriority:90}],prioritySemantics:'ADVISORY_SIGNAL_NOT_DATE'}}
},ctx);
assert.equal(hide.evidence_type,'MEMORY_RETRIEVAL_EVIDENCE');
assert.equal(hide.learning_target_id,'w1');
assert.equal(hide.memory.average_strength,67);
assert.equal(hide.raw_app_signals.case_mastery,84);
assert.equal(hide.verified_outcome,null,'app mastery score must not become verified outcome');
assert.equal(A.validateCanonical(hide).ok,true);


const itemSignal=A.fromHide({
  event_id:'h-item-1',source:'hide-seek',event_type:'LEARNING_MEMORY_SIGNAL',
  occurred_at:'2026-10-02T07:00:00.000Z',
  payload:{
    word:'accept',skill_id:'accept',correct:true,assisted:false,
    mode:'TRACE',confusion:null,weakness:null,spacedEvidence:false,
    nextReviewPriority:72,word_origin:'CURRENT',sourceSheetId:'sheet-current',
    hint_stage:1,helped:true,self_corrected:false,recall_degree:0.6,
    responseLatencyMs:1450,
    connection_evidence:{left_id:'accept',right_id:'accept',matched:true},
    spelling_evidence:{instrument:'HIDE_CODE_RED_V1',result_type:'HINT_USED'}
  }
},ctx);
assert.equal(itemSignal.evidence_type,'MEMORY_RETRIEVAL_EVIDENCE');
assert.equal(itemSignal.learning_target_id,'accept');
assert.equal(itemSignal.interaction_mode,'TRACE');
assert.equal(itemSignal.memory.item_signal.mode,'TRACE');
assert.equal(itemSignal.memory.item_signal.word_origin,'CURRENT');
assert.equal(itemSignal.memory.item_signal.correct,true);
assert.equal(itemSignal.memory.review_advisories[0].nextReviewPriority,72);
assert.equal(itemSignal.memory.item_signal.hint_stage,1);
assert.equal(itemSignal.memory.item_signal.helped,true);
assert.equal(itemSignal.memory.item_signal.self_corrected,false);
assert.equal(itemSignal.memory.item_signal.recall_degree,0.6);
assert.equal(itemSignal.memory.item_signal.response_latency_ms,1450);
assert.equal(itemSignal.memory.item_signal.connection_evidence.matched,true);
assert.equal(itemSignal.memory.item_signal.spelling_evidence.result_type,'HINT_USED');
assert.equal(itemSignal.verified_outcome,null);
assert.equal(A.validateCanonical(itemSignal).ok,true);

const hideGrowth=A.fromHide({
  event_id:'hg1',source:'hide-seek',event_type:'LEARNING_MEMORY_SIGNAL',
  occurred_at:'2026-10-02T08:00:00.000Z',
  payload:{
    word:'accept',learning_target_id:'accept',mode:'TRACE',
    growth_signals:[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,target_id:'accept'},
      {dimension:'ENGLISH_THINKING',outcome:'PARTIAL',direct_english:true,target_id:'accept'}
    ]
  }
},ctx);
assert.equal(hideGrowth.language_growth_signals.length,2);
assert.equal(hideGrowth.language_growth_signals[0].dimension,'VOCABULARY');
assert.equal(hideGrowth.language_growth_signals[1].direct_english,true);
assert.equal(A.validateCanonical(hideGrowth).ok,true);

const snap=A.fromSnap({
  event_id:'s1',source:'snap-pop',event_type:'TASK_COMPLETED',occurred_at:'2026-09-25T08:00:00.000Z',
  payload:{
    child_authored:true,landmark:'forest',step:3,used_handoff_word:'ocean',
    production_texts:['I saw the ocean.','The ocean looked calm.','I liked it because it felt peaceful.'],
    vocabulary_used:['ocean'],
    expression_expansion:{step_lengths:[16,22,38],quality_judgment:'UNVERIFIED'},
    reasoning_evidence:{raw_response_present:true,quality_judgment:'UNVERIFIED'},
    story_structure:{completed_steps:3,expected_steps:3,quality_judgment:'UNVERIFIED'},
    direct_english:null,
    expression_reuse:{handoff_word_reused:true},
    self_correction:null,
    assistance_strength:null,
    growth_intent_ref:'TAKY_GROWTH_NEXT_STEP_POLICY_V2',
    growth_verification_status:'PENDING_DIMENSION_REVIEW',
    growth_review_required:true,
    requested_growth_dimensions:['GRAMMAR','EXPRESSION','THINKING','ENGLISH_THINKING'],
    growth_control_applied:{
      evidence_confidence:'MEDIUM',
      learning_intensity:'STRETCH_TRANSFER',
      expression_level:'L4_REASONED_RESPONSE',
      question_depth:4,
      hint_strength:'MINIMAL_CUE',
      hint_fade:'MINIMAL_CUE',
      challenge_direction:'TRANSFER'
    },
    growth_signals:[
      {dimension:'EXPRESSION',outcome:'SUCCESS',assisted:false,transfer:true,depth:4}
    ]
  }
},ctx);
assert.equal(snap.evidence_type,'LEARNER_PRODUCTION_EVIDENCE');
assert.equal(snap.production.child_authored,true);
assert.equal(snap.production.production_texts.length,3);
assert.deepEqual(snap.production.vocabulary_used,['ocean']);
assert.equal(snap.production.expression_expansion.quality_judgment,'UNVERIFIED');
assert.equal(snap.production.reasoning_evidence.quality_judgment,'UNVERIFIED');
assert.equal(snap.production.story_structure.completed_steps,3);
assert.equal(snap.production.expression_reuse.handoff_word_reused,true);
assert.equal(snap.production.raw_observation_only,true);
assert.equal(snap.production.quality_interpretation_authority,false);
assert.equal(snap.production.local_growth_grading_forbidden,true);
assert.equal(snap.verified_outcome,null,'child authored completion is not objective mastery');
assert.equal(snap.growth_execution_context.authority,'SPECIALIST_EXECUTION_CONTEXT_ONLY');
assert.equal(snap.growth_execution_context.expression_level,'L4_REASONED_RESPONSE');
assert.equal(snap.growth_execution_context.engine_authority,false);
assert.equal(snap.raw_app_signals.growth_intent_ref,'TAKY_GROWTH_NEXT_STEP_POLICY_V2');
assert.equal(snap.raw_app_signals.growth_verification_status,'PENDING_DIMENSION_REVIEW');
assert.equal(snap.raw_app_signals.growth_review_required,true);
assert.deepEqual(snap.raw_app_signals.requested_growth_dimensions,
 ['GRAMMAR','EXPRESSION','THINKING','ENGLISH_THINKING']);
assert.equal(A.validateCanonical(snap).ok,true);

const ready=A.fromReady({
  event_id:'r1',source:'ready-set',occurred_at:'2026-09-25T09:00:00.000Z',
  payload:{
    evidence_type:'CHILD_SELF_REPORT',
    self_report:{difficulty:'HARD'},
    planner_allocation:{
      authority:'READY_SET_PLANNER_ALLOCATION',
      date:'2026-09-25',quantity:4,date_and_quantity_owner:'READY_SET_PLANNER'
    },
    started_at:'2026-09-25T08:30:00.000Z',
    ended_at:'2026-09-25T09:00:00.000Z',
    actual_minutes:30,performed_quantity:3,
    completion_state:'PARTIAL',parent_confirmation:false
  }
},{...ctx,evidence_type:'CHILD_SELF_REPORT'});
assert.equal(ready.evidence_type,'CHILD_SELF_REPORT');
assert.equal(ready.verified_outcome,null);
assert.equal(ready.raw_app_signals.planner_allocation.authority,'READY_SET_PLANNER_ALLOCATION');
assert.equal(ready.raw_app_signals.actual_minutes,30);
assert.equal(ready.raw_app_signals.performed_quantity,3);
assert.equal(ready.raw_app_signals.completion_state,'PARTIAL');
assert.equal(ready.references.curriculum_refs[0],'CURR:ENG5:1');
assert.equal(ready.references.lexical_refs[0],'OEWN:accept');
assert.equal(ready.references.usage_refs[0],'USAGE:accept-an-idea');
assert.equal(A.validateCanonical(ready).ok,true);


const friction=A.fromReady({
  event_id:'rf1',source:'ready-set',occurred_at:'2026-10-02T10:00:00.000Z',
  payload:{
    member_id:'A',subject:'영어',concept_skill_target:'vocabulary',
    evidence_type:'READY_EXECUTION_FRICTION_OBSERVATION',
    instrument_version:'READY_CARRY_FRICTION_V1',
    observation_only:true,global_mastery_claim:false,
    forwarded_ready_friction_observation:true,
    assignment_id:'assignment-1',source_carry_over_id:'carry-1',
    carry_over_depth:4,carry_over_state:'OPEN',
    escalation_reason:'REPEATED_CARRY_LIMIT',
    observation_count:4,friction_states:['PARTIAL','DEFERRED','BLOCKED'],
    actual_minutes:[20,22,25]
  }
},ctx);
assert.equal(friction.evidence_type,'READY_EXECUTION_FRICTION_OBSERVATION');
assert.equal(friction.observation_only,true);
assert.equal(friction.verified_outcome,null);
assert.equal(friction.execution_friction.authority,'READY_EXECUTION_FRICTION_OBSERVATION_ONLY');
assert.equal(friction.execution_friction.learner_state_authority,false);
assert.equal(friction.raw_app_signals.forwarded_ready_friction_observation,true);
assert.equal(friction.identity.scope_kind,'AGGREGATED_EXECUTION');
assert.equal(A.validateCanonical(friction).ok,true);

const imagination=A.fromImaginationCloud({
  event_id:'i1',source:'imagination-cloud',event_type:'HELP_USED',
  occurred_at:'2026-10-02T08:30:00.000Z',
  payload:{
    invocation_reason:'CONCEPT_NOT_CLEAR',
    target_concept:'fraction equivalence',
    visualization_used:'AREA_MODEL',
    explanation_used:'STEP_BY_STEP',
    response_before:{state:'UNSURE'},
    response_after:{state:'CAN_EXPLAIN_PART'},
    additional_help_needed:true,
    curiosity_only:false
  }
},ctx);
assert.equal(imagination.evidence_type,'LEARNING_SUPPORT_OBSERVATION');
assert.equal(imagination.observation_only,true);
assert.equal(imagination.verified_outcome,null);
assert.equal(imagination.support_observation.authority,'IMAGINATION_CLOUD_SUPPORT_OBSERVATION_ONLY');
assert.equal(imagination.support_observation.learner_state_authority,false);
assert.equal(imagination.support_observation.schedule_authority,false);
assert.equal(A.validateCanonical(imagination).ok,true);

const receipt=V.issueReceipt({
  receipt_id:'vr-h2',
  target_event_id:'h2',
  verified_at:'2026-09-26T07:01:00.000Z',
  verifier_type:'RETRIEVAL_EXACT_MATCH',
  verifier_version:'1.0.0',
  outcome:1,
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  reference_id:'answer-key:vocab-001'
}).receipt;
const verifiedHide=A.fromHide({
  event_id:'h2',source:'hide-seek',event_type:'TASK_COMPLETED',occurred_at:'2026-09-26T07:00:00.000Z',
  payload:{memorySummary:{averageMemoryStrength:80}}
},{...ctx,verification_receipt:receipt});
assert.equal(verifiedHide.verified_outcome,1,'verified outcome must require a valid verification receipt');
assert.equal(verifiedHide.verification.receipt_id,'vr-h2');

const forged={...hide,verified_outcome:1};
assert.equal(A.validateCanonical(forged).ok,false);
assert.equal(A.validateCanonical(forged).issues.includes('VERIFIED_OUTCOME_WITHOUT_RECEIPT'),true);

const leaked={...hide,due_at:'2026-09-30T07:00:00.000Z'};
assert.equal(A.validateCanonical(leaked).ok,false);
assert.equal(A.validateCanonical(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('CANONICAL_LEARNING_EVIDENCE_ADAPTER_PASS');

const autoVerified=A.fromHide({
  event_id:'h3',
  source:'hide-seek',
  event_type:'RETRIEVAL_ATTEMPT_RESULT',
  occurred_at:'2026-09-27T07:00:00.000Z',
  payload:{
    instrumentVersion:'HIDE_CODE_RED_V1',
    interactionMode:'CORE',
    assisted:false,
    attemptCount:1,
    responseLatencyMs:1200,
    verification_candidate:{
      verifier_type:'RETRIEVAL_EXACT_MATCH',
      verifier_version:'HIDE_CODE_RED_V1',
      target_semantics:'UNASSISTED_EXACT_RETRIEVAL',
      outcome:1,
      reference_id:'hide-word:sheet-1:w1:spelling',
      basis:'DETERMINISTIC_LOCAL_MATCH',
      result_type:'CORRECT'
    }
  }
},ctx);
assert.equal(autoVerified.evidence_type,'MEMORY_RETRIEVAL_EVIDENCE');
assert.equal(autoVerified.verified_outcome,1);
assert.equal(autoVerified.verification.verifier_type,'RETRIEVAL_EXACT_MATCH');
assert.equal(autoVerified.instrument_version,'HIDE_CODE_RED_V1');
assert.equal(autoVerified.assistance,'UNASSISTED');
assert.equal(A.validateCanonical(autoVerified).ok,true);
