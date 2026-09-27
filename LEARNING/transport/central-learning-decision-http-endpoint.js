'use strict';

/**
 * Read-only, authenticated Learning Engine decision endpoint.
 * Evidence ingestion and receipt issuance stay at /api/learning/evidence.
 * This route only derives intent from the server's durable, validated
 * verified evidence. Observation-only events cannot be promoted into proof.
 */
const Identity=require('./family-member-identity-resolver.js');
const Durable=require('./durable-evidence-store-adapter.js');
const Intake=require('../intake/real-evidence-intake.js');
const Receipt=require('../receipts/real-evidence-receipt.js');
const Runtime=require('../runtime/learning-engine-runtime.js');

const VERSION='TAKY_CENTRAL_LEARNING_DECISION_HTTP_V1';
const ENDPOINT='/api/learning/decision';
const MAX_BODY_BYTES=8192;
const clean=x=>typeof x==='string'?x.trim():'';
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const headers=Object.freeze({
 'Content-Type':'application/json; charset=utf-8',
 'Cache-Control':'private, no-store, max-age=0',
 Pragma:'no-cache','X-Content-Type-Options':'nosniff'
});
const response=(status,body)=>({status,headers:{...headers},
 body:JSON.stringify({...body,decision_response_version:VERSION})});
const fail=(status,reason)=>response(status,{ok:false,reason});
const header=(h,name)=>{
 if(!object(h))return '';
 const key=Object.keys(h).find(k=>k.toLowerCase()===name.toLowerCase());
 return key?String(h[key]??''):'';
};
function create({verifyBearerToken,store}={}){
 if(typeof verifyBearerToken!=='function')
  throw Error('TRUSTED_BEARER_IDENTITY_VERIFIER_REQUIRED');
 if(typeof store?.getWithMetadata!=='function')
  throw Error('STRONG_DURABLE_EVIDENCE_READ_REQUIRED');
 return Object.freeze({version:VERSION,async handle(req={}){
  if(req.path!==ENDPOINT)return fail(404,'CENTRAL_DECISION_ENDPOINT_NOT_FOUND');
  if(req.method!=='POST')return fail(405,'POST_REQUIRED');
  if(!/^application\/json(?:\s*;|\s*$)/i.test(header(req.headers,'content-type')))
   return fail(415,'JSON_CONTENT_TYPE_REQUIRED');
  const match=header(req.headers,'authorization')
   .match(/^Bearer ([A-Za-z0-9._~+/-]{16,4096}=*)$/);
  if(!match)return fail(401,'VERIFIED_BEARER_REQUIRED');
  if(typeof req.body!=='string'||Buffer.byteLength(req.body,'utf8')>MAX_BODY_BYTES)
   return fail(413,'BOUNDED_JSON_BODY_REQUIRED');
  let input;
  try{input=JSON.parse(req.body)}catch{return fail(400,'VALID_JSON_REQUIRED')}
  const allowed=new Set(['family_id','member_id','subject','concept_skill_target']);
  if(!object(input)||Object.keys(input).some(k=>!allowed.has(k))||
     ['family_id','member_id','subject','concept_skill_target']
      .some(k=>!clean(input[k])||clean(input[k]).length>128))
   return fail(400,'EXPLICIT_DECISION_SCOPE_ONLY_REQUIRED');
  let principal;
  try{principal=await verifyBearerToken(match[1])}
  catch{return fail(401,'BEARER_IDENTITY_VERIFICATION_FAILED')}
  const resolved=Identity.resolve(principal,{requested_family_id:input.family_id});
  if(!resolved.ok)return fail(403,'VERIFIED_FAMILY_MEMBERSHIP_REQUIRED');
  const identity=resolved.identity;
  if(!identity.authorized_member_ids.includes(input.member_id))
   return fail(403,'AUTHORIZED_MEMBER_REQUIRED');

  const scope={member_id:input.member_id,
   subject:input.subject.toLowerCase(),
   concept_skill_target:input.concept_skill_target.toLowerCase()};
  const key=Durable.stateKey({context:{family_id:identity.family_id,
   member_id:scope.member_id}});
  let stored;
  try{stored=await store.getWithMetadata(key,{type:'json',consistency:'strong'})}
  catch{return fail(503,'CENTRAL_DURABLE_READ_UNAVAILABLE')}
  if(stored&&(!clean(stored.etag)||stored.consistency!=='strong'||
    !object(stored.data)||!object(stored.data.scope_receipts)))
   return fail(503,'CENTRAL_VERIFIED_STATE_INVALID');
  const group=stored?.data?.scope_receipts?.[Intake.scopeKey(scope)]||null;
  let evidence=[];
  let receiptId=null;
  if(group){
   const check=Receipt.validateBatchReceipt(group.receipt,group.canonical_evidence);
   if(!check.ok)return fail(503,'CENTRAL_VERIFIED_RECEIPT_INVALID');
   if(JSON.stringify(group.receipt.scope)!==JSON.stringify(scope))
    return fail(503,'CENTRAL_VERIFIED_SCOPE_MISMATCH');
   evidence=group.canonical_evidence;
   receiptId=group.receipt.receipt_id;
  }
  // Observation-only rows are intentionally excluded, even when the browser
  // sent a convincing memory strength or an unauthenticated verifier claim.
  let runtime;
  try{runtime=Runtime.derive({scope,evidence})}
  catch{return fail(503,'CENTRAL_RUNTIME_UNAVAILABLE')}
  if(!runtime.ok||!Runtime.validate(runtime).ok)
   return fail(503,'CENTRAL_RUNTIME_INVALID');
  const safe={
   ok:true,authority:runtime.authority,engine_runtime:runtime.engine_runtime,
   scope:runtime.scope,decision:runtime.decision,
   cannot_influence:runtime.cannot_influence,
   trace:{evidence_ids:runtime.trace.evidence_ids,
    decision_contract:runtime.trace.decision_contract,
    verified_receipt_id:receiptId,verified_evidence_count:evidence.length}
  };
  return response(200,{ok:true,authenticated_server_response:true,
   receipt_scope:{family_id:identity.family_id,member_id:scope.member_id},
   runtime_result:safe,source:'SERVER_DURABLE_VERIFIED_EVIDENCE_ONLY',
   observation_only_excluded:true});
 }});
}
module.exports=Object.freeze({VERSION,ENDPOINT,MAX_BODY_BYTES,create});
