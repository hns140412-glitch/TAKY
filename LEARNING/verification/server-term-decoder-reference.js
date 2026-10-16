'use strict';
/**
 * Server-owned Hide & Seek TERM_DECODER answer-key adapter.
 * Reuses the canonical independent specialist verifier. No browser answer
 * claims or self-reported correctness are accepted. Defaults fail-closed.
 * Calling host MUST provide a separate catalog release attestation callback.
 */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const Specialist=require('./server-specialist-verifier.js');
const Grade=require('../pedagogy/grade-aware-term-selector.js');
const VERSION='TAKY_SERVER_TERM_DECODER_REFERENCE_V1';
const SHA=/^[a-f0-9]{64}$/;
const TERM=/^[a-zA-Z0-9][a-zA-Z0-9_-]{1,95}$/;
const clean=x=>typeof x==='string'?x.trim():'';
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const ROOT=path.resolve(__dirname,'..','projection');
function readPinnedCatalog({catalogPath,pinnedSha256}){
 if(!SHA.test(pinnedSha256||''))throw Error('TRUSTED_CATALOG_SHA256_PIN_REQUIRED');
 const resolved=path.resolve(catalogPath||'');
 if(!resolved.startsWith(ROOT+path.sep))throw Error('CATALOG_NOT_UNDER_CODE_OWNED_DATA_ROOT');
 if(fs.lstatSync(resolved).isSymbolicLink())throw Error('UNTRUSTED_CATALOG_SYMLINK');
 const bytes=fs.readFileSync(resolved);
 if(bytes.length>5_000_000||digest(bytes)!==pinnedSha256)
   throw Error('CATALOG_IMMUTABLE_REVISION_MISMATCH');
 const catalog=JSON.parse(bytes.toString('utf8'));
 if(catalog.schema!=='TAKY_TERM_DECODER_ALIGNED_CATALOG_V1'
   ||!Array.isArray(catalog.terms)||catalog.terms.length>3000)
   throw Error('TRUSTED_CATALOG_SCHEMA_MISMATCH');
 return catalog;
}
function allowedMode(packet){
 const p=packet?.event?.payload||{};
 const s=packet?.context||{};
 const id=clean(s.learning_target_id);
 return packet?.source_app==='hide-seek'
   &&packet?.event?.source==='hide-seek'
   &&packet?.event?.event_type==='RETRIEVAL_ATTEMPT_RESULT'
   &&p.instrument_version==='HIDE_TERM_DECODER_V1'
   &&p.interaction_mode==='CORE'
   &&id.startsWith('term:')&&TERM.test(id.slice(5))
   &&clean(p.learning_target_id)===id
   &&clean(p.term_id)===id.slice(5)
   &&clean(p.subject).toLowerCase()===clean(s.subject).toLowerCase()
   &&clean(s.concept_skill_target)==='vocabulary';
}
function create({
 catalogPath, pinnedSha256, authorizeCatalogRelease,
 resolveLearnerProfile
}={}){
 if(typeof authorizeCatalogRelease!=='function')
  throw Error('INDEPENDENT_CATALOG_RELEASE_AUTHORITY_REQUIRED');
 if(typeof resolveLearnerProfile!=='function')
  throw Error('TRUSTED_GRADE_PROFILE_PROVIDER_REQUIRED');
 // Fail closed on code-owned source and pin before building the callback.
 readPinnedCatalog({catalogPath,pinnedSha256});
 const specialist=Specialist.create({
   resolveReference:async scope=>{
     if(scope.source_app!=='hide-seek'||scope.concept_skill_target!=='vocabulary'
       ||scope.verifier_type!=='RETRIEVAL_EXACT_MATCH'||!scope.learning_target_id.startsWith('term:'))
       return null;
     const id=scope.learning_target_id.slice(5);
     if(!TERM.test(id))return null;
     // Recheck immutable bytes on EVERY verification, including replays.
     const catalog=readPinnedCatalog({catalogPath,pinnedSha256});
     const matches=catalog.terms.filter(x=>x.term_id===id&&clean(x.subject).toLowerCase()===scope.subject);
     if(matches.length!==1)return null;
     const term=matches[0];
     if(term.grade_alignment?.state!=='VERIFIED'
       ||term.grade_alignment?.reviewed!==true
       ||term.grade_alignment?.authority_class!=='OFFICIAL_CURRICULUM_AND_UNIT_MAPPING_EVIDENCE'
       ||term.official_alignment?.state!=='VERIFIED'
       ||!clean(term.grade_alignment?.source_ref)||!clean(term.meaning))
       return null;
     const profile=await resolveLearnerProfile({
       family_id:scope.family_id,member_id:scope.member_id
     });
     if(!Grade.gradeMatch(term,profile).ok)return null;
     // Independent release verification must be external to catalog JSON.
     // Approving one source never signs a different byte revision or owner.
     if(await authorizeCatalogRelease({
       catalog_path:path.resolve(catalogPath),
       catalog_sha256:pinnedSha256,
       source_ref:term.grade_alignment.source_ref,
       term_id:term.term_id,
       subject:scope.subject,
       school_stage:profile.school_stage||profile.schoolStage,
       consumer:'HIDE_SEEK',
       source_owner:'LEARNING_OS'
     })!==true)return null;
     return {
       authority:'SERVER_OWNED_LEARNING_REFERENCE',
       reference_id:'server-catalog:'+pinnedSha256+':'+id,
       verifier_version:VERSION,
       source_app:scope.source_app,subject:scope.subject,
       concept_skill_target:scope.concept_skill_target,
       learning_target_id:scope.learning_target_id,
       verifier_type:'RETRIEVAL_EXACT_MATCH',
       match_rule:'EXACT_STRING',
       expected_value:term.meaning
     };
   },
   resolveHumanReview:async()=>null
 });
 return async function verifySpecialistEvidence({packet,identity}={}){
   if(!allowedMode(packet))return {ok:false,reason:'TERM_DECODER_CORE_EVENT_SCOPE_REQUIRED'};
   // Identity and membership are also rechecked in the central verifier.
   return specialist({packet,identity});
 };
}
module.exports=Object.freeze({VERSION,create,readPinnedCatalog,allowedMode});
