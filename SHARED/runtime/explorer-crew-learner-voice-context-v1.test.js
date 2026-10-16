'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const ctx=require('./explorer-crew-learner-voice-context-v1.js');
const owner=require('./explorer-crew-content-owner-v1.js');
const personality=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/dialogue-personality-v1.js');
const source=JSON.parse(fs.readFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_PRERECORDING_ROUTING_264.json','utf8'));
const roster=[...new Set(source.rows.filter(x=>x.kind==='SIGNATURE').map(x=>x.character_id))];
test('all primary school grades, unknown stage and middle stage retain optional metadata, never gate voice',()=>{
 for(const schoolStage of ['E1','E2','E3','E4','E5','E6','M1',null]){
  const r=ctx.resolve({app_id:'READY_SET',identityReady:true,
   identity:{memberId:'QA_LEARNER',schoolStage}});
  assert.equal(r.ok,true,String(schoolStage));
  assert.equal(r.voice_content_scope,'MAIN_CREW');
  assert.equal(r.school_stage,schoolStage);
  assert.equal(r.learner_id,'QA_LEARNER');
 }
});
test('no profile or no school grade cannot falsely assign E5 and cannot block main crew speech',()=>{
 const r=ctx.resolve({app_id:'HIDE_SEEK'});
 assert.equal(r.ok,true);assert.equal(r.school_stage,null);
 assert.equal(r.source,'NOT_SUPPLIED');
 const ready=ctx.resolve({app_id:'READY_SET',identityReady:false});
 assert.equal(ready.ok,true);assert.equal(ready.school_stage,null);
});
test('bound session with conflicting/unknown grade is optional metadata, not voice exclusion',()=>{
 const base={source:'APP_BOUND_NAVIGATION_CONTEXT',session_id:'s1',task_id:'t1',child_id:'CHILD_A',school_stage:'E4',school_grade:'5'};
 const r=ctx.resolve({app_id:'SNAP_POP',explicitContext:base});
 assert.equal(r.ok,true);assert.equal(r.school_stage,'E4');
 assert.equal(r.learner_stage_metadata_conflict,true);
 assert.equal(ctx.resolve({app_id:'SNAP_POP',explicitContext:{...base,school_stage:null}}).ok,true);
});
test('24 voices / three main consumer apps / seven age variants route same approved script key',()=>{
 const samples=['E1','E3','E4','E5','E6','M1',null];
 assert.equal(roster.length,24);
 const targets=new Map();
 for(const app_id of ['READY_SET','HIDE_SEEK','SNAP_POP']){
  const adapter=owner.create(personality,{app_id});
  for(const character_id of roster){
   for(const school_stage of samples){
    const r=adapter.resolve({app_id,character_id,intent:'ASK',school_stage,
     relation_state:'MAIN_COMPANION',affinity:1,voice_content_scope:'MAIN_CREW'});
    assert.equal(r.source,'CHARACTER_GRADE_RELATION_SCRIPT_AUTHORITY',app_id+'/'+character_id+'/'+school_stage+':'+r.reason);
    assert.equal(r.content_scope,'MAIN_CREW');
    assert.match(r.line_key,new RegExp('^'+character_id+':E5_6:ASK:'));
    const index=character_id+':'+app_id;
    if(targets.has(index))assert.equal(targets.get(index),r.line_key);
    targets.set(index,r.line_key);
   }
  }
 }
 assert.equal(targets.size,72);
});
test('cross-app scope cannot borrow Play Camp as MAIN or MAIN as Play Camp',()=>{
 const main=owner.create(personality,{app_id:'HIDE_SEEK'});
 const camp=owner.create(personality,{app_id:'PLAY_CAMP'});
 assert.equal(main.resolve({app_id:'PLAY_CAMP',character_id:'dubi',intent:'ASK'}).reason,'APP_CONTENT_OWNER_MISMATCH');
 const selected=camp.resolve({app_id:'PLAY_CAMP',character_id:'dubi',intent:'ASK',relation_state:'COMPANION'});
 assert.equal(selected.source,'PLAY_CAMP_CORE6_SCRIPT_AUTHORITY');
 assert.equal(selected.content_scope,'PLAY_CAMP');
 assert.equal(camp.resolve({app_id:'PLAY_CAMP',character_id:'guide-19',intent:'ASK'}).text,null);
});
test('actual app scripts load owner before consumer exactly once',()=>{
 for(const name of ['Ready & Set','Hide & Seek','Snap & Pop']){
  const html=fs.readFileSync('D:/Git PWA/'+name+'/index.html','utf8');
  const src='explorer-crew-content-owner-v1.js';
  const target='explorer-crew-ui-voice-integration-v1.js';
  assert.equal(html.split(src).length,2,name);
  assert.ok(html.indexOf(src)<html.indexOf(target),name);
 }
});
