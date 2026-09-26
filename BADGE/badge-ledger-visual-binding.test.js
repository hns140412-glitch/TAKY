'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {createLedger}=require('./badge-award-ledger-store.js');
const {resolveBadgeDisplay}=require('./badge-ledger-visual-binding.js');
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'taky-badge-vertical-'));
const family_id='FAMILY_A',child_id='CHILD_A',badge_id='ACTIVE_BADGE_1';
const tier_order=['GREEN','BLUE','RED','GOLD','PLATINUM'];
const store=createLedger({directory,family_id,signingKey:crypto.randomBytes(32),
 verifyDecision:x=>x?.trusted===true?{ok:true,receipt:x.receipt}:{ok:false},
 isBadgeActive:x=>x.child_id===child_id&&x.badge_id===badge_id});
const record={
 badge_id,visual_id:'APPROVED_EXAMPLE_V1',name:'모의 탐험 배지',active:true,
 renderer_binding:true,asset_state:'APPROVED_RUNTIME_ASSET',
 approval_status:'APPROVED_RUNTIME_ASSET',asset_path:'tests/fixtures/approved-example.webp',
 approval_evidence_refs:['TEST_ONLY_APPROVAL_NOT_PRODUCTION']
};
const profile={authority:'CHILD_PROFILE',child_id,avatar_asset_ref:'tests/fixtures/child-a.webp'};
const args={source:store.source,child_id,badge_id,tier_order,visualRecord:record,profile};
const award=(i,award_kind)=>store.appendApprovedDecision({trusted:true,receipt:{
 decision_id:'decision-'+i,decision_ref:'test-decision-'+i,family_id,child_id,badge_id,
 decision_status:'APPROVED',award_kind,approved_at:'2026-09-26T09:00:00Z'
}});
(async()=>{
 try{
   assert.equal((await resolveBadgeDisplay({...args,source:null})).ok,false);
   let result=await resolveBadgeDisplay(args);
   assert.equal(result.ok,true);
   assert.equal(result.render_model.ownership_state,'LOCKED');
   assert.equal(result.render_model.star_count,0);
   assert.equal(result.render_model.character_overlay_ref,null);
   assert.equal((await resolveBadgeDisplay({...args,visualRecord:{...record,asset_state:'UNBOUND'}})).ok,false);
   assert.equal(award(0,'INITIAL_AWARD').ok,true);
   result=await resolveBadgeDisplay(args);
   assert.equal(result.ok,true);
   assert.equal(result.render_model.ownership_state,'EARNED');
   assert.equal(result.render_model.star_count,0);
   assert.equal(result.render_model.character_overlay_ref,profile.avatar_asset_ref);
   assert.equal((await resolveBadgeDisplay({...args,profile:{...profile,child_id:'CHILD_B'}})).ok,false);
   for(let i=1;i<=5;i++)assert.equal(award(i,'REAWARD').ok,true);
   result=await resolveBadgeDisplay(args);
   assert.equal(result.ok,true);
   assert.equal(result.verified_awards,6);
   assert.equal(result.render_model.tier,'BLUE');
   assert.equal(result.render_model.star_count,0);
   assert.equal((await resolveBadgeDisplay({...args,visualRecord:{...record,badge_id:'OTHER_BADGE'}})).ok,false);
   console.log('persisted ledger to verified silhouette/earned layered render model: PASS');
 }finally{fs.rmSync(directory,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
