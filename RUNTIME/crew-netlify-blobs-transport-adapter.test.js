'use strict';
const assert=require('node:assert/strict');
const N=require('./crew-netlify-blobs-transport-adapter.js');
let args=null,writes=0;
const store={row:null,async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null},async setJSON(key,value){writes++;this.row={data:value,etag:'e'+writes};return {modified:true,etag:this.row.etag}}};
const packet={schema:'TAKY_CREW_EVIDENCE_HANDOFF_V1',source_app:'HIDE_SEEK',context:{family_id:'F1',member_id:'CHILD'},events:[{event_id:'E1',type:'HELP_ACCEPTED',verified:true,evidence_ref:'EV1',character_id:'C1',source_app:'HIDE_SEEK'}]};
(async()=>{
 const a=N.create({getStore:x=>(args=x,store),resolveIdentity:async()=>({authenticated:true,family_id:'F1',authorized_member_ids:['CHILD']})});
 const out=await a.ingest(packet,{});assert.equal(out.ok,true);assert.equal(out.store_consistency,'strong');assert.equal(args.consistency,'strong');assert.equal(out.deployment_authority,false);
 assert.throws(()=>N.create({getStore:()=>store}),/IDENTITY_RESOLVER_REQUIRED/);
 console.log('CREW_NETLIFY_BLOBS_TRANSPORT_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
