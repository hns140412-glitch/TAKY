(function(root,factory){
  const api=factory();
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  if(root) root.TakyCrewEvidenceBrowserProviderV1=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_CREW_EVIDENCE_BROWSER_PROVIDER_V1';
  const EXPECTED_HTTP='TAKY_CENTRAL_CREW_EVIDENCE_HTTP_V1';
  const SCHEMA='TAKY_CREW_EVIDENCE_HANDOFF_V1';
  const ENDPOINT_PATH='/api/crew/evidence';
  const clean=v=>typeof v==='string'?v.trim():'';
  const object=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
  function endpoint(url){
    let u;try{u=new URL(url);}catch{throw Error('EXPLICIT_HTTPS_CENTRAL_CREW_ENDPOINT_REQUIRED')}
    if(u.protocol!=='https:'||u.username||u.password||u.search||u.hash||u.pathname!==ENDPOINT_PATH)
      throw Error('EXPLICIT_HTTPS_CENTRAL_CREW_ENDPOINT_REQUIRED');
    return u.href;
  }
  function packetValid(packet,appId){
    return object(packet)&&packet.schema===SCHEMA&&packet.source_app===appId&&
      Array.isArray(packet.events)&&packet.events.length>0&&packet.events.every(e=>
        object(e)&&e.verified===true&&clean(e.event_id)&&clean(e.type)&&clean(e.evidence_ref)&&clean(e.character_id));
  }
  function responseValid(body,scope,appId){
    return object(body)&&body.ok===true&&body.endpoint_version===EXPECTED_HTTP&&
      body.acknowledgement_kind==='CREW_EVIDENCE_RECEIPT'&&clean(body.receipt_id)&&
      body.storage_confirmed===true&&body.relationship_auto_commit===false&&
      body.learning_engine_state_mutated===false&&body.source_app===appId&&
      body.receipt_scope?.family_id===scope.family_id&&body.receipt_scope?.member_id===scope.member_id;
  }
  function create({appId,endpointUrl,fetchImpl,tokenProvider,scopeProvider,eventTarget}={}){
    const app=clean(appId);
    if(!app)throw Error('APP_ID_REQUIRED');
    const url=endpoint(endpointUrl);
    if(typeof fetchImpl!=='function'||typeof tokenProvider!=='function'||typeof scopeProvider!=='function')
      throw Error('CENTRAL_CREW_BROWSER_PROVIDERS_REQUIRED');
    const target=eventTarget||null;
    const emit=(type,detail)=>{try{target?.dispatchEvent?.(new target.CustomEvent(type,{detail}));}catch{}};
    async function send(packet){
      if(!packetValid(packet,app))return {ok:false,reason:'VERIFIED_CREW_PACKET_REQUIRED'};
      let scope;try{scope=await scopeProvider();}catch{return {ok:false,reason:'CENTRAL_CREW_SCOPE_UNAVAILABLE'}}
      if(scope?.authenticated!==true||!clean(scope.family_id)||!clean(scope.member_id))
        return {ok:false,reason:'CENTRAL_CREW_AUTHENTICATED_SCOPE_REQUIRED'};
      const normalized=Object.freeze({family_id:clean(scope.family_id),member_id:clean(scope.member_id)});
      let token;try{token=clean(await tokenProvider());}catch{return {ok:false,reason:'CENTRAL_CREW_TOKEN_UNAVAILABLE'}}
      if(!token||token.length>8192)return {ok:false,reason:'CENTRAL_CREW_TOKEN_REQUIRED'};
      const payload={schema:SCHEMA,source_app:app,context:normalized,events:packet.events.map(e=>({...e}))};
      let response,body;
      try{
        response=await fetchImpl(url,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json',Authorization:'Bearer '+token},credentials:'omit',redirect:'error',cache:'no-store',body:JSON.stringify(payload)});
        body=await response.json();
      }catch{return {ok:false,reason:'CENTRAL_CREW_HTTP_UNAVAILABLE'};}
      if(response.status!==200||!responseValid(body,normalized,app))
        return {ok:false,reason:response.status===401||response.status===403?'CENTRAL_CREW_AUTHORIZATION_REQUIRED':'CENTRAL_CREW_RESPONSE_CONTRACT_INVALID',status:response.status};
      return Object.freeze({ok:true,receipt_id:body.receipt_id,imported_event_ids:Object.freeze([...(body.imported_event_ids||[])]),duplicate_event_ids:Object.freeze([...(body.duplicate_event_ids||[])]),storage_confirmed:true});
    }
    function install(){
      if(!target?.addEventListener)return {ok:false,reason:'EVENT_HOST_UNAVAILABLE'};
      const handler=ev=>Promise.resolve(send(ev?.detail)).then(result=>emit('taky:crew-evidence-central-result',Object.freeze({app_id:app,result}))).catch(()=>{});
      target.addEventListener('taky:crew-evidence-export',handler);
      return Object.freeze({ok:true,app_id:app,version:VERSION});
    }
    return Object.freeze({VERSION,appId:app,send,install});
  }
  return Object.freeze({VERSION,EXPECTED_HTTP,SCHEMA,ENDPOINT_PATH,create,packetValid,responseValid});
});
