'use strict';

const assert=require('node:assert/strict');
const Gap=require('./evidence-gap.js');

const none=Gap.derive({
  scope:{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},
  decision:{blockers:[{code:'NO_EVIDENCE',priority:'HIGH'}],advisories:[],state_summary:{evidence_sufficiency:'NONE'}}
});
assert.equal(none.ok,true);
assert.equal(none.gap.gap_type,'LEARNER_EVIDENCE_ABSENT');
assert.equal(none.gap.index_check_required,false);
assert.equal(none.gap.resolution_path,'SPECIALIST_EVIDENCE_ACQUISITION');
assert.equal(none.gap.mining_request_authorized,false);

const reference=Gap.derive({
  scope:{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},
  decision:{blockers:[],advisories:[],state_summary:{evidence_sufficiency:'EMERGING'}},
  reference_requirement:{
    function_id:'LE-F01',
    consumer_app:'READY_SET',
    requested_behavior:'STANDARD_ALIGNMENT',
    priority:'MEDIUM',
    acceptable_source_families:['OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS'],
    acceptable_authority_classes:['OFFICIAL'],
    required_provenance:['OFFICIAL_STANDARD_REF'],
    query_terms:['영어','VOCABULARY','교육과정']
  }
});
assert.equal(reference.ok,true);
assert.equal(reference.gap.gap_type,'REFERENCE_EVIDENCE_REQUIRED');
assert.equal(reference.gap.index_check_required,true);
assert.equal(reference.gap.resolution_path,'INDEX_THEN_MINING_IF_INSUFFICIENT');

const enough=Gap.derive({
  scope:{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},
  decision:{blockers:[],advisories:[],state_summary:{evidence_sufficiency:'EMERGING'}}
});
assert.equal(enough.gap,null);



const lexicalMissing=Gap.derive({
  scope:{member_id:'A',subject:'english',concept_skill_target:'vocabulary'},
  decision:{blockers:[],advisories:[],state_summary:{evidence_sufficiency:'EMERGING'}},
  indexed_evidence:{
    source_refs:['INDEX:EDU1'],
    candidates:[{
      source_id:'EDU1',source_ref:'INDEX:EDU1',
      source_family:'OFFICIAL_CURRICULUM',authority_class:'OFFICIAL',
      provenance:['OFFICIAL_EDUCATION_SOURCE']
    }]
  },
  reference_requirement:{
    gap_type:'LEXICAL_SEMANTICS_REFERENCE_REQUIRED',
    function_id:'LE-GROWTH-01',consumer_app:'LEARNING_ENGINE',
    requested_behavior:'CURRICULUM_GROUNDED_LANGUAGE_GROWTH',
    requested_capability:'LEXICAL_SEMANTICS',
    required_learning_evidence_role:'LEXICAL_SEMANTICS',
    required_provenance_any_of:['LEXICAL_REFERENCE_SOURCE'],
    priority:'MEDIUM'
  }
});
assert.equal(lexicalMissing.gap.gap_type,'LEXICAL_SEMANTICS_REFERENCE_REQUIRED');
assert.deepEqual(lexicalMissing.gap.existing_source_refs,['INDEX:EDU1']);
assert.deepEqual(lexicalMissing.gap.required_provenance_any_of,['LEXICAL_REFERENCE_SOURCE']);
assert.equal(lexicalMissing.gap.mining_request_authorized,false);

const lexicalPresent=Gap.derive({
  scope:{member_id:'A',subject:'english',concept_skill_target:'vocabulary'},
  decision:{blockers:[],advisories:[],state_summary:{evidence_sufficiency:'EMERGING'}},
  indexed_evidence:{
    source_refs:['INDEX:EDU1','INDEX:DICT1'],
    candidates:[
      {source_id:'EDU1',source_ref:'INDEX:EDU1',provenance:['OFFICIAL_EDUCATION_SOURCE']},
      {source_id:'DICT1',source_ref:'INDEX:DICT1',provenance:['LEXICAL_REFERENCE_SOURCE']}
    ]
  },
  reference_requirement:{
    gap_type:'LEXICAL_SEMANTICS_REFERENCE_REQUIRED',
    function_id:'LE-GROWTH-01',consumer_app:'LEARNING_ENGINE',
    requested_behavior:'CURRICULUM_GROUNDED_LANGUAGE_GROWTH',
    requested_capability:'LEXICAL_SEMANTICS',
    required_learning_evidence_role:'LEXICAL_SEMANTICS',
    required_provenance_any_of:['LEXICAL_REFERENCE_SOURCE']
  }
});
assert.equal(lexicalPresent.gap,null);
assert.deepEqual(lexicalPresent.satisfied_reference_requirement.matching_source_refs,['INDEX:DICT1']);

console.log('LEARNING_EVIDENCE_GAP_PASS');