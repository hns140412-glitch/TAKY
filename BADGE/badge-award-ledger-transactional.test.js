'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {SQL,createTransactionalAwardLedger}=require('./badge-award-ledger-transactional.js');
const {deriveFromLedger}=require('./badge-ledger-projection-bridge.js');
const {projectBadgeCalendar}=require('./badge-award-calendar.js');

class FakeTransactionalPool{
 constructor(){
   this.data=new Map();this.locks=new Map();this.contentions=0;
   this.failOnceOn=null;this.sqlSeen=[];
 }
 aggregateKey(f,c,b){return JSON.stringify([f,c,b]);}
 async acquire(key){
   const previous=this.locks.get(key)||Promise.resolve();
   if(this.locks.has(key))this.contentions++;
   let done;
   const current=new Promise(resolve=>{done=resolve});
   this.locks.set(key,current);
   await previous;
   return ()=>{done();if(this.locks.get(key)===current)this.locks.delete(key)};
 }
 async connect(){return new FakeClient(this)}
}
class FakeClient{
 constructor(pool){this.pool=pool;this.tx=null;this.releaseLock=null;this.key=null;this.local=null;this.released=false;}
 async query(statement,args=[]){
   this.pool.sqlSeen.push({statement,args});
   if(this.pool.failOnceOn&&statement.includes('/* '+this.pool.failOnceOn+' */')){
     this.pool.failOnceOn=null;throw Error('SIMULATED_DB_FAILURE');
   }
   if(statement.startsWith('BEGIN')){
     if(this.tx)throw Error('NESTED_TRANSACTION_FORBIDDEN');
     const readonly=statement.includes('READ ONLY');
     const snapshot=new Map([...this.pool.data].map(([k,v])=>[k,structuredClone(v)]));
     this.tx={readonly,snapshot};return {rowCount:0,rows:[]};
   }
   if(statement==='COMMIT'){
     if(!this.tx)throw Error('NO_TRANSACTION');
     if(!this.tx.readonly&&this.local)this.pool.data.set(this.key,structuredClone(this.local));
     this.releaseLock?.();this.releaseLock=null;this.tx=null;return {rowCount:0,rows:[]};
   }
   if(statement==='ROLLBACK'){
     this.releaseLock?.();this.releaseLock=null;this.tx=null;this.local=null;return {rowCount:0,rows:[]};
   }
   if(!this.tx)throw Error('TRANSACTION_REQUIRED');
   const marker=(statement.match(/^\/\* (BADGE_[A-Z_]+) \*\//)||[])[1];
   if(!marker)throw Error('UNRECOGNIZED_PARAMETERIZED_SQL');
   const [family,child,badge]=args;
   const key=this.pool.aggregateKey(family,child,badge);
   if(marker==='BADGE_INSERT_HEAD'){
     if(this.tx.readonly)throw Error('READ_ONLY');
     if(this.key&&this.key!==key)throw Error('ONE_AGGREGATE_PER_WRITE_TX');
     if(!this.releaseLock){this.releaseLock=await this.pool.acquire(key);this.key=key}
     const existing=this.pool.data.get(key);
     this.local=existing?structuredClone(existing):{
       head:{award_count:'0',checkpoint:args[3]},rows:[]
     };
     return {rowCount:existing?0:1,rows:[]};
   }
   const aggregate=this.tx.readonly?this.tx.snapshot.get(key):this.local;
   if(!this.tx.readonly&&this.key!==key)throw Error('MISSING_LOCK');
   if(marker==='BADGE_HEAD_LOCK'||marker==='BADGE_HEAD_READ'){
     if(marker==='BADGE_HEAD_LOCK'&&!this.releaseLock)throw Error('HEAD_NOT_LOCKED');
     return {rowCount:aggregate?1:0,rows:aggregate?[structuredClone(aggregate.head)]:[]};
   }
   if(marker==='BADGE_EVENTS_READ'){
     const rows=aggregate?structuredClone(aggregate.rows):[];
     return {rowCount:rows.length,rows};
   }
   if(this.tx.readonly||!aggregate)throw Error('MISSING_WRITABLE_AGGREGATE');
   if(marker==='BADGE_INSERT_EVENT'){
     const [, , ,seq,decision_id,award_id,record_json,digest]=args;
     if(aggregate.rows.length!==seq||aggregate.rows.some(x=>x.decision_id===decision_id||x.award_id===award_id))
       throw Error('DB_UNIQUE_VIOLATION');
     aggregate.rows.push({ledger_sequence:String(seq),decision_id,award_id,record_json,digest});
     return {rowCount:1,rows:[]};
   }
   if(marker==='BADGE_UPDATE_HEAD'){
     const [, , ,newCount,newCheckpoint,oldCount,oldCheckpoint]=args;
     if(Number(aggregate.head.award_count)!==oldCount||
        aggregate.head.checkpoint!==oldCheckpoint)return {rowCount:0,rows:[]};
     aggregate.head={award_count:String(newCount),checkpoint:newCheckpoint};
     return {rowCount:1,rows:[]};
   }
   throw Error('UNKNOWN_QUERY:'+marker);
 }
 release(){this.released=true}
}

const pool=new FakeTransactionalPool();
const signingKey=crypto.randomBytes(32);
const family_id='FAMILY_A',child_id='CHILD_A',badge_id='ACTIVE_BADGE';
const verifyDecision=input=>input?.trusted===true?{ok:true,receipt:input.receipt}:{ok:false};
const isBadgeActive=({family_id:f,child_id:c,badge_id:b})=>
 f===family_id&&c===child_id&&b===badge_id;
const create=(opts={})=>createTransactionalAwardLedger({
 pool,family_id,signingKey,verifyDecision,isBadgeActive,
 now:()=> '2026-09-26T15:00:00.000Z',...opts
});
const receipt=(id,kind,override={})=>({
 family_id,child_id,badge_id,decision_id:'approved-decision-'+id,
 decision_ref:'TRUSTED_OWNER_DECISION_'+id,
 decision_status:'APPROVED',award_kind:kind,
 approved_at:'2026-09-25T10:00:00Z',...override
});
const award=(store,id,kind,override={},trusted=true)=>
 store.appendApprovedDecision({trusted,receipt:receipt(id,kind,override)});
const project=(source)=>deriveFromLedger({
 source,child_id,badge_id,tier_order:['GREEN','BLUE','RED','GOLD','PLATINUM']
});

(async()=>{
 const ddl=fs.readFileSync(path.join(__dirname,'badge-award-ledger-postgres.sql'),'utf8');
 assert(ddl.includes('PRIMARY KEY (family_id,child_id,badge_id,ledger_sequence)'));
 assert(ddl.includes('UNIQUE (family_id,child_id,badge_id,decision_id)'));
 assert(ddl.includes('ON DELETE RESTRICT'));
 assert(ddl.includes('record_json text'));assert(!ddl.includes('record_json jsonb'));
 assert(SQL.headLock.includes('FOR UPDATE'));
 assert(SQL.insertHead.includes('ON CONFLICT'));
 assert(SQL.insertEvent.includes('VALUES ($1,$2,$3,$4,$5,$6,$7,$8)'));
 assert.throws(()=>createTransactionalAwardLedger({pool:null}),/TRANSACTIONAL_DATABASE_POOL_REQUIRED/);
 assert.throws(()=>create({signingKey:Buffer.alloc(8)}),/TRUSTED_SIGNING_KEY_REQUIRED/);
 const ledger=create();
 assert.equal((await project(ledger.source)).ownership_state,'LOCKED');
 assert.equal((await award(ledger,0,'INITIAL_AWARD',{},false)).reason,'APPROVED_DECISION_REQUIRED');
 assert.equal((await award(ledger,0,'INITIAL_AWARD',{family_id:'FAMILY_B'})).reason,'DECISION_FAMILY_SCOPE_MISMATCH');
 assert.equal((await award(ledger,0,'INITIAL_AWARD',{badge_id:'WORKING_DRAFT_001'})).reason,'BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
 assert.equal((await award(ledger,0,'INITIAL_AWARD',{child_id:'CHILD_B'})).reason,'BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
 assert.equal((await award(ledger,0,'REAWARD')).reason,'AWARD_KIND_OUT_OF_SEQUENCE');
 assert.equal(pool.data.size,0,'denied attempts must roll back bootstrap head');
 const first=await award(ledger,0,'INITIAL_AWARD');
 assert.equal(first.ok,true);
 assert.equal(first.transaction,'COMMITTED');
 assert.equal(first.ledger_sequence,0);
 assert.equal(first.awarded_at,'2026-09-26T15:00:00.000Z');
 assert.equal((await award(ledger,0,'INITIAL_AWARD')).reason,'DUPLICATE_APPROVED_DECISION');
 assert.equal((await award(ledger,1,'INITIAL_AWARD')).reason,'AWARD_KIND_OUT_OF_SEQUENCE');
 const one=await ledger.source.loadCompleteHistory({child_id,badge_id});
 assert.equal(one.row_count,1);
 assert.equal(one.rows[0].record.awarded_at,'2026-09-26T15:00:00.000Z');

 // Two different workers compete for a REAWARD; row-level FOR UPDATE serializes
 // complete event insert + head checkpoint update in ONE transaction.
 const [a,b]=await Promise.all([award(create(),1,'REAWARD'),award(create(),2,'REAWARD')]);
 assert.equal(a.ok,true,JSON.stringify(a));assert.equal(b.ok,true,JSON.stringify(b));
 assert.deepEqual([a.ledger_sequence,b.ledger_sequence].sort(),[1,2]);
 assert.ok(pool.contentions>=1,'second writer must wait for aggregate lock');
 assert.equal((await ledger.source.loadCompleteHistory({child_id,badge_id})).row_count,3);
 const dupe=await Promise.all([award(create(),3,'REAWARD'),award(create(),3,'REAWARD')]);
 assert.equal(dupe.filter(x=>x.ok).length,1);
 assert.equal(dupe.filter(x=>x.reason==='DUPLICATE_APPROVED_DECISION').length,1);
 assert.equal((await ledger.source.loadCompleteHistory({child_id,badge_id})).row_count,4);

 // Insert succeeds within transaction but later head update fails. Rollback must
 // erase the uncommitted inserted event, preserving the verified signed history.
 pool.failOnceOn='BADGE_UPDATE_HEAD';
 const partial=await award(create(),4,'REAWARD');
 assert.equal(partial.reason,'TRANSACTIONAL_LEDGER_WRITE_OR_INTEGRITY_FAILED');
 assert.equal((await ledger.source.loadCompleteHistory({child_id,badge_id})).row_count,4);
 assert.equal((await award(create(),4,'REAWARD')).ok,true);

 const full=await ledger.source.loadCompleteHistory({child_id,badge_id});
 assert.equal(full.row_count,5);
 assert.equal((await ledger.source.verifyAwardRow(one.rows[0],
   {child_id,badge_id,checkpoint:one.checkpoint})).ok,false);
 assert.equal((await ledger.source.verifyAwardRow(full.rows[4],
   {child_id,badge_id,checkpoint:full.checkpoint})).ok,true);
 assert.equal(full.rows.every(r=>typeof r.record.awarded_at==='string'),true);
 const projection=await project(ledger.source);
 assert.equal(projection.ok,true);
 assert.equal(projection.verified_awards,5);
 assert.equal(projection.state.star_count,4);
 const month=projectBadgeCalendar({family_id,child_id,month:'2026-09',history:projection.history});
 assert.equal(month.ok,true);
 assert.equal(month.days.find(d=>d.date==='2026-09-27').award_count,5);
 assert.equal(month.summary.first_acquisitions,1);
 assert.equal(month.summary.reacquisitions,4);

 const sameScope=pool.aggregateKey(family_id,child_id,badge_id);
 const saved=structuredClone(pool.data.get(sameScope));
 const changed=structuredClone(saved);changed.rows[1].record_json=
   changed.rows[1].record_json.replace('"REAWARD"','"INITIAL_AWARD"');
 pool.data.set(sameScope,changed);
 assert.equal((await project(ledger.source)).ok,false);
 assert.equal((await award(ledger,5,'REAWARD')).reason,'TRANSACTIONAL_LEDGER_WRITE_OR_INTEGRITY_FAILED');
 pool.data.set(sameScope,saved);

 // Wrong signing key sees same DB rows: cannot open a new invisible history.
 const wrong=create({signingKey:crypto.randomBytes(32)});
 assert.equal((await project(wrong.source)).ok,false);
 assert.equal((await award(wrong,5,'REAWARD')).reason,'TRANSACTIONAL_LEDGER_WRITE_OR_INTEGRITY_FAILED');
 const other=createTransactionalAwardLedger({
   pool,family_id:'FAMILY_B',signingKey,verifyDecision,isBadgeActive:()=>false
 });
 assert.equal((await deriveFromLedger({source:other.source,child_id,badge_id})).ownership_state,'LOCKED');
 pool.data.set(pool.aggregateKey('FAMILY_B',child_id,badge_id),saved);
 assert.equal((await deriveFromLedger({source:other.source,child_id,badge_id})).ok,false);
 assert.equal((await award(create({now:()=> 'invalid'}),5,'REAWARD')).reason,'TRUSTED_AWARD_TIME_INVALID');
 assert.equal((await award(create({now:()=> '2026-09-26T14:59:59.000Z'}),5,'REAWARD')).reason,'AWARD_TIME_REGRESSION');
 assert(pool.sqlSeen.some(x=>x.statement.includes('REPEATABLE READ READ ONLY')));
 assert(pool.sqlSeen.some(x=>x.statement==='ROLLBACK'));
 assert(pool.sqlSeen.some(x=>x.statement==='COMMIT'));
 assert(pool.sqlSeen.filter(x=>x.statement.includes('BADGE_INSERT_EVENT')).every(x=>x.args.length===8));
 assert(pool.sqlSeen.filter(x=>x.statement.includes('BADGE_HEAD_LOCK')).every(x=>x.args.length===3));
 console.log('BADGE_TRANSACTIONAL_DB_PASS: SQL constraints, row-locked two concurrent awards, duplicate denial, failed-head rollback, immutable signed read, family tamper/wrong key, KST calendar');
})().catch(e=>{console.error(e);process.exitCode=1});
