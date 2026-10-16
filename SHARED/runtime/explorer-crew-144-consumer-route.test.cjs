'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const repo='D:/Git PWA/TAKY';
const reg=JSON.parse(fs.readFileSync(repo+'/staging/crew_voice_20261012/EXPLORER_CREW_PRERECORDING_ROUTING_264.json','utf8'));
const mock=JSON.parse(fs.readFileSync(repo+'/staging/crew_voice_20261012/mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json','utf8'));
const person=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/dialogue-personality-v1.js');
const switcher=require('./explorer-crew-tts-mock-switch-v1.js');
const adapter=require('./explorer-crew-voice-event-adapter-v1.js');
const owner=require('./explorer-crew-content-owner-v1.js');
const cast=[...new Set(reg.rows.map(r=>r.character_id))];
function make(app){return adapter.create({personality:owner.create(person,{app_id:app}),bridge:switcher.create({registry:reg,mockManifest:mock,AudioCtor:null})});}
test('24 companions x 3 apps x 7 real/unknown learner stages: same canonical ASK WAV key',()=>{
 assert.equal(cast.length,24);
 const errors=[],baselines=new Map();let count=0;
 for(const app_id of ['READY_SET','HIDE_SEEK','SNAP_POP']){
  const e=make(app_id);
  for(const school_stage of ['E1','E2','E3','E4','E5','E6',null]){
   for(const character_id of cast){
    const event={app_id,character_id,event_type:'ASK',school_stage,
     relation_state:'MAIN_COMPANION',affinity:2,locale:'ko-KR'};
    const r=e.prepare(event);count++;
    if(!r.ok||r.status!=='TTS_MOCK_ROUTE_READY'||!r.key.startsWith('MAIN_CREW:'+character_id+':ASK:'))errors.push({app_id,school_stage,character_id,result:r.status});
    const k=app_id+':'+character_id;
    if(baselines.has(k)&&baselines.get(k)!==r.key)errors.push({app_id,school_stage,character_id,wrongKey:r.key});
    else baselines.set(k,r.key);
   }
  }
 }
 assert.deepEqual(errors,[]);assert.equal(count,504);
});
test('24 companions x 3 apps x 8 learner stages x ASK/HINT/FEEDBACK: no age-based voice gaps',()=>{
 const errors=[];let count=0;
 for(const app_id of ['READY_SET','HIDE_SEEK','SNAP_POP']){
  const e=make(app_id);
  for(const school_stage of ['E1','E2','E3','E4','E5','E6','M1',null]){
   for(const character_id of cast){
    for(const event_type of ['ASK','HINT','FEEDBACK']){
     const r=e.prepare({app_id,character_id,event_type,school_stage,
      relation_state:'MAIN_COMPANION',affinity:2,locale:'ko-KR'});
     count++;
     const intent=event_type==='FEEDBACK'?'ACKNOWLEDGE':event_type;
     if(!r.ok||r.status!=='TTS_MOCK_ROUTE_READY'||!r.key.startsWith('MAIN_CREW:'+character_id+':'+intent+':'))
      errors.push({app_id,school_stage,character_id,event_type,result:r.status});
    }
   }
  }
 }
 assert.deepEqual(errors,[]);assert.equal(count,1728);
});
test('main script owner never routes unknown app or Play Camp-specific 36 lines',()=>{
 const e=make('READY_SET');
 assert.equal(e.prepare({app_id:'PLAY_CAMP',character_id:'dubi',event_type:'ASK'}).ok,false);
 assert.ok(reg.rows.filter(x=>x.scope==='PLAY_CAMP').length===36);
});
