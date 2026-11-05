'use strict';
const crypto=require('node:crypto');
const Identity=require('../LEARNING/transport/family-member-identity-resolver.js');
const Authenticated=require('./authenticated-crew-evidence-transport.js');

const VERSION='TAKY_CENTRAL_CREW_EVIDENCE_HTTP_V1';
const ENDPOINT='/api/crew/evidence';
const MAX_BODY_BYTES=65536;
const headers=Object.freeze({'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store, max-age=0',Pragma:'no-cache','X-Content-Type-Options':'nosniff'});
const response=(status,body)=>({status,headers:{...headers},body:JSON.stringify({...body,endpoint_version:VERSION})});
const bad=(status,reason)=>response(status,{ok:false,reason});
const clean=v=>typeof v==='string'?v.trim():'';
const object=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
const header=(h,n)=>{if(!object(h))return '';const k=Object.keys(h).find(x=>x.toLowerCase()===n.toLowerCase());return k?String(h[k]??''):''};
const stable=v=>Array.isArray(v)?v.map(stable):object(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,stable(v[k])])):v;
const digest=v=>crypto.createHash('sha256').update(JSON.stringify(stable(v))).digest('hex');
function scrub(packet){
 const p=JSON.parse(JSON.stringify(packet));
 delete p.authority_ref;
 for(const e of p.events||[]){
   delete e.verified;
   delete e.import_authority_ref;
   delete e.relationship_state;
 }
 return p;
}
function shapeValid(p){
 return object(p)&&p.schema==='TAKY_CREW_EVIDENCE_HANDOFF_V1'&&clean(p.source_app)&&
   object(p.context)&&clean(p.context.family_id)&&clean(p.context.member_id)&&
   Array.isArray(p.events)&&p.events.length>0&&p.events.every(e=>object(e)&&clean(e.event_id)&&clean(e.type)&&clean(e.evidence_ref)&&clean(e.character_id));
}
function sameScope(a,b){
 if(a.schema!==b.schema||a.source_app!==b.source_app||a.context?.family_id!==b.context?.family_id||a.context?.member_id!==b.context?.member_id)return false;
 const aa=(a.events||[]).map(e=>e.event_id).sort(),bb=(b.events||[]).map(e=>e.event_id).sort();
 return JSON.stringify(aa)===JSON.stringify(bb);
}
function create({verifyBearerToken,verifyCrewEvidence,store,maxBodyBytes=MAX_BODY_BYTES}={}){
 if(typeof verifyBearerToken!=='function')throw Error('TRUSTED_BEARER_IDENTITY_VERIFIER_REQUIRED');
 if(typeof verifyCrewEvidence!=='function')throw Error('TRUSTED_CREW_EVIDENCE_VERIFIER_REQUIRED');
 if(!store||typeof store.getWithMetadata!=='function'||typeof store.setJSON!=='function')throw Error('DURABLE_CONDITIONAL_STORE_REQUIRED');
 if(!Number.isInteger(maxBodyBytes)||maxBodyBytes<1024||maxBodyBytes>MAX_BODY_BYTES)throw Error('BOUNDED_JSON_BODY_LIMIT_REQUIRED');
 return Object.freeze({version:VERSION,async handle(request={}){
   if(request.method!=='POST')return bad(405,'POST_REQUIRED');
   if(request.path!==ENDPOINT)return bad(404,'CENTRAL_CREW_ENDPOINT_NOT_FOUND');
   if(!/^application\/json(?:\s*;|\s*$)/i.test(header(request.headers,'content-type')))return bad(415,'JSON_CONTENT_TYPE_REQUIRED');
   const token=header(request.headers,'authorization').match(/^Bearer ([A-Za-z0-9._~+/-]{16,4096}=*)$/);
   if(!token)return bad(401,'VERIFIED_BEARER_REQUIRED');
   if(typeof request.body!=='string'||Buffer.byteLength(request.body,'utf8')>maxBodyBytes)return bad(413,'BOUNDED_JSON_BODY_REQUIRED');
   let packet;try{packet=JSON.parse(request.body)}catch{return bad(400,'VALID_JSON_PACKET_REQUIRED')}
   if(!shapeValid(packet))return bad(400,'CREW_PACKET_SHAPE_REQUIRED');
   let principal;try{principal=await verifyBearerToken(token[1])}catch{return bad(401,'BEARER_IDENTITY_VERIFICATION_FAILED')}
   const resolved=Identity.resolve(principal,{requested_family_id:packet.context.family_id});
   if(!resolved.ok)return bad(403,'VERIFIED_FAMILY_MEMBERSHIP_REQUIRED');
   const identity=resolved.identity;
   if(!identity.authorized_member_ids.includes(packet.context.member_id))return bad(403,'AUTHORIZED_MEMBER_REQUIRED');
   const untrusted=scrub(packet);
   let verified;
   try{verified=await verifyCrewEvidence({packet:untrusted,identity:Object.freeze({...identity,authorized_member_ids:Object.freeze([...identity.authorized_member_ids])})})}
   catch{return bad(503,'TRUSTED_CREW_VERIFICATION_UNAVAILABLE')}
   if(verified?.ok!==true||!shapeValid(verified.packet)||!sameScope(packet,verified.packet))return bad(422,'TRUSTED_CREW_VERIFICATION_REQUIRED');
   if(!verified.packet.events.every(e=>e.verified===true))return bad(422,'TRUSTED_CREW_VERIFIED_FLAG_REQUIRED');
   let result;
   try{result=await Authenticated.ingestAuthenticated(store,verified.packet,identity)}
   catch{return bad(503,'CENTRAL_CREW_DURABLE_INGEST_UNAVAILABLE')}
   if(!result?.ok)return bad(result?.reason==='TRANSPORT_NOT_AUTHORIZED'?403:result?.retryable?503:422,clean(result?.reason)||'CREW_EVIDENCE_NOT_ACCEPTED');
   if(result.acknowledgement_kind!=='CREW_EVIDENCE_RECEIPT'||!result.durable_store?.etag)return bad(503,'COMMITTED_CREW_RECEIPT_NOT_CONFIRMED');
   const receiptId='crew-evidence:'+digest({source_app:packet.source_app,event_ids:verified.packet.events.map(e=>e.event_id).sort(),etag:result.durable_store.etag}).slice(0,24);
   return response(200,{ok:true,acknowledgement_kind:result.acknowledgement_kind,receipt_id:receiptId,
     receipt_scope:{family_id:identity.family_id,member_id:packet.context.member_id},source_app:packet.source_app,
     imported_event_ids:result.imported||[],duplicate_event_ids:result.duplicates||[],storage_confirmed:true,
     relationship_auto_commit:false,learning_engine_state_mutated:false});
 }});
}
module.exports=Object.freeze({VERSION,ENDPOINT,MAX_BODY_BYTES,create,scrub,shapeValid,sameScope});
