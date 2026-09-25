'use strict';
const assert=require('node:assert/strict');
const S=require('./storage-scope.js');

const anon=S.identity({});
assert.equal(anon.mode,'ANONYMOUS_LOCAL');
assert.equal(S.storageKey('app_state','readyset_state',{}),'readyset_state');
assert.equal(S.snapshotScope('planner',{}),'local/anonymous/scope/planner');

const a={authenticated:true,family_id:'F A',member_id:'CHILD_A'};
const b={authenticated:true,family_id:'F A',member_id:'CHILD_B'};
assert.equal(S.validate(a).ok,true);
assert.notEqual(S.storageKey('app_state','readyset_state',a),S.storageKey('app_state','readyset_state',b));
assert.notEqual(S.snapshotScope('planner',a),S.snapshotScope('planner',b));
assert(S.storageKey('app_state','readyset_state',a).includes('family/F%20A/member/CHILD_A'));
assert.equal(S.belongsTo(S.snapshotScope('assignments',a),'assignments',a),true);
assert.equal(S.belongsTo(S.snapshotScope('assignments',a),'assignments',b),false);
assert.equal(S.validate({authenticated:true,family_id:'F'}).ok,false);
console.log('TAKY_FAMILY_MEMBER_STORAGE_SCOPE_V1_PASS');
