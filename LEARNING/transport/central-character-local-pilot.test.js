'use strict';
const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs').promises;
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const Host=require('./central-learning-production-host.js');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const {LocalCharacterObjectStore}=require('./local-character-object-store.js');
const clientId='TAKY_CHARACTER_PILOT_TEST_CLIENT';
const nowMs=Date.UTC(2026,8,30,10,0,0),nowSec=Math.floor(nowMs/1000),token='pilot-parent-google-id-token-0001';
const oauth2Client={verifyIdToken:async()=>({getPayload:()=>({iss:'https://accounts.google.com',aud:clientId,sub:'PARENT_SUB',iat:nowSec-60,exp:nowSec+3600})})};
const lookupMemberships=async()=>[{status:'ACTIVE',family_id:'F1',self_member_id:'PARENT_A',role:'PARENT',learning_evidence_submit_member_ids:['CHILD_A'],permissions:[]}];
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-char-pilot-'));let server;
 try{
  const store=await new LocalJsonStrongStore(path.join(root,'state')).init();
  const objectStore=await new LocalCharacterObjectStore(path.join(root,'assets'),{publicBaseUrl:'http://127.0.0.1:0'}).init();
  const host=Host.create({clientIds:[clientId],oauth2Client,lookupMemberships,store,characterAssetObjectStore:objectStore,verifySpecialistEvidence:async()=>({ok:false}),resolveIndexedEvidence:async()=>null,independentIndexOwnerVerifier:()=>null,allowedOrigins:['https://ready.example.test'],now:()=>nowMs});
  server=http.createServer(host.handler);await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});const base='http://127.0.0.1:'+server.address().port;objectStore.publicBaseUrl=base;
  const auth={'Content-Type':'application/json','Authorization':'Bearer '+token,Origin:'https://ready.example.test'};
  const bytes=Buffer.from('realistic-character-master-webp-payload'),sha=crypto.createHash('sha256').update(bytes).digest('hex');
  let resp=await fetch(base+'/api/family/character-asset',{method:'POST',headers:auth,body:JSON.stringify({action:'CREATE_UPLOAD',family_id:'F1',member_id:'CHILD_A',character_id:'char_CHILD_A_v1',content_type:'image/webp',byte_size:bytes.length,sha256:sha,asset_version:'v1'})});let body=await resp.json();assert.equal(resp.status,200,JSON.stringify(body));
  resp=await fetch(body.upload_url,{method:'PUT',headers:{'Content-Type':'image/webp'},body:bytes});assert.equal(resp.status,204);
  const assetRef=body.asset_ref,uploadId=body.upload_id;
  resp=await fetch(base+'/api/family/character-asset',{method:'POST',headers:auth,body:JSON.stringify({action:'COMMIT_UPLOAD',family_id:'F1',member_id:'CHILD_A',character_id:'char_CHILD_A_v1',asset_ref:assetRef,upload_id:uploadId,sha256:sha})});assert.equal(resp.status,200);
  resp=await fetch(base+'/api/family/character-profile',{method:'POST',headers:auth,body:JSON.stringify({action:'PUBLISH',family_id:'F1',member_id:'CHILD_A',projection:{member_id:'CHILD_A',character_id:'char_CHILD_A_v1',identity_version:1,master_asset_ref:assetRef,master_sha256:sha,asset_version:'v1',derivative_refs:{},status:'CONFIRMED',updated_at:'2026-09-30T10:00:00.000Z'}})});body=await resp.json();assert.equal(resp.status,200,JSON.stringify(body));
  resp=await fetch(base+'/api/family/character-asset',{method:'POST',headers:auth,body:JSON.stringify({action:'RESOLVE_READ',family_id:'F1',member_id:'CHILD_A',character_id:'char_CHILD_A_v1',asset_ref:assetRef})});body=await resp.json();assert.equal(resp.status,200,JSON.stringify(body));
  resp=await fetch(body.read_url);assert.equal(resp.status,200);assert.deepEqual(Buffer.from(await resp.arrayBuffer()),bytes);
  console.log('CENTRAL_CHARACTER_LOCAL_PILOT_PASS: Ready-style upload -> verified commit -> profile publish -> signed read works end-to-end locally');
 }finally{if(server)await new Promise(r=>server.close(r));await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exit(1)});
