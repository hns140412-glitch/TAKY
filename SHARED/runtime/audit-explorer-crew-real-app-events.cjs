'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),dir=path.join(root,'staging/crew_voice_20261012');
const source=JSON.parse(fs.readFileSync(path.join(dir,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json')));
const drafts=JSON.parse(fs.readFileSync(path.join(dir,'EXPLORER_CREW_MISSING_SCENARIO_DIALOGUES_DRAFT_20261013.json')));
const map=new Map();
for(const row of source.rows){
 const key=row.scope+':'+(row.kind==='LOCKED_INTENT'?row.intent:row.kind);
 map.set(key,(map.get(key)||0)+1);
}
const candidateCounts=Object.fromEntries(['RETURN','FAREWELL','RETRY_AFTER_FAILURE','CELEBRATE'].map(
 event=>[event,drafts.rows.filter(r=>r.event===event).length]));
const rows=[
 {app:'READY_SET',event:'PICKER_CARD_TAP',trigger:'TAKY approved 24-person selection overlay',
  source:'MAIN_CREW:SIGNATURE',status:'WIRED_BUT_READY_PLAYING_NOT_VERIFIED',
  evidence:'READY identity ready, picker visible; media playing remains OPEN'},
 {app:'HIDE_SEEK',event:'PICKER_CARD_TAP',trigger:'takyCrewSelectionLauncher → card',
  source:'MAIN_CREW:SIGNATURE',status:'APP_EVENT_PLAYING_CONFIRMED',
  evidence:'24/24 browser cards including human special'},
 {app:'SNAP_POP',event:'PICKER_CARD_TAP',trigger:'takyCrewSelectionLauncher → card',
  source:'MAIN_CREW:SIGNATURE',status:'APP_EVENT_PLAYING_CONFIRMED',
  evidence:'24/24 browser cards including human special'},
 {app:'READY_SET',event:'MISSION_ASK',trigger:'dedicated takiCrewVoiceBtn',
  source:'MAIN_CREW:ASK',status:'WIRED_BUT_READY_PLAYING_NOT_VERIFIED',
  evidence:'age/profile and 24 x E5/E6 route static passed'},
 {app:'HIDE_SEEK',event:'MISSION_ASK',trigger:'takyCrewVoiceBtn; HideSeekBridge session context',
  source:'MAIN_CREW:ASK',status:'APP_EVENT_PLAYING_CONFIRMED_ONE_CHARACTER',
  evidence:'dubi ASK:1 media playing, E5'},
 {app:'SNAP_POP',event:'MISSION_ASK',trigger:'homeRadio; SnapPopBridge context',
  source:'MAIN_CREW:ASK',status:'APP_EVENT_PLAYING_CONFIRMED_ONE_CHARACTER',
  evidence:'guide-19 ASK:1 media playing, E5'},
 {app:'READY_SET',event:'SESSION_ENDED',trigger:'ready-runtime-v07.js/finalizeSession',
  source:'CANDIDATE:FAREWELL',status:'NO_CANONICAL_VOICE_CONSUMER_EVENT',evidence:'24 drafts, not approved'},
 {app:'READY_SET',event:'TASK_STATE_CHANGED',trigger:'ready-runtime-v07.js/contract state',
  source:'MAIN_CREW:ACKNOWLEDGE',status:'NOT_MAPPED_TO_AUDIO',evidence:'confirmed eligible task result required'},
 {app:'HIDE_SEEK',event:'RETRIEVAL_WRONG',trigger:'app.js codeRed result/wrong and hide-bridge event',
  source:'CANDIDATE:RETRY_AFTER_FAILURE',status:'NO_CANONICAL_VOICE_CONSUMER_EVENT',evidence:'24 drafts, not approved'},
 {app:'HIDE_SEEK',event:'TASK_COMPLETED',trigger:'hide-bridge.js task status',
  source:'MAIN_CREW:ACKNOWLEDGE',status:'NOT_MAPPED_TO_AUDIO',evidence:'only after actual completed result'},
 {app:'HIDE_SEEK',event:'HELP_NEEDED',trigger:'hide-bridge.js task status',
  source:'MAIN_CREW:HINT',status:'NOT_MAPPED_TO_AUDIO',evidence:'must not reveal answer'},
 {app:'SNAP_POP',event:'TASK_COMPLETED',trigger:'snap-bridge.js task status',
  source:'MAIN_CREW:ACKNOWLEDGE',status:'NOT_MAPPED_TO_AUDIO',evidence:'only after actual completed result'},
 {app:'SNAP_POP',event:'HELP_NEEDED',trigger:'snap-bridge.js task status',
  source:'MAIN_CREW:HINT',status:'NOT_MAPPED_TO_AUDIO',evidence:'must be real request for help'},
 {app:'SHARED',event:'APP_RETURN',trigger:'return from adventure; reconnection logic',
  source:'CANDIDATE:RETURN',status:'DIALOGUE_UNAPPROVED_AND_EVENT_NOT_MAPPED',
  evidence:'currently identical SIGNATURE reused; 24 distinct draft lines'},
 {app:'SHARED',event:'BADGE_EARNED',trigger:'achievement/badge engine',
  source:'CANDIDATE:CELEBRATE',status:'DIALOGUE_UNAPPROVED_AND_EVENT_NOT_MAPPED',
  evidence:'needs evidence of own action; 24 drafts'},
 {app:'SHARED',event:'SCENE_IDEA_EMOTION_DESCRIPTION_VIEWPOINT_FINAL',trigger:'Core6 chapter scenes',
  source:'MAIN_CREW:SCENE',status:'RUNTIME_SOURCE_EXISTS_ACTUAL_APP_EVENT_NOT_PROVEN',
  evidence:'30 conditional lines, no automatic playback'},
 {app:'SHARED',event:'MEMORY_CALLBACK',trigger:'Shared Memory & Episode Engine',
  source:'MAIN_CREW:MEMORY',status:'EVIDENCE_REQUIRED_ACTUAL_APP_EVENT_NOT_PROVEN',
  evidence:'30 conditional lines, no simulated fake memories'},
 {app:'PLAY_CAMP',event:'CORE6_SCRIPT',trigger:'Play Camp Core6 existing source only',
  source:'PLAY_CAMP:ASK/HINT/ACKNOWLEDGE',status:'OUTSIDE_THIS_APP_CONSUMER_AUDIT',
  evidence:'36 source lines; Play Camp repo untouched'}
];
const report={schema_version:'TAKY_CREW_ACTUAL_APP_EVENT_VOICE_CONSUMPTION_MATRIX_V1',
 status:'PARTIAL_CONSUMER_IMPLEMENTATION',
 source_rows:source.rows.length,candidate_rows:drafts.rows.length,voice_groups:9,characters:24,
 source_counts:Object.fromEntries(map),candidate_counts:candidateCounts,
 rows,confirmed_app_consumption:rows.filter(x=>x.status.startsWith('APP_EVENT_PLAYING_CONFIRMED')).length,
 open_consumption:rows.filter(x=>!x.status.startsWith('APP_EVENT_PLAYING_CONFIRMED')).length,
 note:'Audio slot exists != real app event wired. Avoid paid production of unapproved or unconsumed events.'
};
fs.writeFileSync(path.join(dir,'EXPLORER_CREW_REAL_APP_EVENT_TO_VOICE_MATRIX_20261013.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({status:report.status,source_rows:report.source_rows,candidates:report.candidate_rows,rows:rows.length,confirmed:report.confirmed_app_consumption,open:report.open_consumption},null,2));
