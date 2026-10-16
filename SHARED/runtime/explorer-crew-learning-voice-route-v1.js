/* TAKY: native learning event -> Explorer Crew voice intent.
 * An event with insufficient evidence never triggers a random line.
 * Silent/duplicate/identity-mismatch output is auditable, not a speaking error. */
(function(root,factory){
 const api=factory();
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else if(root)root.TakyExplorerCrewLearningVoiceRouteV1=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const APP_LABELS=Object.freeze({READY_SET:'ready-set',HIDE_SEEK:'hide-seek',SNAP_POP:'snap-pop'});
 const clean=s=>typeof s==='string'?s.trim():'';
 function route({app_id,event,context,character_id}={}){
  const label=APP_LABELS[app_id];
  if(!label)return {ok:false,status:'UNSUPPORTED_APP'};
  if(!event||event.app!==label||!clean(event.event_id)||!clean(event.type))
   return {ok:false,status:'EVENT_APP_OR_ID_MISMATCH'};
  if(!clean(character_id))return {ok:false,status:'NO_CANONICAL_COMPANION'};
  if(!clean(event.task_id)||!clean(event.session_id)||!clean(event.child_id))
   return {ok:false,status:'EVENT_SESSION_EVIDENCE_MISSING'};
  if(!context||event.task_id!==context.task_id||event.session_id!==context.session_id||
    event.child_id!==context.child_id)return {ok:false,status:'EVENT_CONTEXT_MISMATCH'};
  const payload=event.payload&&typeof event.payload==='object'?event.payload:{};
  let kind=null,autoplay=false;
  if(event.type==='HELP_NEEDED'){
   kind='HINT';
   // Help return-navigation should not start audio which will be cut off.
   autoplay=payload.crew_voice_requested===true && payload.navigation_pending!==true;
  }else if(event.type==='TASK_COMPLETED'){
   kind='FEEDBACK';
   autoplay=payload.child_authored===true&&payload.navigation_pending!==true;
  }else if(event.type==='TASK_STATE_CHANGED'&&app_id==='READY_SET'&&
    payload.next==='COMPLETED'&&payload.provenance==='SESSION_DERIVED'){
   kind='FEEDBACK';autoplay=false; // Ready task system may have its own narration.
  }else if(event.type==='GUIDE_RADIO_REQUEST'&&app_id==='SNAP_POP'){
   return {ok:false,status:'NATIVE_RADIO_ALREADY_OWNS_ASK'};
  }else return {ok:false,status:'EVENT_HAS_NO_VOICE_INTENT'};
  return Object.freeze({ok:true,status:'VERIFIED_NATIVE_EVENT',
   event_type:kind,autoplay,event_id:event.event_id,character_id,
   session_id:event.session_id,task_id:event.task_id,learner_id:event.child_id});
 }
 return Object.freeze({APP_LABELS,route});
});