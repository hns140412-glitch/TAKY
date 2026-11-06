'use strict';
const assert=require('node:assert/strict');
const S=require('./family-session-http-endpoint.js');
const token='verified-family-session-token-0001';
const verify=async t=>{assert.equal(t,token);return{authenticated:true,principal_id:'google:sub1',identity_provider:'GOOGLE_OIDC_VERIFIED',families:[{family_id:'F1',self_member_id:'P1',authorized_member_ids:['C1','P1']}]}};
const req=()=>({method:'POST',path:S.ENDPOINT,headers:{'content-type':'application/json',authorization:'Bearer '+token},body:'{}'});
(async()=>{const ep=S.create({verifyBearerToken:verify});const r=await ep.handle(req()),b=JSON.parse(r.body);assert.equal(r.status,200);assert.equal(b.session.families[0].family_id,'F1');assert.deepEqual(b.session.families[0].authorized_member_ids,['C1','P1']);assert.equal(b.session.email,undefined);console.log('FAMILY_SESSION_HTTP_PASS: verified bearer -> server family scope projection only')})().catch(e=>{console.error(e);process.exit(1)});
