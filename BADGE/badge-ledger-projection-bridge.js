'use strict';

// Integration seam ONLY. A trusted owner-supplied adapter must read COMPLETE Award Ledger
// history and verify each row. Neither this module nor the visual renderer grants awards.
const {project}=require('./badge-reaward-progress.js');
const text=v=>typeof v==='string'?v.trim():'';
const blocked=(reason,details)=>({ok:false,reason,...(details?{details}:{})});
const SOURCE_CONTRACT='TAKY_TRUSTED_BADGE_AWARD_HISTORY_SOURCE_V1';

async function deriveFromLedger({source,child_id,badge_id,tier_order}={}){
  const child=text(child_id),badge=text(badge_id);
  if(!child||!badge)return blocked('CHILD_AND_BADGE_SCOPE_REQUIRED');
  if(!source || source.contract!==SOURCE_CONTRACT ||
      typeof source.loadCompleteHistory!=='function' ||
      typeof source.verifyAwardRow!=='function')
    return blocked('TRUSTED_AWARD_LEDGER_CONNECTOR_NOT_BOUND');

  let snapshot;
  try{snapshot=await source.loadCompleteHistory({child_id:child,badge_id:badge});}
  catch{return blocked('AWARD_LEDGER_READ_FAILED');}
  if(!snapshot||snapshot.kind!=='COMPLETE_CHILD_BADGE_AWARD_HISTORY'||
      snapshot.complete!==true||snapshot.child_id!==child||snapshot.badge_id!==badge||
      !text(snapshot.checkpoint)||!Array.isArray(snapshot.rows)||
      !Number.isSafeInteger(snapshot.row_count)||snapshot.row_count!==snapshot.rows.length)
    return blocked('INCOMPLETE_OR_MISMATCHED_AWARD_LEDGER_SNAPSHOT');

  let state=null, lastSequence=-1, lastId='';
  const seen=new Set();
  for(const row of snapshot.rows){
    let check;
    try{check=await source.verifyAwardRow(row,{
      child_id:child,badge_id:badge,checkpoint:snapshot.checkpoint
    });}catch{return blocked('AWARD_LEDGER_ROW_VERIFICATION_FAILED');}
    if(check?.ok!==true||!check.receipt||check.source_contract!==SOURCE_CONTRACT)
      return blocked('AWARD_LEDGER_ROW_NOT_VERIFIED');
    const receipt=check.receipt;
    if(receipt.child_id!==child||receipt.badge_id!==badge||
        receipt.authority!=='AWARD_LEDGER' ||
        receipt.source_checkpoint!==snapshot.checkpoint ||
        !Number.isSafeInteger(receipt.ledger_sequence)||
        receipt.ledger_sequence<=lastSequence)
      return blocked('VERIFIED_RECEIPT_SCOPE_OR_SEQUENCE_INVALID');
    if(!text(receipt.award_id)||seen.has(receipt.award_id))
      return blocked('DUPLICATE_OR_MISSING_VERIFIED_AWARD_ID');
    seen.add(receipt.award_id);
    lastSequence=receipt.ledger_sequence;lastId=receipt.award_id;
    const next=project(state,receipt,{tier_order});
    if(!next.ok)return blocked('AWARD_HISTORY_PROJECTION_REJECTED',next.reason);
    state=next.state;
  }
  // Empty COMPLETE history is a locked badge; never fabricate an initial award.
  return {ok:true,contract:'TAKY_BADGE_LEDGER_PROJECTION_BRIDGE_V1',
    checkpoint:snapshot.checkpoint,verified_awards:seen.size,last_award_id:lastId||null,
    ownership_state:state?'EARNED':'LOCKED',state};
}
module.exports=Object.freeze({SOURCE_CONTRACT,deriveFromLedger});
