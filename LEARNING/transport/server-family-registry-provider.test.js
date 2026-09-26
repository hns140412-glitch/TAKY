'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const crypto=require('node:crypto');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Registry=require('./server-family-registry-provider.js');
const Google=require('./google-learning-principal.js');

const now=Date.UTC(2026,8,26,13),expiry=new Date(now+3600000).toISOString();
const hash=sub=>crypto.createHash('sha256').update('GOOGLE_OIDC:'+sub).digest('hex');
const row=(family,self,role,active,grants,permissions=[])=>({
 status:'ACTIVE',family_id:family,self_member_id:self,role,
 active_family_member_ids:active,
 learning_evidence_submit_member_ids:grants,permissions
});
const record=(sub,memberships)=>({
 authority:Registry.REGISTRY_AUTHORITY,version:1,
 identity_provider:'GOOGLE_OIDC',subject_sha256:hash(sub),
 status:'ACTIVE',expires_at:expiry,memberships
});
(async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'taky-registry-'));
 try{
  const store=await new LocalJsonStrongStore(dir).init();
  const provider=Registry.create({store,now:()=>now});
  const subject='GOOGLE_PARENT_SUB';
  const key=Registry.subjectRecordKey(subject);
  assert(!key.includes(subject));
  const good=record(subject,[
   row('F1','PARENT_A','PARENT',['PARENT_A','CHILD_A','CHILD_B'],['CHILD_A']),
   row('F2','PARENT_A','PARENT',['PARENT_A','CHILD_C'],['CHILD_C'])
  ]);
  await store.setJSON(key,good,{onlyIfNew:true});
  const rows=await provider.lookupMemberships({provider:'GOOGLE_OIDC',subject});
  assert.equal(rows.length,2);
  assert.deepEqual(rows[0].learning_evidence_submit_member_ids,['CHILD_A']);
  assert(!JSON.stringify(rows).includes('CHILD_B'));
  assert(!JSON.stringify(rows).includes('subject_sha256'));
  const client='TAKY_TEST_WEB_CLIENT_ID',nowS=Math.floor(now/1000);
  const google=Google.create({
   clientIds:[client],
   verifyIdToken:async()=>({getPayload:()=>({
    iss:'https://accounts.google.com',aud:client,sub:subject,
    iat:nowS-30,exp:nowS+3600,email:'untrusted@example.test',
    family_id:'ATTACK_FAMILY',role:'PARENT'})}),
   lookupMemberships:provider.lookupMemberships,now:()=>now
  });
  const principal=await google.verifyBearerToken('test-only-google-ticket-0001');
  assert.deepEqual(principal.families[0].authorized_member_ids,['CHILD_A','PARENT_A']);
  assert(!JSON.stringify(principal).includes('untrusted@example.test'));
  assert.equal(principal.families[1].family_id,'F2');
  assert.deepEqual(await provider.lookupMemberships({provider:'GOOGLE_OIDC',subject:'UNKNOWN'}),[]);
  assert.deepEqual(await provider.lookupMemberships({provider:'UNTRUSTED',subject}),[]);
  // No permission caching: revocation is visible at the next token check.
  const current=await store.getWithMetadata(key,{consistency:'strong',type:'json'});
  await store.setJSON(key,{...good,status:'REVOKED'},{onlyIfMatch:current.etag});
  assert.deepEqual(await provider.lookupMemberships({provider:'GOOGLE_OIDC',subject}),[]);
  await assert.rejects(()=>google.verifyBearerToken('test-only-google-ticket-0001'),
   /ACTIVE_TAKY_MEMBERSHIP_REQUIRED/);
  const revoked=await store.getWithMetadata(key,{consistency:'strong',type:'json'});
  await store.setJSON(key,{...good,expires_at:new Date(now-1).toISOString()},
   {onlyIfMatch:revoked.etag});
  assert.deepEqual(await provider.lookupMemberships({provider:'GOOGLE_OIDC',subject),[]);
  const old=await store.getWithMetadata(key,{consistency:'strong',type:'json'});
  const corrupted={...good,subject_sha256:hash('OTHER_SUB')};
  await store.setJSON(key,corrupted,{onlyIfMatch:old.etag});
  await assert.rejects(()=>provider.lookupMemberships({provider:'GOOGLE_OIDC',subject}),
   /REGISTRY_PROVENANCE_INVALID/);
  const corruptCurrent=await store.getWithMetadata(key,{consistency:'strong',type:'json'});
  await store.setJSON(key,record(subject,[
   row('F1','PARENT_A','PARENT',['PARENT_A','CHILD_A'],['CHILD_B'])
  ]),{onlyIfMatch:corruptCurrent.etag});
  await assert.rejects(()=>provider.lookupMemberships({provider:'GOOGLE_OIDC',subject}),
   /REGISTRY_MEMBER_GRANT_PROVENANCE_INVALID/);
  const other=await store.getWithMetadata(key,{consistency:'strong',type:'json'});
  await store.setJSON(key,record(subject,[
   row('F1','CHILD_A','CHILD',['CHILD_A','CHILD_B'],['CHILD_B'])
  ]),{onlyIfMatch:other.etag});
  await assert.rejects(()=>provider.lookupMemberships({provider:'GOOGLE_OIDC',subject}),
   /CHILD_CROSS_MEMBER_GRANT_FORBIDDEN/);
  const missingEtags=Registry.create({store:{
   getWithMetadata:async()=>({consistency:'strong',data:good})
  },now:()=>now});
  await assert.rejects(()=>missingEtags.lookupMemberships({provider:'GOOGLE_OIDC',subject}),
   /REGISTRY_STRONG_READ_REQUIRED/);
  assert.throws(()=>Registry.create({store:{}}),/SERVER_REGISTRY_STRONG_STORE_REQUIRED/);
  // FAMILY_ADULT gift-only membership is preserved but Google principal denies
  // learning submission without a separate server-issued permission.
  const adult='GOOGLE_ADULT_SUB';
  await store.setJSON(Registry.subjectRecordKey(adult),record(adult,[
   row('F1','GRANDMA','FAMILY_ADULT',['GRANDMA','CHILD_A'],['CHILD_A'],
    ['FAMILY_PRAISE_GIFT'])
  ]),{onlyIfNew:true});
  const adultGoogle=Google.create({
   clientIds:[client],
   verifyIdToken:async()=>({getPayload:()=>({
    iss:'https://accounts.google.com',aud:client,sub:adult,
    iat:nowS-30,exp:nowS+3600})}),
   lookupMemberships:provider.lookupMemberships,now:()=>now
  });
  await assert.rejects(()=>adultGoogle.verifyBearerToken('test-only-adult-ticket-0001'),
   /FAMILY_ADULT_EXPLICIT_LEARNING_PERMISSION_REQUIRED/);
  console.log('SERVER_FAMILY_REGISTRY_PROVIDER_PASS: strong read, Google sub mapping, family/member grants, immediate revocation, expiry, invalid grants and gift-only adult rejection');
 }finally{await fs.rm(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
