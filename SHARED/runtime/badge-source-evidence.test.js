'use strict';
const assert=require('node:assert/strict');
const S=require('./badge-source-evidence.js');
const V=require('./badge-explicit-evidence.js');

const correction=S.selfCorrection({
  member_id:'C1',
  evidence_ref:'EV1',
  explicit_child_action:true,
  error_marked_by_child:true,
  before_artifact_ref:'draft:v1',
  after_artifact_ref:'draft:v2'
});
assert.equal(correction.source_contract_id,'TAKY_CHILD_SELF_CORRECTION_V1');
assert.equal(V.verify('ERROR_DISCOVERY',{
  evidenceRef:correction.evidence_ref,
  sourceContractId:correction.source_contract_id,
  explicitChildAction:correction.explicit_child_action,
  errorMarkedByChild:correction.error_marked_by_child,
  beforeArtifactRef:correction.before_artifact_ref,
  afterArtifactRef:correction.after_artifact_ref
}).family,'ERROR_DISCOVERY');

const reflection=S.reflectionArtifact({
  member_id:'C1',
  evidence_ref:'EV2',
  explicit_child_action:true,
  child_chose_to_reflect:true,
  reflection_artifact_ref:'reflection:R1'
});
assert.equal(V.verify('DEEP_THINKING',{
  evidenceRef:reflection.evidence_ref,
  sourceContractId:reflection.source_contract_id,
  explicitChildAction:reflection.explicit_child_action,
  childChoseToReflect:reflection.child_chose_to_reflect,
  reflectionArtifactRef:reflection.reflection_artifact_ref
}).family,'DEEP_THINKING');

const special=S.declaredSpecialAction({
  member_id:'C1',
  evidence_ref:'EV3',
  explicit_child_action:true,
  declared_by_feature:true,
  feature_contract_id:'FEATURE_SPECIAL_EXPLORATION_V1',
  behavior_code:'CHILD_SELECTED_OPTIONAL_SPECIAL_EXPLORATION'
});
assert.equal(V.verify('SPECIAL_BEHAVIOR',{
  evidenceRef:special.evidence_ref,
  sourceContractId:special.source_contract_id,
  explicitChildAction:special.explicit_child_action,
  declaredByFeature:special.declared_by_feature,
  featureContractId:special.feature_contract_id,
  behaviorCode:special.behavior_code
},{
  allowedFeatureContracts:['FEATURE_SPECIAL_EXPLORATION_V1'],
  allowedSpecialBehaviorCodes:['CHILD_SELECTED_OPTIONAL_SPECIAL_EXPLORATION']
}).family,'SPECIAL_BEHAVIOR');

assert.throws(()=>S.selfCorrection({member_id:'C1',evidence_ref:'EV4'}),/EXPLICIT_CHILD_ACTION/);
assert.throws(()=>S.reflectionArtifact({member_id:'C1',evidence_ref:'EV5',explicit_child_action:true}),/REFLECTION_CHILD_CHOICE/);

console.log('TAKY_BADGE_SOURCE_EVIDENCE_V1_PASS');
