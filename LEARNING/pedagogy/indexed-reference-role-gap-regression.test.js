'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const Policy=require('./growth-next-step-policy.js');

const projection=JSON.parse(fs.readFileSync(
 path.join(__dirname,'../../MIGRATION/PROJECTION/DATA_INDEX_V27_BRANCH_SEARCH_LEARNING_PROJECTION_2026-10-02_V1.json'),
 'utf8'
));
const curriculum=projection.learning_projection.find(x=>x.learning_evidence_role==='CURRICULUM_ALIGNMENT');
const lexical=projection.learning_projection.find(x=>x.learning_evidence_role==='LEXICAL_SEMANTICS');

assert.equal(Policy.sourceRole(curriculum),'CURRICULUM_ALIGNMENT');
assert.equal(Policy.sourceRole(lexical),'LEXICAL_SEMANTICS');
// Family/title/provenance alone must never invent a Learning evidence role.
assert.equal(Policy.sourceRole({
 source_family:'OFFICIAL_CURRICULUM',
 authority_class:curriculum.authority_class,
 provenance_tags:curriculum.provenance_tags
}),'GENERAL_REFERENCE');
assert.equal(Policy.sourceRole({
 source_family:'OPEN_ENGLISH_WORDNET_2025',
 authority_class:lexical.authority_class,
 provenance_tags:lexical.provenance_tags
}),'GENERAL_REFERENCE');

const gaps=Policy.languageResourceGaps({
 curriculum_verified:true,
 easy_english_definitions:['derived easy English candidate'],
 expression_chunks:['I can accept ...'],
 natural_collocations:[]
});
assert.equal(gaps.some(x=>x.source_role==='CURRICULUM_ALIGNMENT'),false);
assert.equal(gaps.some(x=>x.gap_type==='LEXICAL_SEMANTICS_REFERENCE_REQUIRED'),false);
assert.equal(gaps.some(x=>x.gap_type==='LANGUAGE_USAGE_REFERENCE_REQUIRED'),true);

console.log('indexed-reference-role-gap-regression.test.js PASS');
