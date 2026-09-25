(function(root,factory){
  const api=factory(root);
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyCrewVisualProjection=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(root){
  'use strict';
  const VERSION='TAKY_CREW_VISUAL_PROJECTION_V1';
  const Identity=(typeof module==='object'&&module.exports)
    ? require('./crew-visual-identity.js')
    : root.TakyCrewVisualIdentity;
  if(!Identity?.identity) throw new Error('TAKY_CREW_VISUAL_IDENTITY_REQUIRED');
  const clean=v=>String(v??'').trim();

  function normalize(input={}){
    const character_id=clean(input.character_id);
    const identity=Identity.identity(character_id);
    if(!identity) throw new Error('CREW_VISUAL_CHARACTER_UNKNOWN');
    return Object.freeze({
      crew_visual_projection_contract:VERSION,
      character_id,
      canonical_name:identity.canonical_name,
      species:identity.species,
      identity,
      asset_ref:clean(input.asset_ref)||null,
      theme_id:clean(input.theme_id)||null,
      personality_prop_ref:clean(input.personality_prop_ref)||null,
      identity_mutation_allowed:false,
      functional_advantage:null,
      reward_advantage:null
    });
  }

  function bindReviewedAsset(input={}){
    if(input.reviewed!==true) throw new Error('CREW_VISUAL_REVIEW_REQUIRED');
    const asset_ref=clean(input.asset_ref);
    if(!asset_ref) throw new Error('CREW_VISUAL_ASSET_REF_REQUIRED');
    return normalize({...input,asset_ref});
  }

  return Object.freeze({VERSION,normalize,bindReviewedAsset});
});
