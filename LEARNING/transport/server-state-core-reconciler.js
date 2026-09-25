'use strict';
const Receipt=require('../receipts/real-evidence-receipt.js');
const Ledger=require('../lifecycle/evaluation-ledger.js');
const Trigger=require('../lifecycle/real-evidence-evaluation-trigger.js');

function reconcile(state={},options={}){
  let ledger=options.evaluation_ledger||Ledger.emptyLedger();
  const results=[];
  for(const [scope_key,rows] of Object.entries(state.verified_by_scope||{})){
    if(!Array.isArray(rows)||!rows.length)continue;
    const issued=Receipt.issueBatchReceipt(rows,{created_at:options.created_at});
    if(!issued.ok)return {ok:false,reason:'RECEIPT_REBUILD_FAILED',scope_key};
    const evaluated=Trigger.evaluateReceipt({
      ledger,
      receipt:issued.receipt,
      canonical_evidence:issued.canonical_evidence,
      created_at:options.created_at,
      promotion_policy:options.promotion_policy||{}
    });
    if(!evaluated.ok)return {ok:false,reason:'EVALUATION_FAILED',scope_key};
    ledger=evaluated.ledger;
    results.push({scope_key,receipt_id:issued.receipt.receipt_id,data_readiness:evaluated.data_readiness});
  }
  return {ok:true,evaluation_ledger:ledger,results,observation_only_count:Object.keys(state.observations_by_id||{}).length};
}

module.exports=Object.freeze({reconcile});
