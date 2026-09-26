'use strict';
const assert=require('node:assert/strict');
const catalog=require('./badge-60-story-20-history-working.json');
const source=require('./badge-visual-registry-working.json');
const {validateStoryCatalog,suggestHistoryDiscoveries}=require('./badge-story-discovery.js');
let valid=validateStoryCatalog(catalog,source);
assert.equal(valid.ok,true,JSON.stringify(valid.issues));
assert.deepEqual(valid.counts.rankCount,{POCKET:20,FIELD:20,EXPEDITION:14,SECRET:6});
assert.equal(catalog.presets.length,60);
assert.equal(catalog.history_discovery_templates.length,20);
assert.equal(catalog.presets[0].stable_name,'해뜰락말락');
assert.equal(catalog.presets[59].stable_name,'오늘 좀 특별한데?');
assert.equal(source.items.every(x=>x.active===false&&x.renderer_binding===false&&x.asset_state==='UNBOUND'),true);
const corrupted=structuredClone(catalog);
corrupted.presets[0].stable_name='changed';
assert.equal(validateStoryCatalog(corrupted,source).ok,false);
const auto=structuredClone(catalog);
auto.presets[0].auto_award=true;
assert.equal(validateStoryCatalog(auto,source).ok,false);
const direct=structuredClone(catalog);
direct.history_discovery_templates[0].award_status='AWARDED';
assert.equal(validateStoryCatalog(direct,source).ok,false);
const family_id='FAMILY_A',child_id='CHILD_A';
const verify=(input)=>({
 ok:input?.trusted===true,
 receipt:input?.trusted?{receipt_id:input.id,kind:input.kind,
   family_id:input.family_id,child_id:input.child_id,status:'VERIFIED_HISTORY_EVIDENCE'}:null
});
const record=(id,kind,who=child_id,which=family_id)=>({
 trusted:true,id,kind,child_id:who,family_id:which
});
const args={catalog,family_id,child_id,verifyEvidence:verify};
assert.equal(suggestHistoryDiscoveries({...args,evidence_records:[]}).proposal_count,0);
assert.equal(suggestHistoryDiscoveries({...args,evidence_records:[],verifyEvidence:null}).reason,'TRUSTED_EVIDENCE_VERIFIER_REQUIRED');
const first=catalog.history_discovery_templates[0];
const onlyOne=suggestHistoryDiscoveries({...args,evidence_records:[record('e1',first.required_evidence_kinds[0])]});
assert.equal(onlyOne.proposal_count,0);
const pair=first.required_evidence_kinds.map((kind,i)=>record('rec-'+i,kind));
const found=suggestHistoryDiscoveries({...args,evidence_records:pair});
assert.equal(found.ok,true);assert.equal(found.proposal_count,1);
assert.equal(found.proposals[0].template_id,'HIST-DISCOVERY-001');
assert.equal(found.proposals[0].proposal_status,'REVIEW_REQUIRED_NOT_AWARD');
assert.equal(found.proposals[0].award_id,null);
assert.equal(found.proposals[0].ownership_state,null);
assert.equal(found.proposals[0].asset_status,'UNBOUND_NOT_APPROVED');
assert.equal(suggestHistoryDiscoveries({...args,evidence_records:[...pair,pair[0]]}).reason,'UNVERIFIED_DUPLICATE_OR_CROSS_CHILD_EVIDENCE');
assert.equal(suggestHistoryDiscoveries({...args,evidence_records:[pair[0],record('e2',first.required_evidence_kinds[1],'CHILD_B')]}).reason,'UNVERIFIED_DUPLICATE_OR_CROSS_CHILD_EVIDENCE');
assert.equal(suggestHistoryDiscoveries({...args,evidence_records:[pair[0],{...pair[1],trusted:false}]}).reason,'UNVERIFIED_DUPLICATE_OR_CROSS_CHILD_EVIDENCE');
assert.equal(suggestHistoryDiscoveries({...args,evidence_records:[pair[0],record('e3',first.required_evidence_kinds[1],child_id,'FAMILY_B')]}).reason,'UNVERIFIED_DUPLICATE_OR_CROSS_CHILD_EVIDENCE');
const all=[];
for(const t of catalog.history_discovery_templates){
 for(const kind of t.required_evidence_kinds)all.push(record('r-'+all.length,kind));
}
const complete=suggestHistoryDiscoveries({...args,evidence_records:all});
assert.equal(complete.ok,true);
assert.equal(complete.proposal_count,20);
assert.equal(new Set(complete.proposals.map(x=>x.template_id)).size,20);
assert.ok(complete.proposals.every(x=>x.proposal_status==='REVIEW_REQUIRED_NOT_AWARD'));
assert.ok(complete.proposals.every(x=>!x.award_id&&!x.ownership_state));
console.log('BADGE_60_PRESET_AND_20_HISTORY_DISCOVERY_PASS: fixed names, rank vs stars, gated child evidence, no automatic award');
