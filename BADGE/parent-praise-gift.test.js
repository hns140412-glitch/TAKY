'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {createParentPraiseGiftService,MAX_GEMS_PER_GIFT}=require('./parent-praise-gift.js');
const sessions={
  parent:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_A',member_id:'PARENT_A',role:'PARENT'},
  secondParent:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_A',member_id:'PARENT_A2',role:'PARENT'},
  child:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_A',member_id:'CHILD_A',role:'CHILD'},
  other:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_B',member_id:'PARENT_B',role:'PARENT'},
  spoof:{authenticated:true,source:'TEST_ONLY',family_id:'FAMILY_A',member_id:'PARENT_A',role:'PARENT'}
};
const members={
 CHILD_A:{identity_verified:true,member_id:'CHILD_A',family_id:'FAMILY_A',role:'CHILD'},
 CHILD_B:{identity_verified:true,member_id:'CHILD_B',family_id:'FAMILY_A',role:'CHILD'},
 FOREIGN:{identity_verified:true,member_id:'FOREIGN',family_id:'FAMILY_B',role:'CHILD'},
 PARENT_A:{identity_verified:true,member_id:'PARENT_A',family_id:'FAMILY_A',role:'PARENT'}
};
const goodBadge={badge_id:'PRAISE_01',title:'탐험 응원 훈장',status:'APPROVED_ACTIVE',source:'FAMILY_PRAISE_BADGE',giftable:true};
const draftBadge={badge_id:'BDG-DRAFT-001',title:'역사적 초안',status:'WORKING_DRAFT',source:'FAMILY_PRAISE_BADGE',giftable:true};
const giftRecords=new Map();
let appends=0;
const create=(options={})=>createParentPraiseGiftService({
 resolveServerSession:async req=>sessions[req.sessionKey],
 verifyRequestOrigin:async req=>req.sameOrigin===true,
 lookupIdentityMember:async id=>members[id],
 listGiftableBadges:async()=>[draftBadge,goodBadge,goodBadge,{...goodBadge,badge_id:'BADGE_2',source:'ACTIVITY_BADGE'}],
 resolveGiftableBadge:async ({badge_id})=>badge_id==='PRAISE_01'?goodBadge:
   badge_id==='BDG-DRAFT-001'?draftBadge:null,
 appendGiftRecord:async record=>{
   if(options.failWrite)throw Error('storage not available');
   if(options.badReceipt)return {ok:true,persisted:false};
   const key=record.family_id+':'+record.giver_parent_id+':'+record.idempotency_key;
   const fingerprint=crypto.createHash('sha256').update(JSON.stringify(record)).digest('hex');
   const existing=giftRecords.get(key);
   if(existing){
     if(existing.fingerprint!==fingerprint)throw Error('CONFLICTING_IDEMPOTENCY_KEY');
     return {...existing.receipt,idempotent:true};
   }
   appends++;
   const receipt={
     ok:true,persisted:true,gift_id:'gift-'+appends,
     family_id:record.family_id,receiver_child_id:record.receiver_child_id,
     idempotency_key:record.idempotency_key,kind:record.kind,
     ...(record.kind==='GEM_GIFT'?{gem_count:record.gem_count}:{badge_id:record.badge_id})
   };
   giftRecords.set(key,{fingerprint,receipt});
   return {...receipt,idempotent:false};
 }
});
const parent={sessionKey:'parent',sameOrigin:true};
const base={target_child_id:'CHILD_A',gift_type:'GEM',gem_count:5,
 idempotency_key:'gift-request-0001',explicit_parent_action:true,message:'오늘도 멋졌어!'};
(async()=>{
  assert.equal(MAX_GEMS_PER_GIFT,5);
  const service=create();
  const options=await service.getGiftOptions(parent);
  assert.equal(options.ok,true);
  assert.deepEqual(options.gem_amount_options,[1,2,3,4,5]);
  assert.deepEqual(options.badge_options,[{badge_id:'PRAISE_01',title:'탐험 응원 훈장'}]);
  assert.equal(Object.hasOwn(options,'parent_collection'),false);
  assert.equal(JSON.stringify(options).includes('LOCKED'),false);
  assert.equal((await service.getGiftOptions({sessionKey:'child'})).reason,'VERIFIED_PARENT_SESSION_REQUIRED');
  assert.equal((await service.getGiftOptions({sessionKey:'spoof'})).reason,'VERIFIED_PARENT_SESSION_REQUIRED');
  assert.equal((await service.sendGift({...parent,sameOrigin:false},base)).reason,'REQUEST_ORIGIN_NOT_VERIFIED');
  assert.equal((await service.sendGift({sessionKey:'child',sameOrigin:true},base)).reason,'VERIFIED_PARENT_SESSION_REQUIRED');
  assert.equal((await service.sendGift({sessionKey:'spoof',sameOrigin:true},base)).reason,'VERIFIED_PARENT_SESSION_REQUIRED');
  assert.equal((await service.sendGift({sessionKey:'other',sameOrigin:true},base)).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await service.sendGift(parent,{...base,target_child_id:'FOREIGN'})).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await service.sendGift(parent,{...base,target_child_id:'PARENT_A'})).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await service.sendGift(parent,{...base,explicit_parent_action:false})).reason,'EXPLICIT_GIFT_ACTION_REQUIRED');
  assert.equal((await service.sendGift(parent,{...base,family_id:'FAMILY_B'})).reason,'CLIENT_AUTHORITY_FIELDS_FORBIDDEN');
  assert.equal((await service.sendGift(parent,{...base,award_id:'AWARD_FAKE'})).reason,'CLIENT_AUTHORITY_FIELDS_FORBIDDEN');
  for(const invalid of [0,6,-1,1.5,'5','6',NaN,Infinity,null,undefined]){
    assert.equal((await service.sendGift(parent,{...base,gem_count:invalid})).reason,'GEM_GIFT_PER_TRANSACTION_LIMIT_1_TO_5');
  }
  assert.equal(appends,0);
  const sent=await service.sendGift(parent,base);
  assert.equal(sent.ok,true);
  assert.equal(sent.gem_count,5);
  assert.equal(appends,1);
  const dup=await service.sendGift(parent,base);
  assert.equal(dup.ok,true);
  assert.equal(dup.idempotent,true);
  assert.equal(appends,1);
  assert.equal((await service.sendGift(parent,{...base,gem_count:4})).reason,'GIFT_PERSISTENCE_FAILED');
  assert.equal(appends,1);
  // Cap applies to EACH gift transaction; no unsupported daily/monthly cap is invented.
  const second=await service.sendGift(parent,{...base,idempotency_key:'gift-request-0002',gem_count:5});
  assert.equal(second.ok,true);
  assert.equal(appends,2);
  const one=await service.sendGift(parent,{...base,idempotency_key:'gift-request-0003',gem_count:1});
  assert.equal(one.ok,true);
  assert.equal(appends,3);
  const badgeBase={target_child_id:'CHILD_A',gift_type:'BADGE',badge_id:'PRAISE_01',
    idempotency_key:'badge-request-001',explicit_parent_action:true,message:'다시 도전했구나!'};
  assert.equal((await service.sendGift(parent,{...badgeBase,badge_id:'BDG-DRAFT-001'})).reason,'BADGE_NOT_APPROVED_FOR_FAMILY_PRAISE');
  assert.equal((await service.sendGift(parent,{...badgeBase,gem_count:1})).reason,'MIXED_GIFT_FIELDS_FORBIDDEN');
  const badge=await service.sendGift(parent,badgeBase);
  assert.equal(badge.ok,true);
  assert.equal(badge.kind,'PRAISE_BADGE_GIFT');
  assert.equal(badge.badge_id,'PRAISE_01');
  assert.equal((await create({failWrite:true}).sendGift(parent,{...base,idempotency_key:'unavailable-001'})).reason,'GIFT_PERSISTENCE_FAILED');
  assert.equal((await create({badReceipt:true}).sendGift(parent,{...base,idempotency_key:'fake-receipt-001'})).reason,'GIFT_PERSISTENCE_RECEIPT_INVALID');
  console.log('PARENT_PRAISE_GIFT_PASS: verified parent/child, no parent locked atlas, 1..5 gems per gift, approved gift-only badge, dedup/failure gates');
})().catch(e=>{console.error(e);process.exitCode=1});
