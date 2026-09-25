'use strict';
const assert=require('node:assert/strict');
const P=require('./promotion-policy.js');

function makePoint(i,{obs,bkt,dsr,y,history=3,drift=false}){
  const sq=(p)=>Math.pow(p-y,2);
  return {
    history_count:history,
    target_event_id:'e'+i,
    target_outcome:y,
    instrument_changed:drift,
    predictions:{
      observational:{probability:obs,promoted:false},
      bkt:{probability:bkt,promoted:false},
      dsr:{probability:dsr,promoted:false}
    },
    losses:{observational:sq(obs),bkt:sq(bkt),dsr:sq(dsr)}
  };
}

const small={
  source_kind:'REAL_EVIDENCE',
  evidence_receipt_id:'receipt-small',
  verified_target_count:10,
  benchmark:{
    total_points:9,
    stable_instrument_points:9,
    instrument_change_points:0,
    brier:{observational:0.20,bkt:0.18,dsr:0.19},
    points:Array.from({length:9},(_,i)=>makePoint(i,{obs:0.6,bkt:0.65,dsr:0.62,y:i%2,history:i+1}))
  }
};
const smallReport=P.evaluatePromotion(small);
assert.equal(smallReport.dataset_blockers.includes('MIN_VERIFIED_TARGETS_NOT_MET'),true);
assert.equal(smallReport.promotion_review_available,false);

const pts=[];
for(let i=0;i<36;i++){
  const y=i%3===0?0:1;
  pts.push(makePoint(i,{
    obs:y?0.68:0.48,
    bkt:y?0.80:0.20,
    dsr:y?0.73:0.35,
    y,
    history:i<4?2:5,
    drift:false
  }));
}
const good={
  source_kind:'REAL_EVIDENCE',
  evidence_receipt_id:'receipt-good',
  verified_target_count:40,
  benchmark:{
    total_points:36,
    stable_instrument_points:36,
    instrument_change_points:0,
    brier:{
      observational:pts.reduce((s,x)=>s+x.losses.observational,0)/pts.length,
      bkt:pts.reduce((s,x)=>s+x.losses.bkt,0)/pts.length,
      dsr:pts.reduce((s,x)=>s+x.losses.dsr,0)/pts.length
    },
    points:pts
  }
};
const goodReport=P.evaluatePromotion(good,{max_calibration_mae:0.25,min_brier_improvement:0.005});
assert.equal(goodReport.dataset_blockers.length,0);
assert.equal(goodReport.candidate_reports.bkt.review_eligible,true);
assert.equal(goodReport.auto_promotion,false);
assert.equal(goodReport.promotion_review_available,true);

const drifted=JSON.parse(JSON.stringify(good));
drifted.benchmark.points=drifted.benchmark.points.map((x,i)=>({...x,instrument_changed:i<10}));
drifted.benchmark.instrument_change_points=10;
drifted.benchmark.stable_instrument_points=26;
const driftReport=P.evaluatePromotion(drifted);
assert.equal(driftReport.dataset_blockers.includes('INSTRUMENT_DRIFT_TOO_HIGH'),true);
assert.equal(driftReport.promotion_review_available,false);

console.log('ESTIMATOR_PROMOTION_POLICY_PASS');
