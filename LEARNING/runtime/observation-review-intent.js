'use strict';
/**
 * Central read-only review signals from server-durable, independently scoped
 * observation rows. A child's unverified memory report can request another
 * checkpoint; it must never become a correct answer, verified performance,
 * mastery, retention calibration, award or a dated task.
 */
const crypto=require('node:crypto');
const VERSION='TAKY_OBSERVATION_REVIEW_INTENT_V1';
const clean=x=>typeof x==='string'?x.trim():'';
function prepare(rows=[],scope={}){
 if(!clean(scope.member_id)||!clean(scope.subject)||!clean(scope.concept_skill_target))
  return {ok:false,reason:'EXPLICIT_LEARNER_SCOPE_REQUIRED'};
 const evidence=[];
 for(const row of(Array.isArray(rows)?rows:[])){
  if(row?.member_id!==scope.member_id||
     clean(row.subject).toLowerCase()!==clean(scope.subject).toLowerCase()||
     clean(row.concept_skill_target).toLowerCase()!==clean(scope.concept_skill_target).toLowerCase()||
     row?.source_app!=='ready-set'||row?.raw_app_signals?.forwarded_hide_observation!==true||
     row?.verified_outcome!==null||row?.evidence_type!=='MEMORY_RETRIEVAL_EVIDENCE'||
     row?.memory?.next_review_semantics!=='ADVISORY_SIGNAL_NOT_DATE')
   continue;
  if(!clean(row.event_id)||!Number.isFinite(Date.parse(row.observed_at||''))||
     !clean(row.instrument_version))continue;
  const advisories=(Array.isArray(row.memory.review_advisories)
   ?row.memory.review_advisories:[])
   .filter(x=>x?.advisoryOnly===true&&x.evidenceBasis==='HIDE_MEMORY_EVIDENCE'&&
     clean(x.lexicalId)&&
     (x.needsUnassistedRecall===true||
      (Number.isFinite(x.nextReviewPriority)&&x.nextReviewPriority>0)))
   .slice(0,24)
   .map(x=>({lexicalId:clean(x.lexicalId),
    nextReviewPriority:Number.isFinite(x.nextReviewPriority)
     ?Math.max(0,Math.min(100,x.nextReviewPriority)):0,
    needsUnassistedRecall:x.needsUnassistedRecall===true,
    advisoryOnly:true,evidenceBasis:'HIDE_MEMORY_EVIDENCE'}));
  if(!advisories.length)continue;
  const strength=typeof row.memory.average_strength==='number'?
   row.memory.average_strength:null;
  evidence.push({
   event_id:row.event_id,observed_at:row.observed_at,
   member_id:scope.member_id,subject:scope.subject,
   concept_skill_target:scope.concept_skill_target,
   evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',source_app:'ready-set',
   instrument_version:row.instrument_version,
   verified_performance:false,verified_outcome:null,
   observation_only:true,
   memory:{average_strength:Number.isFinite(strength)&&strength>=0&&strength<=100
     ?strength:null,review_advisories:advisories}
  });
 }
 evidence.sort((a,b)=>Date.parse(a.observed_at)-Date.parse(b.observed_at)||
  a.event_id.localeCompare(b.event_id));
 const latest=evidence.slice(-120);
 const digest=latest.length?crypto.createHash('sha256')
  .update(JSON.stringify(latest)).digest('hex'):null;
 return {ok:true,policy_version:VERSION,advisory_only:true,
  actionable:latest.length>0,evidence:latest,
  evidence_ids:latest.map(x=>x.event_id),basis_digest_sha256:digest};
}
function augmentFeedback(feedback,prepared){
 if(feedback?.ok!==true||prepared?.ok!==true)
  return {ok:false,reason:'VALID_FEEDBACK_AND_DURABLE_ADVISORY_REQUIRED'};
 if(!prepared.actionable)return feedback;
 const intents=[...feedback.intents.map(x=>({...x}))];
 const existing=intents.find(x=>x.intent==='RETRIEVAL_CHECKPOINT');
 if(existing){
  existing.priority='HIGH';
  existing.bases=[...new Set([
   ...(existing.bases||[existing.basis].filter(Boolean)),
   'HIDE_MEMORY_ADVISORY_ONLY'])];
  delete existing.basis;
 }else{
  intents.push({intent:'RETRIEVAL_CHECKPOINT',priority:'HIGH',
   basis:'HIDE_MEMORY_ADVISORY_ONLY'});
 }
 return {...feedback,intents,observation_review_authority:VERSION};
}
module.exports=Object.freeze({VERSION,prepare,augmentFeedback});
