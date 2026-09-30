'use strict';
const assert=require('node:assert/strict');
const P=require('./explorer-crew-browser-provider-v1.js');
const packet={schema:'TAKY_CREW_EVIDENCE_HANDOFF_V1',source_app:'READY_SET',events:[{event_id:'E1',type:'SHARED_EPISODE',verified:true,evidence_ref:'EV1',character_id:'C1'}]};
(async()=>{
 assert.throws(()=>P.create({appId:'READY_SET',endpointUrl:'http://x.test/api/crew/evidence',fetchImpl:()=>{},tokenProvider:()=>'',scopeProvider:()=>({})}),/EXPLICIT_HTTPS/);
 let request;
 const provider=P.create({appId:'READY_SET',endpointUrl:'https://central.example/api/crew/evidence',fetchImpl:async(url,opt)=>{request={url,opt};return {status:200,json:async()=>({ok:true,endpoint_version:'TAKY_CENTRAL_CREW_EVIDENCE_HTTP_V1',acknowledgement_kind:'CREW_EVIDENCE_RECEIPT',receipt_id:'R1',receipt_scope:{family_id:'F1',member_id:'M1'},source_app:'READY_SET',storage_confirmed:true,relationship_auto_commit:false,learning_engine_state_mutated:false,imported_event_ids:['E1'],duplicate_event_ids:[]})}},tokenProvider:async()=>'1234567890abcdef',scopeProvider:async()=>({authenticated:true,family_id:'F1',member_id:'M1'})});
 const ok=await provider.send(packet);assert.equal(ok.ok,true);assert.equal(request.opt.credentials,'omit');assert.equal(request.opt.redirect,'error');assert.equal(request.opt.headers.Authorization,'Bearer 1234567890abcdef');assert.deepEqual(JSON.parse(request.opt.body).context,{family_id:'F1',member_id:'M1'});
 assert.equal((await provider.send({...packet,source_app:'HIDE_SEEK'})).reason,'VERIFIED_CREW_PACKET_REQUIRED');
 const noScope=P.create({appId:'READY_SET',endpointUrl:'https://central.example/api/crew/evidence',fetchImpl:async()=>{throw Error('should not call')},tokenProvider:async()=>'1234567890abcdef',scopeProvider:async()=>({authenticated:false})});
 assert.equal((await noScope.send(packet)).reason,'CENTRAL_CREW_AUTHENTICATED_SCOPE_REQUIRED');
 console.log('EXPLORER_CREW_BROWSER_PROVIDER_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
