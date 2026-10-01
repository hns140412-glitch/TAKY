'use strict';
const assert=require('assert');
const U=require('./language-usage-evidence-kind-contract.js');

assert.equal(U.normalize('example_sentence'),'EXAMPLE_SENTENCE');
assert.equal(U.permits('EXAMPLE_SENTENCE','CONTEXT_EXAMPLE'),true);
assert.equal(U.permits('EXAMPLE_SENTENCE','COLLOCATION_CANDIDATE'),false);
assert.equal(U.permits('DEPENDENCY_PATTERN','GRAMMAR_PATTERN'),true);
assert.equal(U.permits('DEPENDENCY_PATTERN','COLLOCATION_CANDIDATE'),true);
assert.equal(U.permits('CHILD_ADULT_SPOKEN_DEPENDENCY_PATTERN','SPOKEN_CHUNK_CANDIDATE'),true);
assert.equal(U.validateEvidence({
 learning_evidence_role:'LANGUAGE_USAGE',usage_evidence_kind:'EXAMPLE_SENTENCE'
}).ok,true);
assert.equal(U.validateEvidence({
 learning_evidence_role:'CURRICULUM_ALIGNMENT',usage_evidence_kind:'DEPENDENCY_PATTERN'
}).ok,false);

console.log('language-usage-evidence-kind-contract.test.js PASS');
