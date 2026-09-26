'use strict';
/**
 * Evidence-only browser composition. No implicit event producer, login,
 * background polling, or Planner/app_state queue ownership.
 * The host must supply a trusted selected-member session and central token.
 */
const Outbox=require('./scoped-evidence-outbox.js');
const IndexedDB=require('./indexeddb-evidence-outbox-store.js');
const Client=require('./pwa-central-evidence-ack-client.js');
const VERSION='TAKY_PWA_SCOPED_EVIDENCE_PIPELINE_V1';
const clean=x=>typeof x==='string'?x.trim():'';
function create({indexedDB,dbName,storageAdapter=null,endpointUrl,fetchImpl,tokenProvider,
 sessionProvider,clock=Date.now,leaseMs=30000}={}){
 const storage=storageAdapter||IndexedDB.create({indexedDB,dbName});
 if(typeof storage?.read!=='function'||typeof storage?.compareAndSwap!=='function'||
    typeof storage?.close!=='function')throw Error('PIPELINE_PERSISTENT_STORAGE_REQUIRED');
 const queue=Outbox.create({storage,clock,leaseMs});
 const client=Client.create({endpointUrl,fetchImpl,tokenProvider,sessionProvider});
 async function activeScope(source_app){
  const session=await sessionProvider();
  if(session?.authenticated!==true||!clean(session.family_id)||
   !clean(session.selected_member_id)||!['ready-set','hide-seek','snap-pop'].includes(source_app))
   throw Error('ACTIVE_SCOPED_SESSION_REQUIRED');
  return [session.family_id,session.selected_member_id,source_app];
 }
 async function enqueue(packet){
  const scope=await activeScope(packet?.source_app);
  if(packet?.context?.family_id!==scope[0]||packet?.context?.member_id!==scope[1])
   throw Error('EVIDENCE_ENQUEUE_SESSION_SCOPE_MISMATCH');
  return queue.enqueue(packet);
 }
 async function flushOne(source_app,owner){
  const scope=await activeScope(source_app);
  if(!clean(owner))throw Error('EVIDENCE_FLUSH_OWNER_REQUIRED');
  const claimed=await queue.claim(scope,owner);
  if(!claimed)return {processed:false};
  let result;
  try{result=await client.sendPending(claimed.packet)}
  catch{result={ok:false,retryable:true,reason:'CENTRAL_CLIENT_UNAVAILABLE'}}
  const settled=await queue.settle(claimed,result);
  return {processed:true,settled:settled.updated===true,status:settled.status||null,
   reason:result.ok?'CENTRAL_ACK_VALIDATED':result.reason||'CENTRAL_SEND_FAILED'};
 }
 async function listActive(source_app){
  return queue.list(await activeScope(source_app));
 }
 return Object.freeze({version:VERSION,enqueue,flushOne,listActive,close:storage.close});
}
module.exports=Object.freeze({VERSION,create});
