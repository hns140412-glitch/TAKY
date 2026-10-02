'use strict';
const assert=require('assert');
const p=require('./distribution-sync-policy');

let r=p.buildRequest({network:{online:true,type:'wifi'},bytes:10000000});
assert.equal(r.decision.allow,true);
assert.equal(r.decision.reason,'CONFIRMED_WIFI');
assert.equal(r.ui_visibility,'APP_INTERNAL');
assert.equal(r.expose_drive_structure,false);
assert.equal(r.expose_provider_credentials,false);

r=p.buildRequest({network:{online:true,type:'cellular'},bytes:10000000});
assert.equal(r.decision.allow,false);
assert.equal(r.decision.reason,'WAIT_FOR_CONFIRMED_WIFI');

r=p.buildRequest({network:{online:true},bytes:10000000});
assert.equal(r.decision.allow,false);
assert.equal(r.decision.reason,'WAIT_FOR_CONFIRMED_WIFI');

r=p.buildRequest({network:{online:false},bytes:1000});
assert.equal(r.decision.allow,false);
assert.equal(r.decision.reason,'OFFLINE');

r=p.buildRequest({network:{online:true,type:'wifi'},save_data:true,bytes:1000});
assert.equal(r.decision.allow,false);
assert.equal(r.decision.reason,'SAVE_DATA_ENABLED');

console.log('PASS: distribution sync policy');
