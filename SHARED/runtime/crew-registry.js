(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyCrewRegistry=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='TAKY_CREW_REGISTRY_V1';
  const ROSTER_CEILING=20;
  const CORE6=Object.freeze([
    Object.freeze({character_id:'crew.core.dubi',canonical_name:'두비',romanized_name:'Dubi',group:'CORE6'}),
    Object.freeze({character_id:'crew.core.lori',canonical_name:'로리',romanized_name:'Lori',group:'CORE6'}),
    Object.freeze({character_id:'crew.core.ink',canonical_name:'잉크',romanized_name:'Ink',group:'CORE6'}),
    Object.freeze({character_id:'crew.core.nova',canonical_name:'노바',romanized_name:'Nova',group:'CORE6'}),
    Object.freeze({character_id:'crew.core.take',canonical_name:'테이크',romanized_name:'Take',group:'CORE6'}),
    Object.freeze({character_id:'crew.core.zero',canonical_name:'제로',romanized_name:'Zero',group:'CORE6'})
  ]);

  const clean=v=>String(v??'').trim();

  function defaultRegistry(member_id=null){
    return Object.freeze({
      crew_registry_contract:VERSION,
      member_id:clean(member_id)||null,
      roster_ceiling:ROSTER_CEILING,
      roster:Object.freeze(CORE6.map(x=>Object.freeze({...x,display_name:x.canonical_name,name_history:Object.freeze([]),encountered:true}))),
      primary_companion_id:null,
      revision:0
    });
  }

  function normalizeMember(input={}){
    const base=CORE6.find(x=>x.character_id===clean(input.character_id));
    if(!base)return null;
    const history=Array.isArray(input.name_history)?input.name_history.map(x=>Object.freeze({
      name:clean(x.name)||null,
      changed_at:x.changed_at||null
    })).filter(x=>x.name):[];
    return Object.freeze({
      ...base,
      display_name:clean(input.display_name)||base.canonical_name,
      name_history:Object.freeze(history),
      encountered:input.encountered!==false
    });
  }

  function normalizeRegistry(input={}){
    const member_id=clean(input.member_id)||null;
    const supplied=Array.isArray(input.roster)?input.roster:[];
    const byId=new Map(supplied.map(x=>[clean(x.character_id),x]));
    const roster=CORE6.map(base=>normalizeMember(byId.get(base.character_id)||base));
    const selected=clean(input.primary_companion_id)||null;
    const selectedValid=roster.some(x=>x.character_id===selected);
    return Object.freeze({
      crew_registry_contract:VERSION,
      member_id,
      roster_ceiling:ROSTER_CEILING,
      roster:Object.freeze(roster),
      primary_companion_id:selectedValid?selected:null,
      revision:Number.isInteger(input.revision)?input.revision:0
    });
  }

  function selectPrimary(input={},characterId){
    const reg=normalizeRegistry(input),id=clean(characterId);
    if(!reg.roster.some(x=>x.character_id===id))return {ok:false,reason:'CREW_MEMBER_NOT_FOUND',registry:reg};
    return {ok:true,registry:normalizeRegistry({...reg,primary_companion_id:id,revision:reg.revision+1})};
  }

  function rename(input={},characterId,newName,changedAt=new Date().toISOString()){
    const reg=normalizeRegistry(input),id=clean(characterId),name=clean(newName);
    if(!name)return {ok:false,reason:'DISPLAY_NAME_REQUIRED',registry:reg};
    const current=reg.roster.find(x=>x.character_id===id);
    if(!current)return {ok:false,reason:'CREW_MEMBER_NOT_FOUND',registry:reg};
    const roster=reg.roster.map(x=>{
      if(x.character_id!==id)return x;
      const history=[...x.name_history,{name:x.display_name,changed_at:changedAt}];
      return {...x,display_name:name,name_history:history};
    });
    return {ok:true,registry:normalizeRegistry({...reg,roster,revision:reg.revision+1})};
  }

  function primary(input={}){
    const reg=normalizeRegistry(input);
    return reg.roster.find(x=>x.character_id===reg.primary_companion_id)||null;
  }

  return Object.freeze({VERSION,ROSTER_CEILING,CORE6,defaultRegistry,normalizeMember,normalizeRegistry,selectPrimary,rename,primary});
});
