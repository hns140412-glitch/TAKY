'use strict';
const assert=require('node:assert/strict');
const R=require('./recovery-profile.js');

const e=(id,target,day,outcome,opts={})=>({
  event_id:id,
  learning_target_id:target,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  verified_outcome:outcome,
  verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-'+id},
  assisted:opts.assisted,
  assistance:opts.assisted===true?'ASSISTED':opts.assisted===false?'UNASSISTED':'UNKNOWN',
  attempt_count:opts.attempt_count
});

const rows=[
  e('a1','word:a',20,0,{assisted:true,attempt_count:2}),
  e('b1','word:b',20,1,{assisted:false,attempt_count:1}),
  e('a2','word:a',21,1,{assisted:false,attempt_count:1}),
  e('c1','word:c',21,0,{assisted:true,attempt_count:3})
];

const p=R.derive(rows);
assert.equal(p.ok,true);
assert.equal(p.status,'OBSERVED');
assert.equal(p.target_count,3);
assert.equal(p.recovery_episode_count,2);
assert.equal(p.recovered_episode_count,1);
assert.equal(p.unresolved_episode_count,1);
assert.equal(p.median_recovery_hours,24);
assert.equal(p.assistance_rate,0.5);
assert.equal(R.validate(p).ok,true);

const noTarget=R.derive([{event_id:'x',observed_at:'2026-09-20T07:00:00.000Z',verified_outcome:0}]);
assert.equal(noTarget.status,'INSUFFICIENT_TARGET_IDENTITY');
assert.equal(noTarget.recovery_episode_count,0);

const leaked={...p,due_at:'2026-10-01'};
assert.equal(R.validate(leaked).ok,false);
assert.equal(R.validate(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('LEARNING_RECOVERY_PROFILE_PASS');

const unverifiedTarget=R.derive([{
  event_id:'u1',learning_target_id:'word:u',observed_at:'2026-09-22T07:00:00.000Z',
  verified_outcome:0,verification:null
}]);
assert.equal(unverifiedTarget.status,'INSUFFICIENT_VERIFIED_TARGET_EVENTS');
assert.equal(unverifiedTarget.recovery_episode_count,0);
