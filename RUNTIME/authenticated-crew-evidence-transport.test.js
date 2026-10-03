'use strict';
const assert=require('node:assert/strict');
const T=require('./authenticated-crew-evidence-transport.js');
let writes=0;
const store={row:null,async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null},async setJSON(key,value){writes++;this.row={data:value,etag:'e'+writes};return {modified:true,etag:this.row.etag}}};
const packet={schema:'TAKY_CREW_EVIDENCE_HANDOFF_V1',source_app:'READY_SET',context:{family_id:'F1',member_id:'CHILD'},events:[{event_id:'E1',type:'SHARED_EPISODE',verified:true,evidence_ref:'EV1',character_id:'C1',source_app:'READY_SET'}]};
(async()=>{
 const denied=await T.ingestAuthenticated(store,packet,{authenticated:true,family_id:'F1',authorized_member_ids:['OTHER']});assert.equal(denied.ok,false);assert.equal(writes,0);
 const ok=await T.ingestAuthenticated(store,packet,{authenticated:true,family_id:'F1',authorized_member_ids:['CHILD']});assert.equal(ok.ok,true);assert.equal(ok.authenticated_scope.member_id,'CHILD');assert.equal(writes,1);
 console.log('AUTHENTICATED_CREW_EVIDENCE_TRANSPORT_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
