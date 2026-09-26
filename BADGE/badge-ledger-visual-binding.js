'use strict';
const {deriveFromLedger}=require('./badge-ledger-projection-bridge.js');
const {buildRenderModel}=require('./badge-visual-renderer.js');
const clean=v=>typeof v==='string'?v.trim():'';

/**
 * Pure composition from a VERIFIED history, not from client-supplied ownership.
 * Callers must supply an approved registry record and the correct child profile.
 * This code never approves assets, activates catalog entries, or displays UI itself.
 */
async function resolveBadgeDisplay({source,child_id,badge_id,tier_order,visualRecord,profile={}}={}){
  const child=clean(child_id),badge=clean(badge_id);
  if(!child||!badge)return {ok:false,reason:'DISPLAY_SCOPE_REQUIRED'};
  if(!visualRecord||visualRecord.badge_id!==badge)
    return {ok:false,reason:'VISUAL_BADGE_ID_MISMATCH'};
  const projected=await deriveFromLedger({source,child_id:child,badge_id:badge,tier_order});
  if(!projected.ok)return {ok:false,reason:'VERIFIED_AWARD_HISTORY_REQUIRED',details:projected.reason};
  const earned=projected.ownership_state==='EARNED';
  const award={
    badge_id:badge,child_id:child,
    ownership_state:earned?'EARNED':'LOCKED',
    ownership_source:earned?'AWARD_LEDGER':null,
    award_status:earned?'AWARDED':null,
    tier:earned?projected.state.tier:null,
    star_count:earned?projected.state.star_count:0
  };
  const result=buildRenderModel(visualRecord,award,profile);
  if(!result.ok)return {ok:false,reason:'VISUAL_REVIEW_OR_PROFILE_NOT_READY',details:result.issues};
  return {ok:true,contract:'TAKY_BADGE_LEDGER_TO_VISUAL_V1',checkpoint:projected.checkpoint,
    verified_awards:projected.verified_awards,render_model:result};
}
module.exports=Object.freeze({resolveBadgeDisplay});
