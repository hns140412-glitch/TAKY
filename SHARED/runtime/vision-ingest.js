(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyVisionIngest=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const IMAGE_MIME=/^image\/(jpeg|png|webp|heic|heif)$/i;

  const clean=v=>String(v??'').trim();
  const clone=v=>v===undefined?undefined:JSON.parse(JSON.stringify(v));

  function normalizeManifest(items=[]){
    if(!Array.isArray(items)) return {ok:false,reason:'MANIFEST_NOT_ARRAY',items:[]};
    const out=[];
    const errors=[];
    const seen=new Set();
    for(let i=0;i<items.length;i++){
      const raw=items[i]||{};
      const source_id=clean(raw.source_id||raw.capture_item_id||raw.page_id||raw.id);
      const mime_type=clean(raw.mime_type||raw.type);
      if(!source_id){errors.push({index:i,reason:'SOURCE_ID_REQUIRED'});continue}
      if(seen.has(source_id)){errors.push({index:i,source_id,reason:'DUPLICATE_SOURCE_ID'});continue}
      seen.add(source_id);
      const analyzable=IMAGE_MIME.test(mime_type) && raw.exclude_from_analysis!==true;
      out.push(Object.freeze({
        source_id,
        mime_type,
        file_name:clean(raw.file_name||raw.name)||null,
        size:Number.isFinite(Number(raw.size))?Number(raw.size):null,
        analyzable,
        exclusion_reason:analyzable?null:(raw.exclude_from_analysis===true?'EXPLICITLY_EXCLUDED':'UNSUPPORTED_MIME'),
        metadata:clone(raw.metadata||null)
      }));
    }
    return {ok:errors.length===0,items:Object.freeze(out),errors:Object.freeze(errors)};
  }

  function buildRequest({request_id,source,manifest,metadata=null}={}){
    const normalized=normalizeManifest(manifest);
    if(!normalized.ok) return {ok:false,reason:'INVALID_MANIFEST',errors:normalized.errors};
    const analyzable=normalized.items.filter(x=>x.analyzable);
    if(!analyzable.length) return {ok:false,reason:'NO_ANALYZABLE_SOURCES'};
    const rid=clean(request_id)||('vision_'+Date.now()+'_'+Math.random().toString(36).slice(2,8));
    const src=clean(source);
    if(!src) return {ok:false,reason:'SOURCE_REQUIRED'};
    return {
      ok:true,
      request:Object.freeze({
        ingest_version:1,
        request_id:rid,
        source:src,
        source_count:normalized.items.length,
        analyzable_source_ids:Object.freeze(analyzable.map(x=>x.source_id)),
        manifest:normalized.items,
        metadata:clone(metadata),
        created_at:new Date().toISOString()
      })
    };
  }

  function normalizeEvidenceIds(value){
    const arr=Array.isArray(value)?value:[];
    return Object.freeze([...new Set(arr.map(clean).filter(Boolean))]);
  }

  function normalizeResult({request_id,provider=null,model=null,items=[]}={}){
    const rid=clean(request_id);
    if(!rid) return {ok:false,reason:'REQUEST_ID_REQUIRED'};
    if(!Array.isArray(items)) return {ok:false,reason:'RESULT_ITEMS_NOT_ARRAY'};
    const normalized=[];
    for(let i=0;i<items.length;i++){
      const raw=items[i]||{};
      normalized.push(Object.freeze({
        result_id:clean(raw.result_id)||(`result_${rid}_${i}`),
        evidence_source_ids:normalizeEvidenceIds(raw.evidence_source_ids||raw.evidence_item_ids||raw.source_ids),
        confidence:raw.confidence==null?null:Number(raw.confidence),
        provider_payload:clone(raw.provider_payload??raw.payload??raw.value??null),
        metadata:clone(raw.metadata||null)
      }));
    }
    return {
      ok:true,
      result:Object.freeze({
        ingest_version:1,
        request_id:rid,
        provider:clean(provider)||null,
        model:clean(model)||null,
        items:Object.freeze(normalized),
        received_at:new Date().toISOString()
      })
    };
  }

  function validateEvidence(result,knownSourceIds=[]){
    const known=new Set((knownSourceIds||[]).map(clean).filter(Boolean));
    const unknown=[];
    for(const item of result?.items||[]){
      for(const id of item.evidence_source_ids||[]) if(!known.has(id)) unknown.push({result_id:item.result_id,source_id:id});
    }
    return {ok:unknown.length===0,unknown:Object.freeze(unknown)};
  }

  return Object.freeze({
    version:'1.0.0',
    normalizeManifest,
    buildRequest,
    normalizeResult,
    validateEvidence
  });
});
