(function(root,factory){
 const api=factory(); if(typeof module==='object'&&module.exports)module.exports=api; else root.TakyCrewVisualIdentity=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const VERSION='TAKY_CREW_VISUAL_IDENTITY_V1';
 const CORE=Object.freeze({
  'crew.core.dubi':Object.freeze({canonical_name:'두비',species:'dog-like',core_traits:['호기심','활력','막내'],signature_props:['cap','backpack'],visual_status:'RECOVERED_CURRENT_COMPATIBLE_LINEAGE'}),
  'crew.core.lori':Object.freeze({canonical_name:'로리',species:'rabbit',core_traits:['다정','공감','따뜻함'],signature_props:['pink braids'],visual_status:'RECOVERED_CURRENT_COMPATIBLE_LINEAGE'}),
  'crew.core.ink':Object.freeze({canonical_name:'잉크',species:'dark fox',core_traits:['관찰','아이디어','신중함'],signature_props:['goggles','tablet'],visual_status:'RECOVERED_DIRECT_PROFILE_EVIDENCE'}),
  'crew.core.nova':Object.freeze({canonical_name:'노바',species:'otter/ferret-like',core_traits:['에너지','도전','활동적'],signature_props:['goggles','ponytail'],visual_status:'RECOVERED_CURRENT_COMPATIBLE_LINEAGE'}),
  'crew.core.take':Object.freeze({canonical_name:'테이크',species:'panda',core_traits:['정리','든든함','차분함'],signature_props:['blue neckwear'],visual_status:'RECOVERED_CURRENT_COMPATIBLE_LINEAGE'}),
  'crew.core.zero':Object.freeze({canonical_name:'제로',species:'penguin',core_traits:['음악','여유','챙김'],signature_props:['headphones','cap'],visual_status:'RECOVERED_CURRENT_COMPATIBLE_LINEAGE'})
 });
 const clean=v=>String(v??'').trim();
 function identity(character_id){const id=clean(character_id);const x=CORE[id];return x?Object.freeze({crew_visual_identity_contract:VERSION,character_id:id,...x,golden_asset_ref:null,golden_asset_status:'OPEN_EXACT_ASSET_MAPPING'}):null}
 function project(character_id,{theme_id=null,theme_asset_ref=null,personality_prop_ref=null}={}){
   const base=identity(character_id); if(!base)return {ok:false,reason:'CREW_VISUAL_IDENTITY_NOT_FOUND'};
   return {ok:true,projection:Object.freeze({
     visual_projection_contract:VERSION,
     identity:base,
     theme:Object.freeze({theme_id:clean(theme_id)||null,theme_asset_ref:clean(theme_asset_ref)||null}),
     personality_prop_ref:clean(personality_prop_ref)||null,
     identity_body_stable:true,
     species_mutation_allowed:false,
     canonical_name_mutation_allowed:false,
     power_effect:null,reward_effect:null
   })};
 }
 function assertNoIdentityMutation(candidate={}){
   if(candidate.species||candidate.canonical_name||candidate.character_id)return false;
   return true;
 }
 return Object.freeze({VERSION,CORE,identity,project,assertNoIdentityMutation});
});