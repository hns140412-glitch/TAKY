'use strict';

/**
 * Pure host composition. It exposes a Node request handler, not a deployed
 * URL, credentials, database, or independently running background service.
 * Operators MUST provision a real official Google verifier/Client IDs and
 * server-administered registry rows before using it outside test fixtures.
 */
const Google=require('./google-learning-principal.js');
const Registry=require('./server-family-registry-provider.js');
const References=require('./server-specialist-reference-store.js');
const Specialist=require('./server-specialist-verifier.js');
const Central=require('./central-learning-http-endpoint.js');
const NodeBridge=require('./node-http-learning-bridge.js');
const VERSION='TAKY_CENTRAL_GOOGLE_NODE_HOST_COMPOSITION_V1';

function create({
 googleAuthLibrary,oauth2Client,clientIds,registryStore,evidenceStore,
 referenceStore=null,allowedOrigins,verifySpecialistEvidence=null,now=Date.now
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
 if(referenceStore&&verifySpecialistEvidence)
   throw Error('HOST_AMBIGUOUS_SPECIALIST_VERIFIER_CONFIGURATION');
 const sources=referenceStore?References.create({store:referenceStore}):null;
 const specialist=sources?Specialist.create({
   loadAssessment:sources.loadAssessment,
   loadHumanReview:sources.loadHumanReview,now
 }):null;
 const endpoint=Central.create({
   verifyBearerToken:google.verifyBearerToken,store:evidenceStore,
   verifySpecialistEvidence:specialist?.verifySpecialistEvidence||verifySpecialistEvidence
 });
 const handler=NodeBridge.createHandler({endpoint,allowedOrigins});
 return Object.freeze({version:VERSION,handler});
}
module.exports=Object.freeze({VERSION,create});
