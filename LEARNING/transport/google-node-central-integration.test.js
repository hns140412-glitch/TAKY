'use strict';
const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs').promises;
const os=require('node:os');
const path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Google=require('./google-learning-principal.js');
const Central=require('./central-learning-http-endpoint.js');
const NodeBridge=require('./node-http-learning-bridge.js');

const clientId='TAKY_TEST_WEB_CLIENT_ID';
const nowMs=Date.UTC(2026,8,26,13,0,0),nowSec=Math.floor(nowMs/1000);
const basic={iss:'https://accounts.google.com',aud:clientId,
 exp:nowSec+3600,iat:nowSec-120};
const claims={
 'valid-parent-google-token-0001':{...basic,sub:'GOOGLE_PARENT_SUB',email:'old@example.test'},
 'valid-parent-renamed-mail-0002':{...basic,sub:'GOOGLE_PARENT_SUB',email:'new@example.test'},
 'valid-child-a-google-token-003':{...basic,sub:'GOOGLE_CHILD_A_SUB'},
 'invalid-audience-google-token4':{...basic,sub:'GOOGLE_PARENT_SUB',aud:'OTHER_APP'},
 'expired-parent-google-token5':{...basic,sub:'GOOGLE_PARENT_SUB',exp:nowSec-1},
 'bad-issuer-google-token-006':{...basic,sub:'GOOGLE_PARENT_SUB',iss:'https://malicious.example'},
 'future-issued-google-token7':{...basic,sub:'GOOGLE_PARENT_SUB',iat:nowSec+120},
 'adult-no-learning-grant-008':{...basic,sub:'GOOGLE_ADULT_SUB'},
 'bad-child-grant-token-0009':{...basic,sub:'GOOGLE_BAD_CHILD_SUB'},
 'duplicate-family-token-0010':{...basic,sub:'GOOGLE_DUPLICATE_SUB'}
};
const active=(family_id,self_member_id,role,ids,permissions=[])=>({
 status:'ACTIVE',family_id,self_member_id,role,
 learning_evidence_submit_member_ids:ids,permissions
});
let verifyCalls=[],lookups=[];
const verifier=async({idToken,audience})=>{
 verifyCalls.push({idToken,audience});
 if(!claims[idToken])throw Error('INVALID_GOOGLE_SIGNATURE');
 // Fake Google library in test ONLY; production runtime must supply actual
 // google-auth-library OAuth2Client.verifyIdToken signature/certificate check.
 return {getPayload:()=>claims[idToken]};
};
const membership=async({provider,subject})=>{
 lookups.push({provider,subject});
 if(subject==='GOOGLE_PARENT_SUB')return [
  active('F1','PARENT_A','PARENT',['CHILD_A']),
  active('F2','PARENT_A','PARENT',['CHILD_B'])
 ];
 if(subject==='GOOGLE_CHILD_A_SUB')return [
  active('F1','CHILD_A','CHILD',[])
 ];
 if(subject==='GOOGLE_ADULT_SUB')return [
  active('F1','GRANDMA_A','FAMILY_ADULT',['CHILD_A'],['FAMILY_PRAISE_GIFT'])
 ];
 if(subject==='GOOGLE_BAD_CHILD_SUB')return [
  active('F1','CHILD_A','CHILD',['CHILD_B'])
 ];
 if(subject==='GOOGLE_DUPLICATE_SUB')return [
  active('F1','PARENT_A','PARENT',['CHILD_A']),
  active('F1','PARENT_A','PARENT',['CHILD_A'])
 ];
 return [];
};
const google=Google.createFromGoogleAuthLibrary({
 clientIds:[clientId],oauth2Client:{verifyIdToken:verifier},
 lookupMemberships:membership,now:()=>nowMs
});
const packet=(id,family_id='F1',member_id='CHILD_A')=>({
 packet_id:'hide-seek:'+id,source_app:'hide-seek',
 context:{family_id,member_id,subject:'영어',concept_skill_target:'vocabulary'},
 event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-26T12:00:00.000Z',
 event_type:'RETRIEVAL_RESULT',payload:{
 member_id,subject:'영어',concept_skill_target:'vocabulary',
 instrument_version:'HIDE_CODE_RED_V1',verification_candidate:{
 verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',
 basis:'DETERMINISTIC_LOCAL_MATCH',outcome:1,reference_id:'UNTRUSTED_CLIENT_ANSWER'
 }}}
});
const headers=(token,origin)=>({
 'Content-Type':'application/json','Authorization':'Bearer '+token,
 ...(origin?{'Origin':origin}:{})
});
(async()=>{
 const principal=await google.verifyBearerToken('valid-parent-google-token-0001');
 assert.equal(principal.principal_id,'google:GOOGLE_PARENT_SUB');
 assert.equal(principal.identity_provider,'GOOGLE_OIDC_VERIFIED');
 assert.deepEqual(principal.families[0].authorized_member_ids,['CHILD_A','PARENT_A']);
 assert.deepEqual(principal.families[1].authorized_member_ids,['CHILD_B','PARENT_A']);
 assert(!JSON.stringify(principal).includes('old@example.test'));
 assert(!JSON.stringify(principal).includes('valid-parent-google-token-0001'));
 const renamed=await google.verifyBearerToken('valid-parent-renamed-mail-0002');
 assert.equal(renamed.principal_id,principal.principal_id);
 assert.deepEqual(renamed.families,principal.families);
 assert.equal(verifyCalls[0].audience[0],clientId);
 assert.deepEqual(lookups[0],{provider:'GOOGLE_OIDC',subject:'GOOGLE_PARENT_SUB'});
 for(const t of ['invalid-audience-google-token4','expired-parent-google-token5',
  'bad-issuer-google-token-006','future-issued-google-token7',
  'adult-no-learning-grant-008','bad-child-grant-token-0009','duplicate-family-token-0010']){
  await assert.rejects(()=>google.verifyBearerToken(t),/INVALID|REQUIRED|FORBIDDEN/);
 }
 await assert.rejects(()=>google.verifyBearerToken('not-a-google-token-valid'),/INVALID_GOOGLE_SIGNATURE/);
 assert.throws(()=>Google.create({clientIds:[clientId],lookupMemberships:membership}),
  /GOOGLE_SIGNATURE_VERIFIER_REQUIRED/);
 assert.throws(()=>Google.create({clientIds:[],verifyIdToken:verifier,lookupMemberships:membership}),
  /EXPLICIT_GOOGLE_CLIENT_ID_ALLOWLIST_REQUIRED/);
 assert.throws(()=>NodeBridge.createHandler({endpoint:{handle(){}} ,
  allowedOrigins:['*']}),/EXPLICIT_HTTPS_ORIGIN_ALLOWLIST_REQUIRED/);

 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-google-node-central-'));
 let server;
 try{
  const store=await new LocalJsonStrongStore(root).init();
  const endpoint=Central.create({
   verifyBearerToken:google.verifyBearerToken,store
  });
  server=http.createServer(NodeBridge.createHandler({
   endpoint,allowedOrigins:['https://ready.example.test','https://hide.example.test']
  }));
  await new Promise((resolve,reject)=>{
   server.once('error',reject);
   server.listen(0,'127.0.0.1',resolve);
  });
  const baseUrl='http://127.0.0.1:'+server.address().port;
  const send=(token,p,origin='https://ready.example.test')=>fetch(baseUrl+Central.ENDPOINT,{
   method:'POST',headers:headers(token,origin),body:JSON.stringify(p)
  });
  const success=await send('valid-parent-google-token-0001',packet('real-http-1'));
  const body=await success.json();
  assert.equal(success.status,200,JSON.stringify(body));
  assert.equal(body.ok,true);
  assert.equal(body.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
  assert.equal(body.receipt_scope.member_id,'CHILD_A');
  assert.equal(success.headers.get('Access-Control-Allow-Origin'),'https://ready.example.test');
  assert.equal(success.headers.get('Cache-Control'),'private, no-store, max-age=0');
  assert(!JSON.stringify(body).includes('authorized_member_ids'));
  assert(!JSON.stringify(body).includes('verification_candidate'));
  assert(!JSON.stringify(body).includes('google:GOOGLE_PARENT_SUB'));
  const saved=await store.getWithMetadata(
   'families/F1/members/CHILD_A/learning-engine/state-v1',{consistency:'strong',type:'json'});
  assert(saved?.etag);
  assert.equal(saved.data.observation_only.length,1);
  assert.equal(Object.keys(saved.data.scope_receipts||{}).length,0);

  const duplicate=await send('valid-parent-google-token-0001',packet('real-http-1'));
  assert.equal((await duplicate.json()).duplicate,true);
  const own=await send('valid-child-a-google-token-003',packet('child-self-1'));
  assert.equal(own.status,200);
  const childOther=await send('valid-child-a-google-token-003',packet('child-cross-1','F2','CHILD_B'));
  assert.equal(childOther.status,403);
  const parentCross=await send('valid-parent-google-token-0001',packet('parent-cross-1','F2','CHILD_A'));
  assert.equal(parentCross.status,403);
  const giftOnlyAdult=await send('adult-no-learning-grant-008',packet('adult-gift-only-1'));
  assert.equal(giftOnlyAdult.status,401);
  const forgedOrigin=await send('valid-parent-google-token-0001',packet('origin-forged-1'),
    'https://untrusted.example.test');
  assert.equal(forgedOrigin.status,403);
  assert.equal(forgedOrigin.headers.get('Access-Control-Allow-Origin'),null);
  const preflight=await fetch(baseUrl+Central.ENDPOINT,{
   method:'OPTIONS',headers:{Origin:'https://hide.example.test',
    'Access-Control-Request-Method':'POST',
    'Access-Control-Request-Headers':'authorization,content-type'}
  });
  assert.equal(preflight.status,204);
  assert.equal(preflight.headers.get('Access-Control-Allow-Origin'),'https://hide.example.test');
  const forbiddenPreflight=await fetch(baseUrl+Central.ENDPOINT,{
   method:'OPTIONS',headers:{Origin:'https://untrusted.example.test'}
  });
  assert.equal(forbiddenPreflight.status,403);
  const absentToken=await fetch(baseUrl+Central.ENDPOINT,{
   method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(packet('no-token-1'))
  });
  assert.equal(absentToken.status,401);
  const missingRoute=await fetch(baseUrl+'/api/badge/award',{method:'POST'});
  assert.equal(missingRoute.status,404);
  const overLimit=await fetch(baseUrl+Central.ENDPOINT,{
   method:'POST',headers:headers('valid-parent-google-token-0001'),
   body:'X'.repeat(65537)
  });
  assert.equal(overLimit.status,413);
  assert.equal(overLimit.headers.get('Cache-Control'),'private, no-store, max-age=0');

  console.log('GOOGLE_NODE_CENTRAL_LEARNING_PASS: actual loopback HTTP, Google sub not email, server membership grants, sibling and family isolation, gift-only adult denied, forged origin/size fail, no-store observation ACK');
 }finally{
  if(server)await new Promise((resolve,reject)=>server.close(err=>err?reject(err):resolve()));
  await fs.rm(root,{recursive:true,force:true});
 }
})().catch(err=>{console.error(err);process.exitCode=1;});
