'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const crypto=require('node:crypto');
const {createLedger}=require('./badge-award-ledger-store.js');
const {deriveFromLedger}=require('./badge-ledger-projection-bridge.js');
const {projectBadgeCalendar}=require('./badge-award-calendar.js');
const {createFamilyBadgeReader}=require('./badge-family-read-access.js');
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'taky-award-calendar-'));
const family_id='FAMILY_A',child_id='CHILD_A',tiers=['GREEN','BLUE','RED','GOLD','PLATINUM'];
const dates=[
 '2026-09-26T14:59:00.000Z',
 '2026-09-26T15:00:00.000Z',
 '2026-09-26T15:01:00.000Z',
 '2026-09-26T15:02:00.000Z',
 '2026-09-26T15:03:00.000Z',
 '2026-09-26T15:04:00.000Z',
 '2026-09-26T16:00:00.000Z',
 '2026-09-26T16:10:00.000Z'
];
let cursor=0;
const signingKey=crypto.randomBytes(32);
const approvedBadges=new Set(['BADGE_A','BADGE_B','LEGACY_BADGE','INVALID_DATE_BADGE']);
const ledger=createLedger({
 directory,family_id,signingKey,now:()=>dates[cursor++],
 verifyDecision:x=>x?.testTrusted===true?{ok:true,receipt:x.receipt}:{ok:false},
 isBadgeActive:x=>approvedBadges.has(x.badge_id)&&x.child_id===child_id
});
const append=(badge_id,n,award_kind)=>ledger.appendApprovedDecision({
 testTrusted:true,receipt:{
 family_id,child_id,badge_id,decision_id:badge_id+'-decision-'+n,
 decision_ref:'verified-test-decision-'+n,decision_status:'APPROVED',
 award_kind,approved_at:'2026-09-25T10:00:00Z'
 }});
const initialArgs={source:ledger.source,child_id,badge_id:'BADGE_A',tier_order:tiers};
const catalog=[
 {badge_id:'BADGE_A',title:'실수 청소부',active:true,approved:true},
 {badge_id:'BADGE_B',title:'해뜰락말락',active:true,approved:true},
 {badge_id:'LEGACY_BADGE',title:'이전 기록',active:true,approved:true}
];
const sessions={
 parent:{authenticated:true,source:'NETLIFY_IDENTITY',family_id,member_id:'PARENT_A',role:'PARENT'},
 child:{authenticated:true,source:'NETLIFY_IDENTITY',family_id,member_id:child_id,role:'CHILD'},
 sibling:{authenticated:true,source:'NETLIFY_IDENTITY',family_id,member_id:'CHILD_B',role:'CHILD'},
 foreign:{authenticated:true,source:'NETLIFY_IDENTITY',family_id:'FAMILY_B',member_id:'PARENT_B',role:'PARENT'},
 fake:{authenticated:true,source:'TEST_ONLY',family_id,member_id:'PARENT_A',role:'PARENT'}
};
function reader(list=()=>catalog){
 return createFamilyBadgeReader({
 resolveServerSession:async request=>sessions[request.session]||null,
 lookupIdentityMember:async id=>id===child_id?{identity_verified:true,member_id:child_id,family_id,role:'CHILD'}:null,
 openFamilyLedgerSource:async()=>ledger.source,
 listActiveBadgeIds:list
 });
}
(async()=>{
 try{
  assert.equal((await deriveFromLedger(initialArgs)).history.length,0);
  assert.equal(append('BADGE_A',0,'INITIAL_AWARD').ok,true);
  for(let i=1;i<=5;i++)assert.equal(append('BADGE_A',i,'REAWARD').ok,true);
  assert.equal(append('BADGE_B',0,'INITIAL_AWARD').ok,true);
  const legacy=append('LEGACY_BADGE',0,'INITIAL_AWARD');
  assert.equal(legacy.ok,true);
  // Reconstruct a valid prior-format signed ledger that had only approved_at,
  // never silently treating that timestamp as the actual award day.
  const legacyFile=path.join(directory,crypto.createHash('sha256')
    .update(family_id+'\0'+child_id+'\0'+'LEGACY_BADGE').digest('hex')+'.json');
  const raw=JSON.parse(fs.readFileSync(legacyFile,'utf8'));
  assert.equal(raw.rows.length,1);
  delete raw.rows[0].record.awarded_at;
  const oldRecord=raw.rows[0].record;
  const legacyDigest=crypto.createHmac('sha256',signingKey)
    .update(oldRecord.previous_digest+'\n'+JSON.stringify(oldRecord)).digest('hex');
  raw.rows[0].digest=legacyDigest;raw.checkpoint=legacyDigest;
  fs.writeFileSync(legacyFile,JSON.stringify(raw));

  const progress=await deriveFromLedger(initialArgs);
  assert.equal(progress.ok,true);
  assert.equal(progress.history.length,6);
  assert.equal(progress.history[0].event_type,'FIRST_ACQUISITION');
  assert.equal(progress.history[0].star_count_after,0);
  assert.equal(progress.history[0].decision_approved_at,'2026-09-25T10:00:00Z');
  assert.equal(progress.history[0].awarded_at,dates[0]);
  assert.equal(progress.history[5].event_type,'TIER_PROMOTION');
  assert.equal(progress.history[5].award_kind,'REAWARD');
  assert.equal(progress.history[5].star_count_before,4);
  assert.equal(progress.history[5].star_count_after,0);
  assert.equal(progress.history[5].to_tier,'BLUE');
  const regressedClock=createLedger({
    directory,family_id,signingKey,now:()=>dates[0],
    verifyDecision:x=>x?.testTrusted===true?{ok:true,receipt:x.receipt}:{ok:false},
    isBadgeActive:x=>approvedBadges.has(x.badge_id)&&x.child_id===child_id
  });
  const backdated=regressedClock.appendApprovedDecision({testTrusted:true,receipt:{
    family_id,child_id,badge_id:'BADGE_A',decision_id:'BADGE_A-backdated',
    decision_ref:'verified-new-decision',decision_status:'APPROVED',
    award_kind:'REAWARD',approved_at:'2026-09-26T10:00:00Z'
  }});
  assert.equal(backdated.reason,'AWARD_TIME_REGRESSION');
  assert.equal((await ledger.source.loadCompleteHistory({child_id,badge_id:'BADGE_A'})).row_count,6);

  const legacyProjected=await deriveFromLedger({
    source:ledger.source,child_id,badge_id:'LEGACY_BADGE',tier_order:tiers
  });
  assert.equal(legacyProjected.ok,true);
  assert.equal(legacyProjected.history[0].date_status,'AWARD_TIME_NOT_RECORDED');
  assert.equal(legacyProjected.history[0].awarded_at,null);
  assert.equal(legacyProjected.history[0].decision_approved_at,'2026-09-25T10:00:00Z');

  const r=reader(),req={session:'parent'};
  const detail=await r.getBadgeHistory(req,{child_id,badge_id:'BADGE_A',tier_order:tiers});
  assert.equal(detail.ok,true);
  assert.equal(detail.history.length,6);
  assert.equal(detail.current_state.tier,'BLUE');
  assert.equal(detail.current_state.star_count,0);
  const month=await r.getMonth(req,{child_id,month:'2026-09',tier_order:tiers});
  assert.equal(month.ok,true);
  assert.equal(month.time_zone,'Asia/Seoul');
  assert.equal(month.days.length,30);
  assert.equal(month.days.find(d=>d.date==='2026-09-26').award_count,1);
  assert.equal(month.days.find(d=>d.date==='2026-09-27').award_count,6);
  assert.equal(month.summary.dated_awards,7);
  assert.equal(month.summary.first_acquisitions,2);
  assert.equal(month.summary.reacquisitions,4);
  assert.equal(month.summary.promotions,1);
  assert.equal(month.summary.legacy_undated_awards,1);
  assert.equal(month.undated_history[0].badge_title,'이전 기록');
  assert.equal(month.undated_history[0].awarded_at,null);
  assert.equal(month.events.find(x=>x.event_type==='TIER_PROMOTION').calendar_date,'2026-09-27');
  const later=await r.getMonth(req,{child_id,month:'2026-10',tier_order:tiers});
  assert.equal(later.ok,true);
  assert.equal(later.days.length,31);
  assert.equal(later.summary.dated_awards,0);
  assert.equal(later.summary.legacy_undated_awards,1);
  assert.equal((await r.getMonth({session:'fake'},{child_id,month:'2026-09',tier_order:tiers})).reason,'VERIFIED_FAMILY_SESSION_REQUIRED');
  assert.equal((await r.getMonth({session:'sibling'},{child_id,month:'2026-09',tier_order:tiers})).reason,'CHILD_MAY_ONLY_READ_OWN_BADGES');
  assert.equal((await r.getMonth({session:'foreign'},{child_id,month:'2026-09',tier_order:tiers})).reason,'VERIFIED_CHILD_FAMILY_MEMBERSHIP_REQUIRED');
  assert.equal((await r.getBadgeHistory({session:'child'},{child_id,badge_id:'BADGE_A',tier_order:tiers})).ok,true);
  assert.equal((await r.getMonth(req,{child_id,month:'2026-13',tier_order:tiers})).reason,'VALID_YEAR_MONTH_REQUIRED');
  assert.equal((await reader(()=>[]).getMonth({session:'fake'},{child_id,month:'2026-09',tier_order:tiers})).reason,'VERIFIED_FAMILY_SESSION_REQUIRED');
  assert.equal((await reader(()=>[]).getMonth(req,{child_id,month:'2026-09',tier_order:tiers})).summary.dated_awards,0);
  assert.equal((await reader(()=>[catalog[0],catalog[0]]).getMonth(req,{child_id,month:'2026-09',tier_order:tiers})).reason,'ACTIVE_BADGE_LIST_INVALID_OR_UNAPPROVED');
  assert.equal((await reader(()=>[{...catalog[0],approved:false}]).getMonth(req,{child_id,month:'2026-09',tier_order:tiers})).reason,'ACTIVE_BADGE_LIST_INVALID_OR_UNAPPROVED');
  const corrupted=structuredClone(progress.history);corrupted.push({...corrupted[0]});
  assert.equal(projectBadgeCalendar({family_id,child_id,month:'2026-09',history:corrupted}).ok,false);
  assert.equal(projectBadgeCalendar({family_id,child_id,month:'2026-09',history:[{...corrupted[0],child_id:'CHILD_B'}]}).ok,false);
  assert.equal(projectBadgeCalendar({family_id,child_id,month:'2026-09',history:[{...corrupted[0],date_status:'VERIFIED_AWARD_TIME',awarded_at:null}]}).ok,false);
  const invalidClock=createLedger({
    directory,family_id,signingKey,now:()=> 'yesterday',
    verifyDecision:x=>x?.testTrusted===true?{ok:true,receipt:x.receipt}:{ok:false},
    isBadgeActive:x=>approvedBadges.has(x.badge_id)&&x.child_id===child_id
  });
  const invalid=invalidClock.appendApprovedDecision({testTrusted:true,receipt:{
    family_id,child_id,badge_id:'INVALID_DATE_BADGE',decision_id:'new-decision',
    decision_ref:'verified-decision',decision_status:'APPROVED',
    award_kind:'INITIAL_AWARD',approved_at:'2026-09-25T10:00:00Z'
  }});
  assert.equal(invalid.reason,'TRUSTED_AWARD_TIME_INVALID');
  assert.equal((await invalidClock.source.loadCompleteHistory({child_id,badge_id:'INVALID_DATE_BADGE'})).row_count,0);
  console.log('BADGE_HISTORY_CALENDAR_PASS: signed actual award timestamps, KST boundary, first/reaward/promotion, legacy undated, family permissions, tamper/dedupe');
 }finally{fs.rmSync(directory,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1;});
