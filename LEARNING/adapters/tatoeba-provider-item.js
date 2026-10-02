'use strict';

const VERSION='TAKY_TATOEBA_PROVIDER_ITEM_ADAPTER_V1';
const SOURCE_ID='LANGUAGE_TATOEBA_TEXT_2026';
const SOURCE_REF='INDEX:LANGUAGE_TATOEBA_TEXT_2026';
const clean=v=>String(v??'').trim();
const lower=v=>clean(v).toLowerCase();

function normalizeLicense(value){
  const raw=clean(value);
  const k=raw.toLowerCase().replace(/[\s_]+/g,'-');
  if(['cc-by-2.0-fr','cc-by-2.0-france','ccby-2.0-fr'].includes(k)) return 'CC-BY-2.0-FR';
  if(['cc0','cc0-1.0','public-domain-cc0'].includes(k)) return 'CC0';
  return null;
}

function readAuthor(item={}){
  return clean(item.owner_or_author||item.author||item.owner?.username||item.owner?.name||item.user?.username||item.user?.name);
}

function readId(item={}){
  const v=item.sentence_id??item.id;
  return clean(v);
}

function readLanguage(item={}){
  return lower(item.language||item.lang||item.language_code);
}

function readTags(item={}){
  const tags=Array.isArray(item.tags)?item.tags:[];
  return tags.map(x=>lower(typeof x==='string'?x:(x?.name||x?.tag))).filter(Boolean);
}

function readApproved(item={}){
  if(item.is_unapproved===true) return false;
  if(item.is_unapproved===false) return true;
  if(item.approved===true) return true;
  if(item.approved===false) return false;
  if(item.is_approved===true) return true;
  if(item.is_approved===false) return false;
  return null;
}

function normalizeProviderItem(item={},query={}){
  if(!item||typeof item!=='object'||Array.isArray(item)){
    return {ok:false,state:'PROVIDER_RESPONSE_INVALID',version:VERSION};
  }

  const sentenceId=readId(item);
  const text=clean(item.text||item.sentence);
  const language=readLanguage(item);
  const requestedLanguage=lower(query.requested_language);
  if(!sentenceId) return {ok:false,state:'ITEM_ID_MISSING',version:VERSION};
  if(!text) return {ok:false,state:'TEXT_MISSING',version:VERSION,sentence_id:sentenceId};
  if(!language||!requestedLanguage||language!==requestedLanguage){
    return {ok:false,state:'LANGUAGE_MISSING_OR_MISMATCH',version:VERSION,sentence_id:sentenceId,language:language||null};
  }

  const license=normalizeLicense(item.license||item.license_name||item.license_code);
  const licenseProvenance=clean(item.license_provenance||item.license_url||item.license_source);
  const author=readAuthor(item);
  if(!license||!licenseProvenance){
    return {ok:false,state:'PROVENANCE_INCOMPLETE',version:VERSION,sentence_id:sentenceId,reason:!license?'LICENSE_UNKNOWN':'LICENSE_PROVENANCE_MISSING'};
  }
  if(license==='CC-BY-2.0-FR'&&!author){
    return {ok:false,state:'PROVENANCE_INCOMPLETE',version:VERSION,sentence_id:sentenceId,reason:'OWNER_OR_ATTRIBUTION_MISSING_WHEN_REQUIRED'};
  }

  const approved=readApproved(item);
  if(approved===false){
    return {ok:false,state:'QUALITY_HOLD',version:VERSION,sentence_id:sentenceId,reason:'UNAPPROVED_ITEM'};
  }
  const childFacing=query.requested_use==='CHILD_FACING'||query.child_facing===true;
  if(childFacing&&item.is_orphan===true){
    return {ok:false,state:'QUALITY_HOLD',version:VERSION,sentence_id:sentenceId,reason:'ORPHAN_CHILD_FACING_CANDIDATE'};
  }
  if(query.context_verified!==true){
    return {ok:false,state:'CONTEXT_HOLD',version:VERSION,sentence_id:sentenceId,reason:'CONTEXT_OR_SENSE_UNVERIFIED'};
  }
  if(childFacing&&query.safety_age_fit_verified!==true){
    return {ok:false,state:'SAFETY_HOLD',version:VERSION,sentence_id:sentenceId,reason:'SAFETY_AGE_FIT_UNVERIFIED'};
  }

  const retrievedAt=clean(item.retrieved_at||query.retrieved_at);
  const sentenceUrl=clean(item.sentence_url||item.url)||`https://tatoeba.org/en/sentences/show/${encodeURIComponent(sentenceId)}`;
  const targetLearningId=clean(query.target_learning_id);
  const targetForm=clean(query.target_form);
  const contextRef=clean(query.context_or_sense_ref);
  if(!retrievedAt||!targetLearningId||!targetForm||!contextRef){
    return {ok:false,state:'PROVENANCE_INCOMPLETE',version:VERSION,sentence_id:sentenceId,reason:'QUERY_OR_RETRIEVAL_PROVENANCE_INCOMPLETE'};
  }

  const normalized={
    provider:'Tatoeba',
    sentence_id:sentenceId,
    text,
    language,
    sentence_url:sentenceUrl,
    owner_or_author:author||null,
    license,
    license_provenance:licenseProvenance,
    retrieved_at:retrievedAt,
    source_id:SOURCE_ID,
    source_ref:SOURCE_REF,
    target_learning_id:targetLearningId,
    target_form:targetForm,
    context_or_sense_ref:contextRef,
    tags:readTags(item),
    ratings:Array.isArray(item.ratings)?item.ratings:[],
    is_orphan:item.is_orphan===true,
    is_unapproved:approved===false,
    translation_links:Array.isArray(item.translation_links)?item.translation_links:[],
    provider_item_version_or_modified_at:clean(item.provider_item_version_or_modified_at||item.modified_at)||null,
    context_verified:true,
    safety_age_fit_verified:childFacing?true:(query.safety_age_fit_verified===true),
    child_facing_requested:childFacing,
    index_owner_authority:false,
    normative_usage_authority:false,
    frequency_authority:false,
    mastery_authority:false
  };

  const curated=!!clean(query.curation_receipt);
  return {
    ok:true,
    state:curated?'CANDIDATE_NORMALIZED':'REFERENCE_ONLY_CANDIDATE',
    version:VERSION,
    normalized_item:normalized,
    direct_child_approval:false,
    cannot_claim:['NORMATIVE_USAGE','FREQUENCY','LEARNER_MASTERY','CURRICULUM_ALIGNMENT']
  };
}

function validateResult(result={}){
  const issues=[];
  const allowed=new Set(['CANDIDATE_NORMALIZED','REFERENCE_ONLY_CANDIDATE','PROVIDER_RESPONSE_INVALID','ITEM_ID_MISSING','LANGUAGE_MISSING_OR_MISMATCH','TEXT_MISSING','PROVENANCE_INCOMPLETE','QUALITY_HOLD','CONTEXT_HOLD','SAFETY_HOLD','REJECTED']);
  if(!allowed.has(clean(result.state)))issues.push('STATE_INVALID');
  if(result.normalized_item){
    const n=result.normalized_item;
    if(n.source_id!==SOURCE_ID)issues.push('SOURCE_ID_MUTATED');
    if(n.source_ref!==SOURCE_REF)issues.push('SOURCE_REF_MUTATED');
    if(n.index_owner_authority!==false)issues.push('INDEX_OWNER_AUTHORITY_LEAK');
    if(n.normative_usage_authority!==false||n.frequency_authority!==false||n.mastery_authority!==false)issues.push('CLAIM_AUTHORITY_LEAK');
  }
  if(result.direct_child_approval===true)issues.push('ADAPTER_CANNOT_APPROVE_CHILD_FACING');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,SOURCE_ID,SOURCE_REF,normalizeLicense,normalizeProviderItem,validateResult});
