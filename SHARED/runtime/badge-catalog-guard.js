(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyBadgeCatalogGuard=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const VERSION='TAKY_BADGE_CATALOG_GUARD_V1';
  function validateCatalog(catalog={}){
    const items=Array.isArray(catalog.items)?catalog.items:[];
    for(const item of items){
      if(!item||typeof item!=='object')continue;
      const working=item.status==='WORKING_DRAFT'||catalog.status==='WORKING_DRAFT_NOT_ACTIVE';
      if(working&&item.active===true)throw new Error('BADGE_WORKING_DRAFT_ACTIVATION_FORBIDDEN');
    }
    return true;
  }
  function canActivate(item={},catalog={}){
    if(!item||typeof item!=='object')return false;
    if(catalog.status==='WORKING_DRAFT_NOT_ACTIVE')return false;
    if(item.status==='WORKING_DRAFT')return false;
    return item.active===true;
  }
  function activeItems(catalog={}){
    validateCatalog(catalog);
    return (Array.isArray(catalog.items)?catalog.items:[]).filter(item=>canActivate(item,catalog));
  }
  return Object.freeze({VERSION,validateCatalog,canActivate,activeItems});
});
