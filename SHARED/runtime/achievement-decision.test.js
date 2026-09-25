'use strict';
const assert=require('node:assert/strict');
const A=require('./achievement-decision.js');

const rule={rule_id:'R1',badge_id:'B1',event_types:['TASK_COMPLETED'],min_count:2};
assert.equal(A.validateRule(rule).ok,true);

const e={exploration_event_id:'E1',member_id:'C1',source_event_type:'TASK_COMPLETED',category:'EXECUTION',occurred_at:'2026-09-25T00:00:00.000Z'};
assert.equal(A.decide({rule,event:e,prior_count:0}).reason,'THRESHOLD_NOT_MET');
const d=A.decide({rule,event:e,prior_count:1});
assert.equal(d.reason,'AWARD');
assert.equal(d.award.badge_id,'B1');
assert.equal(d.award.member_id,'C1');
assert.equal(A.decide({rule,event:e,prior_count:1,already_awarded:true}).reason,'ALREADY_AWARDED');

console.log('TAKY_ACHIEVEMENT_DECISION_V1_PASS');
