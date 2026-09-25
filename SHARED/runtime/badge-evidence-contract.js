(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyBadgeEvidence=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_BADGE_EXPLICIT_EVIDENCE_V1';
  const STRONG_FAMILIES=new Set(['ERROR_DISCOVERY','DEEP_THINKING','SPECIAL_BEHAVIOR']);
  const WEAK_PROXY_KEYS=new Set([
    'elapsedMs','elapsed_ms','idleMs','idle_ms','silenceMs','silence_ms',
    'attemptCount','attempt_count','emptyAttemptCount','empty_attempt_count',
    'retryCount','retry_count','editCount','edit_count','score','confidence',
    'aiInference','ai_inference','modelInference','model_inference'
  ]);
  const clean=(v,max=180)=>typeof v==='string'?v.trim().slice(0,max):'';
  function hasWeakProxy(value,depth=0){
    if(depth>4||value===null||typeof value!=='object')return false;
    if(Array.isArray(value))return value.some(x=>hasWeakProxy(x,depth+1));
    for(const [key,item] of Object.entries(value)){
      if(WEAK_PROXY_KEYS.has(key))return true;
      if(hasWeakProxy(item,depth+1))return true;
    }
    return false;
  }
  function base(family,evidence={}){
    if(!STRONG_FAMILIES.has(family))throw new Error('BADGE_EVIDENCE_FAMILY_UNSUPPORTED');
    if(!evidence||typeof evidence!=='object'||Array.isArray(evidence))throw new Error('BADGE_EVIDENCE_OBJECT_REQUIRED');
    if(hasWeakProxy(evidence))throw new Error('BADGE_EVIDENCE_WEAK_PROXY_FORBIDDEN');
    if(evidence.explicit_child_action!==true&&evidence.explicitChildAction!==true)throw new Error('BADGE_EVIDENCE_EXPLICIT_CHILD_ACTION_REQUIRED');
    const evidence_ref=clean(evidence.evidence_ref||evidence.evidenceRef);
    const source_contract_id=clean(evidence.source_contract_id||evidence.sourceContractId);
    if(!evidence_ref)throw new Error('BADGE_EVIDENCE_REF_REQUIRED');
    if(!source_contract_id)throw new Error('BADGE_EVIDENCE_SOURCE_CONTRACT_REQUIRED');
    return {
      badge_evidence_contract:VERSION,
      family,
      evidence_ref,
      source_contract_id,
      explicit_child_action:true,
      inference_allowed:false,
      elapsed_time_evidence_allowed:false,
      score_evidence_allowed:false
    };
  }
  function verifyErrorDiscovery(e={}){
    const out=base('ERROR_DISCOVERY',e);
    const allowed=new Set(['TAKY_CHILD_SELF_CORRECTION_V1','SNAP_POP_CHILD_SELF_CORRECTION_V1']);
    if(!allowed.has(out.source_contract_id))throw new Error('BADGE_ERROR_DISCOVERY_SOURCE_CONTRACT_INVALID');
    if(e.error_marked_by_child!==true&&e.errorMarkedByChild!==true)throw new Error('BADGE_ERROR_DISCOVERY_CHILD_MARK_REQUIRED');
    const before_ref=clean(e.before_artifact_ref||e.beforeArtifactRef),after_ref=clean(e.after_artifact_ref||e.afterArtifactRef);
    if(!before_ref)throw new Error('BADGE_ERROR_DISCOVERY_BEFORE_REQUIRED');
    if(!after_ref)throw new Error('BADGE_ERROR_DISCOVERY_AFTER_REQUIRED');
    return Object.freeze({...out,before_artifact_ref:before_ref,after_artifact_ref:after_ref,error_marked_by_child:true});
  }
  function verifyDeepThinking(e={}){
    const out=base('DEEP_THINKING',e);
    const allowed=new Set(['TAKY_CHILD_REFLECTION_ARTIFACT_V1','SNAP_POP_CHILD_REFLECTION_ARTIFACT_V1']);
    if(!allowed.has(out.source_contract_id))throw new Error('BADGE_DEEP_THINKING_SOURCE_CONTRACT_INVALID');
    if(e.child_chose_to_reflect!==true&&e.childChoseToReflect!==true)throw new Error('BADGE_DEEP_THINKING_EXPLICIT_REFLECTION_REQUIRED');
    const ref=clean(e.reflection_artifact_ref||e.reflectionArtifactRef);
    if(!ref)throw new Error('BADGE_DEEP_THINKING_ARTIFACT_REQUIRED');
    return Object.freeze({...out,reflection_artifact_ref:ref,child_chose_to_reflect:true});
  }
  function verifySpecialBehavior(e={},options={}){
    const out=base('SPECIAL_BEHAVIOR',e);
    const allowedContracts=new Set(['TAKY_DECLARED_SPECIAL_ACTION_V1','SNAP_POP_DECLARED_SPECIAL_ACTION_V1']);
    if(!allowedContracts.has(out.source_contract_id))throw new Error('BADGE_SPECIAL_BEHAVIOR_SOURCE_CONTRACT_INVALID');
    if(e.declared_by_feature!==true&&e.declaredByFeature!==true)throw new Error('BADGE_SPECIAL_BEHAVIOR_FEATURE_DECLARATION_REQUIRED');
    const feature_contract_id=clean(e.feature_contract_id||e.featureContractId);
    const behavior_code=clean(e.behavior_code||e.behaviorCode);
    if(!feature_contract_id)throw new Error('BADGE_SPECIAL_BEHAVIOR_FEATURE_CONTRACT_REQUIRED');
    if(!behavior_code)throw new Error('BADGE_SPECIAL_BEHAVIOR_CODE_REQUIRED');
    const fc=Array.isArray(options.allowed_feature_contracts)?options.allowed_feature_contracts:(options.allowedFeatureContracts||[]);
    const bc=Array.isArray(options.allowed_behavior_codes)?options.allowed_behavior_codes:(options.allowedSpecialBehaviorCodes||[]);
    if(!fc.includes(feature_contract_id))throw new Error('BADGE_SPECIAL_BEHAVIOR_FEATURE_NOT_ALLOWLISTED');
    if(!bc.includes(behavior_code))throw new Error('BADGE_SPECIAL_BEHAVIOR_CODE_NOT_ALLOWLISTED');
    return Object.freeze({...out,feature_contract_id,behavior_code,declared_by_feature:true});
  }
  function verify(family,evidence,options={}){
    if(family==='ERROR_DISCOVERY')return verifyErrorDiscovery(evidence);
    if(family==='DEEP_THINKING')return verifyDeepThinking(evidence);
    if(family==='SPECIAL_BEHAVIOR')return verifySpecialBehavior(evidence,options);
    throw new Error('BADGE_EVIDENCE_FAMILY_UNSUPPORTED');
  }
  return Object.freeze({VERSION,families:Object.freeze([...STRONG_FAMILIES]),weakProxyKeys:Object.freeze([...WEAK_PROXY_KEYS]),verify,hasWeakProxy});
});
