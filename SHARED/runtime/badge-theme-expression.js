(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyBadgeThemeExpression=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_BADGE_THEME_EXPRESSION_V1';
  const ASSET_STATES=new Set(['UNRESOLVED','REVIEWED_ASSET_SET']);
  const FORBIDDEN_KEYS=new Set([
    'identity','profile','name','photo','hair','glasses','face','userId','user_id',
    'tier','stars','level','rank','power','ability','score','exp','gem','gems',
    'reward','rewardAmount','reward_amount','badgeAwarded','awardState','catalogItemId'
  ]);
  const clean=(v,max=220)=>typeof v==='string'?v.trim().slice(0,max):'';
  function containsForbidden(value,depth=0){
    if(depth>4||value===null||typeof value!=='object')return false;
    if(Array.isArray(value))return value.some(x=>containsForbidden(x,depth+1));
    for(const [key,item] of Object.entries(value)){
      if(FORBIDDEN_KEYS.has(key))return true;
      if(containsForbidden(item,depth+1))return true;
    }
    return false;
  }
  function refs(v,max=12){
    return Array.isArray(v)?v.filter(x=>typeof x==='string').map(x=>clean(x)).filter(Boolean).slice(0,max):[];
  }
  function normalize(input={}){
    if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('BADGE_THEME_EXPRESSION_OBJECT_REQUIRED');
    if(containsForbidden(input))throw new Error('BADGE_THEME_EXPRESSION_AUTHORITY_VIOLATION');
    const theme_id=clean(input.theme_id||input.themeId,80);
    if(!theme_id)throw new Error('BADGE_THEME_EXPRESSION_ID_REQUIRED');
    const asset_state=clean(input.asset_state||input.assetState,40).toUpperCase()||'UNRESOLVED';
    if(!ASSET_STATES.has(asset_state))throw new Error('BADGE_THEME_EXPRESSION_ASSET_STATE_INVALID');
    const asset_refs=refs(input.asset_refs||input.assetRefs);
    if(asset_state==='REVIEWED_ASSET_SET'&&!asset_refs.length)throw new Error('BADGE_THEME_EXPRESSION_REVIEWED_ASSET_REQUIRED');
    return Object.freeze({
      badge_theme_expression_contract:VERSION,
      theme_id,
      asset_state,
      asset_refs:Object.freeze(asset_refs),
      pose_ref:clean(input.pose_ref||input.poseRef)||null,
      backdrop_ref:clean(input.backdrop_ref||input.backdropRef)||null,
      prop_refs:Object.freeze(refs(input.prop_refs||input.propRefs,8)),
      effect_refs:Object.freeze(refs(input.effect_refs||input.effectRefs,8)),
      expression_cue:clean(input.expression_cue||input.expressionCue,120)||null,
      identity_mutation_allowed:false,
      growth_mutation_allowed:false,
      economy_mutation_allowed:false,
      award_mutation_allowed:false,
      power_mutation_allowed:false,
      cosmetic_only:true
    });
  }
  function compose(identity={},themeExpression={}){
    const theme=normalize(themeExpression);
    return Object.freeze({identity,theme_expression:theme,identity_stable:true,cosmetic_only:true,power_effect:null,reward_effect:null,economy_effect:null});
  }
  return Object.freeze({VERSION,ASSET_STATES:Object.freeze([...ASSET_STATES]),normalize,compose,containsForbidden});
});
