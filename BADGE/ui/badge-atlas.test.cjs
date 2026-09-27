'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const src=fs.readFileSync(path.join(__dirname,'badge-atlas.js'),'utf8');
const script=src.replace(/export const /g,'const ').replace(/export function /g,'function ')+
 '\n;globalThis.__test={BADGE_COPY,TIERS,badgeStars,validAsset,validOverlay,validPlacement,verifiedAward,composeBadgeArtwork,mountBadgeAtlas};';
const sandbox={};vm.runInNewContext(script,sandbox);
const {BADGE_COPY,TIERS,badgeStars,validAsset,validOverlay,validPlacement,verifiedAward,composeBadgeArtwork}=sandbox.__test;
assert.equal(BADGE_COPY.length,60,'60 distinct source records');
assert.equal(new Set(BADGE_COPY.map(x=>x.id)).size,60,'unique original badge ids');
assert.equal(TIERS.length,5);
for(const tier of TIERS)for(let n=1;n<=5;n++){
 const html=badgeStars(n,tier);
 assert.equal((html.match(/class="badge-star"/g)||[]).length,n);
 assert.ok(html.includes('tier-'+tier));
}
for(const n of [0,6,-1,1.5])assert.throws(()=>badgeStars(n,'green'));
assert.throws(()=>badgeStars(1,'unknown'));
const layer=ref=>({approved:true,asset_ref:ref});
const evidence=['REVIEWED_ASSET_RECEIPT'];
const layout=()=>({x:24,y:72,scale:35,depth:'BEHIND_FOREGROUND',review_status:'APPROVED_LAYOUT',reviewEvidenceRefs:['REVIEWED_LAYOUT_RECEIPT']});
const crewSlot=()=>({x:77,y:76,scale:27,depth:'ABOVE_FOREGROUND',review_status:'APPROVED_LAYOUT',reviewEvidenceRefs:['REVIEWED_LAYOUT_RECEIPT']});
const a={approved:true,active:true,renderer_binding:true,
 asset_state:'APPROVED_RUNTIME_ASSET',approval_status:'APPROVED_RUNTIME_ASSET',approvalEvidenceRefs:evidence,
 visualId:'BADGE_VISUAL_DRAFT_001',
 layers:{background:layer('approved/background.svg'),interior:layer('approved/interior.svg'),foreground:layer('approved/foreground.svg')},
 overlay_slots:{profile:layout(),crew:crewSlot()}};
assert.equal(!!validAsset(a),true,'approved base independent of any child character');
assert.equal(!!validAsset({...a,approved:false}),false,'candidate cannot become a runtime base');
assert.equal(!!validAsset({...a,layers:{}}),false,'real individual layer file required');
assert.equal(!!validAsset({...a,approvalEvidenceRefs:[]}),false,'no evidence, no runtime art');
assert.equal(!!validAsset({...a,layers:{...a.layers,crew:layer('crew/inline.svg')}}),false,'no baked-in crew in badge base');
assert.equal(!!validAsset({...a,layers:{...a.layers,frame:layer('shared/copy.svg')}}),false,'duplicated per-badge rim forbidden');
for(const bad of ['https://host/x.svg','//host/x.svg','/root/x.svg','../private/x.svg','foo.svg?token=123']){
 assert.equal(!!validAsset({...a,layers:{...a.layers,interior:layer(bad)}}),false,'reject unsafe ref '+bad);
}
const badge=BADGE_COPY[0];
const award={verified:true,ownership_source:'AWARD_LEDGER',award_status:'AWARDED',child_id:'CHILD_A',family_id:'FAMILY_A',stars:1,tier:'green'};
assert.equal(verifiedAward(award),true);
assert.equal(verifiedAward({...award,verified:false}),false);
assert.equal(verifiedAward({...award,child_id:''}),false);
const profile={approved:true,approval_status:'APPROVED_RUNTIME_ASSET',approvalEvidenceRefs:evidence,asset_ref:'profiles/child-a.webp',child_id:'CHILD_A',family_id:'FAMILY_A',authority:'CHILD_PROFILE',visual_id:'CHILD_VISUAL_A'};
const crew={approved:true,approval_status:'APPROVED_RUNTIME_ASSET',approvalEvidenceRefs:evidence,asset_ref:'crew/snap-owned.webp',child_id:'CHILD_A',family_id:'FAMILY_A',authority:'SNAP_OWNED_CREW_ASSET',owner:'snap-pop',character_id:'SNAP_CREW_CONFIRMED'};
assert.equal(validOverlay(profile,'profile',award),true);
assert.equal(validOverlay(crew,'crew',award),true);
assert.equal(validPlacement(layout(),'profile'),true);
assert.equal(validPlacement({...layout(),y:10},'profile'),false,'star arc is safe');
assert.equal(validPlacement({...layout(),scale:95},'profile'),false);
assert.equal(validPlacement({...crewSlot(),review_status:'PROVISIONAL_UNTIL_FINAL_INDIVIDUAL_ART'},'crew'),false);
assert.equal(validOverlay({...profile,child_id:'CHILD_B'},'profile',award),false,'cross-child denies overlay');
assert.equal(validOverlay({...profile,family_id:'FAMILY_B'},'profile',award),false,'cross-family denies overlay');
assert.equal(validOverlay({...crew,owner:'ready-set'},'crew',award),false,'Snap is crew owner');
assert.equal(validOverlay({...crew,approvalEvidenceRefs:[]},'crew',award),false);
const plain=composeBadgeArtwork(badge,a,award,{});
assert.ok(plain.includes('badge-art-background')&&plain.includes('badge-art-interior'));
assert.ok(!plain.includes('badge-character-overlay'),'approved base-only is complete');
const joined=composeBadgeArtwork(badge,a,award,{profile,crew});
assert.equal((joined.match(/badge-character-overlay/g)||[]).length,2,'independent optional profile and crew layers');
assert.ok(joined.indexOf('badge-art-interior')<joined.indexOf('badge-character-profile'));
assert.ok(joined.indexOf('badge-character-profile')<joined.indexOf('badge-art-foreground'));
assert.ok(joined.indexOf('badge-art-foreground')<joined.indexOf('badge-character-crew'),'reviewed front depth');
assert.equal((joined.match(/badge-art-foreground/g)||[]).length,1);
assert.ok(!joined.includes('badge-star')&&!joined.includes('badge-rim'),'no per-badge ornaments baked into scene HTML');
assert.ok(composeBadgeArtwork(badge,a,award,{profile:{...profile,child_id:'CHILD_B'}}).includes('INVALID_OVERLAY'));
assert.ok(composeBadgeArtwork(badge,a,award,{crew:{...crew,owner:'ready-set'}}).includes('INVALID_OVERLAY'));
assert.ok(composeBadgeArtwork(badge,{...a,approved:false},award,{profile}).includes('UNBOUND'));
assert.ok(composeBadgeArtwork(badge,{...a,overlay_slots:{...a.overlay_slots,profile:{...layout(),review_status:'PROVISIONAL_UNTIL_FINAL_INDIVIDUAL_ART'}}},award,{profile}).includes('INVALID_OVERLAY'));
const locked=composeBadgeArtwork(badge,a,{child_id:'CHILD_A',stars:0},{profile,crew});
assert.ok(!locked.includes('badge-character-overlay'),'locked never leaks private overlays');
for(const filename of ['rim.svg','shadow.svg','star-mask.svg','lock.svg']){
 assert.ok(fs.existsSync(path.join(__dirname,'..','assets','shared',filename)),'single reusable asset '+filename);
}
const css=fs.readFileSync(path.join(__dirname,'badge-atlas.css'),'utf8');
assert.match(css,/assets\/shared\/rim\.svg/);
assert.match(css,/badge-character-front/);
assert.match(css,/prefers-reduced-motion/);
console.log('Badge atlas overlay contract PASS — 60 identities, approved base-only, separate optional same-child overlays, safe placement, shared assets, fail closed.');
// Keep the original ES-module source/copy and candidate-registry regressions in the existing CI entry point.
require('node:child_process').execFileSync(process.execPath,['--test',path.join(__dirname,'badge-atlas.test.mjs')],{stdio:'inherit'});
