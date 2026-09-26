'use strict';
const assert=require('node:assert/strict');
const os=require('node:os');
const path=require('node:path');
const fsp=require('node:fs').promises;
const Identity=require('./family-member-identity-resolver.js');
const Endpoint=require('./local-learning-endpoint.js');

const principal={
  authenticated:true,
  principal_id:'PARENT_1',
  identity_provider:'GOOGLE_OIDC_CANDIDATE',
  families:[
    {family_id:'F1',self_member_id:'PARENT_1',authorized_member_ids:['CHILD_A']},
    {family_id:'F2',self_member_id:'PARENT_1',authorized_member_ids:['CHILD_B']}
  ]
};

const packet=(family,member,id)=>({
  packet_id:'hide-seek:'+id,source_app:'hide-seek',
  context:{family_id:family,member_id:member,subject:'영어',concept_skill_target:'vocabulary'},
  event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-26T00:00:00.000Z',event_type:'RETRIEVAL_RESULT',payload:{
    member_id:member,subject:'영어',concept_skill_target:'vocabulary',instrument_version:'HIDE_CODE_RED_V1',
    verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',basis:'DETERMINISTIC_LOCAL_MATCH',outcome:1,reference_id:'word:'+id}
  }}
});

(async()=>{
  const ambiguous=Identity.resolve(principal,{});
  assert.equal(ambiguous.ok,false);
  assert.ok(ambiguous.issues.includes('FAMILY_SCOPE_EXPLICIT_SELECTION_REQUIRED'));

  const f1=Identity.resolve(principal,{requested_family_id:'F1'});
  assert.equal(f1.ok,true);
  assert.deepEqual(f1.identity.authorized_member_ids,['CHILD_A','PARENT_1']);

  const root=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-endpoint-'));
  try{
    const endpoint=Endpoint.create({root,resolvePrincipal:async()=>principal});

    const ok=await endpoint.handle({},packet('F1','CHILD_A','e1'));
    assert.equal(ok.ok,true);
    assert.equal(ok.authenticated_scope.family_id,'F1');
    assert.equal(ok.authenticated_scope.member_id,'CHILD_A');

    const crossFamily=await endpoint.handle({},packet('F2','CHILD_A','e2'));
    assert.equal(crossFamily.ok,false);
    assert.equal(crossFamily.reason,'TRANSPORT_NOT_AUTHORIZED');
    assert.ok(crossFamily.issues.includes('MEMBER_SCOPE_NOT_AUTHORIZED'));

    const crossMember=await endpoint.handle({},packet('F1','CHILD_B','e3'));
    assert.equal(crossMember.ok,false);
    assert.equal(crossMember.reason,'TRANSPORT_NOT_AUTHORIZED');
    assert.ok(crossMember.issues.includes('MEMBER_SCOPE_NOT_AUTHORIZED'));

    const f2ok=await endpoint.handle({},packet('F2','CHILD_B','e4'));
    assert.equal(f2ok.ok,true);
    assert.equal(f2ok.authenticated_scope.family_id,'F2');
    assert.equal(f2ok.authenticated_scope.member_id,'CHILD_B');

    const denied=Endpoint.create({root,resolvePrincipal:async()=>({...principal,authenticated:false})});
    const unauth=await denied.handle({},packet('F1','CHILD_A','e5'));
    assert.equal(unauth.ok,false);
    assert.equal(unauth.reason,'IDENTITY_RESOLUTION_FAILED');

    console.log('FAMILY_MEMBER_IDENTITY_ENDPOINT_BINDING_PASS');
  }finally{await fsp.rm(root,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});
