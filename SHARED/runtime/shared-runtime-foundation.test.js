const assert=require('assert');
const release=require('./release-contract.js');
const pwa=require('./pwa-update-state.js');
const eventEnvelope=require('./event-envelope.js');
const localQueue=require('./local-queue.js');
const vision=require('./vision-ingest.js');
const httpJson=require('./http-json.js');

function descriptor(overrides={}){
  return {
    app_id:'ready-set',
    app_version:'1.0.0',
    runtime_version:'1',
    data_schema_version:5,
    contract_version:1,
    release_id:'ready-set-test-1',
    ...overrides
  };
}

// Release descriptor validation
assert.equal(release.validateDescriptor(descriptor()).ok,true);
assert.equal(release.validateDescriptor({...descriptor(),release_id:''}).ok,false);
assert.equal(
  release.checkCompatibility(descriptor(),descriptor({release_id:'remote'})).state,
  'COMPATIBLE'
);
assert.equal(
  release.checkCompatibility(descriptor(),descriptor({contract_version:2})).state,
  'INCOMPATIBLE_CONTRACT'
);
assert.equal(
  release.checkCompatibility(
    descriptor(),
    descriptor({contract_version:2,release_id:'remote-v2'}),
    {accept_contract_version:{min:1,max:2},accept_data_schema_version:{min:5,max:5}}
  ).state,
  'COMPATIBLE'
);
assert.equal(
  release.checkCompatibility(descriptor(),descriptor({data_schema_version:6})).state,
  'INCOMPATIBLE_SCHEMA'
);

// PWA update lifecycle: no direct activation while merely waiting.
let s='IDLE';
for(const [event,ctx,expected] of [
  ['DETECT',{},'UPDATE_DETECTED'],
  ['DOWNLOAD_COMPLETE',{},'DOWNLOADED_WAITING'],
]){
  const r=pwa.transition(s,event,ctx); assert.equal(r.ok,true); assert.equal(r.state,expected); s=r.state;
}
let r=pwa.transition(s,'ACTIVATE',{safe_point:true});
assert.equal(r.ok,false);
assert.equal(r.state,'DOWNLOADED_WAITING');

r=pwa.transition(s,'EVALUATE_SAFE_POINT',{safe_point:false,reason:'ACTIVE_SESSION'});
assert.equal(r.ok,true);
assert.equal(r.state,'DOWNLOADED_WAITING');

r=pwa.transition(s,'EVALUATE_SAFE_POINT',{safe_point:true});
assert.equal(r.ok,true); assert.equal(r.state,'SAFE_TO_ACTIVATE'); s=r.state;

for(const [event,expected] of [
  ['ACTIVATE','ACTIVATING'],
  ['CONTROLLER_CHANGED','RESTORING'],
  ['RESTORE_COMPLETE','READY'],
  ['SETTLE','IDLE']
]){
  const next=pwa.transition(s,event,{safe_point:true});
  assert.equal(next.ok,true); assert.equal(next.state,expected); s=next.state;
}

console.log('PASS: shared runtime foundation release compatibility and safe PWA state transitions');


const eventA=eventEnvelope.create({
  source:'test-consumer',
  event_type:'OPAQUE_TEST_EVENT',
  payload:{b:2,a:1},
  correlation_id:'corr-1'
});
const eventB=eventEnvelope.create({
  source:'test-consumer',
  event_type:'OPAQUE_TEST_EVENT',
  payload:{a:1,b:2},
  correlation_id:'corr-1'
});
assert.equal(eventEnvelope.validate(eventA).ok,true);
assert.notEqual(eventA.event_id,eventB.event_id);
assert.equal(eventA.payload_digest,eventB.payload_digest);
assert.equal(eventA.idempotency_key,eventA.event_id);
assert.equal(Object.isFrozen(eventA),true);
assert.equal(Object.isFrozen(eventA.payload),true);
eventA.payload.a=9;
assert.equal(eventA.payload.a,1);
const tampered={...eventA,payload:{a:9,b:2}};
assert.equal(eventEnvelope.validate(tampered).ok,false);
console.log('PASS: shared immutable event envelope identity is distinct from payload digest');


const q0=localQueue.create({event_id:'evt-1',idempotency_key:'idem-1',max_attempts:3,created_at:'2026-09-21T00:00:00.000Z'});
assert.equal(localQueue.validate(q0).ok,true);
assert.equal(localQueue.canAttempt(q0,'2026-09-21T00:00:00.000Z'),true);
let qi=localQueue.markInFlight(q0,'2026-09-21T00:00:00.000Z').row;
let qr=localQueue.markRetry(qi,'NETWORK','2026-09-21T00:00:00.000Z',{base_ms:1000,max_ms:8000}).row;
assert.equal(qr.status,'RETRY');
assert.equal(qr.attempts,1);
assert.equal(qr.next_retry_at,'2026-09-21T00:00:01.000Z');
assert.equal(localQueue.canAttempt(qr,'2026-09-21T00:00:00.500Z'),false);
qi=localQueue.markInFlight(qr,'2026-09-21T00:00:01.000Z').row;
qr=localQueue.markRetry(qi,'NETWORK','2026-09-21T00:00:01.000Z',{base_ms:1000,max_ms:8000}).row;
assert.equal(qr.status,'RETRY');
assert.equal(qr.attempts,2);
qi=localQueue.markInFlight(qr,'2026-09-21T00:00:03.000Z').row;
const dead=localQueue.markRetry(qi,'NETWORK','2026-09-21T00:00:03.000Z').row;
assert.equal(dead.status,'DEAD_LETTER');
assert.equal(dead.attempts,3);
const ack=localQueue.markAcked(localQueue.markInFlight(q0,'2026-09-21T00:00:00.000Z').row,{ack_token:'ack-1',remote_version:'v2',now:'2026-09-21T00:00:02.000Z'}).row;
assert.equal(ack.status,'ACKED');
assert.equal(ack.ack_token,'ack-1');
assert.equal(Object.isFrozen(ack),true);
console.log('PASS: shared local queue bounded retry, dead-letter and ack lifecycle');


const manifest=vision.normalizeManifest([
  {source_id:'img-1',mime_type:'image/jpeg',size:100},
  {source_id:'answer-1',mime_type:'image/png',exclude_from_analysis:true}
]);
assert.equal(manifest.ok,true);
assert.equal(manifest.items[0].analyzable,true);
assert.equal(manifest.items[1].analyzable,false);
assert.equal(manifest.items[1].exclusion_reason,'EXPLICITLY_EXCLUDED');
const req=vision.buildRequest({source:'test',manifest:[
  {source_id:'img-1',mime_type:'image/jpeg'},
  {source_id:'img-2',mime_type:'image/webp'}
]});
assert.equal(req.ok,true);
assert.deepEqual([...req.request.analyzable_source_ids],['img-1','img-2']);
const norm=vision.normalizeResult({request_id:req.request.request_id,provider:'test',items:[
  {evidence_source_ids:['img-1'],provider_payload:{opaque:'value'}}
]});
assert.equal(norm.ok,true);
assert.equal(vision.validateEvidence(norm.result,['img-1','img-2']).ok,true);
assert.equal(vision.validateEvidence(norm.result,['img-2']).ok,false);
console.log('PASS: shared vision ingest keeps transport/evidence mechanics separate from domain semantics');


const retrySeconds=httpJson.parseRetryAfter('2',0);
assert.equal(retrySeconds,2000);
const retryDate=httpJson.parseRetryAfter('Thu, 01 Jan 1970 00:00:05 GMT',0);
assert.equal(retryDate,5000);
assert.equal(httpJson.normalizeStatus(200).category,'SUCCESS');
assert.equal(httpJson.normalizeStatus(409).category,'CONFLICT');
assert.equal(httpJson.normalizeStatus(429,{retry_after:'3',now_ms:0}).retry_after_ms,3000);
assert.equal(httpJson.normalizeStatus(503).retryable,true);
assert.equal(httpJson.normalizeStatus(403).category,'AUTH_REJECTED');
const jsonInit=httpJson.buildRequestInit({method:'post',headers:{Accept:'application/json'},body:{x:1}});
assert.equal(jsonInit.method,'POST');
assert.equal(jsonInit.headers['Content-Type'],'application/json');
assert.equal(jsonInit.body,'{"x":1}');
console.log('PASS: shared HTTP transport normalizes request/status/rate-limit mechanics without domain authority');
