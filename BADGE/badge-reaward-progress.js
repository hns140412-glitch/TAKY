'use strict';

// Projection only: the authoritative Award Ledger verifies each receipt before calling this.
const CONTRACT='TAKY_BADGE_REAWARD_PROGRESS_V1';
const text=v=>typeof v==='string'?v.trim():'';
const blocked=reason=>({ok:false,reason});
function project(state=null,receipt={},configuration={}){
  const tiers=configuration.tier_order;
  if(!Array.isArray(tiers)||tiers.length<2||tiers.some(x=>!text(x))||new Set(tiers).size!==tiers.length)
    return blocked('EXPLICIT_TIER_ORDER_REQUIRED');
  if(receipt.authority!=='AWARD_LEDGER'||receipt.decision_status!=='APPROVED'||receipt.award_status!=='AWARDED')
    return blocked('APPROVED_AWARD_LEDGER_RECEIPT_REQUIRED');
  const id=text(receipt.award_id), child=text(receipt.child_id), badge=text(receipt.badge_id);
  if(!id||!child||!badge)return blocked('AWARD_ID_AND_SCOPE_REQUIRED');
  if(!['INITIAL_AWARD','REAWARD'].includes(receipt.award_kind))return blocked('AWARD_KIND_REQUIRED');
  if(state&&((state.child_id!==child)||(state.badge_id!==badge)))return blocked('CROSS_MEMBER_OR_BADGE_STATE_FORBIDDEN');
  const seen=state?.processed_award_ids||[];
  if(!Array.isArray(seen))return blocked('LEDGER_RECEIPT_HISTORY_INVALID');
  if(seen.includes(id))return blocked('DUPLICATE_AWARD_RECEIPT');
  if(!state||state.owned!==true){
    if(receipt.award_kind!=='INITIAL_AWARD')return blocked('INITIAL_AWARD_REQUIRED');
    return {ok:true,contract:CONTRACT,tier_up:false,
      state:{child_id:child,badge_id:badge,owned:true,tier:tiers[0],tier_index:0,
        star_count:0,processed_award_ids:[...seen,id],top_tier_rule_pending:false}};
  }
  if(receipt.award_kind!=='REAWARD')return blocked('REAWARD_KIND_REQUIRED');
  if(state.top_tier_rule_pending===true)return blocked('TOP_TIER_RULE_PENDING');
  const index=tiers.indexOf(state.tier);
  if(index<0||index!==state.tier_index||!Number.isInteger(state.star_count)||state.star_count<0||state.star_count>4)
    return blocked('INVALID_CURRENT_PROGRESS_STATE');
  const nextStars=state.star_count+1;
  const tierUp=nextStars===5&&index<tiers.length-1;
  const topPending=nextStars===5&&index===tiers.length-1;
  return {ok:true,contract:CONTRACT,tier_up:tierUp,
    stars_collected_before_promotion:tierUp?5:null,
    state:{...state,tier:tierUp?tiers[index+1]:state.tier,tier_index:tierUp?index+1:index,
      star_count:tierUp?0:nextStars,top_tier_rule_pending:topPending,
      processed_award_ids:[...seen,id]}};
}
module.exports=Object.freeze({CONTRACT,project});
