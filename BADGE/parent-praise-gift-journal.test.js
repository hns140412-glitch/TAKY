'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {createParentPraiseGiftService}=require('./parent-praise-gift.js');
const {createParentGiftJournal}=require('./parent-praise-gift-journal.js');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'taky-praise-journal-'));
const signingKey=crypto.randomBytes(32);
const makeJournal=(family_id='FAMILY_A',key=signingKey)=>createParentGiftJournal({
 directory:root,family_id,signingKey:key,now:()=> '2026-09-26T10:00:00Z'
});
const parent={sessionKey:'PARENT',sameOrigin:true};
const badge={badge_id:'PRAISE_001',title:'가족 응원 훈장',
 status:'APPROVED_ACTIVE',source:'FAMILY_PRAISE_BADGE',giftable:true};
function createService(journal=makeJournal()){
 return createParentPraiseGiftService({
  resolveServerSession:async req=>req.sessionKey==='PARENT'?{
   authenticated:true,source:'NETLIFY_IDENTITY',
   family_id:'FAMILY_A',member_id:'PARENT_01',role:'PARENT'
  }:null,
  verifyRequestOrigin:async req=>req.sameOrigin===true,
  lookupIdentityMember:async id=>id==='CHILD_01'?{
    identity_verified:true,member_id:id,role:'CHILD',family_id:'FAMILY_A'
  }:null,
  listGiftableBadges:async()=>[badge],
  resolveGiftableBadge:async({badge_id})=>badge_id===badge.badge_id?badge:null,
  appendGiftRecord:journal.appendGiftRecord
 });
}
const item=(id,count)=>({
 target_child_id:'CHILD_01',gift_type:'GEM',gem_count:count,
 idempotency_key:id,explicit_parent_action:true,message:'함께 해냈어!'
});
(async()=>{
 try{
  const service=createService();
  assert.equal((await service.getGiftOptions(parent)).ok,true);
  assert.equal((await service.sendGift(parent,item('gift-001',6))).reason,'GEM_GIFT_PER_TRANSACTION_LIMIT_1_TO_5');
  assert.equal((await service.sendGift(parent,item('gift-001',0))).reason,'GEM_GIFT_PER_TRANSACTION_LIMIT_1_TO_5');
  assert.equal(makeJournal().readGiftHistory().rows.length,0);
  const first=await service.sendGift(parent,item('gift-001',5));
  assert.equal(first.ok,true);assert.equal(first.gem_count,5);assert.equal(first.idempotent,false);
  const repeated=await createService(makeJournal()).sendGift(parent,item('gift-001',5));
  assert.equal(repeated.ok,true);assert.equal(repeated.idempotent,true);
  assert.equal(repeated.gift_id,first.gift_id);
  assert.equal((await service.sendGift(parent,item('gift-001',4))).reason,'GIFT_IDEMPOTENCY_CONFLICT');
  assert.equal(makeJournal().readGiftHistory().rows.length,1);
  const second=await service.sendGift(parent,item('gift-002',5));
  assert.equal(second.ok,true);assert.equal(second.gem_count,5);
  const one=await service.sendGift(parent,item('gift-003',1));
  assert.equal(one.ok,true);assert.equal(one.gem_count,1);
  const badgeGift=await service.sendGift(parent,{
   target_child_id:'CHILD_01',gift_type:'BADGE',badge_id:'PRAISE_001',
   idempotency_key:'gift-badge-001',explicit_parent_action:true,message:'고마워!'
  });
  assert.equal(badgeGift.ok,true);assert.equal(badgeGift.kind,'PRAISE_BADGE_GIFT');
  assert.equal(makeJournal().readGiftHistory().rows.length,4);
  const records=makeJournal().readGiftHistory().rows.map(row=>row.record);
  assert.deepEqual(records.map(row=>row.gem_count??null),[5,5,1,null]);
  assert.ok(records.every(row=>row.family_id==='FAMILY_A'&&row.receiver_child_id==='CHILD_01'));
  assert.ok(records.every(row=>!Object.hasOwn(row,'balance_after')));
  // Writer repeats the 1..5 cap, not merely a client-side selector.
  const forbidden=makeJournal().appendGiftRecord({
    contract:'TAKY_PARENT_PRAISE_GIFT_V1',source:'PARENT_PRAISE',
    family_id:'FAMILY_A',giver_parent_id:'PARENT_01',receiver_child_id:'CHILD_01',
    idempotency_key:'direct-invalid-006',message:'x',kind:'GEM_GIFT',gem_count:6
  });
  assert.equal(forbidden.reason,'GIFT_RECORD_SCHEMA_OR_AMOUNT_INVALID');
  const filename=fs.readdirSync(root).find(f=>f.endsWith('.json'));
  assert.ok(filename);
  const mainFile=path.join(root,filename),saved=fs.readFileSync(mainFile,'utf8');
  const altered=JSON.parse(saved);
  altered.rows[0].record.gem_count=6;
  fs.writeFileSync(mainFile,JSON.stringify(altered));
  assert.throws(()=>makeJournal().readGiftHistory(),/PRAISE_JOURNAL_INTEGRITY_INVALID/);
  fs.writeFileSync(mainFile,saved);
  assert.equal(makeJournal().readGiftHistory().rows.length,4);
  // The same file cannot be transplanted into another family, even with same HMAC key.
  const familyBFile=path.join(root,crypto.createHash('sha256')
   .update('PRAISE_JOURNAL\nFAMILY_B').digest('hex')+'.json');
  fs.writeFileSync(familyBFile,saved);
  assert.throws(()=>makeJournal('FAMILY_B').readGiftHistory(),/PRAISE_JOURNAL_SCOPE_INVALID/);
  assert.throws(()=>makeJournal('FAMILY_A',crypto.randomBytes(32)).readGiftHistory(),
    /PRAISE_JOURNAL_INTEGRITY_INVALID|PRAISE_JOURNAL_CHECKPOINT_INVALID/);
  console.log('PARENT_PRAISE_JOURNAL_PASS: persisted 5-gem cap, reboot, dedupe, conflict, family scope, tamper, no auto balance');
 }finally{fs.rmSync(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
