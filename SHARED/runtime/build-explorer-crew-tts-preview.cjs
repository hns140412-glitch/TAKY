'use strict';
/* Build a stand-alone, file://-friendly local HTML preview. Only TAKY mock_tts outputs.
   The producer writes immutable source WAV; recordings, when approved, take precedence. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const repo=path.resolve(__dirname,'../..');
const work=path.join(repo,'staging','crew_voice_20261012'),out=path.join(work,'mock_tts');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const registry=read(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json'));
const mock=read(path.join(out,'EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json'));
const approved=read(path.join(work,'EXPLORER_CREW_PLAYBACK_MANIFEST.json'));
if(registry.rows.length!==264||mock.clip_count!==264||!Array.isArray(approved.clips))
 throw new Error('BAD_MOCK_SCOPE_OR_APPROVED_MANIFEST');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const byKey=new Map(registry.rows.map(r=>[r.key,r]));
for(const m of mock.clips){
 const r=byKey.get(m.key),full=path.resolve(out,m.relative_path);
 if(!r||r.voice_id!==m.target_elevenlabs_voice_id||r.text_sha256!==m.text_sha256
  ||!full.startsWith(path.resolve(out,'audio')+path.sep)||!fs.existsSync(full)
  ||digest(fs.readFileSync(full))!==m.wav_sha256)throw new Error('WRONG_TTS_MOCK:'+m.key);
}
for(const a of approved.clips){
 const row=byKey.get(a.key);
 if(!row||a.voice_id!==row.voice_id||a.text_sha256!==row.text_sha256
  ||a.exact_text!==row.exact_text||!['USER_APPROVED','LOCKED'].includes(a.status))
  throw new Error('WRONG_APPROVED_RECORDING:'+a.key);
 const source=path.resolve(work,row.file_relative_path);
 if(!fs.existsSync(source)||digest(fs.readFileSync(source))!==a.audio_sha256)
  throw new Error('APPROVED_AUDIO_SOURCE_INVALID:'+a.key);
 const target=path.resolve(out,a.url.split('?')[0].replace(/^\.\//,''));
 if(!target.startsWith(path.resolve(out,'audio')+path.sep))throw new Error('DANGEROUS_AUDIO_URL');
 fs.mkdirSync(path.dirname(target),{recursive:true});
 if(fs.existsSync(target)){
  if(digest(fs.readFileSync(target))!==a.audio_sha256)throw new Error('APPROVED_AUDIO_DESTINATION_CONFLICT:'+a.key);
 }else fs.copyFileSync(source,target,fs.constants.COPYFILE_EXCL);
}
fs.mkdirSync(path.join(out,'js'),{recursive:true});
for(const name of ['explorer-crew-dialogue-voice-bridge-v1.js','explorer-crew-tts-mock-switch-v1.js']){
 fs.copyFileSync(path.join(__dirname,name),path.join(out,'js',name));
}
const emit=(name,global,value)=>{
 fs.writeFileSync(path.join(out,name),'globalThis.'+global+'='+JSON.stringify(value)+';\n','utf8');
};
emit('data-registry.js','TakyCrewVoiceRegistry',registry);
emit('data-mock.js','TakyCrewMockManifest',mock);
emit('data-approved.js','TakyCrewApprovedManifest',approved);
const result={status:'PREVIEW_READY',mock_files:264,approved_mp3_in_preview:approved.clips.length,
 groups:9,characters:24,html:path.join(out,'index.html'),mode:'file:// local playback supported'};
fs.writeFileSync(path.join(out,'BUILD_RECEIPT.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
