'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const Bridge=require('./central_forming_owner_gate.cjs');
const Forming=require('../LEARNING/intake/forming-bridge.js');
const Approved=require('../LEARNING/intake/approved-forming-consumer.js');
const folder=String.raw`D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\80_EVIDENCE`;
const file=fs.readdirSync(folder)
  .filter(name=>/^TAKY_FORMING_REVIEW_QUEUE_[0-9a-f]{20}\.json$/.test(name))
  .map(name=>path.join(folder,name))
  .sort((a,b)=>fs.statSync(a).mtimeMs-fs.statSync(b).mtimeMs)
  .at(-1);
if(!file)throw Error('SOURCE_REVIEW_QUEUE_MISSING');
let queue;

test('actual central queue is freshly RAW-verified before owner handoff',()=>{
  queue=Bridge.verifyQueueOnDisk(file).queue;
  // Both full-corpus and explicitly scoped, SHA-verified queues are valid.
  // A minimum historical document count is not a trust/approval invariant.
  assert.ok(queue.review_packet_count>0);
  assert.equal(queue.missing_extract_hold_count,queue.holds.length);
  assert.equal(queue.verbatim_legal_reference_marker_count,
    queue.review_packets.reduce((n,p)=>n+(p.verbatim_legal_reference_markers?.length||0),0));
  assert.ok(queue.source_count>=queue.review_packet_count);
  const result=Bridge.evaluateQueue(queue);
  assert.equal(result.status,
    result.domain_routing_owner_review_required_count?
      'DOMAIN_ROUTING_OWNER_REVIEW_REQUIRED':'ALL_INDEX_OWNER_REVIEW_REQUIRED');
  assert.equal(result.index_owner_review_required_count+
    result.domain_routing_owner_review_required_count,queue.review_packet_count);
  assert.equal(result.reviewed_owner_draft_count,0);
  assert.equal(result.semantic_approvals,0);
  assert.equal(result.knowledge_promotions,0);
  assert.equal(result.projection_eligible,false);
  assert.equal(result.summary_by_route.ARCHI_GROW_OWNER_REVIEW||0,
    queue.review_packets.filter(x=>x.owner_review_route_hint==='ARCHI_GROW_OWNER_REVIEW').length);
  assert.equal(result.summary_by_route.OWNER_ROUTING_REQUIRED||0,
    queue.review_packets.filter(x=>x.owner_review_route_hint==='OWNER_ROUTING_REQUIRED').length);
  assert.equal(result.summary_by_route.SYSTEM_GROW_TECHNICAL_OWNER_REVIEW,
    queue.domain_counts.AI_REFERENCE);
});

test('reviewed index owner fixture can produce genuine unapproved forming DRAFT',()=>{
  const scopedQueue=Bridge.verifyQueueOnDisk(path.join(folder,
    'TAKY_FORMING_REVIEW_QUEUE_c35c15fc0a7e5edec0ea.json')).queue;
  const packet=scopedQueue.review_packets[0];
  const expected=Bridge.candidateFromPacket(packet);
  // Test-only independent verifier injection, not a production credential.
  const verifier=(sourceId,sourceRef)=>({
    issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
    domain_use_authorized:true,source_id:sourceId,source_ref:sourceRef,
    index_version:'TEST_ONLY_INDEX_OWNER_V1',
    review_evidence_refs:['TEST_ONLY_INDEPENDENT_INDEX_OWNER_ATTESTATION'],
    source_family:expected.source_family,source_type:expected.source_type,
    authority_class:expected.authority_class,detail_anchor:expected.detail_anchor,
    relations:[],provenance:[...expected.provenance]});
  const trustedScope={owner:'SYSTEM_GROW',consumer:'TAKY_REVIEW_CONSUMER',
    kind:'KNOWLEDGE_FORMING'};
  const yes=Bridge.prepareForOwner(packet,verifier,trustedScope);
  assert.equal(yes.status,'VERIFIED_UNAPPROVED_FORMING_DRAFT');
  assert.equal(yes.forming_draft.status,'DRAFT');
  assert.equal(yes.forming_draft.approval_status,'UNAPPROVED');
  assert.equal(yes.forming_draft.consumer_contract.readiness,'NOT_APPROVED');
  assert.equal(Forming.verifyArtifact(yes.forming_draft).ok,true);
  assert.ok(yes.issues.includes('APPROVAL_VERIFIER_REQUIRED'));
  const fakePrepared={ok:true,stage:'FORMING_DRAFT',formed:yes.forming_draft};
  assert.equal(Approved.consume(fakePrepared,null,'TAKY_REVIEW_CONSUMER').ok,false);
  assert.throws(()=>Bridge.prepareForOwner(packet,verifier),
    /TRUSTED_OWNER_CONSUMER_SCOPE_REQUIRED/);
  const one=Bridge.evaluateQueue(scopedQueue,(id,ref)=>id===packet.source_id?verifier(id,ref):null,
    trustedScope);
  assert.equal(one.reviewed_owner_draft_count,1);
  assert.equal(one.index_owner_review_required_count,scopedQueue.review_packet_count-1);
  assert.equal(one.semantic_approvals,0);
  assert.equal(one.knowledge_promotions,0);
  assert.equal(one.projection_eligible,false);
});

test('missing and spoofed review credentials never create drafts',()=>{
  const scopedQueue=Bridge.verifyQueueOnDisk(path.join(folder,
    'TAKY_FORMING_REVIEW_QUEUE_c35c15fc0a7e5edec0ea.json')).queue;
  const packet=scopedQueue.review_packets[0];
  const claimed={...packet,issuer:'INDEXING_OWNER',reviewed:true,
      domain_use_authorized:true,review_evidence_refs:['SPOOFED']};
  assert.throws(()=>Bridge.prepareForOwner(claimed),/UNREVIEWED_PACKET_REVISION_CHANGED/);
  const wrong=(sid,ref)=>({issuer:'INDEXING_OWNER',reviewed:true,
    decision:'INDEXED',domain_use_authorized:true,source_id:sid,
    source_ref:ref,review_evidence_refs:['FAKE'],provenance:[]});
  assert.equal(Bridge.prepareForOwner(packet,wrong,{
    owner:'SYSTEM_GROW',consumer:'TAKY_REVIEW_CONSUMER',
    kind:'KNOWLEDGE_FORMING'}).status,'INDEX_OWNER_REVIEW_REQUIRED');
  const modified={...scopedQueue,review_packets:[{...scopedQueue.review_packets[0],
      verified_extracts:[{...scopedQueue.review_packets[0].verified_extracts[0],
         excerpt:'ALTERED'}]},...scopedQueue.review_packets.slice(1)]};
  assert.throws(()=>Bridge.evaluateQueue(modified),/CENTRAL_QUEUE_MANIFEST_TAMPERED/);
  assert.throws(()=>Bridge.candidateFromPacket({...packet,
    packet_revision:'0'.repeat(64)}),/UNREVIEWED_PACKET_REVISION_CHANGED/);
});

test('real GSD source carries grounded meaning into FORMING draft without fabricating approval',()=>{
 const sourceQueue=path.join(folder,'TAKY_FORMING_REVIEW_QUEUE_c35c15fc0a7e5edec0ea.json');
 const proposalFile=path.join(folder,'GSD_FORMING_APPLICATION_CANDIDATE_20261016.json');
 const {queue:scoped}=Bridge.verifyQueueOnDisk(sourceQueue);
 assert.equal(scoped.review_packet_count,1);
 const packet=scoped.review_packets[0];
 const sourceProposal=JSON.parse(fs.readFileSync(proposalFile,'utf8')).items[0];
 const policy={owner:'SYSTEM_GROW',consumer:'TAKY_EXECUTION_EVIDENCE',kind:'APPLICATION_FORMING'};
 const plan=Bridge.proposedPlanFromPacket(packet,sourceProposal,policy.consumer);
 assert.equal(plan.items.length,1);
 assert.equal(plan.items[0].source_grounding.length,2);
 assert.match(plan.items[0].observed_method,/Discuss/);
 const unreviewed=Bridge.prepareForOwner(packet,null,policy,sourceProposal);
 assert.equal(unreviewed.status,'INDEX_OWNER_REVIEW_REQUIRED');
 assert.equal(unreviewed.semantic_plan_status,'GROUNDED_PROPOSAL_AWAITING_OWNER');
 assert.equal(unreviewed.forming_draft,null);
 // Independent INDEX owner is simulated ONLY inside this test to verify wiring.
 const expected=Bridge.candidateFromPacket(packet);
 const simulatedOwner=(sourceId,sourceRef)=>({
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',domain_use_authorized:true,
  source_id:sourceId,source_ref:sourceRef,index_version:'UNIT_TEST_ONLY',
  review_evidence_refs:['TEST_ONLY_NOT_AN_APPROVAL'],
  source_family:expected.source_family,source_type:expected.source_type,
  authority_class:expected.authority_class,detail_anchor:expected.detail_anchor,
  relations:[],provenance:[...expected.provenance]
 });
 const prepared=Bridge.prepareForOwner(packet,simulatedOwner,policy,sourceProposal);
 assert.equal(prepared.status,'VERIFIED_UNAPPROVED_FORMING_DRAFT');
 const draft=prepared.forming_draft;
 assert.deepEqual(draft.semantic_plan,plan);
 assert.equal(Forming.verifyArtifact(draft).ok,true);
 assert.equal(Approved.consume({ok:true,stage:'FORMING_DRAFT',formed:draft},null,policy.consumer).ok,false);
 const edited=structuredClone(draft);
 edited.semantic_plan.items[0].proposed_change+='TAMPER';
 assert.equal(Forming.verifyArtifact(edited).ok,false);
 const falseCitation=structuredClone(sourceProposal);
 falseCitation.source_grounding[0].exact_quote='This quote was not present in any verified original source paragraph';
 assert.throws(()=>Bridge.proposedPlanFromPacket(packet,falseCitation,policy.consumer),
   /FORMING_PROOF_NOT_IN_VERIFIED_RAW/);
});

test('incorrect domain hints are quarantined even if a caller provides a plausible INDEX owner',()=>{
 const q=Bridge.verifyQueueOnDisk(path.join(folder,'TAKY_FORMING_REVIEW_QUEUE_2008abc8d54f9ca54c07.json')).queue;
 const packet=q.review_packets[0];
 assert.equal(packet.domain_hint,'ARCHITECTURE');
 assert.equal(packet.owner_review_route_hint,'OWNER_ROUTING_REQUIRED');
 const ownerCandidate=Bridge.candidateFromPacket(packet);
 const fakeAuthority=(sid,ref)=>({
  ...ownerCandidate,issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
  domain_use_authorized:true,source_id:sid,source_ref:ref,
  index_version:'TEST_ONLY',review_evidence_refs:['TEST_ONLY']
 });
 const result=Bridge.evaluateQueue(q,fakeAuthority,{owner:'ARCHI_GROW',
   consumer:'ARCHI_GROW_REVIEW_CONSUMER',kind:'KNOWLEDGE_FORMING'});
 assert.equal(result.status,'DOMAIN_ROUTING_OWNER_REVIEW_REQUIRED');
 assert.equal(result.domain_routing_owner_review_required_count,1);
 assert.equal(result.reviewed_owner_draft_count,0);
 assert.equal(result.semantic_approvals,0);
 assert.equal(result.projection_eligible,false);
 assert.equal(result.sample_results[0].issues[0],'SOURCE_INDEX_DOMAIN_HINT_CONFLICT');
});
