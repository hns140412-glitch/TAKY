'use strict';
// TAKY Central INDEX -> independently reviewed FORMING draft gate.
// The queue is input evidence, NEVER a review approval or issuer credential.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const Pipeline=require('../LEARNING/intake/index-forming-learning-consumption');
const Approved=require('../LEARNING/intake/approved-forming-consumer');

const ROOT='D:\\Git PWA\\TAKY_AI_WORKBENCH\\01_BACKLOG_AND_ADOPTION\\80_EVIDENCE';
const QUEUE_SCHEMA='TAKY_CENTRAL_FORMING_REVIEW_QUEUE_V1';
const CAP=1024;
const SHA=/^[a-f0-9]{64}$/;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=x=>Array.isArray(x)?'['+x.map(canonical).join(',')+']':
  x&&typeof x==='object'?'{'+Object.keys(x).sort()
    .map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}':JSON.stringify(x);
const digest=x=>hash(canonical(x));
const strictInside=(base,file)=>file.startsWith(base+path.sep);
const own=(obj,key)=>Object.prototype.hasOwnProperty.call(obj,key);

function candidateFromPacket(packet){
  if(!packet||typeof packet.source_id!=='string'||
     !/^raw:[0-9a-f]{64}$/.test(packet.source_id)||
     packet.raw_sha256!==packet.source_id.slice(4)||
     packet.review_status!=='OWNER_SEMANTIC_REVIEW_REQUIRED'||
     packet.forming_status!=='HOLD_PENDING_INDEPENDENT_OWNER_REVIEW'||
     packet.assigned_owner_namespace!==null||
     packet.route_is_authority!==false||
     !Array.isArray(packet.verified_extracts)||!packet.verified_extracts.length){
    throw Error('UNREVIEWED_INDEX_PACKET_INVALID');
  }
  const {packet_revision,...fields}=packet;
  if(!SHA.test(packet_revision)||digest(fields)!==packet_revision)
    throw Error('UNREVIEWED_PACKET_REVISION_CHANGED');
  const a=packet.verified_extracts[0];
  if(a.raw_sha256!==packet.raw_sha256||!SHA.test(a.content_sha256)||
     !['TEXT_LINE','PDF_PAGE','HTML_SEGMENT'].includes(a.kind)||
     a.review_state!=='EXTRACTIVE_UNREVIEWED'){
    throw Error('UNREVIEWED_DETAIL_ANCHOR_INVALID');
  }
  return Object.freeze({
    source_id:packet.source_id,
    source_ref:'INDEX:'+packet.source_id,
    source_family:packet.domain_hint,
    source_type:packet.media_kind,
    authority_class:'RAW_EXTRACTIVE_UNREVIEWED',
    detail_anchor:a.kind+':'+a.ref+':'+a.content_sha256,
    provenance:['RAW_SHA256:'+packet.raw_sha256,...packet.verified_extracts.map(x=>'DETAIL_SHA256:'+x.content_sha256)],
    relations:[]
  });
}

// A source-grounded proposed behavior, never an INDEX-owner decision.
// Quotes are verified against the actual hash-pinned excerpts from Central RAW.
function proposedPlanFromPacket(packet, proposal, consumer){
 const candidate=candidateFromPacket(packet);
 if(!proposal||typeof proposal!=='object'||proposal.source_id!==packet.source_id
  ||proposal.raw_sha256!==packet.raw_sha256||proposal.semantic_approved!==false
  ||!packet.verified_extracts.some(x=>x.content_sha256===proposal.review_anchor_sha256)
  ||typeof consumer!=='string'||!consumer.trim())throw Error('UNAPPROVED_PROPOSAL_SCOPE_INVALID');
 const fields=['observed_method','design_pattern','taky_gap','proposed_change','verification_test'];
 if(fields.some(k=>typeof proposal[k]!=='string'||proposal[k].length<8||proposal[k].length>1200))
   throw Error('FORMING_BEHAVIOR_MISSING');
 const byAnchor=new Map(packet.verified_extracts.map(a=>[a.ref+'|'+a.content_sha256,a]));
 const proofs=proposal.source_grounding;
 if(!Array.isArray(proofs)||proofs.length<2||proofs.length>8)throw Error('FORMING_EXACT_SOURCE_GROUNDING_REQUIRED');
 const observed=new Set();
 const grounded=[];
 for(const proof of proofs){
  if(!proof||!['observed_method','design_pattern'].includes(proof.field)
    ||observed.has(proof.field)||!SHA.test(proof.content_sha256)
    ||typeof proof.exact_quote!=='string'||proof.exact_quote.length<24
    ||proof.exact_quote.length>210)throw Error('FORMING_PROOF_SHAPE_INVALID');
  const anchor=byAnchor.get(proof.anchor_id+'|'+proof.content_sha256);
  if(!anchor||!anchor.excerpt.includes(proof.exact_quote))
    throw Error('FORMING_PROOF_NOT_IN_VERIFIED_RAW');
  observed.add(proof.field);
  grounded.push({field:proof.field,anchor_id:proof.anchor_id,
    content_sha256:proof.content_sha256,exact_quote:proof.exact_quote});
 }
 if(observed.size!==2)throw Error('FORMING_REQUIRED_METHOD_AND_PATTERN_MISSING');
 return {schema:'TAKY_FORMING_GROUNDED_APPLICATION_PLAN_V1',status:'UNAPPROVED_PROPOSAL',
   consumer,items:[{source_id:candidate.source_id,source_ref:candidate.source_ref,
      ...Object.fromEntries(fields.map(k=>[k,proposal[k]])),source_grounding:grounded}]};
}

function prepareForOwner(packet, independentIndexOwnerVerifier=null, config={}, applicationProposal=null){
  const candidate=candidateFromPacket(packet);
  if(packet.domain_hint_conflict){
    // Before even requesting INDEX owner attestation, a conflicting route must
    // be reviewed by a separately scoped domain owner; a generic INDEXED
    // receipt cannot silently turn a math article into architecture guidance.
    return {status:'DOMAIN_ROUTING_OWNER_REVIEW_REQUIRED',
      source_id:packet.source_id,route_hint:'OWNER_ROUTING_REQUIRED',
      authority:false,issues:['SOURCE_INDEX_DOMAIN_HINT_CONFLICT'],
      domain_hint_conflict:packet.domain_hint_conflict,
      forming_draft:null,projected:false};
  }
  // Only the independent trusted host can supply a real owner + consumer.
  // A domain-hint route never grants ownership by default.
  if(typeof independentIndexOwnerVerifier==='function'&&
     (!config||typeof config.owner!=='string'||!config.owner.trim()||
      typeof config.consumer!=='string'||!config.consumer.trim()||
      !['KNOWLEDGE_FORMING','CONTENT_FORMING','APPLICATION_FORMING'].includes(config.kind))){
    throw Error('TRUSTED_OWNER_CONSUMER_SCOPE_REQUIRED');
  }
  const consumer=String(config.consumer||'UNASSIGNED_NOT_CONSUMABLE');
  const owner=String(config.owner||'UNASSIGNED_OWNER_HOLD');
  const kind=String(config.kind||'KNOWLEDGE_FORMING');
  const semanticPlan=applicationProposal?proposedPlanFromPacket(packet,applicationProposal,consumer):null;
  const inputs={query_context:{
    consumer_app:consumer,
    function_id:'CENTRAL-INDEX-REVIEW',
    requested_behavior:'EVIDENCE_GROUNDED_CANDIDATE_NO_AUTO_APPROVAL',
    requested_claims:[]},
    candidates:[candidate]};
  const forming=Pipeline.prepare(inputs,
     typeof independentIndexOwnerVerifier==='function'?independentIndexOwnerVerifier:null,
     {owner_namespace:owner,forming_kind:kind,
       target_consumer:consumer,ruleset_revision:'TAKY_CENTRAL_INDEX_OWNER_REVIEW_V1',
       ...(semanticPlan?{semantic_plan:semanticPlan}:{})});
  if(!forming.ok){
    return {status:'INDEX_OWNER_REVIEW_REQUIRED',source_id:packet.source_id,
      route_hint:packet.owner_review_route_hint,authority:false,
      issues:[...forming.issues],forming_draft:null,projected:false,
      ...(semanticPlan?{semantic_plan_status:'GROUNDED_PROPOSAL_AWAITING_OWNER',semantic_plan_sha256:digest(semanticPlan),semantic_plan_preview:semanticPlan}: {})};
  }
  // The approved-forming consumer must reject even a structurally valid draft.
  const attempt=Approved.consume(forming,null,consumer);
  if(attempt.ok||forming.formed.approval_status!=='UNAPPROVED'||
     forming.formed.consumer_contract.readiness!=='NOT_APPROVED'){
    throw Error('FORMING_APPROVAL_GATE_VIOLATION');
  }
  return {status:'VERIFIED_UNAPPROVED_FORMING_DRAFT',source_id:packet.source_id,
    route_hint:packet.owner_review_route_hint,authority:false,
    issues:[...attempt.issues],forming_draft:forming.formed,
    projected:false};
}

function evaluateQueue(queue, verifier=null, config={}, applicationProposals={}){
  if(queue?.schema!==QUEUE_SCHEMA||queue.authority!=='NON_AUTHORITATIVE_DERIVED_QUEUE'||
     queue.forming_approved!==false||queue.learning_consumed!==false||
     !Array.isArray(queue.review_packets)||queue.review_packets.length>CAP||
     queue.review_packet_count!==queue.review_packets.length||
     !SHA.test(queue.manifest_sha256)){
    throw Error('CENTRAL_QUEUE_CONTRACT_INVALID');
  }
  const {manifest_sha256,...payload}=queue;
  if(digest(payload)!==manifest_sha256)
    throw Error('CENTRAL_QUEUE_MANIFEST_TAMPERED');
  const results=queue.review_packets.map(p=>prepareForOwner(p,verifier,config,applicationProposals[p.source_id]||null));
  const drafts=results.filter(x=>x.status==='VERIFIED_UNAPPROVED_FORMING_DRAFT');
  const blocked=results.filter(x=>x.status==='INDEX_OWNER_REVIEW_REQUIRED');
  const routeBlocked=results.filter(x=>x.status==='DOMAIN_ROUTING_OWNER_REVIEW_REQUIRED');
  const grounded=results.filter(x=>x.semantic_plan_status==='GROUNDED_PROPOSAL_AWAITING_OWNER');
  return {schema:'TAKY_CENTRAL_FORMING_OWNER_BOUND_GATE_V1',
    status:drafts.length?'FORMING_DRAFTS_NOT_CONSUMABLE':grounded.length?'GROUNDED_FORMING_PLAN_OWNER_REVIEW_PENDING':routeBlocked.length?'DOMAIN_ROUTING_OWNER_REVIEW_REQUIRED':'ALL_INDEX_OWNER_REVIEW_REQUIRED',
    source_queue_sha256:queue.manifest_sha256,
    reviewed_owner_draft_count:drafts.length,
    grounded_proposal_count:grounded.length,
    index_owner_review_required_count:blocked.length,
    domain_routing_owner_review_required_count:routeBlocked.length,
    missing_detail_hold_count:queue.missing_extract_hold_count,
    semantic_approvals:0,knowledge_promotions:0,
    projection_eligible:false,authority:false,
    summary_by_route:Object.fromEntries(
       [...new Set(results.map(x=>x.route_hint))].sort().map(route=>
         [route,results.filter(x=>x.route_hint===route).length])),
    sample_results:results.slice(0,Math.min(10,Math.max(1,config.sampleLimit||5)))
      .map(({forming_draft,...x})=>({...x,
          ...(forming_draft?{draft_id:forming_draft.artifact_id,
                             draft_revision:forming_draft.artifact_revision,
                             draft_status:forming_draft.approval_status}:{})}))
  };
}

function verifyQueueOnDisk(file, options={}){
  const folder=fs.realpathSync(options.evidenceRoot||ROOT);
  const full=fs.realpathSync(file);
  if(!strictInside(folder,full)||!/TAKY_FORMING_REVIEW_QUEUE_[0-9a-f]{20}\.json$/.test(path.basename(full)))
    throw Error('QUEUE_OUTSIDE_CANONICAL_EVIDENCE_ROOT');
  const bytes=fs.readFileSync(full);
  if(bytes.length>4_000_000)throw Error('QUEUE_BYTES_EXCEED_BUDGET');
  const queue=JSON.parse(bytes.toString('utf8'));
  const verifierScript=path.join(__dirname,'central_forming_review_queue.py');
  const verifyResult=execFileSync(options.python||'python',
    ['-B',verifierScript,'--verify-file',full],
    {encoding:'utf8',timeout:120000,maxBuffer:200_000,windowsHide:true});
  const verified=JSON.parse(verifyResult);
  if(verified.status!=='FORMING_QUEUE_VERIFIED_NO_APPROVAL'||
     verified.manifest_sha256!==queue.manifest_sha256||
     verified.review_packets!==queue.review_packet_count){
    throw Error('SOURCE_REGENERATED_QUEUE_REVISION_MISMATCH');
  }
  return {queue,file_sha256:hash(bytes)};
}

function main(){
  const [file,proposalFile,consumer]=process.argv.slice(2);
  if(!file)throw Error('USAGE: node central_forming_owner_gate.cjs <canonical_queue_path> [candidate_json] [review_consumer]');
  const {queue,file_sha256}=verifyQueueOnDisk(file);
  let proposals={};
  let config={};
  if(proposalFile){
    if(typeof consumer!=='string'||!consumer.trim()||consumer.length>100)
      throw Error('REVIEW_CONSUMER_HINT_REQUIRED');
    const root=fs.realpathSync(ROOT);
    const input=fs.realpathSync(proposalFile);
    if(!strictInside(root,input)||fs.lstatSync(proposalFile).isSymbolicLink()
      ||fs.statSync(input).size>250_000)throw Error('APPLICATION_PROPOSAL_OUTSIDE_EVIDENCE_ROOT');
    const document=JSON.parse(fs.readFileSync(input,'utf8'));
    if(document.schema!=='TAKY_SOURCE_APPLICATION_CANDIDATES_V1'
      ||document.semantic_approved!==false||document.applied!==false
      ||!SHA.test(document.full_review_sha256)||!Array.isArray(document.items)
      ||document.items.length>queue.review_packet_count)
      throw Error('APPLICATION_PROPOSAL_NOT_REVIEW_CANDIDATE');
    const scoped=new Set(queue.review_packets.map(p=>p.source_id));
    for(const item of document.items){
      if(!scoped.has(item.source_id)||Object.hasOwn(proposals,item.source_id))
        throw Error('APPLICATION_PROPOSAL_SOURCE_SCOPE_INVALID');
      proposals[item.source_id]=item;
    }
    config={consumer};
  }
  const result=evaluateQueue(queue,null,config,proposals);
  process.stdout.write(JSON.stringify({...result,queue_file_sha256:file_sha256})+'\n');
}
if(require.main===module){
  try{main();}catch(e){
    process.stderr.write('INDEX_OWNER_GATE_HOLD: '+e.message+'\n');
    process.exitCode=2;
  }
}
module.exports=Object.freeze({candidateFromPacket,proposedPlanFromPacket,prepareForOwner,evaluateQueue,verifyQueueOnDisk});
