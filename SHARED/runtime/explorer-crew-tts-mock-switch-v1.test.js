'use strict';
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),crypto=require('crypto'),{test}=require('node:test');
const work='D:/Git PWA/TAKY/staging/crew_voice_20261012';
const reg=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json')));
const mock=JSON.parse(fs.readFileSync(path.join(work,'mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json')));
const switcher=require('./explorer-crew-tts-mock-switch-v1.js');
const registry=new Map(reg.rows.map(x=>[x.key,x]));
const source={
 LOCKED_INTENT:r=>({source:r.scope==='PLAY_CAMP'?'PLAY_CAMP_CORE6_SCRIPT_AUTHORITY':'CHARACTER_GRADE_RELATION_SCRIPT_AUTHORITY',line_key:r.line_key,text:r.exact_text}),
 SIGNATURE:r=>({source:'APPROVED_BOARD_SIGNATURE',text:r.exact_text}),
 SCENE:r=>({source:'SOURCED_CORE6_SCENE_LINE',text:r.exact_text}),
 MEMORY:r=>({source:'EVIDENCE_BACKED_MEMORY_CALLBACK',line_key:r.line_key,text:r.exact_text})
};
function args(row){return {
 app_id:row.scope==='PLAY_CAMP'?'PLAY_CAMP':'HIDE_SEEK',character_id:row.character_id,
 intent:row.kind==='SIGNATURE'?'GREET':row.kind==='MEMORY'?'ASK':row.intent||'ASK',
 scene_id:row.scene_id, memoryCue:row.kind==='MEMORY'?{callback_allowed:true,event_type:row.memory_event,memory_id:'real-evidence'}:undefined,
 locale:'ko-KR',dialogue:source[row.kind](row)
}}
class TestAudio{
 static urls=[];
 constructor(url){this.url=url;this.listeners={};this.error=null;this.currentTime=0;TestAudio.urls.push(url);}
 addEventListener(k,v){(this.listeners[k]??=[]).push(v);}
 removeEventListener(k,v){this.listeners[k]=(this.listeners[k]||[]).filter(x=>x!==v)}
 pause(){}
 play(){queueMicrotask(()=>this.listeners.playing?.forEach(fn=>fn()));return Promise.resolve();}
}
test('all 264 generated wav audio files, SHA and exact voice target are valid',()=>{
 assert.equal(mock.clip_count,264);assert.equal(reg.rows.length,264);
 assert.equal(new Set(mock.clips.map(x=>x.key)).size,264);
 assert.equal(new Set(mock.clips.map(x=>x.wav_sha256)).size,264);
 for(const m of mock.clips){
  const r=registry.get(m.key);assert.ok(r,m.key);assert.equal(m.exact_text,r.exact_text);
  assert.equal(m.target_elevenlabs_voice_id,r.voice_id);assert.equal(m.text_sha256,r.text_sha256);
  const p=path.join(work,'mock_tts',m.relative_path);
  assert.ok(fs.existsSync(p),m.key);
  const b=fs.readFileSync(p);assert.equal(b.toString('ascii',0,4),'RIFF');
  assert.equal(b.toString('ascii',8,12),'WAVE');
  assert.equal(crypto.createHash('sha256').update(b).digest('hex'),m.wav_sha256);
 }
});
test('all 264 source routes return TTS_MOCK unless approved MP3 exists',()=>{
 const s=switcher.create({registry:reg,mockManifest:mock,AudioCtor:TestAudio});
 for(const row of reg.rows){
  const route=s.resolve(args(row));
  assert.equal(route.mode,'TTS_MOCK',row.key);
  assert.equal(route.key,row.key);
  assert.equal(route.recording_approved,false);
 }
 assert.equal(s.snapshot().mock_files,264);
});
test('mock plays with actual browser playing event; clearly labels provenance',async()=>{
 TestAudio.urls.length=0;
 const s=switcher.create({registry:reg,mockManifest:mock,AudioCtor:TestAudio});
 const r=await s.play(args(reg.rows[0]));
 assert.equal(r.status,'PLAYING_STARTED');assert.equal(r.mode,'TTS_MOCK');
 assert.equal(r.recording_approved,false);
 assert.ok(TestAudio.urls[0].endsWith('.wav?v='+mock.clips[0].wav_sha256.slice(0,12)));
});
test('when one approved MP3 appears, only that key replaces WAV automatically',async()=>{
 const row=reg.rows[0],sha='c'.repeat(64);
 const approved={clips:[{
  key:row.key,voice_family:row.voice_family,voice_id:row.voice_id,exact_text:row.exact_text,
  text_sha256:row.text_sha256,audio_sha256:sha,status:'USER_APPROVED',
  url:'./audio/explorer-crew/MAIN_CREW/01/ASK_0.mp3?v='+sha.slice(0,12)
 }]};
 const s=switcher.create({registry:reg,mockManifest:mock,approvedAudioManifest:approved,AudioCtor:TestAudio});
 assert.equal(s.resolve(args(row)).mode,'APPROVED_MP3');
 assert.equal(s.resolve(args(reg.rows[1])).mode,'TTS_MOCK');
 const r=await s.play(args(row));
 assert.equal(r.status,'PLAYING_STARTED');assert.equal(r.mode,'APPROVED_MP3');
 assert.equal(r.recording_approved,true);
});
test('cannot silently say approved for malformed or wrong recorded data',()=>{
 const row=reg.rows[0],sha='d'.repeat(64);
 assert.throws(()=>switcher.create({registry:reg,mockManifest:mock,approvedAudioManifest:{clips:[{
 key:row.key,voice_family:row.voice_family,voice_id:row.voice_id,exact_text:'WRONG',
 text_sha256:row.text_sha256,audio_sha256:sha,status:'USER_APPROVED',
 url:'./audio/explorer-crew/MAIN_CREW/01/ASK_0.mp3?v='+sha.slice(0,12)}]}}),
 /RECORDING_MANIFEST_WRONG_SCRIPT_OR_VOICE/);
});
test('wrong user intent or source cannot get a TTS mock via a different key',()=>{
 const s=switcher.create({registry:reg,mockManifest:mock,AudioCtor:TestAudio}),row=reg.rows[0];
 assert.equal(s.resolve({...args(row),dialogue:{source:'UNKNOWN',text:row.exact_text}}).ok,false);
 assert.equal(s.resolve({...args(row),character_id:'lori'}).ok,false);
});
