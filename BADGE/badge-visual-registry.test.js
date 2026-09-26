'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const api=require('./badge-visual-registry.js');
const registry=JSON.parse(fs.readFileSync(path.join(__dirname,'badge-visual-registry-working.json'),'utf8'));

assert.equal(registry.items.length,60);
assert.equal(registry.status,'WORKING_DRAFT_VISUAL_REGISTRY_NOT_ACTIVE');
assert.equal(registry.visual_contract.reacquisition_stars.meaning,'APPROVED_REAWARD_COUNT_WITHIN_CURRENT_TIER');
assert.equal(registry.visual_contract.reacquisition_stars.first_award,'ACTIVATES_BADGE_WITH_ZERO_STARS');
assert.equal(registry.visual_contract.reacquisition_stars.tier_up_at,5);
assert.equal(registry.visual_contract.reacquisition_stars.telemetry_repeat_is_not_reaward,true);
assert.equal(registry.visual_contract.reacquisition_stars.gem_currency,false);
assert.equal(registry.visual_contract.character_layer.source,'CHILD_PROFILE');
assert.equal(registry.visual_contract.ownership_presentation.unearned,'SILHOUETTE');
assert.equal(registry.visual_contract.border_fx,'SOFT_RADIAL_GRADIENT_FADE');
assert.equal(registry.items.every(x=>x.active===false),true);
assert.equal(registry.items.every(x=>x.asset_state==='UNBOUND'),true);
assert.equal(registry.items.every(x=>x.renderer_binding===false),true);
assert.equal(api.validateRegistry(registry).ok,true);
assert.equal(api.resolveApproved(registry,'BDG-DRAFT-001').ok,false);

const forged=structuredClone(registry.items[0]);
forged.active=true;
forged.renderer_binding=true;
assert.equal(api.validateEntry(forged).ok,false);

const approved=structuredClone(registry.items[0]);
approved.active=true;
approved.renderer_binding=true;
approved.asset_state='APPROVED_RUNTIME_ASSET';
approved.approval_status='APPROVED_RUNTIME_ASSET';
approved.asset_path='assets/badges/approved/bdg-001.webp';
approved.asset_version='v1';
approved.approval_evidence_refs=['USER_APPROVAL_EVIDENCE'];
assert.equal(api.validateEntry(approved).ok,true);

console.log('badge visual registry guards: PASS');
