'use strict';
const fs=require('fs'),path=require('path');
const root='D:/Git PWA/TAKY/staging/crew_voice_20261012';
const qa=JSON.parse(fs.readFileSync(path.join(root,'EXPLORER_CREW_NATIVE_LEARNING_EVENT_AUDIO_QA_20261013.json')));
if(qa.status!=='PASS'||qa.tests.length!==2||qa.tests.some(x=>x.pass!==true||
 !x.last?.key||x.last.status!=='PLAYING_STARTED'))throw Error('NO_REAL_NATIVE_PLAYBACK_PROOF');
const file=path.join(root,'EXPLORER_CREW_REAL_APP_EVENT_TO_VOICE_MATRIX_20261013.json');
const matrix=JSON.parse(fs.readFileSync(file));
const cases=[
 {app:'HIDE_SEEK',event:'HELP_NEEDED',expected:'MAIN_CREW:dubi:HINT:1',
  evidence:'HideSeekBridge.emit(HELP_NEEDED, crew_voice_requested=true) native same-tab event -> HINT WAV playing'},
 {app:'SNAP_POP',event:'TASK_COMPLETED',expected:'MAIN_CREW:guide-19:ACKNOWLEDGE:1',
  evidence:'SnapPopBridge.emit(TASK_COMPLETED, child_authored=true) native same-tab event -> ACK WAV playing'}
];
for(const c of cases){
 const test=qa.tests.find(x=>x.app===c.app);
 if(!test||test.last.key!==c.expected)throw Error('QA_KEY_MISMATCH:'+c.app);
 const row=matrix.rows.find(x=>x.app===c.app&&x.event===c.event);
 if(!row)throw Error('EVENT_ROW_MISSING:'+c.app+'/'+c.event);
 row.status='APP_EVENT_PLAYING_CONFIRMED_NATIVE';
 row.evidence=c.evidence;
 row.audio_key_confirmed=c.expected;
 row.qa_report='EXPLORER_CREW_NATIVE_LEARNING_EVENT_AUDIO_QA_20261013.json';
}
matrix.confirmed_app_consumption=matrix.rows.filter(x=>x.status.startsWith('APP_EVENT_PLAYING_CONFIRMED')).length;
matrix.open_consumption=matrix.rows.length-matrix.confirmed_app_consumption;
matrix.status='PARTIAL_CONSUMER_IMPLEMENTATION';
matrix.last_evidence_review='2026-10-13';
matrix.note='6/18 supported event paths include 24-character cards (Hide/Snap) + ASK buttons (Hide/Snap) + native Hide HINT + native Snap FEEDBACK. Do not count all app/character permutations as tested.';
fs.writeFileSync(file,JSON.stringify(matrix,null,2)+'\n');
console.log(JSON.stringify({status:matrix.status,total:matrix.rows.length,confirmed:matrix.confirmed_app_consumption,open:matrix.open_consumption},null,2));
