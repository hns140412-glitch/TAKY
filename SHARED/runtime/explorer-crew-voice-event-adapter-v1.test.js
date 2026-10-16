'use strict';
const fs=require('fs'),path=require('path'),{test}=require('node:test'),assert=require('node:assert/strict');
const work='D:/Git PWA/TAKY/staging/crew_voice_20261012';
const plan=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json'),'utf8'));
const dialogue=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/dialogue-personality-v1.js');
const bridgeLib=require('./explorer-crew-dialogue-voice-bridge-v1.js');
const adapterLib=require('./explorer-crew-voice-event-adapter-v1.js');
const base={app_id:'HIDE_SEEK',presentation_band:'UPPER_PRIMARY',school_stage:'E5',
 relation_state:'COMPANION',affinity:1,character_id:'dubi'};
const make=(audioManifest)=>adapterLib.create({personality:dialogue,
 bridge:bridgeLib.create(plan,{audioManifest})});
test('valid stage + ASK maps actual source script and nine-group voice without audio',()=>{
 const a=make(),result=a.prepare({...base,event_type:'ASK'});
 assert.equal(result.status,'RECORDING_NOT_YET_AVAILABLE');
 assert.ok(result.voice_id);assert.ok(result.key.startsWith('MAIN_CREW:dubi:ASK:'));
 assert.equal(result.dialogue.source,'CHARACTER_GRADE_RELATION_SCRIPT_AUTHORITY');
});
test('real GREET and RETURN resolve same semantic clip without duplicate audio',()=>{
 const a=make(),g=a.prepare({...base,event_type:'FIRST_MEET'}),r=a.prepare({...base,event_type:'RETURN'});
 assert.equal(g.key,'MAIN_CREW:dubi:SIGNATURE');assert.equal(r.key,g.key);
});
test('actual scene resolver routes SOURCE scene to named recording',()=>{
 const a=make();
 for(const scene_id of ['IDEA','EMOTION','DESCRIPTION','VIEWPOINT','FINAL']){
  const r=a.prepare({...base,event_type:'SCENE',scene_id});
  assert.equal(r.key,'MAIN_CREW:dubi:SCENE:'+scene_id);
 }
});
test('real memory event requires evidence',()=>{
 const a=make(),bad=a.prepare({...base,event_type:'MEMORY',
   memoryCue:{callback_allowed:false,event_type:'DISCOVERY',memory_id:'evidence'}});
 assert.equal(bad.status,'MEMORY_EVIDENCE_REQUIRED');
 const ok=a.prepare({...base,event_type:'MEMORY',
   memoryCue:{callback_allowed:true,event_type:'DISCOVERY',memory_id:'real-record'}});
 assert.equal(ok.key,'MAIN_CREW:dubi:MEMORY:DISCOVERY');
});
test('PLAY_CAMP uses strictly its own Core6 variants and does not map 07',()=>{
 const a=make(),camp={...base,app_id:'PLAY_CAMP',presentation_band:'EARLY_EXPLORER',school_stage:'E1'};
 assert.ok(a.prepare({...camp,event_type:'ASK'}).key.startsWith('PLAY_CAMP:dubi:ASK:'));
 const wrong=a.prepare({...camp,character_id:'guide-07',event_type:'ASK'});
 assert.notEqual(wrong.status,'RECORDING_NOT_YET_AVAILABLE');
});
test('unknown event, automatic ambient and noncanonical context do not voice',()=>{
 const a=make();
 assert.equal(a.prepare({...base,event_type:'BREAK'}).status,'EVENT_NOT_MAPPED');
 assert.equal(a.prepare({...base,event_type:'ASK',ambient:true}).status,'AMBIENT_DOES_NOT_AUTOPLAY');
 assert.equal(a.prepare({...base,event_type:'ASK',interaction_mode:'SILENT'}).status,'AMBIENT_DOES_NOT_AUTOPLAY');
});
class MockAudio {
 constructor(url){this.url=url;this.listeners=new Map();this.currentTime=0;}
 addEventListener(e,fn){this.listeners.set(e,fn)}
 removeEventListener(e){this.listeners.delete(e)}
 pause(){}
 play(){queueMicrotask(()=>this.listeners.get('playing')?.());return Promise.resolve()}
}
test('same approved clip event only recorded once and two variants then no forced repeat',async()=>{
 const rows=plan.rows.filter(x=>x.character_id==='dubi'&&x.scope==='MAIN_CREW'&&x.kind==='LOCKED_INTENT'&&x.intent==='ASK');
 const clips=rows.map(x=>({key:x.key,voice_family:x.voice_family,voice_id:x.voice_id,
  exact_text:x.exact_text,text_sha256:x.text_sha256,audio_sha256:'d'.repeat(64),status:'USER_APPROVED',
  url:'./audio/explorer-crew/MAIN_CREW/01/'+x.file_stem+'.mp3?v='+'d'.repeat(12)}));
 const b=bridgeLib.create(plan,{audioManifest:{clips},AudioCtor:MockAudio});
 const a=adapterLib.create({personality:dialogue,bridge:b});
 const first=await a.handle({...base,event_type:'ASK',event_id:'event-001'});
 assert.equal(first.status,'PLAYING_STARTED');
 assert.equal((await a.handle({...base,event_type:'ASK',event_id:'event-001'})).status,'EVENT_ALREADY_CONSUMED');
 const second=await a.handle({...base,event_type:'ASK',event_id:'event-002'});
 assert.equal(second.status,'PLAYING_STARTED');assert.notEqual(first.key,second.key);
 const third=await a.handle({...base,event_type:'ASK',event_id:'event-003'});
 assert.equal(third.status,'RECENT_VARIANTS_EXHAUSTED_USE_NONVOICE_RESPONSE');
});
