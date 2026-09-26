'use strict';
const assert=require('node:assert/strict');
const {project}=require('./badge-reaward-progress.js');
const cfg={tier_order:['GREEN','BLUE','RED','GOLD','PLATINUM']};
function receipt(i,kind='REAWARD'){return {authority:'AWARD_LEDGER',decision_status:'APPROVED',
  award_status:'AWARDED',award_id:'award-'+i,child_id:'CHILD_A',badge_id:'BADGE_1',award_kind:kind};}
let result=project(null,receipt(0,'INITIAL_AWARD'),cfg);
assert.equal(result.ok,true);
assert.equal(result.state.owned,true);
assert.equal(result.state.star_count,0); // Initial acquisition only unlocks the badge.
let state=result.state;
assert.equal(project(state,receipt(0,'INITIAL_AWARD'),cfg).reason,'DUPLICATE_AWARD_RECEIPT');
assert.equal(project(state,{...receipt(1),authority:'ACTIVITY_TELEMETRY'},cfg).ok,false);
assert.equal(project(state,{...receipt(1),child_id:'CHILD_B'},cfg).reason,'CROSS_MEMBER_OR_BADGE_STATE_FORBIDDEN');
assert.equal(project(state,receipt(1,'INITIAL_AWARD'),cfg).ok,false);
for(let i=1;i<=4;i++){
  result=project(state,receipt(i),cfg);
  assert.equal(result.ok,true);
  assert.equal(result.tier_up,false);
  assert.equal(result.state.star_count,i);
  state=result.state;
}
result=project(state,receipt(5),cfg);
assert.equal(result.ok,true);
assert.equal(result.tier_up,true);
assert.equal(result.stars_collected_before_promotion,5);
assert.equal(result.state.tier,'BLUE');
assert.equal(result.state.star_count,0);
assert.equal(project(result.state,receipt(5),cfg).reason,'DUPLICATE_AWARD_RECEIPT');
let top=project(null,receipt(100,'INITIAL_AWARD'),{tier_order:['GREEN','BLUE']}).state;
for(let i=101;i<=105;i++)top=project(top,receipt(i),{tier_order:['GREEN','BLUE']}).state;
assert.equal(top.tier,'BLUE');
for(let i=106;i<=110;i++)top=project(top,receipt(i),{tier_order:['GREEN','BLUE']}).state;
assert.equal(top.star_count,5);
assert.equal(top.top_tier_rule_pending,true);
assert.equal(project(top,receipt(111),{tier_order:['GREEN','BLUE']}).reason,'TOP_TIER_RULE_PENDING');
console.log('badge reaward progression: PASS');
