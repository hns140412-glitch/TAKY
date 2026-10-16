'use strict';
// TAKY QA runner: existing tests only; local synthetic data; one process at a time.
// Does NOT deploy, push, call paid models, or write real family/finance records.
const fs=require('node:fs'), path=require('node:path'), os=require('node:os');
const {spawnSync,spawn}=require('node:child_process');
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
 item('hide-hint-no-answer-browser','Hide & Seek','tools/code-red-hint-behavior.e2e.cjs',[],'deep'),
 item('hide-subject-grade-routing-browser','Hide & Seek','tools/hide-subject-routing.e2e.cjs'),
 item('hide-subject-home-learning-browser','Hide & Seek','tools/approved-home-learning-behavior.e2e.cjs',[],'deep'),
 item('snap-syntax','Snap & Pop','app.js',['--check']),
 item('snap-expression-input-quality-browser','Snap & Pop','tools/test-snap-expression-expansion-browser.cjs'),
 item('mobile-console-browser','TAKY-MOBILE','tests/admin-console-browser-e2e.mjs',[],'deep'),
 item('independent-savey-admin-browser-bots','TAKY','ENFORCEMENT/family_group_browser_guard.cjs',[],'deep'),
 item('independent-learning-specialist-browser-bots','TAKY','ENFORCEMENT/family_group_browser_guard.cjs',['--specialists'],'deep'),
 item('mobile-family-signin-resume-browser','TAKY-MOBILE','tests/family-google-login-browser-e2e.mjs',[],'deep'),
 item('mobile-cross-app-browser','TAKY-MOBILE','tests/learning-loop-multi-specialist-roundtrip-e2e.cjs',[],'deep'),
 item('ready-homework-parent','Ready & Set','tests/ready-homework-parent-confirm-planner-e2e.mjs',[],'deep'),
 item('ready-planner-history','Ready & Set','tests/ready-planner-actual-history-replan-e2e.mjs',[],'deep'),
 item('play-camp-voice-preflight','Play Camp','scripts/validate-voice-preview-preflight.mjs',[],'deep'),
];
// These are gaps in evidence, not failures and NEVER silently turn green.
const gaps=[
 {id:'hide-hanja-canonical-learning-link',priority:'P0',area:'HIDE',why:'한자 전용 훈·음·뜻 Language Memory 실행 경로 미연결. 원천 자료만 확인됐고 다른 과목으로 대체 금지'},
 {id:'hide-six-subject-real-device-and-learning',priority:'P0',area:'HIDE/READY',why:'6과목 홈/학년별 정적 프로젝션만 국지 검증. 실제 Ready 지정 범위, 영어 12+24, 한자, 모바일 실기기, 중앙 결과 왕복은 미검증'},
 {id:'snap-expression-validity',priority:'P0',area:'SNAP',why:'2026-10-17 이전 Chrome에서는 qzxqzx 3회로 EXP 55가 잘못 지급됨. 현재 반복 문자열/동일 답변 재사용은 실제 브라우저 부정 테스트로 차단하나, 문장의 의미와 확장 논리·독립 성취는 확인되지 않음. 구조 검사 통과를 Learning Engine 성취로 승격하지 말 것'},
 {id:'cross-app-learning-achievement-evidence',priority:'P0',area:'HIDE/SNAP/PLAY',why:'기존 5앱 완료 영수증은 버튼·청취·자기보고 중심. 독립 회상·오답·도움 수준·성취 검증의 부정 테스트와 사실 판단 미확보'},
 {id:'visual-family-role-e2e',priority:'P0',area:'ALL',why:'부모/학습자 실제 화면을 가족 단위로 연속 조작하는 UI E2E 미검증'},
 {id:'ready-pointer-navigation-timeout',priority:'P0',area:'READY',why:'부모 가상 세션 READY 진입 성공 후 실제 홈/설정 포인터 클릭 완료되지 않음; 16초 watchdog으로 차단 · 초기 입력/화면 차폐/동기 렌더링 원인 미확정'},
 {id:'savey-cross-app-family-e2e',priority:'P0',area:'SAVEY',why:'같은 가족의 학습/미션/금융 데이터 앱 간 통합 시나리오 미검증'},
 {id:'administrator-qa-consumption',priority:'P0',area:'TAKY-MOBILE',why:'QA 보고서가 관리자 화면에서 읽혀 조치되는 소비 경로 미검증'},
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
   const startedCheck=Date.now();
   const args=test.id==='independent-learning-specialist-browser-bots'
     ? [file,...test.args] : [...test.args,file];
   // node --test/--check precede file, no additional shell.
   let call, fixtures=[];
   try{
     if(test.id==='mobile-cross-app-browser')fixtures=startFixtures();
     call=spawnSync(node,args,{
       cwd:here,env:{...process.env,TAKY_QA_SYNTHETIC:'1',TAKY_QA_NETWORK:'MOCK_ONLY',TAKY_QA_SEED:process.env.TAKY_QA_SEED||new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Seoul'}).replace(/-/g,''),TAKY_QA_AGENT_STEPS:mode==='deep'?'24':'10'},
       encoding:'utf8',timeout:test.level==='deep'?60000:45000,
       maxBuffer:1024*1024,windowsHide:true
     });
   }catch(error){call={error,status:null,stderr:error.message};}
   finally{stopFixtures(fixtures);}
   const state=call.error?.code==='ETIMEDOUT'?'TIMEOUT':call.error?'ERROR':call.status===0?'PASS':'FAIL';
   results.push({id:test.id,repo:test.repo,state,durationMs:Date.now()-startedCheck,
     ...(state==='PASS'?{}:{reason:safe(call.stderr||call.stdout||call.error?.message||'UNKNOWN_TEST_FAILURE'),exitCode:call.status})});
 }
 const verifiedFiveApp=results.some(r=>r.id==='mobile-cross-app-browser'&&r.state==='PASS');
 const activeGaps=gaps.filter(g=>!(g.id==='multi-specialist-browser-stability'&&verifiedFiveApp));
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
