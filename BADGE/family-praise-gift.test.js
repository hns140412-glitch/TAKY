'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {createFamilyPraiseGiftService,MAX_GEMS_PER_GIFT}=require('./family-praise-gift.js');
const {createFamilyGiftJournal}=require('./family-praise-gift-journal.js');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'taky-family-gift-v2-'));
const key=crypto.randomBytes(32),family='FAMILY_A';
const sessions={
 parent:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:family,member_id:'PARENT_A',role:'PARENT'},
 grandparent:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:family,member_id:'GRANDMA_A',role:'GRANDPARENT'},
 guardian:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:family,member_id:'GUARDIAN_A',role:'GUARDIAN'},
 sibling:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:family,member_id:'SIBLING_A',role:'CHILD'},
 uncle:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:family,member_id:'UNCLE_A',role:'RELATIVE'},
 foreign:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_B',member_id:'FOREIGN_A',role:'GRANDPARENT'},
 fake:{authenticated:true,source:'TEST_ONLY',family_id:family,member_id:'PARENT_A',role:'PARENT'}
};
const members={
 PARENT_A:{identity_verified:true,member_id:'PARENT_A',family_id:family,role:'PARENT'},
 GRANDMA_A:{identity_verified:true,member_id:'GRANDMA_A',family_id:family,role:'GRANDPARENT'},
 GUARDIAN_A:{identity_verified:true,member_id:'GUARDIAN_A',family_id:family,role:'GUARDIAN'},
 SIBLING_A:{identity_verified:true,member_id:'SIBLING_A',family_id:family,role:'CHILD'},
 UNCLE_A:{identity_verified:true,member_id:'UNCLE_A',family_id:family,role:'RELATIVE'},
 FOREIGN_A:{identity_verified:true,member_id:'FOREIGN_A',family_id:'FAMILY_B',role:'GRANDPARENT'},
 CHILD_A:{identity_verified:true,member_id:'CHILD_A',family_id:family,role:'CHILD'},
 CHILD_B:{identity_verified:true,member_id:'CHILD_B',family_id:family,role:'CHILD'},
 OTHER_CHILD:{identity_verified:true,member_id:'OTHER_CHILD',family_id:'FAMILY_B',role:'CHILD'}
};
const grants=new Set(['PARENT_A','GRANDMA_A','GUARDIAN_A','SIBLING_A']);
const badge={badge_id:'PRAISE_001',title:'탐험대 가족 응원',source:'FAMILY_PRAISE_BADGE',status:'APPROVED_ACTIVE',giftable:true};
const draft={badge_id:'BDG-DRAFT-001',title:'초안',source:'FAMILY_PRAISE_BADGE',status:'WORKING_DRAFT',giftable:true};
const journal=()=>createFamilyGiftJournal({directory:root,family_id:family,signingKey:key,now:()=> '2026-09-26T10:00:00Z'});
function service({permissionOverride=null,memberOverride=null}={}){
 return createFamilyPraiseGiftService({
  resolveServerSession:async req=>sessions[req.sessionKey]||null,
  verifyRequestOrigin:async req=>req.sameOrigin===true,
  lookupIdentityMember:async id=>memberOverride&&id===memberOverride.member_id?memberOverride:members[id],
  authorizeFamilyGiver:async args=>permissionOverride||({
   ...args,allowed:grants.has(args.giver_member_id),membership_verified:true
  }),
  listGiftableBadges:async()=>[draft,badge,badge],
  resolveGiftableBadge:async({badge_id})=>badge_id===badge.badge_id?badge:badge_id===draft.badge_id?draft:null,
  appendGiftRecord:journal().appendGiftRecord
 });
}
const request=(sessionKey)=>({sessionKey,sameOrigin:true});
const gift=(id,count=5,target='CHILD_A')=>({
 target_child_id:target,gift_type:'GEM',gem_count:count,idempotency_key:id,
 explicit_gift_action:true,message:'우리 탐험대 최고!'
});
(async()=>{
 try{
  assert.equal(MAX_GEMS_PER_GIFT,5);
  for(const who of ['parent','grandparent','guardian','sibling']){
   const opts=await service().getGiftOptions(request(who));
   assert.equal(opts.ok,true,who);
   assert.deepEqual(opts.gem_amount_options,[1,2,3,4,5]);
   assert.deepEqual(opts.badge_options,[{badge_id:'PRAISE_001',title:'탐험대 가족 응원'}]);
   assert.equal(Object.hasOwn(opts,'parent_collection'),false);
   assert.equal(JSON.stringify(opts).includes('LOCKED'),false);
  }
  assert.equal((await service().getGiftOptions(request('uncle'))).reason,'FAMILY_GIFT_PERMISSION_REQUIRED');
  assert.equal((await service().getGiftOptions(request('fake'))).reason,'VERIFIED_FAMILY_SESSION_REQUIRED');
  assert.equal((await service({permissionOverride:{allowed:true,permission:'FAMILY_PRAISE_GIFT',family_id:family,giver_member_id:'PARENT_A',action:'VIEW_GIFT_OPTIONS',target_child_id:null,membership_verified:false}}).getGiftOptions(request('parent'))).reason,'FAMILY_GIFT_PERMISSION_REQUIRED');
  assert.equal((await service({memberOverride:{...members.GRANDMA_A,identity_verified:false}}).getGiftOptions(request('grandparent'))).reason,'VERIFIED_GIVER_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await service().sendGift({...request('parent'),sameOrigin:false},gift('no-origin-01'))).reason,'REQUEST_ORIGIN_NOT_VERIFIED');
  assert.equal((await service().sendGift(request('uncle'),gift('uncle-no-grant-01'))).reason,'FAMILY_GIFT_PERMISSION_REQUIRED');
  assert.equal((await service().sendGift(request('foreign'),gift('foreign-target-01'))).reason,'FAMILY_GIFT_PERMISSION_REQUIRED');
  assert.equal((await service().sendGift(request('sibling'),gift('self-gift-01',1,'SIBLING_A'))).reason,'SELF_GIFT_FORBIDDEN');
  assert.equal((await service().sendGift(request('grandparent'),gift('cross-family-01',1,'OTHER_CHILD'))).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await service().sendGift(request('grandparent'),gift('parent-target-01',1,'PARENT_A'))).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await service().sendGift(request('parent'),{...gift('old-parent-field'),explicit_parent_action:true,explicit_gift_action:false})).reason,'EXPLICIT_GIFT_ACTION_REQUIRED');
  assert.equal((await service().sendGift(request('parent'),{...gift('forged-role-01'),giver_role:'GRANDPARENT'})).reason,'CLIENT_AUTHORITY_FIELDS_FORBIDDEN');
  for(const n of [0,6,-2,1.5,'5',null]){
   assert.equal((await service().sendGift(request('grandparent'),gift('invalid-gem-'+String(n),n))).reason,'GEM_GIFT_PER_TRANSACTION_LIMIT_1_TO_5');
  }
  assert.equal((await service().sendGift(request('grandparent'),{...gift('invalid-gem-undefined'),gem_count:undefined})).reason,'GEM_GIFT_PER_TRANSACTION_LIMIT_1_TO_5');
  assert.equal(journal().readGiftHistory().rows.length,0);
  for(const [who,id,n] of [
   ['parent','family-praise-parent-01',5],
   ['grandparent','family-praise-grandma-01',5],
   ['guardian','family-praise-guardian-01',1],
   ['sibling','family-praise-sibling-01',2]
  ]){
   const sent=await service().sendGift(request(who),gift(id,n));
   assert.equal(sent.ok,true,who); assert.equal(sent.gem_count,n);
  }
  assert.equal(journal().readGiftHistory().rows.length,4);
  const repeat=await service().sendGift(request('grandparent'),gift('family-praise-grandma-01',5));
  assert.equal(repeat.ok,true); assert.equal(repeat.idempotent,true);
  assert.equal((await service().sendGift(request('grandparent'),gift('family-praise-grandma-01',4))).reason,'GIFT_IDEMPOTENCY_CONFLICT');
  assert.equal(journal().readGiftHistory().rows.length,4);
  const praise=await service().sendGift(request('grandparent'),{
   target_child_id:'CHILD_B',gift_type:'BADGE',badge_id:'PRAISE_001',idempotency_key:'family-badge-grandma-01',
   explicit_gift_action:true,message:'도전 최고!'
  });
  assert.equal(praise.ok,true);assert.equal(praise.kind,'PRAISE_BADGE_GIFT');
  assert.equal((await service().sendGift(request('grandparent'),{
   target_child_id:'CHILD_B',gift_type:'BADGE',badge_id:'BDG-DRAFT-001',idempotency_key:'draft-badge-no-01',
   explicit_gift_action:true
  })).reason,'BADGE_NOT_APPROVED_FOR_FAMILY_PRAISE');
  const savedHistory=journal().readGiftHistory();
  assert.equal(savedHistory.rows.length,5);
  assert.deepEqual(savedHistory.rows.map(x=>x.record.giver_member_id),['PARENT_A','GRANDMA_A','GUARDIAN_A','SIBLING_A','GRANDMA_A']);
  assert.ok(savedHistory.rows.every(x=>x.record.family_id===family));
  assert.ok(savedHistory.rows.every(x=>!Object.hasOwn(x.record,'giver_parent_id')&&!Object.hasOwn(x.record,'balance_after')));
  const direct=journal().appendGiftRecord({
   contract:'TAKY_FAMILY_PRAISE_GIFT_V2',source:'FAMILY_PRAISE',family_id:family,
   giver_member_id:'GRANDMA_A',receiver_child_id:'CHILD_A',message:'x',idempotency_key:'direct-over-5-gems',
   kind:'GEM_GIFT',gem_count:6
  });
  assert.equal(direct.reason,'GIFT_RECORD_SCHEMA_OR_AMOUNT_INVALID');
  const file=fs.readdirSync(root).find(x=>x.endsWith('.json'));
  const old=fs.readFileSync(path.join(root,file),'utf8');
  const tamper=JSON.parse(old);tamper.rows[0].record.gem_count=6;
  fs.writeFileSync(path.join(root,file),JSON.stringify(tamper));
  assert.throws(()=>journal().readGiftHistory(),/PRAISE_JOURNAL_INTEGRITY_INVALID/);
  fs.writeFileSync(path.join(root,file),old);
  assert.equal(journal().readGiftHistory().rows.length,5);
  const otherJournal=createFamilyGiftJournal({directory:root,family_id:'FAMILY_B',signingKey:key});
  const transplanted=path.join(root,crypto.createHash('sha256').update('FAMILY_PRAISE_JOURNAL_V2\nFAMILY_B').digest('hex')+'.json');
  fs.writeFileSync(transplanted,old);
  assert.throws(()=>otherJournal.readGiftHistory(),/PRAISE_JOURNAL_SCOPE_INVALID/);
  console.log('FAMILY_PRAISE_V2_PASS: parent/grandparent/guardian/sibling by permission, non-granted relative denied, 1..5 gems, journal integrity');
 }finally{fs.rmSync(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
