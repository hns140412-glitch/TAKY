'use strict';
const assert=require('node:assert/strict');
const G=require('./concept-dependency-graph.js');

const graph=G.build([
  {
    relation_id:'rel1',
    subject:'수학',
    from_concept:'fraction_basics',
    to_concept:'fraction_addition',
    relation_type:'PREREQUISITE',
    source_ref:'curriculum:math-v1'
  },
  {
    relation_id:'rel2',
    subject:'수학',
    from_concept:'fraction_equivalence',
    to_concept:'fraction_addition',
    relation_type:'PREREQUISITE',
    source_ref:'curriculum:math-v1'
  }
]);
assert.equal(graph.ok,true);
assert.equal(graph.relations.length,2);
assert.equal(graph.rejected.length,0);

const bad=G.build([{
  relation_id:'bad1',
  subject:'수학',
  from_concept:'x',
  to_concept:'y',
  relation_type:'PREREQUISITE',
  source_ref:'auto',
  inferred_from_learner_data:true
}]);
assert.equal(bad.relations.length,0);
assert.equal(bad.rejected[0].issues.includes('LEARNER_DATA_AUTO_INFERENCE_FORBIDDEN'),true);

const states=[
  {
    ok:true,
    scope:{concept_skill_target:'fraction_basics'},
    inferred:{evidence_sufficiency:'ESTABLISHED',retention_signal:'STABLE',trend:'STABLE'}
  },
  {
    ok:true,
    scope:{concept_skill_target:'fraction_equivalence'},
    inferred:{evidence_sufficiency:'SPARSE',retention_signal:'MODEL_NOT_BOUND',trend:'INSUFFICIENT_EVIDENCE'}
  }
];

const readiness=G.deriveReadiness(graph,states,'수학','fraction_addition');
assert.equal(readiness.readiness,'PREREQUISITE_RISK');
assert.equal(readiness.at_risk_prerequisites.length,1);
assert.equal(readiness.at_risk_prerequisites[0].concept,'fraction_equivalence');
assert.equal(readiness.scheduling_authority,false);
assert.equal(G.validateReadiness(readiness).ok,true);

const clear=G.deriveReadiness(graph,[
  states[0],
  {
    ok:true,
    scope:{concept_skill_target:'fraction_equivalence'},
    inferred:{evidence_sufficiency:'ESTABLISHED',retention_signal:'STABLE',trend:'STABLE'}
  }
],'수학','fraction_addition');
assert.equal(clear.readiness,'READY_SIGNAL');

const none=G.deriveReadiness(graph,states,'수학','geometry');
assert.equal(none.readiness,'NO_DECLARED_PREREQUISITE');

console.log('CONCEPT_DEPENDENCY_GRAPH_PASS');

const candidateGraph=G.build([
  {
    relation_id:'cand1',
    subject:'수학',
    from_concept:'number_sense',
    to_concept:'fraction_basics',
    relation_type:'PREREQUISITE',
    source_ref:'learner-analysis:trial-001',
    authority:'DATA_CANDIDATE',
    inferred_from_learner_data:true,
    confidence:0.72
  }
]);
assert.equal(candidateGraph.ok,true);
assert.equal(candidateGraph.active_relations.length,0);
assert.equal(candidateGraph.candidate_relations.length,1);
assert.equal(candidateGraph.candidate_relations[0].state,'CANDIDATE');
assert.equal(candidateGraph.candidate_relations[0].can_influence_learning_sequence,false);
assert.equal(G.prerequisitesFor(candidateGraph,'수학','fraction_basics').length,0,'data candidate must not become active prerequisite');
assert.equal(G.candidateRelationsFor(candidateGraph,'수학','fraction_basics').length,1);
assert.equal(G.selfValidate(candidateGraph).ok,true);

const cycle=G.build([
  {relation_id:'c1',subject:'수학',from_concept:'a',to_concept:'b',relation_type:'PREREQUISITE',source_ref:'curriculum:v1'},
  {relation_id:'c2',subject:'수학',from_concept:'b',to_concept:'a',relation_type:'PREREQUISITE',source_ref:'curriculum:v1'}
]);
assert.equal(cycle.ok,false);
assert.equal(cycle.cycles.length>0,true);
assert.equal(G.selfValidate(cycle).ok,false);
assert.equal(G.selfValidate(cycle).issues.includes('ACTIVE_PREREQUISITE_CYCLE'),true);
