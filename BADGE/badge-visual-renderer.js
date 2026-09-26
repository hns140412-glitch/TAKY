'use strict';

const APPROVED='APPROVED_RUNTIME_ASSET';

function clean(v,max=240){
  return typeof v==='string'?v.trim().slice(0,max):'';
}

function normalizeGrade(value){
  const n=Math.floor(Number(value)||0);
  return n>=1&&n<=5?n:null;
}

function buildRenderModel(record={},award={}){
  const issues=[];
  if(record.active!==true)issues.push('VISUAL_NOT_ACTIVE');
  if(record.renderer_binding!==true)issues.push('RENDERER_BINDING_DISABLED');
  if(record.asset_state!==APPROVED)issues.push('ASSET_NOT_APPROVED');
  if(record.approval_status!==APPROVED)issues.push('APPROVAL_STATUS_INVALID');
  if(!clean(record.asset_path))issues.push('ASSET_PATH_REQUIRED');
  if(!Array.isArray(record.approval_evidence_refs)||record.approval_evidence_refs.length===0)issues.push('APPROVAL_EVIDENCE_REQUIRED');

  const grade=normalizeGrade(award.grade_stars);
  if(!grade)issues.push('GRADE_STARS_1_TO_5_REQUIRED');
  if(award.repeat_count!==undefined && award.grade_stars===undefined){
    issues.push('REPEAT_COUNT_CANNOT_DERIVE_GRADE');
  }

  if(issues.length)return {ok:false,issues};

  return {
    ok:true,
    contract:'TAKY_BADGE_VISUAL_RENDER_MODEL_V1',
    badge_id:clean(award.badge_id||record.badge_id||record.draft_id,120),
    visual_id:clean(record.visual_id,120),
    title:clean(award.title||record.name,80)||'배지',
    asset_path:clean(record.asset_path),
    asset_version:clean(record.asset_version,80)||null,
    grade_stars:grade,
    tier:clean(award.tier,40)||null,
    alt:clean(award.alt,160)||`${clean(award.title||record.name,80)||'배지'} · ${grade}성급`,
    semantics:{
      stars:'GRADE_CLASSIFICATION',
      repeat_count_affects_stars:false,
      gem_affects_stars:false,
      exp_affects_stars:false,
      affinity_affects_stars:false,
      power_effect:false
    }
  };
}

function renderInto(host,record={},award={},doc=globalThis.document){
  if(!host||typeof host.replaceChildren!=='function')return {ok:false,issues:['HOST_REQUIRED']};
  const model=buildRenderModel(record,award);
  if(!model.ok){
    host.replaceChildren();
    host.dataset.badgeVisualState='UNBOUND_OR_UNAPPROVED';
    return model;
  }
  if(!doc?.createElement)return {ok:false,issues:['DOCUMENT_REQUIRED']};

  const figure=doc.createElement('figure');
  figure.dataset.badgeVisualId=model.visual_id;
  figure.dataset.badgeGrade=String(model.grade_stars);
  const img=doc.createElement('img');
  img.src=model.asset_path;
  img.alt=model.alt;
  img.decoding='async';
  const caption=doc.createElement('figcaption');
  caption.textContent=model.title;
  figure.append(img,caption);
  host.replaceChildren(figure);
  host.dataset.badgeVisualState='APPROVED_BOUND';
  return model;
}

module.exports=Object.freeze({buildRenderModel,renderInto});
