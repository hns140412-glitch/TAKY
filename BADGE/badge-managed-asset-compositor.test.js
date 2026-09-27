'use strict';
const assert=require('node:assert/strict');
const {composeManagedAsset,SHARED}=require('./badge-managed-asset-compositor.js');
const approvedLayer=ref=>({approved:true,asset_ref:ref});
const registry={badge_id:'BDG-DRAFT-001',draft_id:'BDG-DRAFT-001',visual_id:'BADGE_VISUAL_DRAFT_001',name:'해뜰락말락',
 active:true,renderer_binding:true,asset_state:'APPROVED_RUNTIME_ASSET',approval_status:'APPROVED_RUNTIME_ASSET',
 approval_evidence_refs:['TEST_ONLY_ASSET_APPROVAL'],asset_path:'assets/badges/approved/001-base.webp',asset_version:'test-v1',
 layers:{background:approvedLayer('assets/badges/001/background.webp'),interior:approvedLayer('assets/badges/001/interior.webp'),
 foreground:approvedLayer('assets/badges/001/foreground.webp')}};
const ownership={badge_id:'BDG-DRAFT-001',child_id:'CHILD_A',family_id:'FAMILY_A',verified:true,
 ownership_state:'EARNED',ownership_source:'AWARD_LEDGER',award_status:'AWARDED',tier:'GREEN',star_count:1};
const layout={visual_id:registry.visual_id,
 profile:{x:24,y:72,scale:35,depth:'BEHIND_FOREGROUND',review_status:'APPROVED_LAYOUT',reviewEvidenceRefs:['TEST_ONLY_LAYOUT_APPROVAL']},
 crew:{x:77,y:76,scale:27,depth:'ABOVE_FOREGROUND',review_status:'APPROVED_LAYOUT',reviewEvidenceRefs:['TEST_ONLY_LAYOUT_APPROVAL']}};
const baseOverlay={approved:true,approval_status:'APPROVED_RUNTIME_ASSET',
 approvalEvidenceRefs:['TEST_ONLY_INDIVIDUAL_OVERLAY_APPROVAL'],child_id:'CHILD_A',family_id:'FAMILY_A'};
const profile={...baseOverlay,asset_ref:'assets/profiles/approved/child.webp',authority:'CHILD_PROFILE',visual_id:'CHILD_VISUAL_A'};
const crew={...baseOverlay,asset_ref:'assets/snap-approved/crew.webp',authority:'SNAP_OWNED_CREW_ASSET',owner:'snap-pop',character_id:'SNAP_CREW_APPROVED_ID'};
const basic=composeManagedAsset({record:registry,ownership});
assert.equal(basic.ok,true,'character-free base is valid and earned');
assert.equal(basic.overlays.profile,false);
assert.deepEqual(basic.layers.map(x=>x.kind),['background','interior','foreground']);
assert.equal(basic.stars,1);
const mixed=composeManagedAsset({record:registry,ownership,profile,crew,layout});
assert.equal(mixed.ok,true,JSON.stringify(mixed.issues));
assert.deepEqual(mixed.layers.map(x=>x.kind),['background','interior','profile','foreground','crew']);
assert.deepEqual(mixed.overlays,{profile:true,crew:true});
assert.equal(mixed.layers[2].x,24);
assert.equal(mixed.layers[4].x,77);
assert.equal(SHARED.rim,'assets/shared/rim.svg');
assert.equal(composeManagedAsset({record:registry,ownership:{...ownership,verified:false}}).ok,false);
assert.equal(composeManagedAsset({record:{...registry,active:false},ownership}).ok,false);
assert.equal(composeManagedAsset({record:{...registry,approval_status:'NOT_APPROVED'},ownership}).ok,false);
assert.equal(composeManagedAsset({record:{...registry,layers:{...registry.layers,crew:approvedLayer('assets/crew/baked.webp')}},ownership}).ok,false,'no baked crew');
assert.equal(composeManagedAsset({record:{...registry,layers:{...registry.layers,frame:approvedLayer('assets/badges/001/rim.svg')}},ownership}).ok,false,'no per-badge rim');
assert.equal(composeManagedAsset({record:{...registry,layers:{interior:approvedLayer('a.svg')}},ownership}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,profile:{...profile,child_id:'CHILD_B'},layout}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,profile:{...profile,family_id:'FAMILY_B'},layout}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,profile:{...profile,approvalEvidenceRefs:[]},layout}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,crew:{...crew,owner:'ready-set'},layout}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,crew:{...crew,asset_ref:'//evil/crew.webp'},layout}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,profile,layout:{...layout,profile:{...layout.profile,y:9}}}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,profile,layout:{...layout,profile:{...layout.profile,review_status:'PROVISIONAL'}}}).ok,false);
assert.equal(composeManagedAsset({record:registry,ownership,profile,layout:{...layout,visual_id:'BADGE_VISUAL_DRAFT_002'}}).ok,false);
const locked=composeManagedAsset({record:registry,ownership:{child_id:'CHILD_A',family_id:'FAMILY_A',ownership_state:'LOCKED',star_count:0},
profile,crew,layout});
assert.equal(locked.ok,true);
assert.deepEqual(locked.layers.map(x=>x.kind),['background','interior','foreground'],'no private overlay in locked state');
assert.equal(locked.silhouette,true);
console.log('Managed Badge composition PASS — base-only, approved dual overlays, child/family/Snap scope, scene depth, shared assets, zero auto promotion');
