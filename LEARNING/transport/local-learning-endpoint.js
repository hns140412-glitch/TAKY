'use strict';
const path=require('node:path');
const Identity=require('./family-member-identity-resolver.js');
const Authenticated=require('./authenticated-evidence-transport.js');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');

const VERSION='TAKY_LOCAL_LEARNING_ENDPOINT_V1';

function create({root,resolvePrincipal}={}){
  if(!root)throw new Error('LOCAL_STORE_ROOT_REQUIRED');
  if(typeof resolvePrincipal!=='function')throw new Error('PRINCIPAL_RESOLVER_REQUIRED');
  const store=new LocalJsonStrongStore(path.resolve(String(root)));

  return Object.freeze({
    version:VERSION,
    async handle(request_context={},packet={},options={}){
      const principal=await resolvePrincipal(request_context);
      const resolved=Identity.resolve(principal,{requested_family_id:packet?.context?.family_id});
      if(!resolved.ok)return {ok:false,reason:'IDENTITY_RESOLUTION_FAILED',issues:resolved.issues,endpoint_version:VERSION};
      const result=await Authenticated.ingestAuthenticated(store,packet,resolved.identity,options);
      return {...result,endpoint_version:VERSION,identity_resolver_version:Identity.VERSION,deployment_authority:false};
    }
  });
}

module.exports=Object.freeze({VERSION,create});
