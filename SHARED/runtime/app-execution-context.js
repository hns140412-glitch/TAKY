(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyAppExecutionContext=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='TAKY_APP_EXECUTION_CONTEXT_V1';
  const clean=v=>String(v??'').trim();
  const APP_SET=new Set(['ready-set','hide-seek','snap-pop','']);

  function normalize(input={}){
    const out={
      context_contract:VERSION,
      family_id:clean(input.family_id)||null,
      member_id:clean(input.member_id||input.child_id)||null,
      profile_id:clean(input.profile_id)||null,

      assignment_id:clean(input.assignment_id)||null,
      analysis_id:clean(input.analysis_id)||null,
      learning_unit_id:clean(input.learning_unit_id)||null,
      todo_id:clean(input.todo_id)||null,

      session_id:clean(input.session_id)||null,
      task_id:clean(input.task_id)||null,
      lap_id:clean(input.lap_id)||null,

      source_app:clean(input.source_app||input.from_app)||null,
      target_app:clean(input.target_app)||null,
      return_target:clean(input.return_target)||null
    };
    return Object.freeze(out);
  }

  function merge(base={},incoming={}){
    const a=normalize(base),b=normalize(incoming),next={};
    for(const key of Object.keys(a)){
      if(key==='context_contract'){ next[key]=VERSION; continue; }
      next[key]=b[key]??a[key]??null;
    }
    return normalize(next);
  }

  function validate(input={},options={}){
    const c=normalize(input);
    const issues=[];
    if(!c.member_id)issues.push('MEMBER_ID_REQUIRED');
    if(c.source_app&&!APP_SET.has(c.source_app))issues.push('SOURCE_APP_INVALID');
    if(c.target_app&&!APP_SET.has(c.target_app))issues.push('TARGET_APP_INVALID');

    const linked=options.linked===true||!!c.return_target;
    if(linked){
      if(!c.session_id)issues.push('SESSION_ID_REQUIRED_WHEN_LINKED');
      if(!c.task_id)issues.push('TASK_ID_REQUIRED_WHEN_LINKED');
      if(!c.return_target)issues.push('RETURN_TARGET_REQUIRED_WHEN_LINKED');
    }

    if(c.return_target){
      try{
        const u=new URL(c.return_target,'https://example.invalid/');
        if(!['http:','https:'].includes(u.protocol))issues.push('RETURN_TARGET_PROTOCOL_INVALID');
      }catch{ issues.push('RETURN_TARGET_INVALID'); }
    }

    return {ok:issues.length===0,issues,context:c};
  }

  function toEventContext(input={}){
    const c=normalize(input);
    return {
      family_id:c.family_id,
      member_id:c.member_id,
      profile_id:c.profile_id,
      assignment_id:c.assignment_id,
      analysis_id:c.analysis_id,
      learning_unit_id:c.learning_unit_id,
      todo_id:c.todo_id,
      session_id:c.session_id,
      task_id:c.task_id,
      lap_id:c.lap_id,
      source_app:c.source_app
    };
  }

  function fromSearchParams(search=''){
    const p=search instanceof URLSearchParams?search:new URLSearchParams(String(search||'').replace(/^\?/,''));
    const raw={};
    for(const key of [
      'family_id','member_id','profile_id','assignment_id','analysis_id','learning_unit_id','todo_id',
      'session_id','task_id','lap_id','source_app','from_app','target_app','return_target','child_id'
    ]){
      const v=p.get(key); if(v)raw[key]=v;
    }
    return normalize(raw);
  }

  return Object.freeze({VERSION,normalize,merge,validate,toEventContext,fromSearchParams});
});
