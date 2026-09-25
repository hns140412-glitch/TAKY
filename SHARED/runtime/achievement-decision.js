(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyAchievementDecision=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_ACHIEVEMENT_DECISION_V1';
  const clean=v=>String(v??'').trim();

  function normalizeRule(input={}){
    return Object.freeze({
      rule_id:clean(input.rule_id)||null,
      badge_id:clean(input.badge_id)||null,
      event_types:Object.freeze(Array.isArray(input.event_types)?input.event_types.map(clean).filter(Boolean):[]),
      categories:Object.freeze(Array.isArray(input.categories)?input.categories.map(x=>clean(x).toUpperCase()).filter(Boolean):[]),
      min_count:Number.isInteger(input.min_count)&&input.min_count>0?input.min_count:1,
      active:input.active!==false
    });
  }

  function validateRule(input={}){
    const rule=normalizeRule(input),issues=[];
    if(!rule.rule_id)issues.push('RULE_ID_REQUIRED');
    if(!rule.badge_id)issues.push('BADGE_ID_REQUIRED');
    if(!rule.event_types.length&&!rule.categories.length)issues.push('MATCH_CRITERIA_REQUIRED');
    return {ok:issues.length===0,issues,rule};
  }

  function matches(ruleInput,event={}){
    const checked=validateRule(ruleInput);
    if(!checked.ok)return false;
    const rule=checked.rule;
    if(!rule.active)return false;
    const type=clean(event.source_event_type);
    const category=clean(event.category).toUpperCase();
    const typeMatch=!rule.event_types.length||rule.event_types.includes(type);
    const categoryMatch=!rule.categories.length||rule.categories.includes(category);
    return typeMatch&&categoryMatch;
  }

  function decide({rule,event,prior_count=0,already_awarded=false}={}){
    const checked=validateRule(rule);
    if(!checked.ok)return {ok:false,reason:checked.issues[0],award:null};
    if(already_awarded)return {ok:true,reason:'ALREADY_AWARDED',award:null};
    if(!matches(checked.rule,event))return {ok:true,reason:'RULE_NOT_MATCHED',award:null};
    const nextCount=Math.max(0,Number(prior_count)||0)+1;
    if(nextCount<checked.rule.min_count)return {ok:true,reason:'THRESHOLD_NOT_MET',count:nextCount,award:null};
    const member_id=clean(event.member_id);
    const source_event_id=clean(event.exploration_event_id||event.event_id);
    if(!member_id||!source_event_id)return {ok:false,reason:'EVENT_IDENTITY_REQUIRED',award:null};
    return {
      ok:true,
      reason:'AWARD',
      count:nextCount,
      award:Object.freeze({
        achievement_contract:VERSION,
        achievement_id:'achievement:'+checked.rule.rule_id+':'+member_id+':'+source_event_id,
        member_id,
        badge_id:checked.rule.badge_id,
        rule_id:checked.rule.rule_id,
        source_event_id,
        source_event_type:clean(event.source_event_type),
        awarded_at:event.occurred_at||new Date().toISOString()
      })
    };
  }

  return Object.freeze({VERSION,normalizeRule,validateRule,matches,decide});
});
