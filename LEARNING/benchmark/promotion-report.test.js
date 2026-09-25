'use strict';
const assert=require('node:assert/strict');
const Report=require('./promotion-report.js');

const hold={
  ok:true,
  source_kind:'REAL_EVIDENCE',
  evidence_receipt_id:'receipt-1',
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  verified_target_count:10,
  benchmark:{
    total_points:9,
    stable_instrument_points:9,
    instrument_change_points:0,
    brier:{observational:0.20,bkt:0.19,dsr:0.21},
    points:[]
  }
};
const hr=Report.buildPromotionReport(hold);
assert.equal(hr.ok,true);
assert.equal(hr.decision,'HOLD');
assert.equal(hr.auto_promotion,false);
assert.equal(Report.selfValidate(hr).ok,true);

const invalid=Report.buildPromotionReport({ok:false});
assert.equal(invalid.ok,false);

console.log('ESTIMATOR_PROMOTION_REPORT_PASS');
