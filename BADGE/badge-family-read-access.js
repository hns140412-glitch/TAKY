'use strict';

/**
 * Server-side badge collection read access.
 * All capabilities are injected by the trusted runtime; NO client-supplied
 * session, family_id, target user or badge ownership packet is authoritative.
 */
const {deriveFromLedger}=require('./badge-ledger-projection-bridge.js');
const {projectBadgeCalendar}=require('./badge-award-calendar.js');
const SOURCE_CONTRACT='TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1';
const clean=v=>typeof v==='string'?v.trim():'';
const deny=reason=>({ok:false,reason});

function createFamilyBadgeReader({resolveServerSession,lookupIdentityMember,openFamilyLedgerSource,listActiveBadgeIds}={}){
  if(typeof resolveServerSession!=='function'||typeof lookupIdentityMember!=='function'||
    typeof openFamilyLedgerSource!=='function')
    throw Error('TRUSTED_SERVER_CAPABILITIES_REQUIRED');

  async function authorizeChildScope(request,child_id){
    const child=clean(child_id);
    if(!child||child_id!==child)return deny('CHILD_BADGE_SCOPE_REQUIRED');
    let session;
    try{session=await resolveServerSession(request)}catch{return deny('SERVER_AUTHENTICATION_FAILED')}
    // Compatible with Ready's verified familySessionFromIdentityUser() output;
    // a bootstrap or arbitrary browser object is NOT a server identity.
    if(!session||session.authenticated!==true||session.source!=='NETLIFY_IDENTITY'||
      !clean(session.family_id)||!clean(session.member_id)||
      !['PARENT','CHILD'].includes(session.role))
      return deny('VERIFIED_FAMILY_SESSION_REQUIRED');
    if(session.role==='CHILD'&&session.member_id!==child)
      return deny('CHILD_MAY_ONLY_READ_OWN_BADGES');

    // Parent must have a current, provider-verified CHILD target in the same
    // family. Do not trust caller-supplied family_id or a cached member list.
    let member;
    try{member=await lookupIdentityMember(child)}catch{return deny('TARGET_MEMBER_LOOKUP_FAILED')}
    if(!member||member.identity_verified!==true||
      member.member_id!==child||member.role!=='CHILD'||
      !clean(member.family_id)||member.family_id!==session.family_id)
      return deny('VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');

    return {ok:true,family_id:session.family_id,child_id:child};
  }

  async function openSource(scope){
    let source;
    try{source=await openFamilyLedgerSource({family_id:scope.family_id,child_id:scope.child_id})}
    catch{return deny('FAMILY_LEDGER_SOURCE_OPEN_FAILED')}
    if(!source||source.contract!==SOURCE_CONTRACT||source.family_id!==scope.family_id||
       typeof source.loadCompleteHistory!=='function'||typeof source.verifyAwardRow!=='function')
      return deny('FAMILY_SCOPED_LEDGER_SOURCE_REQUIRED');
    return {ok:true,source};
  }

  async function getProgress(request,{child_id,badge_id,tier_order}={}){
    const badge=clean(badge_id);
    if(!badge||badge!==badge_id)return deny('CHILD_BADGE_SCOPE_REQUIRED');
    const scope=await authorizeChildScope(request,child_id);
    if(!scope.ok)return scope;
    const opened=await openSource(scope);
    if(!opened.ok)return opened;
    const result=await deriveFromLedger({source:opened.source,child_id:scope.child_id,badge_id:badge,tier_order});
    if(!result.ok)return deny('VERIFIED_AWARD_HISTORY_REQUIRED:'+result.reason);
    return {ok:true,contract:'TAKY_FAMILY_BADGE_READ_V1',
      family_id:scope.family_id,child_id:scope.child_id,badge_id:badge,
      checkpoint:result.checkpoint,verified_awards:result.verified_awards,
      ownership_state:result.ownership_state,
      state:result.state,history:result.history};
  }

  async function getBadgeHistory(request,params={}){
    const result=await getProgress(request,params);
    if(!result.ok)return result;
    return {ok:true,contract:'TAKY_FAMILY_BADGE_DETAIL_HISTORY_V1',
      family_id:result.family_id,child_id:result.child_id,badge_id:result.badge_id,
      checkpoint:result.checkpoint,ownership_state:result.ownership_state,
      current_state:result.state,history:result.history};
  }

  async function getMonth(request,{child_id,month,tier_order}={}){
    const scope=await authorizeChildScope(request,child_id);
    if(!scope.ok)return scope;
    if(typeof listActiveBadgeIds!=='function')return deny('TRUSTED_ACTIVE_BADGE_LIST_REQUIRED');
    if(typeof month!=='string'||!/^\\d{4}-(0[1-9]|1[0-2])$/.test(month))
      return deny('VALID_YEAR_MONTH_REQUIRED');
    let catalog;
    try{catalog=await listActiveBadgeIds({family_id:scope.family_id,child_id:scope.child_id})}
    catch{return deny('ACTIVE_BADGE_LIST_UNAVAILABLE')}
    if(!Array.isArray(catalog)||catalog.length>100||catalog.some(x=>
       !x||x.active!==true||x.approved!==true||!clean(x.badge_id)||x.badge_id!==clean(x.badge_id))||
       new Set(catalog.map(x=>x.badge_id)).size!==catalog.length)
      return deny('ACTIVE_BADGE_LIST_INVALID_OR_UNAPPROVED');
    const opened=await openSource(scope);
    if(!opened.ok)return opened;
    const histories=[],labels={};
    for(const entry of catalog){
      const result=await deriveFromLedger({source:opened.source,child_id:scope.child_id,
        badge_id:entry.badge_id,tier_order});
      if(!result.ok)return deny('VERIFIED_AWARD_HISTORY_REQUIRED:'+entry.badge_id+':'+result.reason);
      histories.push(...result.history);
      labels[entry.badge_id]=clean(entry.title)||entry.badge_id;
    }
    return projectBadgeCalendar({family_id:scope.family_id,child_id:scope.child_id,
      month,history:histories,labels});
  }
  return Object.freeze({contract:'TAKY_FAMILY_BADGE_READ_V1',getProgress,getBadgeHistory,getMonth});
}
module.exports=Object.freeze({createFamilyBadgeReader});
