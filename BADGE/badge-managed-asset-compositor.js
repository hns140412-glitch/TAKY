'use strict';
/**
 * Read-only TAKY managed-asset composition. Additive to the existing CLOSED renderer:
 * approved character-free BASE + optional independently verified child/Crew overlays.
 * No raw activity, registry candidate, browser flag, or art file grants an award.
 */
const {buildRenderModel}=require('./badge-visual-renderer.js');
const SCENE_LAYERS=Object.freeze(['background','interior','foreground']);
const SHARED=Object.freeze({
 shadow:'assets/shared/shadow.svg',
 rim:'assets/shared/rim.svg',
 star_mask:'assets/shared/star-mask.svg',
 lock:'assets/shared/lock.svg'
});
const refOk=s=>typeof s==='string'&&s.length>0&&s.length<240&&!s.startsWith('/')&&!s.includes('..')&&!s.includes('//')&&!s.includes(':')&&!s.includes('?')&&!s.includes('#')&&/\.(png|webp|svg|avif)$/i.test(s)&&/^[a-z0-9_./-]+$/i.test(s);
const evidence=a=>Array.isArray(a)&&a.length>0&&a.every(s=>typeof s==='string'&&s.trim().length>0&&s.length<200);
const has=v=>v!==undefined&&v!==null;
const approvedLayer=l=>l&&l.approved===true&&refOk(l.asset_ref);
const slotValid=(slot,kind)=>slot&&slot.review_status==='APPROVED_LAYOUT'&&evidence(slot.reviewEvidenceRefs)&&
 Number.isInteger(slot.x)&&slot.x>=(kind==='profile'?15:60)&&slot.x<=(kind==='profile'?40:85)&&
 Number.isInteger(slot.y)&&slot.y>=55&&slot.y<=83&&Number.isInteger(slot.scale)&&slot.scale>=15&&slot.scale<=42&&
 (slot.depth==='BEHIND_FOREGROUND'||slot.depth==='ABOVE_FOREGROUND');
function overlayValid(o,kind,ownership){
 if(!o||o.approved!==true||o.approval_status!=='APPROVED_RUNTIME_ASSET'||!evidence(o.approvalEvidenceRefs)||!refOk(o.asset_ref)||
 typeof ownership?.child_id!=='string'||!ownership.child_id||o.child_id!==ownership.child_id)return false;
 if(ownership.family_id&&o.family_id!==ownership.family_id)return false;
 if(kind==='profile')return o.authority==='CHILD_PROFILE'&&typeof o.visual_id==='string'&&o.visual_id.length>0;
 return o.authority==='SNAP_OWNED_CREW_ASSET'&&o.owner==='snap-pop'&&typeof o.character_id==='string'&&o.character_id.length>0;
}
function composeManagedAsset({record,ownership,profile=null,crew=null,layout=null}={}){
 const issues=[];
 if(!record||typeof record!=='object')return {ok:false,issues:['APPROVED_VISUAL_RECORD_REQUIRED']};
 const layers=record.layers||{};
 if(!approvedLayer(layers.background)||!approvedLayer(layers.interior))issues.push('INDEPENDENT_BACKGROUND_AND_INTERIOR_REQUIRED');
 for(const [kind,asset] of Object.entries(layers))if(!SCENE_LAYERS.includes(kind)||!approvedLayer(asset))issues.push('UNAPPROVED_OR_BAKED_SHARED_OR_CHARACTER_LAYER_'+kind);
 if(ownership?.ownership_state==='EARNED'&&ownership.verified!==true)issues.push('VERIFIED_LEDGER_PROJECTION_REQUIRED');
 const earned=ownership?.ownership_state==='EARNED';
 const approvedProfile=has(profile)&&earned&&overlayValid(profile,'profile',ownership);
 const approvedCrew=has(crew)&&earned&&overlayValid(crew,'crew',ownership);
 if(has(profile)&&earned&&!approvedProfile)issues.push('INVALID_CHILD_PROFILE_OVERLAY');
 if(has(crew)&&earned&&!approvedCrew)issues.push('INVALID_SNAP_OWNED_CREW_OVERLAY');
 if((approvedProfile||approvedCrew)&&(!layout||layout.visual_id!==record.visual_id))issues.push('APPROVED_MATCHING_LAYOUT_REQUIRED');
 if(approvedProfile&&!slotValid(layout?.profile,'profile'))issues.push('APPROVED_PROFILE_SLOT_REQUIRED');
 if(approvedCrew&&!slotValid(layout?.crew,'crew'))issues.push('APPROVED_CREW_SLOT_REQUIRED');
 // An optional empty profile is not passed to the historical renderer; never make EARNED depend on a character.
 const profileForLegacy=approvedProfile?{authority:'CHILD_PROFILE',child_id:profile.child_id,avatar_asset_ref:profile.asset_ref}:{};
 const base=buildRenderModel(record,ownership||{},profileForLegacy);
 if(!base.ok)issues.push(...base.issues);
 if(issues.length)return {ok:false,issues:[...new Set(issues)]};
 const renderLayers=[
 {kind:'background',ref:layers.background.asset_ref},
 {kind:'interior',ref:layers.interior.asset_ref}
 ];
 const overlay=(kind,source)=>({kind,ref:source.asset_ref,child_id:ownership.child_id,
  x:layout[kind].x,y:layout[kind].y,scale:layout[kind].scale,depth:layout[kind].depth});
 for(const [kind,source,approved] of [['profile',profile,approvedProfile],['crew',crew,approvedCrew]])
  if(approved&&layout[kind].depth==='BEHIND_FOREGROUND')renderLayers.push(overlay(kind,source));
 if(approvedLayer(layers.foreground))renderLayers.push({kind:'foreground',ref:layers.foreground.asset_ref});
 for(const [kind,source,approved] of [['profile',profile,approvedProfile],['crew',crew,approvedCrew]])
  if(approved&&layout[kind].depth==='ABOVE_FOREGROUND')renderLayers.push(overlay(kind,source));
 return {ok:true,contract:'TAKY_BADGE_MANAGED_ASSET_COMPOSITION_V1',badge_id:base.badge_id,visual_id:base.visual_id,
   child_id:base.child_id,ownership_state:base.ownership_state,stars:base.star_count,tier:base.tier,
   layers:renderLayers,shared:SHARED,character_free_base:true,derived_from_approved_registry:true,
   overlays:earned?{profile:approvedProfile,crew:approvedCrew}:{profile:false,crew:false},
   silhouette:base.silhouette,asset_version:base.asset_version};
}
module.exports=Object.freeze({composeManagedAsset,SCENE_LAYERS,SHARED});
