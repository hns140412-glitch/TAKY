import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
const src=readFileSync(new URL('./badge-atlas.js',import.meta.url),'utf8');
const css=readFileSync(new URL('./badge-atlas.css',import.meta.url),'utf8');
const source=JSON.parse(readFileSync(new URL('../badge-wow-inspired-copyworking.json',import.meta.url),'utf8'));
const managed=JSON.parse(readFileSync(new URL('../assets/asset-registry-working.json',import.meta.url),'utf8'));
const registry=JSON.parse(readFileSync(new URL('../badge-visual-registry-working.json',import.meta.url),'utf8'));
const moduleUrl='data:text/javascript;base64,'+Buffer.from(src).toString('base64');
const {BADGE_COPY,badgeStars,composeBadgeArtwork}=await import(moduleUrl);
test('all 60 exact source display copy identities remain preserved',()=>{
 assert.equal(BADGE_COPY.length,60);
 assert.deepEqual(BADGE_COPY,source.preset_copy.map(x=>({
 id:x.source_draft_id,title:x.display_title_proposal,toast:x.unlock_toast_proposal,story:x.flavor_text_proposal
 })));
 assert.equal(new Set(BADGE_COPY.map(x=>x.id)).size,60);
});
test('first displayed award is one star; five tier colors reuse one shared mask',()=>{
 for(let n=1;n<=5;n++)assert.equal((badgeStars(n,'green').match(/class="badge-star"/g)||[]).length,n);
 for(const t of ['green','blue','red','gold','platinum'])assert.match(badgeStars(1,t),new RegExp('tier-'+t));
 assert.throws(()=>badgeStars(0,'green'));
 assert.throws(()=>badgeStars(1,'purple'));
 assert.match(css,/assets\/shared\/star-mask\.svg/);
});
test('all managed artwork candidates remain unapproved and unbound in runtime registry',()=>{
 assert.equal(managed.items.length,60);
 assert.equal(registry.items.length,60);
 for(let i=0;i<60;i++){
 const a=managed.items[i],r=registry.items[i];
 assert.equal(a.badge_id,r.draft_id);
 assert.equal(a.visual_id,r.visual_id);
 assert.equal(a.runtime_approved,false);
 assert.equal(a.runtime_bound,false);
 assert.equal(a.character_asset_ref,null);
 assert.equal(a.crew_asset_ref,null);
 assert.equal(r.active,false);
 assert.equal(r.renderer_binding,false);
 assert.equal(r.asset_path,null);
 assert.match(composeBadgeArtwork(BADGE_COPY[i],a,{}),/UNBOUND/);
 }
});
test('shared assets are independent of scene artwork and no sheet crop is used',()=>{
 for(const asset of ['rim','shadow','star-mask','lock'])assert.match(css,new RegExp('assets/shared/'+asset+'\\.svg'));
 assert.doesNotMatch(src,/object-position|sheet-crop/i);
 assert.match(css,/badge-character-overlay/);
 assert.match(src,/SNAP_OWNED_CREW_ASSET/);
 assert.match(src,/CHILD_PROFILE/);
});
