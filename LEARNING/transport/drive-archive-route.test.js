'use strict';
const assert=require('node:assert/strict');
const {route,archiveManifest}=require('./drive-archive-route.js');
const drive=['EXTERNAL_REFERENCE_SOURCE','DATA_INDEX_SNAPSHOT',
  'LEARNING_POLICY_SNAPSHOT','LEARNING_RECEIPT_ARCHIVE',
  'BADGE_AWARD_LEDGER_ARCHIVE','FAMILY_GIFT_JOURNAL_ARCHIVE'];
const central=['LEARNING_EVIDENCE_INGEST','LEARNER_STATE_MUTATION',
  'PEDAGOGICAL_DECISION','BADGE_AWARD_TRANSACTION','GEM_WALLET_TRANSACTION',
  'FAMILY_PERMISSION_MUTATION'];
for(const key of drive){
 const r=route(key);assert.equal(r.ok,true);
 assert.equal(r.drive_is_transaction_authority,false);
 assert.equal(r.pwa_is_learning_engine,false);
 assert(r.storage_role.startsWith('GOOGLE_DRIVE'));
}
for(const key of central){
 const r=route(key);assert.equal(r.ok,true);
 assert(!r.storage_role.startsWith('GOOGLE_DRIVE'),key);
 assert.equal(r.pwa_is_learning_engine,false);
}
assert.equal(route('PWA_OFFLINE_OUTBOX').storage_role,'DEVICE_LOCAL_PENDING_SYNC');
assert.equal(route('PLANNER_DATED_ALLOCATION').owner,'PLANNER');
assert.equal(route('SPECIALIST_INTERACTION').owner,'SPECIALIST_PWA');
assert.equal(route('DIRECT_PWA_LEARNING_ENGINE').ok,false);
assert.equal(route('GOOGLE_DRIVE_BADGE_AWARD_TRANSACTION').ok,false);
const digest='a'.repeat(64),checkpoint='b'.repeat(64),scope='c'.repeat(64);
const base={kind:'LEARNING_RECEIPT_ARCHIVE',archive_id:'ARCHIVE-2026-09-26-A',
  source_contract:'REAL_LEARNING_EVIDENCE_RECEIPT',
  source_current_ref:'CURRENT/LEARNING_ENGINE_VERIFICATION_CURRENT_2026-09-25.md',
  source_status:'COMMITTED_AND_VERIFIED',
  content_sha256:digest,source_checkpoint_sha256:checkpoint,
  scope_sha256:scope,encrypted:true};
const exported=archiveManifest(base);
assert.equal(exported.ok,true);
assert.equal(exported.manifest.authoritative_runtime_source,false);
assert.equal(exported.manifest.export_status,'PREPARED_NOT_UPLOADED');
assert.equal(exported.manifest.current_pointer_promotion,
 'AFTER_UPLOAD_HASH_READBACK_AND_RECEIPT_ONLY');
assert(!JSON.stringify(exported).includes('member_id'));
assert(!JSON.stringify(exported).includes('FAMILY_A'));
assert.equal(archiveManifest({...base,encrypted:false}).reason,
 'PRIVATE_ARCHIVE_REQUIRES_ENCRYPTION');
assert.equal(archiveManifest({...base,scope_sha256:null}).reason,
 'PRIVATE_ARCHIVE_REQUIRES_OPAQUE_SCOPE');
assert.equal(archiveManifest({...base,source_status:'WORKING_DRAFT'}).reason,
 'COMMITTED_VERIFIED_SOURCE_REQUIRED');
assert.equal(archiveManifest({...base,content_sha256:'bad'}).reason,
 'ARCHIVE_DIGEST_AND_SOURCE_CHECKPOINT_REQUIRED');
assert.equal(archiveManifest({...base,child_id:'CHILD_A'}).reason,
 'SENSITIVE_OR_RAW_AUTHORITY_FIELDS_FORBIDDEN');
assert.equal(archiveManifest({...base,access_token:'secret'}).reason,
 'SENSITIVE_OR_RAW_AUTHORITY_FIELDS_FORBIDDEN');
assert.equal(archiveManifest({...base,raw_evidence:[1]}).reason,
 'SENSITIVE_OR_RAW_AUTHORITY_FIELDS_FORBIDDEN');
assert.equal(archiveManifest({...base,kind:'BADGE_AWARD_TRANSACTION'}).reason,
 'NOT_A_DRIVE_EXPORT_OPERATION');
assert.equal(archiveManifest({...base,kind:'BADGE_AWARD_LEDGER_ARCHIVE'}).ok,true);
assert.equal(archiveManifest({...base,kind:'FAMILY_GIFT_JOURNAL_ARCHIVE',encrypted:false}).ok,false);
assert.equal(archiveManifest({...base,kind:'DATA_INDEX_SNAPSHOT',encrypted:false,scope_sha256:null}).ok,true);
console.log('LEARNING_DRIVE_ARCHIVE_BOUNDARY_PASS: central Core not PWA; Drive export only; private encryption; immutable hash/readback gate; no live award/wallet');
