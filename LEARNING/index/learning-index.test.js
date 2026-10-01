'use strict';

const assert=require('assert');
const LearningIndex=require('./learning-index.js');

const OWNER={
  source_id:'SRC1',source_ref:'INDEX:SRC1',source_family:'OFFICIAL',
  source_type:'OFFICIAL_CURRICULUM',authority_class:'OFFICIAL',
  detail_anchor:'DETAIL:SRC1#1',provenance:['OFFICIAL_EDUCATION_SOURCE'],
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',domain_use_authorized:true,
  index_version:'V1',review_evidence_refs:['R1']
};
const verifier=(sid,ref)=>sid===OWNER.source_id&&ref===OWNER.source_ref?OWNER:null;
const base={
  indexed_evidence_handoff:{
    query_context:{consumer_app:'READY_SET',function_id:'LE-F01',requested_behavior:'STANDARD_ALIGNMENT'},
    candidates:[{
      source_id:'SRC1',source_ref:'INDEX:SRC1',source_family:'OFFICIAL',
      source_type:'OFFICIAL_CURRICULUM',authority_class:'OFFICIAL',
      detail_anchor:'DETAIL:SRC1#1',provenance:['OFFICIAL_EDUCATION_SOURCE']
    }]
  },
  learning_mapping:{
    by_source_id:{
      SRC1:{curriculum_version:'2022',subject:'science',term:'지층',concept_node:'GEO_LAYER',easy_english_definition:'a layer of rock or soil',expression_chunks:['It is made of ...'],grammar_patterns:['It is + adjective'],thinking_moves:['COMPARE']}
    }
  }
};

const view=LearningIndex.prepare(base,verifier);
assert.equal(view.ok,true);
assert.equal(view.authority,'DERIVED_NON_SOURCE_OF_TRUTH');
assert.deepEqual(view.source_refs,['INDEX:SRC1']);
assert.equal(view.semantic_items[0].learning_evidence_role,'CURRICULUM_ALIGNMENT');
assert.equal(view.semantic_items[0].semantic_groups.lexical.term,'지층');
assert.equal(view.semantic_items[0].semantic_groups.concept.concept_node,'GEO_LAYER');
assert.equal(view.semantic_items[0].semantic_groups.language_growth.easy_english_definition,'a layer of rock or soil');
assert.deepEqual(view.semantic_items[0].semantic_groups.language_growth.expression_chunks,['It is made of ...']);
assert.equal(LearningIndex.validate(view).ok,true);

const roleAmbiguous=LearningIndex.evidenceRoleFromProvenance([
  'OFFICIAL_EDUCATION_SOURCE','LEXICAL_REFERENCE_SOURCE'
]);
assert.equal(roleAmbiguous.ambiguous,true);
assert.equal(roleAmbiguous.role,null);

const bad=LearningIndex.prepare({...base,learning_mapping:{default:{mastery_estimate:0.9}}},verifier);
assert.equal(bad.ok,false);
assert.equal(bad.reason,'LEARNING_INDEX_PROHIBITED_LEARNER_OR_SCHEDULE_FIELD');

console.log('learning-index.test.js PASS');
