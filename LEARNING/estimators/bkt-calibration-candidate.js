'use strict';

const Benchmark=require('../benchmark/estimator-benchmark.js');

const VERSION='TAKY_BKT_CALIBRATION_CANDIDATE_V1';
const GRID=Object.freeze({
  pL0:[0.15,0.30,0.45],
  pT:[0.05,0.10,0.20],
  pG:[0.10,0.20,0.30],
  pS:[0.05,0.10,0.20]
});

function combinations(grid=GRID){
  const out=[];
  for(const pL0 of grid.pL0)
    for(const pT of grid.pT)
      for(const pG of grid.pG)
        for(const pS of grid.pS)
          out.push({pL0,pT,pG,pS});
  return out;
}

function rollingBrier(rows=[],params={}){
  if(rows.length<2)return null;
  const losses=[];
  for(let i=1;i<rows.length;i++){
    const history=rows.slice(0,i);
    const pred=Benchmark.bktCandidate(history,params);
    losses.push(Math.pow(pred.probability-rows[i].verified_outcome,2));
  }
  return losses.length?losses.reduce((a,b)=>a+b,0)/losses.length:null;
}

function calibrate(rows=[],options={}){
  const checked=Benchmark.validateSequence(rows);
  if(!checked.ok)return {ok:false,reason:'INVALID_SEQUENCE',issues:checked.issues};
  const seq=checked.rows;
  const minTrain=Number.isFinite(options.min_train)?Math.max(3,Math.floor(options.min_train)):8;
  if(seq.length<minTrain){
    return {
      ok:true,
      estimator_id:'BKT_CALIBRATION_CANDIDATE',
      estimator_version:VERSION,
      status:'INSUFFICIENT_TRAINING_EVIDENCE',
      training_count:seq.length,
      min_training_count:minTrain,
      parameters:null,
      training_brier:null,
      promoted:false
    };
  }

  let best=null;
  for(const params of combinations(options.grid||GRID)){
    const score=rollingBrier(seq,params);
    if(!Number.isFinite(score))continue;
    if(!best||score<best.training_brier-1e-12||
      (Math.abs(score-best.training_brier)<=1e-12&&JSON.stringify(params)<JSON.stringify(best.parameters))){
      best={parameters:params,training_brier:score};
    }
  }

  return {
    ok:true,
    estimator_id:'BKT_CALIBRATION_CANDIDATE',
    estimator_version:VERSION,
    status:best?'CALIBRATED_CANDIDATE':'CALIBRATION_FAILED',
    training_count:seq.length,
    min_training_count:minTrain,
    grid_size:combinations(options.grid||GRID).length,
    parameters:best?.parameters||null,
    training_brier:Number.isFinite(best?.training_brier)?Math.round(best.training_brier*1e6)/1e6:null,
    calibration_provenance:{
      method:'DETERMINISTIC_GRID_SEARCH_ROLLING_BRIER',
      train_only:true,
      future_holdout_untouched:true
    },
    promoted:false,
    scheduling_authority:false
  };
}

function benchmarkWithCalibration(rows=[],options={}){
  const checked=Benchmark.validateSequence(rows);
  if(!checked.ok)return {ok:false,reason:'INVALID_SEQUENCE',issues:checked.issues};
  const seq=checked.rows;
  const holdoutCount=Math.max(1,Math.floor(seq.length*(Number(options.holdout_fraction)||0.25)));
  const cut=Math.max(1,seq.length-holdoutCount);
  const train=seq.slice(0,cut);
  const holdout=seq.slice(cut);
  const calibrated=calibrate(train,{min_train:options.min_train,grid:options.grid});

  if(calibrated.status!=='CALIBRATED_CANDIDATE'){
    return {
      ok:true,
      status:'HOLD_INSUFFICIENT_CALIBRATION',
      train_count:train.length,
      holdout_count:holdout.length,
      calibration:calibrated,
      promoted:false
    };
  }

  const combined=[...train,...holdout];
  const benchmark=Benchmark.timeHeldOut(combined,{
    min_history:train.length,
    bkt_params:calibrated.parameters
  });

  return {
    ok:true,
    status:'CALIBRATED_AND_HELD_OUT_EVALUATED',
    train_count:train.length,
    holdout_count:holdout.length,
    calibration:calibrated,
    held_out_brier:benchmark.brier?.bkt??null,
    observational_held_out_brier:benchmark.brier?.observational??null,
    benchmark,
    promoted:false,
    scheduling_authority:false
  };
}

function selfValidate(result={}){
  const issues=[];
  if(!result?.ok)issues.push('RESULT_NOT_OK');
  if(result.promoted!==false)issues.push('CANDIDATE_CANNOT_SELF_PROMOTE');
  if(result.scheduling_authority===true)issues.push('SCHEDULING_AUTHORITY_FORBIDDEN');
  if(result.calibration?.calibration_provenance?.future_holdout_untouched===false)issues.push('HOLDOUT_CONTAMINATION');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,GRID,combinations,rollingBrier,calibrate,benchmarkWithCalibration,selfValidate});
