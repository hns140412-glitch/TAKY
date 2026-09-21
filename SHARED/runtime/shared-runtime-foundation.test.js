const assert=require('assert');
const release=require('./release-contract.js');
const pwa=require('./pwa-update-state.js');
const eventEnvelope=require('./event-envelope.js');

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
assert.throws(()=>{eventA.payload.a=9;},/read only|Cannot assign|object is not extensible/i);
const tampered={...eventA,payload:{a:9,b:2}};
assert.equal(eventEnvelope.validate(tampered).ok,false);
console.log('PASS: shared immutable event envelope identity is distinct from payload digest');
