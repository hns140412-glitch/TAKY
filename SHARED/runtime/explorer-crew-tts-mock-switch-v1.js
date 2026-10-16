/* TAKY Explorer Crew voice switch: approved ElevenLabs recording first; otherwise offline TTS mock.
   A mock file is NEVER a user-approved recording. */
(function(root,factory){
 const api=factory(root?.TakyExplorerCrewDialogueVoiceBridge);
 if(typeof module!=='undefined'&&module.exports) module.exports=factory(require('./explorer-crew-dialogue-voice-bridge-v1.js'));
 else if(root)root.TakyExplorerCrewTtsMockSwitch=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(bridgeLib){
 'use strict';
 const VERSION='TAKY_EXPLORER_CREW_TTS_MOCK_SWITCH_V1';
 function create({registry,approvedAudioManifest={clips:[]},mockManifest,AudioCtor=typeof Audio!=='undefined'?Audio:null,timeoutMs=11000}={}){
  if(!bridgeLib?.create)throw new Error('REQUIRES_CANONICAL_SOURCE_VOICE_BRIDGE');
  if(mockManifest?.schema_version!=='TAKY_EXPLORER_CREW_TTS_MOCK_264_V1'||
     mockManifest.clip_count!==264||!Array.isArray(mockManifest.clips)||mockManifest.clips.length!==264)
    throw new Error('REQUIRES_ALL_264_TTS_MOCKS');
  const original=bridgeLib.create(registry,{audioManifest:approvedAudioManifest,AudioCtor,timeoutMs});
  const sourceMap=new Map(registry.rows.map(x=>[x.key,x])),mocks=new Map(),urlOwner=new Map();
  for(const clip of mockManifest.clips){
   const source=sourceMap.get(clip.key);
   if(!source||mocks.has(clip.key)||
     source.character_id!==clip.character_id||source.voice_family!==clip.voice_family||
     source.voice_id!==clip.target_elevenlabs_voice_id||source.text_sha256!==clip.text_sha256||
     source.exact_text!==clip.exact_text||clip.mode!=='TTS_MOCK'||clip.approved_recording!==false||
     !/^[0-9a-f]{64}$/.test(clip.wav_sha256||'')||
     !/^(?:\.\/|\/)?audio\/explorer-crew\/mock\/[A-Za-z0-9_/-]+\.wav(?:\?v=[a-f0-9]{8,64})?$/.test(clip.url||''))
    throw new Error('INVALID_MOCK_OR_UNMATCHED_SOURCE:'+String(clip?.key));
   const owner=urlOwner.get(clip.url);
   if(owner&&owner!==clip.key)throw new Error('TTS_MOCK_URL_COLLISION:'+clip.url);
   urlOwner.set(clip.url,clip.key);
   mocks.set(clip.key,clip);
  }
  if(mocks.size!==264)throw new Error('MISSING_MOCK_AUDIO');
  let current=null,epoch=0;
  function resolve(input){
   const base=original.resolve(input);
   if(base.ok)return {...base,mode:'APPROVED_MP3'};
   if(base.status!=='RECORDING_NOT_YET_AVAILABLE')return base;
   const mock=mocks.get(base.key);
   if(!mock)return {...base,status:'MOCK_NOT_FOUND'};
   return {ok:true,status:'TTS_MOCK_ROUTE_READY',mode:'TTS_MOCK',key:base.key,
    voice_id:mock.target_elevenlabs_voice_id,tts_provider:mock.provider,
    url:mock.url,audio_sha256:mock.wav_sha256,recording_approved:false,mock};
  }
  function stop(){
   epoch++;
   original.stop?.();
   if(current){
    const a=current.audio;
    a.pause?.();
    try{a.currentTime=0}catch{}
    current.complete({ok:false,status:'INTERRUPTED',mode:'TTS_MOCK',key:current.key});
    current=null;
   }
  }
  function playMock(route,{reason=null}={}){
   if(!AudioCtor)return Promise.resolve({ok:false,status:'MOCK_AUDIO_UNAVAILABLE',mode:'TTS_MOCK',key:route.key});
   stop();
   const n=++epoch;
   let audio;
   try{audio=new AudioCtor(route.url)}catch{return Promise.resolve({ok:false,status:'MOCK_AUDIO_CONSTRUCTION_FAILED',mode:'TTS_MOCK',key:route.key})}
   return new Promise(done=>{
    let finished=false,timeout=null;
    const complete=result=>{
     if(finished)return;
     finished=true;
     if(timeout!==null)clearTimeout(timeout);
     audio.removeEventListener?.('playing',onPlaying);
     audio.removeEventListener?.('error',onError);
     if(current?.epoch===n && !result.ok)current=null;
     done(result);
    };
    const onPlaying=()=>complete({ok:true,status:'PLAYING_STARTED',mode:'TTS_MOCK',
      key:route.key,url:route.url,tts_provider:route.tts_provider,recording_approved:false,
      ...(reason?{original_recording_failure:reason}:{})});
    const onError=()=>complete({ok:false,status:'MOCK_AUDIO_ERROR',mode:'TTS_MOCK',key:route.key,
      error_code:audio.error?.code||null});
    current={audio,epoch:n,key:route.key,complete};
    audio.addEventListener?.('playing',onPlaying);
    audio.addEventListener?.('error',onError);
    audio.addEventListener?.('ended',()=>{if(current?.epoch===n)current=null},{once:true});
    timeout=setTimeout(()=>complete({ok:false,status:'MOCK_PLAYBACK_TIMEOUT',mode:'TTS_MOCK',key:route.key}),timeoutMs);
    try{Promise.resolve(audio.play()).catch(()=>complete({ok:false,status:'MOCK_PLAY_REJECTED',mode:'TTS_MOCK',key:route.key}));}
    catch{complete({ok:false,status:'MOCK_PLAY_REJECTED',mode:'TTS_MOCK',key:route.key})}
   });
  }
  async function play(input){
   const route=resolve(input);
   if(!route.ok)return route;
   if(route.mode==='APPROVED_MP3'){
    stop();
    const outcome=await original.play(input);
    if(outcome.ok)return {...outcome,mode:'APPROVED_MP3',recording_approved:true};
    // A failed recorded-asset fetch is not grounds for generating another paid clip.
    const mock=mocks.get(route.key);
    if(!mock)return {...outcome,mode:'APPROVED_MP3',recording_approved:true};
    return playMock({key:mock.key,url:mock.url,tts_provider:mock.provider}, {reason:outcome.status});
   }
   return playMock(route);
  }
  return Object.freeze({VERSION,resolve,play,stop,snapshot:()=>({source_slots:264,mock_files:mocks.size,approved_audio:original.snapshot().approved_audio||0})});
 }
 return Object.freeze({VERSION,create});
});