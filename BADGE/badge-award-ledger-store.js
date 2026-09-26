'use strict';

/**
 * Node-only durable source adapter. The caller MUST supply both a trusted, synchronous
 * Achievement Decision verifier and an explicit active-badge authorization predicate.
 * Browser JS, candidate observations and a user-supplied "approved" flag are not trusted.
 * The signing key belongs to the trusted runtime, never frontend code or this repository.
 */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const SOURCE_CONTRACT='TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1';
const STORE_CONTRACT='TAKY_BADGE_AWARD_LEDGER_STORE_V1';
const clean=v=>typeof v==='string'?v.trim():'';
const deny=(reason)=>({ok:false,reason});
const hmac=(secret,s)=>crypto.createHmac('sha256',secret).update(s).digest('hex');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const same=(a,b)=>typeof a==='string'&&typeof b==='string'&&
  a.length===64&&b.length===64&&crypto.timingSafeEqual(Buffer.from(a,'hex'),Buffer.from(b,'hex'));
const scopeKey=(family,child,badge)=>hash(family+'\0'+child+'\0'+badge);
const genesis=(secret,family,child,badge)=>hmac(secret,'GENESIS\n'+family+'\n'+child+'\n'+badge);

const isSignedUtcInstant=value=>typeof value==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value)&&Number.isFinite(Date.parse(value))&&new Date(value).toISOString()===value;

function createLedger({directory,family_id,signingKey,verifyDecision,isBadgeActive,now}={}){
  if(!clean(directory)||!path.isAbsolute(directory))throw Error('ABSOLUTE_LEDGER_DIRECTORY_REQUIRED');
  const family=clean(family_id);
  if(!family||family!==family_id||family.length>128)throw Error('EXPLICIT_FAMILY_SCOPE_REQUIRED');
  if(!Buffer.isBuffer(signingKey)||signingKey.length<32)throw Error('TRUSTED_SIGNING_KEY_REQUIRED');
  if(typeof verifyDecision!=='function'||typeof isBadgeActive!=='function')
    throw Error('TRUSTED_DECISION_AND_ACTIVE_CATALOG_CAPABILITIES_REQUIRED');
  if(now!==undefined&&typeof now!=='function')throw Error('TRUSTED_AWARD_CLOCK_REQUIRED');
  const trustedNow=now||(()=>new Date().toISOString());
  fs.mkdirSync(directory,{recursive:true,mode:0o700});
  const file=(child,badge)=>path.join(directory,scopeKey(family,child,badge)+'.json');
  const validScope=(child,badge)=>clean(child)===child&&clean(badge)===badge&&child.length<=128&&badge.length<=128;
  const empty=(child,badge)=>({
    contract:STORE_CONTRACT,family_id:family,child_id:child,badge_id:badge,
    rows:[],checkpoint:genesis(signingKey,family,child,badge)
  });
  function readVerified(child,badge){
    if(!validScope(child,badge))throw Error('LEDGER_SCOPE_REQUIRED');
    const f=file(child,badge);
    const data=fs.existsSync(f)?JSON.parse(fs.readFileSync(f,'utf8')):empty(child,badge);
    if(data.contract!==STORE_CONTRACT||data.family_id!==family||data.child_id!==child||data.badge_id!==badge||!Array.isArray(data.rows))
      throw Error('LEDGER_SCOPE_OR_SHAPE_INVALID');
    let previous=genesis(signingKey,family,child,badge);
    const decisions=new Set(),awards=new Set();
    for(let i=0;i<data.rows.length;i++){
      const row=data.rows[i],receipt=row?.record||{};
      if(!row||row.record?.ledger_sequence!==i||
        receipt.family_id!==family||receipt.child_id!==child||receipt.badge_id!==badge||
        receipt.award_status!=='AWARDED'||receipt.decision_status!=='APPROVED'||
        receipt.award_kind!==(i===0?'INITIAL_AWARD':'REAWARD')||
        !clean(receipt.decision_id)||!clean(receipt.decision_ref)||
        !clean(receipt.award_id)||!clean(receipt.approved_at)||
        (receipt.awarded_at!==undefined&&!isSignedUtcInstant(receipt.awarded_at))||
        decisions.has(receipt.decision_id)||awards.has(receipt.award_id)||
        receipt.previous_digest!==previous||
        receipt.award_id!==hash('AWARD\n'+family+'\n'+child+'\n'+badge+'\n'+receipt.decision_id)||
        !same(row.digest,hmac(signingKey,previous+'\n'+JSON.stringify(receipt))))
        throw Error('LEDGER_INTEGRITY_OR_SEQUENCE_FAILED');
      decisions.add(receipt.decision_id);awards.add(receipt.award_id);
      previous=row.digest;
    }
    if(!same(previous,data.checkpoint))throw Error('LEDGER_CHECKPOINT_INVALID');
    return data;
  }
  function appendApprovedDecision(input){
    let checked;
    try{checked=verifyDecision(input)}catch{return deny('TRUSTED_ACHIEVEMENT_DECISION_VERIFICATION_FAILED')}
    if(checked?.ok!==true||!checked.receipt)return deny('APPROVED_DECISION_REQUIRED');
    const r=checked.receipt;
    const child=clean(r.child_id),badge=clean(r.badge_id);
    if(!validScope(child,badge)||r.child_id!==child||r.badge_id!==badge)
      return deny('CHILD_BADGE_SCOPE_REQUIRED');
    if(r.decision_status!=='APPROVED'||!clean(r.decision_id)||
      !clean(r.decision_ref)||!clean(r.approved_at)||!['INITIAL_AWARD','REAWARD'].includes(r.award_kind))
      return deny('APPROVED_DECISION_RECEIPT_INCOMPLETE');
    if(clean(r.family_id)!==family)return deny('DECISION_FAMILY_SCOPE_MISMATCH');
    try{if(isBadgeActive({family_id:family,child_id:child,badge_id:badge,decision:r})!==true)
      return deny('BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED')}
    catch{return deny('BADGE_AUTHORIZATION_FAILED')}
    const f=file(child,badge),lock=f+'.lock';let lockFd=null,temp=null;
    // Exclusive OS-level lock prevents concurrent same-scope writers in separate processes.
    try{
      lockFd=fs.openSync(lock,'wx',0o600);
      const data=readVerified(child,badge);
      if(data.rows.some(x=>x.record.decision_id===r.decision_id))
        return deny('DUPLICATE_APPROVED_DECISION');
      const sequence=data.rows.length,neededKind=sequence===0?'INITIAL_AWARD':'REAWARD';
      if(r.award_kind!==neededKind)return deny('AWARD_KIND_OUT_OF_SEQUENCE');
      const awardId=hash('AWARD\n'+family+'\n'+child+'\n'+badge+'\n'+r.decision_id);
      let awardedAt;
      try{awardedAt=trustedNow();}catch{return deny('TRUSTED_AWARD_TIME_UNAVAILABLE')}
      if(!isSignedUtcInstant(awardedAt))return deny('TRUSTED_AWARD_TIME_INVALID');
      const record={
        ledger_sequence:sequence,award_id:awardId,decision_id:r.decision_id,
        family_id:family,
        decision_ref:r.decision_ref,child_id:child,badge_id:badge,
        decision_status:'APPROVED',award_status:'AWARDED',award_kind:r.award_kind,
        approved_at:r.approved_at,previous_digest:data.checkpoint,
        awarded_at:awardedAt
      };
      const digest=hmac(signingKey,data.checkpoint+'\n'+JSON.stringify(record));
      const updated={...data,rows:[...data.rows,{record,digest}],checkpoint:digest};
      temp=f+'.tmp-'+crypto.randomUUID();
      const fd=fs.openSync(temp,'wx',0o600);
      try{fs.writeFileSync(fd,JSON.stringify(updated,null,2)+'\n');fs.fsyncSync(fd)}finally{fs.closeSync(fd)}
      fs.renameSync(temp,f);temp=null;
      const dirFd=fs.openSync(directory,'r');
      try{fs.fsyncSync(dirFd)}finally{fs.closeSync(dirFd)}
      return {ok:true,award_id:awardId,ledger_sequence:sequence,checkpoint:digest,awarded_at:awardedAt};
    }catch{return deny('LEDGER_LOCK_OR_DURABLE_WRITE_FAILED')}
    finally{
      if(temp){try{fs.unlinkSync(temp)}catch{}}
      if(lockFd!==null){fs.closeSync(lockFd);fs.unlinkSync(lock)}
    }
  }
  const source=Object.freeze({
    contract:SOURCE_CONTRACT,family_id:family,
    async loadCompleteHistory({child_id,badge_id}={}){
      const data=readVerified(child_id,badge_id);
      return {kind:'COMPLETE_CHILD_BADGE_AWARD_HISTORY',complete:true,
        family_id:family,child_id,badge_id,row_count:data.rows.length,checkpoint:data.checkpoint,
        rows:data.rows.map(row=>JSON.parse(JSON.stringify(row)))};
    },
    async verifyAwardRow(row,{child_id,badge_id,checkpoint}={}){
      let data;
      try{data=readVerified(child_id,badge_id)}catch{return deny('LEDGER_INTEGRITY_FAILED')}
      if(!same(checkpoint,data.checkpoint)||!Number.isSafeInteger(row?.record?.ledger_sequence))
        return deny('AWARD_SNAPSHOT_STALE_OR_ROW_INVALID');
      const stored=data.rows[row.record.ledger_sequence];
      if(!stored||!same(stored.digest,row.digest)||
        JSON.stringify(stored.record)!==JSON.stringify(row.record))
        return deny('AWARD_ROW_NOT_IN_VERIFIED_LEDGER');
      const r=stored.record;
      return {ok:true,source_contract:SOURCE_CONTRACT,receipt:{
        authority:'AWARD_LEDGER',decision_status:r.decision_status,
        award_status:r.award_status,award_id:r.award_id,
        family_id:r.family_id,child_id:r.child_id,badge_id:r.badge_id,award_kind:r.award_kind,
        ledger_sequence:r.ledger_sequence,source_checkpoint:checkpoint,
        awarded_at:r.awarded_at??null,decision_approved_at:r.approved_at
      }};
    }
  });
  return Object.freeze({contract:STORE_CONTRACT,appendApprovedDecision,source});
}
module.exports=Object.freeze({STORE_CONTRACT,SOURCE_CONTRACT,createLedger});
