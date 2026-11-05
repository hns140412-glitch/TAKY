'use strict';
const VERSION='TAKY_CREW_TRANSPORT_AUTH_POLICY_V1';
const clean=v=>String(v??'').trim();
function authorize(packet={},identity={}){
  const issues=[];
  const familyId=clean(packet?.context?.family_id);
  const memberId=clean(packet?.context?.member_id);
  const sourceApp=clean(packet?.source_app);
  if(identity?.authenticated!==true)issues.push('AUTHENTICATION_REQUIRED');
  if(!familyId)issues.push('PACKET_FAMILY_ID_REQUIRED');
  if(!memberId)issues.push('PACKET_MEMBER_ID_REQUIRED');
  if(!clean(identity.family_id))issues.push('IDENTITY_FAMILY_ID_REQUIRED');
  if(familyId&&clean(identity.family_id)&&familyId!==clean(identity.family_id))issues.push('FAMILY_SCOPE_MISMATCH');
  const members=new Set(Array.isArray(identity.authorized_member_ids)?identity.authorized_member_ids.map(clean).filter(Boolean):[]);
  if(memberId&&!members.has(memberId))issues.push('MEMBER_SCOPE_NOT_AUTHORIZED');
  if(!['READY_SET','HIDE_SEEK','SNAP_POP','ready-set','hide-seek','snap-pop'].includes(sourceApp))issues.push('SOURCE_APP_NOT_ALLOWED');
  return {ok:issues.length===0,policy_version:VERSION,issues,scope:issues.length?null:{family_id:familyId,member_id:memberId},source_app:sourceApp||null};
}
module.exports=Object.freeze({VERSION,authorize});
