'use strict';
/* One-command idempotent refresh: canonical source -> receipts -> WAV/MP3 manifests ->
   app-local bundles. No ElevenLabs calls, push, merge or Netlify deployment. */
const {spawnSync}=require('node:child_process'),fs=require('fs'),path=require('path');
const dir=__dirname,work=path.resolve(dir,'../../staging/crew_voice_20261012');
const steps=[
 ['Canonical script/character routing',process.execPath,[path.join(dir,'compile-explorer-crew-prerecording.cjs')]],
 ['Approved recorded-audio manifest',process.execPath,[path.join(dir,'build-explorer-crew-voice-manifest.cjs')]],
 ['Local offline Korean TTS refresh','pwsh',['-NoProfile','-File',path.join(dir,'generate-explorer-crew-mock-tts.ps1')]],
 ['Playable mixed WAV/MP3 preview',process.execPath,[path.join(dir,'build-explorer-crew-tts-preview.cjs')]],
 ['Ready/Hide/Snap app-local consumer assets',process.execPath,[path.join(dir,'install-explorer-crew-mock-into-apps.cjs')]],
 ['Central Voice ID and script receipt QA',process.execPath,[path.join(dir,'verify-explorer-crew-voice-binding.cjs')]],
 ['WAV / recording selection tests',process.execPath,['--test',path.join(dir,'explorer-crew-tts-mock-switch-v1.test.js')]]
];
const results=[];
for(const [step,cmd,args] of steps){
 const r=spawnSync(cmd,args,{cwd:work,encoding:'utf8',windowsHide:true,timeout:240000,maxBuffer:4e6});
 const status=r.status===0?'PASS':'FAIL';
 results.push({step,status,exit_code:r.status,stdout:(r.stdout||'').slice(-850),stderr:(r.stderr||'').slice(-700)});
 if(status==='FAIL')break;
}
const receipt={schema_version:'TAKY_EXPLORER_CREW_VOICE_REFRESH_V1',
 status:results.length===steps.length&&results.every(x=>x.status==='PASS')?'PASS':'FAIL',
 group_count:9,script_slots:264,paid_tts_calls:0,results};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_VOICE_REFRESH_RECEIPT.json'),JSON.stringify(receipt,null,2));
console.log(JSON.stringify({status:receipt.status,completed:results.length,steps:results.map(x=>({step:x.step,status:x.status,exit_code:x.exit_code}))},null,2));
if(receipt.status!=='PASS')process.exitCode=2;
