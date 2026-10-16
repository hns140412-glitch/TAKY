"use strict";
const fs=require("fs"),path=require("path");
const repo="D:/Git PWA/TAKY";
const p=path.join(repo,"CURRENT","EXPLORER_CREW_SCRIPT_VOICE_MATCH_CURRENT.json");
const data=JSON.parse(fs.readFileSync(p,"utf8"));
const m=JSON.parse(fs.readFileSync(path.join(repo,"staging/crew_voice_20261012/mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json"),"utf8"));
if(data.voice_families.length!==9||data.character_routes.length!==24||m.clip_count!==264||m.status!=="COMPLETE_MOCK_SOURCE")
 throw Error("SOURCE_STATE_MISMATCH");
data.audio_consumer={
 mode:"PREFER_VERIFIED_APPROVED_MP3_OTHERWISE_OFFLINE_TTS_MOCK_WAV",
 script_authority:"staging/crew_voice_20261012/EXPLORER_CREW_PRERECORDING_ROUTING_264.json",
 mock_manifest:"staging/crew_voice_20261012/mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json",
 mock_preview:"staging/crew_voice_20261012/mock_tts/index.html",
 recorded_manifest:"staging/crew_voice_20261012/EXPLORER_CREW_PLAYBACK_MANIFEST.json",
 update_script:"SHARED/runtime/update-explorer-crew-voice-assets.cjs",
 mock_engine:"Windows SAPI Microsoft Heami Desktop",
 mock_files:264,provider_approved_recordings:0,
 recording_priority:"EXACT_CHARACTER_ID + EXACT_TEXT_SHA256 + EXACT_VERIFIED_VOICE_ID + APPROVED_AUDIO_SHA256",
 group_voice_profiles:"9 speed/pitch profiles on one installed Korean voice, not nine timbres",
 production_complete:false,app_event_consumption_complete:false,
 note:"Mock is for direct local preview and future app packaging. Child apps have not yet wired real events."
};
fs.writeFileSync(p,JSON.stringify(data,null,2)+"\n");
const again=JSON.parse(fs.readFileSync(p,"utf8"));
if(again.audio_consumer.mock_files!==264||again.voice_families.filter(x=>x.voice_id_verified).length!==9)
 throw Error("POST_WRITE_VALIDATION_FAILURE");
console.log(JSON.stringify({status:"MOCK_SOURCE_REGISTERED",mock_clips:again.audio_consumer.mock_files,
 group_voice_ids:9,approved_mp3:again.audio_consumer.provider_approved_recordings,
 app_consumption_complete:again.audio_consumer.app_event_consumption_complete},null,2));
