(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyReleaseContract=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const REQUIRED=['app_id','app_version','runtime_version','data_schema_version','contract_version','release_id'];

  function nonEmpty(value){
    return (typeof value==='string' && value.trim()!=='') || (typeof value==='number' && Number.isFinite(value));
  }

  function validateDescriptor(input){
    const errors=[];
    if(!input || typeof input!=='object' || Array.isArray(input)){
      return {ok:false,errors:['DESCRIPTOR_NOT_OBJECT']};
    }
    for(const key of REQUIRED){
      if(!nonEmpty(input[key])) errors.push('MISSING_'+key.toUpperCase());
    }
    for(const key of ['data_schema_version','contract_version']){
      const value=Number(input[key]);
      if(!Number.isInteger(value) || value<0) errors.push('INVALID_'+key.toUpperCase());
    }
    return {ok:errors.length===0,errors};
  }

  function normalizeRange(range){
    if(range==null) return null;
    if(Number.isInteger(Number(range))) {
      const n=Number(range);
      return {min:n,max:n};
    }
    if(typeof range!=='object') return null;
    const min=Number(range.min), max=Number(range.max);
    if(!Number.isInteger(min)||!Number.isInteger(max)||min<0||max<min) return null;
    return {min,max};
  }

  function inRange(value,range){
    const n=Number(value), r=normalizeRange(range);
    return Number.isInteger(n) && !!r && n>=r.min && n<=r.max;
  }

  function checkCompatibility(local,remote,policy={}){
    const lv=validateDescriptor(local), rv=validateDescriptor(remote);
    if(!lv.ok || !rv.ok){
      return {
        compatible:false,
        state:'INVALID_DESCRIPTOR',
        errors:[...lv.errors.map(x=>'LOCAL_'+x),...rv.errors.map(x=>'REMOTE_'+x)]
      };
    }

    const contractRange=policy.accept_contract_version ?? {
      min:Number(local.contract_version),
      max:Number(local.contract_version)
    };
    if(!inRange(remote.contract_version,contractRange)){
      return {
        compatible:false,
        state:'INCOMPATIBLE_CONTRACT',
        local_contract_version:Number(local.contract_version),
        remote_contract_version:Number(remote.contract_version)
      };
    }

    const schemaRange=policy.accept_data_schema_version ?? {
      min:Number(local.data_schema_version),
      max:Number(local.data_schema_version)
    };
    if(!inRange(remote.data_schema_version,schemaRange)){
      return {
        compatible:false,
        state:'INCOMPATIBLE_SCHEMA',
        local_data_schema_version:Number(local.data_schema_version),
        remote_data_schema_version:Number(remote.data_schema_version)
      };
    }

    return {
      compatible:true,
      state:'COMPATIBLE',
      local_release_id:String(local.release_id),
      remote_release_id:String(remote.release_id)
    };
  }

  return Object.freeze({
    version:'1.0.0',
    requiredFields:Object.freeze([...REQUIRED]),
    validateDescriptor,
    checkCompatibility
  });
});
