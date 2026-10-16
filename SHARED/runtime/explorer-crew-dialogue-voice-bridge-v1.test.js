'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const crypto=require('node:crypto'),{test}=require('node:test');
const repo=path.resolve(__dirname,'../..');
const work=path.join(repo,'staging','crew_voice_20261012');
const registry=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json'),'utf8'));
const script=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/dialogue-script-authority-v1.js');
const personality=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/dialogue-personality-v1.js');
const bridge=require('./explorer-crew-dialogue-voice-bridge-v1.js');
const common={app_id:'HIDE_SEEK',presentation_band:'UPPER_PRIMARY',school_stage:'E5',relation_state:'COMPANION',affinity:1};
const camp={...common,app_id:'PLAY_CAMP',presentation_band:'EARLY_EXPLORER',school_stage:'E1'};
const compile=(row)=>{
  let context,dialogue;
  if(row.kind==='LOCKED_INTENT'){
    context={...(row.scope==='PLAY_CAMP'?camp:common),character_id:row.character_id,intent:row.intent,
      recent_line_keys:row.variant===0?[row.character_id+':'+(row.scope==='MAIN_CREW'?'E5_6':'PLAY_CAMP')+':'+row.intent+':1']:[]};
    dialogue=personality.resolve(context);
  }else if(row.kind==='SIGNATURE'){
    context={...common,character_id:row.character_id,intent:'GREET'};
    dialogue=personality.resolve(context);
  }else if(row.kind==='SCENE'){
    context={...common,character_id:row.character_id,intent:'ASK',scene_id:row.scene_id};
    dialogue=personality.resolve(context);
  }else if(row.kind==='MEMORY'){
    context={...common,character_id:row.character_id,intent:'ASK',
      memoryCue:{callback_allowed:true,event_type:row.memory_event,memory_id:'TEST_MEMORY_EVENT'}};
    dialogue=personality.resolve(context);
  }else throw new Error('BAD_ROW_KIND');
  return {context,dialogue};
};
test('all 264 exact canonical runtime responses have unique correct premade audio slots',()=>{
 const b=bridge.create(registry);
 assert.equal(b.snapshot().source_slots,264);
 assert.equal(b.snapshot().approved_audio,0);
 for(const row of registry.rows){
  const {context,dialogue}=compile(row);
  assert.equal(dialogue.text,row.exact_text,row.key+':TEXT');
  const answer=b.resolve({...context,dialogue});
  assert.equal(answer.status,'RECORDING_NOT_YET_AVAILABLE',row.key+':NOT_LINKED');
  assert.equal(answer.key,row.key,row.key+':KEY');
  assert.equal(answer.voice_id,row.voice_id,row.key+':VOICE');
 }
});
test('all R10 source line keys are true runtime keys, never invented',()=>{
 for(const row of registry.rows.filter(x=>x.kind==='LOCKED_INTENT')){
  const {dialogue}=compile(row);
  assert.equal(dialogue.line_key,row.line_key,row.key+':LINE_KEY');
  assert.equal(dialogue.production_group,row.scope,row.key+':PRODUCTION_SCOPE');
 }
});
test('all 30 memory routes refuse unevidenced runtime events',()=>{
 const b=bridge.create(registry);
 for(const row of registry.rows.filter(x=>x.kind==='MEMORY')){
  const context={...common,character_id:row.character_id,intent:'ASK',
    memoryCue:{callback_allowed:false,event_type:row.memory_event,memory_id:'UNVERIFIED'}};
  const d=personality.resolve(context);
  const result=b.resolve({...context,dialogue:d});
  assert.notEqual(result.key,row.key,'false memory selected');
  const evidenced=compile(row);
  assert.equal(b.resolve({...evidenced.context,dialogue:evidenced.dialogue,memoryCue:null}).status,'MEMORY_EVIDENCE_REQUIRED');
 }
});
test('all 30 Core6 scenes must not leak into Play Camp context',()=>{
 const b=bridge.create(registry);
 for(const row of registry.rows.filter(x=>x.kind==='SCENE')){
  const {dialogue}=compile(row);
  const answer=b.resolve({...camp,character_id:row.character_id,intent:'ASK',scene_id:row.scene_id,dialogue});
  assert.equal(answer.status,'MAIN_CREW_SCENE_ONLY');
 }
});
test('GREET and RECONNECT share same single signature recording key',()=>{
 const b=bridge.create(registry);
 for(const row of registry.rows.filter(x=>x.kind==='SIGNATURE')){
  const greet=compile(row),reconnect={...greet.context,intent:'RECONNECT'};
  const d2=personality.resolve(reconnect);
  assert.equal(b.resolve({...greet.context,dialogue:greet.dialogue}).key,row.key);
  assert.equal(b.resolve({...reconnect,dialogue:d2}).key,row.key);
 }
});
test('Core6 signatures can be shared into Play Camp without duplicating recording',()=>{
 const b=bridge.create(registry);
 for(const row of registry.rows.filter(x=>x.kind==='SIGNATURE'&&x.allowed_app_contexts.includes('PLAY_CAMP'))){
  const d=personality.resolve({...camp,character_id:row.character_id,intent:'GREET'});
  assert.equal(b.resolve({...camp,character_id:row.character_id,intent:'GREET',dialogue:d}).key,row.key);
 }
});
test('cannot map foreign text, fabricated source, swapped character or missing locale',()=>{
 const b=bridge.create(registry),row=registry.rows[0],{context,dialogue}=compile(row);
 const mutate={
  dialogue:{...dialogue,text:dialogue.text+' 틀린 대사'},
 };
 assert.equal(b.resolve({...context,...mutate}).status,'SCRIPT_TO_ASSET_MISMATCH');
 assert.equal(b.resolve({...context,character_id:'lori',dialogue}).status,'SCRIPT_TO_ASSET_MISMATCH');
 assert.equal(b.resolve({...context,dialogue:{...dialogue,source:'NON_CANONICAL'}}).status,'UNMAPPED_DIALOGUE_SOURCE');
 assert.equal(b.resolve({...context,dialogue,locale:'en-US'}).status,'LANGUAGE_NOT_PRODUCED');
});
test('no approved audio means no TTS, no false playback success',async()=>{
 const b=bridge.create(registry);
 const row=registry.rows[0],{context,dialogue}=compile(row);
 const result=await b.play({...context,dialogue});
 assert.equal(result.ok,false);
 assert.equal(result.status,'RECORDING_NOT_YET_AVAILABLE');
});
class MockAudio {
 constructor(url){this.url=url;this.handlers=new Map();this.currentTime=0;this.paused=false;}
 addEventListener(evt,fn){this.handlers.set(evt,fn);}
 removeEventListener(evt){this.handlers.delete(evt);}
 pause(){this.paused=true}
 play(){queueMicrotask(()=>this.handlers.get('playing')?.());return Promise.resolve()}
}
test('approved mock entry flows all the way to playing event; generated audio not required',async()=>{
 const row=registry.rows[0],{context,dialogue}=compile(row);
 const a={key:row.key,voice_family:row.voice_family,voice_id:row.voice_id,
  exact_text:row.exact_text,text_sha256:row.text_sha256,audio_sha256:'e'.repeat(64),
  url:'./audio/explorer-crew/MAIN_CREW/01/ASK_0.mp3?v='+'e'.repeat(12),status:'USER_APPROVED'};
 const b=bridge.create(registry,{audioManifest:{clips:[a]},AudioCtor:MockAudio});
 const result=await b.play({...context,dialogue});
 assert.equal(result.status,'PLAYING_STARTED');
 assert.equal(result.key,row.key);
 assert.equal(b.snapshot().approved_audio,1);
});
test('same voice_id but different text cannot point to wrong MP3',()=>{
 const first=registry.rows[0],second=registry.rows.find(x=>x.kind==='LOCKED_INTENT'&&x.character_id==='guide-08');
 assert.equal(first.voice_id,second.voice_id);
 const a={key:first.key,voice_family:first.voice_family,voice_id:first.voice_id,
  exact_text:second.exact_text,text_sha256:first.text_sha256,audio_sha256:'e'.repeat(64),
  url:'./audio/explorer-crew/MAIN_CREW/01/ASK_0.mp3',status:'USER_APPROVED'};
 assert.throws(()=>bridge.create(registry,{audioManifest:{clips:[a]}}),/RECORDING_MANIFEST_WRONG_SCRIPT_OR_VOICE/);
});
const scriptReport={script_rows:registry.rows.length,source_hash:crypto.createHash('sha256').update(JSON.stringify(registry.rows.map(x=>x.text_sha256))).digest('hex'),
 auth_used:'EXPLORER_CREW_V2_SOURCE_LOCK_R10_PLUS_APPROVED_EXTRAS',
 no_elevenlabs_calls:true};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_PREPRODUCTION_RUNTIME_TEST_META.json'),JSON.stringify(scriptReport,null,2));
