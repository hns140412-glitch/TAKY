'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const repo=path.resolve(__dirname,'../..'),work=path.join(repo,'staging','crew_voice_20261012');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const cur=read(path.join(repo,'CURRENT','EXPLORER_CREW_SCRIPT_VOICE_MATCH_CURRENT.json'));
const provider=read(path.join(work,'PROVIDER_VOICE_LIST_20261013.json'));
const policy=read(path.join(work,'VOICE_GROUP_9_FIXED_POLICY_20261013.json'));
const plan=read(path.join(work,'locked_dialogue_production_plan.json'));
const compiled=read(path.join(work,'EXPLORER_CREW_PLAYBACK_MANIFEST.json'));
const report=read(path.join(work,'EXPLORER_CREW_RECORDING_LINK_REPORT.json'));
assert.equal(provider.groups.length,9);
assert.equal(new Set(provider.groups.map(g=>g.voice_id)).size,9);
assert.equal(cur.voice_families.length,9);
assert.equal(cur.character_routes.length,24);
assert.equal(plan.length,180);
assert.equal(plan.filter(x=>x.scope==='MAIN_CREW').length,144);
assert.equal(plan.filter(x=>x.scope==='PLAY_CAMP').length,36);
const byFamily=new Map(cur.voice_families.map(g=>[g.family,g]));
for(const p of provider.groups){
 const g=byFamily.get(p.id);
 assert.ok(g);assert.equal(g.elevenlabs_voice_id,p.voice_id);
 assert.equal(g.provider_display_name,p.name);assert.equal(g.voice_id_verified,true);
 assert.equal(g.verification_evidence.source_file,'staging/crew_voice_20261012/PROVIDER_VOICE_LIST_20261013.json');
}
for(const person of cur.character_routes){
 const family=byFamily.get(person.family);assert.ok(family);
 assert.ok(family.characters.includes(person.character));
 assert.equal(person.elevenlabs_voice_id,family.elevenlabs_voice_id);
}
const items=new Set();
for(const row of plan){
 assert.ok(!items.has(row.key),'duplicate recorded line');items.add(row.key);
 const family=byFamily.get(row.voice_family);
 assert.equal(row.voice_id,family.elevenlabs_voice_id);
 assert.equal(row.status,'VOICE_ID_VERIFIED_SOURCE_LOCKED');
 assert.equal(crypto.createHash('sha256').update(row.text).digest('hex'),row.text_sha256);
}
assert.equal(policy.groups.length,9);
assert.equal(compiled.total_slots,264);
assert.equal(report.expected_slots,264);
assert.equal(report.actual_audio_ready,compiled.clips.length);
assert.equal(Object.values(report.counts).reduce((sum,n)=>sum+n,0),264);
const prerecord=read(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json'));
const sourceIndex=new Map(prerecord.rows.map(r=>[r.key,r]));
for(const clip of compiled.clips){
 const row=sourceIndex.get(clip.key);
 assert.ok(row,'approved clip source missing');
 assert.equal(clip.voice_id,row.voice_id);
 assert.equal(clip.text_sha256,row.text_sha256);
 assert.equal(clip.exact_text,row.exact_text);
}
const output={status:'VOICE_IDS_BOUND_264_SOURCE_ROUTES_PREWIRED',provider_voice_ids:9,characters:24,script_keys:180,additional_source_keys:84,total_prepared_routes:264,approved_mp3:compiled.clips.length,runtime_app_playback_confirmed:0};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_VOICE_BINDING_QA_20261013.json'),JSON.stringify(output,null,2));
console.log(JSON.stringify(output,null,2));
