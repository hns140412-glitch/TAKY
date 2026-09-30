'use strict';

const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs').promises;
const os=require('node:os');
const path=require('node:path');
const Host=require('./central-learning-production-host.js');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');

const clientId='TAKY_PRODUCTION_HOST_TEST_CLIENT';
const nowMs=Date.UTC(2026,8,30,9,0,0);
const nowSec=Math.floor(nowMs/1000);
const token='valid-parent-google-id-token-0001';
const oauth2Client={verifyIdToken:async({idToken,audience})=>{
  assert.equal(idToken,token);
  assert.deepEqual(audience,[clientId]);
  return {getPayload:()=>({
    iss:'https://accounts.google.com',aud:clientId,
    sub:'GOOGLE_PARENT_SUB',iat:nowSec-60,exp:nowSec+3600
  })};
}};
const lookupMemberships=async({provider,subject})=>{
  assert.equal(provider,'GOOGLE_OIDC');
  assert.equal(subject,'GOOGLE_PARENT_SUB');
  return [{status:'ACTIVE',family_id:'F1',self_member_id:'PARENT_A',role:'PARENT',
    learning_evidence_submit_member_ids:['CHILD_A'],permissions:[]}];
};
const verifySpecialistEvidence=async()=>({ok:false});
const resolveIndexedEvidence=async scope=>{
  assert.equal(scope.family_id,'F1');
  assert.equal(scope.member_id,'CHILD_A');
  return null;
};
const independentIndexOwnerVerifier=()=>null;

(async()=>{
  assert.throws(()=>Host.create({}),/PRODUCTION_MEMBERSHIP_PROVIDER_REQUIRED/);
  assert.throws(()=>Host.create({lookupMemberships}),/PRODUCTION_STRONG_STORE_REQUIRED/);
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-production-host-'));
  let server;
  try{
    const store=await new LocalJsonStrongStore(root).init();
    const uploads=new Map();
    const characterAssetObjectStore={
      async createUploadTicket(meta){uploads.set('U1',{...meta,committed:false});return{upload_id:'U1',upload_url:'https://upload.example.test/U1',expires_at:'2026-09-30T09:05:00.000Z'}},
      async commitUpload({asset_ref,upload_id,sha256}){const row=uploads.get(upload_id);if(!row||row.asset_ref!==asset_ref)return{ok:false};row.committed=true;row.sha256=sha256;return{ok:true,sha256,etag:'ASSET-E1'}},
      async createReadTicket({asset_ref}){const row=[...uploads.values()].find(x=>x.asset_ref===asset_ref&&x.committed);return row?{read_url:'https://read.example.test/asset',expires_at:'2026-09-30T09:05:00.000Z'}:null}
    };
    const common={clientIds:[clientId],oauth2Client,lookupMemberships,store,
      verifySpecialistEvidence,resolveIndexedEvidence,independentIndexOwnerVerifier,
      characterAssetObjectStore,
      allowedOrigins:['https://ready.example.test']};
    assert.throws(()=>Host.create({...common,verifySpecialistEvidence:null}),
      /PRODUCTION_SPECIALIST_VERIFIER_REQUIRED/);
    assert.throws(()=>Host.create({...common,resolveIndexedEvidence:null}),
      /PRODUCTION_INDEXED_EVIDENCE_RESOLVER_REQUIRED/);
    assert.throws(()=>Host.create({...common,independentIndexOwnerVerifier:null}),
      /PRODUCTION_INDEX_OWNER_VERIFIER_REQUIRED/);
    assert.throws(()=>Host.create({...common,allowedOrigins:['http://ready.example.test']}),
      /PRODUCTION_HTTPS_ORIGIN_ALLOWLIST_REQUIRED/);

    const host=Host.create({...common,now:()=>nowMs});
    assert.deepEqual([...host.routes],['/api/learning/evidence','/api/learning/decision','/api/family/character-profile','/api/family/character-asset']);
    assert.deepEqual([...host.allowed_origins],['https://ready.example.test']);
    server=http.createServer(host.handler);
    await new Promise((resolve,reject)=>{
      server.once('error',reject);server.listen(0,'127.0.0.1',resolve);
    });
    const base='http://127.0.0.1:'+server.address().port;
    const response=await fetch(base+'/api/learning/decision',{
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,
        Origin:'https://ready.example.test'},
      body:JSON.stringify({family_id:'F1',member_id:'CHILD_A',
        subject:'math',concept_skill_target:'g5-math-equivalent-fraction-reasoning'})
    });
    const body=await response.json();
    assert.equal(response.status,200,JSON.stringify(body));
    assert.equal(body.ok,true);
    assert.equal(body.authenticated_server_response,true);
    assert.equal(body.runtime_result.decision.execution_status,
      'HOLD_FOR_MORE_RELIABLE_INTERPRETATION');
    assert.equal(body.runtime_result.trace.verified_evidence_count,0);
    assert.equal(response.headers.get('Access-Control-Allow-Origin'),'https://ready.example.test');

    const assetCreate=await fetch(base+'/api/family/character-asset',{
      method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,Origin:'https://ready.example.test'},
      body:JSON.stringify({action:'CREATE_UPLOAD',family_id:'F1',member_id:'CHILD_A',character_id:'char_CHILD_A_v1',content_type:'image/webp',byte_size:2048,sha256:'a'.repeat(64),asset_version:'v1'})
    });
    const assetCreateBody=await assetCreate.json();assert.equal(assetCreate.status,200,JSON.stringify(assetCreateBody));assert.ok(assetCreateBody.asset_ref.startsWith('taky-character:'));
    const assetCommit=await fetch(base+'/api/family/character-asset',{
      method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,Origin:'https://ready.example.test'},
      body:JSON.stringify({action:'COMMIT_UPLOAD',family_id:'F1',member_id:'CHILD_A',character_id:'char_CHILD_A_v1',asset_ref:assetCreateBody.asset_ref,upload_id:assetCreateBody.upload_id,sha256:'a'.repeat(64)})
    });
    assert.equal(assetCommit.status,200);

    const published=await fetch(base+'/api/family/character-profile',{
      method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,Origin:'https://ready.example.test'},
      body:JSON.stringify({action:'PUBLISH',family_id:'F1',member_id:'CHILD_A',projection:{member_id:'CHILD_A',character_id:'char_CHILD_A_v1',identity_version:1,master_asset_ref:assetCreateBody.asset_ref,master_sha256:'a'.repeat(64),asset_version:'gen-v1',derivative_refs:{},status:'CONFIRMED',updated_at:'2026-09-30T10:00:00.000Z'}})
    });
    const publishedBody=await published.json();assert.equal(published.status,200,JSON.stringify(publishedBody));assert.equal(publishedBody.published,true);
    const fetched=await fetch(base+'/api/family/character-profile',{
      method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,Origin:'https://ready.example.test'},
      body:JSON.stringify({action:'GET',family_id:'F1',member_id:'CHILD_A'})
    });
    const fetchedBody=await fetched.json();assert.equal(fetched.status,200);assert.equal(fetchedBody.projection.character_id,'char_CHILD_A_v1');

    const denied=await fetch(base+'/api/learning/decision',{
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,
        Origin:'https://evil.example.test'},
      body:'{}'
    });
    assert.equal(denied.status,403);

    console.log('CENTRAL_PRODUCTION_HOST_PASS: identity auth, CORS, learning + character profile + private character asset endpoints');
  }finally{
    if(server)await new Promise(resolve=>server.close(resolve));
    await fs.rm(root,{recursive:true,force:true});
  }
})().catch(e=>{console.error(e);process.exitCode=1});