'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const Envelope=require('../LEARNING/transport/private-user-data-archive-envelope.js');
const Drive=require('../LEARNING/transport/drive-archive-route.js');

const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
const key=crypto.randomBytes(32);
const record={
  schema:'TAKY_FAMILY_USER_DATA_RECORD_V1',
  family_id:'FAMILY_PRIVATE_TEST',
  member_id:'CHILD_PRIVATE_TEST',
  record_type:'ASSIGNMENT',
  record_id:'HW-BACKUP-1',
  status:'CONFIRMED',
  payload:{title:'Private homework',subject:'Science',task_id:'T1',note:'private note'},
  recorded_at:'2026-10-07T13:00:00.000Z',
  updated_at:'2026-10-07T13:00:00.000Z'
};
const plaintext=Buffer.from(JSON.stringify(record),'utf8');
const sealed=Envelope.seal({
  plaintext,encryption_key:key,key_id:'FAMILY-KEY-V1',archive_id:'USERDATA-HW-BACKUP-1-V1',
  family_id:record.family_id,member_id:record.member_id
});
assert.equal(sealed.ok,true);
assert.equal(sealed.envelope.algorithm,'AES-256-GCM');
assert.equal(sealed.envelope.scope_sha256.length,64);
const encoded=sealed.serialized.toString('utf8');
assert.equal(encoded.includes(record.family_id),false);
assert.equal(encoded.includes(record.member_id),false);
assert.equal(encoded.includes('private note'),false);

const opened=Envelope.open({envelope:sealed.envelope,encryption_key:key});
assert.equal(opened.ok,true);
assert.deepEqual(JSON.parse(opened.plaintext.toString('utf8')),record);
assert.equal(Envelope.open({envelope:sealed.envelope,encryption_key:crypto.randomBytes(32)}).ok,false);

const checkpoint=sha(Buffer.from('committed-etag:ETAG-1','utf8'));
const manifest=Drive.archiveManifest({
  kind:'USER_DATA_RECORD_ARCHIVE',
  archive_id:'USERDATA-HW-BACKUP-1-V1',
  source_contract:'TAKY_FAMILY_USER_DATA_RECORD_V1',
  source_current_ref:'CENTRAL_USER_DATA_COMMIT_RECEIPT',
  source_status:'COMMITTED_AND_VERIFIED',
  content_sha256:sealed.content_sha256,
  source_checkpoint_sha256:checkpoint,
  scope_sha256:sealed.envelope.scope_sha256,
  encrypted:true
});
assert.equal(manifest.ok,true);
assert.equal(manifest.manifest.drive_role,'SECONDARY_VERSIONED_EXPORT');
assert.equal(manifest.manifest.current_pointer_promotion,'AFTER_UPLOAD_HASH_READBACK_AND_RECEIPT_ONLY');
assert.equal(JSON.stringify(manifest).includes(record.family_id),false);
assert.equal(JSON.stringify(manifest).includes(record.member_id),false);
assert.equal(Drive.archiveManifest({...manifest.manifest,kind:'USER_DATA_RECORD_ARCHIVE',source_status:'COMMITTED_AND_VERIFIED',encrypted:false}).ok,false);

console.log('FAMILY_USER_DATA_PRIVATE_BACKUP_E2E_PASS');
console.log(JSON.stringify({
  aes_256_gcm:true,opaque_member_scope:true,round_trip_verified:true,
  wrong_key_denied:true,drive_manifest_ready:true,
  drive_upload_status:'BLOCKED_UNTIL_PRIVATE_PERMISSION_AND_HASH_READBACK'
}));
