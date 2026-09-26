'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const crypto=require('node:crypto');
const {createLedger}=require('./badge-award-ledger-store.js');
const {deriveFromLedger}=require('./badge-ledger-projection-bridge.js');

const directory=fs.mkdtempSync(path.join(os.tmpdir(),'taky-badge-award-ledger-'));
const signingKey=crypto.randomBytes(32);
const child_id='CHILD_A',badge_id='ACTIVE_BADGE_1';
const verifier=input=>input?.trustedDecision===true ? {ok:true,receipt:input.receipt} : {ok:false};
const active=({child_id:member,badge_id:id})=>member==='CHILD_A'&&id==='ACTIVE_BADGE_1';
const create=(key=signingKey)=>createLedger({directory,signingKey:key,verifyDecision:verifier,isBadgeActive:active});
const receipt=(i,kind='REAWARD',override={})=>({
 decision_id:'decision-'+i,decision_ref:'DECISION_LEDGER_REF_'+i,
 child_id,badge_id,decision_status:'APPROVED',award_kind:kind,approved_at:'2026-09-26T09:00:00Z',...override
});
const award=(store,i,kind,override={},trustedDecision=true)=>
 store.appendApprovedDecision({trustedDecision,receipt:receipt(i,kind,override)});
const options={child_id,badge_id,tier_order:['GREEN','BLUE','RED','GOLD','PLATINUM']};

(async()=>{
 try{
  assert.throws(()=>createLedger({directory,verifyDecision:verifier,isBadgeActive:active}),/TRUSTED_SIGNING_KEY_REQUIRED/);
  const store=create();
  let projected=await deriveFromLedger({...options,source:store.source});
  assert.equal(projected.ok,true);
  assert.equal(projected.ownership_state,'LOCKED');
  assert.equal(award(store,0,'INITIAL_AWARD',{},false).reason,'APPROVED_DECISION_REQUIRED');
  assert.equal(award(store,0,'INITIAL_AWARD',{badge_id:'WORKING_DRAFT_001'}).reason,'BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
  assert.equal(award(store,0,'INITIAL_AWARD',{child_id:'CHILD_B'}).reason,'BADGE_NOT_ACTIVE_OR_CHILD_NOT_AUTHORIZED');
  assert.equal(award(store,0,'REAWARD').reason,'AWARD_KIND_OUT_OF_SEQUENCE');
  const first=award(store,0,'INITIAL_AWARD');
  assert.equal(first.ok,true);
  assert.equal(first.ledger_sequence,0);
  assert.equal(award(store,0,'INITIAL_AWARD').reason,'DUPLICATE_APPROVED_DECISION');
  assert.equal(award(store,1,'INITIAL_AWARD').reason,'AWARD_KIND_OUT_OF_SEQUENCE');
  projected=await deriveFromLedger({...options,source:create().source});
  assert.equal(projected.ok,true);
  assert.equal(projected.ownership_state,'EARNED');
  assert.equal(projected.state.star_count,0);
  for(let i=1;i<=5;i++)assert.equal(award(create(),i,'REAWARD').ok,true);
  projected=await deriveFromLedger({...options,source:create().source});
  assert.equal(projected.ok,true);
  assert.equal(projected.verified_awards,6);
  assert.equal(projected.state.tier,'BLUE');
  assert.equal(projected.state.star_count,0);
  const snapshot=await store.source.loadCompleteHistory({child_id,badge_id});
  assert.equal(snapshot.complete,true);
  assert.equal(snapshot.rows.length,6);
  assert.equal((await store.source.verifyAwardRow(snapshot.rows[1],{child_id,badge_id,checkpoint:snapshot.checkpoint})).ok,true);
  const forged=JSON.parse(JSON.stringify(snapshot.rows[1]));
  forged.record.award_kind='INITIAL_AWARD';
  assert.equal((await store.source.verifyAwardRow(forged,{child_id,badge_id,checkpoint:snapshot.checkpoint})).ok,false);
  assert.equal(award(create(),5,'REAWARD').reason,'DUPLICATE_APPROVED_DECISION');
  assert.equal((await deriveFromLedger({...options,child_id:'CHILD_B',source:store.source})).ok,true); // Separate, empty scope.
  assert.equal((await deriveFromLedger({...options,child_id:'CHILD_B',source:store.source})).ownership_state,'LOCKED');
  // Signing key must remain stable across restarts; a different key cannot read existing awards.
  assert.equal((await deriveFromLedger({...options,source:create(crypto.randomBytes(32)).source})).ok,false);
  const filename=fs.readdirSync(directory).find(x=>x.endsWith('.json'));
  assert.ok(filename);
  const file=path.join(directory,filename),old=fs.readFileSync(file,'utf8');
  const data=JSON.parse(old);data.rows[1].record.award_kind='INITIAL_AWARD';
  fs.writeFileSync(file,JSON.stringify(data));
  assert.equal((await deriveFromLedger({...options,source:store.source})).ok,false);
  fs.writeFileSync(file,old);
  assert.equal((await deriveFromLedger({...options,source:store.source})).ok,true);
  console.log('durable badge Award Ledger + real persisted replay: PASS');
 }finally{fs.rmSync(directory,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
