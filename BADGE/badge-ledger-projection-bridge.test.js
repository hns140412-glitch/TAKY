'use strict';
const assert=require('node:assert/strict');
const {SOURCE_CONTRACT,deriveFromLedger}=require('./badge-ledger-projection-bridge.js');
const tier_order=['GREEN','BLUE','RED','GOLD','PLATINUM'];
const child_id='CHILD_A',badge_id='BDG_A',checkpoint='snapshot-001';
const raws=Array.from({length:6},(_,i)=>({id:'id-'+i,seq:i}));
function source(rows=raws,opts={}){
  return {
    contract:SOURCE_CONTRACT,
    async loadCompleteHistory(){
      return {kind:'COMPLETE_CHILD_BADGE_AWARD_HISTORY',
        complete:opts.complete??true,child_id:opts.child_id??child_id,
        badge_id,row_count:opts.row_count??rows.length,
        checkpoint,rows};
    },
    async verifyAwardRow(row){
      if(opts.badVerify)return {ok:false};
      return {ok:true,source_contract:SOURCE_CONTRACT,
        receipt:{
          authority:'AWARD_LEDGER',decision_status:'APPROVED',
          award_status:'AWARDED',award_id:row.id,
          child_id:opts.receiptChild??child_id,badge_id,
          award_kind:row.seq===0?'INITIAL_AWARD':'REAWARD',
          ledger_sequence:row.seq,source_checkpoint:checkpoint
        }};
    }
  };
}
(async()=>{
  const args={child_id,badge_id,tier_order};
  assert.equal((await deriveFromLedger(args)).reason,'TRUSTED_AWARD_LEDGER_CONNECTOR_NOT_BOUND');
  const none=await deriveFromLedger({...args,source:source([])});
  assert.equal(none.ok,true);
  assert.equal(none.ownership_state,'LOCKED');
  assert.equal(none.state,null);
  const first=await deriveFromLedger({...args,source:source(raws.slice(0,1))});
  assert.equal(first.ok,true);
  assert.equal(first.state.star_count,0);
  const four=await deriveFromLedger({...args,source:source(raws.slice(0,5))});
  assert.equal(four.state.star_count,4);
  const five=await deriveFromLedger({...args,source:source(raws)});
  assert.equal(five.ok,true);
  assert.equal(five.verified_awards,6);
  assert.equal(five.state.tier,'BLUE');
  assert.equal(five.state.star_count,0); // Provisional post-promotion reset.
  assert.equal((await deriveFromLedger({...args,source:source(raws,{complete:false})})).ok,false);
  assert.equal((await deriveFromLedger({...args,source:source(raws,{row_count:5})})).ok,false);
  assert.equal((await deriveFromLedger({...args,source:source(raws,{receiptChild:'CHILD_B'})})).ok,false);
  assert.equal((await deriveFromLedger({...args,source:source(raws,{badVerify:true})})).ok,false);
  assert.equal((await deriveFromLedger({...args,source:source([raws[0],raws[0]])})).ok,false);
  assert.equal((await deriveFromLedger({...args,source:source([raws[1],raws[0]])})).ok,false);
  assert.equal((await deriveFromLedger({...args,source:source(raws.slice(1))})).ok,false);
  const incomplete={contract:SOURCE_CONTRACT,async loadCompleteHistory(){throw Error('offline')},async verifyAwardRow(){return {ok:true}}};
  assert.equal((await deriveFromLedger({...args,source:incomplete})).reason,'AWARD_LEDGER_READ_FAILED');
  console.log('badge ledger bridge: PASS (complete-history, 0+5 stars, dedupe, scope, failure gates)');
})().catch(e=>{console.error(e);process.exitCode=1;});
