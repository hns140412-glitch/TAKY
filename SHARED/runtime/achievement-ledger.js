(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyAchievementLedger=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_ACHIEVEMENT_LEDGER_V1';
  const clean=v=>String(v??'').trim();
  function blank(member_id=null){
    return Object.freeze({achievement_ledger_contract:VERSION,member_id:clean(member_id)||null,awards:Object.freeze([]),revision:0});
  }
  function normalize(input={}){
    const awards=Array.isArray(input.awards)?input.awards.filter(x=>x&&typeof x==='object').map(x=>Object.freeze({...x})):[];
    const seen=new Set(),dedup=[];
    for(const a of awards){
      const id=clean(a.achievement_id);
      if(!id||seen.has(id))continue;
      seen.add(id);dedup.push(a);
    }
    return Object.freeze({achievement_ledger_contract:VERSION,member_id:clean(input.member_id)||null,awards:Object.freeze(dedup),revision:Number.isInteger(input.revision)?input.revision:0});
  }
  function append(input={},award={}){
    const ledger=normalize(input);
    if(!award||award.achievement_contract!=='TAKY_ACHIEVEMENT_DECISION_V1')return {ok:false,reason:'ACHIEVEMENT_DECISION_REQUIRED',ledger};
    const achievement_id=clean(award.achievement_id),member_id=clean(award.member_id);
    if(!achievement_id||!member_id)return {ok:false,reason:'ACHIEVEMENT_IDENTITY_REQUIRED',ledger};
    if(ledger.member_id&&ledger.member_id!==member_id)return {ok:false,reason:'MEMBER_SCOPE_MISMATCH',ledger};
    if(ledger.awards.some(x=>x.achievement_id===achievement_id))return {ok:true,reason:'IDEMPOTENT_DUPLICATE',ledger};
    return {ok:true,reason:'APPENDED',ledger:normalize({member_id:ledger.member_id||member_id,awards:[...ledger.awards,award],revision:ledger.revision+1})};
  }
  function hasBadge(input={},badge_id){
    const id=clean(badge_id);
    return normalize(input).awards.some(x=>clean(x.badge_id)===id);
  }
  return Object.freeze({VERSION,blank,normalize,append,hasBadge});
});
