'use strict';

const assert=require('assert');
const Runtime=require('./learning-engine-runtime.js');

const owner={
  source_id:'EDU-ENG-G5-1',
  source_ref:'INDEX:EDU-ENG-G5-1',
  source_family:'OFFICIAL_CURRICULUM',
  source_type:'OFFICIAL_EDUCATION_STANDARD',
  authority_class:'OFFICIAL',
  detail_anchor:'DETAIL:EDU-ENG-G5-1#language-growth',
  provenance:['OFFICIAL_EDUCATION_SOURCE'],
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',domain_use_authorized:true,
  index_version:'V1',review_evidence_refs:['REVIEW:EDU-1']
};
const verifier=(sid,ref)=>sid===owner.source_id&&ref===owner.source_ref?owner:null;

const evidence=[
  {
    event_id:'H1',observed_at:'2026-10-01T09:00:00.000Z',
    member_id:'A',subject:'english',concept_skill_target:'vocabulary',
    learning_target_id:'accept',evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
    source_app:'hide-seek',instrument_version:'HIDE_TRACE_V2',
    interaction_mode:'TRACE',assisted:false,verified_outcome:null,
    language_growth_signals:[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,target_id:'accept'},
      {dimension:'ENGLISH_THINKING',outcome:'PARTIAL',direct_english:false,target_id:'accept'}
    ]
  },
  {
    event_id:'S1',observed_at:'2026-10-02T09:00:00.000Z',
    member_id:'A',subject:'english',concept_skill_target:'vocabulary',
    learning_target_id:'accept',evidence_type:'LEARNER_PRODUCTION_EVIDENCE',
    source_app:'snap-pop',instrument_version:'SNAP_PRODUCTION_V1',
    interaction_mode:'SENTENCE',assisted:true,verified_outcome:null,
    language_growth_signals:[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true,target_id:'accept'},
      {dimension:'GRAMMAR',outcome:'PARTIAL',assisted:true,target_id:'accept'},
      {dimension:'EXPRESSION',outcome:'PARTIAL',assisted:true,target_id:'accept'},
      {dimension:'THINKING',outcome:'SUCCESS',assisted:false,depth:3,transfer:true,target_id:'accept'}
    ]
  }
];

const out=Runtime.derive({
  scope:{member_id:'A',subject:'english',concept_skill_target:'vocabulary'},
  evidence,
  growth_context:{enabled:true,learner_context:{grade:5}},
  learning_index_handoff:{
    indexed_evidence_handoff:{
      query_context:{consumer_app:'LEARNING_ENGINE',function_id:'LE-GROWTH-01',requested_behavior:'CURRICULUM_GROUNDED_LANGUAGE_GROWTH'},
      candidates:[{
        source_id:owner.source_id,source_ref:owner.source_ref,
        source_family:owner.source_family,source_type:owner.source_type,
        authority_class:owner.authority_class,detail_anchor:owner.detail_anchor,
        provenance:[...owner.provenance]
      }]
    },
    learning_mapping:{
      by_source_id:{
        'EDU-ENG-G5-1':{
          curriculum_version:'2022',grade:5,subject:'english',
          achievement_standard_refs:['ENG-G5-EXPR-01'],
          term:'accept',
          easy_english_definition:'to say yes to something or receive it',
          expression_chunks:['accept an idea','I can accept ...'],
          natural_collocations:['accept an idea','accept an invitation'],
          grammar_patterns:['can + base verb','accept + noun'],
          thinking_moves:['EXPLAIN','COMPARE','APPLY'],
          question_stems:['Why would someone accept it?'],
          production_targets:['USE_WORD_IN_OWN_SENTENCE'],
          english_thinking_support:['picture -> easy English meaning -> chunk -> own sentence']
        }
      }
    }
  }
},verifier);

assert.equal(out.ok,true);
assert.equal(out.growth_profile.ok,true);
assert.equal(out.growth_profile.learner_context.language_load,'SIMPLE');
assert.equal(out.growth_profile.dimensions.VOCABULARY.state,'READY_TO_STRETCH');
assert.equal(out.growth_next_step.ok,true);
assert.equal(out.growth_next_step.curriculum_grounding.verified,true);
assert.equal(out.growth_next_step.guards.engine_guides_growth_not_answers,true);
assert.equal(out.growth_next_step.guards.korean_to_english_word_by_word_translation_is_not_default,true);
assert.ok(out.growth_next_step.language_support.easy_english_definitions.length>0);
assert.ok(out.growth_next_step.language_support.expression_chunks.length>0);
assert.equal(out.growth_next_step.hide_to_snap_handoff.to_app,'snap-pop');
assert.equal(out.growth_next_step.hide_to_snap_handoff.child_authorship_required,true);
assert.equal(out.growth_next_step.hide_to_snap_handoff.final_answer_generation_forbidden,true);
assert.equal(out.growth_next_step.reference_gap_candidate,null);
assert.equal(Runtime.validate(out).ok,true);

console.log('learning-engine-language-growth-integration.test.js PASS');
