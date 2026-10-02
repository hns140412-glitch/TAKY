'use strict';

const Curation=require('../verification/reference-curation-receipt.js');

const VERSION='TAKY_TATOEBA_ITEM_LEVEL_SELECTION_FILTER_V1';
const SOURCE_ID='LANGUAGE_TATOEBA_TEXT_2026';
const SOURCE_REF='INDEX:LANGUAGE_TATOEBA_TEXT_2026';
const clean=v=>String(v??'').trim();
const lower=v=>clean(v).toLowerCase();

const PROBLEM_TAGS=new Set([
  '@change','@change or delete','@change or unlink','@check','@check translation','@delete','@delete maybe',
  '@needs completion','@needs native check','@not a sentence','@wrong translation','@possibly copyright infringement'
]);
const BLOCKED_CLAIMS=new Set(['normative usage','frequency','grade alignment','curriculum membership','learner mastery','independent recall','causal learning effectiveness']);
const HUMAN_REVIEWER_ROLES=new Set(['PARENT','TEACHER','QUALIFIED_REVIEWER']);

function licenseAllowed(v){
  return v==='CC-BY-2.0-FR'||v==='CC0';
}

function targetMatches(text,target,acceptableVariants=[]){
  const hay=lower(text);
  const values=[target,...(Array.isArray(acceptableVariants)?acceptableVariants:[])].map(lower).filter(Boolean);
  return values.some(v=>hay.includes(v));
}

function validateCuration(item={},request={},review={}){
  const childFacing=request.requested_use==='CHILD_FACING'||request.child_facing===true;
  if(!childFacing)return {ok:true,receipt:null};
  const receipt=review.curation_receipt||request.curation_receipt||null;
  if(!receipt)return {ok:false,state:'REFERENCE_ONLY',reason:'CHILD_FACING_REVIEW_MISSING'};
  if(!receipt||typeof receipt!=='object'||Array.isArray(receipt)){
    return {ok:false,state:'REVIEW_REQUIRED',reason:'CURATION_RECEIPT_INVALID',issues:['STRUCTURED_RECEIPT_REQUIRED']};
  }
  const checked=Curation.validate(receipt,item);
  if(!checked.ok)return {ok:false,state:'REVIEW_REQUIRED',reason:'CURATION_RECEIPT_INVALID',issues:checked.issues};
  if(item.is_orphan===true&&!HUMAN_REVIEWER_ROLES.has(clean(receipt.reviewer_role))){
    return {ok:false,state:'REVIEW_REQUIRED',reason:'ORPHAN_REQUIRES_HUMAN_REVIEW'};
  }
  return {ok:true,receipt};
}

function select(item={},request={},review={}){
  const required=['sentence_id','text','language','sentence_url','license','license_provenance','retrieved_at','source_id','source_ref','target_learning_id','target_form','context_or_sense_ref'];
  for(const k of required){
    if(!clean(item[k]))return {ok:false,state:'REJECTED',version:VERSION,reason:'MISSING_'+k.toUpperCase()};
  }
  if(item.source_id!==SOURCE_ID||item.source_ref!==SOURCE_REF){
    return {ok:false,state:'REJECTED',version:VERSION,reason:'SOURCE_IDENTITY_INVALID'};
  }
  if(!licenseAllowed(item.license))return {ok:false,state:'REJECTED',version:VERSION,reason:'UNKNOWN_LICENSE'};
  if(item.license==='CC-BY-2.0-FR'&&!clean(item.owner_or_author)){
    return {ok:false,state:'REJECTED',version:VERSION,reason:'ATTRIBUTION_REQUIRED'};
  }

  const tags=(Array.isArray(item.tags)?item.tags:[]).map(lower);
  if(tags.some(t=>PROBLEM_TAGS.has(t)))return {ok:false,state:'REJECTED',version:VERSION,reason:'PROBLEM_TAG'};
  if(item.is_unapproved===true)return {ok:false,state:'REJECTED',version:VERSION,reason:'UNAPPROVED'};

  const childFacing=request.requested_use==='CHILD_FACING'||request.child_facing===true;
  const requestedLanguage=lower(request.requested_language||item.language);
  if(lower(item.language)!==requestedLanguage){
    return {ok:false,state:'REJECTED',version:VERSION,reason:'LANGUAGE_MISMATCH'};
  }
  if(!targetMatches(item.text,request.target_form||item.target_form,request.acceptable_variants)){
    return {ok:false,state:'REJECTED',version:VERSION,reason:'TARGET_FORM_NOT_PRESENT'};
  }
  if(item.context_verified!==true||request.context_verified===false){
    return {ok:false,state:'REJECTED',version:VERSION,reason:'CONTEXT_OR_SENSE_UNVERIFIED'};
  }
  if(childFacing&&item.safety_age_fit_verified!==true){
    return {ok:false,state:'REJECTED',version:VERSION,reason:'SAFETY_AGE_FIT_UNVERIFIED'};
  }

  const requestedClaims=(Array.isArray(request.requested_claims)?request.requested_claims:[]).map(lower);
  const blocked=requestedClaims.find(x=>BLOCKED_CLAIMS.has(x));
  if(blocked)return {ok:false,state:'REJECTED',version:VERSION,reason:'PROHIBITED_CLAIM:'+blocked};

  const curation=validateCuration(item,request,review);
  if(!curation.ok){
    return {
      ok:curation.state==='REFERENCE_ONLY',
      state:curation.state,
      version:VERSION,
      reason:curation.reason,
      issues:curation.issues||[],
      child_facing_approved:false
    };
  }

  const selectedAt=clean(request.selected_at||item.retrieved_at);
  const selection={
    selection_id:clean(request.selection_id)||`tatoeba:${item.sentence_id}:${clean(item.target_learning_id)}`,
    sentence_id:clean(item.sentence_id),
    text:item.text,
    language:lower(item.language),
    source_id:SOURCE_ID,
    source_ref:SOURCE_REF,
    sentence_url:item.sentence_url,
    owner_or_author:item.owner_or_author||null,
    license:item.license,
    license_provenance:item.license_provenance,
    attribution_text_or_components:item.license==='CC-BY-2.0-FR'?{
      source:'Tatoeba',author:item.owner_or_author,url:item.sentence_url,license:item.license
    }:{source:'Tatoeba',url:item.sentence_url,license:item.license},
    target_learning_id:item.target_learning_id,
    target_form:item.target_form,
    context_or_sense_ref:item.context_or_sense_ref,
    quality_gate_result:'PASS',
    safety_age_fit_result:childFacing?'PASS':'NOT_REQUIRED_BY_THIS_REQUEST',
    review_state:childFacing?'CHILD_FACING_APPROVED':'REFERENCE_ONLY',
    review_receipt:curation.receipt?.receipt_id||null,
    review_receipt_version:curation.receipt?.receipt_version||null,
    reviewer_role:curation.receipt?.reviewer_role||null,
    reviewed_at:curation.receipt?.reviewed_at||null,
    selected_at:selectedAt,
    cannot_claim:['NORMATIVE_USAGE','FREQUENCY','GRADE_ALIGNMENT','CURRICULUM_MEMBERSHIP','LEARNER_MASTERY','INDEPENDENT_RECALL','CAUSAL_EFFECTIVENESS']
  };
  return {ok:true,state:selection.review_state,version:VERSION,selection,child_facing_approved:selection.review_state==='CHILD_FACING_APPROVED'};
}

function validateSelection(result={}){
  const issues=[];
  if(result.child_facing_approved===true&&!clean(result.selection?.review_receipt))issues.push('CHILD_APPROVAL_WITHOUT_REVIEW_RECEIPT');
  if(result.child_facing_approved===true&&result.selection?.review_receipt_version!==Curation.VERSION)issues.push('CURATION_RECEIPT_VERSION_INVALID');
  if(result.selection){
    if(result.selection.source_id!==SOURCE_ID)issues.push('SOURCE_ID_MUTATED');
    if(result.selection.source_ref!==SOURCE_REF)issues.push('SOURCE_REF_MUTATED');
    if((result.selection.cannot_claim||[]).length<4)issues.push('CLAIM_GUARDS_MISSING');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,SOURCE_ID,SOURCE_REF,PROBLEM_TAGS,BLOCKED_CLAIMS,HUMAN_REVIEWER_ROLES,licenseAllowed,targetMatches,validateCuration,select,validateSelection});
