'use strict';
const assert=require('node:assert/strict');
const V=require('./server-specialist-verifier.js');

const identity={family_id:'F1',authorized_member_ids:['CHILD_A']};
const packet=(source,id,payload={},context={})=>({
  packet_id:source+':'+id,
  source_app:source,
  context:{family_id:'F1',member_id:'CHILD_A',subject:'영어',concept_skill_target:'vocabulary',learning_target_id:'word:apple',...context},
  event:{source,event_id:id,occurred_at:'2026-10-04T00:00:00.000Z',event_type:'ATTEMPT_RESULT',payload:{
    instrument_version:'test-v1',...payload
  }}
});

(async()=>{
  let refCalls=0,reviewCalls=0;
  const verify=V.create({
    resolveReference:async s=>{
      refCalls++;
      assert(!('reference_id' in s),'client reference id must not drive server lookup');
      return {
        authority:'SERVER_OWNED_LEARNING_REFERENCE',
        reference_id:'server:word:apple',
        source_app:s.source_app,
        subject:s.subject,
        concept_skill_target:s.concept_skill_target,
        learning_target_id:s.learning_target_id,
        verifier_type:s.verifier_type,
        verifier_version:'SERVER_REF_V1',
        match_rule:'CASEFOLD_TRIM',
        expected_values:['apple']
      };
    },
    resolveHumanReview:async s=>{
      reviewCalls++;
      return {
        authority:'SERVER_OWNED_HUMAN_RUBRIC_REVIEW',
        receipt_id:'server-review:'+s.event_id,
        reference_id:'rubric:writing-v1',
        verifier_version:'RUBRIC_V1',
        target_event_id:s.event_id,
        family_id:s.family_id,
        member_id:s.member_id,
        subject:s.subject,
        concept_skill_target:s.concept_skill_target,
        outcome:1,
        verified_at:'2026-10-04T00:01:00.000Z',
        reviewer_role:'PARENT'
      };
    }
  });

  const hide=packet('hide-seek','h1',{
    verification_observation:{response_value:' Apple ',reference_id:'client:fake'}
  });
  const hv=await verify({packet:hide,identity});
  assert.equal(hv.ok,true);
  assert.equal(hv.packet.event.payload.verification_candidate.outcome,1);
  assert.equal(hv.packet.event.payload.verification_candidate.reference_id,'server:word:apple');
  assert.equal(hv.packet.event.payload.verification_candidate.basis,'DETERMINISTIC_LOCAL_MATCH');

  const wrong=packet('hide-seek','h2',{verification_observation:{response_value:'banana'}});
  const hw=await verify({packet:wrong,identity});
  assert.equal(hw.ok,true);
  assert.equal(hw.packet.event.payload.verification_candidate.outcome,0);

  const ready=packet('ready-set','r1',{
    evidence_type:'STRUCTURED_PRACTICE_EVIDENCE',
    verification_observation:{response_value:'apple'}
  });
  const rv=await verify({packet:ready,identity});
  assert.equal(rv.ok,true);
  assert.equal(rv.packet.event.payload.verification_candidate.verifier_type,'ANSWER_KEY_EXACT');

  const self=packet('ready-set','r2',{
    evidence_type:'CHILD_SELF_REPORT',
    verification_observation:{response_value:'apple'}
  });
  assert.equal((await verify({packet:self,identity})).reason,'SELF_REPORT_NOT_VERIFIABLE');

  const snap=packet('snap-pop','s1',{child_authored:true});
  const sv=await verify({packet:snap,identity});
  assert.equal(sv.ok,true);
  assert.equal(sv.packet.verification_input.verifier_type,'HUMAN_RUBRIC_BINARY');
  assert.equal(sv.packet.verification_input.reviewer_role,'PARENT');

  const noTarget=packet('hide-seek','h3',{verification_observation:{response_value:'apple'}},{learning_target_id:''});
  delete noTarget.context.learning_target_id;
  assert.equal((await verify({packet:noTarget,identity})).reason,'LEARNING_TARGET_REQUIRED');

  const noResponse=packet('hide-seek','h4',{});
  assert.equal((await verify({packet:noResponse,identity})).reason,'RAW_RESPONSE_REQUIRED');

  const wrongIdentity={family_id:'F1',authorized_member_ids:['OTHER']};
  assert.equal((await verify({packet:hide,identity:wrongIdentity})).reason,'VERIFIED_IDENTITY_SCOPE_MISMATCH');

  const badRef=V.create({
    resolveReference:async()=>({authority:'CLIENT_REFERENCE',reference_id:'x'}),
    resolveHumanReview:async()=>null
  });
  assert.equal((await badRef({packet:hide,identity})).reason,'SERVER_REFERENCE_NOT_AVAILABLE');

  const badReview=V.create({
    resolveReference:async()=>null,
    resolveHumanReview:async s=>({
      authority:'SERVER_OWNED_HUMAN_RUBRIC_REVIEW',receipt_id:'x',reference_id:'x',
      verifier_version:'v1',target_event_id:s.event_id,family_id:s.family_id,member_id:s.member_id,
      subject:s.subject,concept_skill_target:s.concept_skill_target,outcome:1,
      verified_at:'2026-10-04T00:01:00.000Z',reviewer_role:'CHILD'
    })
  });
  assert.equal((await badReview({packet:snap,identity})).reason,'AUTHORIZED_HUMAN_REVIEW_NOT_AVAILABLE');

  assert(refCalls>=3);
  assert.equal(reviewCalls,1);
  console.log('SERVER_SPECIALIST_EVIDENCE_VERIFIER_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
