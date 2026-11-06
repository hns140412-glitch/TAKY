'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const Export=require('./encrypted-drive-archive-export.js');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=Buffer.from(JSON.stringify({
 receipt:'central-verified-receipt-fixture',data:'private learner evidence',
 version:2
}));
const meta={
 kind:'LEARNING_RECEIPT_ARCHIVE',archive_id:'opaque-archive-001',
 source_contract:'TAKY_REAL_EVIDENCE_RECEIPT_V1',
 source_current_ref:'CURRENT/LEARNING_ENGINE_VERIFICATION_CURRENT_2026-09-25.md',
 source_checkpoint_sha256:sha(source),
 scope_sha256:sha(Buffer.from('test-only-opaque-scope'))
};
(async()=>{
 const files=new Map(),key=crypto.randomBytes(32);let uploadCount=0,indexCount=0;
 const sourceProvider=async()=>({status:'COMMITTED_AND_VERIFIED',bytes:source});
 const keyProvider=async()=>({key_id:'fixture-key-v1',key_bytes:key});
 const driveProvider={
  async uploadVersioned({folder_id,name,bytes,mime_type}){
   assert.equal(folder_id,'EXISTING_APPROVED_ARCHIVE_FOLDER');
   assert(name.endsWith('.enc.json'));
   assert.equal(mime_type,'application/json');
   const file_id='fixture-version-'+(++uploadCount);
   files.set(file_id,Buffer.from(bytes));return {file_id};
  },
  async readFileBytes({file_id}){return files.get(file_id)}
 };
 const indexSink={async appendVerifiedDelta(row){
  indexCount++;return {ok:true,archive_id:row.archive_id,
   drive_file_id:row.drive_file_id,content_sha256:row.content_sha256}
 }};
 const create=(drive=driveProvider,index=indexSink,read=sourceProvider)=>Export.create({
  readVerifiedSource:read,keyProvider,driveProvider:drive,indexSink:index,
  folderId:'EXISTING_APPROVED_ARCHIVE_FOLDER'
 });
 const success=await create().exportOnce(meta);
 assert.equal(success.ok,true,JSON.stringify(success));
 assert.equal(success.archive_receipt.status,'READBACK_VERIFIED_AND_INDEXED');
 assert.equal(success.archive_receipt.drive_is_runtime_authority,false);
 assert.equal(indexCount,1);
 const raw=files.get(success.archive_receipt.file_id);
 assert(!raw.toString('utf8').includes('private learner evidence'));
 assert.equal(sha(raw),success.archive_receipt.content_sha256);
 const envelope=JSON.parse(raw.toString('utf8'));
 assert.equal(envelope.algorithm,'AES-256-GCM');
 const decipher=crypto.createDecipheriv('aes-256-gcm',key,Buffer.from(envelope.iv_base64,'base64'));
 decipher.setAuthTag(Buffer.from(envelope.auth_tag_base64,'base64'));
 const recovered=Buffer.concat([
  decipher.update(Buffer.from(envelope.ciphertext_base64,'base64')),decipher.final()]);
 assert.deepEqual(recovered,source);
 const mismatched=await create().exportOnce({
  ...meta,source_checkpoint_sha256:'0'.repeat(64)
 });
 assert.equal(mismatched.reason,'SOURCE_CHECKPOINT_HASH_MISMATCH');
 assert.equal(indexCount,1);
 const corruptDrive={
  ...driveProvider,
  async readFileBytes(){return Buffer.from('tampered ciphertext')}
 };
 const tamper=await create(corruptDrive).exportOnce(meta);
 assert.equal(tamper.reason,'DRIVE_READBACK_HASH_MISMATCH');
 assert.equal(indexCount,1);
 const failedIndex=await create(driveProvider,{
  async appendVerifiedDelta(){return {ok:false}}
 }).exportOnce(meta);
 assert.equal(failedIndex.reason,'INDEX_DELTA_PENDING');
 assert.equal(failedIndex.stage,'READBACK_VERIFIED_INDEX_PENDING');
 assert.equal(failedIndex.ok,false);
 assert.throws(()=>Export.create({}),/AUTHORIZED_ARCHIVE_SOURCE_KEY_DRIVE_INDEX_PROVIDERS_REQUIRED/);
 assert.equal(key.length,32);
 console.log('ENCRYPTED_DRIVE_ARCHIVE_EXPORT_PASS: AES-256-GCM ciphertext only; source digest gate; hash readback gate; tamper blocks index; failed index retained pending; fixture providers only');
})().catch(e=>{console.error(e);process.exitCode=1});
