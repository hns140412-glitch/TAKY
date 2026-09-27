// Cross-origin actual Ready Draft #100 ↔ Hide V2 Draft #12 with TEST-ONLY
// central host and browser-stored original mission. NOT Google authentication,
// an installed mobile test, a verified recall receipt or canonical promotion.
const {test,expect}=require('@playwright/test');
const READY='http://127.0.0.1:4173/';
const HIDE='http://127.0.0.1:4175/v2.html';

test('Real central Planner lexical directive → actual Hide V2 scoped source → partial browser fragment → Ready same task',async({page})=>{
 await page.addInitScript(({ready,hide})=>{
  const origin=location.origin;
  if(origin===new URL(hide).origin){
   globalThis.HideV2TrustedReadyOrigins=[new URL(ready).origin];
   const word=(id,lexicalId,token)=>({
    id,lexicalId,token,meaning:token+' 뜻',languageDomain:'ENGLISH',
    missionRole:'REVIEW',evidence:[],source:{}
   });
   const source={id:'source-authored-words',title:'Original review source',
    status:'READY',createdAt:'2026-09-27T00:00:00Z',
    updatedAt:'2026-09-27T00:00:00Z',sourceCount:1,
    provenance:{source:'TEST_ORIGINAL_CHILD_WORDS'},
    items:[word('a','a::뜻','a'),word('b','b::뜻','b'),
           word('extra','extra::뜻','extra')]};
   localStorage.setItem('hide_seek_v2_state',JSON.stringify({
    version:1,profile:{displayName:'연결 검증'},missions:[source],
    activeMissionId:source.id,activeSession:null,events:[],
    updatedAt:'2026-09-27T00:00:00Z'
   }));
  }else if(origin===new URL(ready).origin){
   document.addEventListener('DOMContentLoaded',()=>{
    const scope={authenticated:true,family_id:'F1',selected_member_id:'CHILD_A'};
    globalThis.__pairedCentralScope=scope;
    globalThis.ReadyCentralLearningRoundtripV01.installBrowserHost({
     eventTarget:globalThis,activeScopeProvider:()=>scope,
     roundtrip:{run:async()=>({ok:false,reason:'TEST_ONLY_NO_LIVE_CENTRAL_ACCOUNT'})},
     resolveRecordOptions:()=>({})
    });
   },{once:true});
  }
 },{ready:READY,hide:HIDE});
 await page.goto(READY,{waitUntil:'load'});
 const setup=await page.evaluate(({hide})=>{
  window.ReadySetSpecialistTargets={hideSeekV2:hide};
  const today=new Date(),date=[today.getFullYear(),
   String(today.getMonth()+1).padStart(2,'0'),
   String(today.getDate()).padStart(2,'0')].join('-');
  ReadySetPlanner.upsertDailyAvailabilityWindow({
   date,start:'16:00',end:'17:00',source:'PARENT_CONFIRMED',confirmed:true
  });
  const member='CHILD_A',subject='english',concept_skill_target='vocabulary';
  const scope={member_id:member,subject,concept_skill_target};
  const intent={ok:true,authority:'CENTRAL_PEDAGOGICAL_INTENT_ONLY',
   scope,receipt_scope:{family_id:'F1',member_id:member},
   actions:[{intent:'RETRIEVAL_CHECKPOINT',basis:['HIDE_MEMORY_ADVISORY_ONLY']}],
   adaptive_plan:{ok:true,authority:'LEARNING_ADAPTIVE_PLAN_INTENT_ONLY',
    adaptive_plan_contract:'TAKY_ADAPTIVE_PLAN_INTENT_V1',scope,
    add_checkpoint:true,add_retrieval_checkpoint:true,unit_span_policy:'REDUCE',
    assistance_policy:'FADE_GRADUALLY',target_learning_ids:['a::뜻','b::뜻']},
   trace:{verified_receipt_id:null,verified_evidence_count:0,
    basis_kind:'OBSERVATION_ADVISORY_ONLY',observation_review_evidence_count:1,
    observation_review_evidence_ids:['fixture-observation'],
    observation_review_digest_sha256:'a'.repeat(64)}};
  const planned=ReadyCentralIntentToPlannerV01.planAccepted(
   intent,ReadySetPlanner,{activeSession:globalThis.__pairedCentralScope,candidate_dates:[date]});
  if(!planned.ok)return {ok:false,planned};
  state.selectedTodoIds=[planned.todo.todo_id];state.targetMin=1;save();
  document.getElementById('startBtn').click();
  return {ok:true,todo_id:planned.todo.todo_id};
 },{hide:HIDE});
 expect(setup.ok).toBe(true);
 await expect.poll(()=>page.evaluate(()=>!!ReadySetRev07.contract()?.active_lap_id)).toBe(true);
 const before=await page.evaluate(()=>{
  const c=ReadySetRev07.contract(),t=c.tasks[0];
  return {session_id:c.session_id,task_id:t.task_id,lap_id:c.active_lap_id,
   directive:t.review_directive,source:t.central_checkpoint};
 });
 expect(before.source).toBe(true);
 expect(before.directive.lexicalIds).toEqual(['a::뜻','b::뜻']);
 const hideNavigation=page.waitForURL(url=>url.origin===new URL(HIDE).origin&&url.pathname==='/v2.html',{waitUntil:'load'});
 expect(await page.evaluate(()=>ReadySetRev07.launchSpecialist('hide-seek'))).toBe(true);
 await hideNavigation;
 await expect.poll(()=>page.evaluate(()=>!!globalThis.HideV2ReadyBridge)).toBe(true);
 const started=await page.evaluate(()=>{
  const pre=HideV2ReadyBridge.resolveTargetMission();
  const r=HideV2App.start(),s=HideV2Store.snapshot();
  const projected=HideV2ReadyBridge.buildResult();
  return {pre:{ok:pre.ok,id:pre.mission?.id,targets:pre.targetItemIds},
    start:r,session:s.activeSession,sourceCount:s.missions.length,
    projection:{state:projected.taskState,lexical:projected.reviewedLexicalIds,
      memoryOwner:projected.memorySummary?.reviewPolicyOwner,
      scoped:projected.memorySummary?.scopedItemIds,
      verified:projected.reviewDirective?.observationIsVerifiedProof}};
 });
 expect(started.pre.ok).toBe(true);
 expect(started.pre.id).toBe('source-authored-words');
 expect(started.pre.targets).toEqual(['a','b']);
 expect(started.start.ok).toBe(true);
 expect(started.session.readyChildId).toBe('CHILD_A');
 expect(started.session.readySessionId).toBe(before.session_id);
 expect(started.session.readyTaskId).toBe(before.task_id);
 expect(started.session.readyLapId).toBe(before.lap_id);
 expect(started.session.queue).toEqual(['a','b']);
 expect(started.sourceCount).toBe(1);
 expect(started.projection.state).toBe('PARTIAL');
 expect(started.projection.lexical).toEqual(['a::뜻','b::뜻']);
 expect(started.projection.scoped).toEqual(['a','b']);
 expect(started.projection.memoryOwner).toBe('TAKY_LEARNING_ENGINE_CORE');
 expect(started.projection.verified).toBe(false);
 const readyNavigation=page.waitForURL(url=>url.origin===new URL(READY).origin,{waitUntil:'load'});
 await page.evaluate(()=>HideV2ReadyBridge.returnToReady());
 await readyNavigation;
 const ret=await page.evaluate(()=>{
  const c=ReadySetRev07.contract(),t=c.tasks[0];
  const todo=ReadySetPlanner.snapshot().dated_todos.find(x=>x.todo_id===t.planner_todo_id);
  return {session:c.session_id,task:t.task_id,state:t.state,
   todoState:todo?.state,activeApp:c.active_app,
   centralProof:t.specialist_result?.rawResult?.reviewDirective?.observationIsVerifiedProof,
   lexical:t.specialist_result?.rawResult?.reviewedLexicalIds,
   query:location.search,fragment:location.hash,
   duplicateEvent:c.applied_event_ids?.length||0};
 });
 expect(ret.session).toBe(before.session_id);
 expect(ret.task).toBe(before.task_id);
 expect(ret.state).toBe('PARTIAL');
 expect(ret.todoState).toBe('PARTIAL');
 expect(ret.activeApp).toBe('ready-set');
 expect(ret.centralProof).toBe(false);
 expect(ret.lexical).toEqual(['a::뜻','b::뜻']);
 expect(ret.query).not.toContain('learning_event');
 expect(ret.fragment).not.toContain('learning_event');
 expect(ret.duplicateEvent).toBe(1);
});
