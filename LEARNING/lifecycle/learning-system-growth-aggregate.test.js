'use strict';
const assert=require('node:assert/strict');
const Agg=require('./learning-system-growth-aggregate.js');

const rows=[
 {member_id:'A',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:3,success_count:2,failure_count:1},
 {member_id:'B',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:2,success_count:1,failure_count:1},
 {member_id:'C',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:3,success_count:1,failure_count:2}
];
const r=Agg.aggregate(rows,{min_members:3,min_verified_outcomes:6});
assert.equal(r.ok,true);
assert.equal(r.candidate_count,1);
assert.equal(r.candidates[0].member_count,3);
assert.equal(r.candidates[0].promotion_authorized,false);
assert.equal(r.candidates[0].grow_lineage_event.grow_domain,'LEARNING_GROW');
assert.equal(r.candidates[0].grow_lineage_event.payload.scope_kind,'SYSTEM_AGGREGATE');
assert.equal('member_id' in r.candidates[0].grow_lineage_event.payload,false);
assert.equal(JSON.stringify(r).includes('"A"'),false);
assert.equal(JSON.stringify(r).includes('"B"'),false);
assert.equal(JSON.stringify(r).includes('"C"'),false);
assert.equal(Agg.validate(r).ok,true);

const tooSmall=Agg.aggregate(rows.slice(0,2),{min_members:3,min_verified_outcomes:4});
assert.equal(tooSmall.candidate_count,0);
console.log('LEARNING_SYSTEM_GROWTH_AGGREGATE_PASS');