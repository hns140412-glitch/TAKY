'use strict';

const assert=require('node:assert/strict');
const Gap=require('./evidence-gap.js');

const none=Gap.derive({
  scope:{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},
  decision:{
    blockers:[{code:'NO_EVIDENCE',priority:'HIGH'}],
    advisories:[],
    state_summary:{evidence_sufficiency:'NONE'}
  }
});
assert.equal(none.ok,true);
assert.equal(none.gap.gap_type,'LEARNER_EVIDENCE_ABSENT');
assert.equal(none.gap.index_check_required,true);
assert.equal(none.gap.mining_request_authorized,false);

const sparse=Gap.derive({
  scope:{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},
  decision:{
    blockers:[],
    advisories:[{code:'SPARSE_EVIDENCE',priority:'MEDIUM'}],
    state_summary:{evidence_sufficiency:'SPARSE'}
  },
  indexed_evidence:{source_refs:['INDEX:SRC-1']}
});
assert.equal(sparse.gap.gap_type,'LEARNER_EVIDENCE_SPARSE');
assert.deepEqual(sparse.gap.existing_source_refs,['INDEX:SRC-1']);

const enough=Gap.derive({
  scope:{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},
  decision:{
    blockers:[],
    advisories:[],
    state_summary:{evidence_sufficiency:'EMERGING'}
  }
});
assert.equal(enough.gap,null);

console.log('LEARNING_EVIDENCE_GAP_PASS');
