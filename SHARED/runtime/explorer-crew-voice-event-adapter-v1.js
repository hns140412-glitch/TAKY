/* TAKY shared Explorer Crew event adapter: app event -> canonical dialogue -> exact approved audio.
   Production does not fall back to arbitrary browser TTS or replay a different role. */
(function(root,factory){
 const api=factory();
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else if(root)root.TakyExplorerCrewVoiceEventAdapter=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const EVENTS=Object.freeze({
  FIRST_MEET:{intent:'GREET'},
  RETURN:{intent:'RECONNECT'},
  ASK:{intent:'ASK'},HINT:{intent:'HINT'},FEEDBACK:{intent:'ACKNOWLEDGE'},
  SCENE:{intent:'ASK',needs_scene:true},MEMORY:{intent:'ASK',needs_memory:true}
 });
 const SUPPORTED_SCENES=new Set(['IDEA','EMOTION','DESCRIPTION','VIEWPOINT','FINAL']);
 function create({personality,bridge,repeatBudget=2}={}){
  if(!personality?.resolve||!bridge?.resolve||!bridge?.play)throw new Error('CANONICAL_DIALOGUE_AND_AUDIO_BRIDGE_REQUIRED');
  const recent=new Map(),eventIds=new Set();
  const trim=t=>typeof t==='string'?t.trim():'';
  function prepare(event={}){
   const kind=EVENTS[event.event_type];
   if(!kind)return {ok:false,status:'EVENT_NOT_MAPPED'};
   if(event.interaction_mode==='SILENT'||event.ambient===true)
    return {ok:false,status:'AMBIENT_DOES_NOT_AUTOPLAY'};
   const id=trim(event.character_id),app=trim(event.app_id);
   if(!id||!app)return {ok:false,status:'CANONICAL_APP_AND_CHARACTER_REQUIRED'};
   const scope=app==='PLAY_CAMP'?'PLAY_CAMP':'MAIN_CREW';
   if(event.event_type==='SCENE'&&!SUPPORTED_SCENES.has(trim(event.scene_id).toUpperCase()))
    return {ok:false,status:'UNSUPPORTED_SCENE'};
   if(event.event_type==='MEMORY'&&!(event.memoryCue?.callback_allowed===true&&trim(event.memoryCue.memory_id)))
    return {ok:false,status:'MEMORY_EVIDENCE_REQUIRED'};
   const memoryKey=app+':'+id+':'+kind.intent;
   const preceding=recent.get(memoryKey)||[];
   if(['ASK','HINT','FEEDBACK'].includes(event.event_type)&&preceding.length>=repeatBudget)
    return {ok:false,status:'RECENT_VARIANTS_EXHAUSTED_USE_NONVOICE_RESPONSE'};
   const args={...event,intent:kind.intent,
    scene_id:event.event_type==='SCENE'?event.scene_id:undefined,
    memoryCue:event.event_type==='MEMORY'?event.memoryCue:undefined,
    recent_line_keys:preceding.slice(-2)};
   const dialogue=personality.resolve(args);
   if(!dialogue?.text)return {ok:false,status:dialogue?.reason||'NO_SCRIPT',dialogue};
   const routeArgs={...args,dialogue,locale:event.locale||'ko-KR'};
   const route=bridge.resolve(routeArgs);
   return {ok:route.ok,status:route.status,key:route.key||null,
    voice_id:route.voice_id||null,text:dialogue.text,dialogue,routeArgs,event_key:memoryKey,scope};
  }
  async function handle(event={}, {play=true}={}){
   const eventId=trim(event.event_id);
   if(eventId&&eventIds.has(eventId))return {ok:false,status:'EVENT_ALREADY_CONSUMED',event_id:eventId};
   const prepared=prepare(event);
   if(!prepared.ok)return prepared;
   if(!play)return {...prepared,status:'PREPARED_FOR_PLAYBACK'};
   const res=await bridge.play(prepared.routeArgs);
   if(res.status==='PLAYING_STARTED'){
    if(eventId){eventIds.add(eventId);if(eventIds.size>1024)eventIds.clear();}
    if(['ASK','HINT','FEEDBACK'].includes(event.event_type)&&prepared.dialogue?.line_key){
     const list=recent.get(prepared.event_key)||[];
     recent.set(prepared.event_key,[...list,prepared.dialogue.line_key].slice(-repeatBudget));
    }
   }
   return {...prepared,ok:res.ok,status:res.status,playback:res};
  }
  function reset(){recent.clear();eventIds.clear();bridge.stop?.();}
  return Object.freeze({prepare,handle,reset,snapshot:()=>({recent_slots:recent.size,events_consumed:eventIds.size})});
 }
 return Object.freeze({EVENTS,create});
});