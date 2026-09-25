'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const Behavior=require('./badge-behavior-observation.js');
const Evidence=require('./badge-explicit-evidence.js');
const Guard=require('./badge-catalog-guard.js');
const Theme=require('./badge-theme-expression.js');

const recovered=JSON.parse(fs.readFileSync(path.join(__dirname,'../../EXPLORATION/recovery/snap-2026-09-21/badge-catalog-working.json'),'utf8'));
assert.equal(recovered.status,'WORKING_DRAFT_NOT_ACTIVE');
assert.equal(recovered.items.length,60);
assert.equal(recovered.items.every(x=>x.active===false&&x.status==='WORKING_DRAFT'),true);
assert.equal(Guard.validateCatalog(recovered),true);
assert.equal(Guard.activeItems(recovered).length,0);

const corrupted=structuredClone(recovered);
corrupted.items[0].active=true;
assert.throws(()=>Guard.validateCatalog(corrupted),/BADGE_WORKING_DRAFT_ACTIVATION_FORBIDDEN/);

const obs=Behavior.normalize({
 event_id:'E1',family:'HELP_REQUEST',member_id:'C1',source_app:'hide-seek',
 payload:{explicit:true}
});
assert.equal(obs.disposition,'OBSERVATION_ONLY');
assert.equal(obs.badge_award_authorized,false);
assert.equal(obs.child_ability_inference_allowed,false);
assert.throws(()=>Behavior.normalize({event_id:'E2',family:'FOCUS',payload:{ability:'high'}}),/BADGE_BEHAVIOR_LABELING_FORBIDDEN/);

assert.throws(()=>Evidence.verify('DEEP_THINKING',{
 explicitChildAction:true,evidenceRef:'R1',sourceContractId:'TAKY_CHILD_REFLECTION_ARTIFACT_V1',
 childChoseToReflect:true,reflectionArtifactRef:'A1',elapsedMs:90000
}),/BADGE_EVIDENCE_WEAK_PROXY_FORBIDDEN/);

const deep=Evidence.verify('DEEP_THINKING',{
 explicitChildAction:true,evidenceRef:'R2',sourceContractId:'TAKY_CHILD_REFLECTION_ARTIFACT_V1',
 childChoseToReflect:true,reflectionArtifactRef:'A2'
});
assert.equal(deep.inference_allowed,false);
assert.equal(deep.elapsed_time_evidence_allowed,false);

const error=Evidence.verify('ERROR_DISCOVERY',{
 explicitChildAction:true,evidenceRef:'R3',sourceContractId:'TAKY_CHILD_SELF_CORRECTION_V1',
 errorMarkedByChild:true,beforeArtifactRef:'BEFORE',afterArtifactRef:'AFTER'
});
assert.equal(error.error_marked_by_child,true);

assert.throws(()=>Theme.normalize({theme_id:'T1',identity:{name:'x'}}),/BADGE_THEME_EXPRESSION_AUTHORITY_VIOLATION/);
const theme=Theme.normalize({theme_id:'T1',asset_state:'UNRESOLVED',expression_cue:'정글 탐험'});
assert.equal(theme.cosmetic_only,true);
assert.equal(theme.identity_mutation_allowed,false);
assert.equal(theme.power_mutation_allowed,false);
assert.equal(theme.economy_mutation_allowed,false);

console.log('TAKY_BADGE_RECOVERY_GUARDS_PASS');
