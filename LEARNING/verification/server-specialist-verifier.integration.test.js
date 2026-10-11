'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('../transport/local-json-strong-store.js');
const Evidence=require('../transport/central-learning-http-endpoint.js');
const ServerVerifier=require('./server-specialist-verifier.js');

const principal={
  authenticated:true,principal_id:'PARENT_A',identity_provider:'TEST_TRUSTED_TOKEN_VERIFIER',
  families:[{family_id:'F1',self_member_id:'PARENT_A',authorized_member_ids:['CHILD_A']}]
};
const request=body=>({
  method:'POST',path:'/api/learning/evidence',
  headers:{Authorization:'Bearer validated-bearer-token-001','content-type':'application/json'},
  body:JSON.stringify(body)
});
const parse=r=>JSON.parse(r.body);

(async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-specialist-verifier-e2e-'));
  try{
    const store=await new LocalJsonStrongStore(root).init();
    const verifier=ServerVerifier.create({
      resolveReference:async s=>({
        authority:'SERVER_OWNED_LEARNING_REFERENCE',
        reference_id:'server-ref:'+s.learning_target_id,
        source_app:s.source_app,subject:s.subject,concept_skill_target:s.concept_skill_target,
        learning_target_id:s.learning_target_id,verifier_type:s.verifier_type,
        verifier_version:'SERVER_REF_V1',match_rule:'CASEFOLD_TRIM',expected_values:['apple']
      }),
      resolveHumanReview:async s=>({
        authority:'SERVER_OWNED_HUMAN_RUBRIC_REVIEW',
        receipt_id:'server-review:'+s.event_id,
        reference_id:'rubric:writing-v1',verifier_version:'RUBRIC_V1',
        target_event_id:s.event_id,family_id:s.family_id,member_id:s.member_id,
        subject:s.subject,concept_skill_target:s.concept_skill_target,
        outcome:1,verified_at:'2026-10-04T00:03:00.000Z',reviewer_role:'PARENT'
      })
    });
    const endpoint=Evidence.create({
      store,
      verifyBearerToken:async token=>{
        assert.equal(token,'validated-bearer-token-001');
        return principal;
      },
      verifySpecialistEvidence:verifier
    });

    const hide={
      packet_id:'hide-seek:h-real-1',source_app:'hide-seek',
      context:{family_id:'F1',member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary',learning_target_id:'word:apple'},
      event:{source:'hide-seek',event_id:'h-real-1',occurred_at:'2026-10-04T00:00:00.000Z',
        event_type:'RETRIEVAL_ATTEMPT_RESULT',payload:{
          instrument_version:'HIDE_CODE_RED_V1',
          verification_observation:{response_value:'APPLE',reference_id:'CLIENT_FAKE'}
        }}
    };
    const h=await endpoint.handle(request(hide));
    assert.equal(h.status,200,h.body);
    assert.equal(parse(h).acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');

    const ready={
      packet_id:'ready-set:r-real-1',source_app:'ready-set',
      context:{family_id:'F1',member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary',learning_target_id:'word:apple'},
      event:{source:'ready-set',event_id:'r-real-1',occurred_at:'2026-10-04T00:01:00.000Z',
        event_type:'STRUCTURED_PRACTICE_RESULT',payload:{
          instrument_version:'READY_PRACTICE_V1',evidence_type:'STRUCTURED_PRACTICE_EVIDENCE',
          verification_observation:{response_value:'banana'}
        }}
    };
    const r=await endpoint.handle(request(ready));
    assert.equal(r.status,200,r.body);
    assert.equal(parse(r).acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');

    const snap={
      packet_id:'snap-pop:s-real-1',source_app:'snap-pop',
      context:{family_id:'F1',member_id:'CHILD_A',subject:'영어',concept_skill_target:'writing',learning_target_id:'writing:1'},
      event:{source:'snap-pop',event_id:'s-real-1',occurred_at:'2026-10-04T00:02:00.000Z',
        event_type:'TASK_COMPLETED',payload:{instrument_version:'SNAP_WRITING_V1',child_authored:true}}
    };
    const s=await endpoint.handle(request(snap));
    assert.equal(s.status,200,s.body);
    assert.equal(parse(s).acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');

    const saved=await store.getWithMetadata('families/F1/members/CHILD_A/learning-engine/state-v1',
      {type:'json',consistency:'strong'});
    const receipts=Object.values(saved.data.scope_receipts||{});
    assert(receipts.length>=2,'verified scope receipts required');
    const events=receipts.flatMap(x=>x.canonical_evidence||[]);
    assert(events.some(x=>x.event_id==='h-real-1'&&x.verified_outcome===1));
    assert(events.some(x=>x.event_id==='r-real-1'&&x.verified_outcome===0));
    assert(events.some(x=>x.event_id==='s-real-1'&&x.verified_outcome===1));

    console.log('SERVER_SPECIALIST_VERIFIER_CENTRAL_E2E_PASS');
  }finally{
    await fs.rm(root,{recursive:true,force:true});
  }
})().catch(e=>{console.error(e);process.exit(1)});
