'use strict';
const assert=require('node:assert/strict');
const C=require('./badge-candidate-review.js');

const p=C.propose({
  candidate_id:'BC1',
  member_id:'C1',
  proposed_name:'새 배지 후보',
  behavior_family:'HELP_REQUEST',
  rationale:'explicit help request evidence',
  evidence_event_ids:['E1','E1','E2'],
  source_app:'hide-seek',
  active:true,
  award_authorized:true
});
assert.equal(p.ok,true);
assert.equal(p.candidate.status,'REVIEW_REQUIRED');
assert.equal(p.candidate.active,false);
assert.equal(p.candidate.award_authorized,false);
assert.equal(p.candidate.catalog_insert_authorized,false);
assert.deepEqual(p.candidate.evidence_event_ids,['E1','E2']);

const approved=C.review(p.candidate,{
  action:'APPROVE_FOR_CATALOG_REVIEW',
  reviewed_by:'PARENT_REVIEW',
  reviewed_at:'2026-09-26T00:00:00.000Z'
});
assert.equal(approved.ok,true);
assert.equal(approved.candidate.status,'APPROVED_FOR_CATALOG_REVIEW');
assert.equal(approved.candidate.active,false);
assert.equal(approved.candidate.award_authorized,false);

const bad=C.propose({candidate_id:'BC2',member_id:'C1',behavior_family:'RETRY'});
assert.equal(bad.ok,false);
assert(bad.issues.includes('EVIDENCE_EVENT_IDS_REQUIRED'));

console.log('TAKY_BADGE_CANDIDATE_REVIEW_V1_PASS');
