(function(root,factory){
 const api=factory(); if(typeof module==='object'&&module.exports)module.exports=api; else root.TakyBadgeBehaviorObservation=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const VERSION='TAKY_BADGE_BEHAVIOR_OBSERVATION_V1';
 const FAMILIES=new Set(['SELF_START','TIME_CREATION','EXTRA_TASK','FOCUS','RETURN_RECOVERY','HELP_REQUEST','ERROR_DISCOVERY','RETRY','DEEP_THINKING','ISSUE_DURATION','SELF_EXPLANATION','PLAN_ADAPTATION','SPECIAL_BEHAVIOR','WRITING_EXPLORATION']);
 const FORBIDDEN=new Set(['score','grade','ability','abilityLabel','intelligence','trait','failureLabel','mastery','rank','level','penalty','rewardAmount','power']);
 const clean=v=>String(v??'').trim();
 function hasForbidden(v,d=0){if(d>4||!v||typeof v!=='object')return false;if(Array.isArray(v))return v.some(x=>hasForbidden(x,d+1));for(const [k,x] of Object.entries(v)){if(FORBIDDEN.has(k))return true;if(hasForbidden(x,d+1))return true}return false}
 function normalize(input={}){
   const family=clean(input.family).toUpperCase(); if(!FAMILIES.has(family))throw new Error('BADGE_BEHAVIOR_UNKNOWN_FAMILY');
   const event_id=clean(input.event_id||input.eventId); if(!event_id)throw new Error('BADGE_BEHAVIOR_EVENT_ID_REQUIRED');
   if(hasForbidden(input.payload||{}))throw new Error('BADGE_BEHAVIOR_LABELING_FORBIDDEN');
   return Object.freeze({contract_version:VERSION,event_id,family,member_id:clean(input.member_id)||null,source_app:clean(input.source_app)||null,occurred_at:input.occurred_at||new Date().toISOString(),payload:input.payload&&typeof input.payload==='object'?input.payload:{},disposition:'OBSERVATION_ONLY',badge_award_authorized:false,catalog_activation_allowed:false,child_ability_inference_allowed:false,penalty_allowed:false});
 }
 return Object.freeze({VERSION,FAMILIES:Object.freeze([...FAMILIES]),normalize,hasForbidden});
});