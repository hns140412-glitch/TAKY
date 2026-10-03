(function(root,factory){
  const api=factory();
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  if(root) root.TakyCrewEvidenceHandoffV1=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const SCHEMA='TAKY_CREW_EVIDENCE_HANDOFF_V1';
  function envelope(event,targetApp=null){
    if(!event||event.verified!==true||!event.event_id||!event.evidence_ref||!event.character_id)
      return {ok:false,reason:'VERIFIED_EVENT_REQUIRED'};
    return Object.freeze({ok:true,schema:SCHEMA,source_app:event.source_app||event.source||null,target_app:targetApp,
      authority_ref:null,events:Object.freeze([Object.freeze({...event})]),automatic_relation_commit:false});
  }
  function validateImport(packet,targetApp){
    const errors=[];
    if(!packet||packet.schema!==SCHEMA)errors.push('SCHEMA_INVALID');
    if(!packet?.authority_ref)errors.push('AUTHORITY_REF_REQUIRED');
    if(packet?.target_app&&packet.target_app!==targetApp)errors.push('TARGET_APP_MISMATCH');
    if(!Array.isArray(packet?.events)||!packet.events.length)errors.push('EVENTS_REQUIRED');
    for(const e of packet?.events||[]){
      if(e?.verified!==true||!e?.event_id||!e?.evidence_ref||!e?.character_id)errors.push('INVALID_EVENT');
    }
    return errors;
  }
  function importPacket(packet,{targetApp,evidenceRuntime,storage}={}){
    const errors=validateImport(packet,targetApp);
    if(errors.length)return {ok:false,detected:errors};
    if(!evidenceRuntime?.importVerified)return {ok:false,detected:['IMPORT_RUNTIME_UNAVAILABLE']};
    const imported=[],duplicates=[],failed=[];
    for(const event of packet.events){
      const r=evidenceRuntime.importVerified(storage,event,packet.authority_ref);
      if(r.ok)imported.push(event.event_id);
      else if(r.reason==='DUPLICATE_EVENT')duplicates.push(event.event_id);
      else failed.push({event_id:event.event_id,reason:r.reason});
    }
    return Object.freeze({ok:failed.length===0,imported:Object.freeze(imported),duplicates:Object.freeze(duplicates),
      failed:Object.freeze(failed),automatic_relation_commit:false});
  }
  function install({appId,evidenceRuntime,storage,root:host}={}){
    const r=host||globalThis;
    if(!r?.addEventListener||!r?.dispatchEvent||!r?.CustomEvent)return {ok:false,reason:'EVENT_HOST_UNAVAILABLE'};
    const exportHandler=ev=>{
      const packet=envelope(ev?.detail);
      if(packet.ok)r.dispatchEvent(new r.CustomEvent('taky:crew-evidence-export',{detail:packet}));
    };
    const importHandler=ev=>importPacket(ev?.detail,{targetApp:appId,evidenceRuntime,storage});
    r.addEventListener('taky:crew-evidence',exportHandler);
    r.addEventListener('taky:crew-evidence-import',importHandler);
    return {ok:true,app_id:appId};
  }
  return Object.freeze({SCHEMA,envelope,validateImport,importPacket,install,automaticRelationCommit:false});
});
