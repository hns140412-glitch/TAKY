'use strict';
const assert=require('node:assert/strict');
const C=require('./crew-registry.js');

const r=C.defaultRegistry('CHILD_A');
assert.equal(r.roster_ceiling,20);
assert.deepEqual(r.roster.map(x=>x.canonical_name),['두비','로리','잉크','노바','테이크','제로']);
assert.equal(r.primary_companion_id,null);

const selected=C.selectPrimary(r,'crew.core.ink');
assert.equal(selected.ok,true);
assert.equal(C.primary(selected.registry).canonical_name,'잉크');

const renamed=C.rename(selected.registry,'crew.core.ink','잉키','2026-09-25T00:00:00.000Z');
assert.equal(renamed.ok,true);
assert.equal(C.primary(renamed.registry).display_name,'잉키');
assert.equal(C.primary(renamed.registry).name_history[0].name,'잉크');

assert.equal(C.selectPrimary(r,'crew.unknown').ok,false);
assert.equal(C.CORE6.length,6);

console.log('TAKY_CREW_REGISTRY_V1_PASS');
