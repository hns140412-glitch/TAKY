'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {createCasAwardLedger}=require('./badge-award-ledger-cas-store.js');
const {deriveFromLedger}=require('./badge-ledger-projection-bridge.js');
const {projectBadgeCalendar}=require('./badge-award-calendar.js');

class MemoryConditionalStore{
 constructor(){this.objects=new Map();this.version=0;this.conflicts=0;this.readLog=[];this.writeLog=[];this.barrier=null;this.throwWrite=false;}
 armSimultaneousPair(){
   let count=0,release;
   const wait=new Promise(ok=>{release=ok});
   this.barrier=async()=>{
     count++;
     if(count===2){this.barrier=null;release()}
     else await wait;
   };
 }
 async getWithMetadata(key,options){
   if(options?.consistency!=='strong'||options.type!=='text')throw Error('STRONG_READ_REQUIRED');
   this.readLog.push({key,options});
   const v=this.objects.get(key);
   const copy=v?{data:v.value,etag:v.etag}:{data:null,etag:null};
   const gate=this.barrier;
   if(gate)await gate();
   return copy;
 }
 async set(key,value,options={}){
   if(this.throwWrite)throw Error('REMOTE_STORE_DOWN');
   if(typeof value!=='string'||!options.onlyIfNew&&!options.onlyIfMatch)
     throw Error('ATOMIC_CONDITION_REQUIRED');
   const current=this.objects.get(key);
   const valid=options.onlyIfNew?current===undefined:current?.etag===options.onlyIfMatch;
   this.writeLog.push({key,options,valid});
   if(!valid){this.conflicts++;return {modified:false}}
   this.version++;
   const etag='"version-'+this.version+'"';
   this.objects.set(key,{value,etag});
   return {modified:true,etag};
 }
}
const family_id='FAMILY_A',child_id='CHILD_A',badge_id='APPROVED_BADGE';
const key=crypto.randomBytes(32);
const store=new MemoryConditionalStore();
const verifier=x=>x?.trusted===true?{ok:true,receipt:x.receipt}:{ok:false};
const active=({family_id:f,child_id:c,badge_id:b})=>
 f===family_id&&c===child_id&&b===badge_id;
const create=(opts={})=>createCasAwardLedger({
 store,family_id,signingKey:key,verifyDecision:verifier,isBadgeActive:active,
 now:()=> '2026-09-26T15:00:00.000Z',...opts
});
const receipt=(i,kind,changes={})=>({
 family_id,child_id,badge_id,decision_id:'decision-'+i,
 decision_ref:'TRUSTED_DECISION_'+i,decision_status:'APPROVED',
 award_kind:kind,approved_at:'2026-09-25T10:00:00Z',...changes
});
const award=(ledger,i,kind,changes={},trusted=true)=>
 ledger.appendApprovedDecision({trusted,receipt:receipt(i,kind,changes)});
const projection=(ledger)=>deriveFromLedger({
 source:ledger.source,child_id,badge_id,tier_order:['GREEN','BLUE','RED','GOLD','PLATINUM']
});
(async()=>{
 assert.throws(()=>createCasAwardLedger({family_id,signingKey:key,
   verifyDecision:verifier,isBadgeActive:active}),/ATOMIC_CONDITIONAL_STORE_REQUIRED/);
 assert.throws(()=>create({signingKey:Buffer.alloc(3)}),/TRUSTED_SIGNING_KEY_REQUIRED/);
 assert.throws(()=>create({maxRetries:0}),/BOUNDED_CAS_RETRIES_REQUIRED/);
 assert.throws(()=>create({maxRetries:9}),/BOUNDED_CAS_RETRIES_REQUIRED/);
 let original=create();
 let state=await projection(original);
 assert.equal(state.ok,true);assert.equal(state.ownership_state,'LOCKED');
 assert.equal((await award(original,1,'INITIAL_AWARD',{},false)).reason,'APPROVED_DECISION_REQUIRED');
 assert.equal((await award(original,1,'INITIAL_AWARD',{family_id:'FAMILY_B'})).reason,'DECISION_FAMILY_SCOPE_MISMATCH');
 assert.equal((await award(original,1,'INITIAL_AWARD',{badge_id:'DRAFT_001'})).reason,'BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
 assert.equal((await award(original,1,'INITIAL_AWARD',{child_id:'CHILD_B'})).reason,'BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
 assert.equal((await award(original,1,'REAWARD')).reason,'AWARD_KIND_OUT_OF_SEQUENCE');
 const first=await award(original,1,'INITIAL_AWARD');
 assert.equal(first.ok,true);assert.equal(first.ledger_sequence,0);
 assert.equal(first.awarded_at,'2026-09-26T15:00:00.000Z');
 assert.equal((await award(original,1,'INITIAL_AWARD')).reason,'DUPLICATE_APPROVED_DECISION');
 assert.equal((await award(original,2,'INITIAL_AWARD')).reason,'AWARD_KIND_OUT_OF_SEQUENCE');
 const earlier=await original.source.loadCompleteHistory({child_id,badge_id});
 assert.equal(earlier.row_count,1);
 assert.ok(earlier.rows[0].record.awarded_at!==earlier.rows[0].record.approved_at);
 state=await projection(create());
 assert.equal(state.ok,true);assert.equal(state.state.star_count,0);
 // Force two separate workers to read the SAME strong-consistency ETag.
 store.armSimultaneousPair();
 const parallel=await Promise.all([award(create(),2,'REAWARD'),award(create(),3,'REAWARD')]);
 assert.ok(parallel.every(x=>x.ok===true),JSON.stringify(parallel));
 assert.deepEqual(parallel.map(x=>x.ledger_sequence).sort(),[1,2]);
 assert.equal(store.conflicts,1);
 assert.ok(parallel.some(x=>x.attempts===2));
 const full=await original.source.loadCompleteHistory({child_id,badge_id});
 assert.equal(full.row_count,3);
 assert.equal(new Set(full.rows.map(x=>x.record.decision_id)).size,3);
 assert.deepEqual(full.rows.map(x=>x.record.ledger_sequence),[0,1,2]);
 assert.equal((await original.source.verifyAwardRow(earlier.rows[0],
   {child_id,badge_id,checkpoint:earlier.checkpoint})).ok,false);
 assert.equal((await original.source.verifyAwardRow(full.rows[2],
   {child_id,badge_id,checkpoint:full.checkpoint})).ok,true);
 // Duplicate concurrent requests can never produce two receipts.
 store.armSimultaneousPair();
 const duplicates=await Promise.all([award(create(),4,'REAWARD'),award(create(),4,'REAWARD')]);
 assert.equal(duplicates.filter(x=>x.ok).length,1);
 assert.equal(duplicates.filter(x=>x.reason==='DUPLICATE_APPROVED_DECISION').length,1);
 assert.equal((await original.source.loadCompleteHistory({child_id,badge_id})).row_count,4);
 state=await projection(original);
 assert.equal(state.ok,true);assert.equal(state.verified_awards,4);
 assert.equal(state.state.star_count,3);
 assert.equal(state.history.length,4);
 const month=projectBadgeCalendar({family_id,child_id,month:'2026-09',history:state.history});
 assert.equal(month.ok,true);
 assert.equal(month.days.find(x=>x.date==='2026-09-27').award_count,4);
 assert.equal(month.summary.first_acquisitions,1);
 assert.equal(month.summary.reacquisitions,3);
 assert.equal(store.readLog.every(x=>x.options.consistency==='strong'),true);
 assert.equal(store.writeLog.every(x=>x.options.onlyIfNew===true||typeof x.options.onlyIfMatch==='string'),true);
 const storageKey=[...store.objects.keys()][0],saved=store.objects.get(storageKey);
 assert.ok(storageKey.startsWith('badge-award-cas/'));
 assert.ok(!storageKey.includes('CHILD_A')&&!storageKey.includes('FAMILY_A'));
 const corrupted=JSON.parse(saved.value);
 corrupted.rows[1].record.award_kind='INITIAL_AWARD';
 store.objects.set(storageKey,{value:JSON.stringify(corrupted),etag:saved.etag});
 assert.equal((await projection(original)).ok,false);
 assert.equal((await award(original,5,'REAWARD')).reason,'STRONG_LEDGER_READ_OR_INTEGRITY_FAILED');
 store.objects.set(storageKey,saved);
 assert.equal((await projection(original)).ok,true);
 // A mistaken key rotation must NOT open a parallel empty ledger.
 const wrong=create({signingKey:crypto.randomBytes(32)});
 assert.equal((await projection(wrong)).ok,false);
 assert.equal((await award(wrong,5,'REAWARD')).reason,'STRONG_LEDGER_READ_OR_INTEGRITY_FAILED');
 const foreign=createCasAwardLedger({
   store,family_id:'FAMILY_B',signingKey:key,verifyDecision:verifier,
   isBadgeActive:()=>false
 });
 assert.equal((await deriveFromLedger({source:foreign.source,child_id,badge_id})).ownership_state,'LOCKED');
 // The same signed document cannot be transplanted into another family scope.
 const keyForForeign='badge-award-cas/'+crypto.createHash('sha256').update(
   'BADGE_CAS_KEY_V1\nFAMILY_B\n'+child_id+'\n'+badge_id).digest('hex');
 store.objects.set(keyForForeign,saved);
 assert.equal((await deriveFromLedger({source:foreign.source,child_id,badge_id})).ok,false);
 store.throwWrite=true;
 assert.equal((await award(original,6,'REAWARD')).reason,'ATOMIC_CAS_WRITE_FAILED');
 store.throwWrite=false;
 assert.equal((await original.source.loadCompleteHistory({child_id,badge_id})).row_count,4);
 assert.equal((await award(create({now:()=> 'invalid'}),7,'REAWARD')).reason,'TRUSTED_AWARD_TIME_INVALID');
 assert.equal((await award(create({now:()=> '2026-09-26T14:59:59.000Z'}),8,'REAWARD')).reason,'AWARD_TIME_REGRESSION');
 console.log('BADGE_CAS_LEDGER_PASS: signed source replay, strong reads, real ETag CAS conflicts, two concurrent awards retained, duplicate idempotency, key rotation failure, family tamper denial, KST month');
})().catch(e=>{console.error(e);process.exitCode=1});
