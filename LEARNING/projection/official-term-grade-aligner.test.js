'use strict';

const assert=require('node:assert/strict');
const path=require('node:path');
const Aligner=require('./official-term-grade-aligner.js');

const sources=Aligner.loadSources({
  registry_path:path.resolve(__dirname,'..','data','official-snapshots','official-standard-registry-v0.3.0.json'),
  unit_map_path:path.resolve(__dirname,'..','data','official-snapshots','official-unit-map-v0.2.2.json')
});

assert.equal(sources.provenance.registry.version,'0.3.0');
assert.equal(sources.provenance.registry.records,177);
assert.equal(sources.provenance.unit_map.version,'0.2.2');
assert.equal(sources.provenance.unit_map.records,196);

const burn=Aligner.alignTerm({subject:'SCIENCE',term:'연소'},sources);
assert.equal(burn.state,'VERIFIED');
assert.deepEqual(burn.school_stages,['E6']);
assert.ok(burn.evidence.some(x=>x.standard_code==='6과14-02'));

const dissolve=Aligner.alignTerm({subject:'SCIENCE',term:'용해'},sources);
assert.equal(dissolve.state,'VERIFIED');
assert.deepEqual(dissolve.school_stages,['E5']);

const fraction=Aligner.alignTerm({subject:'MATH',term:'분수'},sources);
assert.equal(fraction.state,'VERIFIED');
assert.deepEqual(fraction.school_stages,['E5','E6']);

const coldFront=Aligner.alignTerm({subject:'SCIENCE',term:'한랭전선'},sources);
assert.equal(coldFront.state,'UNALIGNED');
assert.equal(coldFront.reason,'NO_EXACT_OFFICIAL_TERM_SIGNAL');

const photo=Aligner.alignTerm({subject:'SCIENCE',term:'광합성'},sources);
assert.equal(photo.state,'UNALIGNED');

console.log('OFFICIAL_TERM_GRADE_ALIGNER_TEST: PASS');
