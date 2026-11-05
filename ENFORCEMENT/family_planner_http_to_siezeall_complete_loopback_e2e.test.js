'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),fsp=require('node:fs/promises');
const os=require('node:os'),path=require('node:path'),http=require('node:http'),vm=require('node:vm'),crypto=require('node:crypto');
const {LocalJsonStrongStore}=require('../LEARNING/transport/local-json-strong-store.js');
const FamilyData=require('../LEARNING/transport/family-user-data-http-endpoint.js');
const UserData=require('../LEARNING/transport/family-user-data-store.js');
const Queue=require('../LEARNING/transport/family-user-data-archive-outbox.js');
const Bridge=require('../LEARNING/transport/node-http-learning-bridge.js');
const Worker=require('../LEARNING/transport/family-user-data-archive-service.js');
const Route=require('../LEARNING/transport/family-user-data-siezeall-archive-publisher.js');
const script=fs.readFileSync(path.join(__dirname,'../../Ready & Set/ready-family-planner-sync-v1.js'),'utf8');
function browser(base,member){
 const values=new Map(),events=new Map();
 const localStorage={getItem:k=>values.has(k)?values.get(k):null,
  setItem:(k,v)=>values.set(k,String(v)),removeItem:k=>values.delete(k)};
 const addEventListener=(e,f)=>{if(!events.has(e))events.set(e,[]);events.get(e).push(f)};
 const dispatchEvent=e=>{for(const f of events.get(e.type)||[])f(e)};
 const document={
  readyState:'loading',visibilityState:'visible',documentElement:{dataset:{}},body:null,
  addEventListener,getElementById:()=>null
 };
 const family={family_id:'FAMILY_A',self_member_id:'PARENT_A',authorized_member_ids:['CHILD_A','CHILD_B']};
 const window={addEventListener,dispatchEvent,
  TAKY_FAMILY_RUNTIME:{apiBaseUrl:base,getToken:async()=> 'test-central-access-bearer-token-12345',
   currentSession:async()=>family,fetchImpl:fetch},
  ReadyIdentityV1:{get:()=>({memberId:member})},
  ReadyFamilyRuntimeBootstrapV1:{resolveMemberBinding:(identity,session)=>
    session.authorized_member_ids.includes(identity.memberId)
     ?{ok:true,member_id:identity.memberId}:{ok:false}}
 };
 const ctx={window,document,localStorage,URL,URLSearchParams,location:{href:base},
  crypto:crypto.webcrypto,TextEncoder,JSON,Math,Date,fetch,
  Event:class{constructor(type){this.type=type}},CustomEvent:class{constructor(type,opts){this.type=type;this.detail=opts?.detail}},
  setTimeout:()=>0,clearTimeout:()=>{},console};
 ctx.globalThis=ctx;vm.createContext(ctx);vm.runInContext(script,ctx);
 return{api:window.ReadyFamilyPlannerSyncV1,storage:localStorage,read:()=>JSON.parse(localStorage.getItem('readyset_planner_v1')||'{}')};
}
async function launchServer(store){
 const principal={authenticated:true,principal_id:'PARENT_A',identity_provider:'TEST_FIXTURE',
  families:[{family_id:'FAMILY_A',self_member_id:'PARENT_A',authorized_member_ids:['CHILD_A','CHILD_B']}]};
 const data=FamilyData.create({store,verifyBearerToken:async()=>principal});
 const endpoint={handle:async()=>({status:200,headers:{},body:JSON.stringify({ok:true})})};
 const server=http.createServer(Bridge.createHandler({endpoint,userDataEndpoint:data,allowedOrigins:[]}));
 await new Promise((resolve,reject)=>server.listen(0,'127.0.0.1',e=>e?reject(e):resolve()));
 return{server,base:'http://127.0.0.1:'+server.address().port};
}
function fakeDrive(){
 const folder=Route.ids;
 const owner=[{type:'user',role:'owner',emailAddress:'siezeall@gmail.com'}];
 const m=new Map([
  [folder.root,{id:folder.root,permissions:[...owner,{type:'anyone',role:'writer'}]}],
  [folder.platform,{id:folder.platform,parents:[folder.root],permissions:owner}],
  [folder.leaf,{id:folder.leaf,parents:[folder.platform],permissions:owner}]
 ]);
 const objectBytes=new Map();
 let uploads=0;
 async function fetchImpl(url,opts){
  assert.equal(opts.headers.Authorization,'Bearer fake-siezeall-backend-service-token');
  const u=new URL(url);
  const reply=x=>({ok:true,status:200,json:async()=>x});
  if(u.pathname.startsWith('/upload/drive/v3/files')&&opts.method==='POST'){
   uploads++;
   const raw=Buffer.from(opts.body).toString('utf8');
   const start=raw.lastIndexOf('{"contract":"TAKY_PRIVATE_USER_DATA_ARCHIVE_ENVELOPE_V1"');
   const end=raw.indexOf('\r\n--taky-',start);
   assert(start>=0&&end>start);
   const blob=Buffer.from(raw.slice(start,end),'utf8'), envelope=JSON.parse(blob.toString());
   const id='mockSIEZEALLArchivedFile0000000001';
   const doc={id,parents:[folder.leaf],permissions:owner,
    appProperties:{taky_archive_id:envelope.archive_id,taky_scope:'PRIVATE_USER_DATA_BACKUP'}};
   m.set(id,doc);objectBytes.set(id,blob);
   return reply(doc);
  }
  if(u.pathname==='/drive/v3/files'&&opts.method==='GET'){
   const q=u.searchParams.get('q')||'',wanted=q.match(/taky_archive_id' and value='([^']+)'/)?.[1];
   const found=[...m.values()].filter(x=>x.appProperties?.taky_archive_id===wanted);
   return reply({files:found});
  }
  if(u.pathname.startsWith('/drive/v3/files/')&&opts.method==='GET'){
   const id=decodeURIComponent(u.pathname.split('/').pop());
   if(u.searchParams.get('alt')==='media'){
    assert(objectBytes.has(id));
    return{ok:true,status:200,arrayBuffer:async()=>objectBytes.get(id)};
   }
   assert(m.has(id));
   return reply(m.get(id));
  }
  throw Error('MOCK_DRIVE_UNEXPECTED_REQUEST');
 }
 return {fetchImpl,metadata:m,objectBytes,unblock:()=>{
  m.set(folder.root,{id:folder.root,permissions:owner});
 },stats:()=>({uploads,object_count:objectBytes.size})};
}
(async()=>{
 const dir=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-full-userloop-'));
 let server=null;
 try{
  const store=await new LocalJsonStrongStore(dir).init();
  const started=await launchServer(store);server=started.server;
  const deviceA=browser(started.base,'CHILD_A');
  assert.equal((await deviceA.api.sync()).state,'SYNC_READY');
  deviceA.storage.setItem('readyset_planner_v1',JSON.stringify({
   version:1,assignmentFacts:{HW1:{title:'서버 저장 숙제',subject:'과학',confirmationState:'FACT_CONFIRMED'}},
   days:{'2026-10-14':{tasks:[{id:'H1',title:'서버 저장 숙제',status:'PLANNED'}]}}
  }));
  deviceA.storage.setItem('ready_foundation_v1',JSON.stringify({profiles:[{id:'weekly',revision:7}]}));
  assert.equal((await deviceA.api.sync()).state,'SERVER_ACKNOWLEDGED');
  const identity={family_id:'FAMILY_A',member_id:'CHILD_A',record_type:'PLANNER_SNAPSHOT',record_id:'ready-planner-current-v1'};
  const stored=await UserData.read(store,identity,{authenticated:true,family_id:'FAMILY_A',authorized_member_ids:['CHILD_A']});
  assert.equal(stored.ok,true);
  const pending=await Queue.read(store,stored.record);assert.equal(pending.data.state,'PENDING_VERIFIED_ARCHIVE');
  const fake=fakeDrive();
  const service=Worker.create({store,getSiezeallAccessToken:async()=> 'fake-siezeall-backend-service-token',
   fetchImpl:fake.fetchImpl,encryptionKey:crypto.randomBytes(32),encryptionKeyId:'private-key-v1'});
  assert.equal((await service.processRecord(identity)).reason,'ARCHIVE_PRIVATE_SCOPE_EXPOSED');
  assert.equal(fake.stats().uploads,0);
  fake.unblock();
  const archived=await service.processRecord(identity);
  assert.equal(archived.ok,true,JSON.stringify(archived));
  assert.equal(fake.stats().uploads,1);
  const encrypted=[...fake.objectBytes.values()][0].toString('utf8');
  assert.equal(encrypted.includes('서버 저장 숙제'),false);
  const deviceB=browser(started.base,'CHILD_A');
  assert.equal((await deviceB.api.sync()).state,'SERVER_RESTORED');
  assert.equal(deviceB.read().assignmentFacts.HW1.title,'서버 저장 숙제');
  assert.equal(JSON.parse(deviceB.storage.getItem('ready_foundation_v1')).profiles[0].revision,7);
  const differentChild=browser(started.base,'CHILD_B');
  assert.equal((await differentChild.api.sync()).state,'SYNC_READY');
  assert(!differentChild.read().assignmentFacts,'members must not inherit another learner state');
  console.log('FAMILY_PLANNER_HTTP_TO_SIEZEALL_LOOPBACK_E2E_PASS',JSON.stringify({
   real_loopback_http:true,user_scoped_durable_commit:true,
   archive_work_item:true,unsafe_acl_blocks:true,encryption_and_readback:true,
   second_device_restore:true,second_member_isolation:true,no_live_google_call:true
  }));
 }finally{
  if(server)await new Promise(r=>server.close(r));
  await fsp.rm(dir,{recursive:true,force:true,maxRetries:6,retryDelay:30});
 }
})().catch(e=>{console.error(e);process.exitCode=1});
