(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyBadgeSourceEvidence=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='TAKY_BADGE_SOURCE_EVIDENCE_V1';
  const IDS=Object.freeze({
    SELF_CORRECTION:'TAKY_CHILD_SELF_CORRECTION_V1',
    REFLECTION_ARTIFACT:'TAKY_CHILD_REFLECTION_ARTIFACT_V1',
    DECLARED_SPECIAL_ACTION:'TAKY_DECLARED_SPECIAL_ACTION_V1'
  });
  const clean=v=>String(v??'').trim();

  function common(input={},sourceContractId){
    const member_id=clean(input.member_id);
    const evidence_ref=clean(input.evidence_ref||input.evidenceRef);
    const occurred_at=input.occurred_at||new Date().toISOString();
    if(!member_id)throw new Error('BADGE_SOURCE_MEMBER_ID_REQUIRED');
    if(!evidence_ref)throw new Error('BADGE_SOURCE_EVIDENCE_REF_REQUIRED');
    if(input.explicit_child_action!==true&&input.explicitChildAction!==true)
      throw new Error('BADGE_SOURCE_EXPLICIT_CHILD_ACTION_REQUIRED');
    return {
      badge_source_evidence_contract:VERSION,
      source_contract_id:sourceContractId,
      member_id,
      actor_member_id:clean(input.actor_member_id)||member_id,
      evidence_ref,
      occurred_at,
      explicit_child_action:true,
      inference_allowed:false
    };
  }

  function selfCorrection(input={}){
    const base=common(input,IDS.SELF_CORRECTION);
    const before=clean(input.before_artifact_ref||input.beforeArtifactRef);
    const after=clean(input.after_artifact_ref||input.afterArtifactRef);
    if(input.error_marked_by_child!==true&&input.errorMarkedByChild!==true)
      throw new Error('SELF_CORRECTION_CHILD_MARK_REQUIRED');
    if(!before||!after)throw new Error('SELF_CORRECTION_ARTIFACTS_REQUIRED');
    if(before===after)throw new Error('SELF_CORRECTION_ARTIFACTS_MUST_DIFFER');
    return Object.freeze({
      ...base,
      error_marked_by_child:true,
      before_artifact_ref:before,
      after_artifact_ref:after
    });
  }

  function reflectionArtifact(input={}){
    const base=common(input,IDS.REFLECTION_ARTIFACT);
    const artifact=clean(input.reflection_artifact_ref||input.reflectionArtifactRef);
    if(input.child_chose_to_reflect!==true&&input.childChoseToReflect!==true)
      throw new Error('REFLECTION_CHILD_CHOICE_REQUIRED');
    if(!artifact)throw new Error('REFLECTION_ARTIFACT_REQUIRED');
    return Object.freeze({
      ...base,
      child_chose_to_reflect:true,
      reflection_artifact_ref:artifact
    });
  }

  function declaredSpecialAction(input={}){
    const base=common(input,IDS.DECLARED_SPECIAL_ACTION);
    const feature=clean(input.feature_contract_id||input.featureContractId);
    const code=clean(input.behavior_code||input.behaviorCode);
    if(input.declared_by_feature!==true&&input.declaredByFeature!==true)
      throw new Error('SPECIAL_ACTION_FEATURE_DECLARATION_REQUIRED');
    if(!feature)throw new Error('SPECIAL_ACTION_FEATURE_CONTRACT_REQUIRED');
    if(!code)throw new Error('SPECIAL_ACTION_BEHAVIOR_CODE_REQUIRED');
    return Object.freeze({
      ...base,
      declared_by_feature:true,
      feature_contract_id:feature,
      behavior_code:code
    });
  }

  return Object.freeze({VERSION,IDS,selfCorrection,reflectionArtifact,declaredSpecialAction});
});
