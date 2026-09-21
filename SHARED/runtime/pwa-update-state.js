(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyPwaUpdateState=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const STATES=Object.freeze([
    'IDLE','UPDATE_DETECTED','DOWNLOADED_WAITING','SAFE_TO_ACTIVATE',
    'ACTIVATING','RESTORING','READY','FAILED'
  ]);

  function fail(state,event,reason){
    return {ok:false,state,error:reason||('INVALID_TRANSITION:'+state+':'+event)};
  }

  function transition(state,event,context={}){
    state=String(state||'IDLE').toUpperCase();
    event=String(event||'').toUpperCase();
    if(!STATES.includes(state)) return fail(state,event,'UNKNOWN_STATE');

    if(event==='FAIL') return {ok:true,state:'FAILED',error:context.error||null};
    if(event==='RESET') return {ok:true,state:'IDLE'};

    switch(state){
      case 'IDLE':
        return event==='DETECT' ? {ok:true,state:'UPDATE_DETECTED'} : fail(state,event);
      case 'UPDATE_DETECTED':
        return event==='DOWNLOAD_COMPLETE' ? {ok:true,state:'DOWNLOADED_WAITING'} : fail(state,event);
      case 'DOWNLOADED_WAITING':
        if(event!=='EVALUATE_SAFE_POINT') return fail(state,event);
        return context.safe_point===true
          ? {ok:true,state:'SAFE_TO_ACTIVATE'}
          : {ok:true,state:'DOWNLOADED_WAITING',waiting_reason:context.reason||'SAFE_POINT_FALSE'};
      case 'SAFE_TO_ACTIVATE':
        return event==='ACTIVATE' ? {ok:true,state:'ACTIVATING'} : fail(state,event);
      case 'ACTIVATING':
        return event==='CONTROLLER_CHANGED' ? {ok:true,state:'RESTORING'} : fail(state,event);
      case 'RESTORING':
        return event==='RESTORE_COMPLETE' ? {ok:true,state:'READY'} : fail(state,event);
      case 'READY':
        return event==='SETTLE' ? {ok:true,state:'IDLE'} : fail(state,event);
      case 'FAILED':
        return event==='RETRY' ? {ok:true,state:'DOWNLOADED_WAITING'} : fail(state,event);
      default:
        return fail(state,event);
    }
  }

  function canActivate(state,context={}){
    if(String(state).toUpperCase()!=='SAFE_TO_ACTIVATE') return false;
    return context.safe_point!==false;
  }

  return Object.freeze({
    version:'1.0.0',
    states:STATES,
    transition,
    canActivate
  });
});
