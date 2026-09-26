'use strict';

// Authenticated server composition ONLY: source must be a trusted signed V2
// Family Gift Journal. These are never Achievement Award Ledger events or Gem credits.
const {ZONE}=require('./badge-award-calendar.js');
const CONTRACT='TAKY_CHILD_FAMILY_GIFT_CALENDAR_V1';
const JOURNAL='TAKY_FAMILY_PRAISE_GIFT_JOURNAL_V2';
const clean=v=>typeof v==='string'?v.trim():'';
const fail=reason=>({ok:false,reason});
const validInstant=v=>typeof v==='string'&&
 /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(v)&&
 Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===(v.includes('.')?v:v.slice(0,-1)+'.000Z');
const formatter=new Intl.DateTimeFormat('en-GB',{timeZone:ZONE,year:'numeric',month:'2-digit',day:'2-digit'});
const toDay=v=>{const p=Object.fromEntries(formatter.formatToParts(new Date(v))
 .filter(x=>x.type!=='literal').map(x=>[x.type,x.value]));return p.year+'-'+p.month+'-'+p.day;};
async function projectFamilyGiftMonth({source,family_id,child_id,month}={}){
 const family=clean(family_id),child=clean(child_id);
 if(!family||!child||family!==family_id||child!==child_id)return fail('FAMILY_CHILD_SCOPE_REQUIRED');
 if(typeof month!=='string'||!/^\d{4}-(0[1-9]|1[0-2])$/.test(month))return fail('VALID_YEAR_MONTH_REQUIRED');
 if(!source||source.contract!==JOURNAL||source.family_id!==family||typeof source.readGiftHistory!=='function')
  return fail('TRUSTED_FAMILY_GIFT_JOURNAL_REQUIRED');
 let snapshot;
 try{snapshot=await source.readGiftHistory()}catch{return fail('SIGNED_GIFT_JOURNAL_VERIFICATION_FAILED')}
 if(!snapshot||snapshot.contract!==JOURNAL||snapshot.family_id!==family||
   !clean(snapshot.checkpoint)||!Array.isArray(snapshot.rows)||snapshot.rows.length>10000)
  return fail('SIGNED_FAMILY_GIFT_SNAPSHOT_INVALID');
 const seen=new Set(),events=[];
 for(const row of snapshot.rows){
  const r=row?.record;
  if(!r||r.family_id!==family||!clean(r.gift_id)||seen.has(r.gift_id)||
     !clean(r.giver_member_id)||!clean(r.receiver_child_id)||
     !validInstant(r.accepted_at)||!['PRAISE_BADGE_GIFT','GEM_GIFT'].includes(r.kind)||
     (r.kind==='PRAISE_BADGE_GIFT'&&!clean(r.badge_id))||
     (r.kind==='GEM_GIFT'&&(!Number.isInteger(r.gem_count)||r.gem_count<1||r.gem_count>5)))
   return fail('GIFT_HISTORY_SCOPE_OR_TIMESTAMP_INVALID');
  seen.add(r.gift_id);
  if(r.receiver_child_id!==child)continue; // Never leak a sibling's gifts.
  const date=toDay(r.accepted_at);
  if(date.slice(0,7)!==month)continue;
  events.push({
   event_id:r.gift_id,source:'FAMILY_GIFT_JOURNAL',
   type:r.kind==='PRAISE_BADGE_GIFT'?'FAMILY_PRAISE_BADGE_GIFT':'FAMILY_GEM_GIFT',
   calendar_date:date,accepted_at:r.accepted_at,
   receiver_child_id:child,giver_member_id:r.giver_member_id,
   ...(r.kind==='PRAISE_BADGE_GIFT'?{badge_id:r.badge_id}:{gem_count:r.gem_count}),
   message:r.message||''
  });
 }
 events.sort((a,b)=>a.accepted_at.localeCompare(b.accepted_at)||a.event_id.localeCompare(b.event_id));
 return {ok:true,contract:CONTRACT,time_zone:ZONE,family_id:family,child_id:child,
   month,events,
   summary:{family_praise_badge_gifts:events.filter(e=>e.type==='FAMILY_PRAISE_BADGE_GIFT').length,
    gem_gift_events:events.filter(e=>e.type==='FAMILY_GEM_GIFT').length,
    // Number of journaled gifts, not a claim about the child's credited wallet.
    journaled_gems:events.filter(e=>e.type==='FAMILY_GEM_GIFT').reduce((n,e)=>n+e.gem_count,0)}
 };
}
function composeChildCalendar({achievementCalendar,familyGiftCalendar}={}){
 const a=achievementCalendar,g=familyGiftCalendar;
 if(a?.ok!==true||a.contract!=='TAKY_CHILD_BADGE_CALENDAR_V1'||g?.ok!==true||
    g.contract!==CONTRACT||a.family_id!==g.family_id||a.child_id!==g.child_id||
    a.month!==g.month||a.time_zone!==ZONE||g.time_zone!==ZONE||
    !Array.isArray(a.days)||!Array.isArray(g.events))
  return fail('VERIFIED_MATCHING_CHILD_CALENDAR_LANES_REQUIRED');
 return {ok:true,contract:'TAKY_CHILD_BADGE_AND_FAMILY_GIFT_CALENDAR_V1',
  family_id:a.family_id,child_id:a.child_id,month:a.month,time_zone:ZONE,
  days:a.days.map(day=>({...day,achievement_events:day.events,
    family_gift_events:g.events.filter(e=>e.calendar_date===day.date)})),
  undated_achievement_history:a.undated_history,
  // The counters remain independent. Gift events never increment stars/awards.
  summary:{achievement:{...a.summary},family_gifts:{...g.summary}}
 };
}
module.exports=Object.freeze({CONTRACT,projectFamilyGiftMonth,composeChildCalendar});
