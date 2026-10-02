'use strict';

const assert=require('node:assert/strict');
const Runtime=require('./learning-engine-runtime.js');
const Overlay=require('../policy/reference-intake-v29-policy.js');

const ROWS={
  'REF-068':{
    source_family:'NIKH_OUR_HISTORY_NET',
    authority_class:'PRIMARY_OFFICIAL_EDUCATION_SOURCE',
    provenance:['REFERENCE_MINING_INDEX','REF-068']
  },
  'REF-069':{
    source_family:'NATIONAL_BASIC_SKILLS_SUPPORT_CENTER',
    authority_class:'PRIMARY_OFFICIAL_EDUCATION_SUPPORT',
    provenance:['REFERENCE_MINING_INDEX','REF-069']
  },
  'REF-070':{
    source_family:'MATH_CIRCLE_CONCEPT_CONFUSION_GRAPH',
    authority_class:'USER_PROVIDED_VISUAL_REFERENCE',
    provenance:['REFERENCE_MINING_INDEX','REF-070']
  },
  'REF-071':{
    source_family:'TWINKL_KOREA_FREE_DAY_20261006',
    authority_class:'VENDOR_PROMOTION_SOURCE',
    provenance:['REFERENCE_MINING_INDEX','REF-071']
  },
  'REF-074':{
    source_family:'THREE_QUESTION_WRITING_SCAFFOLD',
    authority_class:'COMMERCIAL_PRACTICE_REFERENCE',
    provenance:['REFERENCE_MINING_INDEX','REF-074']
  },
  'REF-075':{
    source_family:'OPEN_ENDED_READING_DIALOGUE_REFERENCE',
    authority_class:'USER_CREATED_PRACTICE_REFERENCE',
    provenance:['REFERENCE_MINING_INDEX','REF-075']
  }
};

function ownerVerifier(sourceId,sourceRef){
  const row=ROWS[sourceId];
  if(!row||sourceRef!=='INDEX:'+sourceId)return null;
  return {
    ...row,
    source_type:null,
    detail_anchor:null,
    issuer:'INDEXING_OWNER',
    reviewed:true,
    decision:'INDEXED',
    domain_use_authorized:true,
    source_id:sourceId,
    source_ref:sourceRef,
    index_version:'V29',
    review_evidence_refs:[
      'C2S/DATA_INDEX_V29_INDEX_OWNER_RECEIPT_2026-10-02.json',
      'REFERENCE_MINING_INDEX#'+sourceId
    ]
  };
}

function evidence(subject,target,id){
  return [{
    event_id:'v29-runtime-'+id,
    observed_at:'2026-10-02T04:10:00.000Z',
    member_id:'TEST_CHILD',
    subject,
    concept_skill_target:target,
    evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
    source_app:'reference-v29-test',
    instrument_version:'v29-test-1',
    assisted:false,
    verified_outcome:1,
    verification:{
      authority:'LEARNING_VERIFICATION_RECEIPT',
      receipt_id:'vr-'+id
    }
  }];
}

const CASES=[
  {
    id:'REF-068',subject:'사회',target:'HISTORY_CONCEPT_LINK',
    function_id:'LE-RV29-HISTORY',consumer_app:'HIDE_SEEK',
    behavior:'HISTORY_CONCEPT_LINK_REFERENCE'
  },
  {
    id:'REF-069',subject:'기초학력',target:'REMEDIATION_REFERENCE',
    function_id:'LE-RV29-REMEDIATION',consumer_app:'READY_SET',
    behavior:'REMEDIATION_RESOURCE_REFERENCE'
  },
  {
    id:'REF-070',subject:'수학',target:'CIRCLE_TERM_CONFUSION',
    function_id:'LE-RV29-CIRCLE',consumer_app:'HIDE_SEEK',
    behavior:'CONCEPT_CONFUSION_REFERENCE'
  },
  {
    id:'REF-071',subject:'학습자료',target:'SUPPLEMENTAL_RESOURCE',
    function_id:'LE-RV29-RESOURCE',consumer_app:'READY_SET',
    behavior:'SUPPLEMENTAL_RESOURCE_DISCOVERY'
  },
  {
    id:'REF-074',subject:'국어',target:'WRITING_SCAFFOLD',
    function_id:'LE-RV29-WRITING',consumer_app:'SNAP_POP',
    behavior:'WRITING_PROCESS_SCAFFOLD'
  },
  {
    id:'REF-075',subject:'국어',target:'READING_DIALOGUE',
    function_id:'LE-RV29-READING',consumer_app:'SNAP_POP',
    behavior:'OPEN_ENDED_READING_DIALOGUE'
  }
];

function handoff(c,claims=[]){
  const row=ROWS[c.id];
  return {
    query_context:{
      function_id:c.function_id,
      consumer_app:c.consumer_app,
      requested_behavior:c.behavior,
      requested_claims:claims
    },
    candidates:[{
      source_id:c.id,
      source_ref:'INDEX:'+c.id,
      source_family:row.source_family,
      source_type:null,
      authority_class:row.authority_class,
      detail_anchor:null,
      provenance:[...row.provenance],
      relations:[]
    }]
  };
}

for(const c of CASES){
  const scope={
    member_id:'TEST_CHILD',
    subject:c.subject,
    concept_skill_target:c.target
  };
  const ev=evidence(c.subject,c.target,c.id);
  const baseline=Runtime.derive({scope,evidence:ev});
  assert.equal(baseline.ok,true,c.id+' baseline must pass');

  const out=Runtime.derive({
    scope,
    evidence:ev,
    indexed_evidence_handoff:handoff(c)
  },ownerVerifier,Overlay.REGISTRY);

  assert.equal(out.ok,true,c.id+' overlay runtime must pass');
  assert.deepEqual(out.trace.source_refs,['INDEX:'+c.id],c.id+' source_ref must survive');
  assert.equal(out.evidence_policy.results[0].decision,'ALLOW_CONDITIONAL');
  assert.equal(out.indexed_evidence.invariant,
    'INDEX_RETRIEVAL_METADATA_IS_CONTEXT_NOT_LEARNER_PERFORMANCE');
  assert.deepEqual(out.learner_state,baseline.learner_state,
    c.id+' reference metadata must not mutate learner state');
  assert.equal(out.learner_state.observed.unique_evidence_count,1);
  assert.equal(Runtime.validate(out).ok,true,c.id+' runtime validation must pass');
  assert.equal(out.cannot_influence.includes('SCHEDULE_DATE'),true);
  assert.equal(out.cannot_influence.includes('PLANNER_DATE'),true);
}

// Default CURRENT policy must still fail closed for a V29-only function.
{
  const c=CASES[0];
  const scope={member_id:'TEST_CHILD',subject:c.subject,concept_skill_target:c.target};
  const out=Runtime.derive({
    scope,
    evidence:evidence(c.subject,c.target,c.id+'-default'),
    indexed_evidence_handoff:handoff(c)
  },ownerVerifier);
  assert.equal(out.ok,false);
  assert.equal(out.reason,'EVIDENCE_POLICY_DENIED');
  assert.equal(out.evidence_policy.denied[0].reason,'DENY_UNKNOWN_POLICY');
}

// Caller input cannot smuggle a permissive policy registry; only trusted third arg can.
{
  const c=CASES[0];
  const scope={member_id:'TEST_CHILD',subject:c.subject,concept_skill_target:c.target};
  const out=Runtime.derive({
    scope,
    evidence:evidence(c.subject,c.target,c.id+'-smuggle'),
    indexed_evidence_handoff:handoff(c),
    evidence_policy_registry:Overlay.REGISTRY
  },ownerVerifier);
  assert.equal(out.ok,false);
  assert.equal(out.reason,'EVIDENCE_POLICY_DENIED');
  assert.equal(out.evidence_policy.denied[0].reason,'DENY_UNKNOWN_POLICY');
}

// Explicit prohibited claim must be denied even with the trusted overlay.
{
  const c=CASES.find(x=>x.id==='REF-070');
  const scope={member_id:'TEST_CHILD',subject:c.subject,concept_skill_target:c.target};
  const out=Runtime.derive({
    scope,
    evidence:evidence(c.subject,c.target,c.id+'-blocked-claim'),
    indexed_evidence_handoff:handoff(c,['LEARNER_CONFUSION_FROM_REFERENCE'])
  },ownerVerifier,Overlay.REGISTRY);
  assert.equal(out.ok,false);
  assert.equal(out.reason,'EVIDENCE_POLICY_DENIED');
  assert.equal(out.evidence_policy.denied[0].reason,'DENY_CLAIM_BOUNDARY');
}

console.log('REFERENCE_INTAKE_V29_LEARNING_RUNTIME_E2E_PASS 6/6');
