'use strict';

const Identity=require('./family-member-identity-resolver.js');
const Runtime=require('../runtime/learning-engine-runtime.js');
const LiteracyBridge=require('../pedagogy/literacy-webapp-bridge.js');
const AcademicVocab=require('../pedagogy/academic-vocab-overlay.js');

const VERSION='TAKY_TERM_RECOMMENDATION_HTTP_V1';
const ENDPOINT='/api/learning/term-recommendations';
const MAX_BODY_BYTES=8192;
const clean=v=>typeof v==='string'?v.trim():'';
const object=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
const headers=Object.freeze({
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  Pragma:'no-cache','X-Content-Type-Options':'nosniff'
});
const response=(status,body)=>({status,headers:{...headers},body:JSON.stringify({...body,term_response_version:VERSION})});
const fail=(status,reason)=>response(status,{ok:false,reason});
const header=(h,name)=>{
  if(!object(h))return '';
  const key=Object.keys(h).find(k=>k.toLowerCase()===name.toLowerCase());
  return key?String(h[key]??''):'';
};

function create({
  verifyBearerToken,
  resolveLearnerProfile,
  resolveCurriculumTerms,
  resolveTermEvidence=null
}={}){
  if(typeof verifyBearerToken!=='function')throw Error('TRUSTED_BEARER_IDENTITY_VERIFIER_REQUIRED');
  if(typeof resolveLearnerProfile!=='function')throw Error('LEARNER_PROFILE_RESOLVER_REQUIRED');
  if(typeof resolveCurriculumTerms!=='function')throw Error('CURRICULUM_TERM_RESOLVER_REQUIRED');
  if(resolveTermEvidence!==null&&typeof resolveTermEvidence!=='function')throw Error('TERM_EVIDENCE_RESOLVER_INVALID');

  return Object.freeze({version:VERSION,async handle(req={}){
    if(req.path!==ENDPOINT)return fail(404,'TERM_RECOMMENDATION_ENDPOINT_NOT_FOUND');
    if(req.method!=='POST')return fail(405,'POST_REQUIRED');
    if(!/^application\/json(?:\s*;|\s*$)/i.test(header(req.headers,'content-type')))
      return fail(415,'JSON_CONTENT_TYPE_REQUIRED');
    const match=header(req.headers,'authorization').match(/^Bearer ([A-Za-z0-9._~+/-]{16,4096}=*)$/);
    if(!match)return fail(401,'VERIFIED_BEARER_REQUIRED');
    if(typeof req.body!=='string'||Buffer.byteLength(req.body,'utf8')>MAX_BODY_BYTES)
      return fail(413,'BOUNDED_JSON_BODY_REQUIRED');

    let input;
    try{input=JSON.parse(req.body)}catch{return fail(400,'VALID_JSON_REQUIRED')}
    const allowed=new Set(['family_id','member_id','subject','unit_context','limit']);
    if(!object(input)||Object.keys(input).some(k=>!allowed.has(k)))return fail(400,'EXPLICIT_TERM_SCOPE_ONLY_REQUIRED');
    if(['family_id','member_id','subject'].some(k=>!clean(input[k])||clean(input[k]).length>128))
      return fail(400,'EXPLICIT_TERM_SCOPE_ONLY_REQUIRED');
    if(input.unit_context!==undefined&&(!Array.isArray(input.unit_context)||input.unit_context.length>24||
      input.unit_context.some(x=>!clean(x)||clean(x).length>128)))return fail(400,'UNIT_CONTEXT_INVALID');
    if(input.limit!==undefined&&(!Number.isInteger(input.limit)||input.limit<1||input.limit>36))
      return fail(400,'TERM_LIMIT_INVALID');

    let principal;
    try{principal=await verifyBearerToken(match[1])}
    catch{return fail(401,'BEARER_IDENTITY_VERIFICATION_FAILED')}
    const resolved=Identity.resolve(principal,{requested_family_id:input.family_id});
    if(!resolved.ok)return fail(403,'VERIFIED_FAMILY_MEMBERSHIP_REQUIRED');
    const identity=resolved.identity;
    if(!identity.authorized_member_ids.includes(input.member_id))
      return fail(403,'AUTHORIZED_MEMBER_REQUIRED');

    let profile;
    try{profile=await resolveLearnerProfile({
      family_id:identity.family_id,member_id:input.member_id
    })}catch{return fail(503,'LEARNER_PROFILE_UNAVAILABLE')}
    if(!object(profile)||!clean(profile.school_stage||profile.schoolStage))
      return fail(503,'LEARNER_GRADE_CONTEXT_REQUIRED');

    let termSource;
    try{termSource=await resolveCurriculumTerms({
      family_id:identity.family_id,member_id:input.member_id,
      subject:clean(input.subject),unit_context:input.unit_context||[],
      learner_profile:profile
    })}catch{return fail(503,'CURRICULUM_TERM_SOURCE_UNAVAILABLE')}
    if(!object(termSource)||!Array.isArray(termSource.terms))
      return fail(503,'CURRICULUM_TERM_SOURCE_INVALID');

    let evidence=[];
    if(resolveTermEvidence){
      try{evidence=await resolveTermEvidence({
        family_id:identity.family_id,member_id:input.member_id,
        subject:clean(input.subject),term_ids:termSource.terms.map(x=>clean(x.term_id||x.id)).filter(Boolean)
      })}catch{return fail(503,'TERM_EVIDENCE_UNAVAILABLE')}
      if(!Array.isArray(evidence))return fail(503,'TERM_EVIDENCE_INVALID');
    }

    let runtime;
    try{runtime=Runtime.deriveTermRecommendations({
      learner_profile:profile,
      subject:clean(input.subject),
      unit_context:input.unit_context||[],
      curriculum_terms:termSource.terms,
      term_evidence:evidence,
      consumer_app:'HIDE_SEEK',
      limit:input.limit||12,
      allow_provisional:termSource.allow_provisional===true
    })}catch{return fail(503,'TERM_RECOMMENDATION_RUNTIME_UNAVAILABLE')}

    if(!runtime.ok)return fail(503,runtime.reason||'TERM_RECOMMENDATION_RUNTIME_INVALID');

    const schoolStage=clean(profile.school_stage||profile.schoolStage);
    const academicVocab=AcademicVocab.decorate(
      runtime.term_recommendations,runtime.cards,schoolStage
    );
    let academicVocabTargets=null;
    if(clean(termSource.unit_text)&&clean(termSource.source_ref)){
      const targetResult=Runtime.deriveAcademicVocabularyTargets({
        school_stage:schoolStage,
        unit_text:termSource.unit_text,
        explicit_terms:Array.isArray(termSource.academic_vocab_explicit_terms)?termSource.academic_vocab_explicit_terms:[],
        evidence,
        source_ref:clean(termSource.source_ref),
        limit:12
      });
      if(!targetResult.ok)return fail(503,targetResult.reason||'ACADEMIC_VOCAB_TARGET_RUNTIME_INVALID');
      academicVocabTargets=targetResult;
    }
    const literacyIntent=LiteracyBridge.derive({
      learner_profile:profile,
      term_recommendations:academicVocab.recommendations,
      academic_vocabulary_targets:academicVocabTargets?.selected||[],
      source_refs:{
        academic_vocabulary:'CNE:ACADEMIC_VOCAB_1387_RESEARCH_2024',
        ondok:'CNE:CNE_ONDOK_INDEX_2026',
        writing_transfer:'CNE:CNE_SAGAKSAGAK_ONGEUL_2026'
      }
    });
    if(!literacyIntent.ok||!LiteracyBridge.validate(literacyIntent).ok)
      return fail(503,'LITERACY_WEBAPP_INTENT_INVALID');

    return response(200,{
      ok:true,
      authenticated_server_response:true,
      authority:runtime.authority,
      projection_type:runtime.projection_type,
      learner_context:runtime.learner_context,
      scope:runtime.scope,
      recommendation_state:runtime.recommendation_state,
      term_recommendations:academicVocab.recommendations,
      cards:academicVocab.cards,
      academic_vocabulary_stage_policy:academicVocab.stage_policy,
      academic_vocabulary_targets:academicVocabTargets,
      literacy_intent:literacyIntent,
      trace:{
        selector_version:runtime.trace?.selector_version||null,
        selected_term_ids:runtime.trace?.selected_term_ids||[],
        source_refs:runtime.trace?.source_refs||[],
        source_projection_ref:clean(termSource.source_ref)||null,
        evidence_count:evidence.length
      },
      cannot_influence:runtime.cannot_influence
    });
  }});
}

module.exports=Object.freeze({VERSION,ENDPOINT,MAX_BODY_BYTES,create});
