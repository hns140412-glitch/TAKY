/* TAKY Explorer Crew shared content-owner adapter (NOT an age gate).
   MAIN_CREW and PLAY_CAMP are source owners, not learner grade buckets.
   Historic E5_6 is the immutable stored key of the existing 144 source lines.
   It must never be interpreted as the school grade of the child speaking. */
(function(root,factory){
 const api=factory();
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else if(root)root.TakyExplorerCrewContentOwner=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const VERSION='TAKY_EXPLORER_CREW_CONTENT_OWNER_V1';
 const legacyMainSourceKey='E5_6';
 const APPS=new Set(['READY_SET','HIDE_SEEK','SNAP_POP','PLAY_CAMP']);
 function create(personality,{app_id}={}){
  if(!personality?.resolve)throw new Error('CANONICAL_PERSONALITY_REQUIRED');
  if(!APPS.has(app_id))throw new Error('UNRECOGNIZED_APP_OWNER');
  const scope=app_id==='PLAY_CAMP'?'PLAY_CAMP':'MAIN_CREW';
  function resolve(args={}){
   if(args.app_id&&args.app_id!==app_id)
    return Object.freeze({text:null,reason:'APP_CONTENT_OWNER_MISMATCH'});
   // The legacy authority uses the source key as a stageBand selector.
   // Preserve all real learner metadata OUTSIDE this source lookup.
   // No first-grade/sixth-grade/unknown-age routing or child identity inference.
   const result=personality.resolve({
    ...args,app_id,
    ...(scope==='MAIN_CREW'?
      {school_stage:legacyMainSourceKey,presentation_band:'UPPER_PRIMARY'}:
      {presentation_band:'EARLY_EXPLORER'})
   });
   if(!result||typeof result!=='object')return Object.freeze({text:null,reason:'CANONICAL_SCRIPT_INVALID'});
   return Object.freeze({...result,content_scope:scope,stored_script_key:scope==='MAIN_CREW'?legacyMainSourceKey:'PLAY_CAMP'});
  }
  return Object.freeze({VERSION,scope,resolve});
 }
 return Object.freeze({VERSION,legacyMainSourceKey,create});
});