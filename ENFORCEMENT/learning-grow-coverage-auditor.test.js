'use strict';
const assert=require('node:assert/strict');
const A=require('./learning-grow-coverage-auditor.js');

const currentLike=[
  {subject:'영어',learner_stage:'SCHOOL_AGE',verified_outcome_count:6,source_kind:'REAL_EVIDENCE'},
  {subject:'수학',learner_stage:'SCHOOL_AGE',verified_outcome_count:3,source_kind:'SYNTHETIC_FIXTURE'}
];
const r=A.audit(currentLike);
assert.equal(r.ok,true);
assert.equal(r.complete,false);
assert.equal(r.subject_coverage.find(x=>x.subject_id==='english').pass,true);
assert.equal(r.subject_coverage.find(x=>x.subject_id==='math').pass,false,'synthetic-only math must not count as real coverage');
for(const id of ['korean','hanja','science','social'])assert(r.gaps.some(x=>x.subject_id===id));
assert.equal(A.validate(r).ok,true);

const full=[];
for(const subject of ['영어','국어','한자','수학','과학','사회']){
  full.push({subject,learner_stage:'SCHOOL_AGE',verified_outcome_count:2,source_kind:'REAL_EVIDENCE'});
}
const complete=A.audit(full);
assert.equal(complete.complete,true);
assert.equal(complete.gaps.length,0);

const staged=A.audit([
  {subject:'영어',learner_stage:'EARLY_LEARNER',verified_outcome_count:2,source_kind:'REAL_EVIDENCE'},
  {subject:'영어',learner_stage:'ADULT',verified_outcome_count:2,source_kind:'REAL_EVIDENCE'}
],{min_distinct_stages_per_subject:2});
assert.equal(staged.subject_coverage.find(x=>x.subject_id==='english').pass,true);
assert.equal(staged.complete,false);

console.log('LEARNING_GROW_COVERAGE_AUDITOR_PASS');
