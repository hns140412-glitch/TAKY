'use strict';
const assert=require('node:assert/strict');
const A=require('./transport-auth-policy.js');

const packet={
  source_app:'hide-seek',
  context:{family_id:'F1',member_id:'CHILD_A'}
};
const ok=A.authorize(packet,{
  authenticated:true,
  family_id:'F1',
  authorized_member_ids:['PARENT','CHILD_A']
});
assert.equal(ok.ok,true);
assert.deepEqual(ok.scope,{family_id:'F1',member_id:'CHILD_A'});

const unauth=A.authorize(packet,{
  authenticated:false,
  family_id:'F1',
  authorized_member_ids:['CHILD_A']
});
assert.equal(unauth.ok,false);
assert.equal(unauth.issues.includes('AUTHENTICATION_REQUIRED'),true);

const wrongFamily=A.authorize(packet,{
  authenticated:true,
  family_id:'F2',
  authorized_member_ids:['CHILD_A']
});
assert.equal(wrongFamily.issues.includes('FAMILY_SCOPE_MISMATCH'),true);

const wrongMember=A.authorize(packet,{
  authenticated:true,
  family_id:'F1',
  authorized_member_ids:['PARENT']
});
assert.equal(wrongMember.issues.includes('MEMBER_SCOPE_NOT_AUTHORIZED'),true);

const badApp=A.authorize({...packet,source_app:'unknown-app'},{
  authenticated:true,
  family_id:'F1',
  authorized_member_ids:['CHILD_A']
});
assert.equal(badApp.issues.includes('SOURCE_APP_NOT_ALLOWED'),true);

console.log('LEARNING_TRANSPORT_AUTH_POLICY_PASS');
