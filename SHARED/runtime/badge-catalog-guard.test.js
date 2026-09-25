'use strict';
const assert=require('node:assert/strict');
const G=require('./badge-catalog-guard.js');
const draft={status:'WORKING_DRAFT_NOT_ACTIVE',items:[{status:'WORKING_DRAFT',active:false}]};
assert.equal(G.validateCatalog(draft),true);
assert.equal(G.activeItems(draft).length,0);
assert.throws(()=>G.validateCatalog({status:'WORKING_DRAFT_NOT_ACTIVE',items:[{status:'WORKING_DRAFT',active:true}]}),/BADGE_WORKING_DRAFT_ACTIVATION_FORBIDDEN/);
console.log('TAKY_BADGE_CATALOG_GUARD_V1_PASS');
