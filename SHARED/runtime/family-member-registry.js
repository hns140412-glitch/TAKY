(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyFamilyMemberRegistry=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_FAMILY_MEMBER_REGISTRY_V1';
  const ROLES=new Set(['CHILD','PARENT']);
  const clean=v=>String(v??'').trim();

  function normalizeProfile(input={}){
    return Object.freeze({
      display_name:clean(input.display_name||input.name)||null,
      avatar_ref:clean(input.avatar_ref)||null,
      profile_version:Number.isInteger(input.profile_version)?input.profile_version:1,
      updated_at:input.updated_at||null
    });
  }

  function normalizeMember(input={}){
    const role=clean(input.role).toUpperCase();
    return Object.freeze({
      family_member_contract:VERSION,
      family_id:clean(input.family_id)||null,
      member_id:clean(input.member_id||input.id)||null,
      role:ROLES.has(role)?role:null,
      profile:normalizeProfile(input.profile||input),
      relationship_label:clean(input.relationship_label)||null,
      active:input.active!==false
    });
  }

  function validateMember(input={}){
    const member=normalizeMember(input),issues=[];
    if(!member.family_id)issues.push('FAMILY_ID_REQUIRED');
    if(!member.member_id)issues.push('MEMBER_ID_REQUIRED');
    if(!member.role)issues.push('ROLE_REQUIRED');
    return {ok:issues.length===0,issues,member};
  }

  function normalizeRegistry(input={}){
    const family_id=clean(input.family_id)||null;
    const members=(Array.isArray(input.members)?input.members:[]).map(normalizeMember);
    const dedup=new Map();
    for(const member of members){
      if(!member.member_id)continue;
      if(family_id&&member.family_id&&member.family_id!==family_id)continue;
      dedup.set(member.member_id,member);
    }
    return Object.freeze({
      registry_contract:VERSION,
      family_id,
      members:Object.freeze([...dedup.values()]),
      active_child_id:clean(input.active_child_id)||null,
      revision:Number.isInteger(input.revision)?input.revision:0
    });
  }

  function children(input={}){
    return normalizeRegistry(input).members.filter(m=>m.role==='CHILD'&&m.active);
  }

  function selectActiveChild(input={},memberId){
    const reg=normalizeRegistry(input),id=clean(memberId);
    const child=reg.members.find(m=>m.member_id===id&&m.role==='CHILD'&&m.active);
    if(!child)return {ok:false,reason:'ACTIVE_CHILD_NOT_FOUND',registry:reg};
    return {ok:true,registry:normalizeRegistry({...reg,active_child_id:id})};
  }

  function memberProfile(input={},memberId){
    const reg=normalizeRegistry(input),id=clean(memberId);
    const member=reg.members.find(m=>m.member_id===id);
    return member?.profile||null;
  }

  function minimalProjection(memberInput={}){
    const member=normalizeMember(memberInput);
    return Object.freeze({
      member_id:member.member_id,
      display_name:member.profile.display_name,
      avatar_ref:member.profile.avatar_ref
    });
  }

  return Object.freeze({VERSION,normalizeProfile,normalizeMember,validateMember,normalizeRegistry,children,selectActiveChild,memberProfile,minimalProjection});
});
