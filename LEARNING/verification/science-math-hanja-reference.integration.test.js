'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const universe=JSON.parse(fs.readFileSync(path.join(root,'data','prelearned','subject-term-universe-56-v1.json'),'utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join(root,'data','prelearned','prelearned-term-universe-manifest-v1.json'),'utf8'));
const byKey=new Map(universe.terms.map(x=>[x.subject+'|'+x.term,x]));

assert.ok(manifest.counts.official_decoder_full>=59);
assert.equal(manifest.counts.official_reference_candidates,7);
assert.equal(manifest.counts.official_reference_bound,2);
assert.equal(manifest.counts.official_reference_held,5);

const sedimentary=byKey.get('SCIENCE|퇴적암');
assert.equal(sedimentary.reference_candidate.binding_state,'BOUND');
assert.equal(sedimentary.morphology_source,'EDUCATION_OFFICE_TERM_REFERENCE');
assert.equal(sedimentary.decoder_reference.literal_meaning,'쌓여서 만들어진 바위');
assert.equal(sedimentary.readiness.decoder_full,true);

const congruent=byKey.get('MATH|합동');
assert.equal(congruent.reference_candidate.binding_state,'BOUND');
assert.equal(congruent.decoder_reference.literal_meaning,'합했을 때 같음');
assert.equal(congruent.readiness.decoder_full,true);

const decimal=byKey.get('MATH|소수');
assert.equal(decimal.lexical.state,'AMBIGUOUS_CONTEXT_REQUIRED');
assert.equal(decimal.reference_candidate.hanja,'素數');
assert.equal(decimal.reference_candidate.binding_state,'HELD_CONTEXT_OR_LEXEME_MISMATCH');
assert.equal(decimal.decoder_reference,null);
assert.equal(decimal.hanja,'');
assert.equal(decimal.readiness.decoder_full,false);

const front=byKey.get('SCIENCE|전선');
assert.equal(front.reference_candidate.binding_state,'HELD_CONTEXT_OR_LEXEME_MISMATCH');
assert.equal(front.decoder_reference,null);

console.log('SCIENCE_MATH_HANJA_REFERENCE_INTEGRATION_TEST: PASS');
console.log(JSON.stringify({
  decoder_full:manifest.counts.official_decoder_full,
  reference_bound:manifest.counts.official_reference_bound,
  reference_held:manifest.counts.official_reference_held,
  guarded_ambiguous_example:'MATH|소수 -> source 素數 held; elementary context not overwritten'
},null,2));
