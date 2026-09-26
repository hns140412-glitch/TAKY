'use strict';
const assert=require('node:assert/strict');
const api=require('./badge-visual-renderer.js');
const approved={
 draft_id:'BDG-DRAFT-001',name:'해뜰락말락',visual_id:'BADGE_VISUAL_DRAFT_001',
 active:true,renderer_binding:true,asset_state:'APPROVED_RUNTIME_ASSET',approval_status:'APPROVED_RUNTIME_ASSET',
 asset_path:'assets/badges/approved/bdg-001.webp',asset_version:'v1',approval_evidence_refs:['APPROVAL_REF']
};
const child={authority:'CHILD_PROFILE',child_id:'CHILD_A',avatar_asset_ref:'assets/profiles/child-a.webp'};
const earned={badge_id:'BDG-DRAFT-001',child_id:'CHILD_A',ownership_state:'EARNED',
 ownership_source:'AWARD_LEDGER',award_status:'AWARDED',tier:'GREEN',star_count:3};
const render=api.buildRenderModel(approved,earned,child);
assert.equal(render.ok,true);
assert.equal(render.star_count,3);
assert.equal(render.character_overlay_ref,child.avatar_asset_ref);
const earnedBaseOnly=api.buildRenderModel(approved,earned);
assert.equal(earnedBaseOnly.ok,true);
assert.equal(earnedBaseOnly.ownership_state,'EARNED');
assert.equal(earnedBaseOnly.character_overlay_ref,null);
assert.equal(api.buildRenderModel(approved,earned,{authority:'CHILD_PROFILE',child_id:'CHILD_A'}).ok,false);
assert.equal(api.buildRenderModel(approved,earned,{authority:'CHILD_PROFILE',child_id:'CHILD_B',avatar_asset_ref:child.avatar_asset_ref}).ok,false);

assert.equal(render.border_fx,'SOFT_RADIAL_GRADIENT_FADE');
assert.equal(render.semantics.five_stars_promote_tier,true);
assert.equal(render.semantics.telemetry_repeat_is_not_reaward,true);
const locked=api.buildRenderModel(approved,{child_id:'CHILD_A',ownership_state:'LOCKED',star_count:0});
assert.equal(locked.ok,true);
assert.equal(locked.silhouette,true);
assert.equal(locked.character_overlay_ref,null);
assert.equal(api.buildRenderModel(approved,{...earned,grade_stars:3},child).ok,false);
assert.equal(api.buildRenderModel(approved,{...earned,star_count:6},child).ok,false);
assert.equal(api.buildRenderModel(approved,{...earned,ownership_source:'ACTIVITY_TELEMETRY'},child).ok,false);
assert.equal(api.buildRenderModel(approved,{...earned,child_id:'CHILD_B'},child).ok,false);
assert.equal(api.buildRenderModel({...approved,asset_state:'UNBOUND'},earned,child).ok,false);
assert.equal(api.buildRenderModel(approved,{...earned,repeat_count:100,star_count:3},child).star_count,3);
class FakeNode {
  constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=[...children];}
  setAttribute(key,value){this.attributes[key]=value;}
}
const doc={createElement:tag=>new FakeNode(tag)};
const host=new FakeNode('div');
assert.equal(api.renderInto(host,approved,earned,child,doc).ok,true);
assert.equal(host.dataset.badgeVisualState,'EARNED');
assert.equal(host.children[0].children.filter(x=>x.className==='takyBadgeCharacterLayer').length,1);
assert.equal(api.renderInto(host,approved,earned,{},doc).ok,true);
assert.equal(host.dataset.badgeVisualState,'EARNED');
assert.equal(host.children[0].children.filter(x=>x.className==='takyBadgeCharacterLayer').length,0);

assert.equal(api.renderInto(host,approved,{child_id:'CHILD_A',ownership_state:'LOCKED',star_count:0},{},doc).ok,true);
assert.equal(host.dataset.badgeVisualState,'LOCKED');
assert.equal(host.children[0].children.filter(x=>x.className==='takyBadgeCharacterLayer').length,0);
assert.equal(api.renderInto(host,{...approved,asset_state:'UNBOUND'},earned,child,doc).ok,false);
assert.equal(host.children.length,0);
assert.equal(host.dataset.badgeVisualState,'UNBOUND_OR_UNAPPROVED');
const css=require('node:fs').readFileSync(require('node:path').join(__dirname,'badge-visual-presentation.css'),'utf8');
assert.match(css,/radial-gradient/);
assert.match(css,/data-badge-state="LOCKED"/);
console.log('badge visual renderer reaward and layered states: PASS');
