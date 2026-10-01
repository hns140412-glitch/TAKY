'use strict';

const VERSION='TAKY_LEARNING_ENGINE_OUTPUT_CONTRACT_V1';
const IO=require('./learning-evidence-io-contract.js');

const clean=v=>String(v??'').trim();

function derive({decision={},growth_next_step=null,reference_gaps=[]}={}){
  if(decision?.ok!==true)return {ok:false,reason:'DECISION_REQUIRED'};

  const adaptive=decision.adaptive_plan||{};
  const targets=Array.isArray(adaptive.target_learning_ids)
    ?[...new Set(adaptive.target_learning_ids.map(clean).filter(Boolean))].slice(0,64):[];
  const growth=growth_next_step||null;
  const intensity=growth?.growth_control?.learning_intensity||
    (adaptive.recovery_floor==='HIGH'?'SUPPORT_BUILD':
      adaptive.recovery_floor==='MEDIUM'?'BUILD_CONNECT':'BUILD_CONNECT');

  const reviewRequired=adaptive.add_checkpoint===true||
    adaptive.add_retrieval_checkpoint===true||
    adaptive.recovery_floor==='HIGH';

  const quantityBand=targets.length
    ?(targets.length<=3?'FOCUSED':targets.length<=8?'STANDARD':'EXTENDED')
    :(intensity==='SUPPORT_BUILD'?'FOCUSED':
      intensity==='STRETCH_TRANSFER'?'EXTENDED':'STANDARD');

  const output={
    ok:true,
    version:VERSION,
    authority:'TAKY_LEARNING_ENGINE_CORE',
    date_authority:false,
    allocated_quantity_authority:false,
    review_need:{
      required:reviewRequired,
      retrieval_checkpoint:adaptive.add_retrieval_checkpoint===true,
      checkpoint:adaptive.add_checkpoint===true,
      recovery_floor:adaptive.recovery_floor||null,
      authority:'LEARNING_ENGINE_REVIEW_NEED_INTENT_ONLY'
    },
    learning_intensity:intensity,
    recommended_quantity:{
      authority:'LEARNING_ENGINE_QUANTITY_INTENT_ONLY',
      unit:'LEARNING_TARGET',
      target_ids:targets,
      target_count_hint:targets.length||null,
      quantity_band:quantityBand,
      planner_must_materialize:true,
      planner_may_adjust_to_available_time:true,
      allocated_quantity:null
    },
    next_growth_intent:growth?{
      authority:growth.authority,
      version:growth.version||null,
      support_phase:growth.support_phase||null,
      growth_control:growth.growth_control?JSON.parse(JSON.stringify(growth.growth_control)):null,
      question_depth:growth.question_depth?JSON.parse(JSON.stringify(growth.question_depth)):null,
      hint_policy:growth.hint_policy?JSON.parse(JSON.stringify(growth.hint_policy)):null
    }:null,
    reference_gaps:Array.isArray(reference_gaps)
      ?reference_gaps.map(x=>({...x,mining_request_authorized:false})) : [],
    cannot_influence:[
      'SCHEDULE_DATE','PLANNER_DATE','DUE_AT','DEADLINE',
      'ALLOCATED_QUANTITY','CALENDAR_TIME','ASSIGNMENT_FACT'
    ]
  };

  const checked=IO.validateLearningOutput(output);
  return checked.ok?output:{ok:false,reason:'LEARNING_OUTPUT_INVALID',issues:checked.issues,output};
}

function validate(output={}){
  return IO.validateLearningOutput(output);
}

module.exports=Object.freeze({VERSION,derive,validate});
