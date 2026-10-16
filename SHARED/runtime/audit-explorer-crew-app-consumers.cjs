'use strict';
const fs=require('fs'),path=require('path');
const base='D:/Git PWA',work=base+'/TAKY/staging/crew_voice_20261012';
const apps=[
{app_id:'READY_SET',dir:'Ready & Set',known_event:'Ready Guide / Mission / Focus',owner:'Planner/Ready Executor'},
{app_id:'HIDE_SEEK',dir:'Hide & Seek',known_event:'partnerVoiceBtn, setPartner/partnerSpeak',owner:'Hide memory signal UI'},
{app_id:'SNAP_POP',dir:'Snap & Pop',known_event:'homeRadio, listenBtn, autoRead',owner:'Snap exploration UI'}
];
const results=[];
for(const a of apps){
 const html=fs.readFileSync(path.join(base,a.dir,'index.html'),'utf8');
 const script=fs.readFileSync(path.join(base,a.dir,'app.js'),'utf8');
 const r={
   app_id:a.app_id,location:path.join(base,a.dir),app_event:a.known_event,owner:a.owner,
   canonical_script_imported:html.includes('dialogue-script-authority-v1.js'),
   canonical_personality_imported:html.includes('dialogue-personality-v1.js'),
   voice_bridge_imported:html.includes('explorer-crew-dialogue-voice-bridge'),
   voice_preproduction_registry_imported:html.includes('EXPLORER_CREW_PRERECORDING_ROUTING_264'),
   crew_voice_event_caller:script.includes('TakyExplorerCrewDialogueVoiceBridge'),
   generic_tts_present:script.includes('speechSynthesis')||script.includes('SpeechSynthesisUtterance'),
   needs_real_app_event_hook:true,
   current_complete_recording_consumer:false
 };
 r.needs_real_app_event_hook=!(r.voice_bridge_imported&&r.voice_preproduction_registry_imported&&r.crew_voice_event_caller);
 results.push(r);
}
const report={status:results.some(x=>x.needs_real_app_event_hook)?'REAL_APP_EVENT_WIRING_INCOMPLETE':'STATIC_APP_HOOKS_PRESENT',
 scope:'TAKY_EXPLORER_CREW_ONLY_NO_PLAY_CAMP_REPO_CHANGES',
 note:'Presence of script imports alone does not prove event/audio playback. Ready has no canonical crew scripts imported at all.',
 results};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_APP_EVENT_REACHABILITY_20261013.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
