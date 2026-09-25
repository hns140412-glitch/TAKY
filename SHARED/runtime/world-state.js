(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyWorldState=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_WORLD_STATE_V1';
  const PRESENCE=new Set(['WITH_EXPLORER','HUB','DISPATCH','SUPPORT','VACATION','REST','SICK','FREE_EXPLORATION','SPECIAL_EVENT','UNKNOWN']);
  const ENCOUNTER=new Set(['UNDISCOVERED','TRACE','ENCOUNTER_WINDOW','FIRST_MEETING','KNOWN_FRIEND','SELECTABLE_COMPANION','REUNION']);
  const clean=v=>String(v??'').trim();

  function blank(member_id=null){
    return Object.freeze({
      world_state_contract:VERSION,
      member_id:clean(member_id)||null,
      primary_companion_id:null,
      crew_presence:Object.freeze([]),
      relationships:Object.freeze([]),
      special_encounters:Object.freeze([]),
      world_memories:Object.freeze([]),
      revision:0
    });
  }

  function normalizePresence(input={}){
    const state=clean(input.state).toUpperCase();
    return Object.freeze({
      character_id:clean(input.character_id)||null,
      state:PRESENCE.has(state)?state:'UNKNOWN',
      hub_id:clean(input.hub_id)||null,
      since_at:input.since_at||null,
      story_reason:clean(input.story_reason)||null
    });
  }

  function normalizeRelationship(input={}){
    return Object.freeze({
      character_id:clean(input.character_id)||null,
      meaningful_episode_count:Math.max(0,Number(input.meaningful_episode_count)||0),
      last_meaningful_episode_at:input.last_meaningful_episode_at||null,
      memory_refs:Object.freeze(Array.isArray(input.memory_refs)?[...new Set(input.memory_refs.map(clean).filter(Boolean))].slice(-120):[]),
      expression_unlock_refs:Object.freeze(Array.isArray(input.expression_unlock_refs)?[...new Set(input.expression_unlock_refs.map(clean).filter(Boolean))].slice(-40):[]),
      power_effect:null,
      reward_multiplier:null,
      absence_decay:false
    });
  }

  function normalizeEncounter(input={}){
    const state=clean(input.state).toUpperCase();
    return Object.freeze({
      character_id:clean(input.character_id)||null,
      state:ENCOUNTER.has(state)?state:'UNDISCOVERED',
      clue_refs:Object.freeze(Array.isArray(input.clue_refs)?[...new Set(input.clue_refs.map(clean).filter(Boolean))].slice(-40):[]),
      last_event_at:input.last_event_at||null,
      exact_probability:null,
      exact_cadence:null,
      miss_penalty:false,
      power_advantage:false
    });
  }

  function normalize(input={}){
    const member_id=clean(input.member_id)||null;
    const presence=(Array.isArray(input.crew_presence)?input.crew_presence:[]).map(normalizePresence).filter(x=>x.character_id);
    const relationships=(Array.isArray(input.relationships)?input.relationships:[]).map(normalizeRelationship).filter(x=>x.character_id);
    const encounters=(Array.isArray(input.special_encounters)?input.special_encounters:[]).map(normalizeEncounter).filter(x=>x.character_id);
    return Object.freeze({
      world_state_contract:VERSION,
      member_id,
      primary_companion_id:clean(input.primary_companion_id)||null,
      crew_presence:Object.freeze(presence),
      relationships:Object.freeze(relationships),
      special_encounters:Object.freeze(encounters),
      world_memories:Object.freeze(Array.isArray(input.world_memories)?input.world_memories.slice(-200).map(x=>Object.freeze({...x})):[]),
      revision:Number.isInteger(input.revision)?input.revision:0
    });
  }

  function setPresence(input={},next={}){
    const state=normalize(input),p=normalizePresence(next);
    if(!p.character_id)return {ok:false,reason:'CHARACTER_ID_REQUIRED',state};
    const rows=state.crew_presence.filter(x=>x.character_id!==p.character_id);
    rows.push(p);
    return {ok:true,state:normalize({...state,crew_presence:rows,revision:state.revision+1})};
  }

  function recordMeaningfulEpisode(input={},episode={}){
    const state=normalize(input),character_id=clean(episode.character_id),memory_ref=clean(episode.memory_ref);
    if(!character_id||!memory_ref)return {ok:false,reason:'MEANINGFUL_EPISODE_IDENTITY_REQUIRED',state};
    const rows=[...state.relationships];
    const i=rows.findIndex(x=>x.character_id===character_id);
    const current=i>=0?rows[i]:normalizeRelationship({character_id});
    const next=normalizeRelationship({
      ...current,
      meaningful_episode_count:current.meaningful_episode_count+1,
      last_meaningful_episode_at:episode.occurred_at||new Date().toISOString(),
      memory_refs:[...current.memory_refs,memory_ref]
    });
    if(i>=0)rows[i]=next;else rows.push(next);
    return {ok:true,state:normalize({...state,relationships:rows,world_memories:[...state.world_memories,{memory_ref,character_id,occurred_at:episode.occurred_at||new Date().toISOString(),source_event_id:clean(episode.source_event_id)||null}],revision:state.revision+1})};
  }

  function recordRawPresence(input={}){
    // Opening/logging-in alone must not raise affinity.
    return {ok:true,reason:'NO_AFFINITY_MUTATION',state:normalize(input)};
  }

  function setEncounter(input={},next={}){
    const state=normalize(input),enc=normalizeEncounter(next);
    if(!enc.character_id)return {ok:false,reason:'CHARACTER_ID_REQUIRED',state};
    const rows=state.special_encounters.filter(x=>x.character_id!==enc.character_id);
    rows.push(enc);
    return {ok:true,state:normalize({...state,special_encounters:rows,revision:state.revision+1})};
  }

  return Object.freeze({VERSION,PRESENCE_STATES:Object.freeze([...PRESENCE]),ENCOUNTER_STATES:Object.freeze([...ENCOUNTER]),blank,normalize,normalizePresence,normalizeRelationship,normalizeEncounter,setPresence,recordMeaningfulEpisode,recordRawPresence,setEncounter});
});
