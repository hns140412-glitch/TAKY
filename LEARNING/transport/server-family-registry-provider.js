'use strict';

const crypto=require('node:crypto');

const VERSION='TAKY_SERVER_FAMILY_REGISTRY_PROVIDER_V1';
const REGISTRY_AUTHORITY='TAKY_SERVER_FAMILY_REGISTRY_V1';
const ROLES=new Set(['PARENT','CHILD','FAMILY_ADULT']);
const clean=v=>typeof v==='string'?v.trim():'';
const validId=v=>typeof v==='string'&&v===clean(v)&&v.length>0&&v.length<=128;
const unique=rows=>new Set(rows).size===rows.length;
const sha256=s=>crypto.createHash('sha256').update(s).digest('hex');

function subjectRecordKey(subject){
 if(!validId(subject))throw Error('GOOGLE_SUBJECT_REQUIRED');
 // The canonical Google sub is never placed un-hashed in a storage key.
 return 'identity/google-oidc/'+sha256('GOOGLE_OIDC:'+subject)+'/registry-v1';
}

/**
 * Read-only projection of an administratively provisioned CENTRAL family
 * registry. The browser cannot write this namespace or set role/grants.
 * Records are re-read strongly at every authentication, without a local
 * permission cache. The registry administrator owns revocation/versioning.
 *
 * This is a real storage adapter, NOT an OAuth login, admin enrollment
 * endpoint, or evidence/award/gem ledger.
 */
function create({store,now=Date.now}={}){
 if(typeof store?.getWithMetadata!=='function')
   throw Error('SERVER_REGISTRY_STRONG_STORE_REQUIRED');
 if(typeof now!=='function')throw Error('TRUSTED_CLOCK_REQUIRED');
 async function lookupMemberships({provider,subject}={}){
   if(provider!=='GOOGLE_OIDC'||!validId(subject))return [];
   const key=subjectRecordKey(subject);
   // No request/browser parameter selects the family or grants.
   const entry=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
   if(!entry)return [];
   if(typeof entry.etag!=='string'||!entry.etag||
      entry.consistency!=='strong')throw Error('REGISTRY_STRONG_READ_REQUIRED');
   const record=entry.data;
   if(!record||record.authority!==REGISTRY_AUTHORITY||
      record.version!==1||record.identity_provider!=='GOOGLE_OIDC'||
      record.subject_sha256!==sha256('GOOGLE_OIDC:'+subject))
     throw Error('REGISTRY_PROVENANCE_INVALID');
   if(record.status==='REVOKED'||record.status==='INACTIVE')return [];
   const expiry=Date.parse(record.expires_at||'');
   if(record.status!=='ACTIVE'||!Number.isFinite(expiry)||
      expiry<=now())return [];
   if(!Array.isArray(record.memberships)||!record.memberships.length||
      record.memberships.length>32)throw Error('REGISTRY_MEMBERSHIPS_INVALID');
   const families=new Set();
   return record.memberships.map(row=>{
     if(!row||row.status!=='ACTIVE'||!validId(row.family_id)||
        !validId(row.self_member_id)||!ROLES.has(row.role)||
        families.has(row.family_id))throw Error('REGISTRY_FAMILY_MEMBERSHIP_INVALID');
     families.add(row.family_id);
     const active=row.active_family_member_ids, grants=row.learning_evidence_submit_member_ids;
     const permissions=row.permissions;
     if(!Array.isArray(active)||!active.length||active.length>100||
        active.some(x=>!validId(x))||!unique(active)||
        !active.includes(row.self_member_id)||
        !Array.isArray(grants)||grants.length>100||
        grants.some(x=>!validId(x)||!active.includes(x))||!unique(grants)||
        !Array.isArray(permissions)||permissions.length>32||
        permissions.some(x=>!validId(x))||!unique(permissions))
       throw Error('REGISTRY_MEMBER_GRANT_PROVENANCE_INVALID');
     if(row.role==='CHILD'&&grants.some(id=>id!==row.self_member_id))
       throw Error('CHILD_CROSS_MEMBER_GRANT_FORBIDDEN');
     // Return only the existing Google principal adapter's trusted contract.
     // No email, display name, unrelated member list, or registry key escapes.
     return {
       status:'ACTIVE',family_id:row.family_id,
       self_member_id:row.self_member_id,role:row.role,
       learning_evidence_submit_member_ids:[...grants],
       permissions:[...permissions]
     };
   });
 }
 return Object.freeze({version:VERSION,lookupMemberships});
}
module.exports=Object.freeze({VERSION,REGISTRY_AUTHORITY,subjectRecordKey,create});
