'use strict';
const crypto=require('node:crypto');
const VERSION='TAKY_CREW_DURABLE_EVIDENCE_STORE_V1';
const STATE_SCHEMA='TAKY_CREW_DURABLE_EVIDENCE_STATE_V1';
const HANDOFF='TAKY_CREW_EVIDENCE_HANDOFF_V1';
const TYPES=new Set(['FIRST_MEETING','SHARED_EPISODE','EXPLORATION_COMPLETE','HELP_ACCEPTED','COACHING_SHARED']);
const clean=v=>String(v??'').trim();
const digest=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function emptyState(){return {schema:STATE_SCHEMA,episodes:[],event_digests:{},committed_relationships:{}}}
function stateKey(packet={}){
 const family=clean(packet?.context?.family_id),member=clean(packet?.context?.member_id);
 if(!family||!member)return null;
 return 'families/'+encodeURIComponent(family)+'/members/'+encodeURIComponent(member)+'/explorer-crew/state-v1';
}
function validatePacket(packet={}){
 const issues=[];
 if(packet.schema!==HANDOFF)issues.push('HANDOFF_SCHEMA_INVALID');
 if(!clean(packet.source_app))issues.push('SOURCE_APP_REQUIRED');
 if(!Array.isArray(packet.events)||!packet.events.length)issues.push('EVENTS_REQUIRED');
 for(const e of packet.events||[]){
   if(!clean(e?.event_id))issues.push('EVENT_ID_REQUIRED');
   if(!TYPES.has(e?.type))issues.push('EVENT_TYPE_INVALID');
   if(e?.verified!==true)issues.push('VERIFIED_EVENT_REQUIRED');
   if(!clean(e?.evidence_ref))issues.push('EVIDENCE_REF_REQUIRED');
   if(!clean(e?.character_id))issues.push('CHARACTER_ID_REQUIRED');
   const source=clean(e?.source_app||e?.source);
   if(source&&source!==clean(packet.source_app))issues.push('EVENT_SOURCE_PACKET_SOURCE_MISMATCH');
 }
 return issues;
}
async function readState(store,key){
 const entry=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
 if(!entry||entry.data==null)return {exists:false,state:emptyState(),etag:null};
 if(!entry.etag||typeof entry.etag!=='string')throw new Error('EXISTING_STRONG_STATE_ETAG_REQUIRED');
 return {exists:true,state:entry.data,etag:entry.etag};
}
async function ingestPacket(store,packet={},options={}){
 const issues=validatePacket(packet);if(issues.length)return {ok:false,reason:'CREW_PACKET_INVALID',issues};
 const key=stateKey(packet);if(!key)return {ok:false,reason:'FAMILY_MEMBER_SCOPE_REQUIRED'};
 const maxAttempts=Math.max(1,Number(options.max_attempts)||4);
 for(let attempt=1;attempt<=maxAttempts;attempt++){
   const current=await readState(store,key),state=current.state?.schema===STATE_SCHEMA?current.state:emptyState();
   const next={...state,episodes:[...(state.episodes||[])],event_digests:{...(state.event_digests||{})},committed_relationships:{...(state.committed_relationships||{})}};
   const imported=[],duplicates=[];
   for(const e of packet.events){
     const k=clean(packet.source_app)+':'+clean(e.event_id),d=digest(e);
     if(Object.hasOwn(next.event_digests,k)){
       if(next.event_digests[k]!==d)return {ok:false,reason:'CREW_EVENT_REPLAY_PAYLOAD_MISMATCH',event_id:e.event_id};
       duplicates.push(e.event_id);continue;
     }
     next.event_digests[k]=d;
     next.episodes.push({...e,source_app:e.source_app||packet.source_app,source:e.source||e.source_app||packet.source_app});
     imported.push(e.event_id);
   }
   const opts=current.exists?{onlyIfMatch:current.etag}:{onlyIfNew:true};
   const write=await store.setJSON(key,next,opts);
   if(write?.modified===true&&typeof write.etag==='string'&&write.etag){
     return {ok:true,acknowledgement_kind:'CREW_EVIDENCE_RECEIPT',imported,duplicates,state:next,durable_store:{adapter_version:VERSION,key,consistency:'strong',conditional_write:current.exists?'onlyIfMatch':'onlyIfNew',attempt,etag:write.etag}};
   }
   if(write?.modified!==false)return {ok:false,reason:'DURABLE_STORE_WRITE_UNCONFIRMED',retryable:true};
 }
 return {ok:false,reason:'DURABLE_STORE_CONFLICT_RETRY_EXHAUSTED',key,retryable:true};
}
module.exports=Object.freeze({VERSION,STATE_SCHEMA,HANDOFF,emptyState,stateKey,validatePacket,readState,ingestPacket});
