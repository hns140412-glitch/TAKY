'use strict';

/**
 * Storage/authority ROUTING contract, not a Drive SDK or a new Learning Engine.
 * Central Learning Engine Core remains the domain authority. The PWA is the
 * interaction/offline-outbox client. Drive is an archive/reference/index source,
 * NEVER the live achievement or learner-state transaction processor.
 */
const VERSION='TAKY_LEARNING_DRIVE_STORAGE_ROUTE_V1';
const ROUTES=Object.freeze({
  EXTERNAL_REFERENCE_SOURCE:['MINING_INDEXING','GOOGLE_DRIVE_SOURCE_ARCHIVE'],
  DATA_INDEX_SNAPSHOT:['INDEXING','GOOGLE_DRIVE_VERSIONED_PROJECTION'],
  LEARNING_POLICY_SNAPSHOT:['TAKY_LEARNING_ENGINE_CORE','GOOGLE_DRIVE_VERSIONED_ARCHIVE'],
  LEARNING_RECEIPT_ARCHIVE:['TAKY_LEARNING_ENGINE_CORE','GOOGLE_DRIVE_ENCRYPTED_ARCHIVE'],
  BADGE_AWARD_LEDGER_ARCHIVE:['BADGE_AWARD_LEDGER','GOOGLE_DRIVE_ENCRYPTED_ARCHIVE'],
  FAMILY_GIFT_JOURNAL_ARCHIVE:['FAMILY_GIFT_JOURNAL','GOOGLE_DRIVE_ENCRYPTED_ARCHIVE'],
  PWA_OFFLINE_OUTBOX:['SPECIALIST_PWA','DEVICE_LOCAL_PENDING_SYNC'],
  SPECIALIST_INTERACTION:['SPECIALIST_PWA','DEVICE_LOCAL_INTERACTION'],
  LEARNING_EVIDENCE_INGEST:['TAKY_LEARNING_ENGINE_CORE','CENTRAL_AUTHENTICATED_EVIDENCE_STORE'],
  LEARNER_STATE_MUTATION:['TAKY_LEARNING_ENGINE_CORE','CENTRAL_VERIFIED_STATE_STORE'],
  PEDAGOGICAL_DECISION:['TAKY_LEARNING_ENGINE_CORE','CENTRAL_DOMAIN_EXECUTION'],
  PLANNER_DATED_ALLOCATION:['PLANNER','PLANNER_AUTHORITATIVE_STATE'],
  BADGE_AWARD_TRANSACTION:['BADGE_AWARD_LEDGER','CENTRAL_ATOMIC_TRANSACTION_STORE'],
  GEM_WALLET_TRANSACTION:['GEM_WALLET','CENTRAL_ATOMIC_TRANSACTION_STORE'],
  FAMILY_PERMISSION_MUTATION:['FAMILY_AUTH_PROVIDER','SERVER_ONLY_PERMISSION_STORE']
});
const DRIVE_EXPORT=new Set([
  'DATA_INDEX_SNAPSHOT','LEARNING_POLICY_SNAPSHOT','LEARNING_RECEIPT_ARCHIVE',
  'BADGE_AWARD_LEDGER_ARCHIVE','FAMILY_GIFT_JOURNAL_ARCHIVE'
]);
const ENCRYPTED=new Set([
  'LEARNING_RECEIPT_ARCHIVE','BADGE_AWARD_LEDGER_ARCHIVE',
  'FAMILY_GIFT_JOURNAL_ARCHIVE'
]);
const clean=v=>typeof v==='string'?v.trim():'';
const SHA=/^[0-9a-f]{64}$/;
function route(operation){
  const row=ROUTES[operation];
  if(!row)return {ok:false,reason:'UNRECOGNIZED_STORAGE_OPERATION'};
  return {ok:true,contract:VERSION,operation,owner:row[0],storage_role:row[1],
    drive_is_transaction_authority:false,
    pwa_is_learning_engine:false};
}
/**
 * Pure archive manifest builder; the caller must implement an authorized,
 * versioned Drive upload AFTER a real committed/source-verified transaction.
 * No member names, raw evidence, OAuth token or unencrypted child data may be
 * supplied to this manifest.
 */
function archiveManifest(input={}){
  const kind=input.kind;
  if(!DRIVE_EXPORT.has(kind))return {ok:false,reason:'NOT_A_DRIVE_EXPORT_OPERATION'};
  if(input.source_status!=='COMMITTED_AND_VERIFIED')
    return {ok:false,reason:'COMMITTED_VERIFIED_SOURCE_REQUIRED'};
  if(!SHA.test(input.content_sha256)||!SHA.test(input.source_checkpoint_sha256))
    return {ok:false,reason:'ARCHIVE_DIGEST_AND_SOURCE_CHECKPOINT_REQUIRED'};
  if(!clean(input.archive_id)||input.archive_id.length>128||
     !clean(input.source_contract)||input.source_contract.length>128||
     !clean(input.source_current_ref)||input.source_current_ref.length>256)
    return {ok:false,reason:'VERSIONED_SOURCE_IDENTITY_REQUIRED'};
  if(ENCRYPTED.has(kind)&&input.encrypted!==true)
    return {ok:false,reason:'PRIVATE_ARCHIVE_REQUIRES_ENCRYPTION'};
  if(ENCRYPTED.has(kind)&&!SHA.test(input.scope_sha256))
    return {ok:false,reason:'PRIVATE_ARCHIVE_REQUIRES_OPAQUE_SCOPE'};
  if(['access_token','refresh_token','member_id','child_id','family_id','raw_evidence',
       'oauth_token','password','secret','signing_key'].some(k=>Object.hasOwn(input,k)))
    return {ok:false,reason:'SENSITIVE_OR_RAW_AUTHORITY_FIELDS_FORBIDDEN'};
  const manifest={
    contract:'TAKY_DRIVE_ARCHIVE_MANIFEST_V1',
    archive_kind:kind,
    archive_id:input.archive_id,
    source_contract:input.source_contract,
    source_current_ref:input.source_current_ref,
    source_status:'COMMITTED_AND_VERIFIED',
    content_sha256:input.content_sha256,
    source_checkpoint_sha256:input.source_checkpoint_sha256,
    encrypted:input.encrypted===true,
    ...(ENCRYPTED.has(kind)?{scope_sha256:input.scope_sha256}:{}),
    drive_role:'SECONDARY_VERSIONED_EXPORT',
    export_status:'PREPARED_NOT_UPLOADED',
    authoritative_runtime_source:false,
    current_pointer_promotion:'AFTER_UPLOAD_HASH_READBACK_AND_RECEIPT_ONLY'
  };
  return {ok:true,manifest};
}
module.exports=Object.freeze({VERSION,route,archiveManifest,ROUTES});
