/* TAKY Explorer Crew: Canonical runtime dialogue -> production slot -> sound.
   Handles 264 exact static source lines. Does not fabricate speech or copy into apps. */
(function(root,factory){
 const api=factory();
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else if(root)root.TakyExplorerCrewDialogueVoiceBridge=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const SCHEMA='TAKY_EXPLORER_CREW_PRERECORDING_ROUTING_V1';
 const VALID_APPS=Object.freeze({'READY_SET':'READY_SET','ready-set':'READY_SET','ready':'READY_SET',
  'HIDE_SEEK':'HIDE_SEEK','hide-seek':'HIDE_SEEK','hide':'HIDE_SEEK',
  'SNAP_POP':'SNAP_POP','snap-pop':'SNAP_POP','snap':'SNAP_POP',
  'PLAY_CAMP':'PLAY_CAMP','play-camp':'PLAY_CAMP'});
 const CORE6=new Set(['dubi','lori','ink','nova','take','zero']);
 const VALID_LOCK_SOURCES=new Set(['CHARACTER_GRADE_RELATION_SCRIPT_AUTHORITY','PLAY_CAMP_CORE6_SCRIPT_AUTHORITY']);
 const clean=s=>typeof s==='string'?s.trim():'';
 function create(registry,{audioManifest={clips:[]},AudioCtor=typeof Audio!=='undefined'?Audio:null,timeoutMs=9000}={}){
  if(registry?.schema_version!==SCHEMA||!Array.isArray(registry.rows)||registry.rows.length!==264)
   throw new Error('PREPRODUCTION_264_SOURCE_REQUIRED');
  const slots=new Map(),byLineKey=new Map(),audioByKey=new Map();
  for(const r of registry.rows){
   if(slots.has(r.key))throw new Error('DUPLICATE_SOURCE_KEY:'+r.key);
   if(!r.voice_id||!r.exact_text||!r.text_sha256)throw new Error('UNBOUND_SOURCE:'+r.key);
   slots.set(r.key,r);
   if(r.kind==='LOCKED_INTENT'||r.kind==='MEMORY'){
    if(byLineKey.has(r.line_key))throw new Error('DUPLICATE_LINE_KEY:'+r.line_key);
    byLineKey.set(r.line_key,r);
   }
  }
  if(!Array.isArray(audioManifest.clips))throw new Error('INVALID_AUDIO_MANIFEST');
  const urls=new Map();
  for(const a of audioManifest.clips){
   const slot=slots.get(a.key);
   if(!slot||a.voice_id!==slot.voice_id||a.text_sha256!==slot.text_sha256||
     a.exact_text!==slot.exact_text||a.voice_family!==slot.voice_family||
     !['USER_APPROVED','LOCKED'].includes(a.status)||
     !/^[0-9a-f]{64}$/.test(a.audio_sha256||'')||
     !/^(?:\.\/|\/)?audio\/explorer-crew\/[A-Za-z0-9_/-]+\.mp3(?:\?v=[a-f0-9]{8,64})?$/.test(a.url||''))
    throw new Error('RECORDING_MANIFEST_WRONG_SCRIPT_OR_VOICE:'+String(a?.key));
   if(audioByKey.has(a.key))throw new Error('DUPLICATE_AUDIO_KEY:'+a.key);
   const old=urls.get(a.url);
   if(old&&(old.audio_sha256!==a.audio_sha256||old.key!==a.key))
    throw new Error('AUDIO_URL_COLLISION:'+a.url);
   urls.set(a.url,a);audioByKey.set(a.key,a);
  }
  let active=null,epoch=0;
  function resolve({app_id,character_id,intent,scene_id,memoryCue,dialogue,locale='ko-KR'}={}){
   const app=VALID_APPS[app_id],id=clean(character_id),source=clean(dialogue?.source);
   if(!app)return {ok:false,status:'APP_ID_REQUIRED'};
   if(locale!=='ko-KR')return {ok:false,status:'LANGUAGE_NOT_PRODUCED'};
   if(!id||!dialogue||!dialogue.text)return {ok:false,status:'NO_SPOKEN_DIALOGUE'};
   let slot=null;
   if(VALID_LOCK_SOURCES.has(source)){
    slot=byLineKey.get(dialogue.line_key);
    if(!slot||slot.kind!=='LOCKED_INTENT')return {ok:false,status:'RUNTIME_SCRIPT_LINE_UNMAPPED'};
    if(app==='PLAY_CAMP'&&slot.scope!=='PLAY_CAMP')return {ok:false,status:'WRONG_APP_SCOPE'};
    if(app!=='PLAY_CAMP'&&slot.scope!=='MAIN_CREW')return {ok:false,status:'WRONG_APP_SCOPE'};
   }else if(source==='EVIDENCE_BACKED_MEMORY_CALLBACK'){
    if(app==='PLAY_CAMP'||memoryCue?.callback_allowed!==true||!clean(memoryCue?.memory_id))
      return {ok:false,status:'MEMORY_EVIDENCE_REQUIRED'};
    slot=byLineKey.get(dialogue.line_key);
    if(!slot||slot.kind!=='MEMORY'||slot.memory_event!==memoryCue?.event_type)
      return {ok:false,status:'RUNTIME_MEMORY_LINE_UNMAPPED'};
   }else if(source==='APPROVED_BOARD_SIGNATURE'){
    if(!['GREET','RECONNECT'].includes(intent))return {ok:false,status:'WRONG_SIGNATURE_EVENT'};
    if(app==='PLAY_CAMP'&&!CORE6.has(id))return {ok:false,status:'PLAY_CAMP_CORE6_ONLY'};
    slot=slots.get('MAIN_CREW:'+id+':SIGNATURE');
   }else if(source==='SOURCED_CORE6_SCENE_LINE'){
    if(app==='PLAY_CAMP')return {ok:false,status:'MAIN_CREW_SCENE_ONLY'};
    if(!CORE6.has(id))return {ok:false,status:'UNKNOWN_CORE6_SCENE'};
    slot=slots.get('MAIN_CREW:'+id+':SCENE:'+clean(scene_id).toUpperCase());
   }else return {ok:false,status:'UNMAPPED_DIALOGUE_SOURCE'};
   if(!slot||slot.character_id!==id||slot.exact_text!==dialogue.text||!slot.allowed_app_contexts.includes(app))
    return {ok:false,status:'SCRIPT_TO_ASSET_MISMATCH'};
   if(slot.kind==='LOCKED_INTENT'&&slot.intent!==intent)
    return {ok:false,status:'INTENT_MISMATCH'};
   const audio=audioByKey.get(slot.key);
   if(!audio)return {ok:false,status:'RECORDING_NOT_YET_AVAILABLE',key:slot.key,voice_id:slot.voice_id,production_authority:slot.production_authority};
   return {ok:true,status:'APPROVED_RECORDING_RESOLVED',key:slot.key,voice_id:slot.voice_id,url:audio.url,text_sha256:slot.text_sha256,audio_sha256:audio.audio_sha256,slot};
  }
  function stop(){
   epoch++;
   if(active){active.audio.pause?.();try{active.audio.currentTime=0}catch{}
    active.finish({ok:false,status:'INTERRUPTED',key:active.key});active=null;}
  }
  function play(input){
   const r=resolve(input);
   if(!r.ok)return Promise.resolve(r);
   if(!AudioCtor)return Promise.resolve({ok:false,status:'NO_AUDIO_DEVICE',key:r.key});
   stop();const n=++epoch;let sound;
   try{sound=new AudioCtor(r.url)}catch{return Promise.resolve({ok:false,status:'CREATE_AUDIO_FAILED',key:r.key})}
   return new Promise(done=>{
    let finished=false,timer=null;
    const complete=value=>{
     if(finished)return;
     finished=true;if(timer!==null)clearTimeout(timer);
     sound.removeEventListener?.('playing',onPlaying);
     sound.removeEventListener?.('error',onError);
     if(active?.epoch===n && !value.ok)active=null;
     done(value);
    };
    const onPlaying=()=>complete(n===epoch?{ok:true,status:'PLAYING_STARTED',key:r.key,url:r.url}:{ok:false,status:'INTERRUPTED',key:r.key});
    const onError=()=>complete({ok:false,status:'MEDIA_ERROR',key:r.key});
    sound.addEventListener?.('playing',onPlaying);
    sound.addEventListener?.('error',onError);
    sound.addEventListener?.('ended',()=>{if(active?.epoch===n)active=null},{once:true});
    active={epoch:n,key:r.key,audio:sound,finish:complete};
    timer=setTimeout(()=>complete({ok:false,status:'PLAYBACK_TIMEOUT',key:r.key}),timeoutMs);
    try{Promise.resolve(sound.play()).catch(()=>complete({ok:false,status:'PLAY_REJECTED',key:r.key}));}
    catch{complete({ok:false,status:'PLAY_REJECTED',key:r.key})}
   });
  }
  return Object.freeze({resolve,play,stop,snapshot:()=>({source_slots:slots.size,approved_audio:audioByKey.size})});
 }
 return Object.freeze({SCHEMA,VALID_APPS,create});
});