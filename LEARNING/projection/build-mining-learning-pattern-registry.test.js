'use strict';

const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const Projector=require('./build-mining-learning-pattern-registry.js');

const result=Projector.build();
const projected=new Map(result.receipt.projected.map(x=>[x.source_id,x]));
assert.equal(result.registry.schema,'TAKY_LEARNING_REFERENCE_PATTERN_REGISTRY_V2');
assert.equal(result.receipt.summary.indexed_learning_refs,9);
assert.equal(result.receipt.summary.runtime_pattern_refs,2);
assert.equal(result.receipt.summary.discovery_only_refs,1);
assert.equal(result.receipt.summary.held_unmapped_refs,6);

assert.deepEqual(
  projected.get('REF-081').patterns.slice().sort(),
  ['P_ERROR_TO_CONCEPT_GAP','P_VISUAL_CONCEPT_CARD'].sort()
);
assert.deepEqual(
  projected.get('REF-085').patterns.slice().sort(),
  ['P_BLANK_RECALL','P_CONCEPT_GRAPH','P_VISUAL_CONCEPT_CARD'].sort()
);
assert.ok(result.receipt.discovery_only.some(x=>x.source_id==='REF-084'));
assert.ok(result.receipt.held_unmapped.some(x=>x.source_id==='REF-068'));

const registry=JSON.parse(fs.readFileSync(path.resolve(__dirname,'..','data','mining-learning-pattern-registry-v1.json'),'utf8'));
assert.ok(registry.sources.some(x=>x.source_id==='MINED:EDU_NAVI:TERM_DECODER_INTRO'));
assert.ok(registry.sources.some(x=>x.source_id==='REF-081'));
assert.ok(registry.sources.some(x=>x.source_id==='REF-085'));
assert.equal(registry.sources.some(x=>x.source_id==='REF-084'),false);

console.log('MINING_LEARNING_PATTERN_PROJECTOR_TEST: PASS');
console.log(JSON.stringify(result.receipt.summary,null,2));
