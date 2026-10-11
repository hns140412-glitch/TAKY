'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os');
const path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Evidence=require('./central-learning-http-endpoint.js');
const Decision=require('./central-learning-decision-http-endpoint.js');

const token='play-camp-parent-token-0001';
const principal={
  authenticated:true,
  principal_id:'PARENT_A',
  families:[{
    family_id:'F1',
    self_member_id:'PARENT_A',
    authorized_member_ids:['CHILD_A']
  }]
};
const auth=async value=>{
  if(value!==token)throw Error('INVALID_TOKEN');
  return principal;
};
const headers={Authorization:'Bearer '+token,'Content-Type':'application/json'};
const parse=r=>JSON.parse(r.body);

(async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'play-camp-central-learning-'));
  try{
    const store=await new LocalJsonStrongStore(root).init();
    const evidenceEndpoint=Evidence.create({store,verifyBearerToken:auth});
    const decisionEndpoint=Decision.create({store,verifyBearerToken:auth});

    const packet={
      packet_id:'play-camp:e2e-bond-1',
      source_app:'play-camp',
      context:{
        family_id:'F1',
        member_id:'CHILD_A',
        subject:'수학',
        concept_skill_target:'number_bond_10',
        learning_target_id:'number-bond:bond-7-3'
      },
      event:{
        source:'play-camp',
        event_id:'play-camp:e2e-bond-1',
        occurred_at:'2026-10-08T01:00:00.000Z',
        event_type:'PLAY_ACTIVITY_OBSERVATION',
        payload:{
          subject:'수학',
          concept_skill_target:'number_bond_10',
          learning_target_id:'number-bond:bond-7-3',
          evidence_type:'PLAY_ACTIVITY_OBSERVATION',
          activity_id:'math-bond-10',
          concept_ids:['math.quantity-10','math.number-bond'],
          instrumentVersion:'PLAY_CAMP_ACTIVITY_V1',
          interactionMode:'DIRECT_MANIPULATION',
          assisted:false,
          attemptCount:3,
          loop_step:'CONNECT',
          completion_state:'TEN_BOND_COMPLETED',
          interaction_count:3,
          response_value:3
        }
      }
    };

    const evidence=await evidenceEndpoint.handle({
      method:'POST',path:Evidence.ENDPOINT,headers,body:JSON.stringify(packet)
    });
    const ack=parse(evidence);
    assert.equal(evidence.status,200,JSON.stringify(ack));
    assert.equal(ack.ok,true);
    assert.equal(ack.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
    assert.equal(ack.storage_confirmed,true);
    assert.equal(ack.packet_id,packet.packet_id);
    assert.equal(ack.event_id,packet.event.event_id);

    const decisionRequest=()=>decisionEndpoint.handle({
      method:'POST',path:Decision.ENDPOINT,headers,
      body:JSON.stringify({
        family_id:'F1',
        member_id:'CHILD_A',
        subject:'수학',
        concept_skill_target:'number_bond_10'
      })
    });

    const decision=await decisionRequest();
    const body=parse(decision);
    assert.equal(decision.status,200,JSON.stringify(body));
    assert.equal(body.ok,true);
    assert.equal(body.authenticated_server_response,true);
    assert.equal(body.runtime_result.authority,'TAKY_LEARNING_ENGINE_CORE');
    assert.equal(body.runtime_result.trace.verified_evidence_count,0);
    assert.equal(body.runtime_result.trace.observation_review_evidence_count,1);
    assert.equal(body.runtime_result.decision.execution_status,'PEDAGOGICAL_ACTION_AVAILABLE');
    assert(body.runtime_result.decision.pedagogical_actions.some(
      x=>x.intent==='CONTINUE_OBSERVATION'
    ));
    assert(!body.runtime_result.decision.pedagogical_actions.some(
      x=>x.intent==='OFFER_ADJACENT_VARIATION'
    ));
    assert(body.runtime_result.decision.advisories.some(
      x=>x.code==='UNVERIFIED_ACTIVITY_OBSERVATION'
    ));

    const second=structuredClone(packet);
    second.packet_id='play-camp:e2e-bond-2';
    second.context.learning_target_id='number-bond:bond-6-4';
    second.event.event_id='play-camp:e2e-bond-2';
    second.event.occurred_at='2026-10-08T01:05:00.000Z';
    second.event.payload.learning_target_id='number-bond:bond-6-4';
    second.event.payload.attemptCount=1;
    const secondEvidence=await evidenceEndpoint.handle({
      method:'POST',path:Evidence.ENDPOINT,headers,body:JSON.stringify(second)
    });
    assert.equal(secondEvidence.status,200,secondEvidence.body);

    const repeatedDecision=await decisionRequest();
    const repeated=parse(repeatedDecision);
    assert.equal(repeated.runtime_result.trace.verified_evidence_count,0);
    assert.equal(repeated.runtime_result.trace.observation_review_evidence_count,2);
    assert(repeated.runtime_result.decision.pedagogical_actions.some(
      x=>x.intent==='CONTINUE_OBSERVATION'
    ));
    assert(!repeated.runtime_result.decision.pedagogical_actions.some(
      x=>x.intent==='OFFER_ADJACENT_VARIATION'
    ));
    assert.equal(repeated.runtime_result.decision.consumer_contract.planner,'OWNS_DATED_ALLOCATION');
    assert.equal(repeated.runtime_result.decision.authority,'LEARNING_DECISION_INTENT_ONLY');
    assert(!repeatedDecision.body.includes('planner_date'));
    assert(!repeatedDecision.body.includes('schedule_date'));

    console.log('PLAY_CAMP_CENTRAL_LEARNING_E2E_PASS: Play Camp observation remains advisory-only CONTINUE_OBSERVATION; zero mastery and zero schedule authority');
  }finally{
    await fs.rm(root,{recursive:true,force:true});
  }
})().catch(error=>{console.error(error);process.exitCode=1});
