'use strict';
const assert=require('node:assert/strict');
const F=require('./family-context.js');

const anon=F.normalize({});
assert.equal(anon.auth_state,'ANONYMOUS_LOCAL');
assert.equal(anon.role,'CHILD');
assert.equal(F.validate(anon).ok,true);
assert.equal(F.requireRole(anon,'CHILD').ok,true);
assert.equal(F.requireRole(anon,'PARENT').reason,'PARENT_AUTH_REQUIRED');

const parent=F.normalize({
  authenticated:true,family_id:'F1',member_id:'P1',role:'parent',session_id:'S1',
  auth_provider:'NETLIFY_IDENTITY',expires_at:'2099-01-01T00:00:00.000Z'
});
assert.equal(parent.auth_state,'AUTHENTICATED_MEMBER');
assert.equal(parent.role,'PARENT');
assert.equal(F.validate(parent,{now:0}).ok,true);
assert.equal(F.requireRole(parent,'PARENT').ok,true);
assert.deepEqual(F.identity(parent),{family_id:'F1',member_id:'P1',role:'PARENT',authenticated:true});

const invalid=F.validate({authenticated:true,family_id:'F1',member_id:'M1',session_id:'S1',role:'OTHER'});
assert.equal(invalid.ok,false);
assert(invalid.issues.includes('ROLE_REQUIRED'));

const expired=F.validate({authenticated:true,family_id:'F1',member_id:'M1',session_id:'S1',role:'CHILD',expires_at:'2000-01-01T00:00:00.000Z'});
assert.equal(expired.ok,false);
assert(expired.issues.includes('SESSION_EXPIRED'));

console.log('TAKY_FAMILY_CONTEXT_V1_PASS');
