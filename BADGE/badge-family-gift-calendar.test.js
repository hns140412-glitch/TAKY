'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {createFamilyGiftJournal}=require('./family-praise-gift-journal.js');
const {projectBadgeCalendar}=require('./badge-award-calendar.js');
const {projectFamilyGiftMonth,composeChildCalendar}=require('./badge-family-gift-calendar.js');
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'taky-gift-calendar-'));
const family_id='FAMILY_A',child_id='CHILD_A',key=crypto.randomBytes(32),month='2026-09';
const times=['2026-09-26T14:59:00Z','2026-09-26T15:00:00Z','2026-09-26T15:10:00Z'];
let cursor=0;
const journal=createFamilyGiftJournal({directory,family_id,signingKey:key,now:()=>times[cursor++]});
const give=(id,receiver,kind,extra)=>journal.appendGiftRecord({
 contract:'TAKY_FAMILY_PRAISE_GIFT_V2',source:'FAMILY_PRAISE',
 family_id,giver_member_id:'GRANDMA_A',receiver_child_id:receiver,
 idempotency_key:id,message:'응원하고 있어!',
 kind,...extra
});
(async()=>{
 try{
  assert.equal(give('gift-praise-001',child_id,'PRAISE_BADGE_GIFT',{badge_id:'PRAISE_001'}).ok,true);
  assert.equal(give('gift-other-002','CHILD_B','GEM_GIFT',{gem_count:1}).ok,true);
  assert.equal(give('gift-gems-003',child_id,'GEM_GIFT',{gem_count:5}).ok,true);
  const result=await projectFamilyGiftMonth({source:journal,family_id,child_id,month});
  assert.equal(result.ok,true);
  assert.equal(result.events.length,2);
  assert.equal(result.events[0].calendar_date,'2026-09-26');
  assert.equal(result.events[1].calendar_date,'2026-09-27');
  assert.equal(result.events[0].badge_id,'PRAISE_001');
  assert.equal(result.events[1].gem_count,5);
  assert.equal(result.summary.family_praise_badge_gifts,1);
  assert.equal(result.summary.gem_gift_events,1);
  assert.equal(result.summary.journaled_gems,5);
  assert.equal(JSON.stringify(result).includes('CHILD_B'),false);
  assert.equal(Object.hasOwn(result,'wallet_balance'),false);
  const other=await projectFamilyGiftMonth({source:journal,family_id,child_id:'CHILD_B',month});
  assert.equal(other.ok,true);assert.equal(other.events.length,1);
  assert.equal(other.summary.journaled_gems,1);
  assert.equal((await projectFamilyGiftMonth({source:journal,family_id:'FAMILY_B',child_id,month})).ok,false);
  assert.equal((await projectFamilyGiftMonth({source:null,family_id,child_id,month})).ok,false);
  assert.equal((await projectFamilyGiftMonth({source:journal,family_id,child_id,month:'2026-13'})).ok,false);
  const award=projectBadgeCalendar({family_id,child_id,month,history:[{
   contract:'TAKY_VERIFIED_BADGE_HISTORY_EVENT_V1',family_id,child_id,
   badge_id:'ACHIEVEMENT_001',award_id:'award-signed-fixture-001',
   ledger_sequence:0,award_kind:'INITIAL_AWARD',event_type:'FIRST_ACQUISITION',
   awarded_at:'2026-09-26T15:00:00.000Z',date_status:'VERIFIED_AWARD_TIME',
   star_count_after:0
  }]});
  assert.equal(award.ok,true);
  const combined=composeChildCalendar({achievementCalendar:award,familyGiftCalendar:result});
  assert.equal(combined.ok,true);
  const sep27=combined.days.find(x=>x.date==='2026-09-27');
  assert.equal(sep27.achievement_events.length,1);
  assert.equal(sep27.family_gift_events.length,1);
  assert.equal(combined.summary.achievement.dated_awards,1);
  assert.equal(combined.summary.family_gifts.journaled_gems,5);
  assert.equal(combined.summary.achievement.reacquisitions,0);
  assert.equal((composeChildCalendar({achievementCalendar:award,
    familyGiftCalendar:{...result,child_id:'CHILD_B'}})).ok,false);
  const file=path.join(directory,fs.readdirSync(directory).find(x=>x.endsWith('.json')));
  const saved=fs.readFileSync(file,'utf8'),tampered=JSON.parse(saved);
  tampered.rows[0].record.badge_id='FORGED_GIFT';
  fs.writeFileSync(file,JSON.stringify(tampered));
  assert.equal((await projectFamilyGiftMonth({source:journal,family_id,child_id,month})).reason,'SIGNED_GIFT_JOURNAL_VERIFICATION_FAILED');
  fs.writeFileSync(file,saved);
  assert.equal((await projectFamilyGiftMonth({source:journal,family_id,child_id,month})).ok,true);
  console.log('CHILD_FAMILY_GIFT_CALENDAR_PASS: signed journal, separate achievement/praise/gem lanes, Korean midnight, sibling privacy, tamper denial');
 }finally{fs.rmSync(directory,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
