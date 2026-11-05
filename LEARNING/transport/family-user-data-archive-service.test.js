'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const fs=require('node:fs').promises,os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const UserData=require('./family-user-data-store.js');
const Queue=require('./family-user-data-archive-outbox.js');
const Publisher=require('./family-user-data-siezeall-archive-publisher.js');
const Service=require('./family-user-data-archive-service.js');
(async()=>{
 const tmp=await fs.mkdtemp(path.join(os.tmpdir(),'taky-drive-rest-service-'));
 try{
  const store=await new LocalJsonStrongStore(tmp).init();
  const input={
   family_id:'F1',member_id:'KID_A',record_type:'PLANNER_SNAPSHOT',record_id:'ready-planner-current-v1',
   status:'CONFIRMED',source_app:'ready-set',payload:{
    planner:{assignmentFacts:{K1:{title:'개인 숙제'},K2:{title:'추가 과제'}}},foundation:{schedule:{}}}
  };
  const principal={authenticated:true,family_id:'F1',authorized_member_ids:['KID_A']};
  const receipt=await UserData.commit(store,input,principal);
  assert(receipt.ok);
  // A previous central crash can leave committed data without outbox.
  // Service must regenerate the exact versioned outbox before publishing.
  const ids=Publisher.ids,owner=[{type:'user',role:'owner',emailAddress:'siezeall@gmail.com'}];
  const meta=new Map([
   [ids.root,{id:ids.root,permissions:[...owner,{type:'anyone',role:'writer'}]}],
   [ids.platform,{id:ids.platform,parents:[ids.root],permissions:owner}],
   [ids.leaf,{id:ids.leaf,parents:[ids.platform],permissions:owner}]
  ]);
  const uploadStore=new Map();
  let httpReads=0,uploadCount=0;
  const fetchImpl=async(url,opt)=>{
   const u=new URL(url);const ok=(json)=>({ok:true,status:200,json:async()=>json,arrayBuffer:async()=>json});
   assert.equal(opt.headers.Authorization,'Bearer test-siezeall-server-access-token-12345');
   if(u.pathname.startsWith('/upload/drive/v3/files')&&opt.method==='POST'){
    uploadCount++;
    const raw=Buffer.from(opt.body);
    const str=raw.toString('utf8');
    const begin=str.lastIndexOf('{"contract":"TAKY_PRIVATE_USER_DATA_ARCHIVE_ENVELOPE_V1"');
    assert(begin>=0,'encrypted bytes must be uploaded');
    const end=str.indexOf('\r\n--taky-',begin);
    const bytes=Buffer.from(str.substring(begin,end),'utf8');
    const encrypted=JSON.parse(bytes.toString('utf8'));
    assert.equal(JSON.stringify(encrypted).includes('개인 숙제'),false);
    const id='SIEZEALLMOCKFILERESULT00000001';
    const doc={id,name:encrypted.archive_id+'.encrypted.json',parents:[ids.leaf],
     mimeType:'application/json',permissions:owner,
     appProperties:{taky_archive_id:encrypted.archive_id,taky_scope:'PRIVATE_USER_DATA_BACKUP'}};
    meta.set(id,doc);uploadStore.set(id,bytes);
    return ok(doc);
   }
   if(u.pathname==='/drive/v3/files'&&opt.method==='GET'){
    const q=u.searchParams.get('q')||'';
    const match=q.match(/taky_archive_id' and value='([^']+)'/);
    assert(match,'archive id needs private appProperties query');
    const files=[...meta.values()].filter(x=>x?.appProperties?.taky_archive_id===match[1]);
    return ok({files});
   }
   if(u.pathname.startsWith('/drive/v3/files/')&&opt.method==='GET'){
    httpReads++;
    const id=decodeURIComponent(u.pathname.split('/').pop());
    if(u.searchParams.get('alt')==='media'){
     const body=uploadStore.get(id);assert(body);
     return {ok:true,status:200,arrayBuffer:async()=>body,json:async()=>null};
    }
    assert(meta.has(id));return ok(meta.get(id));
   }
   throw Error('TEST_UNEXPECTED_GOOGLE_DRIVE_REQUEST:'+u.pathname);
  };
  const key=crypto.randomBytes(32);
  const service=Service.create({store,getSiezeallAccessToken:async()=> 'test-siezeall-server-access-token-12345',
   fetchImpl,encryptionKey:key,encryptionKeyId:'private-key-v1'});
  const blocked=await service.processRecord(input);
  assert.equal(blocked.ok,false);assert.equal(blocked.reason,'ARCHIVE_PRIVATE_SCOPE_EXPOSED');
  assert.equal(uploadCount,0);
  meta.set(ids.root,{id:ids.root,permissions:owner});
  const result=await service.processRecord(input);
  assert.equal(result.ok,true,JSON.stringify(result));
  assert.equal(uploadCount,1);assert.equal(result.receipt.folder_id,ids.leaf);
  assert.equal(result.receipt.content_sha256,crypto.createHash('sha256').update(uploadStore.get(result.receipt.drive_file_id)).digest('hex'));
  const retry=await service.processRecord(input);
  assert.equal(retry.already_archived,true);assert.equal(uploadCount,1);
  assert(httpReads>=3);
  console.log('FAMILY_USER_DATA_ARCHIVE_SERVICE_REST_E2E_PASS',JSON.stringify({
   auth_token_server_only:true,drive_root_acl_blocked:true,
   encrypted_content_written:true,readback_sha256:true,
   correct_route:true,no_duplicate_upload:true,no_real_cloud_calls:true
  }));
 }finally{await fs.rm(tmp,{recursive:true,force:true,maxRetries:6,retryDelay:30});}
})().catch(e=>{console.error(e);process.exitCode=1});
