'use strict';

/**
 * Evidence-only pending-outbox HTTP transport. Do not reuse Ready's
 * planner/app_state snapshot sync queue as Learning Engine evidence.
 * App queue ownership/persistence remains with each specialist PWA.
 * This adapter NEVER marks a queue entry ACKED itself; callers may do so
 * only after an authenticated, scope-matched, durable central receipt.
 */
const VERSION='TAKY_PWA_CENTRAL_EVIDENCE_ACK_CLIENT_V1';
const APPS=new Set(['ready-set','hide-seek','snap-pop']);
const RECEIPTS=new Set(['REAL_EVIDENCE_RECEIPT','OBSERVATION_INGEST_RECEIPT']);
const clean=x=>typeof x==='string'?x.trim():'';
const validPacket=p=>p&&APPS.has(p.source_app)&&clean(p.packet_id)&&
 clean(p?.context?.family_id)&&clean(p?.context?.member_id)&&
 clean(p?.event?.event_id)&&p?.event?.source===p.source_app;

function validateAck(packet,status,body={}){
 if(status!==200||body?.ok!==true||
    body.storage_confirmed!==true||
    !RECEIPTS.has(body.acknowledgement_kind)||
    !clean(body.receipt_id)||body.source_app!==packet.source_app||
    body.receipt_scope?.family_id!==packet.context.family_id||
    body.receipt_scope?.member_id!==packet.context.member_id||
    typeof body.duplicate!=='boolean')
   return {ok:false,reason:'CENTRAL_COMMITTED_ACK_SCOPE_INVALID'};
 return {ok:true,ack_token:body.receipt_id,
   acknowledgement_kind:body.acknowledgement_kind,duplicate:body.duplicate,
   observation_only:body.acknowledgement_kind==='OBSERVATION_INGEST_RECEIPT'};
}
function create({endpointUrl,fetchImpl,tokenProvider,sessionProvider}={}){
 let endpoint;
 try{
   endpoint=new URL(endpointUrl);
   if(endpoint.protocol!=='https:'||endpoint.username||endpoint.password||
      endpoint.search||endpoint.hash||endpoint.pathname!=='/api/learning/evidence')
     throw Error('INVALID');
 }catch{throw Error('EXPLICIT_CENTRAL_HTTPS_EVIDENCE_ENDPOINT_REQUIRED')}
 if(typeof fetchImpl!=='function'||typeof tokenProvider!=='function'||
    typeof sessionProvider!=='function')
   throw Error('PWA_TRUSTED_SESSION_FETCH_AND_TOKEN_PROVIDERS_REQUIRED');
 async function sendPending(packet){
   if(!validPacket(packet))return {ok:false,retryable:false,reason:'EVIDENCE_PACKET_REQUIRED'};
   const session=await sessionProvider();
   if(session?.authenticated!==true||
      session.family_id!==packet.context.family_id||
      session.selected_member_id!==packet.context.member_id)
     return {ok:false,retryable:false,reason:'ACTIVE_FAMILY_MEMBER_SCOPE_REQUIRED'};
   let token;
   try{token=await tokenProvider()}catch{return {ok:false,retryable:true,reason:'TOKEN_REFRESH_UNAVAILABLE'}}
   if(!clean(token)||token.length>8192)
     return {ok:false,retryable:false,reason:'AUTH_TOKEN_REQUIRED'};
   let response,body;
   try{
     response=await fetchImpl(endpoint.href,{
       method:'POST',headers:{
         'Content-Type':'application/json','Accept':'application/json',
         Authorization:'Bearer '+token
       },credentials:'omit',redirect:'error',cache:'no-store',
       body:JSON.stringify(packet)
     });
     body=await response.json();
   }catch{return {ok:false,retryable:true,reason:'CENTRAL_HTTP_OR_RESPONSE_UNAVAILABLE'}}
   if(response.status!==200){
     return {ok:false,retryable:response.status===429||response.status===503||
       response.status>=500,
       reason:response.status===401||response.status===403
         ?'CENTRAL_AUTHORIZATION_REQUIRED':'CENTRAL_HTTP_'+response.status};
   }
   const ack=validateAck(packet,response.status,body);
   return ack.ok?ack:{...ack,retryable:true};
 }
 return Object.freeze({version:VERSION,sendPending});
}
module.exports=Object.freeze({VERSION,validateAck,create});
