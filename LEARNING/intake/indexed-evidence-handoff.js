'use strict';

const VERSION='TAKY_INDEX_TO_LEARNING_EVIDENCE_HANDOFF_V1';

function clean(v){return String(v??'').trim();}

function prepare(input={}){
  const query=input.query_context||{};
  const consumerApp=clean(query.consumer_app);
  const functionId=clean(query.function_id);
  const requestedBehavior=clean(query.requested_behavior);
  const requestedClaims=Array.isArray(query.requested_claims)?query.requested_claims:[];
  const candidates=Array.isArray(input.candidates)?input.candidates:[];

  const issues=[];
  if(!consumerApp)issues.push('CONSUMER_APP_MISSING');
  if(!functionId)issues.push('FUNCTION_ID_MISSING');
  if(!requestedBehavior)issues.push('REQUESTED_BEHAVIOR_MISSING');
  if(!candidates.length)issues.push('RETRIEVAL_CANDIDATES_EMPTY');

  const normalized=[];
  for(const [index,row] of candidates.entries()){
    if(!row||typeof row!=='object'){
      issues.push(`CANDIDATE_INVALID:${index}`);
      continue;
    }
    const sourceId=clean(row.source_id);
    const sourceRef=clean(row.source_ref);
    const provenance=Array.isArray(row.provenance)?row.provenance.filter(Boolean):[];
    if(!sourceId)issues.push(`SOURCE_ID_MISSING:${index}`);
    if(!sourceRef)issues.push(`SOURCE_REF_MISSING:${index}`);
    if(!provenance.length)issues.push(`PROVENANCE_MISSING:${index}`);
    normalized.push({
      source_id:sourceId||null,
      source_ref:sourceRef||null,
      source_family:row.source_family||null,
      source_type:row.source_type||null,
      authority_class:row.authority_class||null,
      detail_anchor:row.detail_anchor||null,
      relations:Array.isArray(row.relations)?row.relations:[],
      provenance,
      retrieval_rank:Number.isFinite(row.retrieval_rank)?row.retrieval_rank:null,
      retrieval_score:Number.isFinite(row.retrieval_score)?row.retrieval_score:null
    });
  }

  if(issues.length){
    return {ok:false,version:VERSION,issues,candidates:normalized,policy_requests:[]};
  }

  const policyRequests=normalized.map(row=>({
    function_id:functionId,
    consumer_app:consumerApp,
    requested_behavior:requestedBehavior,
    requested_claims:[...requestedClaims],
    provenance:[...row.provenance],
    source_id:row.source_id,
    source_ref:row.source_ref
  }));

  return {
    ok:true,
    version:VERSION,
    query_context:{
      function_id:functionId,
      consumer_app:consumerApp,
      requested_behavior:requestedBehavior,
      requested_claims:[...requestedClaims]
    },
    candidates:normalized,
    policy_requests:policyRequests,
    source_refs:normalized.map(x=>x.source_ref),
    invariant:'INDEX_RETRIEVAL_METADATA_IS_CONTEXT_NOT_LEARNER_PERFORMANCE'
  };
}

module.exports=Object.freeze({VERSION,prepare});
