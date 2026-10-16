'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const Authority=require('./independent-signed-forming-authority');
const Pipeline=require('./index-forming-learning-consumption');
const Stage=require('../projection/approved-learning-stage');
const Selector=require('../pedagogy/grade-aware-term-selector');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ruleVersion=require('../data/learning-reference-pattern-projection-rules-v1.json').version;

function verifiedCandidate(){
 const id='REF-081';
 const candidate={source_id:id,source_ref:'INDEX:'+id,
  source_family:'EDUCATION_REFERENCE',source_type:'DOCUMENT',
  authority_class:'REFERENCE_ONLY',detail_anchor:'RAW:LINE:1',
  index_version:'TEST_ONLY_INDEX_OWNER',review_evidence_refs:['TEST_ONLY_OWNER_ATTESTATION'],
  provenance:['FIXTURE_INDEX:'+id],
  relations:[{type:'CONCEPT_RELATION',target:'WEATHER_FRONT',anchor:'LINE:1'}]};
 const input={query_context:{consumer_app:'HIDE_SEEK',function_id:'TEST_FORMING_SOURCE',
  requested_behavior:'SCOPED_TERM_REVIEW'},candidates:[candidate]};
 const verifier=()=>({issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
  domain_use_authorized:true,source_id:candidate.source_id,source_ref:candidate.source_ref,
  source_family:candidate.source_family,source_type:candidate.source_type,
  authority_class:candidate.authority_class,detail_anchor:candidate.detail_anchor,
  index_version:candidate.index_version,review_evidence_refs:candidate.review_evidence_refs,
  provenance:candidate.provenance,relations:candidate.relations});
 const prepared=Pipeline.prepare(input,verifier,{owner_namespace:'LEARNING_OS',
  forming_kind:'CONTENT_FORMING',target_consumer:'HIDE_SEEK',ruleset_revision:ruleVersion});
 assert.equal(prepared.ok,true);
 return prepared;
}
function prepareFixture(){
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'taky-signature-test-'));
 const authorityRoot=path.join(tmp,'approvals');
 const evidenceRoot=path.join(tmp,'evidence');
 fs.mkdirSync(authorityRoot);fs.mkdirSync(evidenceRoot);
 const {privateKey,publicKey}=crypto.generateKeyPairSync('ed25519');
 const keyPath=path.join(tmp,'owner-trust-public.pem');
 fs.writeFileSync(keyPath,publicKey.export({type:'spki',format:'pem'}));
 const expectedSpkiSha256=sha(publicKey.export({type:'spki',format:'der'}));
 const opts=Authority.fromTrustedHostSettings({publicKeyPath:keyPath,expectedSpkiSha256});
 assert.equal(opts.configured,true);
 const prepared=verifiedCandidate();
 const proof=Buffer.from('TEST FIXTURE: explicit independent approval simulation, NOT PRODUCTION');
 fs.writeFileSync(path.join(evidenceRoot,'scope-evidence.txt'),proof);
 const receipt={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',
  artifact_id:prepared.formed.artifact_id,artifact_revision:prepared.formed.artifact_revision,
  owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',
  approved_by:'TEST_ONLY_ED25519_KEY',approved_at:'2026-10-14T21:00:00Z',
  evidence_ref:'scope-evidence.txt',evidence_sha256:sha(proof)};
 receipt.approval_signature_ed25519=crypto.sign(null,Authority.message(receipt),privateKey).toString('base64');
 const approvalRecordPath=path.join(authorityRoot,'approved-test.json');
 fs.writeFileSync(approvalRecordPath,JSON.stringify(receipt));
 return {tmp,authorityRoot,evidenceRoot,privateKey,keyPath,expectedSpkiSha256,
  opts:{authorityRoot,evidenceRoot,independentAuthorityCheck:opts.independentAuthorityCheck},
  prepared,receipt,approvalRecordPath};
}

test('unconfigured owner trust root cannot authorize any FORMING adoption',()=>{
 const no=Authority.fromTrustedHostSettings();
 assert.equal(no.configured,false);
 assert.equal(no.reason,'INDEPENDENT_AUTHORITY_TRUST_NOT_CONFIGURED');
 assert.equal(no.independentAuthorityCheck({receipt:{decision:'APPROVED'}}),false);
});

test('real Ed25519 trust pin gates local approved source into scoped learning selection',()=>{
 const f=prepareFixture();
 const stageId='taky-ed25519-fixture-'+crypto.randomBytes(7).toString('hex');
 try{
  assert.equal(Authority.checkPinnedApproval(f.receipt,{
   publicKeyPem:fs.readFileSync(f.keyPath,'utf8'),
   expectedSpkiSha256:f.expectedSpkiSha256}),true);
  const out=Stage.stageApproved({prepared:f.prepared,
    approvalRecordPath:f.approvalRecordPath,authorityOptions:f.opts,stageId});
  assert.equal(out.ok,true);
  assert.equal(out.stage,'FORMING_LEARNING_STAGED_LOCAL_ONLY');
  assert.equal(out.operating_current_updated,false);
  assert.equal(out.release_approved,false);
  const reread=Stage.loadStaged(stageId);
  assert.equal(reread.ok,true);
  assert.deepEqual(reread.manifest.source_ids,['REF-081']);
  const decision=Selector.select({
   learner_profile:{schoolStage:'E5'},subject:'SCIENCE',consumer_app:'HIDE_SEEK',
   candidate_terms:[{
    id:'weather-front',subject:'SCIENCE',term:'한랭전선',hanja:'寒冷前線',
    meaning:'차가운 공기가 들어와 형성되는 전선',gradeBand:'5-6',
    source_ref:'CURR:SCIENCE:FRONT',grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:FRONT'},
    components:[{text:'寒',meaning:'차다'}],concept:{relations:['기단 관계'],summary:'찬 공기'},
    unit_tags:['날씨']}],
   term_evidence:[{learning_target_id:'weather-front',result_type:'WRONG',interaction_mode:'CORE'},
     {learning_target_id:'weather-front',result_type:'WRONG',interaction_mode:'LINK'}]
  },{mode:'BOUND_FORMING_PREVIEW_ONLY',registry:reread.registry});
  assert.equal(decision.ok,true);
  assert.ok(decision.recommendations[0].learning_pattern_plan.pattern_ids.includes('P_ERROR_TO_CONCEPT_GAP'));
  assert.equal(decision.preview_only,true);
  assert.equal(decision.learning_consumed,false);
  console.log(JSON.stringify({status:'SIGNED_FORMING_TO_LEARNING_SELECTOR_E2E_PASS',
   fixture_only:true,staged_source_ids:reread.manifest.source_ids,
   pattern_ids:decision.recommendations[0].learning_pattern_plan.pattern_ids,
   CURRENT_modified:false,release_approved:false,real_app_consumption:false}));
 }finally{
  fs.rmSync(path.join(Stage.STAGING_ROOT,stageId),{recursive:true,force:true});
  fs.rmSync(f.tmp,{recursive:true,force:true});
 }
});

test('forged signature, wrong trust pin, re-scoped evidence and missing pin fail closed',()=>{
 const f=prepareFixture();
 try{
  const orig=fs.readFileSync(f.approvalRecordPath,'utf8');
  assert.equal(Authority.fromTrustedHostSettings({publicKeyPath:f.keyPath,
   expectedSpkiSha256:'0'.repeat(64)}).configured,false);
  const stageId='taky-ed25519-denied-'+crypto.randomBytes(7).toString('hex');
  let no=Stage.stageApproved({prepared:f.prepared,
    approvalRecordPath:f.approvalRecordPath,
    authorityOptions:{...f.opts,independentAuthorityCheck:()=>false},
    stageId});
  assert.equal(no.ok,false);
  assert.equal(fs.existsSync(path.join(Stage.STAGING_ROOT,stageId)),false);
  const forged={...f.receipt,approval_signature_ed25519:Buffer.alloc(64).toString('base64')};
  fs.writeFileSync(f.approvalRecordPath,JSON.stringify(forged));
  assert.equal(Stage.stageApproved({prepared:f.prepared,
   approvalRecordPath:f.approvalRecordPath,authorityOptions:f.opts,stageId}).ok,false);
  const moved={...f.receipt,target_consumer:'READY'};
  fs.writeFileSync(f.approvalRecordPath,JSON.stringify(moved));
  assert.equal(Stage.stageApproved({prepared:f.prepared,
   approvalRecordPath:f.approvalRecordPath,authorityOptions:f.opts,stageId}).ok,false);
  fs.writeFileSync(f.approvalRecordPath,orig);
  fs.writeFileSync(path.join(f.evidenceRoot,'scope-evidence.txt'),'tampered bytes');
  assert.equal(Stage.stageApproved({prepared:f.prepared,
   approvalRecordPath:f.approvalRecordPath,authorityOptions:f.opts,stageId}).ok,false);
  assert.equal(fs.existsSync(path.join(Stage.STAGING_ROOT,stageId)),false);
 }finally{
  fs.rmSync(f.tmp,{recursive:true,force:true});
 }
});
