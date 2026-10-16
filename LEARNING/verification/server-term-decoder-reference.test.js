'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path'),fs=require('node:fs'),crypto=require('node:crypto');
const fsp=require('node:fs/promises'),os=require('node:os');
const Server=require('./server-term-decoder-reference.js');
const Evidence=require('../transport/central-learning-http-endpoint.js');
const Term=require('../transport/term-recommendation-http-endpoint.js');
const {LocalJsonStrongStore}=require('../transport/local-json-strong-store.js');
const catalogPath=path.resolve(__dirname,'../projection/term-decoder-mined-catalog-v1.json');
const catalogBytes=fs.readFileSync(catalogPath);
const pinnedSha256=crypto.createHash('sha256').update(catalogBytes).digest('hex');
const catalog=JSON.parse(catalogBytes);
const term=catalog.terms.find(t=>t.term_id==='sci-jeungbal');
const provisional=catalog.terms.find(t=>t.term_id==='sci-hanraengjeonseon');
const TOKEN='test-real-server-term-ref-token-123456';
const principal={authenticated:true,principal_id:'PARENT_A',
 active_family_id:'FAMILY_A',families:[{family_id:'FAMILY_A',
  self_member_id:'GUARDIAN',authorized_member_ids:['CHILD_A']}]};
const verifyBearerToken=async value=>{
 if(value!==TOKEN)throw Error('BAD_TEST_BEARER');
 return principal;
};
const headers={authorization:'Bearer '+TOKEN,'content-type':'application/json'};
const packet=(eventId,termId,rawResponse,type='RETRIEVAL_ATTEMPT_RESULT',
   instrument='HIDE_TERM_DECODER_V1',mode='CORE')=>({
 packet_id:'hide-seek:'+eventId,source_app:'hide-seek',
 context:{family_id:'FAMILY_A',member_id:'CHILD_A',subject:'science',
  concept_skill_target:'vocabulary',learning_target_id:'term:'+termId},
 event:{source:'hide-seek',event_id:eventId,occurred_at:'2026-10-15T00:00:00Z',
   event_type:type,payload:{instrument_version:instrument,interaction_mode:mode,
    term_id:termId,subject:'SCIENCE',learning_target_id:'term:'+termId,
    result_type:'CORRECT',verified_outcome:1,
    verification_candidate:{outcome:1,basis:'DETERMINISTIC_LOCAL_MATCH',
     verifier_type:'RETRIEVAL_EXACT_MATCH',reference_id:'FORGED_BROWSER'},
    verification_observation:{response_value:rawResponse}}}
});
const wrap=(data,route=Evidence.ENDPOINT)=>({
 method:'POST',path:route,headers,body:JSON.stringify(data)
});
const parsed=x=>JSON.parse(x.body);
const base={catalogPath,pinnedSha256,
 resolveLearnerProfile:async()=>({school_stage:'E5'}),
 authorizeCatalogRelease:async()=>true // isolated TEST-ONLY release, NOT OPERATING OWNER approval
};
test('server reference requires independent catalog release callback and immutable source pin',()=>{
 assert.throws(()=>Server.create({...base,authorizeCatalogRelease:null}),/INDEPENDENT_CATALOG_RELEASE_AUTHORITY_REQUIRED/);
 assert.throws(()=>Server.create({...base,pinnedSha256:'0'.repeat(64)}),/REVISION_MISMATCH/);
 assert.equal(term.grade_alignment.state,'VERIFIED');
 assert.equal(provisional.grade_alignment.state,'PROVISIONAL');
 assert.equal(Server.allowedMode(packet('h1',term.term_id,term.meaning)),true);
 assert.equal(Server.allowedMode(packet('h1',term.term_id,term.meaning,'TASK_COMPLETED')),false);
 assert.equal(Server.allowedMode(packet('h1',term.term_id,term.meaning,'RETRIEVAL_ATTEMPT_RESULT','FAKE_INSTRUMENT')),false);
});

test('unapproved catalog / provisional term / cross-grade answer never becomes a verified learning receipt',async()=>{
 const noRelease=Server.create({...base,authorizeCatalogRelease:async()=>false});
 const p=packet('h1',term.term_id,term.meaning);
 assert.equal((await noRelease({packet:p,identity:{family_id:'FAMILY_A',
    authorized_member_ids:['CHILD_A']}})).ok,false);
 const verifier=Server.create(base);
 const provisionalP=packet('h2',provisional.term_id,provisional.meaning);
 assert.equal((await verifier({packet:provisionalP,identity:{family_id:'FAMILY_A',
    authorized_member_ids:['CHILD_A']}})).ok,false);
 const otherGrade=Server.create({...base,resolveLearnerProfile:async()=>({school_stage:'E4'})});
 assert.equal((await otherGrade({packet:p,identity:{family_id:'FAMILY_A',
    authorized_member_ids:['CHILD_A']}})).ok,false);
});

test('actual server verifier + central strong store reopens 2 wrong CORE answers into RECOVERY',async()=>{
 const root=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-verified-term-reference-'));
 try{
  let store=await new LocalJsonStrongStore(root).init();
  const verifier=Server.create(base);
  const evidence=Evidence.create({store,verifyBearerToken,
    verifySpecialistEvidence:verifier});
  const termInput={family_id:'FAMILY_A',member_id:'CHILD_A',
    subject:'SCIENCE',limit:2};
  const termEndpoint=store=>Term.create({
    verifyBearerToken,resolveLearnerProfile:async()=>({school_stage:'E5'}),
    resolveCurriculumTerms:async()=>({
      source_ref:catalog.source_ref,terms:[term]}),
    durableTermStore:store
  });
  const get=async store=>parsed(await termEndpoint(store).handle(wrap(termInput,Term.ENDPOINT)));
  let before=await get(store);
  assert.equal(before.term_recommendations[0].priority,'DISCOVERY');
  for(let i=1;i<=2;i++){
    const p=packet('term-wrong-'+i,term.term_id,'일부러 틀린 응답');
    const ack=parsed(await evidence.handle(wrap(p)));
    assert.equal(ack.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
    assert.equal(ack.storage_confirmed,true);
  }
  store=await new LocalJsonStrongStore(root).init();
  const after=await get(store);
  assert.equal(after.trace.evidence_count,2);
  assert.equal(after.term_recommendations[0].priority,'RECOVERY');
  assert.equal(after.term_recommendations[0].evidence_summary.wrong,2);
  assert.equal(after.term_recommendations[0].learning_pattern_plan.recovery.concept_gap,true);
  const p=packet('term-malicious',term.term_id,'틀린 답');
  p.event.payload.verification_candidate.outcome=1;
  const forged=parsed(await evidence.handle(wrap(p)));
  assert.equal(forged.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
  // Even a forged browser success is independently marked as wrong by server.
  const reopened=await new LocalJsonStrongStore(root).init();
  assert.equal((await get(reopened)).term_recommendations[0].evidence_summary.wrong,3);
  const unsigned=parsed(await evidence.handle(wrap(packet('term-preview',provisional.term_id,provisional.meaning))));
  assert.equal(unsigned.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  assert.equal((await get(await new LocalJsonStrongStore(root).init())).trace.evidence_count,3);
  assert.equal((await termEndpoint(store).handle(wrap({...termInput,member_id:'CHILD_B'},Term.ENDPOINT))).status,403);
  console.log(JSON.stringify({
   status:'REAL_REUSABLE_SERVER_TERM_ANSWER_KEY_VERIFIER_DURABLE_RECOVERY_PASS',
   grade:'E5',term:term.term,verified_wrong:3,
   provisional_term_did_not_promote:true,
   client_fake_right_could_not_promote:true,
   independent_release_test_fixture_only:true
  }));
 }finally{await fsp.rm(root,{recursive:true,force:true});}
});
