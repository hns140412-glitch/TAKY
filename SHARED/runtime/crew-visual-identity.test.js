'use strict';
const assert=require('node:assert/strict');
const V=require('./crew-visual-identity.js');
for(const [id,name,species] of [
 ['crew.core.dubi','두비','dog-like'],['crew.core.lori','로리','rabbit'],['crew.core.ink','잉크','dark fox'],
 ['crew.core.nova','노바','otter/ferret-like'],['crew.core.take','테이크','panda'],['crew.core.zero','제로','penguin']
]){
 const x=V.identity(id);assert.equal(x.canonical_name,name);assert.equal(x.species,species);assert.equal(x.golden_asset_status,'OPEN_EXACT_ASSET_MAPPING');
 const p=V.project(id,{theme_id:'JUNGLE'});assert.equal(p.ok,true);assert.equal(p.projection.identity_body_stable,true);assert.equal(p.projection.power_effect,null);
}
assert.equal(V.identity('crew.unknown'),null);
assert.equal(V.assertNoIdentityMutation({theme_id:'X'}),true);
assert.equal(V.assertNoIdentityMutation({species:'bear'}),false);
console.log('TAKY_CREW_VISUAL_IDENTITY_V1_PASS');