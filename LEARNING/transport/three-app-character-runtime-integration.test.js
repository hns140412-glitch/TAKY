'use strict';
const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs').promises;
const os=require('node:os');
const path=require('node:path');
const vm=require('node:vm');
const Host=require('./central-learning-production-host.js');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const {LocalCharacterObjectStore}=require('./local-character-object-store.js');

async function loadBrowserAdapter(file,exportName){
 const code=await fs.readFile(file,'utf8');
 const localStorage={m:new Map(),setItem(k,v){this.m.set(k,String(v))},getItem(k){return this.m.has(k)?this.m.get(k):null},removeItem(k){this.m.delete(k)}};
 const ctx={window:{},globalThis:null,localStorage,location:{href:'http://localhost/'},URL,Blob,fetch,crypto:globalThis.crypto,console,setTimeout,clearTimeout};
 ctx.globalThis=ctx;ctx.window=ctx;
 vm.createContext(ctx);vm.runInContext(code,ctx,{filename:file});
 const adapter=ctx[exportName];assert.ok(adapter,exportName+' missing');return {ctx,adapter};
}

(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-three-app-'));let server;
 try{
  const clientId='TAKY_THREE_APP_TEST_CLIENT',token='three-app-parent-id-token-0001',nowMs=Date.UTC(2026,8,30,11,0,0),nowSec=Math.floor(nowMs/1000);
  const oauth2Client={verifyIdToken:async({idToken})=>{assert.equal(idToken,token);return{getPayload:()=>({iss:'https://accounts.google.com',aud:clientId,sub:'PARENT_SUB',iat:nowSec-60,exp:nowSec+3600})}}};
  const lookupMemberships=async()=>[{status:'ACTIVE',family_id:'F1',self_member_id:'PARENT_A',role:'PARENT',learning_evidence_submit_member_ids:['CHILD_A'],permissions:[]}];
  const store=await new LocalJsonStrongStore(path.join(root,'state')).init();
  const objectStore=await new LocalCharacterObjectStore(path.join(root,'assets'),{publicBaseUrl:'http://127.0.0.1:0'}).init();
  const host=Host.create({clientIds:[clientId],oauth2Client,lookupMemberships,store,characterAssetObjectStore:objectStore,verifySpecialistEvidence:async()=>({ok:false}),resolveIndexedEvidence:async()=>null,independentIndexOwnerVerifier:()=>null,allowedOrigins:['https://ready.example.test','https://hide.example.test','https://snap.example.test'],now:()=>nowMs});
  server=http.createServer(host.handler);await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});const base='http://127.0.0.1:'+server.address().port;objectStore.publicBaseUrl=base;
  const getToken=async()=>token,getFamilyId=async()=> 'F1';
  const readyProfile=await loadBrowserAdapter('D:/Git PWA/Ready & Set/ready-family-character-profile-adapter-v1.js','ReadyFamilyCharacterProfileAdapterV1');
  const readyAsset=await loadBrowserAdapter('D:/Git PWA/Ready & Set/ready-character-asset-storage-adapter-v1.js','ReadyCharacterAssetStorageAdapterV1');
  const hideProfile=await loadBrowserAdapter('D:/Git PWA/Hide & Seek/hide-family-character-profile-adapter-v1.js','HideFamilyCharacterProfileAdapterV1');
  const hideAsset=await loadBrowserAdapter('D:/Git PWA/Hide & Seek/hide-character-asset-read-adapter-v1.js','HideCharacterAssetReadAdapterV1');
  const snapProfile=await loadBrowserAdapter('D:/Git PWA/Snap & Pop/snap-family-character-profile-adapter-v1.js','SnapFamilyCharacterProfileAdapterV1');
  const snapAsset=await loadBrowserAdapter('D:/Git PWA/Snap & Pop/snap-character-asset-read-adapter-v1.js','SnapCharacterAssetReadAdapterV1');
  for(const a of [readyProfile.adapter,readyAsset.adapter,hideProfile.adapter,hideAsset.adapter,snapProfile.adapter,snapAsset.adapter])a.registerHttpProvider({baseUrl:base,getToken,getFamilyId,fetchImpl:fetch});
  const bytes=new Blob(['same-character-master-across-three-apps'],{type:'image/webp'});
  const stored=await readyAsset.adapter.storeMaster({member_id:'CHILD_A',character_id:'char_CHILD_A_v1',asset_version:'v1',source_ref:bytes});
  assert.ok(stored.asset_ref.startsWith('taky-character:'));
  const projection={member_id:'CHILD_A',character_id:'char_CHILD_A_v1',identity_version:1,master_asset_ref:stored.asset_ref,master_sha256:stored.sha256,asset_version:'v1',derivative_refs:{},status:'CONFIRMED',updated_at:'2026-09-30T11:00:00.000Z'};
  const pub=await readyProfile.adapter.publish(projection);assert.equal(pub.state,'PUBLISHED');
  const h=await hideProfile.adapter.resolve('CHILD_A'),s=await snapProfile.adapter.resolve('CHILD_A');
  assert.equal(h.projection.character_id,projection.character_id);assert.equal(s.projection.character_id,projection.character_id);assert.equal(h.projection.master_asset_ref,stored.asset_ref);assert.equal(s.projection.master_asset_ref,stored.asset_ref);
  const hr=await hideAsset.adapter.resolveRead({member_id:'CHILD_A',character_id:projection.character_id,asset_ref:stored.asset_ref});
  const sr=await snapAsset.adapter.resolveRead({member_id:'CHILD_A',character_id:projection.character_id,asset_ref:stored.asset_ref});
  const hb=Buffer.from(await (await fetch(hr.read_url)).arrayBuffer()),sb=Buffer.from(await (await fetch(sr.read_url)).arrayBuffer());
  assert.deepEqual(hb,sb);assert.deepEqual(hb,Buffer.from(await bytes.arrayBuffer()));
  console.log('THREE_APP_CHARACTER_RUNTIME_PASS: Ready published one Character Master; Hide and Snap resolved same character_id, private pointer, and identical signed-read bytes');
 }finally{if(server)await new Promise(r=>server.close(r));await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exit(1)});
