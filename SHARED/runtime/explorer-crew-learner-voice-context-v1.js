/* Voice content selection is owned by app and character, NOT school grade.
   Learner information is optional metadata for non-voice learning engines. */
(function(root,factory){
 const api=factory();
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else if(root)root.TakyExplorerCrewLearnerVoiceContext=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const VALID=new Set(['E1','E2','E3','E4','E5','E6','M1','M2','M3']);
 const APPS=new Set(['READY_SET','HIDE_SEEK','SNAP_POP']);
 const safe=value=>typeof value==='string'&&value.trim()?value.trim():null;
 function resolve({app_id,identity=null,explicitContext=null,identityReady=false}={}){
  if(!APPS.has(app_id))return {ok:false,status:'UNKNOWN_APP_OWNER'};
  let stage=null,source='NOT_SUPPLIED',learnerId=null,contextConflict=false;
  if(app_id==='READY_SET'&&identityReady===true&&identity){
   stage=safe(identity.schoolStage);source='READY_IDENTITY_V1';
   learnerId=safe(identity.memberId)||safe(identity.userId);
  }else if(explicitContext?.source==='TAKY_LEARNING_ENGINE_VERIFIED'&&safe(explicitContext.learner_id)){
   stage=safe(explicitContext.school_stage);source='LEARNING_ENGINE_VERIFIED';
   learnerId=safe(explicitContext.learner_id);
  }else if(['HIDE_SEEK','SNAP_POP'].includes(app_id)&&
   explicitContext?.source==='APP_BOUND_NAVIGATION_CONTEXT'&&
   safe(explicitContext.child_id)&&safe(explicitContext.session_id)&&safe(explicitContext.task_id)){
   stage=safe(explicitContext.school_stage);source='APP_BOUND_NAVIGATION_CONTEXT';
   learnerId=safe(explicitContext.child_id);
   const grade=safe(explicitContext.school_grade)?.toUpperCase();
   if(stage&&grade&&grade!==stage.toUpperCase()&&grade!==stage.toUpperCase().replace(/^E/,'')&&
     grade!=='GRADE_'+stage.toUpperCase().replace(/^E/,''))
    contextConflict=true;
  }
  // No unknown/invalid grade is rewritten to E5, and no grade excludes audio.
  const metadataStage=stage&&VALID.has(stage.toUpperCase())?stage.toUpperCase():null;
  return Object.freeze({ok:true,status:'VOICE_OWNER_NOT_GRADE_GATED',
   source,learner_id:learnerId,school_stage:metadataStage,
   learner_stage_metadata_conflict:contextConflict,
   presentation_band:null,voice_content_scope:'MAIN_CREW'});
 }
 return Object.freeze({VALID,resolve});
});