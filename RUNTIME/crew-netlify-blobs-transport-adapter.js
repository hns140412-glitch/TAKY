'use strict';
const Authenticated=require('./authenticated-crew-evidence-transport.js');
const VERSION='TAKY_CREW_NETLIFY_BLOBS_TRANSPORT_ADAPTER_V1';
function create({getStore,resolveIdentity,store_name='taky-crew-evidence-v1',region=null}={}){
 if(typeof getStore!=='function')throw new Error('GET_STORE_REQUIRED');
 if(typeof resolveIdentity!=='function')throw new Error('IDENTITY_RESOLVER_REQUIRED');
 return Object.freeze({version:VERSION,async ingest(packet={},request_context={},options={}){
   const identity=await resolveIdentity(request_context);
   const args={name:store_name,consistency:'strong'};if(region)args.region=region;
   const store=getStore(args);
   const result=await Authenticated.ingestAuthenticated(store,packet,identity,options);
   return {...result,transport_adapter:VERSION,store_name,store_consistency:'strong',deployment_authority:false};
 }});
}
module.exports=Object.freeze({VERSION,create});
