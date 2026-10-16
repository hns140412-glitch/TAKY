"use strict";
const {test}=require('node:test');
const assert=require('node:assert/strict');
const C=require('./explorer-crew-voice-consumer-v1.js');
const SHA1='a'.repeat(64),SHA2='b'.repeat(64),SHA3='c'.repeat(64);
const voice='abcdefghijABCDEFGHIJ';
const row=(scope,id,voice_family,variant,text,hash,voice_id=voice)=>({
 key:C.keyFor(scope,id,'ASK',variant),
 line_key:C.lineKeyFor(scope,id,'ASK',variant),
 scope,character_id:id,voice_family,voice_id,locale:'ko-KR',intent:'ASK',variant,
 exact_text:text,text_sha256:hash,audio_sha256:hash,
 url:'./audio/explorer-crew/'+scope+'/01/ASK_'+variant+'_'+id+'.mp3?v='+hash.slice(0,12),
 status:'USER_APPROVED'
});
const a=row('MAIN_CREW','dubi','VF01',0,'먼저 살펴볼까?',SHA1);
const b=row('MAIN_CREW','guide-08','VF01',0,'같이 가보자!',SHA2);
const c=row('PLAY_CAMP','dubi','VF01',0,'탐험하자!',SHA3);
const mk=m=>({schema_version:C.SCHEMA,clips:m});
const args=r=>({scope:r.scope,character_id:r.character_id,intent:r.intent,variant:r.variant,
 line_key:r.line_key,text:r.exact_text,voice_family:r.voice_family,locale:r.locale});
test('9-group design keeps character-specific lines despite shared provider ID',()=>{
 const m=mk([a,b,c]),v=C.checkManifest(m);
 assert.deepEqual(v,{ok:true,problems:[]});
 const p=C.createConsumer(m,{AudioCtor:null});
 const x=p.resolve(args(a)),y=p.resolve(args(b));
 assert.equal(x.ok,true);assert.equal(y.ok,true);
 assert.equal(x.voice_id,y.voice_id);assert.notEqual(x.key,y.key);assert.notEqual(x.url,y.url);
});
test('rejects wrong text for otherwise valid character and key',()=>{
 const p=C.createConsumer(mk([a]),{AudioCtor:null});
 assert.equal(p.resolve({...args(a),text:'다른 대사'}).status,'SCRIPT_VOICE_MISMATCH');
});
test('rejects wrong voice family or source line key',()=>{
 const p=C.createConsumer(mk([a]),{AudioCtor:null});
 assert.equal(p.resolve({...args(a),voice_family:'VF02'}).status,'SCRIPT_VOICE_MISMATCH');
 assert.equal(p.resolve({...args(a),line_key:'dubi:E5_6:ASK:1'}).status,'SCRIPT_VOICE_MISMATCH');
});
test('does not swap variant, character or scope silently',()=>{
 const p=C.createConsumer(mk([a,c]),{AudioCtor:null});
 assert.equal(p.resolve({...args(a),variant:1}).status,'MISSING_APPROVED_RECORDING');
 assert.equal(p.resolve({...args(a),character_id:'lori'}).status,'MISSING_APPROVED_RECORDING');
 assert.equal(p.resolve({...args(a),scope:'PLAY_CAMP'}).status,'SCRIPT_VOICE_MISMATCH');
});
test('Play Camp scene is restricted to Core6 without touching Play Camp app',()=>{
 const p=C.createConsumer(mk([a,c]),{AudioCtor:null});
 assert.equal(p.resolve({...args(b),scope:'PLAY_CAMP'}).status,'SCENE_SCOPE_MISMATCH');
 assert.equal(p.resolve({...args(c),locale:'en-US'}).status,'LOCALE_MISMATCH');
});
test('candidate, unverified id, dangerous URL and missing hash fail at load',()=>{
 for(const bad of [{...a,status:'CANDIDATE'},
                    {...a,voice_id:''},
                    {...a,url:'file:///D:/audio.mp3'},
                    {...a,audio_sha256:null}]){
   assert.equal(C.checkManifest(mk([bad])).ok,false);
   assert.throws(()=>C.createConsumer(mk([bad])),/INVALID_CREW_AUDIO_MANIFEST/);
 }
});
test('duplicate key and URL collisions are detected',()=>{
 assert.equal(C.checkManifest(mk([a,{...a}])).ok,false);
 const collision={...b,url:a.url};
 assert.equal(C.checkManifest(mk([a,collision])).ok,false);
});
test('unexpected Core6-only scene and bad script keys are rejected',()=>{
 assert.equal(C.checkManifest(mk([{...b,scope:'PLAY_CAMP',key:C.keyFor('PLAY_CAMP',b.character_id,'ASK',0),line_key:C.lineKeyFor('PLAY_CAMP',b.character_id,'ASK',0)}])).ok,false);
 assert.equal(C.checkManifest(mk([{...a,key:'bad'}])).ok,false);
});
test('zero approved manifest returns truthful missing audio',async()=>{
 const p=C.createConsumer(mk([]),{AudioCtor:null});
 assert.equal((await p.play(args(a))).status,'MISSING_APPROVED_RECORDING');
 assert.equal(p.snapshot().registered_clips,0);
});
class FakeAudio{
 static created=[];
 constructor(url){this.url=url;this.handlers={};this.currentTime=0;this.paused=false;this.error=null;FakeAudio.created.push(this);}
 addEventListener(name,callback){(this.handlers[name]??=[]).push(callback);}
 removeEventListener(name,callback){this.handlers[name]=(this.handlers[name]||[]).filter(x=>x!==callback);}
 emit(name){for(const cb of this.handlers[name]||[])cb();}
 pause(){this.paused=true;}
 play(){queueMicrotask(()=>this.emit('playing'));return Promise.resolve();}
}
test('playback started is reported only after browser playing event',async()=>{
 FakeAudio.created.length=0;
 const p=C.createConsumer(mk([a,b]),{AudioCtor:FakeAudio});
 const res=await p.play(args(a));
 assert.equal(res.status,'PLAYING_STARTED');assert.equal(res.ok,true);
 assert.equal(FakeAudio.created[0].url,a.url);
 await p.play(args(b));
 assert.equal(FakeAudio.created[0].paused,true);
 assert.equal(FakeAudio.created[0].currentTime,0);
 p.stop();assert.equal(FakeAudio.created[1].paused,true);
});
test('play promise rejection is never a success',async()=>{
 class Reject extends FakeAudio{play(){return Promise.reject(new Error('Autoplay blocked'));}}
 const p=C.createConsumer(mk([a]),{AudioCtor:Reject});
 assert.equal((await p.play(args(a))).status,'PLAY_REJECTED');
});
test('media error is not reported as playing',async()=>{
 class Broken extends FakeAudio{play(){queueMicrotask(()=>{this.error={code:4};this.emit('error')});return Promise.resolve();}}
 const p=C.createConsumer(mk([a]),{AudioCtor:Broken});
 const res=await p.play(args(a));assert.equal(res.status,'MEDIA_ERROR');assert.equal(res.error_code,4);
});
test('dispatched play without playing event must timeout, not pass',async()=>{
 class NoEvent extends FakeAudio{play(){return Promise.resolve();}}
 const p=C.createConsumer(mk([a]),{AudioCtor:NoEvent,timeoutMs:10});
 assert.equal((await p.play(args(a))).status,'PLAYBACK_START_TIMEOUT');
});
test('interrupted playback cannot later return success',async()=>{
 class Slow extends FakeAudio{play(){return Promise.resolve();}}
 const p=C.createConsumer(mk([a]),{AudioCtor:Slow,timeoutMs:200});
 const promise=p.play(args(a));p.stop();
 assert.equal((await promise).status,'INTERRUPTED');
});
test('app must not claim playback without audio capability',async()=>{
 const p=C.createConsumer(mk([a]),{AudioCtor:null});
 assert.equal((await p.play(args(a))).status,'AUDIO_DEVICE_UNAVAILABLE');
});
