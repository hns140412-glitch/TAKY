'use strict';
const assert=require('node:assert/strict');
const api=require('./badge-visual-renderer.js');

const base={
  draft_id:'BDG-DRAFT-001',
  name:'해뜰락말락',
  visual_id:'BADGE_VISUAL_DRAFT_001',
  active:false,
  renderer_binding:false,
  asset_state:'UNBOUND',
  approval_status:'NOT_APPROVED',
  asset_path:null,
  approval_evidence_refs:[]
};
assert.equal(api.buildRenderModel(base,{grade_stars:1}).ok,false);

const approved={
  ...base,
  active:true,
  renderer_binding:true,
  asset_state:'APPROVED_RUNTIME_ASSET',
  approval_status:'APPROVED_RUNTIME_ASSET',
  asset_path:'assets/badges/approved/bdg-001.webp',
  asset_version:'v1',
  approval_evidence_refs:['USER_APPROVAL_EVIDENCE']
};
const model=api.buildRenderModel(approved,{badge_id:'BDG-DRAFT-001',title:'해뜰락말락',grade_stars:3,repeat_count:99});
assert.equal(model.ok,true);
assert.equal(model.grade_stars,3);
assert.equal(model.semantics.repeat_count_affects_stars,false);
assert.equal(model.semantics.gem_affects_stars,false);
assert.equal(model.semantics.exp_affects_stars,false);
assert.equal(model.semantics.power_effect,false);

assert.equal(api.buildRenderModel(approved,{repeat_count:4}).ok,false);
assert.equal(api.buildRenderModel(approved,{grade_stars:6}).ok,false);

console.log('badge visual renderer guards: PASS');
