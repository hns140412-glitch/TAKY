(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyHttpJson=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const clean=v=>String(v??'').trim();

  function parseRetryAfter(value,nowMs=Date.now()){
    const raw=clean(value);
    if(!raw) return null;
    if(/^\d+(?:\.\d+)?$/.test(raw)) return Math.max(0,Math.ceil(Number(raw)*1000));
    const at=Date.parse(raw);
    if(!Number.isFinite(at)) return null;
    return Math.max(0,at-Number(nowMs));
  }

  function normalizeStatus(status,{retry_after=null,now_ms=Date.now()}={}){
    const code=Number(status);
    const category=
      code>=200&&code<300?'SUCCESS':
      code===401||code===403?'AUTH_REJECTED':
      code===408?'TIMEOUT':
      code===409?'CONFLICT':
      code===429?'RATE_LIMITED':
      code>=400&&code<500?'CLIENT_ERROR':
      code>=500&&code<600?'SERVER_ERROR':'UNKNOWN';
    return Object.freeze({
      status:Number.isFinite(code)?code:null,
      ok:code>=200&&code<300,
      category,
      retryable:code===408||code===429||code>=500,
      retry_after_ms:parseRetryAfter(retry_after,now_ms)
    });
  }

  function buildRequestInit({method='GET',headers={},body=null,credentials,cache,signal}={}){
    const m=clean(method).toUpperCase()||'GET';
    const out={method:m,headers:{...headers}};
    if(body!==null&&body!==undefined){
      if(typeof body==='string'||body instanceof Blob||body instanceof FormData||body instanceof URLSearchParams){
        out.body=body;
      }else{
        out.body=JSON.stringify(body);
        const hasContentType=Object.keys(out.headers).some(k=>k.toLowerCase()==='content-type');
        if(!hasContentType) out.headers['Content-Type']='application/json';
      }
    }
    if(credentials!==undefined) out.credentials=credentials;
    if(cache!==undefined) out.cache=cache;
    if(signal!==undefined) out.signal=signal;
    return out;
  }

  async function request(url,options={}){
    const fetchImpl=options.fetch_impl||globalThis.fetch;
    if(typeof fetchImpl!=='function') return {ok:false,category:'TRANSPORT_UNAVAILABLE',reason:'FETCH_UNAVAILABLE'};
    const timeoutMs=Math.max(0,Number(options.timeout_ms??15000));
    const controller=typeof AbortController!=='undefined'?new AbortController():null;
    const timer=controller&&timeoutMs>0?setTimeout(()=>controller.abort(),timeoutMs):null;
    const init=buildRequestInit({...options,signal:controller?.signal||options.signal});
    delete init.fetch_impl;
    delete init.timeout_ms;
    try{
      const response=await fetchImpl(url,init);
      const retryAfter=response.headers?.get?.('retry-after')||null;
      const status=normalizeStatus(response.status,{retry_after:retryAfter});
      let data=null;
      let parse_error=null;
      const text=await response.text();
      if(text){
        try{data=JSON.parse(text)}catch(error){parse_error=String(error?.message||error)}
      }
      return Object.freeze({
        ...status,
        url:response.url||String(url),
        data,
        raw_text:text,
        parse_error,
        headers:response.headers||null
      });
    }catch(error){
      const timedOut=error?.name==='AbortError';
      return Object.freeze({
        ok:false,
        status:null,
        category:timedOut?'TIMEOUT':'NETWORK_ERROR',
        retryable:true,
        retry_after_ms:null,
        reason:String(error?.message||error)
      });
    }finally{
      if(timer)clearTimeout(timer);
    }
  }

  return Object.freeze({
    version:'1.0.0',
    parseRetryAfter,
    normalizeStatus,
    buildRequestInit,
    request
  });
});
