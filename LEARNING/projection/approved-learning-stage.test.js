'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),
 path=require('node:path'),crypto=require('node:crypto');
const Pipeline=require('../intake/index-forming-learning-consumption');
const Stage=require('./approved-learning-stage');
const Selector=require('../pedagogy/grade-aware-term-selector');
const repo=path.resolve(__dirname,'..','..');
const registryFile=path.join(repo,'LEARNING','data','mining-learning-pattern-registry-v1.json');
const currentFile=path.join(repo,'CURRENT','DATA','LEARNING_REFERENCE_PATTERN_PROJECTION_CURRENT.json');
const refreshFile=path.join(repo,'CURRENT','DATA','MINING_LEARNING_REFRESH_CURRENT.json');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const files=[registryFile,currentFile,refreshFile];
const before=files.map(file=>({file,digest:sha(fs.readFileSync(file)),mtime:fs.statSync(file).mtimeMs}));
const fixtureRoot=fs.mkdtempSync(path.join(os.tmpdir(),'taky-authority-staging-fixture-'));
const approvals=path.join(fixtureRoot,'approvals'),evidence=path.join(fixtureRoot,'evidence');
fs.mkdirSync(approvals);fs.mkdirSync(evidence);
const proof=Buffer.from('THIS IS AN INDEPENDENT APPROVAL TEST FIXTURE, NOT PROD');
fs.writeFileSync(path.join(evidence,'proof.txt'),proof);
const ruleVersion=require('../data/learning-reference-pattern-projection-rules-v1.json').version;
const authorized={authorityRoot:approvals,evidenceRoot:evidence,
 independentAuthorityCheck:({receipt,evidencePath})=>
  receipt.approved_by==='FIXTURE_ONLY_NOT_PRODUCTION'
  &&evidencePath===path.join(evidence,'proof.txt')};
let published=[];
function makeCandidate(id) {
 const candidate={source_id:id,source_ref:'INDEX:'+id,
  source_family:'EDUCATION_REFERENCE',source_type:'DOCUMENT',
  authority_class:'REFERENCE_ONLY',detail_anchor:'RAW:LINE:1',
  index_version:'TEST_INDEX_1',review_evidence_refs:['TEST_OWNER_PROOF'],
  provenance:['ORIGINAL_LEDG_REF:'+id],
  relations:[{type:'CONCEPT_RELATION',target:'WEATHER_FRONT',anchor:'LINE:1'}]};
 const input={query_context:{consumer_app:'HIDE_SEEK',function_id:'TEST_FORMING_SOURCE',
  requested_behavior:'SCOPED_TERM_REVIEW'},candidates:[candidate]};
 const owner=()=>({issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
  domain_use_authorized:true,source_id:candidate.source_id,source_ref:candidate.source_ref,
  source_family:candidate.source_family,source_type:candidate.source_type,
  authority_class:candidate.authority_class,detail_anchor:candidate.detail_anchor,
  index_version:candidate.index_version,review_evidence_refs:candidate.review_evidence_refs,
  provenance:candidate.provenance,relations:candidate.relations});
 const prepared=Pipeline.prepare(input,owner,{owner_namespace:'LEARNING_OS',
  forming_kind:'CONTENT_FORMING',target_consumer:'HIDE_SEEK',
  ruleset_revision:ruleVersion});
 assert.equal(prepared.ok,true);
 const receipt={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',
  artifact_id:prepared.formed.artifact_id,
  artifact_revision:prepared.formed.artifact_revision,
  owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',
  approved_by:'FIXTURE_ONLY_NOT_PRODUCTION',approved_at:'2026-10-14T00:00:00Z',
  evidence_ref:'proof.txt',evidence_sha256:sha(proof)};
 const approvalRecordPath=path.join(approvals,id+'.json');
 fs.writeFileSync(approvalRecordPath,JSON.stringify(receipt));
 return {prepared,approvalRecordPath,authorityOptions:authorized};
}
const term={id:'weather-front',subject:'SCIENCE',term:'한랭전선',
 hanja:'寒冷前線',meaning:'찬 공기가 움직여 형성하는 전선',
 gradeBand:'5-6',source_ref:'CURR:SCIENCE:FRONT',
 grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:FRONT'},
 components:[{text:'寒',meaning:'차다'}],
 concept:{relations:['기단 관계'],summary:'찬 공기'},
 unit_tags:['날씨']};
const learningInput={learner_profile:{schoolStage:'E5'},subject:'SCIENCE',
 consumer_app:'HIDE_SEEK',candidate_terms:[term],
 term_evidence:[{learning_target_id:'weather-front',result_type:'WRONG',interaction_mode:'CORE'},
  {learning_target_id:'weather-front',result_type:'WRONG',interaction_mode:'LINK'}]};
try{
 const idBase='taky-stage-test-'+crypto.randomBytes(5).toString('hex');
 const cases=[{id:'REF-081',stageId:idBase+'-a'},
              {id:'REF-085',stageId:idBase+'-b'}];
 const decisions=[];
 for(const entry of cases){
  const proposal=makeCandidate(entry.id);
  const status=Stage.stageApproved({...proposal,stageId:entry.stageId});
  published.push(entry.stageId);
  assert.equal(status.ok,true);
  assert.equal(status.operating_current_updated,false);
  assert.equal(status.release_approved,false);
  const retrieved=Stage.loadStaged(entry.stageId);
  assert.equal(retrieved.ok,true);
  assert.equal(retrieved.manifest.state,'LOCAL_STAGE_ONLY_NOT_CURRENT_NOT_DEPLOYED');
  assert.deepEqual(retrieved.manifest.source_ids,[entry.id]);
  assert.equal(retrieved.registry.sources.length,1);
  const decision=Selector.select(learningInput,{
   mode:'BOUND_FORMING_PREVIEW_ONLY',registry:retrieved.registry});
  assert.equal(decision.ok,true);
  assert.equal(decision.preview_only,true);
  assert.equal(decision.learning_consumed,false);
  decisions.push(decision.recommendations[0].learning_pattern_plan);
  assert.throws(()=>Stage.stageApproved({...proposal,stageId:entry.stageId}),
   /STAGE_ALREADY_EXISTS/);
  assert.equal(Stage.stageApproved({...proposal,
   authorityOptions:{...authorized,independentAuthorityCheck:null},
   stageId:idBase+'-denied'}).ok,false);
  assert.equal(fs.existsSync(path.join(Stage.STAGING_ROOT,idBase+'-denied')),false);
 }
 assert.ok(decisions[0].pattern_ids.includes('P_ERROR_TO_CONCEPT_GAP'));
 assert.ok(!decisions[1].pattern_ids.includes('P_ERROR_TO_CONCEPT_GAP'));
 assert.ok(decisions[1].pattern_ids.includes('P_CONCEPT_GRAPH'));
 const firstDir=path.join(Stage.STAGING_ROOT,published[0]);
 const regPath=path.join(firstDir,'registry.json');
 const pristine=fs.readFileSync(regPath);
 fs.writeFileSync(regPath,Buffer.concat([pristine,Buffer.from('\n')]));
 assert.throws(()=>Stage.loadStaged(published[0]),/STAGED_PROVENANCE_MISMATCH/);
 fs.writeFileSync(regPath,pristine);
 assert.equal(Stage.loadStaged(published[0]).ok,true);
 const manifestPath=path.join(firstDir,'manifest.json');
 const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
 manifest.source_ids=['REF-085'];
 fs.writeFileSync(manifestPath,JSON.stringify(manifest));
 assert.throws(()=>Stage.loadStaged(published[0]),/STAGED_SOURCE_BINDING_MISMATCH/);
 assert.throws(()=>Stage.loadStaged('../unauthorized'),/STAGE_ID_INVALID/);
 for(const v of before){
  assert.equal(sha(fs.readFileSync(v.file)),v.digest,'OPERATING_BYTES_MUTATED '+v.file);
  assert.equal(fs.statSync(v.file).mtimeMs,v.mtime,'OPERATING_MTIME_MUTATED '+v.file);
 }
 console.log('FORMING_AUTHORITY_STAGING_AND_LEARNING_READBACK_PASS',JSON.stringify({
  staged_source_ids:['REF-081','REF-085'],scoped_patterns_differ:true,
  authority_fixture_only:true,registry_hash_verified:true,
  tampering_blocked:true,previous_stage_replacement_blocked:true,
  application_runtime_consumed:false,real_approval_verified:false,
  operating_current_changed:false,global_feedback_linked:false
 }));
}finally{
 for(const id of published)fs.rmSync(path.join(Stage.STAGING_ROOT,id),{recursive:true,force:true});
 fs.rmSync(fixtureRoot,{recursive:true,force:true});
}
