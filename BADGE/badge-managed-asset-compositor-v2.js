'use strict';
const {buildRenderModel}=require('./badge-visual-renderer.js');
const ART=Object.freeze(['base','bg','subject','fx']);
const SHARED=Object.freeze({shadow:'assets/shared/shadow.svg',rim:'assets/shared/rim.svg',star_mask:'assets/shared/star-mask.svg',lock:'assets/shared/lock.svg'});
const refOk=s=>typeof s==='string'&&s.length>0&&s.length<240&&!s.startsWith('/')&&!s.includes('..')&&!s.includes('//')&&!s.includes(':')&&!s.includes('?')&&!s.includes('#')&&/\.(png|webp|svg|avif)$/i.test(s)&&/^[a-z0-9_./-]+$/i.test(s);
const evidence=a=>Array.isArray(a)&&a.length>0&&a.every(s=>typeof s==='string'&&s.trim().length>0&&s.length<200);
const layerOk=l=>l&&l.approved===true&&refOk(l.asset_ref);
const overlayOk=(o,kind,own)=>o&&o.approved===true&&o.approval_status==='APPROVED_RUNTIME_ASSET'&&evidence(o.approvalEvidenceRefs)&&refOk(o.asset_ref)&&o.child_id===own.child_id&&(!own.family_id||o.family_id===own.family_id)&&(kind==='profile'?o.authority==='CHILD_PROFILE'&&!!o.visual_id:o.authority==='SNAP_OWNED_CREW_ASSET'&&o.owner==='snap-pop'&&!!o.character_id);
const slotOk=(s,kind)=>s&&s.review_status==='APPROVED_LAYOUT'&&evidence(s.reviewEvidenceRefs)&&Number.isInteger(s.x)&&Number.isInteger(s.y)&&Number.isInteger(s.scale)&&['BEHIND_SUBJECT','ABOVE_SUBJECT','ABOVE_FX'].includes(s.depth);
function composeManagedAssetV2({record,ownership,profile=null,crew=null,layout=null}={}){
 const issues=[];if(!record)return {ok:false,issues:['APPROVED_VISUAL_RECORD_REQUIRED']};
 for(const k of ART)if(!layerOk(record.layers?.[k]))issues.push('APPROVED_'+k.toUpperCase()+'_REQUIRED');
 for(const k of Object.keys(record.layers||{}))if(!ART.includes(k))issues.push('UNKNOWN_OR_BAKED_LAYER_'+k);
 const earned=ownership?.ownership_state==='EARNED';
 const p=earned&&profile?overlayOk(profile,'profile',ownership):false,c=earned&&crew?overlayOk(crew,'crew',ownership):false;
 if(earned&&profile&&!p)issues.push('INVALID_CHILD_PROFILE_OVERLAY');
 if(earned&&crew&&!c)issues.push('INVALID_CURRENT_CREW_OVERLAY');
 if((p||c)&&layout?.visual_id!==record.visual_id)issues.push('MATCHING_LAYOUT_REQUIRED');
 if(p&&!slotOk(layout?.profile,'profile'))issues.push('PROFILE_SLOT_REQUIRED');
 if(c&&!slotOk(layout?.crew,'crew'))issues.push('CREW_SLOT_REQUIRED');
 const legacyRecord={...record,layers:{}};const base=buildRenderModel(legacyRecord,ownership||{},p?{authority:'CHILD_PROFILE',child_id:profile.child_id,avatar_asset_ref:profile.asset_ref}:{});
 if(!base.ok)issues.push(...base.issues);if(issues.length)return {ok:false,issues:[...new Set(issues)]};
 const layers=[];const addOverlay=(kind,o)=>layers.push({kind,ref:o.asset_ref,x:layout[kind].x,y:layout[kind].y,scale:layout[kind].scale});
 layers.push({kind:'base',ref:record.layers.base.asset_ref},{kind:'bg',ref:record.layers.bg.asset_ref});
 if(p&&layout.profile.depth==='BEHIND_SUBJECT')addOverlay('profile',profile);if(c&&layout.crew.depth==='BEHIND_SUBJECT')addOverlay('crew',crew);
 layers.push({kind:'subject',ref:record.layers.subject.asset_ref});
 if(p&&layout.profile.depth==='ABOVE_SUBJECT')addOverlay('profile',profile);if(c&&layout.crew.depth==='ABOVE_SUBJECT')addOverlay('crew',crew);
 layers.push({kind:'fx',ref:record.layers.fx.asset_ref});
 if(p&&layout.profile.depth==='ABOVE_FX')addOverlay('profile',profile);if(c&&layout.crew.depth==='ABOVE_FX')addOverlay('crew',crew);
 return {ok:true,contract:'TAKY_BADGE_MANAGED_ASSET_COMPOSITION_V2',badge_id:base.badge_id,visual_id:base.visual_id,child_id:base.child_id,
 ownership_state:base.ownership_state,stars:base.star_count,tier:base.tier,layers,shared:SHARED,character_free_art:true,
 overlay_resolution:'RUNTIME_CURRENT_POINTERS_NOT_BAKED',overlays:{profile:!!p,crew:!!c},silhouette:base.silhouette};
}
module.exports=Object.freeze({composeManagedAssetV2,ART,SHARED});
