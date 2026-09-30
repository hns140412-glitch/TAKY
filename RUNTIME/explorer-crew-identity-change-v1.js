(function(root,factory){
  const api=factory();
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  if(root) root.TakyCrewIdentityChangeV1=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const ALLOWED=new Set(['name','voice','type','id','style']);
  function apply(state={},patch={},meta={}){
    const before=state.guide||{};
    const safe={};
    for(const [k,v] of Object.entries(patch||{}))if(ALLOWED.has(k))safe[k]=v;
    const after={...before,...safe};
    const history=Array.isArray(state.crewIdentityHistory)?[...state.crewIdentityHistory]:[];
    const at=meta.at||new Date().toISOString();
    const authority_ref=meta.authority_ref||'USER_UI';
    if(safe.name!==undefined&&safe.name!==before.name)history.push({kind:'GUIDE_NAME_CHANGED',from:before.name||null,to:safe.name||null,at,authority_ref});
    const oldId=before.type??before.id, newId=safe.type??safe.id;
    if(newId!==undefined&&newId!==oldId)history.push({kind:'GUIDE_CHARACTER_CHANGED',from:oldId||null,to:newId||null,at,authority_ref});
    if(safe.voice!==undefined&&safe.voice!==before.voice)history.push({kind:'GUIDE_VOICE_CHANGED',from:before.voice||null,to:safe.voice||null,at,authority_ref});
    return Object.freeze({...state,guide:Object.freeze(after),crewIdentityHistory:Object.freeze(history)});
  }
  return Object.freeze({apply,allowedFields:Object.freeze([...ALLOWED]),historyResetAllowed:false});
});
