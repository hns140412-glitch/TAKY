'use strict';

const assert=require('node:assert/strict');
const os=require('node:os');
const path=require('node:path');
const fs=require('node:fs').promises;
const Profile=require('./family-member-profile-http-endpoint.js');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');

const token='valid-family-profile-token-0001';
const principal={
  authenticated:true,
  principal_id:'PARENT_A',
  identity_provider:'GOOGLE_OIDC',
  families:[{family_id:'F1',self_member_id:'PARENT_A',authorized_member_ids:['CHILD_A']}]
};
const verifyBearerToken=async value=>{
  assert.equal(value,token);
  return principal;
};
const request=(action,body={})=>({
  method:'POST',path:Profile.ENDPOINT,
  headers:{'content-type':'application/json','authorization':'Bearer '+token},
  body:JSON.stringify({action,family_id:'F1',member_id:'CHILD_A',...body})
});
const projection=(version=1,extra={})=>({
  member_id:'CHILD_A',
  profile_version:version,
  display_name:'지우',
  legal_name:'김지우',
  nickname:'지우',
  family_role:'CHILD',
  birth_date:'2015-03-14',
  school_stage:'E5',
  share_name_mode:'NAME_NICKNAME',
  status:'CONFIRMED',
  updated_at:'2026-10-09T00:30:00.000Z',
  ...extra
});

(async()=>{
  assert.equal(Profile.normalizeProjection(projection()).ok,true);
  assert.equal(Profile.normalizeProjection({...projection(),parentAccess:true}).reason,'MEMBER_PROFILE_FIELDS_INVALID');
  assert.equal(Profile.normalizeProjection({...projection(),sourcePhoto:'data:image/jpeg;base64,x'}).reason,'MEMBER_PROFILE_FIELDS_INVALID');
  assert.equal(Profile.normalizeProjection({...projection(),birth_date:'2015-02-31'}).reason,'MEMBER_PROFILE_BIRTH_DATE_INVALID');

  const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-family-member-profile-'));
  try{
    const store=await new LocalJsonStrongStore(root).init();
    const endpoint=Profile.create({verifyBearerToken,store});

    const empty=await endpoint.handle(request('GET'));
    assert.equal(empty.status,200);
    assert.equal(JSON.parse(empty.body).found,false);

    const publish=await endpoint.handle(request('PUBLISH',{projection:projection()}));
    const publishBody=JSON.parse(publish.body);
    assert.equal(publish.status,200,JSON.stringify(publishBody));
    assert.equal(publishBody.published,true);
    assert.equal(publishBody.projection.school_stage,'E5');

    const fetched=await endpoint.handle(request('GET'));
    const fetchedBody=JSON.parse(fetched.body);
    assert.equal(fetched.status,200);
    assert.equal(fetchedBody.found,true);
    assert.equal(fetchedBody.projection.nickname,'지우');

    const retry=await endpoint.handle(request('PUBLISH',{projection:projection()}));
    assert.equal(retry.status,200);
    assert.equal(JSON.parse(retry.body).idempotent,true);

    const collision=await endpoint.handle(request('PUBLISH',{projection:projection(1,{nickname:'다른이름'})}));
    assert.equal(collision.status,409);
    assert.equal(JSON.parse(collision.body).reason,'MEMBER_PROFILE_VERSION_COLLISION');

    const upgrade=await endpoint.handle(request('PUBLISH',{projection:projection(2,{school_stage:'E6',updated_at:'2027-03-01T00:00:00.000Z'})}));
    assert.equal(upgrade.status,200);
    assert.equal(JSON.parse(upgrade.body).projection.school_stage,'E6');

    const regression=await endpoint.handle(request('PUBLISH',{projection:projection(1)}));
    assert.equal(regression.status,409);
    assert.equal(JSON.parse(regression.body).reason,'MEMBER_PROFILE_VERSION_REGRESSION');

    const cross=await endpoint.handle({
      ...request('GET'),
      body:JSON.stringify({action:'GET',family_id:'F1',member_id:'OTHER_CHILD'})
    });
    assert.equal(cross.status,403);

    console.log('FAMILY_MEMBER_PROFILE_HTTP_PASS');
  }finally{
    await fs.rm(root,{recursive:true,force:true});
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
