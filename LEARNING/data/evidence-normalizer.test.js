'use strict';
const assert=require('node:assert/strict');
const N=require('./evidence-normalizer.js');

const hide=N.normalizeAdapterEvidence({
  event_id:'h1',observed_at:'2026-09-25T07:00:00.000Z',
  member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',source_app:'hide-seek',
  instrument_version:'hide-v2',interaction_mode:'RECALL',assisted:false,
  attempt_count:2,response_latency_ms:800,verified_performance:true,verified_outcome:1,
  memory:{average_strength:72,review_advisories:[{nextReviewPriority:80}]}
});
assert.equal(N.validateNormalized(hide).ok,true);
assert.equal(hide.assistance,'UNASSISTED');
assert.equal(hide.memory.average_strength,72);

const self=N.normalizeAdapterEvidence({
  event_id:'s1',observed_at:'2026-09-25T07:00:00.000Z',
  member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',
  evidence_type:'CHILD_SELF_REPORT',source_app:'ready-set',
  instrument_version:'ready-v1',verified_performance:true,verified_outcome:1
});
assert.equal(self.verified_performance,false);
assert.equal(self.verified_outcome,null);
assert.equal(N.validateNormalized(self).ok,true);

const bad=N.normalizeAdapterEvidence({event_id:'x',evidence_type:'MEMORY_RETRIEVAL_EVIDENCE'});
assert.equal(N.validateNormalized(bad).ok,false);

console.log('LEARNING_EVIDENCE_NORMALIZER_PASS');
