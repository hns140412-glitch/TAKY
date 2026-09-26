'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const p=path.join(__dirname,'..','..','CURRENT','LEARNING_ENGINE_DATA_READINESS_CURRENT.json');
const cur=JSON.parse(fs.readFileSync(p,'utf8'));

assert.equal(cur.projection_version,'TAKY_LEARNING_ENGINE_DATA_READINESS_CURRENT_V1');
assert.equal(cur.authority,'LEARNING_ENGINE_CORE');
assert.equal(cur.minimum_verified_retrieval_targets_for_promotion_review,30);
assert.equal(cur.code_path.specialist_event_pipeline,'IMPLEMENTED');
assert.equal(cur.code_path.central_transport_handler,'IMPLEMENTED');
assert.equal(cur.code_path.ready_durable_outbox,'IMPLEMENTED');
assert.equal(cur.code_path.ready_fail_safe_sync,'IMPLEMENTED');
assert.equal(cur.code_path.durable_store_adapter,'IMPLEMENTED');
assert.equal(cur.code_path.transport_auth_policy,'IMPLEMENTED');
assert.equal(cur.code_path.authenticated_transport,'IMPLEMENTED');
assert.equal(cur.code_path.netlify_blobs_transport_adapter,'IMPLEMENTED');
assert.equal(cur.code_path.local_json_strong_store,'IMPLEMENTED_AND_CI_VERIFIED');
assert.equal(cur.code_path.family_member_identity_resolver,'IMPLEMENTED_AND_CI_VERIFIED');
assert.equal(cur.code_path.local_learning_endpoint,'IMPLEMENTED_AND_CI_VERIFIED');

assert.equal(cur.runtime_connection.production_deployment,'HOLD');
assert.equal(cur.runtime_connection.netlify_deployment,'HOLD');
assert.equal(cur.runtime_connection.hosted_central_transport,'ADAPTER_READY_NOT_BOUND');
assert.equal(cur.runtime_connection.local_controlled_persisted_receipt_store,'BOUND_AND_CI_VERIFIED');
assert.equal(cur.runtime_connection.local_controlled_growth_strategy_store,'BOUND_AND_CI_VERIFIED');
assert.equal(cur.runtime_connection.live_persisted_receipt_store,'HOSTED_NOT_MATERIALIZED__LOCAL_CONTROLLED_BOUND');
assert.equal(cur.runtime_connection.live_growth_strategy_store,'HOSTED_ADAPTER_READY_NOT_BOUND__LOCAL_CONTROLLED_BOUND');
assert.equal(cur.runtime_connection.identity_resolver,'PROVIDER_NEUTRAL_LOCAL_CONTROLLED_BOUND__UPSTREAM_AUTH_PROVIDER_NOT_BOUND');
assert.equal(cur.runtime_connection.function_endpoint,'LOCAL_CONTROLLED_BOUND__HOSTED_ENDPOINT_NOT_BOUND');

assert.equal(Array.isArray(cur.scopes),true);
assert.equal(cur.local_controlled_binding_checkpoint.durable_receipt_store,'PASS');
assert.equal(cur.local_controlled_binding_checkpoint.durable_growth_store,'PASS');
assert.equal(cur.local_controlled_binding_checkpoint.persistence_after_reopen,'PASS');
assert.equal(cur.local_controlled_binding_checkpoint.cross_family_write,'DENIED');
assert.equal(cur.local_controlled_binding_checkpoint.cross_member_write,'DENIED');
assert.equal(cur.local_controlled_binding_checkpoint.raw_evidence_copied,false);
assert.equal(cur.local_controlled_binding_checkpoint.promotion_authority,false);
assert.equal(cur.local_controlled_binding_checkpoint.upstream_auth_provider_binding,'OPEN');
assert.equal(cur.local_controlled_binding_checkpoint.hosted_endpoint_binding,'OPEN');

assert.equal(cur.interpretation.some(x=>x.includes('Local-controlled receipt persistence')),true);
assert.equal(cur.interpretation.some(x=>x.includes('cross-family and cross-member packets are denied')),true);
assert.equal(cur.invariants.includes('OBSERVATION_ONLY != VERIFIED_TARGET'),true);
assert.equal(cur.invariants.includes('PROMOTION_READINESS != ESTIMATOR_PROMOTION'),true);
assert.equal(cur.invariants.includes('RAW_EVIDENCE_IMMUTABLE_AND_REFERENCED_BY_RECEIPT'),true);

console.log('LEARNING_ENGINE_DATA_READINESS_CURRENT_PASS');
