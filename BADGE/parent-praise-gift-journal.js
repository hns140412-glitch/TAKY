'use strict';

// Trusted Node-only persistence capability for family praise gift receipts.
// Must be invoked AFTER server-origin, parent session, target-child membership
// and approved family praise badge checks in parent-praise-gift.js.
// This is a GIFT JOURNAL, not Achievement Award Ledger or child gem balance.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const CONTRACT='TAKY_PARENT_PRAISE_GIFT_JOURNAL_V1';
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const sign=(key,s)=>crypto.createHmac('sha256',key).update(s).digest('hex');
const clean=s=>typeof s==='string'?s.trim():'';
const same=(a,b)=>typeof a==='string'&&typeof b==='string'&&
  /^[0-9a-f]{64}$/.test(a)&&/^[0-9a-f]{64}$/.test(b)&&
  crypto.timingSafeEqual(Buffer.from(a,'hex'),Buffer.from(b,'hex'));
const fail=reason=>({ok:false,reason});
function createParentGiftJournal({directory,family_id,signingKey,now}={}){
  const family=clean(family_id);
  if(!family||family!==family_id||family.length>128)throw Error('FAMILY_SCOPE_REQUIRED');
  if(!clean(directory)||!path.isAbsolute(directory))throw Error('ABSOLUTE_DIRECTORY_REQUIRED');
  if(!Buffer.isBuffer(signingKey)||signingKey.length<32)throw Error('TRUSTED_SIGNING_KEY_REQUIRED');
  if(now!==undefined&&typeof now!=='function')throw Error('CLOCK_INVALID');
  const time=now||(()=>new Date().toISOString());
  fs.mkdirSync(directory,{recursive:true,mode:0o700});
  const file=path.join(directory,hash('PRAISE_JOURNAL\n'+family)+'.json');
  const genesis=sign(signingKey,'PRAISE_GENESIS\n'+family);
  const empty=()=>({contract:CONTRACT,family_id:family,checkpoint:genesis,rows:[]});
  const identity=r=>hash('PRAISE_GIFT\n'+family+'\n'+r.giver_parent_id+'\n'+r.idempotency_key);
  function normalize(input={}){
    if(!input||typeof input!=='object'||Array.isArray(input))return null;
    if(input.contract!=='TAKY_PARENT_PRAISE_GIFT_V1'||input.source!=='PARENT_PRAISE'||
       input.family_id!==family||!clean(input.giver_parent_id)||
       !clean(input.receiver_child_id)||!clean(input.idempotency_key)||
       input.idempotency_key.length<8||input.idempotency_key.length>128||
       typeof input.message!=='string'||input.message.length>200)return null;
    if([input.giver_parent_id,input.receiver_child_id,input.idempotency_key].some(
      x=>x!==clean(x)||x.length>128))return null;
    if(input.kind==='GEM_GIFT'){
      if(!Number.isInteger(input.gem_count)||input.gem_count<1||input.gem_count>5||
         input.badge_id!==undefined)return null;
      return {contract:input.contract,source:input.source,family_id:family,
        giver_parent_id:input.giver_parent_id,receiver_child_id:input.receiver_child_id,
        idempotency_key:input.idempotency_key,message:input.message,kind:input.kind,
        gem_count:input.gem_count};
    }
    if(input.kind==='PRAISE_BADGE_GIFT'){
      if(!clean(input.badge_id)||input.badge_id!==clean(input.badge_id)||
        input.badge_id.length>128||input.gem_count!==undefined)return null;
      return {contract:input.contract,source:input.source,family_id:family,
        giver_parent_id:input.giver_parent_id,receiver_child_id:input.receiver_child_id,
        idempotency_key:input.idempotency_key,message:input.message,kind:input.kind,
        badge_id:input.badge_id};
    }
    return null;
  }
  function readVerified(){
    const data=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):empty();
    if(data.contract!==CONTRACT||data.family_id!==family||!Array.isArray(data.rows))
      throw Error('PRAISE_JOURNAL_SCOPE_INVALID');
    let previous=genesis;
    const ids=new Set();
    for(let i=0;i<data.rows.length;i++){
      const row=data.rows[i],r=row?.record;
      const normalized=normalize(r);
      if(!r||!normalized||r.sequence!==i||r.gift_id!==identity(r)||
         r.family_id!==family||r.previous_digest!==previous||
         !clean(r.accepted_at)||ids.has(r.gift_id)||
         !same(row.digest,sign(signingKey,previous+'\n'+JSON.stringify(r))))
        throw Error('PRAISE_JOURNAL_INTEGRITY_INVALID');
      ids.add(r.gift_id);
      previous=row.digest;
    }
    if(!same(data.checkpoint,previous))throw Error('PRAISE_JOURNAL_CHECKPOINT_INVALID');
    return data;
  }
  function appendGiftRecord(input){
    const record=normalize(input);
    if(!record)return fail('GIFT_RECORD_SCHEMA_OR_AMOUNT_INVALID');
    const gift_id=identity(record);
    const lock=file+'.lock';let fd=null,temp=null;
    try{
      fd=fs.openSync(lock,'wx',0o600);
      const data=readVerified();
      const existing=data.rows.find(row=>row.record.gift_id===gift_id);
      if(existing){
        const prior=normalize(existing.record);
        if(JSON.stringify(prior)!==JSON.stringify(record))return fail('CONFLICTING_IDEMPOTENCY_KEY');
        return {ok:true,persisted:true,idempotent:true,gift_id,
          family_id:family,receiver_child_id:record.receiver_child_id,
          idempotency_key:record.idempotency_key,kind:record.kind,
          ...(record.kind==='GEM_GIFT'?{gem_count:record.gem_count}:{badge_id:record.badge_id})};
      }
      const accepted_at=time();
      if(!clean(accepted_at))return fail('TRUSTED_TIME_UNAVAILABLE');
      const row={...record,sequence:data.rows.length,gift_id,accepted_at,
        previous_digest:data.checkpoint};
      const digest=sign(signingKey,data.checkpoint+'\n'+JSON.stringify(row));
      const updated={...data,rows:[...data.rows,{record:row,digest}],checkpoint:digest};
      temp=file+'.tmp-'+crypto.randomUUID();
      const tmpFd=fs.openSync(temp,'wx',0o600);
      try{fs.writeFileSync(tmpFd,JSON.stringify(updated,null,2)+'\n');fs.fsyncSync(tmpFd)}
      finally{fs.closeSync(tmpFd)}
      fs.renameSync(temp,file);temp=null;
      const dirFd=fs.openSync(directory,'r');
      try{fs.fsyncSync(dirFd)}finally{fs.closeSync(dirFd)}
      return {ok:true,persisted:true,idempotent:false,gift_id,family_id:family,
        receiver_child_id:record.receiver_child_id,idempotency_key:record.idempotency_key,
        kind:record.kind,
        ...(record.kind==='GEM_GIFT'?{gem_count:record.gem_count}:{badge_id:record.badge_id})};
    }catch{return fail('GIFT_JOURNAL_LOCK_OR_INTEGRITY_OR_WRITE_FAILED')}
    finally{
      if(temp){try{fs.unlinkSync(temp)}catch{}}
      if(fd!==null){fs.closeSync(fd);fs.unlinkSync(lock)}
    }
  }
  function readGiftHistory(){
    const data=readVerified();
    return {contract:CONTRACT,family_id:family,checkpoint:data.checkpoint,
      rows:data.rows.map(row=>JSON.parse(JSON.stringify(row)))};
  }
  return Object.freeze({contract:CONTRACT,family_id:family,appendGiftRecord,readGiftHistory});
}
module.exports=Object.freeze({CONTRACT,createParentGiftJournal});
