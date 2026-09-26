'use strict';
/** Evidence-specific persistent outbox. The host supplies an atomic durable
 * read/CAS adapter; never share planner/app_state snapshot sync storage.
 * Queue entries are immutable packets, scoped to one family/member/app.
 * A successful central ACK is recorded only by a matching lease owner.
 */
const crypto=require('node:crypto');
const VERSION='TAKY_SCOPED_EVIDENCE_OUTBOX_V1';
const APPS=new Set(['ready-set','hide-seek','snap-pop']);
const clean=x=>typeof x==='string'?x.trim():'';
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?
 Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
const fingerprint=p=>hash(canonical(p));
const scopeOf=p=>[p?.context?.family_id,p?.context?.member_id,p?.source_app];
const same=(a,b)=>a.every((v,i)=>v===b[i]);
const valid=p=>p&&APPS.has(p.source_app)&&clean(p.packet_id)&&
 clean(p.context?.family_id)&&clean(p.context?.member_id)&&
 clean(p.event?.event_id)&&p.event.source===p.source_app;
function create({storage,clock=Date.now,leaseMs=30000}={}){
 if(typeof storage?.read!=='function'||typeof storage?.compareAndSwap!=='function')
  throw Error('ATOMIC_PERSISTENT_OUTBOX_ADAPTER_REQUIRED');
 if(typeof clock!=='function'||!Number.isInteger(leaseMs)||leaseMs<1000)
  throw Error('OUTBOX_CLOCK_AND_LEASE_REQUIRED');
 async function change(mutator){
  for(let n=0;n<12;n++){
   const r=await storage.read();
   if(!r||!Array.isArray(r.data?.entries))throw Error('OUTBOX_READ_INVALID');
   const next=structuredClone(r.data);
   const result=mutator(next);
   if(!result.write)return result.value;
   const committed=await storage.compareAndSwap(r.version,next);
   if(committed===true)return result.value;
  }
  throw Error('OUTBOX_CAS_RETRY_EXHAUSTED');
 }
 async function enqueue(packet){
  if(!valid(packet))throw Error('SCOPED_EVIDENCE_PACKET_REQUIRED');
  const immutable=structuredClone(packet),digest=fingerprint(immutable);
  return change(s=>{
   const key=immutable.source_app+':'+immutable.packet_id;
   const old=s.entries.find(x=>x.key===key);
   if(old){
    if(old.digest!==digest||!same(old.scope,scopeOf(immutable)))
     throw Error('OUTBOX_PACKET_ID_CONTENT_CONFLICT');
    return {write:false,value:{queued:false,duplicate:true,status:old.status}};
   }
   s.entries.push({key,digest,scope:scopeOf(immutable),packet:immutable,
    status:'PENDING',lease:null,receipt:null,attempts:0});
   return {write:true,value:{queued:true,duplicate:false,status:'PENDING'}};
  });
 }
 async function claim(scope,owner){
  if(!Array.isArray(scope)||scope.length!==3||!scope.every(clean)||
   !APPS.has(scope[2])||!clean(owner))throw Error('OUTBOX_CLAIM_SCOPE_REQUIRED');
  return change(s=>{
   const row=s.entries.find(x=>same(x.scope,scope)&&
    (x.status==='PENDING'||(x.status==='IN_FLIGHT'&&x.lease?.until<=clock())));
   if(!row)return {write:false,value:null};
   row.status='IN_FLIGHT';row.lease={owner,until:clock()+leaseMs};
   row.attempts++;
   return {write:true,value:{key:row.key,packet:structuredClone(row.packet),
    digest:row.digest,owner,attempts:row.attempts}};
  });
 }
 async function settle(claimed,result){
  if(!claimed||!clean(claimed.owner))throw Error('OUTBOX_CLAIM_REQUIRED');
  return change(s=>{
   const row=s.entries.find(x=>x.key===claimed.key);
   if(!row||row.status!=='IN_FLIGHT'||row.lease?.owner!==claimed.owner||
    row.digest!==claimed.digest||row.lease.until<=clock())
    return {write:false,value:{updated:false,reason:'STALE_OR_WRONG_LEASE'}};
   if(result?.ok===true){
    // sendPending() alone validates the authenticated central response;
    // the receipt must still be tied to this exact packet.
    if(!clean(result.ack_token)||!['REAL_EVIDENCE_RECEIPT',
      'OBSERVATION_INGEST_RECEIPT'].includes(result.acknowledgement_kind)||
      result.packet_id!==row.packet.packet_id||
      result.event_id!==row.packet.event.event_id)
     return {write:false,value:{updated:false,reason:'UNBOUND_ACK_DENIED'}};
    row.status='ACKED';row.receipt={
     receipt_id:result.ack_token,kind:result.acknowledgement_kind,
     observation_only:result.observation_only===true};
   }else{
    row.status=result?.retryable===false?'BLOCKED':'PENDING';
   }
   row.lease=null;
   return {write:true,value:{updated:true,status:row.status}};
  });
 }
 async function list(scope){
  const r=await storage.read();
  return r.data.entries.filter(x=>same(x.scope,scope)).map(x=>({
   key:x.key,status:x.status,attempts:x.attempts,receipt:x.receipt}));
 }
 return Object.freeze({VERSION,enqueue,claim,settle,list});
}
module.exports=Object.freeze({VERSION,create});
