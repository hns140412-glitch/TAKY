'use strict';

const VERSION='TAKY_TATOEBA_LIVE_PROVIDER_TRANSPORT_V1';
const API_BASE='https://api.tatoeba.org';
const SOURCE_ID='LANGUAGE_TATOEBA_TEXT_2026';
const SOURCE_REF='INDEX:LANGUAGE_TATOEBA_TEXT_2026';
const clean=v=>String(v??'').trim();

function mapLicense(value){
  const v=clean(value).toUpperCase();
  if(v==='CC BY 2.0 FR')return 'CC-BY-2.0-FR';
  if(v==='CC0 1.0')return 'CC0';
  return null;
}

function buildSearchUrl({
  language,
  query,
  max_word_count=12,
  limit=10,
  require_owned=true,
  exclude_unapproved=true,
  exclude_license_problem=true
}={}){
  const lang=clean(language);
  const q=clean(query);
  if(!lang)throw new Error('TATOEBA_LANGUAGE_REQUIRED');
  if(!q)throw new Error('TATOEBA_QUERY_REQUIRED');
  const url=new URL('/v1/sentences',API_BASE);
  url.searchParams.set('lang',lang);
  url.searchParams.set('q',q);
  if(Number.isInteger(max_word_count)&&max_word_count>0)url.searchParams.set('word_count','-'+max_word_count);
  if(Number.isInteger(limit)&&limit>0)url.searchParams.set('limit',String(Math.min(limit,20)));
  if(require_owned)url.searchParams.set('is_orphan','no');
  if(exclude_unapproved)url.searchParams.set('is_unapproved','no');
  if(exclude_license_problem)url.searchParams.set('license','!PROBLEM');
  url.searchParams.set('showtrans','none');
  return url.toString();
}

function buildItemUrl(sentenceId){
  const id=clean(sentenceId);
  if(!/^[0-9]+$/.test(id))throw new Error('TATOEBA_SENTENCE_ID_INVALID');
  return new URL('/v1/sentences/'+encodeURIComponent(id),API_BASE).toString();
}

async function requestJson(url,{fetch_impl=globalThis.fetch,timeout_ms=10000}={}){
  if(typeof fetch_impl!=='function')return {ok:false,state:'TRANSPORT_UNAVAILABLE',reason:'FETCH_NOT_CONFIGURED'};
  const controller=typeof AbortController==='function'?new AbortController():null;
  const timer=controller?setTimeout(()=>controller.abort(),timeout_ms):null;
  try{
    const res=await fetch_impl(url,{
      method:'GET',
      headers:{'accept':'application/json','user-agent':'TAKY-Tatoeba-Reference/1.0'},
      signal:controller?.signal
    });
    if(!res||res.ok!==true){
      return {ok:false,state:'PROVIDER_HTTP_ERROR',status:res?.status??null,url};
    }
    const body=await res.json();
    return {ok:true,state:'PROVIDER_RESPONSE_OK',body,url,status:res.status};
  }catch(error){
    return {ok:false,state:'PROVIDER_TRANSPORT_ERROR',reason:error?.name==='AbortError'?'TIMEOUT':clean(error?.message)||'TRANSPORT_ERROR',url};
  }finally{
    if(timer)clearTimeout(timer);
  }
}

function toProviderCandidate(row={},retrievedAt=new Date().toISOString()){
  if(!row||typeof row!=='object'||Array.isArray(row))return {ok:false,state:'PROVIDER_RESPONSE_INVALID'};
  const id=clean(row.id);
  const text=clean(row.text);
  const lang=clean(row.lang).toLowerCase();
  const mappedLicense=mapLicense(row.license);
  if(!id||!text||!lang)return {ok:false,state:'PROVIDER_RESPONSE_INVALID',reason:'CORE_FIELDS_MISSING'};
  if(!mappedLicense)return {ok:false,state:'PROVENANCE_INCOMPLETE',reason:'LICENSE_UNKNOWN_OR_PROBLEM',sentence_id:id};
  const owner=clean(row.owner);
  if(mappedLicense==='CC-BY-2.0-FR'&&!owner){
    return {ok:false,state:'PROVENANCE_INCOMPLETE',reason:'CC_BY_OWNER_MISSING',sentence_id:id};
  }
  const itemApiUrl=buildItemUrl(id);
  return {
    ok:true,
    state:'LIVE_ITEM_MAPPED',
    version:VERSION,
    candidate:{
      provider:'Tatoeba',
      sentence_id:id,
      text,
      lang,
      language:lang,
      sentence_url:'https://tatoeba.org/en/sentences/show/'+encodeURIComponent(id),
      provider_item_url:itemApiUrl,
      owner_or_author:owner||null,
      owner:owner||null,
      license:mappedLicense,
      license_raw:clean(row.license),
      license_provenance:itemApiUrl,
      license_source_field:'data.license',
      retrieved_at:retrievedAt,
      source_id:SOURCE_ID,
      source_ref:SOURCE_REF,
      is_unapproved:row.is_unapproved===true,
      is_orphan:row.owner==null||!owner,
      transport_authority:false,
      index_owner_authority:false,
      child_facing_approved:false,
      normative_usage_authority:false,
      frequency_authority:false,
      mastery_authority:false
    }
  };
}

async function searchSentences(input={},options={}){
  let url;
  try{url=buildSearchUrl(input);}catch(error){
    return {ok:false,state:'QUERY_INVALID',reason:clean(error.message)};
  }
  const response=await requestJson(url,options);
  if(!response.ok)return response;
  const rows=Array.isArray(response.body?.data)?response.body.data:null;
  if(!rows)return {ok:false,state:'PROVIDER_RESPONSE_INVALID',reason:'DATA_ARRAY_MISSING',url};
  const retrievedAt=new Date().toISOString();
  const mapped=rows.map(row=>toProviderCandidate(row,retrievedAt));
  return {
    ok:true,
    state:'LIVE_SEARCH_OK',
    version:VERSION,
    url,
    paging:response.body?.paging||null,
    candidates:mapped.filter(x=>x.ok).map(x=>x.candidate),
    rejected:mapped.filter(x=>!x.ok)
  };
}

async function fetchSentenceById(sentenceId,options={}){
  let url;
  try{url=buildItemUrl(sentenceId);}catch(error){
    return {ok:false,state:'QUERY_INVALID',reason:clean(error.message)};
  }
  const response=await requestJson(url,options);
  if(!response.ok)return response;
  const row=response.body?.data;
  if(!row||typeof row!=='object')return {ok:false,state:'PROVIDER_RESPONSE_INVALID',reason:'DATA_OBJECT_MISSING',url};
  const mapped=toProviderCandidate(row,new Date().toISOString());
  if(!mapped.ok)return {...mapped,url};
  return {ok:true,state:'LIVE_ITEM_OK',version:VERSION,url,candidate:mapped.candidate};
}

function validateCandidate(candidate={}){
  const issues=[];
  if(candidate.source_id!==SOURCE_ID)issues.push('SOURCE_ID_INVALID');
  if(candidate.source_ref!==SOURCE_REF)issues.push('SOURCE_REF_INVALID');
  if(!clean(candidate.sentence_id))issues.push('SENTENCE_ID_MISSING');
  if(!clean(candidate.text))issues.push('TEXT_MISSING');
  if(!clean(candidate.language))issues.push('LANGUAGE_MISSING');
  if(!['CC-BY-2.0-FR','CC0'].includes(candidate.license))issues.push('LICENSE_INVALID');
  if(candidate.license==='CC-BY-2.0-FR'&&!clean(candidate.owner_or_author))issues.push('ATTRIBUTION_MISSING');
  if(!clean(candidate.license_provenance)||!clean(candidate.license_provenance).includes('/v1/sentences/'))issues.push('ITEM_LICENSE_PROVENANCE_INVALID');
  if(candidate.index_owner_authority!==false)issues.push('INDEX_OWNER_AUTHORITY_LEAK');
  if(candidate.child_facing_approved!==false)issues.push('CHILD_APPROVAL_LEAK');
  if(candidate.normative_usage_authority!==false||candidate.frequency_authority!==false||candidate.mastery_authority!==false)issues.push('CLAIM_AUTHORITY_LEAK');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({
  VERSION,API_BASE,SOURCE_ID,SOURCE_REF,mapLicense,buildSearchUrl,buildItemUrl,requestJson,toProviderCandidate,searchSentences,fetchSentenceById,validateCandidate
});
