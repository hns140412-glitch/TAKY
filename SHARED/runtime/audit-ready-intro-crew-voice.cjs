'use strict';
/* Evidence-first audit of Ready & Set / Explorer Crew sound.
 * This is NOT a generation/recording script and does not change the apps. */
const fs=require('fs'), path=require('path'), crypto=require('crypto');
const root='D:/Git PWA/Ready & Set', work='D:/Git PWA/TAKY/staging/crew_voice_20261012';
const read=(f)=>fs.readFileSync(path.join(root,f),'utf8');
const html=read('index.html'), app=read('app.js'), identity=read('ready-onboarding-identity-v1.js');
const completion=read('ready-onboarding-flow-completion-v1.js');
const crew=read('explorer-crew-voice/explorer-crew-ui-voice-integration-v1.js');
const native=read('ready-runtime-v07.js');
const source=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json')));
const mock=JSON.parse(fs.readFileSync(path.join(work,'mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json')));
const scripts=[...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/g)].map(x=>x[1].split('?')[0]);
const loaded=new Set(scripts);
const legacy=(app.match(/(?:lumi|pico|mori):\{defaultName:/g)||[]).length;
const kinds=Object.fromEntries([...new Set(source.rows.map(x=>x.kind))].map(k=>[k,source.rows.filter(x=>x.kind===k).length]));
const appOwners=Object.fromEntries([...new Set(source.rows.map(x=>x.scope))].map(s=>[s,source.rows.filter(x=>x.scope===s).length]));
const issues=[];
const push=(severity,id,area,actual,expected,proof,action)=>issues.push({severity,id,area,actual,expected,proof,action,status:'OPEN'});
if(!loaded.has('./ready-onboarding-flow-completion-v1.js'))
 push('CRITICAL','R01','First-run continuation','EXPLORER/THEME step code exists but is absent from HTML script imports',
   'Actual onboarding can enter 4/5 EXPLORER and 5/5 THEME after character step',
   'index.html; ready-onboarding-flow-completion-v1.js:53-80; ready-onboarding-identity-v1.js:23',
   'Reconnect the final stages to the approved first-run UI and test the entire real onboarding before recording');
if(legacy===3)push('CRITICAL','R02','Character identity','Legacy lumi/pico/mori guide trio controls existing Ready UI',
   'First encounter Core6 and later expanded 24-character canonical relation governs audio and UI',
   'app.js:12-16,29,125-139,427-449,565-612',
   'Reconcile legacy type/name/portrait with approved canonical Visual IDs before assigning paid audio');
if(/id:'lumi',name:'루미'/.test(completion))
 push('CRITICAL','R03','Intro companion choice','Orphan completion flow offers legacy 3 guide IDs and 3 PNGs',
   'Initial Core6 encounter should use approved canonical IDs/images/voice IDs',
   'ready-onboarding-flow-completion-v1.js:9-13,53-57',
   'Correct initial encounter owner/line mapping; do not synthesize for legacy IDs');
if(/SpeechSynthesisUtterance/.test(app))
 push('HIGH','R04','Voice preview and listening feedback','Guide preview / coach audio use OS/browser speechSynthesis and legacy guide voice preset',
  'Canonical 24 character voice rendering and approved recording or mock by exact line key',
  'app.js:593-612','Separate learner read-aloud voice from companion speech; route actual companion words through approved voice audio');
const keyKinds=new Set(source.rows.map(x=>x.kind));
if(!['INTRO','MISSION_START','SESSION_END','RETURN','FAREWELL','RETRY','CELEBRATE'].some(k=>keyKinds.has(k)))
 push('CRITICAL','R05','Intro/mission/return content','264 static voice keys contain no Intro, Mission Start, Session End or Farewell kind',
  'Every spoken introduction or end condition has its own exact script key or deliberately silent state',
  'EXPLORER_CREW_PRERECORDING_ROUTING_264.json; existing kinds '+[...keyKinds].join(', '),
  'Create scenario inventory and script candidate matrix before final batch');
if(!/FIRST_MEET|INTRO|ONBOARDING/.test(crew))
 push('HIGH','R06','Intro audio integration','Ready audio consumer wires selection preview and ASK button, no FIRST_MEET/INTRO onboarding event',
  'A real canonical intro/picker event with correct character, text and audio key',
  'explorer-crew-ui-voice-integration-v1.js; no intro event in actual consumer',
  'Bind approved intro event, speech bubble, media and replay only where UX requests it');
if(/state\.guide\.name/.test(app) && /readRelation/.test(crew))
 push('HIGH','R07','Voice/UI ownership divergence','Legacy app guide labels and canonical companion audio read from separate state owners',
  'Displayed companion identity, portrait, script and voice ID resolve to one canonical character',
  'app.js:138,395,448; explorer-crew-ui-voice-integration-v1.js boundId/readRelation',
  'Use one owner for all companion displays; preserve user nickname as distinct from ID');
if(!/FIRST_MEET|RETURN|RECONNECT/.test(native))
 push('HIGH','R08','Onboarding & reunion triggers','Ready runtime emits task and session events, not canonical first-meet/reconnect voice trigger',
  'First meeting/reunion triggers are distinguishable and can be tested with existing/new audio keys',
  'ready-runtime-v07.js; explorer-crew-voice-event-adapter-v1.js',
  'Specify ownership and timing for first greeting/revisit, not just show a floating voice button');
if(/guideData\(\)\.intro/.test(app) && /recIntro/.test(app))
 push('HIGH','R09','English recording intro','English recording entry displays a legacy guide intro rather than a bound crew line',
  'Recording mode companion text and audio must align with the same canonical actor and cue',
  'app.js:373-396,447-459','List and bind recording start/relisten/rerecord/finish utterances before paid synthesis');
if(/speakGuide\(\$\{state\.guide\.name\}/.test(app))
 push('MEDIUM','R10','Human/legacy name ambiguity','Ready default lumi=루미 is unrelated to the canonical human-shaped guide-20 루미',
  'Display labels cannot be used to infer a voice ID or actor ID',
  'app.js:13; canonical 24 character roster',
  'Use immutable character_id, avoid Korean name-only voice routing');
const count={critical:issues.filter(x=>x.severity==='CRITICAL').length,high:issues.filter(x=>x.severity==='HIGH').length,medium:issues.filter(x=>x.severity==='MEDIUM').length};
const report={
 schema_version:'TAKY_READY_INTRO_VOICE_EVIDENCE_AUDIT_V1',
 date:'2026-10-13',
 result:'NO_GO_INTRO_AND_RECORDING',
 scope:'Ready & Set real onboarding, canonical 24 explorer crew, English recording voice UI, audio event flow',
 source_voices:9,source_characters:24,source_total:source.rows.length,source_by_kind:kinds,source_by_scope:appOwners,
 temporary_tts_clips:mock.clips.length,approved_elevenlabs_mp3:0,
 runtime_scripts:scripts.length,first_run_completion_module_loaded:loaded.has('./ready-onboarding-flow-completion-v1.js'),
 legacy_intro_guides_in_app_js:legacy,issues_count:issues.length,severity_counts:count,issues,
 verification_method:'Source inspection + deterministic code-inventory assertions. Not a complete first-run playback UI E2E.',
 restrictions:'No paid voice generation, no Play Camp edit, no push, no deploy; canonical 264 lines unchanged'
};
fs.writeFileSync(path.join(work,'READY_SET_EXPLORER_CREW_INTRO_VOICE_AUDIT_20261013.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({result:report.result,issues:issues.length,counts:count,scriptLoaded:report.first_run_completion_module_loaded,kind_counts:kinds,scope_counts:appOwners,ids:issues.map(x=>x.id)},null,2));
