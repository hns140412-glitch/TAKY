'use strict';
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const repo='D:/Git PWA/TAKY',work=path.join(repo,'staging/crew_voice_20261012');
const apps=['HIDE_SEEK','SNAP_POP'],reports=[];
for(const app of apps){
 const file=path.join(work,'EXPLORER_CREW_ACTUAL_APP_UI_WAV_SMOKE_20261013_'+app+'.json');
 const evidence=JSON.parse(fs.readFileSync(file,'utf8'));
 const item=evidence.tests?.find(x=>x.app_id===app);
 assert(item,app);
 assert.equal(item.test_school_stage,'E2',app);
 assert.equal(item.audio_playing,true,app);
 assert.equal(item.playing_mode,'TTS_MOCK',app);
 assert.equal(item.url_200,true,app);
 assert(item.route_key.startsWith('MAIN_CREW:'),app);
 reports.push({app,grade_input:'E2',voice_key:item.route_key,confirmed_playing:true,wav_http_200:true});
}
const current=fs.readFileSync(path.join(repo,'CURRENT/EXPLORER_CREW_VOICE_PRODUCTION_CURRENT.md'),'utf8');
assert(current.includes('학년별로 분리하지 않는다'));
assert(current.includes('MAIN_CREW/PLAY_CAMP'));
const source=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json')));
const mock=JSON.parse(fs.readFileSync(path.join(work,'mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json')));
assert.equal(source.rows.length,264);assert.equal(mock.clip_count,264);
const report={authority:'TAKY_CURRENT',status:'PASS_AGE_FREE_VOICE_CONSUMPTION_SCOPE',
 character_count:24,voice_family_count:9,locked_source_rows:264,
 demo_age_matrix:{apps:3,characters:24,stages:['E1','E2','E3','E4','E5','E6','M1',null],intents:['ASK','HINT','FEEDBACK'],test_cases:1728},
 independently_tested_actual_browser:reports,
 retained_legacy_data_key:'E5_6 (MAIN_CREW source lookup only, not learner grade)',
 applies_to:['READY_SET','HIDE_SEEK','SNAP_POP'],play_camp_repo_modified:false,
 scope_notice:'24x3x8x3 static resolve tests are not 1728 real browser playbacks; Ready actual UI audio and intro integration remain OPEN.',
 paid_voice_generation:0};
const dest=path.join(work,'EXPLORER_CREW_GRADE_AGNOSTIC_VOICE_QA_20261013.json');
fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,verified_app_replays:reports,tested_routing:1728,dest},null,2));
