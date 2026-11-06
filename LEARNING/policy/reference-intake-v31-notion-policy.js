'use strict';

const V29=require('./reference-intake-v29-policy.js');

const VERSION='TAKY_REFERENCE_INTAKE_V31_NOTION_POLICY_OVERLAY_V1';
const EXTRA=[
  {
    policy_id:'P-V31-CONCEPT-GAP-HIDE',
    function_id:'LE-RV31-CONCEPT-GAP',
    consumer_app:'HIDE_SEEK',
    authorization_class:'CONDITIONAL',
    allowed_behaviors:['CONCEPT_GAP_REFERENCE_SUPPORT'],
    forbidden_behaviors:['LEARNER_DIAGNOSIS','MASTERY_INFERENCE','AUTO_CURRICULUM_ALIGNMENT'],
    cannot_claim:['LEARNER_DIAGNOSIS_FROM_REFERENCE','LEARNER_MASTERY_FROM_REFERENCE','COMMERCIAL_PRODUCT_EFFECTIVENESS'],
    required_provenance:['REFERENCE_MINING_INDEX','REF-081'],
    requires_human_review:false
  },
  {
    policy_id:'P-V31-EBS-DISCOVERY-READY',
    function_id:'LE-RV31-EBS-DISCOVERY',
    consumer_app:'READY_SET',
    authorization_class:'CONDITIONAL',
    allowed_behaviors:['OFFICIAL_RESOURCE_DISCOVERY'],
    forbidden_behaviors:['MASTERY_INFERENCE','AUTO_SCHEDULE','PORTAL_SHELL_AS_LEARNING_EVIDENCE'],
    cannot_claim:['PORTAL_PAGE_IS_LEARNING_EVIDENCE','RESOURCE_EXPOSURE_IS_MASTERY','PLANNER_SCHEDULE_AUTHORITY'],
    required_provenance:['REFERENCE_MINING_INDEX','REF-084'],
    requires_human_review:false
  },
  {
    policy_id:'P-V31-MATH-RELATION-HIDE',
    function_id:'LE-RV31-MATH-RELATION',
    consumer_app:'HIDE_SEEK',
    authorization_class:'CONDITIONAL',
    allowed_behaviors:['MATH_CONCEPT_RELATION_REFERENCE','BLANK_RECALL_REFERENCE'],
    forbidden_behaviors:['OFFICIAL_CURRICULUM_AUTHORITY','MASTERY_INFERENCE','AUTO_COMPLETED_ANSWER'],
    cannot_claim:['COMMERCIAL_WORKSHEET_IS_CURRICULUM_AUTHORITY','REFERENCE_EXPOSURE_IS_MASTERY','SOURCE_TEXT_IS_LEARNER_AUTHORED_OUTPUT'],
    required_provenance:['REFERENCE_MINING_INDEX','REF-085'],
    requires_human_review:false
  }
];

const REGISTRY=Object.freeze({
  ...V29.REGISTRY,
  policy_version:'2026-10-04.V31-NOTION-BRANCH',
  index_authority:{
    source_index:'DATA_SOURCE_INDEX_2026-10-02_V10.json + V31-NOTION-DELTA',
    utilization_index:'DATA_UTILIZATION_INDEX_2026-10-02_V30.json + V31-NOTION-DELTA'
  },
  overlay_version:VERSION,
  overlay_scope:'REF-081_REF-084_REF-085_LEARNING_REFERENCES_ONLY',
  branch_scoped:true,
  records:[...(V29.REGISTRY.records||[]),...EXTRA]
});

module.exports=Object.freeze({VERSION,REGISTRY});
