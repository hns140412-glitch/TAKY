'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const Pipeline=require('../intake/index-forming-learning-consumption');
const {previewBoundSelector,previewBoundApproved}=require('./forming-approved-input');
const Selector=require('../pedagogy/grade-aware-term-selector');
const Engine=require('../runtime/learning-engine-runtime');
const ROOT=path.resolve(__dirname,'..','..');
const CURRENT=path.join(ROOT,'CURRENT','DATA','LEARNING_REFERENCE_PATTERN_PROJECTION_CURRENT.json');
const REGISTRY=path.join(ROOT,'LEARNING','data','mining-learning-pattern-registry-v1.json');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const currentBefore=sha(fs.readFileSync(CURRENT));
const registryBefore=sha(fs.readFileSync(REGISTRY));
const root=fs.mkdtempSync(path.join(os.tmpdir(),'taky-approved-learning-preview-'));
const approvals=path.join(root,'approvals'),evidence=path.join(root,'evidence');
fs.mkdirSync(approvals);fs.mkdirSync(evidence);
const raw=Buffer.from('local fixture -- NOT a real authority approval');
fs.writeFileSync(path.join(evidence,'proof.txt'),raw);
const opts={authorityRoot:approvals,evidenceRoot:evidence,
 independentAuthorityCheck:({receipt,evidencePath})=>receipt.approved_by==='TEST_FIXTURE_ONLY'
   &&evidencePath===path.join(evidence,'proof.txt')};
const term={
 id:'science-e5-front',subject:'SCIENCE',term:'한랭전선',hanja:'寒冷前線',
 meaning:'찬 공기가 따뜻한 공기 아래로 파고들며 만들어지는 전선',
 gradeBand:'5-6',source_ref:'CURR:SCIENCE:5-6:WEATHER_FRONT',
 grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:5-6:WEATHER_FRONT'},
 components:[{text:'寒',meaning:'차갑다'}],
 concept:{relations:['차가운 공기 관계'],summary:'공기와 날씨 관계'},
 unit_tags:['날씨'],example:'한랭전선이 다가온다'
};
const selectorInput={
 learner_profile:{schoolStage:'E5'},subject:'SCIENCE',consumer_app:'HIDE_SEEK',
 candidate_terms:[term],term_evidence:[
  {learning_target_id:'science-e5-front',result_type:'WRONG',interaction_mode:'CORE'},
  {learning_target_id:'science-e5-front',result_type:'WRONG',interaction_mode:'LINK'}
 ]
};
function approvedSource(id,rev=require('../data/learning-reference-pattern-projection-rules-v1.json').version){
 const sourceRef='INDEX:'+id;
 const relation={type:'CONCEPT_RELATION',target:'LEARNING:PATTERN',anchor:'INDEX:'+id};
 const candidate={source_id:id,source_ref:sourceRef,
  source_family:'EDUCATION_REVIEW',source_type:'REFERENCE_DOCUMENT',
  authority_class:'REFERENCE_ONLY',detail_anchor:'INDEX:'+id,
  provenance:['EXISTING_LEDGER:'+id],relations:[relation]};
 const input={query_context:{consumer_app:'HIDE_SEEK',function_id:'LE-REF-PATTERN',
  requested_behavior:'REVIEW_SOURCE_SCOPED_PATTERN'},candidates:[candidate]};
 const verifier=(sid,ref)=>({
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',domain_use_authorized:true,
  source_id:sid,source_ref:ref,index_version:'TEST_INDEX_OWNER',
  review_evidence_refs:['TEST_INDEX_OWNER_RECEIPT'],
  source_family:candidate.source_family,source_type:candidate.source_type,
  authority_class:candidate.authority_class,detail_anchor:candidate.detail_anchor,
  provenance:candidate.provenance,relations:candidate.relations
 });
 const prepared=Pipeline.prepare(input,verifier,{
  owner_namespace:'LEARNING_OS',forming_kind:'CONTENT_FORMING',
  target_consumer:'HIDE_SEEK',ruleset_revision:rev
 });
 assert.equal(prepared.ok,true);
 const file=path.join(approvals,id+'.json');
 const receipt={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',
  artifact_id:prepared.formed.artifact_id,artifact_revision:prepared.formed.artifact_revision,
  owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',
  approved_by:'TEST_FIXTURE_ONLY',approved_at:'2026-10-14T00:00:00Z',
  evidence_ref:'proof.txt',evidence_sha256:sha(raw)};
 fs.writeFileSync(file,JSON.stringify(receipt));
 return {prepared,file,receipt};
}
try{
 const ref081=approvedSource('REF-081');
 const ref085=approvedSource('REF-085');
 // The unsigned or missing authority path must not promote a source.
 assert.equal(previewBoundApproved(ref081.prepared,ref081.file,{
  ...opts,independentAuthorityCheck:null}).ok,false);
 const a=previewBoundSelector(ref081.prepared,ref081.file,opts,selectorInput);
 const b=previewBoundSelector(ref085.prepared,ref085.file,opts,selectorInput);
 assert.equal(a.ok,true);assert.equal(b.ok,true);
 assert.equal(a.stage,'BOUND_FORMING_LEARNING_PREVIEW');
 assert.equal(a.decision.ok,true);assert.equal(b.decision.ok,true);
 assert.equal(a.decision.recommendations.length,1);
 assert.equal(b.decision.recommendations.length,1);
 const x=a.decision.recommendations[0].learning_pattern_plan;
 const y=b.decision.recommendations[0].learning_pattern_plan;
 assert.ok(x.pattern_ids.includes('P_ERROR_TO_CONCEPT_GAP'));
 assert.ok(!y.pattern_ids.includes('P_ERROR_TO_CONCEPT_GAP'));
 assert.ok(y.pattern_ids.includes('P_CONCEPT_GRAPH'));
 assert.ok(!x.pattern_ids.includes('P_CONCEPT_GRAPH'));
 assert.deepEqual(a.source_ids,['REF-081']);
 assert.deepEqual(b.source_ids,['REF-085']);
 assert.deepEqual(x.source_refs,['INDEX:REF-081']);
 assert.deepEqual(y.source_refs,['INDEX:REF-085']);
 assert.equal(a.decision.authority,'TAKY_LEARNING_PREVIEW_NOT_OPERATIONAL');
 assert.equal(Selector.validate(a.decision).ok,false);
 const central=Engine.previewBoundFormingTermRecommendations({
  prepared:ref081.prepared,approval_record_path:ref081.file,
  authority_options:opts,term_input:selectorInput
 });
 assert.equal(central.ok,true);
 assert.equal(central.stage,'LEARNING_ENGINE_SCOPED_PREVIEW');
 assert.deepEqual(central.selector_decision.recommendations[0].learning_pattern_plan.pattern_ids,
                  x.pattern_ids);
 assert.equal(central.app_consumer_notified,false);
 assert.equal(central.feedback_persisted,false);
 assert.equal(Engine.validate(central).ok,false,'Preview must not pass production engine validation');
 const noAuthority=Engine.previewBoundFormingTermRecommendations({
  prepared:ref081.prepared,approval_record_path:ref081.file,
  authority_options:{...opts,independentAuthorityCheck:null},term_input:selectorInput
 });
 assert.equal(noAuthority.ok,false);
 assert.equal(a.write_performed,false);
 assert.equal(a.learning_consumed,false);
 assert.equal(a.app_runtime_bound,false);
 assert.equal(a.release_approved,false);
 const tampered=structuredClone(ref081.prepared);
 tampered.formed.index_refs[0].relations.push({target:'FORGED_RELATION'});
 assert.equal(previewBoundApproved(tampered,ref081.file,opts).ok,false);
 const stale=approvedSource('REF-081','DEPRECATED_RULES_REV');
 const staleResult=previewBoundApproved(stale.prepared,stale.file,opts);
 assert.equal(staleResult.ok,false);
 assert.equal(staleResult.stage,'FORMING_RULESET');
 assert.ok(staleResult.issues.includes('RULESET_REVISION_MISMATCH'));
 const diff={before:x.pattern_ids,after:y.pattern_ids,
  removed:x.pattern_ids.filter(v=>!y.pattern_ids.includes(v)),
  added:y.pattern_ids.filter(v=>!x.pattern_ids.includes(v))};
 assert.ok(diff.removed.length>0&&diff.added.length>0);
 assert.equal(sha(fs.readFileSync(CURRENT)),currentBefore);
 assert.equal(sha(fs.readFileSync(REGISTRY)),registryBefore);
 console.log('BOUND_FORMING_LEARNING_PREVIEW_PASS',JSON.stringify({
   scope:'ONLY_TEST_FIXTURE_APPROVAL_NO_PRODUCT_AUTHORITY',
   source_a:'REF-081',source_b:'REF-085',difference:diff,
   app_consumer:'HIDE_SEEK_SELECTOR_PREVIEW_ONLY',
   current_unchanged:true, registry_unchanged:true,
   persisted_learning_feedback:false,app_runtime_bound:false,
   approved_real_source:false
 }));
}finally{fs.rmSync(root,{recursive:true,force:true});}
