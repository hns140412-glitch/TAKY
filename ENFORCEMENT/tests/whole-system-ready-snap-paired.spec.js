// Pinned two-repository source integration. Real Ready/Snap browser pages on
// separate loopback origins; TEST-ONLY parent/central fixture. This cannot
// demonstrate production Google auth, server receipt, device or deployment.
const {test,expect}=require('@playwright/test');
const READY='http://127.0.0.1:4173/';
const SNAP='http://127.0.0.1:4174/';

test('Ready confirmed Learning Master unit → Planner run → actual Snap scope → HELP_NEEDED return',async({page})=>{
 await page.addInitScript(({ready,snap})=>{
  if(location.origin===new URL(snap).origin){
   globalThis.SnapPopTrustedReadyTargets=[ready];
  }else if(location.origin===new URL(ready).origin){
   globalThis.ReadySetSpecialistTargets={snapPop:snap};
   globalThis.__READY_AUTH_BOOTSTRAP__={
    authenticated:true,family_id:'FIXTURE_FAMILY',member_id:'FIXTURE_PARENT',
    role:'PARENT',session_id:'FIXTURE_PARENT_LOGIN',
    expires_at:'2099-01-01T00:00:00Z',source:'TEST_ONLY'
   };
   document.addEventListener('DOMContentLoaded',()=>{
    const scope={authenticated:true,family_id:'F1',selected_member_id:'CHILD_A'};
    globalThis.__pairedScope=scope;
    globalThis.ReadyCentralLearningRoundtripV01.installBrowserHost({
     eventTarget:globalThis,activeScopeProvider:()=>scope,
     roundtrip:{run:async()=>({ok:false,reason:'TEST_ONLY_NO_LIVE_CENTRAL_ACCOUNT'})},
     resolveRecordOptions:()=>({})
    });
   },{once:true});
  }
 },{ready:READY,snap:SNAP});
 await page.goto(READY,{waitUntil:'load'});
 const start=await page.evaluate(async()=>{
  if(globalThis.ReadySetRev07.snapTargetUrl()!=='http://127.0.0.1:4174/')
   return {ok:false,reason:'SNAP_TARGET_CONFIGURATION_MISSING'};
  const today=new Date().toLocaleDateString('sv-SE');
  const end=new Date();end.setDate(end.getDate()+7);
  const deadline=end.toLocaleDateString('sv-SE');
  ReadySetPlanner.upsertDailyAvailabilityWindow({
   date:today,start:'16:00',end:'17:00',source:'PARENT_CONFIRMED',confirmed:true
  });
  const books=ReadyAssignmentDomainV2.TALENT_BOOKS.map((subject,i)=>({
   subject,source_range:`unit ${i}`
  }));
  const pkg=ReadyAssignments.upsertTalentPackage({
   actor:'PARENT',source_date:today,deadline_boundary:deadline,books
  });
  for(const id of pkg.fact_ids)ReadyAssignments.confirmFact(id,{actor:'PARENT'});
  const accepted=ReadyIntegrationV1.processAssignment(pkg.fact_ids[0],{
   candidate_dates:[today]
  });
  const todo=ReadySetPlanner.snapshot().dated_todos.find(x=>
   x.assignment_id===pkg.fact_ids[0]&&x.source==='PLANNER_V2_ALLOCATION');
  if(!accepted.ok||!todo||todo.date!==today)
   return {ok:false,reason:'CONFIRMED_PLAN_NOT_AVAILABLE',accepted,todo};
  const unit=ReadyAssignments.load().learningUnits[todo.learning_unit_id];
  state.selectedTodoIds=[todo.todo_id];state.targetMin=1;save();
  document.getElementById('startBtn').click();
  return {ok:true,todo_id:todo.todo_id,
   unit_id:unit.learning_unit_id,subject:unit.subject,
   skill:unit.concept_skill_target};
 });
 expect(start.ok).toBe(true);
 await expect.poll(()=>page.evaluate(()=>!!ReadySetRev07.contract()?.active_lap_id))
  .toBe(true);
 const readyRun=await page.evaluate(()=>{
  const c=ReadySetRev07.contract();
  return {session_id:c.session_id,task_id:c.active_task_id,lap_id:c.active_lap_id};
 });
 const snapNavigation=page.waitForURL(url=>url.origin===new URL(SNAP).origin,{
  waitUntil:'load'
 });
 const launched=await page.evaluate(()=>ReadySetRev07.launchSpecialist('snap-pop'));
 expect(launched).toBe(true);
 await snapNavigation;
 await expect.poll(()=>page.evaluate(()=>!!globalThis.SnapPopBridge)).toBe(true);
 const observed=await page.evaluate(()=>{
  const bridge=SnapPopBridge,status=bridge.handoffStatus(),ctx=bridge.context();
  const before=JSON.parse(sessionStorage.getItem('snap_pop_shared_outbox_v1')||'[]').length;
  const mismatch=bridge.emitLearningOutcome({member_id:'CHILD_B',completed:true});
  const after=JSON.parse(sessionStorage.getItem('snap_pop_shared_outbox_v1')||'[]').length;
  const event=bridge.emitLearningOutcome({completed:true,production_ref:'TEST_ONLY_CHILD_EXPRESSIVE_ARTIFACT'});
  return {status,ctx,mismatch:mismatch.reason,noFalseEvent:before===after,
   event:{type:event.event_type,member:event.payload.member_id,
    target:event.payload.learning_target_id,
    subject:event.payload.subject,skill:event.payload.concept_skill_target,
    contextual:event.payload.contextual_evidence_only,
    mastery:event.payload.global_mastery_claim}};
 });
 expect(observed.status.ok).toBe(true);
 expect(observed.status.linked_context_valid).toBe(true);
 expect(observed.status.authenticated).toBe(false);
 expect(observed.ctx.session_id).toBe(readyRun.session_id);
 expect(observed.ctx.task_id).toBe(readyRun.task_id);
 expect(observed.ctx.lap_id).toBe(readyRun.lap_id);
 expect(observed.ctx.child_id).toBe('CHILD_A');
 expect(observed.ctx.learning_target_id).toBe(start.unit_id);
 expect(observed.mismatch).toBe('BOUND_CHILD_ID_MISMATCH');
 expect(observed.noFalseEvent).toBe(true);
 expect(observed.event).toEqual({
  type:'LEARNING_OUTCOME',member:'CHILD_A',target:start.unit_id,
  subject:start.subject,skill:start.skill,contextual:true,mastery:false
 });
 const readyReturn=page.waitForURL(url=>url.origin===new URL(READY).origin,{
  waitUntil:'load'
 });
 await page.evaluate(()=>SnapPopBridge.returnToBase('HELP_NEEDED',{
  child_authored:true,reason:'TEST_ONLY_NEEDS_PARENT'
 }));
 await readyReturn;
 await expect.poll(()=>page.evaluate(()=>
  globalThis.ReadySetRev07?.contract()?.tasks?.[0]?.state))
  .toBe('WAITING_FOR_PARENT');
 const result=await page.evaluate(()=>{
  const c=ReadySetRev07.contract();
  const todo=ReadySetPlanner.snapshot().dated_todos.find(x=>
   x.todo_id===c.tasks[0].planner_todo_id);
  return {state:c.tasks[0].state,todoState:todo?.state,
   sameSession:c.session_id,activeApp:c.active_app,
   parentWait:c.events.some(e=>e.type==='APP_RETURN'&&
     e.payload.task_state==='WAITING_FOR_PARENT')};
 });
 expect(result.state).toBe('WAITING_FOR_PARENT');
 expect(result.todoState).toBe('WAITING_FOR_PARENT');
 expect(result.sameSession).toBe(readyRun.session_id);
 expect(result.activeApp).toBe('ready-set');
 expect(result.parentWait).toBe(true);
});
