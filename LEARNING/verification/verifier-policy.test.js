'use strict';
const assert=require('node:assert/strict');
const P=require('./verifier-policy.js');

assert.equal(P.canVerify({source_app:'hide-seek',evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',verifier_type:'RETRIEVAL_EXACT_MATCH',auto:true}).ok,true);
assert.equal(P.canVerify({source_app:'snap-pop',evidence_type:'LEARNER_PRODUCTION_EVIDENCE',verifier_type:'HUMAN_RUBRIC_BINARY',auto:false}).ok,true);
assert.equal(P.canVerify({source_app:'snap-pop',evidence_type:'LEARNER_PRODUCTION_EVIDENCE',verifier_type:'HUMAN_RUBRIC_BINARY',auto:true}).reason,'AUTO_VERIFICATION_FORBIDDEN');
assert.equal(P.canVerify({source_app:'ready-set',evidence_type:'STRUCTURED_PRACTICE_EVIDENCE',verifier_type:'ANSWER_KEY_EXACT',auto:true}).ok,true);
assert.equal(P.canVerify({source_app:'ready-set',evidence_type:'LEARNER_PRODUCTION_EVIDENCE',verifier_type:'ANSWER_KEY_EXACT',auto:true}).ok,false);
assert.equal(P.canVerify({source_app:'hide-seek',evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',verifier_type:'HUMAN_RUBRIC_BINARY',auto:false}).ok,false);

console.log('LEARNING_VERIFIER_POLICY_PASS');
