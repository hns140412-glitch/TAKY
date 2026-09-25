(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyExplorationEvent=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='TAKY_EXPLORATION_EVENT_V1';
  const clean=v=>String(v??'').trim();
  const CATEGORIES=new Set(['EXECUTION','RETRIEVAL','EXPRESSION','HANDOFF','SUPPORT','SYSTEM']);

  function categoryFor(sourceApp,eventType){
    const app=clean(sourceApp);
    const type=clean(eventType).toUpperCase();
    if(type.includes('HANDOFF')||type==='APP_SWITCH'||type==='APP_RETURN'||type==='APP_ENTERED')return 'HANDOFF';
    if(type.includes('RETRIEVAL')||type.includes('MEMORY'))return 'RETRIEVAL';
    if(type.includes('WRITING')||type.includes('IMAGINATION')||type.includes('EXPRESSION'))return 'EXPRESSION';
    if(type==='HELP_NEEDED'||type.includes('BLOCKED')||type.includes('WAITING'))return 'SUPPORT';
    if(app==='ready-set'||type.includes('TASK')||type.includes('SESSION')||type.includes('LAP'))return 'EXECUTION';
    return 'SYSTEM';
  }

  function normalize(input={}){
    const source_app=clean(input.source_app||input.app)||null;
    const source_event_type=clean(input.source_event_type||input.event_type||input.type)||null;
    const category=clean(input.category).toUpperCase()||categoryFor(source_app,source_event_type);
    return Object.freeze({
      exploration_event_contract:VERSION,
      exploration_event_id:clean(input.exploration_event_id||input.event_id)||null,
      occurred_at:input.occurred_at||new Date().toISOString(),

      family_id:clean(input.family_id)||null,
      member_id:clean(input.member_id||input.child_id)||null,
      actor_member_id:clean(input.actor_member_id)||null,

      assignment_id:clean(input.assignment_id)||null,
      analysis_id:clean(input.analysis_id)||null,
      learning_unit_id:clean(input.learning_unit_id)||null,
      todo_id:clean(input.todo_id)||null,
      session_id:clean(input.session_id)||null,
      task_id:clean(input.task_id)||null,
      lap_id:clean(input.lap_id)||null,

      source_app,
      source_event_type,
      category:CATEGORIES.has(category)?category:'SYSTEM',
      payload:input.payload&&typeof input.payload==='object'?input.payload:{}
    });
  }

  function validate(input={}){
    const event=normalize(input),issues=[];
    if(!event.member_id)issues.push('MEMBER_ID_REQUIRED');
    if(!event.source_app)issues.push('SOURCE_APP_REQUIRED');
    if(!event.source_event_type)issues.push('SOURCE_EVENT_TYPE_REQUIRED');
    if(!event.category)issues.push('CATEGORY_REQUIRED');
    return {ok:issues.length===0,issues,event};
  }

  function fromAppEvent(appEvent={},fallback={}){
    return normalize({
      ...fallback,
      ...appEvent,
      source_app:appEvent.app||appEvent.source_app||fallback.source_app,
      source_event_type:appEvent.type||appEvent.event_type||fallback.source_event_type,
      payload:appEvent.payload||fallback.payload||{}
    });
  }

  function achievementEligible(input={}){
    const checked=validate(input);
    if(!checked.ok)return {ok:false,eligible:false,reason:checked.issues[0],event:checked.event};
    const t=checked.event.source_event_type;
    const eligible=!['UPDATE_APPLY','APP_ENTERED'].includes(t);
    return {ok:true,eligible,reason:eligible?'ELIGIBLE_SIGNAL':'NON_ACHIEVEMENT_SYSTEM_SIGNAL',event:checked.event};
  }

  return Object.freeze({VERSION,CATEGORIES:Object.freeze([...CATEGORIES]),categoryFor,normalize,validate,fromAppEvent,achievementEligible});
});
