(function(root,factory){
 const api=factory(); if(typeof module==='object'&&module.exports)module.exports=api; else root.TakyBadgeExplicitEvidence=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const VERSION='TAKY_BADGE_EXPLICIT_EVIDENCE_V1';
 const STRONG=new Set(['ERROR_DISCOVERY','DEEP_THINKING','SPECIAL_BEHAVIOR']);
 const WEAK=new Set(['elapsedMs','elapsed_ms','idleMs','idle_ms','silenceMs','silence_ms','attemptCount','attempt_count','retryCount','retry_count','editCount','edit_count','score','confidence','aiInference','ai_inference','modelInference','model_inference']);
 const clean=v=>String(v??'').trim();
 function hasWeak(v,d=0){if(d>4||!v||typeof v!=='object')return false;if(Array.isArray(v))return v.some(x=>hasWeak(x,d+1));for(const [k,x] of Object.entries(v)){if(WEAK.has(k))return true;if(hasWeak(x,d+1))return true}return false}
 function reqTrue(o,k,e){if(o?.[k]!==true)throw new Error(e)}
 function reqStr(o,k,e){const v=clean(o?.[k]);if(!v)throw new Error(e);return v}
 function base(f,e){if(!STRONG.has(f))throw new Error('BADGE_EVIDENCE_FAMILY_UNSUPPORTED');if(!e||typeof e!=='object'||Array.isArray(e))throw new Error('BADGE_EVIDENCE_OBJECT_REQUIRED');if(hasWeak(e))throw new Error('BADGE_EVIDENCE_WEAK_PROXY_FORBIDDEN');reqTrue(e,'explicitChildAction','BADGE_EVIDENCE_EXPLICIT_CHILD_ACTION_REQUIRED');return {contract_version:VERSION,family:f,evidence_ref:reqStr(e,'evidenceRef','BADGE_EVIDENCE_REF_REQUIRED'),source_contract_id:reqStr(e,'sourceContractId','BADGE_EVIDENCE_SOURCE_CONTRACT_REQUIRED'),explicit_child_action:true,inference_allowed:false,elapsed_time_evidence_allowed:false,score_evidence_allowed:false}}
 function verify(f,e,opt={}){
   const b=base(f,e);
   if(f==='ERROR_DISCOVERY'){if(b.source_contract_id!=='TAKY_CHILD_SELF_CORRECTION_V1')throw new Error('BADGE_ERROR_DISCOVERY_SOURCE_CONTRACT_INVALID');reqTrue(e,'errorMarkedByChild','BADGE_ERROR_DISCOVERY_CHILD_MARK_REQUIRED');return Object.freeze({...b,before_artifact_ref:reqStr(e,'beforeArtifactRef','BADGE_ERROR_DISCOVERY_BEFORE_REQUIRED'),after_artifact_ref:reqStr(e,'afterArtifactRef','BADGE_ERROR_DISCOVERY_AFTER_REQUIRED'),error_marked_by_child:true})}
   if(f==='DEEP_THINKING'){if(b.source_contract_id!=='TAKY_CHILD_REFLECTION_ARTIFACT_V1')throw new Error('BADGE_DEEP_THINKING_SOURCE_CONTRACT_INVALID');reqTrue(e,'childChoseToReflect','BADGE_DEEP_THINKING_EXPLICIT_REFLECTION_REQUIRED');return Object.freeze({...b,reflection_artifact_ref:reqStr(e,'reflectionArtifactRef','BADGE_DEEP_THINKING_ARTIFACT_REQUIRED'),child_chose_to_reflect:true})}
   if(f==='SPECIAL_BEHAVIOR'){if(b.source_contract_id!=='TAKY_DECLARED_SPECIAL_ACTION_V1')throw new Error('BADGE_SPECIAL_BEHAVIOR_SOURCE_CONTRACT_INVALID');reqTrue(e,'declaredByFeature','BADGE_SPECIAL_BEHAVIOR_FEATURE_DECLARATION_REQUIRED');const fc=reqStr(e,'featureContractId','BADGE_SPECIAL_BEHAVIOR_FEATURE_CONTRACT_REQUIRED'),bc=reqStr(e,'behaviorCode','BADGE_SPECIAL_BEHAVIOR_CODE_REQUIRED');if(!(opt.allowedFeatureContracts||[]).includes(fc))throw new Error('BADGE_SPECIAL_BEHAVIOR_FEATURE_NOT_ALLOWLISTED');if(!(opt.allowedSpecialBehaviorCodes||[]).includes(bc))throw new Error('BADGE_SPECIAL_BEHAVIOR_CODE_NOT_ALLOWLISTED');return Object.freeze({...b,feature_contract_id:fc,behavior_code:bc,declared_by_feature:true})}
 }
 return Object.freeze({VERSION,STRONG_FAMILIES:Object.freeze([...STRONG]),WEAK_PROXY_KEYS:Object.freeze([...WEAK]),verify,hasWeak});
});