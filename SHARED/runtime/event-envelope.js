(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyEventEnvelope=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  let fallbackCounter=0;

  function nowIso(){
    return new Date().toISOString();
  }

  function stable(value){
    if(value===null||typeof value!=='object') return JSON.stringify(value);
    if(Array.isArray(value)) return '['+value.map(stable).join(',')+']';
    const keys=Object.keys(value).sort();
    return '{'+keys.map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';
  }

  function digest(value){
    const text=stable(value);
    let h=2166136261;
    for(let i=0;i<text.length;i++){
      h^=text.charCodeAt(i);
      h=Math.imul(h,16777619);
    }
    return 'fnv1a32:'+(h>>>0).toString(16).padStart(8,'0');
  }

  function clone(value){
    if(typeof structuredClone==='function') return structuredClone(value);
    return value===undefined?undefined:JSON.parse(JSON.stringify(value));
  }

  function deepFreeze(value){
    if(!value||typeof value!=='object'||Object.isFrozen(value)) return value;
    Object.freeze(value);
    for(const key of Object.keys(value)) deepFreeze(value[key]);
    return value;
  }

  function randomId(){
    const cryptoObj=typeof globalThis!=='undefined'?globalThis.crypto:null;
    if(cryptoObj?.randomUUID) return 'evt_'+cryptoObj.randomUUID();
    fallbackCounter=(fallbackCounter+1)%1000000;
    return 'evt_'+Date.now().toString(36)+'_'+fallbackCounter.toString(36)+'_'+Math.random().toString(36).slice(2,10);
  }

  function validString(value){
    return typeof value==='string'&&value.trim()!=='';
  }

  function create(input={}){
    if(!input||typeof input!=='object'||Array.isArray(input)) throw new TypeError('EVENT_INPUT_NOT_OBJECT');
    if(!validString(input.source)) throw new TypeError('EVENT_SOURCE_REQUIRED');
    if(!validString(input.event_type)) throw new TypeError('EVENT_TYPE_REQUIRED');

    const payload=clone(input.payload??null);
    const event_id=validString(input.event_id)?input.event_id:randomId();
    const occurred_at=validString(input.occurred_at)?input.occurred_at:nowIso();
    const correlation_id=validString(input.correlation_id)?input.correlation_id:null;
    const idempotency_key=validString(input.idempotency_key)?input.idempotency_key:event_id;
    const sequence=Number.isInteger(input.sequence)&&input.sequence>=0?input.sequence:null;

    const envelope={
      envelope_version:1,
      event_id,
      event_type:input.event_type,
      source:input.source,
      occurred_at,
      correlation_id,
      idempotency_key,
      sequence,
      payload_digest:digest(payload),
      payload
    };
    return deepFreeze(envelope);
  }

  function validate(input){
    const errors=[];
    if(!input||typeof input!=='object'||Array.isArray(input)) return {ok:false,errors:['EVENT_NOT_OBJECT']};
    if(Number(input.envelope_version)!==1) errors.push('INVALID_ENVELOPE_VERSION');
    for(const key of ['event_id','event_type','source','occurred_at','idempotency_key','payload_digest']){
      if(!validString(input[key])) errors.push('MISSING_'+key.toUpperCase());
    }
    if(input.sequence!==null && input.sequence!==undefined && (!Number.isInteger(input.sequence)||input.sequence<0)){
      errors.push('INVALID_SEQUENCE');
    }
    if(input.payload_digest && input.payload_digest!==digest(input.payload??null)){
      errors.push('PAYLOAD_DIGEST_MISMATCH');
    }
    return {ok:errors.length===0,errors};
  }

  return Object.freeze({
    version:'1.0.0',
    create,
    validate,
    digest
  });
});
