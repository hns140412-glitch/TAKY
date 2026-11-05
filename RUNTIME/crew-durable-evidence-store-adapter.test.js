'use strict';
const assert=require('node:assert/strict');
const D=require('./crew-durable-evidence-store-adapter.js');
let writes=0;
const store={row:null,async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null},async setJSON(key,value,opts){writes++;this.row={key,data:value,etag:'e'+writes,opts};return {modified:true,etag:this.row.etag}}};
const event={event_id:'E1',type:'FIRST_MEETING',verified:true,evidence_ref:'EV1',character_id:'C1',source_app:'READY_SET',source:'READY_SET',at:'2026-09-30T12:00:00Z'};
const packet={schema:'TAKY_CREW_EVIDENCE_HANDOFF_V1',source_app:'READY_SET',context:{family_id:'F1',member_id:'CHILD'},events:[event]};
(async()=>{
 const a=await D.ingestPacket(store,packet);assert.equal(a.ok,true);assert.equal(a.acknowledgement_kind,'CREW_EVIDENCE_RECEIPT');assert.equal(a.imported[0],'E1');
 const b=await D.ingestPacket(store,packet);assert.equal(b.ok,true);assert.deepEqual(b.duplicates,['E1']);
 const changed={...packet,events:[{...event,evidence_ref:'DIFFERENT'}]};
 const c=await D.ingestPacket(store,changed);assert.equal(c.ok,false);assert.equal(c.reason,'CREW_EVENT_REPLAY_PAYLOAD_MISMATCH');
 assert.match(D.stateKey(packet),/explorer-crew\/state-v1$/);
 console.log('CREW_DURABLE_EVIDENCE_STORE_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
