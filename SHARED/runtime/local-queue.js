(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyLocalQueue=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const ACTIVE=Object.freeze(['PENDING','RETRY']);
  const TERMINAL=Object.freeze(['ACKED','DEAD_LETTER','SUPERSEDED']);

  function nowIso(now){
    return (now instanceof Date?now:new Date(now??Date.now())).toISOString();
  }

  function clone(value){
    if(typeof structuredClone==='function') return structuredClone(value);
    return value===undefined?undefined:JSON.parse(JSON.stringify(value));
  }

  function freeze(value){
    if(!value||typeof value!=='object'||Object.isFrozen(value)) return value;
    Object.freeze(value);
    for(const key of Object.keys(value)) freeze(value[key]);
    return value;
  }

  function create(entry={}){
    if(!entry||typeof entry!=='object'||Array.isArray(entry)) throw new TypeError('QUEUE_ENTRY_NOT_OBJECT');
    const event_id=String(entry.event_id||'').trim();
    const idempotency_key=String(entry.idempotency_key||event_id).trim();
    if(!event_id) throw new TypeError('EVENT_ID_REQUIRED');
    if(!idempotency_key) throw new TypeError('IDEMPOTENCY_KEY_REQUIRED');
    const created_at=entry.created_at||nowIso();
    return freeze({
      queue_version:1,
      event_id,
      idempotency_key,
      status:'PENDING',
      attempts:0,
      max_attempts:Number.isInteger(entry.max_attempts)&&entry.max_attempts>0?entry.max_attempts:5,
      next_retry_at:null,
      last_error:null,
      ack_token:null,
      remote_version:null,
      created_at,
      updated_at:created_at,
      metadata:clone(entry.metadata??null)
    });
  }

  function validate(row){
    const errors=[];
    if(!row||typeof row!=='object'||Array.isArray(row)) return {ok:false,errors:['QUEUE_ENTRY_NOT_OBJECT']};
    if(Number(row.queue_version)!==1) errors.push('INVALID_QUEUE_VERSION');
    for(const key of ['event_id','idempotency_key','status','created_at','updated_at']){
      if(typeof row[key]!=='string'||!row[key].trim()) errors.push('MISSING_'+key.toUpperCase());
    }
    if(!Number.isInteger(row.attempts)||row.attempts<0) errors.push('INVALID_ATTEMPTS');
    if(!Number.isInteger(row.max_attempts)||row.max_attempts<1) errors.push('INVALID_MAX_ATTEMPTS');
    if(![...ACTIVE,...TERMINAL,'IN_FLIGHT'].includes(row.status)) errors.push('INVALID_STATUS');
    return {ok:errors.length===0,errors};
  }

  function retryDelayMs(attempt,{base_ms=1000,max_ms=3600000}={}){
    const n=Math.max(1,Number(attempt)||1);
    return Math.min(max_ms,base_ms*(2**Math.min(n-1,16)));
  }

  function canAttempt(row,now=Date.now()){
    if(!row||!ACTIVE.includes(row.status)) return false;
    if(row.status==='PENDING'||!row.next_retry_at) return true;
    return Date.parse(row.next_retry_at)<=new Date(now).getTime();
  }

  function markInFlight(row,now=Date.now()){
    if(!canAttempt(row,now)) return {ok:false,reason:'NOT_ATTEMPTABLE',row};
    return {ok:true,row:freeze({...clone(row),status:'IN_FLIGHT',updated_at:nowIso(now)})};
  }

  function markRetry(row,error,now=Date.now(),policy={}){
    if(!row||!['IN_FLIGHT','PENDING','RETRY'].includes(row.status)) return {ok:false,reason:'INVALID_RETRY_STATE',row};
    const attempts=(row.attempts||0)+1;
    const updated_at=nowIso(now);
    if(attempts>=row.max_attempts){
      return {ok:true,row:freeze({...clone(row),status:'DEAD_LETTER',attempts,next_retry_at:null,last_error:String(error||'RETRY_EXHAUSTED'),updated_at})};
    }
    const delay=retryDelayMs(attempts,policy);
    return {ok:true,row:freeze({...clone(row),status:'RETRY',attempts,next_retry_at:new Date(new Date(now).getTime()+delay).toISOString(),last_error:String(error||'RETRY'),updated_at})};
  }

  function markAcked(row,{ack_token=null,remote_version=null,now=Date.now()}={}){
    if(!row||!['IN_FLIGHT','PENDING','RETRY'].includes(row.status)) return {ok:false,reason:'INVALID_ACK_STATE',row};
    return {ok:true,row:freeze({...clone(row),status:'ACKED',ack_token,remote_version,next_retry_at:null,last_error:null,updated_at:nowIso(now),acked_at:nowIso(now)})};
  }

  function markSuperseded(row,now=Date.now()){
    if(!row||TERMINAL.includes(row.status)) return {ok:false,reason:'INVALID_SUPERSEDE_STATE',row};
    return {ok:true,row:freeze({...clone(row),status:'SUPERSEDED',next_retry_at:null,updated_at:nowIso(now)})};
  }

  return Object.freeze({
    version:'1.0.0',
    activeStates:ACTIVE,
    terminalStates:TERMINAL,
    create,
    validate,
    retryDelayMs,
    canAttempt,
    markInFlight,
    markRetry,
    markAcked,
    markSuperseded
  });
});
