'use strict';

const crypto=require('node:crypto');

const VERSION='TAKY_REFERENCE_CURATION_RECEIPT_V1';
const AUTHORITY='REFERENCE_CURATION_RECEIPT';
const SOURCE_ID='LANGUAGE_TATOEBA_TEXT_2026';
const SOURCE_REF='INDEX:LANGUAGE_TATOEBA_TEXT_2026';
const REVIEWER_ROLES=new Set(['PARENT','TEACHER','QUALIFIED_REVIEWER','CURATED_REFERENCE_REVIEWER']);
const PASS_FIELDS=['naturalness_correctness','context_sense_fit','safety_age_fit','license_attribution'];
const clean=v=>String(v??'').trim();

function digestText(text){
  return crypto.createHash('sha256').update(String(text??''),'utf8').digest('hex');
}

function issue(item={},review={}){
  const receipt={
    authority:AUTHORITY,
    receipt_version:VERSION,
    receipt_id:clean(review.receipt_id),
    sentence_id:clean(item.sentence_id),
    source_id:clean(item.source_id),
    source_ref:clean(item.source_ref),
    text_sha256:digestText(item.text),
    target_learning_id:clean(item.target_learning_id),
    context_or_sense_ref:clean(item.context_or_sense_ref),
    reviewed_at:clean(review.reviewed_at),
    reviewer_role:clean(review.reviewer_role),
    results:{
      naturalness_correctness:clean(review.naturalness_correctness).toUpperCase(),
      context_sense_fit:clean(review.context_sense_fit).toUpperCase(),
      safety_age_fit:clean(review.safety_age_fit).toUpperCase(),
      license_attribution:clean(review.license_attribution).toUpperCase()
    },
    notes:clean(review.notes)||null
  };
  const checked=validate(receipt,item);
  return checked.ok?{ok:true,receipt}:{ok:false,reason:'CURATION_RECEIPT_INVALID',issues:checked.issues,receipt};
}

function validate(receipt={},item={}){
  const issues=[];
  if(receipt?.authority!==AUTHORITY)issues.push('AUTHORITY_INVALID');
  if(receipt?.receipt_version!==VERSION)issues.push('VERSION_INVALID');
  for(const k of ['receipt_id','sentence_id','source_id','source_ref','text_sha256','target_learning_id','context_or_sense_ref','reviewed_at','reviewer_role']){
    if(!clean(receipt?.[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(!Number.isFinite(Date.parse(receipt?.reviewed_at||'')))issues.push('REVIEWED_AT_INVALID');
  if(!REVIEWER_ROLES.has(clean(receipt?.reviewer_role)))issues.push('REVIEWER_ROLE_INVALID');
  for(const k of PASS_FIELDS){
    if(clean(receipt?.results?.[k]).toUpperCase()!=='PASS')issues.push('REVIEW_GATE_NOT_PASS:'+k);
  }

  if(item&&Object.keys(item).length){
    if(clean(item.source_id)!==SOURCE_ID||clean(item.source_ref)!==SOURCE_REF)issues.push('ITEM_SOURCE_IDENTITY_INVALID');
    if(clean(receipt.sentence_id)!==clean(item.sentence_id))issues.push('SENTENCE_ID_MISMATCH');
    if(clean(receipt.source_id)!==clean(item.source_id))issues.push('SOURCE_ID_MISMATCH');
    if(clean(receipt.source_ref)!==clean(item.source_ref))issues.push('SOURCE_REF_MISMATCH');
    if(clean(receipt.target_learning_id)!==clean(item.target_learning_id))issues.push('LEARNING_TARGET_MISMATCH');
    if(clean(receipt.context_or_sense_ref)!==clean(item.context_or_sense_ref))issues.push('CONTEXT_REF_MISMATCH');
    if(clean(receipt.text_sha256)!==digestText(item.text))issues.push('TEXT_DIGEST_MISMATCH');
    if(!['CC-BY-2.0-FR','CC0'].includes(item.license))issues.push('ITEM_LICENSE_INVALID');
    if(item.license==='CC-BY-2.0-FR'&&!clean(item.owner_or_author))issues.push('ITEM_ATTRIBUTION_MISSING');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,AUTHORITY,SOURCE_ID,SOURCE_REF,REVIEWER_ROLES,PASS_FIELDS,digestText,issue,validate});
