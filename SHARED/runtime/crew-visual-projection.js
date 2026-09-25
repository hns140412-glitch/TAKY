(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyCrewVisualProjection=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_CREW_VISUAL_PROJECTION_V1';
  const clean=v=>String(v??'').trim();
  const CORE=Object.freeze({
    'crew.core.dubi':Object.freeze({canonical_name:'두비',lineage:'dog-like',status:'VISUAL_ID_RECOVERED_ASSET_BINDING_OPEN'}),
    'crew.core.lori':Object.freeze({canonical_name:'로리',lineage:'rabbit / pink-braid lineage',status:'VISUAL_ID_RECOVERED_ASSET_BINDING_OPEN'}),
    'crew.core.ink':Object.freeze({canonical_name:'잉크',lineage:'female dark fox / goggles / dark tone',status:'VISUAL_ID_RECOVERED_ASSET_BINDING_OPEN'}),
    'crew.core.nova':Object.freeze({canonical_name:'노바',lineage:'brown otter-ferret-like / goggles / ponytail',status:'VISUAL_ID_RECOVERED_ASSET_BINDING_OPEN'}),
    'crew.core.take':Object.freeze({canonical_name:'테이크',lineage:'panda',status:'VISUAL_ID_RECOVERED_ASSET_BINDING_OPEN'}),
    'crew.core.zero':Object.freeze({canonical_name:'제로',lineage:'penguin / headphones / cap',status:'VISUAL_ID_RECOVERED_ASSET_BINDING_OPEN'})
  });

  function normalize(input={}){
    const character_id=clean(input.character_id);
    const base=CORE[character_id];
    if(!base)throw new Error('CREW_VISUAL_CHARACTER_UNKNOWN');
    const asset_ref=clean(input.asset_ref)||null;
    const theme_id=clean(input.theme_id)||null;
    return Object.freeze({
      crew_visual_projection_contract:VERSION,
      character_id,
      canonical_name:base.canonical_name,
      lineage:base.lineage,
      identity_status:base.status,
      asset_ref,
      theme_id,
      identity_mutation_allowed:false,
      functional_advantage:null,
      reward_advantage:null
    });
  }

  function bindReviewedAsset(input={}){
    if(input.reviewed!==true)throw new Error('CREW_VISUAL_REVIEW_REQUIRED');
    const asset_ref=clean(input.asset_ref);
    if(!asset_ref)throw new Error('CREW_VISUAL_ASSET_REF_REQUIRED');
    return normalize({...input,asset_ref});
  }

  return Object.freeze({VERSION,CORE,normalize,bindReviewedAsset});
});
