/* TAKY Explorer Crew common audio adapter. No provider calls, no audio synthesis.
   Never treat an accepted script/Audio.play() dispatch as proof of audible playback. */
(function (root, factory) {
  const api=factory();
  if (typeof module!=='undefined' && module.exports) module.exports=api;
  else if(root) root.TakyExplorerCrewVoiceConsumer=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_EXPLORER_CREW_VOICE_CONSUMER_V1';
  const SCHEMA='TAKY_EXPLORER_CREW_PLAYBACK_MANIFEST_V1';
  const APPROVED=new Set(['USER_APPROVED','LOCKED']);
  const CORE6=new Set(['dubi','lori','ink','nova','take','zero']);
  const FAMILY_BY_CHARACTER=Object.freeze({
    dubi:'VF01',lori:'VF02',ink:'VF03',nova:'VF05',take:'VF04',zero:'VF06',
    'guide-07':'VF06','guide-08':'VF01','guide-09':'VF03','guide-10':'VF05',
    'guide-11':'VF04','guide-12':'VF02','guide-13':'VF06','guide-14':'VF01',
    'guide-15':'VF06','guide-16':'VF05','guide-17':'VF03','guide-18':'VF02',
    'guide-19':'SP01','guide-20':'SP02','guide-21':'SP03',
    'guide-22':'SP02','guide-23':'SP01','guide-24':'SP03'
  });
  const INTENTS=new Set(['ASK','HINT','ACKNOWLEDGE']);
  const SCOPES=new Set(['MAIN_CREW','PLAY_CAMP']);
  const TEXT_HASH=/^[0-9a-f]{64}$/i;
  const SAFE_VOICE=/^[A-Za-z0-9_-]{10,80}$/;
  const SAFE_URL=/^(?:\.\/|\/)?audio\/explorer-crew\/[A-Za-z0-9_/-]+\.mp3(?:\?v=[0-9a-f]{8,64})?$/;
  const canonicalId=id=>String(id||'').trim().toLowerCase();
  const keyFor=(scope,id,intent,variant)=>[scope,canonicalId(id),intent,variant].join(':');
  const lineKeyFor=(scope,id,intent,variant)=>[canonicalId(id),scope==='MAIN_CREW'?'E5_6':'PLAY_CAMP',intent,variant].join(':');
  function checkManifest(manifest) {
    const problems=[];
    if(!manifest||manifest.schema_version!==SCHEMA||!Array.isArray(manifest.clips))
      return {ok:false,problems:['INVALID_MANIFEST_SCHEMA']};
    const seen=new Map(),urls=new Map();
    for(const c of manifest.clips){
      if(!c||!SCOPES.has(c.scope)||!INTENTS.has(c.intent)||![0,1].includes(c.variant)
        ||!/^VF0[1-6]$|^SP0[1-3]$/.test(c.voice_family||'')
        ||!canonicalId(c.character_id)||!TEXT_HASH.test(c.text_sha256||'')
        ||!TEXT_HASH.test(c.audio_sha256||'')||!SAFE_VOICE.test(c.voice_id||'')
        ||typeof c.exact_text!=='string'||!c.exact_text||!SAFE_URL.test(c.url||'')
        ||!APPROVED.has(c.status)) {
        problems.push('UNPLAYABLE_CLIP_METADATA:'+String(c?.key||'UNKNOWN'));continue;
      }
      const expected=keyFor(c.scope,c.character_id,c.intent,c.variant);
      if(c.key!==expected||c.line_key!==lineKeyFor(c.scope,c.character_id,c.intent,c.variant))
        problems.push('SCRIPT_KEY_MISMATCH:'+String(c.key));
      if(FAMILY_BY_CHARACTER[c.character_id]!==c.voice_family)
        problems.push('CHARACTER_VOICE_FAMILY_MISMATCH:'+String(c.key));
      if(c.scope==='PLAY_CAMP'&&!CORE6.has(c.character_id))
        problems.push('PLAY_CAMP_NON_CORE6:'+c.key);
      if(seen.has(c.key))problems.push('DUPLICATE_SCRIPT_KEY:'+c.key);
      seen.set(c.key,c);
      const previous=urls.get(c.url);
      if(previous && (previous.exact_text!==c.exact_text||previous.voice_id!==c.voice_id||previous.audio_sha256!==c.audio_sha256))
        problems.push('URL_REFERENCES_DIFFERENT_RECORDING:'+c.url);
      urls.set(c.url,c);
    }
    return {ok:problems.length===0,problems};
  }
  function createConsumer(manifest,{AudioCtor=(typeof Audio!=='undefined'?Audio:null),timeoutMs=9000}={}){
    const result=checkManifest(manifest);
    if(!result.ok) throw new Error('INVALID_CREW_AUDIO_MANIFEST: '+result.problems.join(','));
    const clips=new Map(manifest.clips.map(c=>[c.key,c]));
    let active=null,revision=0;
    function resolve(input={}){
      const {scope,character_id,intent,variant,text,line_key,locale='ko-KR',voice_family}=input;
      if(!SCOPES.has(scope)||!INTENTS.has(intent)||![0,1].includes(variant))
        return {ok:false,status:'INVALID_REQUEST'};
      const id=canonicalId(character_id);
      if(scope==='PLAY_CAMP'&&!CORE6.has(id))return {ok:false,status:'SCENE_SCOPE_MISMATCH'};
      if(locale!=='ko-KR')return {ok:false,status:'LOCALE_MISMATCH'};
      const key=keyFor(scope,id,intent,variant);
      const clip=clips.get(key);
      if(!clip)return {ok:false,status:'MISSING_APPROVED_RECORDING',key};
      if(line_key!==clip.line_key || text!==clip.exact_text || voice_family!==clip.voice_family)
        return {ok:false,status:'SCRIPT_VOICE_MISMATCH',key};
      return {ok:true,status:'ROUTE_RESOLVED',key,url:clip.url,voice_id:clip.voice_id,audio_sha256:clip.audio_sha256,clip};
    }
    function stop(){
      revision++;
      if(active){
        const a=active.audio;
        a.pause?.();
        try{a.currentTime=0}catch{}
        active.finish({ok:false,status:'INTERRUPTED',key:active.key});
        active=null;
      }
    }
    function play(input={}){
      const route=resolve(input);
      if(!route.ok) return Promise.resolve(route);
      if(typeof AudioCtor!=='function')
        return Promise.resolve({ok:false,status:'AUDIO_DEVICE_UNAVAILABLE',key:route.key});
      stop();
      const ticket=++revision;
      let audio;
      try {audio=new AudioCtor(route.url)}catch(error){
        return Promise.resolve({ok:false,status:'AUDIO_CONSTRUCTION_FAILED',key:route.key});
      }
      return new Promise(resolvePromise=>{
        let done=false,timer=null;
        const complete=value=>{
          if(done)return;
          done=true;
          if(timer!==null)clearTimeout(timer);
          audio.removeEventListener?.('playing',onPlaying);
          audio.removeEventListener?.('error',onError);
          if(active?.ticket===ticket && !value.ok)active=null;
          resolvePromise(value);
        };
        const onPlaying=()=>{
          if(ticket!==revision){complete({ok:false,status:'INTERRUPTED',key:route.key});return}
          complete({ok:true,status:'PLAYING_STARTED',key:route.key,url:route.url,voice_id:route.voice_id});
        };
        const onError=()=>complete({ok:false,status:'MEDIA_ERROR',key:route.key,error_code:audio.error?.code||null});
        active={ticket,key:route.key,audio,finish:complete};
        audio.addEventListener?.('playing',onPlaying);
        audio.addEventListener?.('error',onError);
        audio.addEventListener?.('ended',()=>{if(active?.ticket===ticket)active=null},{once:true});
        timer=setTimeout(()=>complete({ok:false,status:'PLAYBACK_START_TIMEOUT',key:route.key}),timeoutMs);
        try {
          const promise=audio.play();
          Promise.resolve(promise).catch(()=>complete({ok:false,status:'PLAY_REJECTED',key:route.key}));
        }catch{complete({ok:false,status:'PLAY_REJECTED',key:route.key})}
      });
    }
    return Object.freeze({resolve,play,stop,snapshot:()=>({registered_clips:clips.size,playing:!!active,version:VERSION})});
  }
  return Object.freeze({VERSION,SCHEMA,keyFor,lineKeyFor,checkManifest,createConsumer});
});
