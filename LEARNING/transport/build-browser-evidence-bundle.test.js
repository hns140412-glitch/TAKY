'use strict';
const assert=require('node:assert/strict');
const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const {build}=require('./build-browser-evidence-bundle.js');
const source=build();
assert.doesNotMatch(source,/require\(['"]node:/);
const browser={crypto:webcrypto,TextEncoder,structuredClone,URL,console};
browser.globalThis=browser;
vm.runInNewContext(source,browser,{timeout:2000});
assert.equal(typeof browser.TakyCentralEvidence.pipeline.create,'function');
const p=browser.TakyCentralEvidence.mapper.map({
 source_app:'hide-seek',
 session:{authenticated:true,family_id:'F',selected_member_id:'A'},
 event:{event_id:'e1',source_app:'hide-seek',type:'LEARNING_MEMORY_SIGNAL',
 occurred_at:'2026-09-27T10:00:00Z',member_id:'A',payload:{member_id:'A'}}
});
assert.equal(p.context.family_id,'F');
assert.throws(()=>browser.TakyCentralEvidence.pipeline.create({
 indexedDB:null,endpointUrl:'https://central.example.test/api/learning/evidence',
 fetchImpl:async()=>{},tokenProvider:async()=>'',sessionProvider:async()=>{}
}),/BROWSER_INDEXEDDB_REQUIRED/);
console.log('BROWSER_EVIDENCE_BUNDLE_PASS: isolated browser-like VM, no Node runtime require, mapper and pipeline exported');
