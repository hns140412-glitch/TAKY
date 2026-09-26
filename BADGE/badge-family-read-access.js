'use strict';

/**
 * Server-side badge collection read access.
 * All capabilities are injected by the trusted runtime; NO client-supplied
 * session, family_id, target user or badge ownership packet is authoritative.
 */
const {deriveFromLedger}=require('./badge-ledger-projection-bridge.js');
const SOURCE_CONTRACT='TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1';
const clean=v=>typeof v==='string'?v.trim():'';
const deny=reason=>({ok:false,reason});

function createFamilyBadgeReader({resolveServerSession,lookupIdentityMember,openFamilyLedgerSource}={}){
  if(typeof resolveServerSession!=='function'||typeof lookupIdentityMember!=='function'||
    typeof openFamilyLedgerSource!=='function')
    throw Error('TRUSTED_SERVER_CAPABILITIES_REQUIRED');

  async function getProgress(request,{child_id,badge_id,tier_order}={}){
    const child=clean(child_id),badge=clean(badge_id);
    if(!child||!badge||child_id!==child||badge_id!==badge)
      return deny('CHILD_BADGE_SCOPE_REQUIRED');
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

    let source;
    try{source=await openFamilyLedgerSource({family_id:session.family_id,child_id:child})}
    catch{return deny('FAMILY_LEDGER_SOURCE_OPEN_FAILED')}
    if(!source||source.contract!==SOURCE_CONTRACT||source.family_id!==session.family_id||
       typeof source.loadCompleteHistory!=='function'||typeof source.verifyAwardRow!=='function')
      return deny('FAMILY_SCOPED_LEDGER_SOURCE_REQUIRED');

    const result=await deriveFromLedger({source,child_id:child,badge_id:badge,tier_order});
    if(!result.ok)return deny('VERIFIED_AWARD_HISTORY_REQUIRED:'+result.reason);
    return {ok:true,contract:'TAKY_FAMILY_BADGE_READ_V1',
      family_id:session.family_id,child_id:child,badge_id:badge,
      checkpoint:result.checkpoint,verified_awards:result.verified_awards,
      ownership_state:result.ownership_state,
      state:result.state};
  }
  return Object.freeze({contract:'TAKY_FAMILY_BADGE_READ_V1',getProgress});
}
module.exports=Object.freeze({createFamilyBadgeReader});
