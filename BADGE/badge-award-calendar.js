'use strict';

// Read-only projection of already VERIFIED per-badge Award Ledger history.
// This code never emits Award Ledger receipts, gives a badge, or infers a timestamp.
const CONTRACT='TAKY_CHILD_BADGE_CALENDAR_V1';
const ZONE='Asia/Seoul';
const clean=v=>typeof v==='string'?v.trim():'';
const fail=reason=>({ok:false,reason});
const signedUtc=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(v)&&
  Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
const dateFormatter=new Intl.DateTimeFormat('en-GB',{
  timeZone:ZONE,year:'numeric',month:'2-digit',day:'2-digit'
});
const localDate=utc=>{
  const p=Object.fromEntries(dateFormatter.formatToParts(new Date(utc)).filter(x=>x.type!=='literal').map(x=>[x.type,x.value]));
  return p.year+'-'+p.month+'-'+p.day;
};
const EVENT_TYPES=new Set(['FIRST_ACQUISITION','REACQUISITION','TIER_PROMOTION']);
function projectBadgeCalendar({family_id,child_id,month,history,labels={}}={}){
  const family=clean(family_id),child=clean(child_id);
  if(!family||!child||family!==family_id||child!==child_id)return fail('VERIFIED_FAMILY_CHILD_SCOPE_REQUIRED');
  if(typeof month!=='string'||!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)||Number(month.slice(0,4))<1)
    return fail('VALID_YEAR_MONTH_REQUIRED');
  if(!Array.isArray(history)||history.length>10000)return fail('VERIFIED_AWARD_HISTORY_REQUIRED');
  const seen=new Set(),dated=[],undated=[];
  for(const event of history){
    if(!event||event.contract!=='TAKY_VERIFIED_BADGE_HISTORY_EVENT_V1'||
       event.family_id!==family||event.child_id!==child||!clean(event.badge_id)||
       !clean(event.award_id)||seen.has(event.award_id)||
       !EVENT_TYPES.has(event.event_type)||
       !Number.isSafeInteger(event.ledger_sequence)||event.ledger_sequence<0||
       !Number.isInteger(event.star_count_after)||event.star_count_after<0||event.star_count_after>5)
      return fail('INVALID_DUPLICATE_OR_CROSS_CHILD_AWARD_HISTORY');
    if(event.event_type==='FIRST_ACQUISITION'&&
       (event.award_kind!=='INITIAL_AWARD'||event.ledger_sequence!==0||event.star_count_after!==0))
      return fail('FIRST_AWARD_HISTORY_INCONSISTENT');
    if(event.event_type!=='FIRST_ACQUISITION'&&event.award_kind!=='REAWARD')
      return fail('REAWARD_HISTORY_INCONSISTENT');
    if(event.event_type==='TIER_PROMOTION'&&event.tier_up!==true)
      return fail('PROMOTION_HISTORY_INCONSISTENT');
    seen.add(event.award_id);
    const entry={
      award_id:event.award_id,badge_id:event.badge_id,
      badge_title:clean(labels[event.badge_id])||event.badge_id,
      event_type:event.event_type,award_kind:event.award_kind,
      awarded_at:event.awarded_at??null,ledger_sequence:event.ledger_sequence,
      star_count_after:event.star_count_after,
      tier_before:event.from_tier??null,tier_after:event.to_tier??null,
      date_status:event.date_status
    };
    if(event.date_status==='AWARD_TIME_NOT_RECORDED'&&event.awarded_at==null){
      undated.push(entry);continue;
    }
    if(event.date_status!=='VERIFIED_AWARD_TIME'||!signedUtc(event.awarded_at))
      return fail('AWARD_DATE_CANNOT_BE_INFERRED_FROM_APPROVAL');
    entry.calendar_date=localDate(event.awarded_at);
    dated.push(entry);
  }
  dated.sort((a,b)=>a.awarded_at.localeCompare(b.awarded_at)||a.award_id.localeCompare(b.award_id));
  const [year,mon]=month.split('-').map(Number);
  const lastDay=new Date(Date.UTC(year,mon,0)).getUTCDate();
  const days=Array.from({length:lastDay},(_,i)=>{
    const date=month+'-'+String(i+1).padStart(2,'0');
    const events=dated.filter(e=>e.calendar_date===date);
    return {date,weekday:new Date(Date.UTC(year,mon-1,i+1)).getUTCDay(),
      award_count:events.length,events};
  });
  const monthEvents=days.flatMap(x=>x.events);
  return {ok:true,contract:CONTRACT,time_zone:ZONE,
    family_id:family,child_id:child,month,days,events:monthEvents,
    // Legacy verified award rows without an actual append timestamp appear here,
    // NEVER on a guessed date using Decision approved_at.
    undated_history:undated,
    summary:{
      dated_awards:monthEvents.length,
      first_acquisitions:monthEvents.filter(x=>x.event_type==='FIRST_ACQUISITION').length,
      reacquisitions:monthEvents.filter(x=>x.event_type==='REACQUISITION').length,
      promotions:monthEvents.filter(x=>x.event_type==='TIER_PROMOTION').length,
      legacy_undated_awards:undated.length
    }};
}
module.exports=Object.freeze({CONTRACT,ZONE,projectBadgeCalendar});
