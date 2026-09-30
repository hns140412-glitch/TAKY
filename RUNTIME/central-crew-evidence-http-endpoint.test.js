'use strict';
const assert=require('node:assert/strict');
const E=require('./central-crew-evidence-http-endpoint.js');
let writes=0;
const store={row:null,async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null},async setJSON(key,value){writes++;this.row={data:value,etag:'e'+writes};return {modified:true,etag:this.row.etag}}};
const packet={schema:'TAKY_CREW_EVIDENCE_HANDOFF_V1',source_app:'READY_SET',context:{family_id:'F1',member_id:'C1'},events:[{event_id:'E1',type:'SHARED_EPISODE',verified:true,evidence_ref:'EV1',character_id:'C1',source_app:'READY_SET'}]};
const req=body=>({method:'POST',path:'/api/crew/evidence',headers:{'content-type':'application/json','authorization':'Bearer 1234567890abcdef'},body:JSON.stringify(body)});
const principal={authenticated:true,family_id:'F1',memberships:[{member_id:'C1',role:'CHILD',active:true}]};
(async()=>{
 assert.throws(()=>E.create({verifyBearerToken:async()=>principal,store}),/TRUSTED_CREW_EVIDENCE_VERIFIER_REQUIRED/);
 const endpoint=E.create({verifyBearerToken:async()=>principal,store,verifyCrewEvidence:async({packet:p})=>({ok:true,packet:{...p,events:p.events.map(e=>({...e,verified:true}))}})});
 const ok=await endpoint.handle(req(packet));const body=JSON.parse(ok.body);assert.equal(ok.status,200);assert.equal(body.ok,true);assert.equal(body.relationship_auto_commit,false);assert.equal(body.learning_engine_state_mutated,false);
 const denied=E.create({verifyBearerToken:async()=>({...principal,memberships:[{member_id:'OTHER',role:'CHILD',active:true}]}),store,verifyCrewEvidence:async()=>({ok:true,packet})});
 assert.equal((await denied.handle(req(packet))).status,403);
 const selfClaim=E.scrub(packet);assert.equal(selfClaim.events[0].verified,undefined);
 console.log('CENTRAL_CREW_EVIDENCE_HTTP_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
