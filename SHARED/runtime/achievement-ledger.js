(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyAchievementLedger=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_ACHIEVEMENT_LEDGER_V1';
  const clean=v=>String(v??'').trim();

  function empty(member_id=null){
    return Object.freeze({
      achievement_ledger_contract:VERSION,
      member_id:clean(member_id)||null,
      entries:Object.freeze([]),
      revision:0
    });
  }

  function normalizeEntry(input={}){
    return Object.freeze({
      achievement_id:clean(input.achievement_id)||null,
      member_id:clean(input.member_id)||null,
      badge_id:clean(input.badge_id)||null,
      rule_id:clean(input.rule_id)||null,
      source_event_id:clean(input.source_event_id)||null,
      source_event_type:clean(input.source_event_type)||null,
      awarded_at:input.awarded_at||null,
      revoked:false
    });
  }

  function normalizeLedger(input={}){
    const member_id=clean(input.member_id)||null;
    const seen=new Set(),entries=[];
    for(const raw of Array.isArray(input.entries)?input.entries:[]){
      const e=normalizeEntry(raw);
      if(!e.achievement_id||seen.has(e.achievement_id))continue;
      if(member_id&&e.member_id&&e.member_id!==member_id)continue;
      seen.add(e.achievement_id); entries.push(e);
    }
    return Object.freeze({
      achievement_ledger_contract:VERSION,
      member_id,
      entries:Object.freeze(entries),
      revision:Number.isInteger(input.revision)?input.revision:0
    });
  }

  function append(input={},award={}){
    const ledger=normalizeLedger(input);
    const e=normalizeEntry(award);
    if(!e.achievement_id||!e.member_id||!e.badge_id||!e.source_event_id)
      return {ok:false,reason:'ACHIEVEMENT_ENTRY_INCOMPLETE',ledger};
    if(ledger.member_id&&ledger.member_id!==e.member_id)
      return {ok:false,reason:'ACHIEVEMENT_MEMBER_SCOPE_MISMATCH',ledger};
    if(ledger.entries.some(x=>x.achievement_id===e.achievement_id))
      return {ok:true,reason:'IDEMPOTENT_ALREADY_RECORDED',ledger};
    if(ledger.entries.some(x=>x.member_id===e.member_id&&x.badge_id===e.badge_id&&x.source_event_id===e.source_event_id))
      return {ok:true,reason:'IDEMPOTENT_SOURCE_ALREADY_RECORDED',ledger};
    return {
      ok:true,
      reason:'RECORDED',
      ledger:normalizeLedger({
        member_id:ledger.member_id||e.member_id,
        entries:[...ledger.entries,e],
        revision:ledger.revision+1
      })
    };
  }

  function hasAward(input={},badge_id,source_event_id=null){
    const ledger=normalizeLedger(input),badge=clean(badge_id),source=clean(source_event_id);
    return ledger.entries.some(x=>x.badge_id===badge&&(!source||x.source_event_id===source));
  }

  function byBadge(input={},badge_id){
    const ledger=normalizeLedger(input),badge=clean(badge_id);
    return ledger.entries.filter(x=>x.badge_id===badge);
  }

  return Object.freeze({VERSION,empty,normalizeEntry,normalizeLedger,append,hasAward,byBadge});
});