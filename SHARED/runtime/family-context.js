(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyFamilyContext=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='TAKY_FAMILY_CONTEXT_V1';
  const ROLES=new Set(['CHILD','PARENT']);
  const clean=v=>String(v??'').trim();
  const upper=v=>clean(v).toUpperCase();

  function anonymousLocal(input={}){
    return Object.freeze({
      family_context_contract:VERSION,
      auth_state:'ANONYMOUS_LOCAL',
      authenticated:false,
      family_id:null,
      member_id:null,
      role:'CHILD',
      session_id:null,
      auth_provider:null,
      source:clean(input.source)||'LOCAL_DEFAULT',
      issued_at:null,
      expires_at:null
    });
  }

  function normalize(input={}){
    const authenticated=input.authenticated===true;
    if(!authenticated) return anonymousLocal(input);

    const role=upper(input.role);
    const family_id=clean(input.family_id)||null;
    const member_id=clean(input.member_id)||null;
    const session_id=clean(input.session_id)||null;
    const auth_provider=clean(input.auth_provider||input.provider)||null;
    return Object.freeze({
      family_context_contract:VERSION,
      auth_state:'AUTHENTICATED_MEMBER',
      authenticated:true,
      family_id,
      member_id,
      role:ROLES.has(role)?role:null,
      session_id,
      auth_provider,
      source:clean(input.source)||'AUTH_ADAPTER',
      issued_at:input.issued_at||null,
      expires_at:input.expires_at||null
    });
  }

  function isExpired(context={},now=Date.now()){
    if(!context.expires_at) return false;
    const t=Date.parse(context.expires_at);
    return Number.isFinite(t)&&t<=now;
  }

  function validate(input={},options={}){
    const context=normalize(input);
    const issues=[];
    if(context.authenticated){
      if(!context.family_id)issues.push('FAMILY_ID_REQUIRED');
      if(!context.member_id)issues.push('MEMBER_ID_REQUIRED');
      if(!context.session_id)issues.push('SESSION_ID_REQUIRED');
      if(!context.role)issues.push('ROLE_REQUIRED');
      if(isExpired(context,options.now??Date.now()))issues.push('SESSION_EXPIRED');
    }else{
      if(context.family_id||context.member_id||context.session_id)issues.push('ANONYMOUS_CONTEXT_MUST_NOT_ASSERT_MEMBER_IDENTITY');
      if(context.role!=='CHILD')issues.push('ANONYMOUS_LOCAL_ROLE_MUST_BE_CHILD');
    }
    return {ok:issues.length===0,issues,context};
  }

  function requireRole(input={},required){
    const checked=validate(input);
    const want=upper(required);
    if(!checked.ok)return {ok:false,reason:checked.issues[0]||'FAMILY_CONTEXT_INVALID',context:checked.context};
    if(want==='PARENT'){
      if(checked.context.authenticated&&checked.context.role==='PARENT')return {ok:true,context:checked.context};
      return {ok:false,reason:'PARENT_AUTH_REQUIRED',context:checked.context};
    }
    if(want==='CHILD'){
      if(checked.context.role==='CHILD')return {ok:true,context:checked.context};
      return {ok:false,reason:'ROLE_NOT_ALLOWED',context:checked.context};
    }
    return {ok:false,reason:'ROLE_NOT_ALLOWED',context:checked.context};
  }

  function identity(input={}){
    const context=normalize(input);
    return Object.freeze({
      family_id:context.family_id,
      member_id:context.member_id,
      role:context.role,
      authenticated:context.authenticated
    });
  }

  function publicContext(input={}){
    const context=normalize(input);
    return Object.freeze({...context});
  }

  return Object.freeze({VERSION,ROLES:Object.freeze([...ROLES]),anonymousLocal,normalize,validate,requireRole,identity,publicContext,isExpired});
});
