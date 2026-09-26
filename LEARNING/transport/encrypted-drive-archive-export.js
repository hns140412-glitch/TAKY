'use strict';

/**
 * Secondary encrypted, versioned Drive export. This is a provider-injected
 * adapter, NOT a Drive SDK, automatic upload, live Learning Engine state,
 * index authority or receipt issuer. It may run only in a provisioned server
 * after reading a committed and digest-verified central source. No PWA token
 * or child plaintext enters Drive. Archive/index failure never rolls back or
 * fabricates the already-issued central learning receipt.
 */
const crypto=require('node:crypto');
const Route=require('./drive-archive-route.js');
const VERSION='TAKY_ENCRYPTED_DRIVE_ARCHIVE_READBACK_V1';
const SHA=/^[0-9a-f]{64}$/;
const clean=x=>typeof x==='string'?x.trim():'';
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=b=>Buffer.isBuffer(b)||b instanceof Uint8Array;

function create({readVerifiedSource,keyProvider,driveProvider,indexSink,folderId}={}){
 if(typeof readVerifiedSource!=='function'||typeof keyProvider!=='function'||
    typeof driveProvider?.uploadVersioned!=='function'||
    typeof driveProvider?.readFileBytes!=='function'||
    typeof indexSink?.appendVerifiedDelta!=='function'||
    !clean(folderId))throw Error('AUTHORIZED_ARCHIVE_SOURCE_KEY_DRIVE_INDEX_PROVIDERS_REQUIRED');
 async function exportOnce(meta={}){
   if(!clean(meta.archive_id)||!SHA.test(meta.source_checkpoint_sha256||''))
     return {ok:false,reason:'VERSIONED_SOURCE_CHECKPOINT_REQUIRED'};
   const source=await readVerifiedSource(meta);
   if(source?.status!=='COMMITTED_AND_VERIFIED'||!bytes(source.bytes))
     return {ok:false,reason:'TRUSTED_COMMITTED_SOURCE_REQUIRED'};
   const plaintext=Buffer.from(source.bytes);
   const sourceHash=digest(plaintext);
   if(sourceHash!==meta.source_checkpoint_sha256)
     return {ok:false,reason:'SOURCE_CHECKPOINT_HASH_MISMATCH'};
   const keyRecord=await keyProvider({purpose:'TAKY_DRIVE_ENCRYPTED_ARCHIVE'});
   if(!clean(keyRecord?.key_id)||!bytes(keyRecord?.key_bytes)||
      keyRecord.key_bytes.length!==32)
     return {ok:false,reason:'SERVER_MANAGED_AES_256_KEY_REQUIRED'};
   const key=Buffer.from(keyRecord.key_bytes);
   let exported;
   try{
     const iv=crypto.randomBytes(12);
     const cipher=crypto.createCipheriv('aes-256-gcm',key,iv);
     const cipherText=Buffer.concat([cipher.update(plaintext),cipher.final()]);
     const envelope={
       envelope_version:VERSION,algorithm:'AES-256-GCM',
       key_id:keyRecord.key_id,archive_id:meta.archive_id,
       source_sha256:sourceHash,
       iv_base64:iv.toString('base64'),
       auth_tag_base64:cipher.getAuthTag().toString('base64'),
       ciphertext_base64:cipherText.toString('base64')
     };
     exported=Buffer.from(JSON.stringify(envelope),'utf8');
   }finally{key.fill(0)}
   const contentHash=digest(exported);
   const prepared=Route.archiveManifest({
     kind:meta.kind,archive_id:meta.archive_id,
     source_contract:meta.source_contract,
     source_current_ref:meta.source_current_ref,
     source_status:'COMMITTED_AND_VERIFIED',
     source_checkpoint_sha256:sourceHash,
     content_sha256:contentHash,encrypted:true,
     scope_sha256:meta.scope_sha256
   });
   if(!prepared.ok)return prepared;
   const filename=meta.archive_id+'.'+sourceHash.slice(0,16)+'.enc.json';
   // The provider MUST implement create-only/versioned upload in the already
   // authorized Drive folder; never overwrite a raw/source/current file.
   const uploaded=await driveProvider.uploadVersioned({
     folder_id:folderId,name:filename,
     bytes:exported,mime_type:'application/json'
   });
   if(!clean(uploaded?.file_id))
     return {ok:false,reason:'DRIVE_UPLOAD_NOT_CONFIRMED'};
   const readback=await driveProvider.readFileBytes({file_id:uploaded.file_id});
   if(!bytes(readback)||digest(Buffer.from(readback))!==contentHash)
     return {ok:false,reason:'DRIVE_READBACK_HASH_MISMATCH',
       stage:'UNVERIFIED_ARCHIVE_NOT_INDEXED',file_id:uploaded.file_id};
   // Indexed only AFTER ciphertext readback hash matches source-bound manifest.
   const index=await indexSink.appendVerifiedDelta({
     kind:meta.kind,archive_id:meta.archive_id,
     drive_file_id:uploaded.file_id,source_checkpoint_sha256:sourceHash,
     content_sha256:contentHash,manifest:prepared.manifest
   });
   if(index?.ok!==true||index.archive_id!==meta.archive_id||
      index.drive_file_id!==uploaded.file_id||index.content_sha256!==contentHash)
     return {ok:false,reason:'INDEX_DELTA_PENDING',
       stage:'READBACK_VERIFIED_INDEX_PENDING',file_id:uploaded.file_id,
       content_sha256:contentHash};
   return {ok:true,version:VERSION,manifest:prepared.manifest,
     archive_receipt:{status:'READBACK_VERIFIED_AND_INDEXED',
       archive_id:meta.archive_id,file_id:uploaded.file_id,
       content_sha256:contentHash,source_checkpoint_sha256:sourceHash,
       key_id:keyRecord.key_id,index_acknowledged:true,
       central_learning_receipt_unchanged:true,drive_is_runtime_authority:false}};
 }
 return Object.freeze({version:VERSION,exportOnce});
}
module.exports=Object.freeze({VERSION,create});
