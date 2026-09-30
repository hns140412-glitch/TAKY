'use strict';

const Evidence=require('./central-learning-http-endpoint.js');
const Decision=require('./central-learning-decision-http-endpoint.js');
const Google=require('./google-learning-principal.js');
const NodeBridge=require('./node-http-learning-bridge.js');

const VERSION='TAKY_CENTRAL_LEARNING_PRODUCTION_HOST_V1';
const clean=x=>typeof x==='string'?x.trim():'';

function create({
  clientIds,
  googleAuthLibrary=null,
  oauth2Client=null,
  lookupMemberships,
  store,
  verifySpecialistEvidence,
  resolveIndexedEvidence,
  independentIndexOwnerVerifier,
  allowedOrigins,
  now=Date.now
}={}){
  if(typeof lookupMemberships!=='function')
    throw Error('PRODUCTION_MEMBERSHIP_PROVIDER_REQUIRED');
  if(!store||typeof store.getWithMetadata!=='function'||typeof store.setJSON!=='function')
    throw Error('PRODUCTION_STRONG_STORE_REQUIRED');
  if(typeof verifySpecialistEvidence!=='function')
    throw Error('PRODUCTION_SPECIALIST_VERIFIER_REQUIRED');
  if(typeof resolveIndexedEvidence!=='function')
    throw Error('PRODUCTION_INDEXED_EVIDENCE_RESOLVER_REQUIRED');
  if(typeof independentIndexOwnerVerifier!=='function')
    throw Error('PRODUCTION_INDEX_OWNER_VERIFIER_REQUIRED');
  if(!Array.isArray(allowedOrigins)||!allowedOrigins.length||
     allowedOrigins.some(x=>!clean(x)||!/^https:\/\/[^/]+$/.test(x)))
    throw Error('PRODUCTION_HTTPS_ORIGIN_ALLOWLIST_REQUIRED');

  const principal=Google.createFromGoogleAuthLibrary({
    googleAuthLibrary,oauth2Client,clientIds,lookupMemberships,now
  });
  const verifyBearerToken=principal.verifyBearerToken;

  const evidenceEndpoint=Evidence.create({
    verifyBearerToken,store,verifySpecialistEvidence
  });
  const decisionEndpoint=Decision.create({
    verifyBearerToken,store,resolveIndexedEvidence,
    independentIndexOwnerVerifier
  });
  const handler=NodeBridge.createHandler({
    endpoint:evidenceEndpoint,
    decisionEndpoint,
    allowedOrigins
  });

  return Object.freeze({
    version:VERSION,
    identity_version:principal.version,
    evidence_version:evidenceEndpoint.version,
    decision_version:decisionEndpoint.version,
    bridge_version:NodeBridge.VERSION,
    routes:Object.freeze([Evidence.ENDPOINT,Decision.ENDPOINT]),
    allowed_origins:Object.freeze([...allowedOrigins]),
    handler
  });
}

module.exports=Object.freeze({VERSION,create});