'use strict';

const {URL}=require('node:url');
const {MAX_BODY_BYTES,ENDPOINT}=require('./central-learning-http-endpoint.js');
const Decision=require('./central-learning-decision-http-endpoint.js');
const CharacterProfile=require('./family-character-profile-http-endpoint.js');
const CharacterAsset=require('./family-character-asset-http-endpoint.js');
const FamilySession=require('./family-session-http-endpoint.js');
const VERSION='TAKY_NODE_HTTP_CENTRAL_LEARNING_BRIDGE_V1';
const baseHeaders=Object.freeze({
 'Content-Type':'application/json; charset=utf-8',
 'Cache-Control':'private, no-store, max-age=0',
 Pragma:'no-cache','X-Content-Type-Options':'nosniff',
 Vary:'Origin'
});
const fail=(res,status,reason,extra={})=>{
 res.writeHead(status,{...baseHeaders,...extra});
 res.end(JSON.stringify({ok:false,reason,bridge_version:VERSION}));
};
const clean=v=>typeof v==='string'?v.trim():'';

/**
 * Real Node http request/response bridge. No cookie/ambient session reliance.
 * Never grants a learning receipt by itself; the injected central endpoint
 * does all identity, membership, specialist and durable commit verification.
 * Only the explicit Origin allowlist receives CORS approval. A cross-origin
 * browser needs Authorization: Bearer and application/json, never wildcard.
 */
function createHandler({endpoint,decisionEndpoint=null,characterProfileEndpoint=null,characterAssetEndpoint=null,familySessionEndpoint=null,allowedOrigins=[],maxBodyBytes=MAX_BODY_BYTES}={}){
 if(typeof endpoint?.handle!=='function')throw Error('CENTRAL_LEARNING_ENDPOINT_REQUIRED');
 if(decisionEndpoint!==null&&typeof decisionEndpoint?.handle!=='function')
   throw Error('CENTRAL_DECISION_ENDPOINT_INVALID');
 if(characterProfileEndpoint!==null&&typeof characterProfileEndpoint?.handle!=='function')
   throw Error('FAMILY_CHARACTER_PROFILE_ENDPOINT_INVALID');
 if(characterAssetEndpoint!==null&&typeof characterAssetEndpoint?.handle!=='function')
   throw Error('FAMILY_CHARACTER_ASSET_ENDPOINT_INVALID');
 if(familySessionEndpoint!==null&&typeof familySessionEndpoint?.handle!=='function')
   throw Error('FAMILY_SESSION_ENDPOINT_INVALID');
 if(!Array.isArray(allowedOrigins)||new Set(allowedOrigins).size!==allowedOrigins.length||
    allowedOrigins.some(s=>!clean(s)||!/^https:\/\/[^/]+$/.test(s)))
   throw Error('EXPLICIT_HTTPS_ORIGIN_ALLOWLIST_REQUIRED');
 if(!Number.isInteger(maxBodyBytes)||maxBodyBytes<1024||maxBodyBytes>MAX_BODY_BYTES)
   throw Error('HTTP_BODY_BOUND_REQUIRED');
 const allowed=new Set(allowedOrigins);
 return async function handler(req,res){
   const origin=clean(req.headers?.origin);
   const cors=origin&&allowed.has(origin)?{
     'Access-Control-Allow-Origin':origin,
     'Access-Control-Allow-Methods':'POST, OPTIONS',
     'Access-Control-Allow-Headers':'Authorization, Content-Type',
     'Access-Control-Max-Age':'300'
   }:{};
   if(origin&&!allowed.has(origin))
     return fail(res,403,'ORIGIN_NOT_ALLOWED');
   let path;
   try{path=new URL(req.url,'http://127.0.0.1').pathname}
   catch{return fail(res,400,'REQUEST_PATH_INVALID',cors)}
   if(req.method==='OPTIONS'){
     if(![ENDPOINT,...(decisionEndpoint?[Decision.ENDPOINT]:[]),...(characterProfileEndpoint?[CharacterProfile.ENDPOINT]:[]),...(characterAssetEndpoint?[CharacterAsset.ENDPOINT]:[]),...(familySessionEndpoint?[FamilySession.ENDPOINT]:[])].includes(path)||!origin)
      return fail(res,404,'PREFLIGHT_NOT_ALLOWED',cors);
     res.writeHead(204,{...baseHeaders,...cors});res.end();return;
   }
   if(path!==ENDPOINT&&(!decisionEndpoint||path!==Decision.ENDPOINT)&&(!characterProfileEndpoint||path!==CharacterProfile.ENDPOINT)&&(!characterAssetEndpoint||path!==CharacterAsset.ENDPOINT)&&(!familySessionEndpoint||path!==FamilySession.ENDPOINT))
     return fail(res,404,'CENTRAL_LEARNING_ENDPOINT_NOT_FOUND',cors);
   if(req.method!=='POST')return fail(res,405,'POST_REQUIRED',cors);
   const length=Number(req.headers?.['content-length']);
   if(Number.isFinite(length)&&length>maxBodyBytes)
     return fail(res,413,'BOUNDED_JSON_BODY_REQUIRED',cors);
   const chunks=[];let size=0;
   try{
     for await(const chunk of req){
       size+=chunk.length;
       if(size>maxBodyBytes)
         return fail(res,413,'BOUNDED_JSON_BODY_REQUIRED',cors);
       chunks.push(chunk);
     }
   }catch{
     if(!res.headersSent)return fail(res,400,'REQUEST_STREAM_INVALID',cors);
     return;
   }
   let result;
   try{
     const target=path===Decision.ENDPOINT?decisionEndpoint:path===CharacterProfile.ENDPOINT?characterProfileEndpoint:path===CharacterAsset.ENDPOINT?characterAssetEndpoint:path===FamilySession.ENDPOINT?familySessionEndpoint:endpoint;
     result=await target.handle({
       method:req.method,path,headers:req.headers,
       body:Buffer.concat(chunks,size).toString('utf8')
     });
   }catch{return fail(res,503,'CENTRAL_LEARNING_ENDPOINT_UNAVAILABLE',cors)}
   if(!result||!Number.isInteger(result.status)||typeof result.body!=='string')
     return fail(res,503,'CENTRAL_ENDPOINT_RESPONSE_INVALID',cors);
   res.writeHead(result.status,{...baseHeaders,...result.headers,...cors});
   res.end(result.body);
 };
}
module.exports=Object.freeze({VERSION,createHandler});
