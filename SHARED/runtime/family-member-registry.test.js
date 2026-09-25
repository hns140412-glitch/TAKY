'use strict';
const assert=require('node:assert/strict');
const R=require('./family-member-registry.js');

const registry=R.normalizeRegistry({
 family_id:'F1',
 members:[
  {family_id:'F1',member_id:'P1',role:'PARENT',display_name:'엄마'},
  {family_id:'F1',member_id:'C1',role:'CHILD',profile:{display_name:'아이1',avatar_ref:'drive:avatar:c1'}},
  {family_id:'F1',member_id:'C2',role:'CHILD',display_name:'아이2'}
 ]
});
assert.equal(registry.members.length,3);
assert.equal(R.children(registry).length,2);
const selected=R.selectActiveChild(registry,'C2');
assert.equal(selected.ok,true);
assert.equal(selected.registry.active_child_id,'C2');
assert.equal(R.memberProfile(registry,'C1').display_name,'아이1');
assert.deepEqual(R.minimalProjection(registry.members[1]),{member_id:'C1',display_name:'아이1',avatar_ref:'drive:avatar:c1'});
assert.equal(R.validateMember({family_id:'F1',member_id:'C1',role:'CHILD'}).ok,true);
assert.equal(R.validateMember({family_id:'F1',member_id:'C1',role:'OTHER'}).ok,false);
console.log('TAKY_FAMILY_MEMBER_REGISTRY_V1_PASS');
