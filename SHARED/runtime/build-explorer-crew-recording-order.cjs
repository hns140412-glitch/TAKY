'use strict';
/* Recording order: real app usage first. No producer calls. Never auto-promote candidate drafts. */
const fs=require('node:fs'),path=require('node:path');
const dir=path.resolve(__dirname,'../../staging/crew_voice_20261012');
const source=JSON.parse(fs.readFileSync(path.join(dir,'EXPLORER_CREW_PRODUCER_LINE_LEDGER_20261013.json')));
const proposals=JSON.parse(fs.readFileSync(path.join(dir,'EXPLORER_CREW_MISSING_SCENARIO_DIALOGUES_DRAFT_20261013.json')));
const recorded=new Map(JSON.parse(fs.readFileSync(path.join(dir,'EXPLORER_CREW_PLAYBACK_MANIFEST.json'))).clips.map(x=>[x.key,x]));
const all=source.rows,main=all.filter(r=>r.production_permission==='R10_PAID_BATCH_AUTHORIZED');
const signatures=all.filter(r=>r.kind==='SIGNATURE');
const conditional=all.filter(r=>['SCENE','MEMORY'].includes(r.kind));
if(main.length!==180||signatures.length!==24||conditional.length!==60||proposals.rows.length!==96)throw Error('PRODUCTION_SCOPE_MISMATCH');
const cast=[...new Set(main.map(r=>r.voice_family))].sort();
const pilot=cast.map(group=>{
 const candidates=main.filter(r=>r.voice_family===group&&r.kind==='LOCKED_INTENT');
 const first=candidates.find(r=>r.event_intent==='ASK')||candidates[0];
 if(!first)throw Error('MISSING_VOICE_PILOT:'+group);
 return first.script_key;
});
const specialSupplement=['SP01','SP02','SP03'].map(group=>{
 const ids=[...new Set(main.filter(r=>r.voice_family===group).map(r=>r.character_id))];
 if(ids.length!==2)throw Error('SPECIAL_CREW_MUST_REMAIN_TWO_PER_GROUP:'+group);
 const p=main.find(r=>r.voice_family===group&&r.character_id===ids[1]&&r.event_intent==='ASK');
 return p.script_key;
});
const steps=[
 {phase:'A0_EXISTING_PRODUCTION_AUTHORITY',status:'AUTHORIZED_BUT_RECORDING_NOT_STARTED',lines:180,
  reason:'R10 original locked; producer should not reinterpret as all app voice coverage'},
 {phase:'A1_ACOUSTIC_PILOT',status:'NOT_GENERATED',pilot_9:pilot,special_second_actor_3:specialSupplement,
  note:'12 selected samples come from the existing 180 authorized lines; no additional paid scope is implied'},
 {phase:'B0_CHARACTER_SELECTION_SIGNATURE',status:'ADDITIONAL_PAID_APPROVAL_REQUIRED',lines:24,
  reason:'24 live selection cards consume these signatures; without them the selection UI remains TTS mock even if A0 completes'},
 {phase:'C0_SCENE_AND_MEMORY',status:'ADDITIONAL_PAID_APPROVAL_REQUIRED_AND_EVENT_TRACE_NEEDED',lines:60,
  reason:'30 Core6 scenes need exact scene event; 30 memory clips need witnessed memory evidence'},
 {phase:'D0_MISSING_SCENARIO_EDITORIAL',status:'NOT_USER_APPROVED__NO_SYNTHESIS',lines:96,
  reason:'Reconnection, farewell, retry, celebration editorial candidates. Not in canonical 264 and not runtime-connected'}
];
const strategy=[
 'Use same immutable script_key, exact_text and text_sha256 for all TTS and MP3.',
 'Check final ElevenLabs voice_id against actual provider-generated voice list, not just group name.',
 'Check acoustic character-fit per family; shared voice_id does not imply identical character personality.',
 'Before paid generation, ensure row is authorized and neither approved file nor matching receipt already exists.',
 'Never regenerate an existing correct audio to repair missing UI event, wrong URL, manifest, or PWA caching.',
 'Store output SHA256 and exact model/settings/voice_id with approval evidence per clip.',
 'Preserve TTS mock WAV per key until approved MP3 passes packager and actual app playback.',
 'Do not pass the additional 84 source lines or the 96 editorial candidates into the paid producer silently.',
 'Producer result must have distinct SynthesisCreated / Packaged / PlayingStarted / ListeningApproved statuses.'
];
const report={schema_version:'TAKY_CREW_RECORDING_EXECUTION_ORDER_V2',status:'PREPARATION_COMPLETE_RECORDING_ON_HOLD',
 existing_audio_mp3:recorded.size,
 central_total_source_lines:264,approved_scope_count:180,source_only_count:84,new_draft_count:96,
 number_of_voice_groups:9,pilot_ids:[...pilot,...specialSupplement],phases:steps,instructions:strategy,
 stop_before_paid_synthesis_until:['UI_EVENT_MATRIX_RECONCILED','24_SIGNATURE_PAID_SCOPE_RESOLVED',
 'NINE_ACTUAL_VOICES_AUDITIONED','READY_SELECTION_AUDIO_E2E_RESOLVED',
 'GRADE_STAGE_MAPPING_CONFIRMED','PRODUCTION_RECEIPT_IDEMPOTENCY_TESTED']
};
fs.writeFileSync(path.join(dir,'EXPLORER_CREW_RECORDING_EXECUTION_ORDER_20261013.json'),JSON.stringify(report,null,2));
const csvEscape=s=>'"'+String(s??'').replaceAll('"','""')+'"';
const columns=['script_key','character_name','voice_family','voice_design_name','elevenlabs_voice_id','scope','kind',
'production_permission','text_exact','text_sha256','original_audio_file','voice_cue','group_directing','line_directing'];
const csv=[columns.join(','),...all.map(r=>columns.map(c=>csvEscape(r[c])).join(','))].join('\r\n');
fs.writeFileSync(path.join(dir,'EXPLORER_CREW_RECORDING_264_SOURCE_SHEET_20261013.csv'),'\ufeff'+csv,'utf8');
console.log(JSON.stringify({status:report.status,phases:steps.map(s=>({phase:s.phase,lines:s.lines??(s.pilot_9?.length+s.special_second_actor_3?.length),status:s.status})),
 pilot_count:report.pilot_ids.length,csv_rows:all.length,unapproved_draft:proposals.rows.length},null,2));