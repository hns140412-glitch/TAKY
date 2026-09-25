(function(root,factory){
 const api=factory(); if(typeof module==='object'&&module.exports)module.exports=api; else root.TakyWorldState=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const VERSION='TAKY_WORLD_STATE_V1';
 const STATES=new Set(['AT_HUB','EXPEDITION','SUPPORTING_OTHER_HUB','VACATION','RESTING','FREE_EXPLORING','SPECIAL_EVENT','MAIN_COMPANION']);
 const clean=v=>String(v??'').trim();
 function empty(member_id=null){return Object.freeze({world_state_contract:VERSION,member_id:clean(member_id)||null,crew:Object.freeze({}),events:Object.freeze([]),revision:0,absence_penalty:false,full_daily_simulation:false})}
 function normalize(input={}){
   const crew={};
   for(const [id,row] of Object.entries(input.crew||{})){
     const state=clean(row?.state).toUpperCase();
     if(!STATES.has(state))continue;
     crew[id]=Object.freeze({character_id:id,state,location_ref:clean(row.location_ref)||null,updated_at:row.updated_at||null,source_event_id:clean(row.source_event_id)||null});
   }
   return Object.freeze({world_state_contract:VERSION,member_id:clean(input.member_id)||null,crew:Object.freeze(crew),events:Object.freeze(Array.isArray(input.events)?input.events.slice(-200):[]),revision:Number.isInteger(input.revision)?input.revision:0,absence_penalty:false,full_daily_simulation:false});
 }
 function apply(input={},event={}){
   const w=normalize(input),event_id=clean(event.event_id); if(!event_id)return {ok:false,reason:'WORLD_EVENT_ID_REQUIRED',world:w};
   if(w.events.some(x=>x.event_id===event_id))return {ok:true,reason:'IDEMPOTENT_ALREADY_APPLIED',world:w};
   const type=clean(event.type).toUpperCase(),character_id=clean(event.character_id),next={...w.crew};
   if(['CREW_STATE_SET','SET_MAIN_COMPANION','SPECIAL_EVENT_STARTED','RETURN_REUNION_RECORDED'].includes(type)){
     if(!character_id)return {ok:false,reason:'WORLD_CHARACTER_ID_REQUIRED',world:w};
     let state=clean(event.state).toUpperCase();
     if(type==='SET_MAIN_COMPANION')state='MAIN_COMPANION';
     if(type==='SPECIAL_EVENT_STARTED')state='SPECIAL_EVENT';
     if(type==='RETURN_REUNION_RECORDED'&&!state)state=next[character_id]?.state||'AT_HUB';
     if(!STATES.has(state))return {ok:false,reason:'WORLD_STATE_INVALID',world:w};
     if(type==='SET_MAIN_COMPANION'){
       for(const [id,row] of Object.entries(next))if(id!==character_id&&row.state==='MAIN_COMPANION')next[id]=Object.freeze({...row,state:'AT_HUB',updated_at:event.occurred_at||null,source_event_id:event_id});
     }
     next[character_id]=Object.freeze({character_id,state,location_ref:clean(event.location_ref)||null,updated_at:event.occurred_at||new Date().toISOString(),source_event_id:event_id});
   }else return {ok:false,reason:'WORLD_EVENT_TYPE_UNSUPPORTED',world:w};
   return {ok:true,reason:'APPLIED',world:normalize({member_id:w.member_id,crew:next,events:[...w.events,{event_id,type,character_id,occurred_at:event.occurred_at||new Date().toISOString()}],revision:w.revision+1})};
 }
 function canonicalFromSynthetic(candidate={}){return {ok:false,reason:'SYNTHETIC_WORLD_STATE_NOT_CANONICAL',candidate};}
 return Object.freeze({VERSION,STATES:Object.freeze([...STATES]),empty,normalize,apply,canonicalFromSynthetic});
});