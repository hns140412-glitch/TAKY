'use strict';
const assert=require('node:assert/strict');
const Gate=require('./ui-lock-execution-rate-gate.js');

const pre=Gate.evaluate({
  measurement_scope:'PRE_UI_RUNTIME',
  ui_lock:false,
  functions:[
    {id:'TRACE',evidence:['ENTRY','ACTION','RESULT','PERSIST','READBACK']},
    {id:'LINK',evidence:['ENTRY','ACTION','RESULT','PERSIST','READBACK']}
  ]
});
assert.equal(pre.state,'PRE_UI_RUNTIME_MEASURED');
assert.equal(pre.execution_rate,1);
assert.equal(pre.claim_allowed,'PRE_UI_RUNTIME_EXECUTION_PASS');

const finalBlocked=Gate.evaluate({
  measurement_scope:'FINAL_UI',
  ui_lock:false,
  functions:[{id:'TRACE'}]
});
assert.equal(finalBlocked.state,'FINAL_UI_NOT_MEASURABLE_BEFORE_UI_LOCK');
assert.equal(finalBlocked.execution_rate,null);

const partial=Gate.evaluate({
  measurement_scope:'FINAL_UI',
  ui_lock:true,
  functions:[
    {id:'TRACE',evidence:['ENTRY','ACTION','RESULT','PERSIST','READBACK']},
    {id:'LINK',evidence:['ENTRY','ACTION','RESULT']}
  ]
});
assert.equal(partial.execution_rate,0.5);
assert.deepEqual(partial.detail[1].missing,['PERSIST','READBACK']);

console.log('EXECUTION_RATE_SCOPE_GATE_TEST: PASS');
