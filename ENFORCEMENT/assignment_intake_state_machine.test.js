'use strict';
const assert=require('node:assert/strict');
const Intake=require('../LEARNING/intake/assignment-intake-state-machine.js');
const UserData=require('../LEARNING/transport/family-user-data-store.js');

let r=Intake.create({family_id:'F1',member_id:'A',batch_id:'B1'});assert.equal(r.ok,true);let s=r.state;
r=Intake.capture(s,{capture_id:'C1',local_temp_ref:'device://tmp/C1.jpg',captured_at:'2026-10-07T13:00:00Z'});assert.equal(r.ok,true);s=r.state;
r=Intake.capture(s,{capture_id:'C2',local_temp_ref:'device://tmp/C2.jpg',captured_at:'2026-10-07T13:00:03Z'});assert.equal(r.ok,true);s=r.state;
assert.deepEqual(s.captures.map(x=>x.display_order),[1,2]);

r=Intake.requestAnalysis(s);assert.equal(r.ok,true);s=r.state;
r=Intake.applyAnalysis(s,{analysis_id:'AN1',results:[{capture_id:'C1',quality:'PASS'},{capture_id:'C2',quality:'RETAKE',reason:'BLUR'}]});
assert.equal(r.ok,true);s=r.state;assert.equal(s.phase,'RETAKE_REQUIRED');
assert.equal(Intake.confirm(s,{assignment_id:'HW1',title:'Homework',subject:'English'}).ok,false);

r=Intake.retake(s,{target_capture_id:'C2',capture_id:'C2R',local_temp_ref:'device://tmp/C2R.jpg',captured_at:'2026-10-07T13:01:00Z'});
assert.equal(r.ok,true);s=r.state;assert.deepEqual(s.captures.map(x=>x.display_order),[1,2]);assert.equal(s.captures[1].replaces_capture_id,'C2');
r=Intake.requestAnalysis(s);assert.equal(r.ok,true);s=r.state;
r=Intake.applyAnalysis(s,{analysis_id:'AN2',results:[{capture_id:'C1',quality:'PASS'},{capture_id:'C2R',quality:'PASS'}]});
assert.equal(r.ok,true);s=r.state;assert.equal(s.phase,'REVIEW_REQUIRED');
r=Intake.confirm(s,{assignment_id:'HW1',title:'Vocabulary homework',subject:'English',task_id:'T1',due_at:'2026-10-09T09:00:00Z',confirmed_at:'2026-10-07T13:02:00Z'});
assert.equal(r.ok,true);assert.equal(r.state.phase,'CONFIRMED');
assert.equal(r.record.member_id,'A');assert.equal(r.record.status,'CONFIRMED');
assert.deepEqual(r.record.payload.capture_refs.map(x=>x.capture_id),['C1','C2R']);
assert.equal(UserData.normalize(r.record).ok,true);

console.log('ASSIGNMENT_INTAKE_STATE_MACHINE_PASS');
console.log(JSON.stringify({continuous_capture:true,targeted_retake:true,display_order_preserved:true,review_before_commit:true,user_data_record_ready:true,real_device_ux:'PENDING'}));
