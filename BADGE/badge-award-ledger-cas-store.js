'use strict';

/**
 * Optional server-only CAS persistence for authenticated multi-instance Badge
 * Award Ledger. It does NOT import a Netlify SDK, select a paid service, or
 * deploy. The injected store needs atomic onlyIfNew / onlyIfMatch with ETag and
 * strongly-consistent getWithMetadata. Fail closed if those capabilities are
 * absent. NEVER expose the signing key or these write functions to browser JS.
 *
 * This is an alternative provider to the already-approved local Node store,
 * not a silent migration, replacement or second source of award authority.
 */
const crypto=require('node:crypto');
const SOURCE_CONTRACT='TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1';
const STORE_CONTRACT='TAKY_BADGE_AWARD_LEDGER_CAS_STORE_V1';
const clean=v=>typeof v==='string'?v.trim():'';
const deny=reason=>({ok:false,reason});
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const hmac=(key,s)=>crypto.createHmac('sha256',key).update(s).digest('hex');
const HEX=/^[0-9a-f]{64}$/;
const same=(a,b)=>typeof a==='string'&&typeof b==='string'&&HEX.test(a)&&HEX.test(b)&&
 crypto.timingSafeEqual(Buffer.from(a,'hex'),Buffer.from(b,'hex'));
const timestamp=s=>typeof s==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(s)&&
 Number.isFinite(Date.parse(s))&&new Date(s).toISOString()===s;
const scopeOk=s=>typeof s==='string'&&s.length>0&&s.length<=128&&s===clean(s);
function createCasAwardLedger({store,family_id,signingKey,verifyDecision,isBadgeActive,now,maxRetries=5,experimentalNonProduction=false}={}){
 // Intent guard, NOT an authentication boundary. This provider cannot satisfy
 // transactional Award Ledger invariants in a production object store.
 if(experimentalNonProduction!==true||process.env.CONTEXT==='production')
   throw Error('EXPERIMENTAL_CAS_NOT_PRODUCTION_STORAGE');
 if(!store||typeof store.getWithMetadata!=='function'||typeof store.set!=='function')
   throw Error('ATOMIC_CONDITIONAL_STORE_REQUIRED');
 if(!scopeOk(family_id))throw Error('EXPLICIT_FAMILY_SCOPE_REQUIRED');
 if(!Buffer.isBuffer(signingKey)||signingKey.length<32)throw Error('TRUSTED_SIGNING_KEY_REQUIRED');
 if(typeof verifyDecision!=='function'||typeof isBadgeActive!=='function')
   throw Error('TRUSTED_DECISION_AND_ACTIVE_CATALOG_CAPABILITIES_REQUIRED');
 if(now!==undefined&&typeof now!=='function')throw Error('TRUSTED_AWARD_CLOCK_REQUIRED');
 if(!Number.isInteger(maxRetries)||maxRetries<1||maxRetries>8)
   throw Error('BOUNDED_CAS_RETRIES_REQUIRED');
 const family=family_id;
 const clock=now||(()=>new Date().toISOString());
 const scope=(child,badge)=>scopeOk(child)&&scopeOk(badge);
 // Key location remains STABLE if a signing key is rotated. A wrong key must
 // read existing records and fail integrity, never create a parallel ledger.
 // Server scope controls prevent browser access to these object keys.
 const objectKey=(child,badge)=>'badge-award-cas/'+hash(
   'BADGE_CAS_KEY_V1\n'+family+'\n'+child+'\n'+badge);
 const genesis=(child,badge)=>hmac(signingKey,'GENESIS\n'+family+'\n'+child+'\n'+badge);
 const empty=(child,badge)=>({
   contract:STORE_CONTRACT,family_id:family,child_id:child,badge_id:badge,
   rows:[],checkpoint:genesis(child,badge)
 });
 const awardId=(child,badge,decision)=>hash('AWARD\n'+family+'\n'+child+'\n'+badge+'\n'+decision);

 function validate(data,child,badge){
   if(!data||data.contract!==STORE_CONTRACT||data.family_id!==family||
      data.child_id!==child||data.badge_id!==badge||!Array.isArray(data.rows)||
      data.rows.length>10000)throw Error('CAS_LEDGER_SCOPE_OR_SHAPE_INVALID');
   let previous=genesis(child,badge),previousTime=null;
   const decisions=new Set(),awards=new Set();
   for(let i=0;i<data.rows.length;i++){
     const row=data.rows[i],r=row?.record;
     if(!r||r.ledger_sequence!==i||r.family_id!==family||
        r.child_id!==child||r.badge_id!==badge||
        r.decision_status!=='APPROVED'||r.award_status!=='AWARDED'||
        r.award_kind!==(i===0?'INITIAL_AWARD':'REAWARD')||
        !clean(r.decision_id)||!clean(r.decision_ref)||!clean(r.approved_at)||
        !clean(r.award_id)||r.award_id!==awardId(child,badge,r.decision_id)||
        r.previous_digest!==previous||
        (r.awarded_at!==undefined&&!timestamp(r.awarded_at))||
        (previousTime&&r.awarded_at&&r.awarded_at<previousTime)||
        decisions.has(r.decision_id)||awards.has(r.award_id)||
        !same(row.digest,hmac(signingKey,previous+'\n'+JSON.stringify(r))))
       throw Error('CAS_LEDGER_INTEGRITY_OR_SEQUENCE_FAILED');
     if(r.awarded_at)previousTime=r.awarded_at;
     previous=row.digest;decisions.add(r.decision_id);awards.add(r.award_id);
   }
   if(!same(previous,data.checkpoint))throw Error('CAS_LEDGER_CHECKPOINT_INVALID');
   return data;
 }

 async function readVerified(child,badge){
   if(!scope(child,badge))throw Error('CAS_LEDGER_CHILD_BADGE_SCOPE_REQUIRED');
   const response=await store.getWithMetadata(objectKey(child,badge),
     {consistency:'strong',type:'text'});
   if(!response||typeof response!=='object')throw Error('STRONG_CAS_READ_REQUIRED');
   if(response.data===null){
     if(response.etag!=null)throw Error('CAS_ABSENT_ETAG_MISMATCH');
     return {data:empty(child,badge),etag:null};
   }
   if(typeof response.data!=='string'||!clean(response.etag))
     throw Error('CAS_PERSISTED_DATA_AND_ETAG_REQUIRED');
   let data;
   try{data=JSON.parse(response.data)}catch{throw Error('CAS_LEDGER_JSON_INVALID')}
   return {data:validate(data,child,badge),etag:response.etag};
 }

 async function appendApprovedDecision(input){
   let checked;
   try{checked=await verifyDecision(input)}
   catch{return deny('TRUSTED_ACHIEVEMENT_DECISION_VERIFICATION_FAILED')}
   if(checked?.ok!==true||!checked.receipt)return deny('APPROVED_DECISION_REQUIRED');
   const r=checked.receipt,child=r.child_id,badge=r.badge_id;
   if(!scope(child,badge))return deny('CHILD_BADGE_SCOPE_REQUIRED');
   if(r.family_id!==family)return deny('DECISION_FAMILY_SCOPE_MISMATCH');
   if(r.decision_status!=='APPROVED'||!clean(r.decision_id)||!clean(r.decision_ref)||
      !clean(r.approved_at)||!['INITIAL_AWARD','REAWARD'].includes(r.award_kind))
     return deny('APPROVED_DECISION_RECEIPT_INCOMPLETE');
   for(let attempt=0;attempt<maxRetries;attempt++){
     let allowed=false;
     try{allowed=await isBadgeActive({
       family_id:family,child_id:child,badge_id:badge,decision:r
     })===true}catch{return deny('BADGE_AUTHORIZATION_FAILED')}
     if(!allowed)return deny('BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
     let current;
     try{current=await readVerified(child,badge)}
     catch{return deny('STRONG_LEDGER_READ_OR_INTEGRITY_FAILED')}
     const data=current.data;
     if(data.rows.some(x=>x.record.decision_id===r.decision_id))
       return deny('DUPLICATE_APPROVED_DECISION');
     const sequence=data.rows.length,kind=sequence===0?'INITIAL_AWARD':'REAWARD';
     if(r.award_kind!==kind)return deny('AWARD_KIND_OUT_OF_SEQUENCE');
     let awardedAt;
     try{awardedAt=await clock()}catch{return deny('TRUSTED_AWARD_TIME_UNAVAILABLE')}
     if(!timestamp(awardedAt))return deny('TRUSTED_AWARD_TIME_INVALID');
     const previousTime=data.rows[data.rows.length-1]?.record.awarded_at;
     if(previousTime&&awardedAt<previousTime)return deny('AWARD_TIME_REGRESSION');
     const id=awardId(child,badge,r.decision_id);
     const record={ledger_sequence:sequence,award_id:id,decision_id:r.decision_id,
       family_id:family,decision_ref:r.decision_ref,child_id:child,badge_id:badge,
       decision_status:'APPROVED',award_status:'AWARDED',award_kind:r.award_kind,
       approved_at:r.approved_at,previous_digest:data.checkpoint,awarded_at:awardedAt};
     const digest=hmac(signingKey,data.checkpoint+'\n'+JSON.stringify(record));
     const next={...data,rows:[...data.rows,{record,digest}],checkpoint:digest};
     const condition=current.etag===null?{onlyIfNew:true}:{onlyIfMatch:current.etag};
     let result;
     try{result=await store.set(objectKey(child,badge),JSON.stringify(next),condition)}
     catch{return deny('ATOMIC_CAS_WRITE_FAILED')}
     if(!result||typeof result.modified!=='boolean')return deny('ATOMIC_CAS_WRITE_RESULT_UNVERIFIED');
     if(result.modified===true){
       if(!clean(result.etag))return deny('ATOMIC_CAS_COMMIT_ETAG_NOT_CONFIRMED');
       return {ok:true,award_id:id,ledger_sequence:sequence,checkpoint:digest,
         awarded_at:awardedAt,cas_etag:result.etag,attempts:attempt+1};
     }
     // Concurrent modification. Reload and verify the entire signed history,
     // NEVER overwrite with the stale read or manufacture the missing award.
   }
   return deny('CAS_CONFLICT_RETRY_REQUIRED');
 }

 const source=Object.freeze({
   contract:SOURCE_CONTRACT,family_id:family,
   async loadCompleteHistory({child_id,badge_id}={}){
     const {data}=await readVerified(child_id,badge_id);
     return {kind:'COMPLETE_CHILD_BADGE_AWARD_HISTORY',complete:true,
       family_id:family,child_id,badge_id,row_count:data.rows.length,
       checkpoint:data.checkpoint,
       rows:data.rows.map(x=>JSON.parse(JSON.stringify(x)))};
   },
   async verifyAwardRow(row,{child_id,badge_id,checkpoint}={}){
     let current;
     try{current=await readVerified(child_id,badge_id)}
     catch{return deny('CAS_LEDGER_INTEGRITY_FAILED')}
     if(!same(checkpoint,current.data.checkpoint)||
       !Number.isSafeInteger(row?.record?.ledger_sequence))
       return deny('AWARD_SNAPSHOT_STALE_OR_ROW_INVALID');
     const existing=current.data.rows[row.record.ledger_sequence];
     if(!existing||!same(existing.digest,row.digest)||
       JSON.stringify(existing.record)!==JSON.stringify(row.record))
       return deny('AWARD_ROW_NOT_IN_VERIFIED_LEDGER');
     const r=existing.record;
     return {ok:true,source_contract:SOURCE_CONTRACT,receipt:{
       authority:'AWARD_LEDGER',decision_status:r.decision_status,
       award_status:r.award_status,award_id:r.award_id,
       family_id:r.family_id,child_id:r.child_id,badge_id:r.badge_id,
       award_kind:r.award_kind,ledger_sequence:r.ledger_sequence,
       source_checkpoint:checkpoint,awarded_at:r.awarded_at??null,
       decision_approved_at:r.approved_at
     }};
   }
 });
 return Object.freeze({contract:STORE_CONTRACT,appendApprovedDecision,source});
}
module.exports=Object.freeze({SOURCE_CONTRACT,STORE_CONTRACT,createCasAwardLedger});
