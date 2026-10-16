'use strict';
/* Private server worker adapter. Delivers only AES-256-GCM encrypted, versioned
   user records to the existing SIEZEALL 04_USER_DATA location. No live
   uploader/secret is bundled, and unsafe inherited Drive ACLs always HOLD. */
const crypto=require('node:crypto');
const Map=require('../../OS/DRIVE_STORAGE_MAP.json');
const UserData=require('./family-user-data-store.js');
const Queue=require('./family-user-data-archive-outbox.js');
const Envelope=require('./private-user-data-archive-envelope.js');
const Route=require('./drive-archive-route.js');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ns=Map.final_storage_namespace;
const ids=Object.freeze({
 leaf:ns.logical_role_ids.siezeall['04_USER_DATA'],
 platform:ns.siezeall.immediate_children['20_PLATFORM'],
 root:ns.siezeall.root.id
});
const allowedEmail='siezeall@gmail.com';
function safePermissions(metadata,expected,parent=null){
 if(!metadata||metadata.id!==expected||!Array.isArray(metadata.permissions)||!metadata.permissions.length)
  return{ok:false,reason:'ARCHIVE_ACL_READBACK_REQUIRED'};
 if(parent && (!Array.isArray(metadata.parents)||!metadata.parents.includes(parent)))
  return{ok:false,reason:'ARCHIVE_FOLDER_PARENT_MISMATCH'};
 for(const p of metadata.permissions){
  if(!p||!['user','group','domain','anyone'].includes(p.type))
   return{ok:false,reason:'ARCHIVE_ACL_UNKNOWN_GRANT'};
  if(p.type!=='user'||p.emailAddress!==allowedEmail)
   return{ok:false,reason:'ARCHIVE_PRIVATE_SCOPE_EXPOSED'};
  if(!['owner','writer','organizer','fileOrganizer'].includes(p.role))
   return{ok:false,reason:'ARCHIVE_ACL_UNEXPECTED_ROLE'};
 }
 return{ok:true};
}
function create({store,drive,encryptionKey,keyId}={}){
 if(!store?.getWithMetadata||!store?.setJSON)throw Error('ARCHIVE_DURABLE_SOURCE_REQUIRED');
 if(!drive||!['getMetadata','findImmutable','createImmutable','readFileBytes'].every(k=>typeof drive[k]==='function'))
  throw Error('ARCHIVE_AUTHENTICATED_DRIVE_TRANSPORT_REQUIRED');
 if(!Buffer.isBuffer(encryptionKey)||encryptionKey.length!==32)throw Error('ARCHIVE_PRIVATE_KEY_REQUIRED');
 if(!/^[A-Za-z0-9._:-]{1,128}$/.test(String(keyId)))throw Error('ARCHIVE_KEY_ID_REQUIRED');
 async function verifyChain(){
  const records=[
   [ids.root,null],[ids.platform,ids.root],[ids.leaf,ids.platform]
  ];
  for(const [folderId,parent] of records){
   const meta=await drive.getMetadata(folderId);
   const result=safePermissions(meta,folderId,parent);
   if(!result.ok)return result;
  }
  return{ok:true,route_id:ids.leaf};
 }
 async function publish({family_id,member_id,record_type,record_id}={}){
  const scope={family_id,member_id};
  const sourceKey=UserData.keyFor(scope,record_type,record_id);
  if(!sourceKey)return{ok:false,reason:'ARCHIVE_RECORD_ID_INVALID'};
  const snapshot=await store.getWithMetadata(sourceKey,{type:'json',consistency:'strong'});
  if(!snapshot?.etag||snapshot.data?.family_id!==family_id||snapshot.data?.member_id!==member_id)
   return{ok:false,reason:'ARCHIVE_SOURCE_MISSING'};
  const pending=await Queue.read(store,snapshot.data);
  if(!pending||pending.data.source_etag!==snapshot.etag)
   return{ok:false,reason:'ARCHIVE_OUTBOX_SOURCE_NOT_CURRENT'};
  if(pending.data.state==='ARCHIVED_VERIFIED')
   return{ok:true,already_archived:true,receipt:pending.data.last_receipt};
  // No cloud write whatsoever until the complete leaf/ancestor readback passes.
  const acl=await verifyChain();
  if(!acl.ok)return{ok:false,reason:acl.reason,route_id:ids.leaf,cloud_written:false};
  const archive_id='u_'+sha(Buffer.from(sourceKey+'|'+snapshot.etag)).slice(0,48);
  const existing=await drive.findImmutable({folder_id:ids.leaf,archive_id});
  let created=existing, expectedBytes=null;
  if(!existing){
   // Always use a fresh random IV for NEW AES-GCM archives. A retried
   // upload must verify the original immutable ciphertext instead of
   // re-encrypting and comparing incompatible random-IV hashes.
   const sealed=Envelope.seal({plaintext:Buffer.from(JSON.stringify(snapshot.data)),
    encryption_key:encryptionKey,key_id:keyId,archive_id,family_id,member_id});
   if(!sealed.ok)return{ok:false,reason:sealed.reason};
   expectedBytes=sealed.serialized;
   created=await drive.createImmutable({
    folder_id:ids.leaf,name:archive_id+'.encrypted.json',mime_type:'application/json',
    archive_id,bytes:expectedBytes
   });
  }
  if(!created?.id)return{ok:false,reason:'ARCHIVE_CLOUD_UPLOAD_UNCONFIRMED'};
  const object=await drive.getMetadata(created.id);
  const child=safePermissions(object,created.id,ids.leaf);
  if(!child.ok)return{ok:false,reason:child.reason,cloud_written:!existing};
  const actual=await drive.readFileBytes(created.id);
  if(!Buffer.isBuffer(actual)||(expectedBytes&&sha(actual)!==sha(expectedBytes)))
   return{ok:false,reason:'ARCHIVE_CLOUD_HASH_READBACK_MISMATCH',cloud_written:!existing};
  let envelope;
  try{envelope=JSON.parse(actual.toString('utf8'))}catch{
   return{ok:false,reason:'ARCHIVE_CLOUD_ENVELOPE_INVALID'};
  }
  if(envelope.archive_id!==archive_id||envelope.key_id!==keyId)
   return{ok:false,reason:'ARCHIVE_CLOUD_SOURCE_IDENTITY_MISMATCH'};
  const opened=Envelope.open({envelope,encryption_key:encryptionKey});
  if(!opened.ok||sha(opened.plaintext)!==sha(Buffer.from(JSON.stringify(snapshot.data))))
   return{ok:false,reason:'ARCHIVE_CLOUD_PLAINTEXT_MISMATCH'};
  const cloudSha=sha(actual);
  const manifest=Route.archiveManifest({
   kind:'USER_DATA_RECORD_ARCHIVE',archive_id,
   source_contract:snapshot.data.schema,source_current_ref:'CENTRAL_USER_DATA_COMMIT_RECEIPT',
   source_status:'COMMITTED_AND_VERIFIED',
   content_sha256:cloudSha,
   source_checkpoint_sha256:pending.data.source_checkpoint_sha256,
   scope_sha256:envelope.scope_sha256,encrypted:true
  });
  if(!manifest.ok)return{ok:false,reason:manifest.reason};
  // Readback is bound to the SAME source ETag; a concurrent newer record
  // cannot be marked archived by a stale worker.
  const now=await store.getWithMetadata(sourceKey,{type:'json',consistency:'strong'});
  if(now?.etag!==snapshot.etag)return{ok:false,reason:'ARCHIVE_SOURCE_SUPERSEDED'};
  const receipt={archive_id,drive_file_id:created.id,folder_id:ids.leaf,
   content_sha256:cloudSha,source_etag:snapshot.etag,
   verified_at:new Date().toISOString(),manifest:manifest.manifest};
  const result=await Queue.markPublished(store,snapshot.data,snapshot.etag,receipt);
  return result.ok?{ok:true,receipt}:{ok:false,reason:result.reason};
 }
 return Object.freeze({publish,verifyChain,route_id:ids.leaf});
}
module.exports=Object.freeze({create,ids,safePermissions});
