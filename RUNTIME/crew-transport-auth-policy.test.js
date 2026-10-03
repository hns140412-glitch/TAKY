'use strict';
const assert=require('node:assert/strict');
const A=require('./crew-transport-auth-policy.js');
const packet={source_app:'READY_SET',context:{family_id:'F1',member_id:'C1'}};
assert.equal(A.authorize(packet,{authenticated:true,family_id:'F1',authorized_member_ids:['C1']}).ok,true);
assert.equal(A.authorize(packet,{authenticated:true,family_id:'F1',authorized_member_ids:['OTHER']}).ok,false);
assert.equal(A.authorize({...packet,source_app:'OTHER'},{authenticated:true,family_id:'F1',authorized_member_ids:['C1']}).ok,false);
console.log('CREW_TRANSPORT_AUTH_POLICY_PASS');
