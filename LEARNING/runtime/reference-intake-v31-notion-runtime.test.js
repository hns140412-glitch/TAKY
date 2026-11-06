'use strict';

const assert=require('node:assert/strict');
const Runtime=require('./learning-engine-runtime.js');
const Overlay=require('../policy/reference-intake-v31-notion-policy.js');

const ROWS={
  'REF-081':{
    source_family:'INDEPENDENT_EDUCATION_CREATOR',
    authority_class:'REFERENCE_ONLY_UNTIL_CURRICULUM_AND_PEDAGOGY_VERIFIED',
    provenance:['REFERENCE_MINING_INDEX','REF-081']
  },
  'REF-084':{
    source_family:'OFFICIAL_PUBLIC_EDUCATION_PROVIDER',
    authority_class:'OFFICIAL_WITHIN_EBS_OWN_PUBLISHED_FACTS__NO_CROSS_DOMAIN_AUTHORITY',
    provenance:['REFERENCE_MINING_INDEX','REF-084']
  },
  'REF-085':{
    source_family:'INDEPENDENT_EDUCATION_CONTENT_CREATOR',
    authority_class:'REFERENCE_ONLY_UNTIL_MATH_CURRICULUM_AND_CONTENT_ACCURACY_VERIFIED',
    provenance:['REFERENCE_MINING_INDEX','REF-085']
  }
};

function ownerVerifier(sourceId,sourceRef){
  const row=ROWS[sourceId];
  if(!row||sourceRef!=='INDEX:'+sourceId)return null;
  return {
    ...row,source_type:'NOTION_REVIEWED_REFERENCE',detail_anchor:null,
    issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',domain_use_authorized:true,
    source_id:sourceId,source_ref:sourceRef,index_version:'V31-NOTION-DELTA',
    review_evidence_refs:[
      'C2S/DATA_INDEX_V31_NOTION_INDEX_OWNER_RECEIPT_2026-10-04.json',
      'C2S/NOTION_REFERENCE_REVIEW_E2E_2026-10-04.json'
    ]
  };
}

function evidence(subject,target,id){
  return [{
    event_id:'v31-notion-'+id,
    observed_at:'2026-10-04T00:20:00.000+09:00',
    member_id:'TEST_CHILD',subject,concept_skill_target:target,
    evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
    source_app:'reference-v31-notion-test',instrument_version:'v31-notion-test-1',
    assisted:false,verified_outcome:1,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-'+id}
  }];
}

const CASES=[
  {id:'REF-081',subject:'수학',target:'CONCEPT_GAP_REVIEW',
   function_id:'LE-RV31-CONCEPT-GAP',consumer_app:'HIDE_SEEK',behavior:'CONCEPT_GAP_REFERENCE_SUPPORT'},
  {id:'REF-084',subject:'학습자료',target:'OFFICIAL_RESOURCE_DISCOVERY',
   function_id:'LE-RV31-EBS-DISCOVERY',consumer_app:'READY_SET',behavior:'OFFICIAL_RESOURCE_DISCOVERY'},
  {id:'REF-085',subject:'수학',target:'MATH_CONCEPT_RELATION',
   function_id:'LE-RV31-MATH-RELATION',consumer_app:'HIDE_SEEK',behavior:'MATH_CONCEPT_RELATION_REFERENCE'}
];

function handoff(c,claims=[]){
  const row=ROWS[c.id];
  return {
    query_context:{function_id:c.function_id,consumer_app:c.consumer_app,requested_behavior:c.behavior,requested_claims:claims},
    candidates:[{
      source_id:c.id,source_ref:'INDEX:'+c.id,source_family:row.source_family,
      source_type:'NOTION_REVIEWED_REFERENCE',authority_class:row.authority_class,
      detail_anchor:null,provenance:[...row.provenance],relations:[]
    }]
  };
}

for(const c of CASES){
  const scope={member_id:'TEST_CHILD',subject:c.subject,concept_skill_target:c.target};
  const ev=evidence(c.subject,c.target,c.id);
  const baseline=Runtime.derive({scope,evidence:ev});
  assert.equal(baseline.ok,true,c.id+' baseline pass');
  const out=Runtime.derive({scope,evidence:ev,indexed_evidence_handoff:handoff(c)},ownerVerifier,Overlay.REGISTRY);
  assert.equal(out.ok,true,c.id+' runtime pass');
  assert.deepEqual(out.trace.source_refs,['INDEX:'+c.id]);
  assert.equal(out.evidence_policy.results[0].decision,'ALLOW_CONDITIONAL');
  assert.deepEqual(out.learner_state,baseline.learner_state,c.id+' reference metadata must not mutate learner state');
  assert.equal(out.indexed_evidence.invariant,'INDEX_RETRIEVAL_METADATA_IS_CONTEXT_NOT_LEARNER_PERFORMANCE');
  assert.equal(out.cannot_influence.includes('SCHEDULE_DATE'),true);
  assert.equal(out.cannot_influence.includes('PLANNER_DATE'),true);
  assert.equal(Runtime.validate(out).ok,true);
}

{
  const c=CASES.find(x=>x.id==='REF-084');
  const scope={member_id:'TEST_CHILD',subject:c.subject,concept_skill_target:c.target};
  const out=Runtime.derive({
    scope,evidence:evidence(c.subject,c.target,c.id+'-blocked'),
    indexed_evidence_handoff:handoff(c,['PORTAL_PAGE_IS_LEARNING_EVIDENCE'])
  },ownerVerifier,Overlay.REGISTRY);
  assert.equal(out.ok,false);
  assert.equal(out.reason,'EVIDENCE_POLICY_DENIED');
  assert.equal(out.evidence_policy.denied[0].reason,'DENY_CLAIM_BOUNDARY');
}

console.log('REFERENCE_INTAKE_V31_NOTION_LEARNING_RUNTIME_E2E_PASS 3/3');
