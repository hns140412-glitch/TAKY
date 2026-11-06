'use strict';
// TAKY QA runner: existing tests only; local synthetic data; one process at a time.
// Does NOT deploy, push, call paid models, or write real family/finance records.
const fs=require('node:fs'), path=require('node:path'), os=require('node:os');
const {spawnSync,spawn}=require('node:child_process');
const {readCurrentDecisionReceipt,classifyDecisionFailure}=require('./family_group_decision_receipt.cjs');
const root=path.resolve(__dirname,'..'), work=path.dirname(root);
const mode=process.argv.includes('--deep')?'deep':'quick';
const outDir=path.join(root,'.local','family-qa');
fs.mkdirSync(outDir,{recursive:true});
const lock=path.join(outDir,'runner.lock');
const latest=path.join(outDir,'latest-'+mode+'.json');
const started=new Date().toISOString();
const runId=started.replace(/[:.]/g,'-')+'-'+mode;
const cwdFor=r=>path.join(work,r);
const node=process.execPath;
const item=(id,repo,file,args=[],level='quick')=>({id,repo,file,args,level});
const checks=[
 item('family-3-mode','TAKY','ENFORCEMENT/family_group_three_mode_simulation.test.js'),
 item('family-independent-bots','TAKY','ENFORCEMENT/family_group_independent_agents.test.cjs'),
 item('family-member-evidence','TAKY','ENFORCEMENT/learning_multi_member_durable_aggregate_e2e.test.js'),
 item('family-app-continuity','TAKY','ENFORCEMENT/learning_cross_app_continuity_owner_runtime.test.js'),
 item('ready-activity-not-mastery','Ready & Set','tests/ready-activity-not-mastery-runtime.test.cjs'),
 item('ready-parent-learner-planner','Ready & Set','tests/ready-family-planner-central-sync-e2e.cjs'),
 item('central-family-user-data-isolation','TAKY','ENFORCEMENT/family_user_data_learning_engine_e2e.test.js',[],'deep'),
 item('central-family-private-backup-loopback','TAKY','ENFORCEMENT/family_planner_http_to_siezeall_complete_loopback_e2e.test.js',[],'deep'),
 item('mobile-owner-console','TAKY-MOBILE','tests/admin-status.test.mjs'),
 item('mobile-learning-receipt','TAKY-MOBILE','tests/learning-loop-execution.test.mjs'),
 item('mobile-two-family-evidence','TAKY-MOBILE','tests/two-family-evidence-mock.cjs'),
 item('mobile-two-family-learning','TAKY-MOBILE','tests/two-family-learning-consumption-mock.cjs'),
 item('savey-finance-full-local-suite','SAVEY','tests/run.mjs'),
 item('play-camp-learning','Play Camp','tests/aggressiveMockFlows.test.ts',['--test']),
 item('hide-syntax','Hide & Seek','app.js',['--check']),
 item('hide-hint-no-answer-browser','Hide & Seek','tools/code-red-hint-behavior.e2e.cjs'),
 item('hide-hint-negative-control-detection','Hide & Seek','tools/code-red-hint-negative-control.e2e.cjs',[],'deep'),
 item('hide-ocr-low-confidence-and-ondevice-mock-browser','Hide & Seek','tools/ocr-review-provenance.e2e.cjs',[],'deep'),
 item('hide-memory-recall-evidence-browser','Hide & Seek','tools/memory-retrieval-credibility.e2e.cjs',[],'deep'),
 item('hide-english-12-24-hanja-reference-browser','Hide & Seek','tools/restore-cycle-hanja.e2e.cjs'),
 item('hide-english-36-recall-source-proof','Hide & Seek','tools/english-cycle-36-mode-behavior.e2e.cjs',[],'deep'),
 item('hide-offline-restore-cache-browser','Hide & Seek','tools/hide-offline-restoration.e2e.cjs',[],'deep'),
 item('hide-central-auth-learning-recovery-browser','Hide & Seek','tools/real-central-term-http-to-hide-browser.e2e.cjs',['--test'],'deep'),
 item('hide-subject-grade-routing-browser','Hide & Seek','tools/hide-subject-routing.e2e.cjs'),
 item('hide-home-interaction-only-NOT-visual-parity','Hide & Seek','tools/approved-home-learning-behavior.e2e.cjs',[],'deep'),
 item('hide-user-decision-independent-regression','Hide & Seek','tools/user-decision-authority.e2e.cjs'),
 item('hide-first-find-unassisted-retrieval','Hide & Seek','tools/first-find-user-contract.e2e.cjs',[],'deep'),
 item('hide-new12-review24-revisit-isolation','Hide & Seek','tools/new-review-trace-separation.e2e.cjs',[],'deep'),
 item('hide-exploration-language-real-screens','Hide & Seek','tools/hide-user-journey-world-copy.e2e.cjs',[],'deep'),
 item('snap-syntax','Snap & Pop','app.js',['--check']),
 item('snap-expression-input-quality-browser','Snap & Pop','tools/test-snap-expression-expansion-browser.cjs'),
 item('mobile-authorized-admin-browser','TAKY-MOBILE','tests/admin-progress-browser-e2e.mjs',[],'deep'),
 item('mobile-ops-release-authenticated-browser','TAKY-MOBILE','tests/admin-console-browser-e2e.mjs',[],'deep'),
 item('independent-savey-admin-browser-bots','TAKY','ENFORCEMENT/family_group_browser_guard.cjs',[],'deep'),
 item('independent-learning-specialist-browser-bots','TAKY','ENFORCEMENT/family_group_browser_guard.cjs',['--specialists'],'deep'),
 item('mobile-family-signin-resume-browser','TAKY-MOBILE','tests/family-google-login-browser-e2e.mjs',[],'deep'),
 item('mobile-cross-app-audio-approval-hold','TAKY-MOBILE','tests/learning-loop-multi-specialist-roundtrip-e2e.cjs',['--approval-hold'],'deep'),
 item('mobile-cross-app-browser','TAKY-MOBILE','tests/learning-loop-multi-specialist-roundtrip-e2e.cjs',[],'deep'),
 item('ready-homework-parent','Ready & Set','tests/ready-homework-parent-confirm-planner-e2e.mjs',[],'deep'),
 item('ready-planner-history','Ready & Set','tests/ready-planner-actual-history-replan-e2e.mjs',[],'deep'),
 item('play-camp-voice-preflight','Play Camp','scripts/validate-voice-preview-preflight.mjs',[],'deep'),
];
// These are gaps in evidence, not failures and NEVER silently turn green.
const gaps=[
 {id:'hide-hanja-canonical-learning-link',priority:'P0',area:'HIDE',why:'한자 참고 훈음 48자와 네 모드 실제 조작은 로컬 구현·테스트했으나 공식 학년별 HANJA Learning Engine 배정·장기복습·정식 성취 반영은 미검증. 참고 학습은 점수 승격 금지'},
 {id:'hide-device-local-ocr-ios-engine-real-photo',priority:'P0',area:'HIDE',why:'기기 내 TextDetector 선행 호출과 저신뢰 수동 승인 경로는 모의 인식기 Chrome E2E를 통과. 실제 iPhone Safari에서는 TextDetector 사용 불가, 한국어+영어 실제 시험지 OCR과 가족별 승인·기기 격리는 검증되지 않음. 운영 복구/정식 인식 완료 주장 금지'},
 {id:'hide-six-subject-real-device-and-learning',priority:'P0',area:'HIDE/READY',why:'영어 기본/6과목 전환과 합성 시험지 신규12+지난24 원문 출처 조합은 로컬 Chrome 검증. 운영 OCR·부모 권한 확인·Learning Engine 복습 우선순위·Ready 실제 배정·가족별 기록 격리·iPhone 실기기·중앙 성취왕복 미검증'},
 {id:'snap-expression-validity',priority:'P0',area:'SNAP',why:'2026-10-17 이전 Chrome에서는 qzxqzx 3회로 EXP 55가 잘못 지급됨. 현재 반복 문자열/동일 답변 재사용은 실제 브라우저 부정 테스트로 차단하나, 문장의 의미와 확장 논리·독립 성취는 확인되지 않음. 구조 검사 통과를 Learning Engine 성취로 승격하지 말 것'},
 {id:'cross-app-learning-achievement-evidence',priority:'P0',area:'HIDE/SNAP/PLAY',why:'Ready 학습앱 복귀의 활동 완료와 검증된 성취를 분리함. 2026-10-21 세 전문앱 실제 Chrome 왕복 중 Hide/Snap 후 Play Camp CVC 완료가 보류됨: 발음 원본 11개는 DEV_PLACEHOLDER, 실제 승인된 소리 듣기 증거가 없으므로 작업 COMPLETED가 아닌 PARTIAL로 유지하는 것이 맞음. 해당 승인·실기기 듣기 검증 없이는 3/3 완료/중앙 성취 증명 금지'},
 {id:'visual-family-role-e2e',priority:'P0',area:'ALL',why:'부모/학습자 실제 화면을 가족 단위로 연속 조작하는 UI E2E 미검증'},
 {id:'ready-pointer-navigation-timeout',priority:'P0',area:'READY',why:'기존 전체 브라우저 QA 16초 제한시간 실패는 Ready 단독 오류로 확정할 수 없음. 범위 분리 후 부모 READY 홈·설정 포인터 클릭·새로고침이 독립 로컬 Chrome 검증에서 약 6초 / 오류 0건으로 PASS. 다중 가족앱 연속 왕복과 실제 기기에서는 미검증이며 해당 범위가 남은 HOLD'},
 {id:'savey-cross-app-family-e2e',priority:'P0',area:'SAVEY',why:'같은 가족의 학습/미션/금융 데이터 앱 간 통합 시나리오 미검증'},
 {id:'mobile-legacy-ops-release-qa-auth-migration',priority:'P1',area:'TAKY-MOBILE',why:'구형 OPS 테스트를 2026-10-21 비공개 로그인 모델로 이관. 6개 Chrome 시나리오(사용자 공개 격리·관리자 인증·배포 버전/오래된 상태·로컬 QA·외부 주소) 단독 PASS. 전체 정기 심층 QA에서 이관된 두 관리자 검사의 재현성 검증은 별도 필요'},
 {id:'administrator-qa-consumption',priority:'P0',area:'TAKY-MOBILE',why:'로컬 관리자 화면에 QA 개수·P0 원본 ID를 연결하고 인증된 모바일/데스크톱 브라우저 검증은 완료. 운영 관리자 데이터 배포와 결함별 실제 조치·검증 환류는 아직 미검증'},
 {id:'hide-snap-browser-e2e',priority:'P1',area:'HIDE/SNAP',why:'5앱 로컬 Chrome 결과 영수증 왕복은 재현 PASS, 운영 중앙 학습 데이터 영속 기록 및 실기기 복귀는 아직 미검증'},
 {id:'tablet-fold-audio-usability',priority:'P1',area:'PLAY-CAMP',why:'종이 넘김/접기/음성 안내의 실기기 시각 및 접근성 검증 필요'},
 {id:'production-device-session',priority:'P1',area:'ALL',why:'운영 배포의 실기기 iOS/Android 세션·복구·동기화 검증 없음'},
 {id:'multi-specialist-browser-stability',priority:'P0',area:'TAKY-MOBILE/READY',why:'정기 deep QA에서 5앱 실브라우저 왕복(학습/공유/복귀)을 검증해야 함; quick 모드에서는 미실행'},
];
function safe(s){
 return String(s||'').replace(/Bearer\s+[^\s]+/gi,'Bearer [REDACTED]')
   .replace(/(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[^\s,;]+/gi,'$1=[REDACTED]')
   .replace(/[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{24,}/g,'[REDACTED_JWT]')
   .slice(-2500);
}
function atomicJSON(dest,data){
 const t=dest+'.tmp-'+process.pid;
 fs.writeFileSync(t,JSON.stringify(data,null,2),'utf8');
 try{fs.renameSync(t,dest);}
 catch(e){
   if(!['EPERM','EEXIST','EACCES'].includes(e.code))throw e;
   // Windows may refuse an atomic rename over a pre-existing file.
   // Each immutable history record is still safely retained separately.
   fs.copyFileSync(t,dest);fs.rmSync(t,{force:true});
 }
}
// This old browser E2E expects five servers. Start isolated localhost fixtures only for that case.
const fixtureMap=[
  ['TAKY-MOBILE',4350],['Ready & Set',4351],['Hide & Seek',4352],
  ['Snap & Pop',4321],['Play Camp/dist',4331]
];
function startFixtures(){
 const children=fixtureMap.map(([repo,port])=>{
   const child=spawn(node,[path.join(__dirname,'family_qa_local_static_host.cjs'),path.join(work,repo),String(port)],
     {windowsHide:true,stdio:'ignore'});
   child.on('error',()=>{});
   return child;
 });
 // Children start asynchronously, and each is probed before the browser test.
 Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,800);
 const probe=spawnSync(node,['-e',
   'Promise.all(process.argv.slice(1).map(async p=>{const r=await fetch("http://127.0.0.1:"+p+"/__taky_qa_probe");if(!r.ok||(await r.text())!=="TAKY_QA_LOCAL_FIXTURE_V1")throw Error("fixture mismatch "+p)})).catch(e=>{console.error(e.message);process.exit(1)})',
   ...fixtureMap.map(x=>String(x[1]))],{encoding:'utf8',timeout:5000,windowsHide:true});
 if(probe.status!==0){for(const c of children)c.kill();throw Error('LOCAL_FIXTURE_NOT_READY: '+safe(probe.stderr||probe.error?.message));}
 return children;
}
function stopFixtures(children){for(const c of children)c.kill();}
let fd;
try {
 try{fd=fs.openSync(lock,'wx');fs.writeFileSync(fd,JSON.stringify({pid:process.pid,started,mode}));}
 catch(e){
   if(e.code!=='EEXIST')throw e;
   const age=Date.now()-fs.statSync(lock).mtimeMs;
   if(age>60*60*1000){fs.rmSync(lock,{force:true});fd=fs.openSync(lock,'wx');fs.writeFileSync(fd,JSON.stringify({pid:process.pid,started,mode}));}
   else {console.log(JSON.stringify({state:'SKIPPED_BUSY',mode,lock}));process.exit(2);}
 }
 const previous=fs.existsSync(latest)?JSON.parse(fs.readFileSync(latest,'utf8')):null;
 const results=[];
 const deadline=Date.now()+(mode==='quick'?5:12)*60*1000;
 for(const test of checks.filter(x=>mode==='deep'||x.level==='quick')){
   const here=cwdFor(test.repo), file=path.join(here,test.file);
   if(!fs.existsSync(file)){
     results.push({id:test.id,state:'MISSING',reason:'TEST_FILE_MISSING',repo:test.repo});
     continue;
   }
   if(Date.now()>deadline){
     results.push({id:test.id,state:'NOT_RUN',reason:'RUN_BUDGET_EXCEEDED',repo:test.repo});
     continue;
   }
   if(test.id==='mobile-cross-app-browser'){
     const source=path.join(work,'Play Camp','src','data','playCampPronunciationAssets.ts');
     const original=fs.readFileSync(source,'utf8');
     const soundStatus=/PLAY_CAMP_PRONUNCIATION_SET_STATUS\s*=\s*'([^']+)'/.exec(original)?.[1]||'UNKNOWN';
     if(soundStatus!=='APPROVED_LOCKED'){
       results.push({id:test.id,repo:test.repo,state:'BLOCKED',
         reason:'UNAPPROVED_ENGLISH_SOUND_FULL_JOURNEY_HOLD:'+soundStatus,
         scope:'EXPECTED_HOLD_NOT_PRODUCT_3_OF_3_PASS',audioSource:source});
       continue;
     }
   }
   const startedCheck=Date.now();
   // Node CLI options such as --test must precede the source file; the
   // app-specific --approval-hold mode is an argument to the test, not Node.
   const args=['independent-learning-specialist-browser-bots','mobile-cross-app-audio-approval-hold'].includes(test.id)
     ? [file,...test.args] : [...test.args,file];
   // node --test/--check precede file, no additional shell.
   let call, fixtures=[];
   try{
     if(['mobile-cross-app-browser','mobile-cross-app-audio-approval-hold'].includes(test.id))fixtures=startFixtures();
     call=spawnSync(node,args,{
       cwd:here,env:{...process.env,TAKY_QA_SYNTHETIC:'1',TAKY_QA_NETWORK:'MOCK_ONLY',TAKY_QA_SEED:process.env.TAKY_QA_SEED||new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Seoul'}).replace(/-/g,''),TAKY_QA_AGENT_STEPS:mode==='deep'?'24':'10',
        TAKY_QA_RUN_ID:runId+'-'+test.id,
        TAKY_ADMIN_E2E_LOCAL_SNAPSHOT:test.id==='mobile-authorized-admin-browser'?'1':process.env.TAKY_ADMIN_E2E_LOCAL_SNAPSHOT},
       encoding:'utf8',timeout:test.level==='deep'?60000:45000,
       maxBuffer:1024*1024,windowsHide:true
     });
   }catch(error){call={error,status:null,stderr:error.message};}
   finally{stopFixtures(fixtures);}
   const state=call.error?.code==='ETIMEDOUT'?'TIMEOUT':call.error?'ERROR':call.status===0?'PASS':'FAIL';
   results.push({id:test.id,repo:test.repo,state,startedMs:startedCheck,durationMs:Date.now()-startedCheck,
     ...(state==='PASS'?{}:{reason:safe(call.stderr||call.stdout||call.error?.message||'UNKNOWN_TEST_FAILURE'),exitCode:call.status})});
 }
 const verifiedFiveApp=results.some(r=>r.id==='mobile-cross-app-browser'&&r.state==='PASS');
 const activeGaps=gaps.filter(g=>!(g.id==='multi-specialist-browser-stability'&&verifiedFiveApp));
 // Read the child test's FRESH structured receipt. Never parse cropped stdout.
 // Preserve USER-violation versus SOURCE-approval-gap separately.
 const authority=results.find(r=>r.id==='hide-user-decision-independent-regression');
 if(authority){
  const receipt=readCurrentDecisionReceipt(
   path.join(cwdFor('Hide & Seek'),'.local','decision_authority_regression_20261017','USER_DECISION_INDEPENDENT_REGRESSION.json'),
   authority.startedMs||Date.now(),runId+'-'+authority.id);
  if(authority.state==='FAIL')activeGaps.push(...classifyDecisionFailure(receipt));
  else if(authority.state==='PASS'){
   // PASS means no direct user-contract violations; source and visual
   // approval gaps must still appear as their own P0/P1 HOLDs, not become
   // either a fake regression failure or a fake completed design.
   if(receipt.status!=='FRESH_VALID'||receipt.violations.length)
    activeGaps.push({id:'hide-decision-inconsistent-green-evidence',priority:'P0',area:'HIDE',why:'PASS와 사용자 원문 검증 영수증 불일치 · 승격 금지'});
   else if(receipt.sourceGaps.length)activeGaps.push(...classifyDecisionFailure(receipt));
  }else activeGaps.push({id:'hide-decision-test-unavailable',priority:'P0',area:'HIDE',why:'사용자 원문 검증 브라우저 미실행/환경 오류'});
 }
 const lastStates=new Map((previous?.results||[]).map(r=>[r.id,r.state]));
 const newFailures=results.filter(r=>!['PASS','BLOCKED','NOT_RUN'].includes(r.state)&&lastStates.get(r.id)!==r.state).map(r=>r.id);
 const recovered=results.filter(r=>r.state==='PASS'&&lastStates.has(r.id)&&lastStates.get(r.id)!=='PASS').map(r=>r.id);
 const blocked=results.filter(r=>r.state==='BLOCKED'||r.state==='NOT_RUN');
 const failed=results.filter(r=>!['PASS','BLOCKED','NOT_RUN'].includes(r.state));
 const report={
  contract:'TAKY_FAMILY_PERIODIC_QA_V1',mode,startedAt:started,finishedAt:new Date().toISOString(),
  scope:'LOCAL_SYNTHETIC_AND_EXISTING_AUTOMATED_TESTS',productionVerified:false,
  statuses:{passed:results.filter(r=>r.state==='PASS').length,failed:failed.length,blocked:blocked.length,openGaps:activeGaps.length},
  results,newFailures,recovered,gaps:activeGaps,
  verdict:failed.length?'TEST_FAILURE':blocked.length?'INCOMPLETE_WITH_GAPS':activeGaps.some(g=>g.priority==='P0')?'TESTS_PASS_WITH_CRITICAL_GAPS':'NO_KNOWN_CRITICAL_GAPS',
  restrictions:['NO_PAID_API','NO_PUSH','NO_MERGE','NO_DEPLOY','NO_PRODUCTION_WRITES']
 };
 const history=path.join(outDir,'history');
 fs.mkdirSync(history,{recursive:true});
 atomicJSON(path.join(history,runId+'.json'),report);
 atomicJSON(latest,report);
 console.log(JSON.stringify({mode,verdict:report.verdict,statuses:report.statuses,newFailures,recovered,
  report:latest,blocked:blocked.map(r=>r.id),failed:failed.map(r=>({id:r.id,state:r.state,reason:r.reason?.slice(-300)}))}));
 process.exitCode=failed.length?1:0;
}catch(error){
 console.error(JSON.stringify({mode,error:safe(error.stack||error.message)}));
 process.exitCode=3;
}finally{
 if(fd!==undefined){fs.closeSync(fd);fs.rmSync(lock,{force:true});}
}
