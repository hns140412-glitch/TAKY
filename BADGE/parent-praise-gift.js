'use strict';

/**
 * Family praise is a parent-authored gift source, NOT child achievement evidence.
 * This module does not touch Achievement Award Ledger, auto-activate historical
 * badge drafts, or change an app's gem balance. A trusted, atomic gift writer
 * must durably persist before a successful receipt is returned.
 */
const VERSION='TAKY_PARENT_PRAISE_GIFT_V1';
const MAX_GEMS_PER_GIFT=5;
const GEM_OPTIONS=Object.freeze([1,2,3,4,5]);
const clean=v=>typeof v==='string'?v.trim():'';
const fail=reason=>({ok:false,reason});
const approved=record=>!!record&&record.status==='APPROVED_ACTIVE'&&
  record.source==='FAMILY_PRAISE_BADGE'&&record.giftable===true&&
  !!clean(record.badge_id)&&record.badge_id===clean(record.badge_id);

function createParentPraiseGiftService({
  resolveServerSession,verifyRequestOrigin,lookupIdentityMember,
  listGiftableBadges,resolveGiftableBadge,appendGiftRecord
}={}){
  if([resolveServerSession,verifyRequestOrigin,lookupIdentityMember,listGiftableBadges,
    resolveGiftableBadge,appendGiftRecord].some(fn=>typeof fn!=='function'))
    throw Error('TRUSTED_FAMILY_GIFT_CAPABILITIES_REQUIRED');

  async function parentSession(request,mutation=false){
    if(mutation){
      let originVerified=false;
      try{originVerified=(await verifyRequestOrigin(request))===true}catch{}
      if(!originVerified)return fail('REQUEST_ORIGIN_NOT_VERIFIED');
    }
    let session;
    try{session=await resolveServerSession(request)}catch{return fail('SERVER_SESSION_RESOLUTION_FAILED')}
    if(!session||session.authenticated!==true||session.source!=='NETLIFY_IDENTITY'||
      session.role!=='PARENT'||!clean(session.family_id)||!clean(session.member_id)||
      session.family_id!==clean(session.family_id)||session.member_id!==clean(session.member_id))
      return fail('VERIFIED_PARENT_SESSION_REQUIRED');
    return {ok:true,session};
  }

  async function getGiftOptions(request){
    const auth=await parentSession(request);
    if(!auth.ok)return auth;
    let badges;
    try{badges=await listGiftableBadges({family_id:auth.session.family_id})}
    catch{return fail('GIFT_CATALOG_UNAVAILABLE')}
    if(!Array.isArray(badges))return fail('GIFT_CATALOG_INVALID');
    const seen=new Set();
    const badge_options=[];
    for(const badge of badges){
      if(!approved(badge)||seen.has(badge.badge_id))continue;
      const title=clean(badge.title);
      if(!title)continue;
      seen.add(badge.badge_id);
      badge_options.push({badge_id:badge.badge_id,title});
    }
    // No parent-owned catalog or locked/unearned silhouette is produced.
    return {ok:true,contract:VERSION,gem_amount_options:[...GEM_OPTIONS],badge_options};
  }

  async function sendGift(request,input={}){
    const auth=await parentSession(request,true);
    if(!auth.ok)return auth;
    if(!input||typeof input!=='object'||Array.isArray(input))return fail('INVALID_GIFT_REQUEST');
    if(['family_id','giver_parent_id','gift_id','award_id','award_kind','decision_status',
      'award_status','ownership_state'].some(key=>Object.hasOwn(input,key)))
      return fail('CLIENT_AUTHORITY_FIELDS_FORBIDDEN');
    const target=clean(input.target_child_id);
    if(!target||target!==input.target_child_id||target.length>128)
      return fail('TARGET_CHILD_REQUIRED');
    if(input.explicit_parent_action!==true)return fail('EXPLICIT_GIFT_ACTION_REQUIRED');
    const idem=clean(input.idempotency_key);
    if(idem.length<8||idem.length>128||idem!==input.idempotency_key)
      return fail('IDEMPOTENCY_KEY_REQUIRED');
    const message=input.message===undefined?'':clean(input.message);
    if(typeof input.message!=='undefined'&&typeof input.message!=='string')
      return fail('GIFT_MESSAGE_INVALID');
    if(message.length>200)return fail('GIFT_MESSAGE_TOO_LONG');
    if(input.gift_type!=='GEM'&&input.gift_type!=='BADGE')return fail('GIFT_TYPE_INVALID');

    let member;
    try{member=await lookupIdentityMember(target)}
    catch{return fail('TARGET_MEMBER_LOOKUP_FAILED')}
    if(!member||member.identity_verified!==true||member.member_id!==target||
      member.role!=='CHILD'||!clean(member.family_id)||
      member.family_id!==auth.session.family_id)
      return fail('VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');

    const record={
      contract:VERSION,source:'PARENT_PRAISE',
      family_id:auth.session.family_id,
      giver_parent_id:auth.session.member_id,receiver_child_id:target,
      idempotency_key:idem,message
    };
    if(input.gift_type==='GEM'){
      if(!Number.isInteger(input.gem_count)||input.gem_count<1||
        input.gem_count>MAX_GEMS_PER_GIFT)
        return fail('GEM_GIFT_PER_TRANSACTION_LIMIT_1_TO_5');
      if(input.badge_id!==undefined&&input.badge_id!==null)
        return fail('MIXED_GIFT_FIELDS_FORBIDDEN');
      record.kind='GEM_GIFT';
      record.gem_count=input.gem_count;
    }else{
      if(input.gem_count!==undefined&&input.gem_count!==null)
        return fail('MIXED_GIFT_FIELDS_FORBIDDEN');
      if(!clean(input.badge_id)||input.badge_id!==clean(input.badge_id))
        return fail('GIFT_BADGE_ID_REQUIRED');
      let badge;
      try{badge=await resolveGiftableBadge({
        family_id:auth.session.family_id,badge_id:input.badge_id
      })}catch{return fail('GIFT_BADGE_CATALOG_LOOKUP_FAILED')}
      if(!approved(badge)||badge.badge_id!==input.badge_id)
        return fail('BADGE_NOT_APPROVED_FOR_FAMILY_PRAISE');
      record.kind='PRAISE_BADGE_GIFT';
      record.badge_id=badge.badge_id;
    }

    let written;
    try{written=await appendGiftRecord(Object.freeze({...record}))}
    catch{return fail('GIFT_PERSISTENCE_FAILED')}
    if(!written||written.ok!==true||written.persisted!==true||
      !clean(written.gift_id)||written.family_id!==record.family_id||
      written.receiver_child_id!==record.receiver_child_id||
      written.idempotency_key!==record.idempotency_key||
      written.kind!==record.kind||
      (record.kind==='GEM_GIFT'&&written.gem_count!==record.gem_count)||
      (record.kind==='PRAISE_BADGE_GIFT'&&written.badge_id!==record.badge_id))
      return fail('GIFT_PERSISTENCE_RECEIPT_INVALID');
    return {ok:true,contract:VERSION,gift_id:written.gift_id,
      kind:record.kind,receiver_child_id:target,
      ...(record.kind==='GEM_GIFT'?{gem_count:record.gem_count}:{badge_id:record.badge_id}),
      idempotent:written.idempotent===true};
  }
  return Object.freeze({contract:VERSION,max_gems_per_gift:MAX_GEMS_PER_GIFT,
    getGiftOptions,sendGift});
}
module.exports=Object.freeze({VERSION,MAX_GEMS_PER_GIFT,GEM_OPTIONS,createParentPraiseGiftService});
