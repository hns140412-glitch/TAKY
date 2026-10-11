'use strict';
const assert=require('assert');
const S=require('./academic-vocab-unit-selector.js');

const source='CNE_TEST_UNIT_SOURCE';
const result=S.select({
  school_stage:'E5',
  source_ref:source,
  unit_text:'자료를 조사하고 결과를 비교하여 변화 과정을 설명한다. 조사한 자료를 확인하고 해결 방법을 표현한다.',
  evidence:[
    {academic_vocab_term:'조사',result_type:'WRONG'},
    {academic_vocab_term:'조사',result_type:'HINT_USED',assisted:true}
  ],
  limit:12
});
assert.equal(result.ok,true);
assert.equal(result.stage_policy.primary,2);
assert.deepEqual(result.stage_policy.foundation,[1]);
assert.ok(result.selected.some(x=>x.term==='자료'&&x.academic_role==='PRIMARY'));
assert.ok(result.selected.some(x=>x.term==='조사'&&x.academic_role==='PRIMARY'));
assert.ok(result.selected.some(x=>x.term==='결과'&&x.academic_role==='FOUNDATION'));
assert.ok(result.selected.some(x=>x.term==='비교'&&x.academic_role==='FOUNDATION'));
assert.equal(result.selected[0].term,'조사');
assert.equal(S.validate(result).ok,true);

const noSource=S.select({school_stage:'E5',unit_text:'자료'});
assert.equal(S.validate(noSource).ok,false);
assert.ok(S.validate(noSource).issues.includes('TERM_PROVENANCE_REQUIRED'));

const oneChar=S.select({school_stage:'E5',source_ref:source,unit_text:'종'});
assert.equal(oneChar.matched_total,0);

console.log('academic-vocab-unit-selector.test.js PASS');
