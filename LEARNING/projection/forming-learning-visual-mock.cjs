'use strict';
/**
 * TAKY FORMING -> LEARNING -> simulated Hide & Seek consumer.
 * TEST-FIXTURE ONLY. Source/owner approvals are deliberately generated in
 * a disposable directory, never persisted as operational authority.
 * The recommendations come from the REAL selector and signed authority gate.
 */
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const assert=require('node:assert/strict');
const Pipeline=require('../intake/index-forming-learning-consumption');
const Sign=require('../intake/independent-signed-forming-authority');
const Stage=require('./approved-learning-stage');
const Selector=require('../pedagogy/grade-aware-term-selector');
const {previewBoundSelector}=require('./forming-approved-input');
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
const ROOT=path.resolve(__dirname,'..','..');
const OUT=path.resolve(ROOT,'..','TAKY_AI_WORKBENCH','01_BACKLOG_AND_ADOPTION','80_EVIDENCE','FORMING_LEARNING_VISUAL_MOCK');
const RULES=require('../data/learning-reference-pattern-projection-rules-v1.json');
const currentPath=path.join(ROOT,'CURRENT','DATA','LEARNING_REFERENCE_PATTERN_PROJECTION_CURRENT.json');
const registryPath=path.join(ROOT,'LEARNING','data','mining-learning-pattern-registry-v1.json');
const canonicalSourceFiles=[currentPath,registryPath];

function candidate(id){
 return {
  source_id:id,source_ref:'INDEX:'+id,
  source_family:'EDUCATION_REVIEW',source_type:'REFERENCE_DOCUMENT',
  authority_class:'REFERENCE_ONLY',detail_anchor:'INDEX:'+id,
  provenance:['FIXTURE_ONLY_NOT_REAL_OWNER:INDEX:'+id],
  relations:[{type:'CONCEPT_RELATION',target:'LEARNING:PATTERN',anchor:'INDEX:'+id}]
 };
}
function prepare(id){
 const x=candidate(id);
 const verifier=(sid,ref)=>({
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
  domain_use_authorized:true,source_id:sid,source_ref:ref,
  index_version:'FIXTURE_NOT_AN_INDEPENDENT_OWNER',
  review_evidence_refs:['MOCK_TEST_OWNER_ONLY'],
  source_family:x.source_family,source_type:x.source_type,
  authority_class:x.authority_class,detail_anchor:x.detail_anchor,
  provenance:x.provenance,relations:x.relations
 });
 const prepared=Pipeline.prepare({
   query_context:{consumer_app:'HIDE_SEEK',function_id:'LE-REF-PATTERN',
    requested_behavior:'REVIEW_SOURCE_SCOPED_PATTERN'},
   candidates:[x]
 },verifier,{owner_namespace:'LEARNING_OS',forming_kind:'CONTENT_FORMING',
  target_consumer:'HIDE_SEEK',ruleset_revision:RULES.version});
 assert.equal(prepared.ok,true);
 return prepared;
}
const term={
 id:'science-e5-front',subject:'SCIENCE',term:'한랭전선',hanja:'寒冷前線',
 meaning:'찬 공기가 따뜻한 공기 아래로 파고들며 만들어지는 전선',
 gradeBand:'5-6',source_ref:'CURR:SCIENCE:5-6:WEATHER_FRONT',
 grade_alignment:{state:'VERIFIED',source_ref:'CURR:SCIENCE:5-6:WEATHER_FRONT'},
 components:[{text:'寒',meaning:'차갑다'}],
 concept:{relations:['차가운 공기 관계'],summary:'공기와 날씨 관계'},
 unit_tags:['날씨'],example:'한랭전선이 다가온다'
};
const learningInput={
 learner_profile:{schoolStage:'E5'},subject:'SCIENCE',consumer_app:'HIDE_SEEK',
 candidate_terms:[term],term_evidence:[
  {learning_target_id:'science-e5-front',result_type:'WRONG',interaction_mode:'CORE'},
  {learning_target_id:'science-e5-front',result_type:'WRONG',interaction_mode:'LINK'}
 ]};
function runSignedMock(sourceId){
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'taky-forming-visual-'));
 const approvals=path.join(temp,'authority'),evidence=path.join(temp,'evidence');
 fs.mkdirSync(approvals);fs.mkdirSync(evidence);
 const pair=crypto.generateKeyPairSync('ed25519');
 const publicKeyPath=path.join(temp,'public.pem');
 fs.writeFileSync(publicKeyPath,pair.publicKey.export({format:'pem',type:'spki'}));
 const pin=sha(pair.publicKey.export({format:'der',type:'spki'}));
 const trust=Sign.fromTrustedHostSettings({publicKeyPath,expectedSpkiSha256:pin});
 assert.equal(trust.configured,true);
 const prepared=prepare(sourceId);
 const proof=Buffer.from('MOCK SIGNED APPROVAL TEST: not a human approval; local-only.');
 fs.writeFileSync(path.join(evidence,'fixture.txt'),proof);
 const record={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',
  artifact_id:prepared.formed.artifact_id,
  artifact_revision:prepared.formed.artifact_revision,
  owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',
  approved_by:'TEST_FIXTURE_DO_NOT_RELEASE',
  approved_at:'2026-10-15T00:00:00Z',
  evidence_ref:'fixture.txt',evidence_sha256:sha(proof)};
 record.approval_signature_ed25519=crypto.sign(null,Sign.message(record),pair.privateKey).toString('base64');
 const approval=path.join(approvals,'test.json');
 fs.writeFileSync(approval,JSON.stringify(record));
 const opts={authorityRoot:approvals,evidenceRoot:evidence,
  independentAuthorityCheck:trust.independentAuthorityCheck};
 const stageId='mock-forming-'+sha(Buffer.from(sourceId+prepared.formed.artifact_revision)).slice(0,22);
 let stageSaved=false;
 try{
  const out=Stage.stageApproved({prepared,approvalRecordPath:approval,
   authorityOptions:opts,stageId});
  assert.equal(out.ok,true);
  stageSaved=true;
  const stage=Stage.loadStaged(stageId);
  assert.equal(stage.manifest.operational,false);
  assert.equal(stage.manifest.publication_authority,false);
  const derived=Selector.select(learningInput,{
   mode:'BOUND_FORMING_PREVIEW_ONLY',registry:stage.registry});
  assert.equal(derived.ok,true);
  assert.equal(derived.preview_only,true);
  assert.equal(derived.learning_consumed,false);
  const expected=previewBoundSelector(prepared,approval,opts,learningInput);
  assert.equal(expected.ok,true);
  const patterns=derived.recommendations[0].learning_pattern_plan.pattern_ids;
  assert.deepEqual(patterns,expected.decision.recommendations[0].learning_pattern_plan.pattern_ids);
  // Recheck changed approval against the REAL signature verifier.
  fs.writeFileSync(approval,JSON.stringify({...record,target_consumer:'PLAY_CAMP'}));
  const tampered=previewBoundSelector(prepared,approval,opts,learningInput);
  assert.equal(tampered.ok,false);
  return {
    sourceId,patterns,
    termCard:derived.recommendations[0].term_card,
    patternPlan:derived.recommendations[0].learning_pattern_plan,
    formation:stage.manifest.artifact_id,
    shaBoundOriginal:stage.manifest.artifact_revision,
    signedVerified:true,independentActualHumanApproval:false,
    stageReadback:true,previewOnly:true,productionLearningConsumed:false,
    appRelease:false,tamperRejected:true
  };
 }finally{
  if(stageSaved)fs.rmSync(path.join(Stage.STAGING_ROOT,stageId),{recursive:true,force:true});
  fs.rmSync(temp,{recursive:true,force:true});
 }
}
function escapeInlineJSON(obj){
 return JSON.stringify(obj).replace(/</g,'\\u003c').replace(/>/g,'\\u003e')
  .replace(/&/g,'\\u0026');
}
function renderHtml(data){
 const payload=escapeInlineJSON(data);
 return `<!doctype html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TAKY · FORMING → LEARNING 목업</title>
<style>
:root{color-scheme:light;--text:#17232e;--muted:#64748b;--line:#d9e4e8;--ink:#2563eb;--bg:#f3f6f8;--orange:#ac5e10}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:"Pretendard","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;color:var(--text);font-size:15px}
main{max-width:1180px;margin:0 auto;padding:24px}header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:22px}
h1{font-size:29px;letter-spacing:-.9px;margin:5px 0 10px}h2{font-size:18px;margin:0 0 12px}p{line-height:1.6;margin:0}.eyebrow{font-size:12px;font-weight:800;letter-spacing:1.4px;color:#52708a}
.sub{color:var(--muted);font-size:14px}.stamp{white-space:nowrap;padding:9px 13px;border:1px solid #ecc597;background:#fff5e7;color:#925014;font-size:12px;border-radius:999px;font-weight:800}
.scenarios{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:18px}
button{font:inherit;cursor:pointer}button.case{padding:14px 10px;background:white;border:1px solid var(--line);border-radius:11px;min-height:54px;text-align:center;font-size:14px;font-weight:750}
button.case[aria-pressed=true]{color:#114cbd;background:#e9f1ff;border-color:#3c7dd9;box-shadow:0 0 0 1px #3c7dd9 inset}
.grid{display:grid;grid-template-columns:1fr 1.25fr;gap:15px}.panel{padding:21px;background:white;border:1px solid var(--line);border-radius:16px;min-width:0}
.steps{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 16px}.step{font-size:11px;background:#eaf0f4;padding:8px 9px;border-radius:7px;font-weight:800}
.step[aria-current=step]{background:#dcecff;color:#2055a7}.flow{display:grid;grid-template-columns:1fr;gap:13px}
.milestone{border-bottom:1px solid #ebeff2;padding-bottom:11px}.milestone:last-child{border:0;padding:0}
.kicker{font-weight:800;font-size:12px;color:var(--muted);margin-bottom:4px}.status{display:inline-block;font-weight:800;font-size:13px;padding:6px 10px;border-radius:7px;background:#edf3f9;color:#365a73}
.status.ok{background:#e8f8ef;color:#16633e}.status.hold{background:#fff0dd;color:#925014}
.trace{margin-top:8px;line-height:1.55;color:var(--muted);font-size:13px;overflow-wrap:anywhere}
.lesson{padding:17px;border:1px solid #d5e7fa;background:linear-gradient(130deg,#f6faff,#fff);border-radius:13px;margin:14px 0}
.word{font-size:30px;font-weight:800;letter-spacing:-.7px}.hanja{color:#64748b;margin-left:8px;font-size:15px}
.lesson>p{color:#4b6579;font-size:14px;margin-top:7px}.pattern-list{display:flex;flex-wrap:wrap;gap:8px;padding:0;list-style:none;margin:12px 0}
.pattern-list>li{padding:9px 12px;border:1px solid #d5e3f2;border-radius:8px;background:#f1f6ff;color:#224a8b;font-size:13px;font-weight:700}
.empty{padding:15px;border:1px dashed #d8a260;border-radius:9px;color:#8d5c27;background:#fff9f2}
.footer{border-top:1px solid #e1e7ec;margin-top:18px;padding-top:12px;color:#68798a;font-size:12px;line-height:1.7}
.mini{font-size:12px;margin-top:9px;color:#667a89}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
@media(max-width:760px){main{padding:14px}header{display:block}h1{font-size:23px}.stamp{display:inline-block;margin-top:10px}.scenarios{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.panel{padding:16px}button.case{font-size:13px}}
</style></head><body><main>
<header><div><div class="eyebrow">TAKY · LEARNING ENGINE</div><h1>FORMING → LEARNING 소비 목업</h1><p class="sub">실제 학습 선택 엔진으로 계산한 승인 시나리오 비교 · 운영 데이터 변경 없음</p></div>
<div class="stamp">검증용 목업 · 운영 미승인</div></header>
<nav class="scenarios" aria-label="승인 시나리오 선택">
 <button class="case" data-case="none" aria-pressed="true">① 승인 없음</button>
 <button class="case" data-case="ref081" aria-pressed="false">② REF-081 서명</button>
 <button class="case" data-case="ref085" aria-pressed="false">③ REF-085 서명</button>
 <button class="case" data-case="tampered" aria-pressed="false">④ 서명 변조</button>
</nav>
<div class="grid">
<section class="panel" aria-label="파이프라인 상태"><h2>파이프라인 · 실행 결과</h2>
 <div class="steps"><span class="step">RAW</span><span class="step">INDEX</span><span class="step" aria-current="step">FORMING</span><span class="step">LEARNING</span><span class="step">앱</span></div>
 <div class="flow">
  <div class="milestone"><div class="kicker">RAW / INDEX</div><span class="status ok" id="raw-status">테스트 원천 근거</span><div class="trace">REF-081 / REF-085 · 검증용 INDEXING_OWNER 영수증</div></div>
  <div class="milestone"><div class="kicker">FORMING 독립 승인</div><span id="approval-status" class="status hold">승인 없음 · HOLD</span><div id="approval-trace" class="trace">독립 승인 서명이 없어 차단했습니다.</div></div>
  <div class="milestone"><div class="kicker">LEARNING 패턴 선택</div><span id="learning-status" class="status hold">소비 차단</span><div id="learning-trace" class="trace">승인 전 지식은 학습 엔진에 적용되지 않습니다.</div></div>
  <div class="milestone"><div class="kicker">CURRENT / 앱 배포</div><span class="status hold">운영 반영 차단</span><div class="trace">모든 시나리오에서 CURRENT·운영 레지스트리·학습자 기록을 변경하지 않습니다.</div></div>
 </div></section>
<section class="panel" aria-label="학습 선택 목업"><h2>Hide & Seek · 학습 선택 미리보기</h2>
 <p class="sub">초등 5학년 과학 · 한랭전선 · CORE / LINK 오답 2회 가정</p>
 <div class="lesson"><span class="word">한랭전선</span><span class="hanja">寒冷前線</span><p>찬 공기가 따뜻한 공기 아래로 파고들며 만들어지는 전선</p></div>
 <div class="kicker">추천 학습 패턴</div><div id="pattern-output" aria-live="polite"><div class="empty">독립 승인 전에는 제안 패턴을 표시하지 않습니다.</div></div>
 <p id="consumer-outcome" class="trace" style="margin-top:14px">앱 콘텐츠 소비: 차단됨</p>
 <div class="footer">표시된 학습 패턴은 테스트용 서명·원천을 거쳐 <strong>실제 Selector.select()</strong>에서 계산한 미리보기입니다. 교사 승인·실제 학생 데이터·운영 앱 배포 증거가 아닙니다.</div>
 </section></div>
</main>
<script id="mock-data" type="application/json">${payload}</script>
<script>
(() => {
 const data=JSON.parse(document.querySelector('#mock-data').textContent);
 const cases={
  none:{hold:'승인 없음 · HOLD',why:'독립 승인 영수증이 없어 FORMING에서 중단',source:null},
  ref081:{hold:null,why:'독립 Ed25519 테스트 서명과 원문 범위 일치',source:data.ref081},
  ref085:{hold:null,why:'독립 Ed25519 테스트 서명과 원문 범위 일치',source:data.ref085},
  tampered:{hold:'서명 변조 · HOLD',why:'서명 검증 또는 승인 대상 일치 검사 실패',source:null}
 };
 function state(key){
  const c=cases[key];
  document.querySelectorAll('button.case').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.case===key)));
  const approved=!!c.source;
  const a=document.querySelector('#approval-status');
  a.className='status '+(approved?'ok':'hold');
  a.textContent=approved?'검증용 서명 일치 · 미리보기 허용':c.hold;
  document.querySelector('#approval-trace').textContent=c.why;
  const l=document.querySelector('#learning-status');
  l.className='status '+(approved?'ok':'hold');
  l.textContent=approved?'패턴 계산 성공 · 미리보기 전용':'소비 차단';
  document.querySelector('#learning-trace').textContent=approved?'원천: '+c.source.sourceId+' / 검증 SHA '+c.source.shaBoundOriginal.slice(0,16)+'…':'승인 전 지식은 학습 엔진에 적용되지 않습니다.';
  const target=document.querySelector('#pattern-output');
  target.replaceChildren();
  if(approved){
    const list=document.createElement('ul');list.className='pattern-list';
    for(const name of c.source.patterns){
      const li=document.createElement('li');li.textContent=name;list.append(li);
    }target.append(list);
  }else{
    const box=document.createElement('div');box.className='empty';box.textContent='독립 승인 전에는 제안 패턴을 표시하지 않습니다.';target.append(box);
  }
  document.querySelector('#consumer-outcome').textContent=approved?
     '테스트용 학습 선택 미리보기만 허용 · 실제 앱 소비와 배포는 차단':
     '앱 콘텐츠 소비: 차단됨';
  document.body.dataset.currentCase=key;
  document.body.dataset.mockApproved=String(approved);
  document.body.dataset.productionReleased='false';
 }
 document.querySelectorAll('button.case').forEach(button=>button.addEventListener('click',()=>state(button.dataset.case)));
 state('none');
})();
</script></body></html>`;
}
async function main(){
 const before=canonicalSourceFiles.map(p=>({path:p,sha:sha(fs.readFileSync(p)),mtime:fs.statSync(p).mtimeMs}));
 assert(fs.existsSync(OUT));
 const result={ref081:runSignedMock('REF-081'),ref085:runSignedMock('REF-085')};
 assert.notDeepEqual(result.ref081.patterns,result.ref085.patterns);
 assert(result.ref081.patterns.includes('P_ERROR_TO_CONCEPT_GAP'));
 assert(result.ref085.patterns.includes('P_CONCEPT_GRAPH'));
 const html=renderHtml(result);
 const revision=sha(Buffer.from(html,'utf8')).slice(0,20);
 const htmlPath=path.join(OUT,'TAKY_FORMING_LEARNING_VISUAL_MOCK_'+revision+'.html');
 if(fs.existsSync(htmlPath)){
  assert.equal(fs.readFileSync(htmlPath,'utf8'),html);
 }else fs.writeFileSync(htmlPath,html,{flag:'wx'});
 for(const p of before){
  assert.equal(sha(fs.readFileSync(p.path)),p.sha);
  assert.equal(fs.statSync(p.path).mtimeMs,p.mtime);
 }
 const proof={schema:'TAKY_FORMING_LEARNING_VISUAL_MOCK_V1',
  status:'BROWSER_VERIFICATION_PENDING',scenario_count:4,
  fixture_only:true,independent_real_owner_approval:false,
  signed_fixture_authority_pass:true,approval_tamper_rejected:true,
  real_selector_pattern_recommendations:result,
  operating_current_modified:false,learning_registry_modified:false,
  real_learners_affected:0,production_deployed:false,
  visual_mock_path:htmlPath,visual_mock_sha256:sha(Buffer.from(html,'utf8'))};
 const proofPath=path.join(OUT,'TAKY_FORMING_LEARNING_VISUAL_MOCK_'+revision+'.json');
 if(!fs.existsSync(proofPath))fs.writeFileSync(proofPath,JSON.stringify(proof,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({status:'SIGNATURE_AND_REAL_SELECTOR_MOCK_GENERATED',
  html_path:htmlPath,proof_path:proofPath,ref081:result.ref081.patterns,
  ref085:result.ref085.patterns,production_operational:false}));
}
if(require.main===module)main().catch(e=>{console.error(e.stack);process.exitCode=1;});
module.exports={renderHtml,runSignedMock};
