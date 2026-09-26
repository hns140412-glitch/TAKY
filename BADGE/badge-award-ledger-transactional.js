'use strict';

/**
 * Server-only, provider-neutral PostgreSQL transaction adapter for Badge Award
 * Ledger. A trusted runtime must inject a database pool, approved immutable
 * Decision verifier, active catalogue/membership predicate and signing key.
 * Does NOT import pg, configure credentials, run migrations, or deploy.
 * Row-level serialization occurs INSIDE the database, not process/local locks.
 */
const crypto=require('node:crypto');
const STORE_CONTRACT='TAKY_BADGE_AWARD_LEDGER_POSTGRES_V1';
const SOURCE_CONTRACT='TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1';
const SQL=Object.freeze({
  insertHead:'/* BADGE_INSERT_HEAD */ INSERT INTO taky_badge_award_head (family_id,child_id,badge_id,award_count,checkpoint) VALUES ($1,$2,$3,0,$4) ON CONFLICT (family_id,child_id,badge_id) DO NOTHING',
  headLock:'/* BADGE_HEAD_LOCK */ SELECT award_count,checkpoint FROM taky_badge_award_head WHERE family_id=$1 AND child_id=$2 AND badge_id=$3 FOR UPDATE',
  headRead:'/* BADGE_HEAD_READ */ SELECT award_count,checkpoint FROM taky_badge_award_head WHERE family_id=$1 AND child_id=$2 AND badge_id=$3',
  eventsRead:'/* BADGE_EVENTS_READ */ SELECT ledger_sequence,decision_id,award_id,record_json,digest FROM taky_badge_award_event WHERE family_id=$1 AND child_id=$2 AND badge_id=$3 ORDER BY ledger_sequence ASC',
  insertEvent:'/* BADGE_INSERT_EVENT */ INSERT INTO taky_badge_award_event (family_id,child_id,badge_id,ledger_sequence,decision_id,award_id,record_json,digest) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)',
  updateHead:'/* BADGE_UPDATE_HEAD */ UPDATE taky_badge_award_head SET award_count=$4,checkpoint=$5 WHERE family_id=$1 AND child_id=$2 AND badge_id=$3 AND award_count=$6 AND checkpoint=$7'
});
const clean=v=>typeof v==='string'?v.trim():'';
const scoped=v=>typeof v==='string'&&v===clean(v)&&v.length>0&&v.length<=128;
const deny=reason=>({ok:false,reason});
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const hmac=(key,s)=>crypto.createHmac('sha256',key).update(s).digest('hex');
const HEX=/^[0-9a-f]{64}$/;
const equal=(a,b)=>typeof a==='string'&&typeof b==='string'&&HEX.test(a)&&HEX.test(b)&&
 crypto.timingSafeEqual(Buffer.from(a,'hex'),Buffer.from(b,'hex'));
const timestamp=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(v)&&
 Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;

function createTransactionalAwardLedger({
 pool,family_id,signingKey,verifyDecision,isBadgeActive,now
}={}){
 if(!pool||typeof pool.connect!=='function')throw Error('TRANSACTIONAL_DATABASE_POOL_REQUIRED');
 if(!scoped(family_id))throw Error('EXPLICIT_FAMILY_SCOPE_REQUIRED');
 if(!Buffer.isBuffer(signingKey)||signingKey.length<32)throw Error('TRUSTED_SIGNING_KEY_REQUIRED');
 if(typeof verifyDecision!=='function'||typeof isBadgeActive!=='function')
   throw Error('TRUSTED_DECISION_AND_ACTIVE_CATALOG_CAPABILITIES_REQUIRED');
 if(now!==undefined&&typeof now!=='function')throw Error('TRUSTED_AWARD_CLOCK_REQUIRED');
 const family=family_id,clock=now||(()=>new Date().toISOString());
 const genesis=(child,badge)=>hmac(signingKey,'GENESIS\n'+family+'\n'+child+'\n'+badge);
 const awardId=(child,badge,decision)=>hash('AWARD\n'+family+'\n'+child+'\n'+badge+'\n'+decision);
 const scope=(child,badge)=>scoped(child)&&scoped(badge);

 function validateSnapshot(head,rows,child,badge){
   const origin=genesis(child,badge);
   if(!head){
     if(rows.length!==0)throw Error('ORPHANED_AWARD_EVENTS');
     return {rows:[],count:0,checkpoint:origin};
   }
   const count=Number(head.award_count);
   if(!Number.isSafeInteger(count)||count<0||count>10000||
      !Array.isArray(rows)||rows.length!==count)throw Error('LEDGER_COUNT_MISMATCH');
   let previous=origin,lastTime=null;
   const decisions=new Set(),awards=new Set(),result=[];
   for(let i=0;i<rows.length;i++){
     const row=rows[i];
     if(typeof row.record_json!=='string'||!scoped(row.decision_id)||
        !clean(row.award_id)||!Number.isSafeInteger(Number(row.ledger_sequence))||
        Number(row.ledger_sequence)!==i)throw Error('LEDGER_EVENT_SCHEMA_INVALID');
     let r;
     try{r=JSON.parse(row.record_json)}catch{throw Error('LEDGER_EVENT_JSON_INVALID')}
     if(!r||r.ledger_sequence!==i||r.family_id!==family||
        r.child_id!==child||r.badge_id!==badge||
        r.decision_id!==row.decision_id||r.award_id!==row.award_id||
        r.award_id!==awardId(child,badge,r.decision_id)||
        r.decision_status!=='APPROVED'||r.award_status!=='AWARDED'||
        r.award_kind!==(i===0?'INITIAL_AWARD':'REAWARD')||
        !clean(r.decision_ref)||!clean(r.approved_at)||
        (r.awarded_at!==undefined&&!timestamp(r.awarded_at))||
        (lastTime&&r.awarded_at&&r.awarded_at<lastTime)||
        r.previous_digest!==previous||decisions.has(r.decision_id)||
        awards.has(r.award_id)||!equal(row.digest,hmac(signingKey,previous+'\n'+row.record_json)))
       throw Error('LEDGER_CHAIN_INTEGRITY_INVALID');
     decisions.add(r.decision_id);awards.add(r.award_id);
     if(r.awarded_at)lastTime=r.awarded_at;
     previous=row.digest;
     result.push({record:r,digest:row.digest});
   }
   if(!equal(head.checkpoint,previous))throw Error('LEDGER_HEAD_CHECKPOINT_INVALID');
   return {rows:result,count,checkpoint:previous};
 }
 async function snapshot(client,child,badge,locked){
   const ids=[family,child,badge];
   const h=await client.query(locked?SQL.headLock:SQL.headRead,ids);
   const e=await client.query(SQL.eventsRead,ids);
   if(!Array.isArray(h?.rows)||h.rows.length>1||!Array.isArray(e?.rows))
     throw Error('TRANSACTIONAL_QUERY_SHAPE_INVALID');
   return validateSnapshot(h.rows[0]||null,e.rows,child,badge);
 }
 async function readVerified(child,badge){
   if(!scope(child,badge))throw Error('LEDGER_CHILD_BADGE_SCOPE_REQUIRED');
   const client=await pool.connect();
   if(!client||typeof client.query!=='function'||typeof client.release!=='function')
     throw Error('TRANSACTIONAL_DATABASE_CLIENT_REQUIRED');
   let began=false,committed=false;
   try{
     await client.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');began=true;
     const data=await snapshot(client,child,badge,false);
     await client.query('COMMIT');committed=true;
     return data;
   }finally{
     if(began&&!committed){try{await client.query('ROLLBACK')}catch{}}
     client.release();
   }
 }
 async function appendApprovedDecision(input){
   let checked;
   try{checked=await verifyDecision(input)}
   catch{return deny('TRUSTED_ACHIEVEMENT_DECISION_VERIFICATION_FAILED')}
   if(checked?.ok!==true||!checked.receipt)return deny('APPROVED_DECISION_REQUIRED');
   const r=checked.receipt,child=r.child_id,badge=r.badge_id;
   if(!scope(child,badge))return deny('CHILD_BADGE_SCOPE_REQUIRED');
   if(r.family_id!==family)return deny('DECISION_FAMILY_SCOPE_MISMATCH');
   if(r.decision_status!=='APPROVED'||!clean(r.decision_id)||
      !clean(r.decision_ref)||!clean(r.approved_at)||
      !['INITIAL_AWARD','REAWARD'].includes(r.award_kind))
      return deny('APPROVED_DECISION_RECEIPT_INCOMPLETE');
   let client;
   try{client=await pool.connect()}catch{return deny('TRANSACTIONAL_DATABASE_UNAVAILABLE')}
   if(!client||typeof client.query!=='function'||typeof client.release!=='function')
     return deny('TRANSACTIONAL_DATABASE_CLIENT_INVALID');
   let began=false,committed=false;
   try{
     await client.query('BEGIN');began=true;
     // INSERT/ON CONFLICT handles the race to create a missing head. The
     // subsequent FOR UPDATE locks one family's one child's one badge.
     await client.query(SQL.insertHead,[family,child,badge,genesis(child,badge)]);
     const data=await snapshot(client,child,badge,true);
     if(data.rows.some(x=>x.record.decision_id===r.decision_id))
       return deny('DUPLICATE_APPROVED_DECISION');
     const sequence=data.count,kind=sequence===0?'INITIAL_AWARD':'REAWARD';
     if(r.award_kind!==kind)return deny('AWARD_KIND_OUT_OF_SEQUENCE');
     let active;
     try{active=await isBadgeActive({family_id:family,child_id:child,badge_id:badge,decision:r})===true}
     catch{return deny('BADGE_AUTHORIZATION_FAILED')}
     if(!active)return deny('BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
     let awardedAt;
     try{awardedAt=await clock()}catch{return deny('TRUSTED_AWARD_TIME_UNAVAILABLE')}
     if(!timestamp(awardedAt))return deny('TRUSTED_AWARD_TIME_INVALID');
     const previousTime=data.rows[data.rows.length-1]?.record.awarded_at;
     if(previousTime&&awardedAt<previousTime)return deny('AWARD_TIME_REGRESSION');
     const id=awardId(child,badge,r.decision_id);
     const record={
       ledger_sequence:sequence,award_id:id,decision_id:r.decision_id,
       family_id:family,decision_ref:r.decision_ref,child_id:child,badge_id:badge,
       decision_status:'APPROVED',award_status:'AWARDED',award_kind:r.award_kind,
       approved_at:r.approved_at,previous_digest:data.checkpoint,awarded_at:awardedAt
     };
     const serialized=JSON.stringify(record);
     const digest=hmac(signingKey,data.checkpoint+'\n'+serialized);
     const inserted=await client.query(SQL.insertEvent,
       [family,child,badge,sequence,r.decision_id,id,serialized,digest]);
     if(inserted?.rowCount!==1)throw Error('IMMUTABLE_EVENT_INSERT_NOT_CONFIRMED');
     const updated=await client.query(SQL.updateHead,
       [family,child,badge,sequence+1,digest,sequence,data.checkpoint]);
     if(updated?.rowCount!==1)throw Error('SIGNED_HEAD_ADVANCE_NOT_CONFIRMED');
     await client.query('COMMIT');committed=true;
     return {ok:true,award_id:id,ledger_sequence:sequence,checkpoint:digest,
       awarded_at:awardedAt,transaction:'COMMITTED'};
   }catch{return deny('TRANSACTIONAL_LEDGER_WRITE_OR_INTEGRITY_FAILED')}
   finally{
     if(began&&!committed){try{await client.query('ROLLBACK')}catch{}}
     client.release();
   }
 }
 const source=Object.freeze({
   contract:SOURCE_CONTRACT,family_id:family,
   async loadCompleteHistory({child_id,badge_id}={}){
     const data=await readVerified(child_id,badge_id);
     return {kind:'COMPLETE_CHILD_BADGE_AWARD_HISTORY',complete:true,
       family_id:family,child_id,badge_id,row_count:data.count,
       checkpoint:data.checkpoint,
       rows:data.rows.map(x=>JSON.parse(JSON.stringify(x)))};
   },
   async verifyAwardRow(row,{child_id,badge_id,checkpoint}={}){
     let data;
     try{data=await readVerified(child_id,badge_id)}
     catch{return deny('TRANSACTIONAL_LEDGER_READ_OR_INTEGRITY_FAILED')}
     if(!equal(data.checkpoint,checkpoint)||
        !Number.isSafeInteger(row?.record?.ledger_sequence))
       return deny('AWARD_SNAPSHOT_STALE_OR_ROW_INVALID');
     const stored=data.rows[row.record.ledger_sequence];
     if(!stored||!equal(stored.digest,row.digest)||
        JSON.stringify(stored.record)!==JSON.stringify(row.record))
       return deny('AWARD_ROW_NOT_IN_VERIFIED_LEDGER');
     const r=stored.record;
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
module.exports=Object.freeze({STORE_CONTRACT,SOURCE_CONTRACT,SQL,createTransactionalAwardLedger});
