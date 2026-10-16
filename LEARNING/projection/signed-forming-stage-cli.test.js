'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const Intake=require('../intake/index-forming-learning-consumption');
const Sign=require('../intake/independent-signed-forming-authority');
const Cli=require('./signed-forming-stage-cli');
const Stage=require('./approved-learning-stage');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ruleVersion=require('../data/learning-reference-pattern-projection-rules-v1.json').version;

test('local production entry has no authority trust fallback',()=>{
 const out=Cli.run({sourcePacketPath:null,approvalRecordPath:null,hostEnv:{}});
 assert.equal(out.ok,false);
 assert.equal(out.status,'HOLD_INDEPENDENT_APPROVAL_TRUST_NOT_CONFIGURED');
 assert.equal(out.learning_consumed,false);
 assert.equal(out.app_released,false);
});

test('trusted signed stage is idempotent, revalidates approval on replay, cannot publish',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'taky-signed-stage-test-'));
 const approvals=path.join(root,'approvals'),evidence=path.join(root,'evidence');
 fs.mkdirSync(approvals);fs.mkdirSync(evidence);
 const pair=crypto.generateKeyPairSync('ed25519');
 const pub=pair.publicKey.export({type:'spki',format:'pem'});
 const keyPath=path.join(root,'trust-key.pem');fs.writeFileSync(keyPath,pub);
 const pin=sha(pair.publicKey.export({type:'spki',format:'der'}));
 const c={source_id:'REF-081',source_ref:'INDEX:REF-081',source_family:'EDUCATION_REFERENCE',
  source_type:'DOCUMENT',authority_class:'REFERENCE_ONLY',
  detail_anchor:'RAW:LINE:1',index_version:'FIXTURE_OWNER_V1',
  review_evidence_refs:['FIXTURE_INDEPENDENT_REVIEW'],
  provenance:['EXISTING_REF:REF-081'],
  relations:[{type:'CONCEPT_RELATION',target:'WEATHER_FRONT',anchor:'LINE:1'}]};
 const prep=Intake.prepare({
  query_context:{consumer_app:'HIDE_SEEK',function_id:'TEST_FORMING_SOURCE',
    requested_behavior:'SCOPED_TERM_REVIEW'},candidates:[c]
 },()=>({issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
  domain_use_authorized:true,...c}),{
  owner_namespace:'LEARNING_OS',forming_kind:'CONTENT_FORMING',
  target_consumer:'HIDE_SEEK',ruleset_revision:ruleVersion
 });
 assert.equal(prep.ok,true);
 const proof=Buffer.from('TEST ONLY -- NOT AN AUTHENTIC FORMING APPROVAL');
 fs.writeFileSync(path.join(evidence,'approval-evidence.txt'),proof);
 const signed={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',
  artifact_id:prep.formed.artifact_id,artifact_revision:prep.formed.artifact_revision,
  owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',
  approved_by:'SIGNED_TEST_FIXTURE',approved_at:'2026-10-14T22:00:00Z',
  evidence_ref:'approval-evidence.txt',evidence_sha256:sha(proof)};
 signed.approval_signature_ed25519=crypto.sign(null,Sign.message(signed),
    pair.privateKey).toString('base64');
 const approvalRecordPath=path.join(approvals,'approval.json');
 fs.writeFileSync(approvalRecordPath,JSON.stringify(signed));
 const sourcePacketPath=path.join(Cli.EVIDENCE,
   '.temporary-test-signed-stage-'+crypto.randomBytes(8).toString('hex')+'.json');
 fs.writeFileSync(sourcePacketPath,JSON.stringify(prep));
 const env={TAKY_FORMING_TRUST_PUBLIC_KEY_FILE:keyPath,
  TAKY_FORMING_TRUST_PINNED_SPKI_SHA256:pin,
  TAKY_FORMING_APPROVAL_ROOT:approvals,
  TAKY_FORMING_EVIDENCE_ROOT:evidence};
 let stageId=null;
 try{
  const first=Cli.run({sourcePacketPath,approvalRecordPath,hostEnv:env});
  assert.equal(first.ok,true);
  assert.equal(first.status,'VERIFIED_SIGNED_STAGE_WRITTEN_LOCAL_ONLY');
  stageId=first.stage_id;
  assert.deepEqual(first.approved_source_ids,['REF-081']);
  assert.equal(first.learning_consumed,false);
  assert.equal(Stage.loadStaged(stageId).manifest.operational,false);
  const again=Cli.run({sourcePacketPath,approvalRecordPath,hostEnv:env});
  assert.equal(again.ok,true);
  assert.equal(again.new_stage_created,false);
  const revoked={...signed,approved_by:'TAMPERED_OWNER'};
  fs.writeFileSync(approvalRecordPath,JSON.stringify(revoked));
  const hold=Cli.run({sourcePacketPath,approvalRecordPath,hostEnv:env});
  assert.equal(hold.ok,false);
  assert.equal(hold.status,'HOLD_INDEPENDENT_SIGNED_APPROVAL_REJECTED');
  assert.equal(hold.learning_consumed,false);
  assert.equal(Stage.loadStaged(stageId).manifest.operational,false);
  console.log(JSON.stringify({status:'PINNED_SIGNED_FORMING_STAGE_REPLAY_PASS',
    fixture_only:true,local_stage_created:true,
    deterministic_replay_new_stage:false,
    tampered_approval_replay_denied:true,
    app_published:false,CURRENT_changed:false}));
 }finally{
  if(stageId)fs.rmSync(path.join(Stage.STAGING_ROOT,stageId),{recursive:true,force:true});
  fs.rmSync(sourcePacketPath,{force:true});
  fs.rmSync(root,{recursive:true,force:true});
 }
});
