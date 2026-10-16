/* Verified ElevenLabs list -> TAKY CURRENT. No TTS calls or app writes. */
'use strict';
const fs=require('fs'),path=require('path');
const repo=path.resolve(__dirname,'../..');
const source=path.join(repo,'staging','crew_voice_20261012','PROVIDER_VOICE_LIST_20261013.json');
const current=path.join(repo,'CURRENT','EXPLORER_CREW_SCRIPT_VOICE_MATCH_CURRENT.json');
const evidence=JSON.parse(fs.readFileSync(source,'utf8'));
const original=JSON.parse(fs.readFileSync(current,'utf8'));
const voices=evidence.groups;
if(evidence.provider!=='ELEVENLABS'||evidence.reported_total_count!==9||voices.length!==9
 ||original.voice_families.length!==9||original.character_routes.length!==24)
 throw new Error('UNEXPECTED_PROVIDER_VOICE_SCOPE');
const families=new Map(),ids=new Set();
for(const voice of voices){
 if(families.has(voice.id)||ids.has(voice.voice_id)||!/^(VF0[1-6]|SP0[1-3])$/.test(voice.id)
 ||!/^[A-Za-z0-9]{20}$/.test(voice.voice_id))throw new Error('INVALID_VOICE_ID_OR_DUPLICATE:'+voice.id);
 families.set(voice.id,voice);ids.add(voice.voice_id);
}
for(const family of original.voice_families){
 const found=families.get(family.family);
 if(!found)throw new Error('MISSING_FAMILY:'+family.family);
 if(family.elevenlabs_voice_id&&family.elevenlabs_voice_id!==found.voice_id)
  throw new Error('EXISTING_VOICE_ID_CONFLICT:'+family.family);
 family.elevenlabs_voice_id=found.voice_id;
 family.provider_display_name=found.name;
 family.voice_id_verified=true;
 family.verification_evidence={
  provider:'ELEVENLABS',source_file:'staging/crew_voice_20261012/PROVIDER_VOICE_LIST_20261013.json',
  method:evidence.provider_read_tool,category:evidence.reported_category,
  language:evidence.reported_language,is_library_voice:evidence.reported_is_library_voice,
  retrieved_on:evidence.retrieved_on
 };
}
for(const c of original.character_routes){
 const family=original.voice_families.find(g=>g.family===c.family);
 if(!family||!family.characters.includes(c.character))throw new Error('CHARACTER_FAMILY_MISMATCH:'+c.character);
 if(c.elevenlabs_voice_id&&c.elevenlabs_voice_id!==family.elevenlabs_voice_id)
  throw new Error('CHARACTER_VOICE_CONFLICT:'+c.character);
 c.elevenlabs_voice_id=family.elevenlabs_voice_id;
}
original.status='SCRIPT_CHARACTER_FAMILY_VOICE_IDS_VERIFIED_AUDIO_NOT_GENERATED';
original.provider_voice_evidence='staging/crew_voice_20261012/PROVIDER_VOICE_LIST_20261013.json';
const tmp=current+'.tmp-bind';
fs.writeFileSync(tmp,JSON.stringify(original,null,2)+'\n');
try {fs.renameSync(tmp,current);} catch (error) {
 if(process.platform!=='win32'||!['EPERM','EEXIST'].includes(error.code))throw error;
 const before=fs.readFileSync(current,'utf8');
 try{fs.writeFileSync(current,fs.readFileSync(tmp));fs.unlinkSync(tmp);}
 catch(writeError){fs.writeFileSync(current,before);throw writeError;}
}
const check=JSON.parse(fs.readFileSync(current,'utf8'));
if(check.voice_families.filter(x=>x.voice_id_verified).length!==9||check.character_routes.filter(x=>x.elevenlabs_voice_id).length!==24)
 throw new Error('POST_WRITE_BINDING_NOT_VERIFIED');
console.log(JSON.stringify({status:'PROVIDER_VOICE_IDS_BOUND',voice_groups:9,character_routes:24,generated_audio:0}));
