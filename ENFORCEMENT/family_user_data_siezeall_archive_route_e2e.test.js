'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {LocalJsonStrongStore}=require('../LEARNING/transport/local-json-strong-store.js');
const UserData=require('../LEARNING/transport/family-user-data-store.js');
const ArchiveQueue=require('../LEARNING/transport/family-user-data-archive-outbox.js');
const Archive=require('../LEARNING/transport/family-user-data-siezeall-archive-publisher.js');
const Envelope=require('../LEARNING/transport/private-user-data-archive-envelope.js');
const owner={authenticated:true,family_id:'F1',authorized_member_ids:['KID_A']};
const record={family_id:'F1',member_id:'KID_A',record_type:'PLANNER_SNAPSHOT',record_id:'ready-planner-current-v1',
 source_app:'ready-set',status:'CONFIRMED',recorded_at:new Date().toISOString(),
 payload:{planner:{assignmentFacts:{A:{title:'가족 기밀 숙제'}}},foundation:{profiles:[]}}};
const permissions=[{type:'user',role:'owner',emailAddress:'siezeall@gmail.com'}];
(async()=>{
 const folder=await fs.mkdtemp(path.join(os.tmpdir(),'taky-archive-store-'));
 try{
  const store=await new LocalJsonStrongStore(folder).init();
  const saved=await UserData.commit(store,record,owner);
  assert.equal(saved.ok,true);
  const queued=await ArchiveQueue.queue(store,saved.record,saved.etag);
  assert.equal(queued.ok,true);
  const objects=new Map();
  let uploads=0;
  const metadata=new Map([
   [Archive.ids.root,{id:Archive.ids.root,permissions}],
   [Archive.ids.platform,{id:Archive.ids.platform,parents:[Archive.ids.root],permissions}],
   [Archive.ids.leaf,{id:Archive.ids.leaf,parents:[Archive.ids.platform],permissions}]
  ]);
  const drive={
   async getMetadata(id){return metadata.get(id)||null},
   async findImmutable({archive_id}){return [...objects.values()].find(x=>x.archive_id===archive_id)||null},
   async createImmutable({folder_id,archive_id,bytes}){
    uploads++;const id='uploaded-'+uploads;
    objects.set(id,{id,archive_id,folder_id,bytes:Buffer.from(bytes)});
    metadata.set(id,{id,parents:[folder_id],permissions});
    return{id};
   },
   async readFileBytes(id){return Buffer.from(objects.get(id).bytes)}
  };
  const key=crypto.randomBytes(32);
  const publisher=Archive.create({store,drive,encryptionKey:key,keyId:'family-key-v1'});
  metadata.set(Archive.ids.leaf,{id:Archive.ids.leaf,parents:[Archive.ids.platform],permissions:[{type:'anyone',role:'writer'},...permissions]});
  let result=await publisher.publish(record);
  assert.equal(result.ok,false);
  assert.equal(result.reason,'ARCHIVE_PRIVATE_SCOPE_EXPOSED');
  assert.equal(uploads,0,'unsafe Google Drive ACL must prevent all uploads');
  metadata.set(Archive.ids.leaf,{id:Archive.ids.leaf,parents:[Archive.ids.platform],permissions});
  metadata.set(Archive.ids.root,{id:Archive.ids.root,permissions:[{type:'anyone',role:'reader'},...permissions]});
  result=await publisher.publish(record);
  assert.equal(result.reason,'ARCHIVE_PRIVATE_SCOPE_EXPOSED');
  assert.equal(uploads,0,'unsafe ancestor must also block');
  metadata.set(Archive.ids.root,{id:Archive.ids.root,permissions});
  assert.equal((await publisher.verifyChain()).ok,true);
  result=await publisher.publish(record);
  assert.equal(result.ok,true,JSON.stringify(result));
  assert.equal(uploads,1);
  const bytes=objects.get(result.receipt.drive_file_id).bytes;
  const json=bytes.toString('utf8');
  assert.equal(json.includes('가족 기밀 숙제'),false,'Drive must receive ciphertext, not homework plaintext');
  assert.equal(json.includes('KID_A'),false,'member id not in envelope');
  const opened=Envelope.open({envelope:JSON.parse(json),encryption_key:key});
  assert.equal(opened.ok,true);
  assert.equal(JSON.parse(opened.plaintext.toString('utf8')).payload.planner.assignmentFacts.A.title,'가족 기밀 숙제');
  const repeat=await publisher.publish(record);
  assert.equal(repeat.already_archived,true);
  assert.equal(uploads,1);
  const outbox=await ArchiveQueue.read(store,record);
  assert.equal(outbox.data.state,'ARCHIVED_VERIFIED');
  assert.equal(outbox.data.last_receipt.folder_id,Archive.ids.leaf);
  // New source version invalidates previous archive receipt and queues a fresh encrypted revision.
  const changed={...record,payload:{planner:{assignmentFacts:{A:{title:'숙제 수정됨'}}},foundation:{profiles:[]}}};
  const update=await UserData.commit(store,changed,owner,{expected_etag:saved.etag});
  assert.equal(update.ok,true);
  assert.equal((await ArchiveQueue.queue(store,update.record,update.etag)).ok,true);
  let droppedReceiptOnce=false;
  const failAfterUpload={
   getWithMetadata:(...args)=>store.getWithMetadata(...args),
   setJSON:(key,value,opts)=>{
    if(!droppedReceiptOnce&&value?.state==='ARCHIVED_VERIFIED'){
     droppedReceiptOnce=true;
     return Promise.resolve({modified:false});
    }
    return store.setJSON(key,value,opts);
   }
  };
  const crashedPublisher=Archive.create({store:failAfterUpload,drive,encryptionKey:key,keyId:'family-key-v1'});
  const interrupted=await crashedPublisher.publish(changed);
  assert.equal(interrupted.ok,false,'missing post-upload receipt must remain retryable');
  assert.equal(uploads,2);
  result=await publisher.publish(changed);
  assert.equal(result.ok,true,'retry must accept immutable ciphertext encrypted with earlier random IV');
  assert.equal(uploads,2,'retry must not upload duplicate encrypted source');
  console.log('FAMILY_USER_DATA_SIEZEALL_ARCHIVE_E2E_PASS',JSON.stringify({
   real_route_id:Archive.ids.leaf,public_writer_blocked:true,parent_public_access_blocked:true,
   encrypted_only:true,remote_byte_readback:true,versioned_revision:true,idempotent_upload:true
  }));
 }finally{await fs.rm(folder,{recursive:true,force:true,maxRetries:5,retryDelay:30});}
})().catch(e=>{console.error(e);process.exitCode=1});
