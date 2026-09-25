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
assert.equal(cur.runtime_connection.production_deployment,'HOLD');
assert.equal(cur.runtime_connection.netlify_deployment,'HOLD');
assert.equal(cur.runtime_connection.hosted_central_transport,'ADAPTER_READY_NOT_BOUND');
assert.equal(cur.runtime_connection.identity_resolver,'NOT_CONNECTED');
assert.equal(cur.runtime_connection.function_endpoint,'NOT_BOUND');
assert.equal(Array.isArray(cur.scopes),true);
assert.equal(cur.interpretation.some(x=>x.includes('does not mean the learner has zero evidence')),true);
assert.equal(cur.invariants.includes('OBSERVATION_ONLY != VERIFIED_TARGET'),true);
assert.equal(cur.invariants.includes('PROMOTION_READINESS != ESTIMATOR_PROMOTION'),true);

console.log('LEARNING_ENGINE_DATA_READINESS_CURRENT_PASS');
