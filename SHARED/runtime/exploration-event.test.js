'use strict';
const assert=require('node:assert/strict');
const E=require('./exploration-event.js');

const ready=E.fromAppEvent({
  event_id:'E1',app:'ready-set',type:'TASK_STATE_CHANGED',
  family_id:'F1',member_id:'C1',actor_member_id:'P1',
  session_id:'S1',task_id:'T1',lap_id:'L1',payload:{next:'COMPLETED'}
});
assert.equal(ready.category,'EXECUTION');
assert.equal(ready.member_id,'C1');
assert.equal(ready.actor_member_id,'P1');
assert.equal(E.validate(ready).ok,true);

const hide=E.fromAppEvent({app:'hide-seek',type:'RETRIEVAL_ATTEMPT_RESULT',member_id:'C1'});
assert.equal(hide.category,'RETRIEVAL');

const snap=E.fromAppEvent({app:'snap-pop',type:'TASK_COMPLETED',member_id:'C1'});
assert.equal(snap.category,'EXECUTION');
assert.equal(E.achievementEligible(snap).eligible,true);

const entered=E.fromAppEvent({app:'snap-pop',type:'APP_ENTERED',member_id:'C1'});
assert.equal(entered.category,'HANDOFF');
assert.equal(E.achievementEligible(entered).eligible,false);

console.log('TAKY_EXPLORATION_EVENT_V1_PASS');
