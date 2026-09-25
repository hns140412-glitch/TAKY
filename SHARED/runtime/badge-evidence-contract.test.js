'use strict';
const assert=require('node:assert/strict');
const E=require('./badge-evidence-contract.js');
assert.equal(E.VERSION,'TAKY_BADGE_EXPLICIT_EVIDENCE_V1');

const err=E.verify('ERROR_DISCOVERY',{
  explicitChildAction:true,
  evidenceRef:'evt:1',
  sourceContractId:'TAKY_CHILD_SELF_CORRECTION_V1',
  errorMarkedByChild:true,
  beforeArtifactRef:'a:before',
  afterArtifactRef:'a:after'
});
assert.equal(err.family,'ERROR_DISCOVERY');

assert.throws(()=>E.verify('DEEP_THINKING',{
  explicitChildAction:true,
  evidenceRef:'evt:2',
  sourceContractId:'TAKY_CHILD_REFLECTION_ARTIFACT_V1',
  childChoseToReflect:true,
  reflectionArtifactRef:'a:r',
  elapsed_ms:9000
}),/WEAK_PROXY_FORBIDDEN/);

const deep=E.verify('DEEP_THINKING',{
  explicitChildAction:true,
  evidenceRef:'evt:3',
  sourceContractId:'TAKY_CHILD_REFLECTION_ARTIFACT_V1',
  childChoseToReflect:true,
  reflectionArtifactRef:'a:r'
});
assert.equal(deep.inference_allowed,false);

const special=E.verify('SPECIAL_BEHAVIOR',{
  explicitChildAction:true,
  evidenceRef:'evt:4',
  sourceContractId:'TAKY_DECLARED_SPECIAL_ACTION_V1',
  declaredByFeature:true,
  featureContractId:'FEATURE_X_V1',
  behaviorCode:'SPECIAL_X'
},{allowedFeatureContracts:['FEATURE_X_V1'],allowedSpecialBehaviorCodes:['SPECIAL_X']});
assert.equal(special.behavior_code,'SPECIAL_X');

console.log('TAKY_BADGE_EXPLICIT_EVIDENCE_ALIAS_PASS');
