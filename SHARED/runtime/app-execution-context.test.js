'use strict';
const assert=require('node:assert/strict');
const C=require('./app-execution-context.js');

const full=C.normalize({
  family_id:'F1',member_id:'M1',profile_id:'P1',
  assignment_id:'A1',analysis_id:'AN1',learning_unit_id:'LU1',todo_id:'T1',
  session_id:'S1',task_id:'TASK1',lap_id:'L1',
  source_app:'ready-set',target_app:'hide-seek',return_target:'https://ready.example/app'
});
assert.equal(full.context_contract,'TAKY_APP_EXECUTION_CONTEXT_V1');
assert.equal(C.validate(full,{linked:true}).ok,true);
assert.equal(full.learning_unit_id,'LU1');
assert.equal(full.todo_id,'T1');

const fromQuery=C.fromSearchParams('?child_id=M2&session_id=S2&task_id=T2&lap_id=L2&return_target=https%3A%2F%2Fready.example%2F');
assert.equal(fromQuery.member_id,'M2');
assert.equal(C.validate(fromQuery,{linked:true}).ok,true);

const merged=C.merge(
  {member_id:'M1',learning_unit_id:'LU1',session_id:'S1',task_id:'TK1',return_target:'https://ready.example/'},
  {source_app:'hide-seek',todo_id:'TD1'}
);
assert.equal(merged.member_id,'M1');
assert.equal(merged.learning_unit_id,'LU1');
assert.equal(merged.todo_id,'TD1');
assert.equal(merged.source_app,'hide-seek');

const event=C.toEventContext(merged);
assert.equal(event.learning_unit_id,'LU1');
assert.equal(event.todo_id,'TD1');
assert.equal(event.member_id,'M1');

assert.equal(C.validate({session_id:'S',task_id:'T',return_target:'https://ready.example/'},{linked:true}).ok,false);
assert.equal(C.validate({member_id:'M',session_id:'S',task_id:'T',return_target:'javascript:alert(1)'},{linked:true}).ok,false);

console.log('TAKY_APP_EXECUTION_CONTEXT_V1_PASS');
