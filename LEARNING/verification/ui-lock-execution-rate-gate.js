'use strict';

const fs=require('node:fs');
const path=require('node:path');

const VERSION='TAKY_EXECUTION_RATE_SCOPE_GATE_V2';
const REQUIRED=Object.freeze(['ENTRY','ACTION','RESULT','PERSIST','READBACK']);

function load(file){
  return JSON.parse(fs.readFileSync(path.resolve(file),'utf8').replace(/^\uFEFF/,''));
}

function measure(functions=[]){
  const promised=Array.isArray(functions)?functions:[];
  let counted=0;
  const detail=promised.map(fn=>{
    const evidence=new Set((fn.evidence||[]).map(String));
    const missing=REQUIRED.filter(x=>!evidence.has(x));
    const executed=missing.length===0;
    if(executed)counted++;
    return {id:fn.id||null,executed,missing};
  });
  const denominator=promised.length;
  return {
    counted,denominator,
    execution_rate:denominator?counted/denominator:0,
    detail
  };
}

function evaluate(input={}){
  const scope=String(input.measurement_scope||'FINAL_UI').toUpperCase();
  if(scope==='PRE_UI_RUNTIME'){
    const measured=measure(input.functions);
    return {
      ok:true,version:VERSION,measurement_scope:scope,
      state:'PRE_UI_RUNTIME_MEASURED',
      ...measured,
      claim_allowed:measured.counted===measured.denominator&&measured.denominator>0
        ?'PRE_UI_RUNTIME_EXECUTION_PASS':'PRE_UI_RUNTIME_PARTIAL',
      claim_forbidden:['FINAL_UI_EXECUTION_PASS','VALUE_DELIVERY_COMPLETE','MOBILE_E2E_COMPLETE']
    };
  }
  if(scope!=='FINAL_UI')return {ok:false,version:VERSION,reason:'UNSUPPORTED_MEASUREMENT_SCOPE'};
  if(input.ui_lock!==true){
    return {
      ok:true,version:VERSION,measurement_scope:scope,
      state:'FINAL_UI_NOT_MEASURABLE_BEFORE_UI_LOCK',
      execution_rate:null,counted:0,denominator:Array.isArray(input.functions)?input.functions.length:0,
      claim_allowed:'PRE_UI_RUNTIME_ONLY',
      claim_forbidden:['FINAL_UI_EXECUTION_PASS','VALUE_DELIVERY_COMPLETE','MOBILE_E2E_COMPLETE']
    };
  }
  const measured=measure(input.functions);
  return {
    ok:true,version:VERSION,measurement_scope:scope,
    state:'FINAL_UI_MEASURED',
    ...measured,
    claim_allowed:measured.counted===measured.denominator&&measured.denominator>0
      ?'FINAL_UI_EXECUTION_PASS':'PARTIAL_EXECUTION_ONLY'
  };
}

if(require.main===module){
  const file=process.argv[2];
  if(!file)throw new Error('INPUT_JSON_REQUIRED');
  console.log(JSON.stringify(evaluate(load(file)),null,2));
}

module.exports=Object.freeze({VERSION,REQUIRED,evaluate});
