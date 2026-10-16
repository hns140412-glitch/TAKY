'use strict';
/* TAKY Explorer Crew source-to-recording compiler, 264 exact prewired lines.
   Zero ElevenLabs usage. Never touch any app repository during --audit. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..'),work=path.join(root,'staging','crew_voice_20261012');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const prerecord=read(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json'));
const mapping=read(path.join(root,'CURRENT','EXPLORER_CREW_SCRIPT_VOICE_MATCH_CURRENT.json'));
const bridge=require('./explorer-crew-dialogue-voice-bridge-v1.js');
const {scan:checkMp3}=require('./verify-explorer-crew-mp3-bytes-v1.cjs');
if(prerecord.rows?.length!==264||mapping.voice_families?.length!==9)throw new Error('MISSING_264_CANONICAL_ROUTING');
const receiptsPath=path.join(work,'PRODUCTION_RECORDING_RECEIPTS.json');
const receipts=fs.existsSync(receiptsPath)?read(receiptsPath):{schema_version:'TAKY_CREW_RECORDING_RECEIPTS_V1',rows:[]};
const receiptsMap=new Map(),problems=[],rows=[],ready=[];
for(const item of receipts.rows||[]){
 if(receiptsMap.has(item.key))problems.push({key:item.key,reason:'DUPLICATE_RECEIPT'});
 else receiptsMap.set(item.key,item);
}
const families=new Map(mapping.voice_families.map(g=>[g.family,g]));
for(const row of prerecord.rows){
 const family=families.get(row.voice_family);
 if(!family||!family.voice_id_verified||family.elevenlabs_voice_id!==row.voice_id)
  throw new Error('WRONG_PROVIDER_VOICE:'+row.key);
 let status=row.production_authority==='R10_USER_PAID_BATCH_AUTHORIZED'?'NOT_RECORDED':'ADDITIONAL_SOURCE_NOT_PRODUCTION_AUTHORIZED';
 const receipt=receiptsMap.get(row.key);
 if(receipt){
  if(receipt.voice_id!==row.voice_id||receipt.voice_family!==row.voice_family
   ||receipt.exact_text!==row.exact_text||receipt.text_sha256!==row.text_sha256
   ||receipt.locale!=='ko-KR'){
    status='RECEIPT_TEXT_VOICE_MISMATCH';problems.push({key:row.key,reason:status});
  }else if(row.production_authority!=='R10_USER_PAID_BATCH_AUTHORIZED'&&
    (!receipt.production_authorization_ref || typeof receipt.production_authorization_ref!=='string')){
    status='EXTRA_LINE_RECORDING_AUTHORIZATION_MISSING';problems.push({key:row.key,reason:status});
  }else if(!['USER_APPROVED','LOCKED'].includes(receipt.approval_status)){
    status='RECORDING_REVIEW_PENDING';
  }else if(!receipt.approval_evidence || typeof receipt.approval_evidence!=='string'){
    status='MISSING_APPROVAL_EVIDENCE';problems.push({key:row.key,reason:status});
  }else {
    const file=path.resolve(work,row.file_relative_path);
    if(!file.startsWith(path.resolve(work,'audio')+path.sep))throw new Error('UNSAFE_FILE_PATH:'+row.key);
    if(!fs.existsSync(file))status='RECORDING_FILE_MISSING';
    else{
      const bytes=fs.readFileSync(file),digest=sha(bytes);
      const codec=checkMp3(bytes);
      if(bytes.length<1000||digest!==receipt.audio_sha256){
       status='RECORDING_CORRUPT_OR_HASH_MISMATCH';problems.push({key:row.key,reason:status});
      }else if(!codec.valid){
       status='RECORDING_NOT_VALID_MP3';problems.push({key:row.key,reason:status,codec_reason:codec.reason});
      }else{
       const relative='audio/explorer-crew/'+row.scope+'/'+row.visual_id+'/'+row.file_stem+'.mp3';
       const clip={
        key:row.key,kind:row.kind,scope:row.scope,character_id:row.character_id,
        voice_family:row.voice_family,voice_id:row.voice_id,locale:'ko-KR',
        intent:row.intent,variant:row.variant,exact_text:row.exact_text,
        text_sha256:row.text_sha256,audio_sha256:digest,
        url:'./'+relative+'?v='+digest.slice(0,12),
        status:receipt.approval_status,source_file:file,packaged_file:relative,
        allowed_app_contexts:row.allowed_app_contexts
       };
       ready.push(clip);status='APPROVED_AUDIO_READY_TO_PACKAGE';
      }
    }
  }
  receiptsMap.delete(row.key);
 }
 rows.push({key:row.key,voice_family:row.voice_family,voice_id:row.voice_id,
   production_authority:row.production_authority,status});
}
for(const [key] of receiptsMap)problems.push({key,reason:'ORPHAN_RECORDING_RECEIPT'});
// Preserve only the public/portable fields in the downloadable recording manifest.
const manifest={schema_version:'TAKY_EXPLORER_CREW_AUDIO_MANIFEST_264_V1',
 source_authority:prerecord.source_authority,total_slots:264,
 clips:ready.map(({source_file,packaged_file,...c})=>c)};
bridge.create(prerecord,{audioManifest:manifest});
const arg=process.argv.find(x=>x.startsWith('--package-app='));
const target=arg?.split('=')[1];
const destination={hide:'D:/Git PWA/Hide & Seek',snap:'D:/Git PWA/Snap & Pop',ready:'D:/Git PWA/Ready & Set'}[target];
if(arg&&!destination)throw new Error('UNKNOWN_APP__PLAY_CAMP_REPOSITORY_EXCLUDED');
let packaged=0;
if(arg){
 if(problems.length)throw new Error('INVALID_RECEIPT_REVIEW_BLOCKS_PACKAGE');
 if(!ready.length)throw new Error('ZERO_APPROVED_AUDIO__NOTHING_TO_PACKAGE');
 // App-level integration is a separate code change: do not place orphan files prematurely.
 const hook=path.join(destination,'audio','explorer-crew','consumer-runtime-registration.json');
 if(!fs.existsSync(hook)||read(hook)?.status!=='CONSUMER_EVENT_HOOK_TESTED')
  throw new Error('APP_EVENT_HOOK_NOT_VERIFIED__REFUSE_ORPHAN_PACKAGE');
 const subset=ready.filter(x=>x.allowed_app_contexts.includes(
  target==='hide'?'HIDE_SEEK':target==='snap'?'SNAP_POP':'READY_SET'));
 for(const x of subset){
  const src=path.join(work,prerecord.rows.find(r=>r.key===x.key).file_relative_path);
  const rel=x.url.slice(2).split('?')[0],dest=path.join(destination,rel);
  if(fs.existsSync(dest)&&sha(fs.readFileSync(dest))!==x.audio_sha256)
   throw new Error('APP_FILE_HASH_CONFLICT:'+x.key);
  if(!fs.existsSync(src)||sha(fs.readFileSync(src))!==x.audio_sha256)
   throw new Error('MISSING_OR_WRONG_APPROVED_SOURCE:'+x.key);
 }
 for(const x of subset){
  const src=path.join(work,prerecord.rows.find(r=>r.key===x.key).file_relative_path);
  const dest=path.join(destination,x.url.slice(2).split('?')[0]);
  fs.mkdirSync(path.dirname(dest),{recursive:true});
  if(!fs.existsSync(dest))fs.copyFileSync(src,dest,fs.constants.COPYFILE_EXCL);
  if(sha(fs.readFileSync(dest))!==x.audio_sha256)throw new Error('COPY_VALIDATION_FAILED:'+x.key);
  packaged++;
 }
 const mf=path.join(destination,'audio','explorer-crew','manifest.json');
 fs.writeFileSync(mf,JSON.stringify({...manifest,clips:subset},null,2)+'\n');
}
const counts=Object.fromEntries([...new Set(rows.map(x=>x.status))].map(s=>[s,rows.filter(x=>x.status===s).length]));
const status=problems.length?'RECORDING_RECEIPTS_INVALID':ready.length===0?'PREPRODUCTION_LINKS_READY_AUDIO_MISSING':'SOME_APPROVED_AUDIO_READY';
const report={status,expected_slots:264,voice_groups:9,paid_authorized_current:180,additional_authority_to_review:84,
 actual_audio_ready:ready.length,packaged,receipt_problems:problems,counts,rows};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_RECORDING_LINK_REPORT.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(work,'EXPLORER_CREW_PLAYBACK_MANIFEST.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({status,source_slots:264,voice_groups:9,ready:ready.length,packaged,counts,problems},null,2));
if(problems.length)process.exitCode=2;
