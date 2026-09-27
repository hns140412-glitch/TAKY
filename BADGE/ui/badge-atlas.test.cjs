'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const src=fs.readFileSync(require('node:path').join(__dirname,'badge-atlas.js'),'utf8');
const script=src.replace(/export const /g,'const ').replace(/export function /g,'function ')+
  '\n;globalThis.__test={BADGE_COPY,TIERS,badgeStars,validAsset,mountBadgeAtlas};';
const sandbox={};vm.runInNewContext(script,sandbox);
const {BADGE_COPY,TIERS,badgeStars,validAsset}=sandbox.__test;
assert.equal(BADGE_COPY.length,60,'60 distinct catalog records');
assert.equal(new Set(BADGE_COPY.map(x=>x.id)).size,60,'unique badge ids');
assert.equal(TIERS.length,5,'five tiers');
for(const tier of TIERS)for(let n=1;n<=5;n++){
  const html=badgeStars(n,tier);
  assert.equal((html.match(/class="badge-star"/g)||[]).length,n);
  assert.ok(html.includes('tier-'+tier));
}
for(const n of [0,6,-1,1.5])assert.throws(()=>badgeStars(n,'green'));
assert.throws(()=>badgeStars(1,'unknown'));
const approved=()=>({approved:true,asset_ref:'individual-file.svg'});
const a={approved:true,visualId:'BADGE_VISUAL_DRAFT_001',layers:{background:approved(),interior:approved(),frame:approved(),shadow:approved()}};
assert.equal(!!validAsset(a),true);
assert.equal(!!validAsset({...a,layers:{background:approved()}}),false,'missing layers must not be called finished');
assert.equal(!!validAsset({...a,layers:{...a.layers,crew:{approved:false,asset_ref:'unreviewed.svg'}}}),false,'unapproved overlay forbidden');
console.log('badge atlas contract: PASS — 60 unique entries, 5 tier colors, 1–5 stars, required independent layers');
