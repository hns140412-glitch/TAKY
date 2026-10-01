'use strict';

const assert=require('assert');
const Runtime=require('./learning-engine-runtime.js');

const owner={
  source_id:'SRC-LI-1',source_ref:'INDEX:SRC-LI-1',
  source_family:'OFFICIAL_STANDARDS',source_type:'OFFICIAL_CURRICULUM',
  authority_class:'OFFICIAL',detail_anchor:'DETAIL:SRC-LI-1#standard',
  provenance:['OFFICIAL_STANDARD_REF'],
  issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',domain_use_authorized:true,
  index_version:'V1',review_evidence_refs:['OWNER:1']
};
const verifier=(sid,ref)=>sid===owner.source_id&&ref===owner.source_ref?owner:null;

const out=Runtime.derive({
  scope:{member_id:'A',subject:'science',concept_skill_target:'climate'},
  evidence:[{
    event_id:'E1',observed_at:'2026-10-02T00:00:00.000Z',
    member_id:'A',subject:'science',concept_skill_target:'climate',
    evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',source_app:'hide-seek',
    instrument_version:'hide-v1',assisted:false,verified_outcome:1,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'VR1'}
  }],
  learning_index_handoff:{
    indexed_evidence_handoff:{
      query_context:{consumer_app:'READY_SET',function_id:'LE-F01',requested_behavior:'STANDARD_ALIGNMENT'},
      candidates:[{
        source_id:'SRC-LI-1',source_ref:'INDEX:SRC-LI-1',
        source_family:'OFFICIAL_STANDARDS',source_type:'OFFICIAL_CURRICULUM',
        authority_class:'OFFICIAL',detail_anchor:'DETAIL:SRC-LI-1#standard',
        provenance:['OFFICIAL_STANDARD_REF']
      }]
    },
    learning_mapping:{
      by_source_id:{
        'SRC-LI-1':{curriculum_version:'2022',subject:'science',term:'기후',concept_node:'CLIMATE'}
      }
    }
  }
},verifier);

assert.equal(out.ok,true);
assert.equal(out.learning_index.ok,true);
assert.equal(out.learning_index.authority,'DERIVED_NON_SOURCE_OF_TRUTH');
assert.equal(out.trace.learning_index_version,'TAKY_LEARNING_INDEX_V1');
assert.deepEqual(out.trace.source_refs,['INDEX:SRC-LI-1']);
assert.equal(Runtime.validate(out).ok,true);

console.log('learning-engine-learning-index-integration.test.js PASS');
