'use strict';

const APPROVED='APPROVED_RUNTIME_ASSET';
const clean=(value,max=240)=>typeof value==='string'?value.trim().slice(0,max):'';
const validStars=n=>Number.isInteger(n)&&n>=0&&n<=5;
function buildRenderModel(record={},ownership={},profile={}){
  const issues=[];
  if(record.active!==true)issues.push('REGISTRY_VISUAL_NOT_ACTIVE');
  if(record.renderer_binding!==true)issues.push('RENDERER_BINDING_DISABLED');
  if(record.asset_state!==APPROVED||record.approval_status!==APPROVED)issues.push('ASSET_NOT_APPROVED');
  if(!clean(record.asset_path))issues.push('ASSET_PATH_REQUIRED');
  if(!Array.isArray(record.approval_evidence_refs)||record.approval_evidence_refs.length===0)issues.push('APPROVAL_EVIDENCE_REQUIRED');
  const state=ownership.ownership_state;
  if(!['LOCKED','EARNED'].includes(state))issues.push('OWNERSHIP_STATE_REQUIRED');
  if(ownership.grade_stars!==undefined)issues.push('OBSOLETE_GRADE_STARS_FORBIDDEN');
  if(ownership.repeat_count!==undefined&&ownership.star_count===undefined)issues.push('TELEMETRY_REPEAT_CANNOT_DERIVE_STARS');
  const stars=ownership.star_count;
  if(!validStars(stars))issues.push('REAWARD_STAR_COUNT_0_TO_5_REQUIRED');
  if(state==='LOCKED'&&stars!==0)issues.push('LOCKED_BADGE_CANNOT_HAVE_REAWARD_STARS');
  const childId=clean(ownership.child_id),profileChildId=clean(profile?.child_id);
  // The approved badge BASE may render on its own. A profile overlay is optional,
  // but if supplied it must be complete and scoped to this child.
  const profileProvided=profile!=null&&typeof profile==='object'&&Object.keys(profile).length>0;
  if(!childId)issues.push('CHILD_SCOPE_REQUIRED');
  if(state==='EARNED'){
    if(ownership.ownership_source!=='AWARD_LEDGER'||ownership.award_status!=='AWARDED')issues.push('VERIFIED_AWARD_OWNERSHIP_REQUIRED');
    if(!clean(ownership.tier))issues.push('TIER_REQUIRED');
    if(profileProvided&&(profile.authority!=='CHILD_PROFILE'||!profileChildId||profileChildId!==childId||!clean(profile.avatar_asset_ref)))
      issues.push('MATCHING_CHILD_PROFILE_OVERLAY_REQUIRED');
  }
  if(state==='LOCKED'&&profileChildId&&profileChildId!==childId)issues.push('CROSS_CHILD_PROFILE_FORBIDDEN');
  if(issues.length)return {ok:false,issues};
  const title=clean(ownership.title||record.name,80)||'탐험 배지';
  return {ok:true,contract:'TAKY_BADGE_VISUAL_RENDER_MODEL_V2',
    badge_id:clean(ownership.badge_id||record.badge_id||record.draft_id,120),
    visual_id:clean(record.visual_id,120),title,
    base_asset_path:clean(record.asset_path),
    asset_version:clean(record.asset_version,80)||null,
    child_id:childId,ownership_state:state,tier:clean(ownership.tier,40)||null,
    star_count:stars,
    character_overlay_ref:state==='EARNED'&&profileProvided?clean(profile.avatar_asset_ref):null,
    silhouette:state==='LOCKED',
    border_fx:'SOFT_RADIAL_GRADIENT_FADE',
    insignia_style:'FICTIONAL_EXPLORATION_CREW_CAMPAIGN_MERIT_INSIGNIA',
    alt:state==='LOCKED'?'미획득 탐험 배지 실루엣':title+' · '+clean(ownership.tier,40)+' · 재획득 별 '+stars+'개',
    semantics:{stars:'VERIFIED_REAWARDS_WITHIN_TIER',initial_award_unlocks:true,
      five_stars_promote_tier:true,telemetry_repeat_is_not_reaward:true,
      gem_affects_stars:false,exp_affects_stars:false,affinity_affects_stars:false,
      power_effect:false}
  };
}
function renderInto(host,record={},ownership={},profile={},doc=globalThis.document){
  if(!host||typeof host.replaceChildren!=='function')return {ok:false,issues:['HOST_REQUIRED']};
  const model=buildRenderModel(record,ownership,profile);
  if(!model.ok){
    host.replaceChildren();
    if(host.dataset)host.dataset.badgeVisualState='UNBOUND_OR_UNAPPROVED';
    return model;
  }
  if(!doc?.createElement)return {ok:false,issues:['DOCUMENT_REQUIRED']};
  const figure=doc.createElement('figure');
  figure.className='takyBadgeInsignia';
  figure.dataset.badgeVisualId=model.visual_id;
  figure.dataset.badgeState=model.ownership_state;
  figure.dataset.badgeStars=String(model.star_count);
  const base=doc.createElement('img');
  base.className='takyBadgeBaseArt';
  base.src=model.base_asset_path;
  base.alt=model.alt;
  base.decoding='async';
  figure.append(base);
  if(model.character_overlay_ref){
    const character=doc.createElement('img');
    character.className='takyBadgeCharacterLayer';
    character.src=model.character_overlay_ref;
    character.alt='';
    character.decoding='async';
    figure.append(character);
  }
  // The upper-arc ornament represents earned reacquisitions only: zero has no stars.
  // Keep the art and child profile separate from the progress ornament.
  if(model.ownership_state==='EARNED'&&model.star_count>0){
    const stars=doc.createElement('div');
    stars.className='takyBadgeReawardStars';
    stars.setAttribute('aria-label','재획득 별 '+model.star_count+'개');
    for(let i=0;i<model.star_count;i++){
      const star=doc.createElement('span');
      star.className='takyBadgeReawardStar';
      star.setAttribute('aria-hidden','true');
      // CSS draws the medal ornament, not a platform-dependent text glyph.
      stars.append(star);
    }
    figure.append(stars);
  }
  const caption=doc.createElement('figcaption');
  caption.textContent=model.title;
  figure.append(caption);
  host.replaceChildren(figure);
  if(host.dataset)host.dataset.badgeVisualState=model.ownership_state;
  return model;
}
module.exports=Object.freeze({buildRenderModel,renderInto});
