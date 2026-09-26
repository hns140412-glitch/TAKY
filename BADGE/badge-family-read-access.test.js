'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {createLedger}=require('./badge-award-ledger-store.js');
const {createFamilyBadgeReader}=require('./badge-family-read-access.js');

const root=fs.mkdtempSync(path.join(os.tmpdir(),'taky-family-badge-'));
const key=crypto.randomBytes(32),tiers=['GREEN','BLUE','RED','GOLD','PLATINUM'];
const sessions={
 parent:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_A',member_id:'PARENT_A',role:'PARENT'},
 ownChild:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_A',member_id:'CHILD_A',role:'CHILD'},
 otherChild:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_A',member_id:'CHILD_B',role:'CHILD'},
 otherParent:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_B',member_id:'PARENT_B',role:'PARENT'},
 untrusted:{authenticated:true,source:'TEST_ONLY',family_id:'FAMILY_A',member_id:'PARENT_A',role:'PARENT'}
};
const members={
 CHILD_A:{identity_verified:true,member_id:'CHILD_A',family_id:'FAMILY_A',role:'CHILD'},
 CHILD_B:{identity_verified:true,member_id:'CHILD_B',family_id:'FAMILY_A',role:'CHILD'},
 FOREIGN_CHILD:{identity_verified:true,member_id:'FOREIGN_CHILD',family_id:'FAMILY_B',role:'CHILD'}
};
const ledger=(family_id)=>createLedger({
 directory:path.join(root,crypto.createHash('sha256').update(family_id).digest('hex')),
 signingKey:key,
 verifyDecision:x=>x?.trusted===true?{ok:true,receipt:x.receipt}:{ok:false},
 isBadgeActive:x=>x.badge_id==='APPROVED_BADGE'&&x.child_id==='CHILD_A'
});
function reader({memberOverride=null,sourceOverride=null}={}){
 return createFamilyBadgeReader({
  resolveServerSession:async request=>sessions[request.serverSessionKey]||null,
  lookupIdentityMember:async id=>memberOverride||members[id]||null,
  openFamilyLedgerSource:async ({family_id})=>{
   if(sourceOverride)return sourceOverride;
   return Object.freeze({...ledger(family_id).source,family_id});
  }
 });
}
const args={child_id:'CHILD_A',badge_id:'APPROVED_BADGE',tier_order:tiers};
const award=(i,kind)=>ledger('FAMILY_A').appendApprovedDecision({trusted:true,receipt:{
 decision_id:'decision-'+i,decision_ref:'verified-test-decision-'+i,
 child_id:'CHILD_A',badge_id:'APPROVED_BADGE',
 decision_status:'APPROVED',award_kind:kind,approved_at:'2026-09-26T09:00:00Z'
}});
(async()=>{
 try{
  const r=reader();
  assert.equal((await r.getProgress({serverSessionKey:'bad',body:{session:sessions.parent}},args)).reason,'VERIFIED_FAMILY_SESSION_REQUIRED');
  assert.equal((await r.getProgress({serverSessionKey:'untrusted'},args)).reason,'VERIFIED_FAMILY_SESSION_REQUIRED');
  assert.equal((await r.getProgress({serverSessionKey:'otherChild'},args)).reason,'CHILD_MAY_ONLY_READ_OWN_BADGES');
  assert.equal((await r.getProgress({serverSessionKey:'otherParent'},args)).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await r.getProgress({serverSessionKey:'parent'},{...args,child_id:'FOREIGN_CHILD'})).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await reader({memberOverride:{...members.CHILD_A,identity_verified:false}}).getProgress({serverSessionKey:'parent'},args)).ok,false);
  assert.equal((await reader({sourceOverride:{...ledger('FAMILY_B').source,family_id:'FAMILY_B'}}).getProgress({serverSessionKey:'parent'},args)).reason,'FAMILY_SCOPED_LEDGER_SOURCE_REQUIRED');
  assert.equal((await r.getProgress({serverSessionKey:'parent'},{...args,child_id:' CHILD_A '})).reason,'CHILD_BADGE_SCOPE_REQUIRED');
  const empty=await r.getProgress({serverSessionKey:'parent'},args);
  assert.equal(empty.ok,true);assert.equal(empty.ownership_state,'LOCKED');assert.equal(empty.verified_awards,0);
  assert.equal(award(0,'INITIAL_AWARD').ok,true);
  const initial=await r.getProgress({serverSessionKey:'ownChild'},args);
  assert.equal(initial.ok,true);assert.equal(initial.ownership_state,'EARNED');assert.equal(initial.state.star_count,0);
  for(let i=1;i<=5;i++)assert.equal(award(i,'REAWARD').ok,true);
  const final=await r.getProgress({serverSessionKey:'parent'},args);
  assert.equal(final.ok,true);assert.equal(final.verified_awards,6);
  assert.equal(final.state.tier,'BLUE');assert.equal(final.state.star_count,0);
  assert.equal(final.family_id,'FAMILY_A');
  assert.equal((await r.getProgress({serverSessionKey:'otherParent'},args)).ok,false);
  console.log('family-scoped server badge read: PASS (parent/child access, cross-family, replay)');
 }finally{fs.rmSync(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
