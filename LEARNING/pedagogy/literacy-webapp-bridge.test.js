'use strict';
const assert=require('assert');
const Bridge=require('./literacy-webapp-bridge.js');

const refs={
  academic_vocabulary:'CNE:ACADEMIC_VOCAB_1387_RESEARCH_2024',
  ondok:'CNE:CNE_ONDOK_INDEX_2026',
  writing_transfer:'CNE:CNE_SAGAKSAGAK_ONGEUL_2026'
};

{
  const x=Bridge.derive({
    learner_profile:{school_stage:'E5'},
    reading_material:{ondok_index:300},
    source_refs:refs,
    term_recommendations:[
      {term_id:'sci-yeol','term':'열전도','priority':'RECOVERY',source_ref:'CURRICULUM:SCIENCE:E5'}
    ]
  });
  assert.equal(x.ok,true);
  assert.deepEqual(x.source_signals.reading_material.grade_reference_band,{min:225,max:285});
  assert.equal(x.source_signals.reading_material.difficulty_state,'ABOVE_GRADE_REFERENCE_BAND');
  assert.equal(x.consumers.ready_set.intent,'FOCUSED_REMEDIATION');
  assert.deepEqual(x.consumers.hide_seek.targets[0].mode_bias,['CORE','RECALL']);
  assert.equal(x.consumers.snap_pop.activity_sequence[3].derivation,'TAKY_DERIVED');
  assert.equal(Bridge.validate(x).ok,true);
}

{
  const x=Bridge.derive({
    learner_profile:{school_stage:'E5'},
    reading_material:{ondok_index:250},
    source_refs:refs,
    term_recommendations:[{term_id:'kor-juje','term':'주제','priority':'DISCOVERY'}]
  });
  assert.equal(x.source_signals.reading_material.difficulty_state,'IN_GRADE_REFERENCE_BAND');
  assert.equal(x.consumers.ready_set.intent,'KEEP_NORMAL_EXECUTION');
  assert.deepEqual(x.consumers.hide_seek.targets[0].mode_bias,['TRACE','LINK','CORE']);
}

{
  const x=Bridge.derive({learner_profile:{school_stage:'M1'}});
  assert.equal(x.ok,false);
  assert.equal(x.reason,'ELEMENTARY_SCHOOL_STAGE_E1_E6_REQUIRED');
}

{
  const x=Bridge.derive({learner_profile:{school_stage:'E6'},source_refs:refs});
  x.consumers.ready_set.due_date='2026-10-08';
  const v=Bridge.validate(x);
  assert.equal(v.ok,false);
  assert.ok(v.issues.includes('SCHEDULE_AUTHORITY_LEAK'));
}

console.log('literacy-webapp-bridge.test.js PASS');
