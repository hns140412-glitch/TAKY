(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyStorageScope=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_FAMILY_MEMBER_STORAGE_SCOPE_V1';
  const clean=v=>String(v??'').trim();
  const enc=v=>encodeURIComponent(clean(v));

  function identity(session={}){
    const authenticated=session?.authenticated===true;
    const family_id=clean(session?.family_id)||null;
    const member_id=clean(session?.member_id)||null;
    if(authenticated&&family_id&&member_id){
      return Object.freeze({
        scope_contract:VERSION,
        mode:'AUTHENTICATED_MEMBER',
        family_id,
        member_id,
        identity_key:'family/'+enc(family_id)+'/member/'+enc(member_id)
      });
    }
    return Object.freeze({
      scope_contract:VERSION,
      mode:'ANONYMOUS_LOCAL',
      family_id:null,
      member_id:null,
      identity_key:'local/anonymous'
    });
  }

  function snapshotScope(logicalScope,session={}){
    const logical=clean(logicalScope);
    if(!logical) throw new TypeError('LOGICAL_SCOPE_REQUIRED');
    const id=identity(session);
    return id.identity_key+'/scope/'+enc(logical);
  }

  function storageKey(logicalScope,legacyKey,session={}){
    const logical=clean(logicalScope);
    if(!logical) throw new TypeError('LOGICAL_SCOPE_REQUIRED');
    const legacy=clean(legacyKey);
    if(!legacy) throw new TypeError('LEGACY_KEY_REQUIRED');
    const id=identity(session);
    if(id.mode==='ANONYMOUS_LOCAL') return legacy;
    return legacy+'::'+id.identity_key;
  }

  function belongsTo(snapshotScopeValue,logicalScope,session={}){
    return clean(snapshotScopeValue)===snapshotScope(logicalScope,session);
  }

  function validate(session={}){
    const id=identity(session);
    const issues=[];
    if(session?.authenticated===true&&id.mode!=='AUTHENTICATED_MEMBER') issues.push('AUTHENTICATED_SCOPE_REQUIRES_FAMILY_AND_MEMBER');
    return {ok:issues.length===0,issues,identity:id};
  }

  return Object.freeze({VERSION,identity,snapshotScope,storageKey,belongsTo,validate});
});
