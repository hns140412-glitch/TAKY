'use strict';

/**
 * Read-only strong-store source for server-issued specialist references.
 * The packet's reference_id is a locator, never evidence of authorization.
 * Record creation/reviewer approval must happen through separately approved
 * server-only administrative services, not this or any PWA endpoint.
 */
const crypto=require('node:crypto');
const VERSION='TAKY_SERVER_SPECIALIST_REFERENCE_STORE_V1';
const clean=x=>typeof x==='string'?x.trim():'';
const id=x=>clean(x)&&x===clean(x)&&x.length<=128;
const hash=items=>crypto.createHash('sha256').update(JSON.stringify(items)).digest('hex');
const scopedKey=(kind,fields)=>'learning-reference/'+kind+'/'+hash(fields)+'/v1';

function assessmentKey({family_id,member_id,event_id,source_app,reference_id}={}){
 if(![family_id,member_id,event_id,source_app,reference_id].every(id)||
    !['hide-seek','ready-set'].includes(source_app))
   throw Error('ASSESSMENT_REFERENCE_SCOPE_INVALID');
 return scopedKey('assessment',[family_id,member_id,event_id,source_app,reference_id]);
}
function humanReviewKey({family_id,member_id,event_id,source_app}={}){
 if(![family_id,member_id,event_id].every(id)||source_app!=='snap-pop')
   throw Error('HUMAN_REVIEW_SCOPE_INVALID');
 return scopedKey('human-review',[family_id,member_id,event_id,source_app]);
}
function create({store}={}){
 if(typeof store?.getWithMetadata!=='function')
   throw Error('SERVER_ONLY_REFERENCE_STORE_REQUIRED');
 async function lookup(key,kind,scope){
   const read=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
   if(!read)return null;
   if(read.consistency!=='strong'||!clean(read.etag))
     throw Error('REFERENCE_STRONG_READ_REQUIRED');
   const row=read.data;
   const expected=kind==='assessment'?'TAKY_SERVER_ASSESSMENT_REFERENCE_V1':'TAKY_SERVER_HUMAN_REVIEW_V1';
   const issuer=kind==='assessment'?'CENTRAL_ASSESSMENT_ISSUER':'CENTRAL_REVIEW_GATE';
   if(!row||row.version!==1||row.authority!==expected||
      row.issuer_service!==issuer||row.issuer_authorized!==true||
      Object.keys(scope).some(k=>row[k]!==scope[k]))
     throw Error('REFERENCE_SERVER_PROVENANCE_INVALID');
   if(kind==='review'&&(!clean(row.reviewer_authorization_receipt_id)||
      row.reviewer_permission_checked!==true))
     throw Error('REVIEWER_AUTHORIZATION_RECEIPT_REQUIRED');
   return {...row};
 }
 return Object.freeze({
   version:VERSION,
   async loadAssessment(scope){
     return lookup(assessmentKey(scope),'assessment',scope);
   },
   async loadHumanReview(scope){
     return lookup(humanReviewKey(scope),'review',scope);
   }
 });
}
module.exports=Object.freeze({VERSION,assessmentKey,humanReviewKey,create});
