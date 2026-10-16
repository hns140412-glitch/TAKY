'use strict';
/* Generates canonical pre-recording production and consumption routes using existing source.
   This is a script *index*, not audio generation or production approval. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const repo=path.resolve(__dirname,'../..'),work=path.join(repo,'staging','crew_voice_20261012');
const source=JSON.parse(fs.readFileSync(path.join(work,'locked_dialogue_production_plan.json'),'utf8'));
const extra=JSON.parse(fs.readFileSync(path.join(work,'VOICE_EXTRA_SOURCE_LINES_REVIEW.json'),'utf8'));
const mapping=JSON.parse(fs.readFileSync(path.join(repo,'CURRENT','EXPLORER_CREW_SCRIPT_VOICE_MATCH_CURRENT.json'),'utf8'));
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const characters=new Map(mapping.character_routes.map(x=>[['dubi','lori','ink','nova','take','zero'][Number(x.character_id)-1] || 'guide-'+x.character_id,x]));
const family=new Map(mapping.voice_families.map(x=>[x.family,x]));
const byKey=new Map(),rows=[],issues=[];
function append(r){
 if(!r.character_id||!r.exact_text||!r.key||byKey.has(r.key)){issues.push('BAD_OR_DUPLICATE:'+r.key);return;}
 const p=characters.get(r.character_id);
 if(!p||p.family!==r.voice_family||p.elevenlabs_voice_id!==r.voice_id)
  {issues.push('CASTING_DRIFT:'+r.key);return}
 r.visual_id=p.character_id;
 r.locale='ko-KR';
 r.text_sha256=hash(r.exact_text);
 r.voice_name=family.get(r.voice_family).provider_display_name;
 r.file_relative_path='audio/'+r.scope+'/'+r.visual_id+'/'+r.file_stem+'.mp3';
 r.asset_id='EXPLORER_CREW:'+r.key+':'+r.text_sha256.slice(0,16);
 r.playback_stage='PENDING_MP3';
 r.recording_status='NOT_GENERATED';
 rows.push(r);byKey.set(r.key,r);
}
for(const r of source){
 append({key:r.key,scope:r.scope,character_id:r.character_id,voice_family:r.voice_family,
 voice_id:r.voice_id,kind:'LOCKED_INTENT',intent:r.intent,variant:r.variant,
 line_key:r.scope==='MAIN_CREW'?r.character_id+':E5_6:'+r.intent+':'+r.variant:r.character_id+':PLAY_CAMP:'+r.intent+':'+r.variant,
 exact_text:r.text,file_stem:r.intent+'_'+r.variant,source:'R10_SCRIPT_LOCK',
 production_authority:'R10_USER_PAID_BATCH_AUTHORIZED',reuse_events:[r.intent],
 allowed_app_contexts:r.scope==='PLAY_CAMP'?['PLAY_CAMP']:['READY_SET','HIDE_SEEK','SNAP_POP']});
}
for(const e of extra){
 const p=characters.get(e.character_id);
 if(!p){issues.push('EXTRA_UNKNOWN_CHARACTER:'+e.character_id);continue;}
 const familyId=p.family,voiceId=p.elevenlabs_voice_id;
 const base={scope:'MAIN_CREW',character_id:e.character_id,voice_family:familyId,voice_id:voiceId,exact_text:e.text,
 production_authority:'PRE_EXISTING_SOURCE_TEXT_PRODUCTION_APPROVAL_NOT_RESOLVED',
 allowed_app_contexts:['READY_SET','HIDE_SEEK','SNAP_POP'],source:e.source};
 if(e.type==='SIGNATURE_GREET_RECONNECT'){
   append({...base,key:'MAIN_CREW:'+e.character_id+':SIGNATURE',kind:'SIGNATURE',
   file_stem:'SIGNATURE',intent:null,variant:null,line_key:null,reuse_events:['GREET','RECONNECT'],
   allowed_app_contexts:[...base.allowed_app_contexts,...(['dubi','lori','ink','nova','take','zero'].includes(e.character_id)?['PLAY_CAMP']:[])]});
 }else if(e.type==='CORE6_SCENE'){
   const scene=e.scene.toUpperCase();
   append({...base,key:'MAIN_CREW:'+e.character_id+':SCENE:'+scene,kind:'SCENE',
   file_stem:'SCENE_'+scene,intent:'ASK',variant:null,scene_id:scene,line_key:null,reuse_events:[scene]});
 }else if(e.type==='MEMORY_CALLBACK'){
   append({...base,key:'MAIN_CREW:'+e.character_id+':MEMORY:'+e.event,kind:'MEMORY',
   file_stem:'MEMORY_'+e.event,intent:'ASK',variant:null,memory_event:e.event,
   requires_real_memory_evidence:true,line_key:e.character_id+':MEMORY:'+e.event,reuse_events:[e.event]});
 }else issues.push('UNKNOWN_EXTRA_TYPE:'+e.type);
}
const types=Object.fromEntries([...new Set(rows.map(x=>x.kind))].map(k=>[k,rows.filter(x=>x.kind===k).length]));
const allTexts=new Set(rows.map(x=>x.exact_text));
if(rows.length!==264||allTexts.size!==264||types.LOCKED_INTENT!==180||types.SIGNATURE!==24||types.SCENE!==30||types.MEMORY!==30)
 issues.push('264_SCRIPT_SOURCE_TOTAL_MISMATCH');
if(mapping.voice_families.length!==9)issues.push('NOT_9_VOICE_GROUPS');
const result={schema_version:'TAKY_EXPLORER_CREW_PRERECORDING_ROUTING_V1',status:issues.length?'FAIL':'STATIC_SOURCE_LINKED',
 scope:'SHARED_EXPLORER_CREW',source_authority:'R10_SCRIPT_LOCK_PLUS_APPROVED_SCENE_SIGNATURE_MEMORY_SOURCE',
 voice_groups:9,characters:24,total_rows:rows.length,counts:types,
 paid_authorized_lines:180,additional_source_lines_pending_recording_approval:84,
 produced_mp3:0,app_runtime_connected:false,issues,rows};
const dest=path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json');
fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,rows:rows.length,unique_texts:allTexts.size,counts:types,errors:issues},null,2));
if(issues.length)process.exitCode=2;