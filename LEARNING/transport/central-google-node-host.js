'use strict';

/**
 * Pure host composition. It exposes a Node request handler, not a deployed
 * URL, credentials, database, or independently running background service.
 * Operators MUST provision a real official Google verifier/Client IDs and
 * server-administered registry rows before using it outside test fixtures.
 */
const Google=require('./google-learning-principal.js');
const Registry=require('./server-family-registry-provider.js');
const Central=require('./central-learning-http-endpoint.js');
const NodeBridge=require('./node-http-learning-bridge.js');
const VERSION='TAKY_CENTRAL_GOOGLE_NODE_HOST_COMPOSITION_V1';

function create({
 googleAuthLibrary,oauth2Client,clientIds,registryStore,evidenceStore,
 allowedOrigins,verifySpecialistEvidence=null,now=Date.now
}={}){
 if(!Array.isArray(allowedOrigins)||!allowedOrigins.length)
   throw Error('HOST_EXPLICIT_BROWSER_ORIGINS_REQUIRED');
 if(typeof registryStore?.getWithMetadata!=='function')
   throw Error('HOST_SERVER_REGISTRY_STORE_REQUIRED');
 if(typeof evidenceStore?.getWithMetadata!=='function'||
    typeof evidenceStore?.setJSON!=='function')
   throw Error('HOST_DURABLE_EVIDENCE_STORE_REQUIRED');
 const registry=Registry.create({store:registryStore,now});
 const google=Google.createFromGoogleAuthLibrary({
   googleAuthLibrary,oauth2Client,clientIds,
   lookupMemberships:registry.lookupMemberships,now
 });
 const endpoint=Central.create({
   verifyBearerToken:google.verifyBearerToken,store:evidenceStore,
   verifySpecialistEvidence
 });
 const handler=NodeBridge.createHandler({endpoint,allowedOrigins});
 return Object.freeze({version:VERSION,handler});
}
module.exports=Object.freeze({VERSION,create});
