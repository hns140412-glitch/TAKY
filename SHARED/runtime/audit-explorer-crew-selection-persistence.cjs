'use strict';
const assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
const system=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/system-v2.js');
const map=new Map();
const storage={getItem:key=>map.get(key)||null,setItem:(key,val)=>map.set(key,val),removeItem:key=>map.delete(key)};
const ctl=system.create({app_id:'HIDE_SEEK',storage,replaceUrl:()=>{}});
const before=ctl.snapshot().relation;
const events=[];
async function call(type,extra={}){
 const now=new Date().toISOString();
 const e={character_id:'dubi',interaction_result:{relation_event:{character_id:'dubi',type,at:now,...extra}}};
 if(type==='SHARED_ACTIVITY'){e.companion_gate={affinity_requirement_met:true,story_unlocked:true};}
 try{
  const result=await ctl.dispatch(e);
  events.push({type,ok:result?.ok??null,relation:ctl.snapshot().relation.members.dubi.relation_state,
    main:ctl.snapshot().relation.main_character_id});
 }catch(error){events.push({type,error:String(error?.message||error)})}
}
(async()=>{
 await call('FIRST_MET');
 await call('SHARED_ACTIVITY',{event_id:'qa-scene-001'});
 await call('MAIN_SELECTED');
 const after=ctl.snapshot().relation;
 const keys=[...map.keys()];
 const expectedStore=storage.getItem('taky_explorer_crew_canonical_v1');
 const report={status:before.main_character_id===null && after.main_character_id==='dubi'?'PASS':'FAIL',
  events,stored_keys:keys,picker_uses_store_key:'taky_explorer_crew_canonical_v1',
  store_key_present:!!expectedStore,
  actual_main:after.main_character_id,actual_state:after.members.dubi.relation_state};
 const out='D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_CANONICAL_SELECTION_PERSISTENCE_AUDIT_20261013.json';
 fs.writeFileSync(out,JSON.stringify(report,null,2));
 console.log(JSON.stringify(report,null,2));
 if(report.status!=='PASS')process.exitCode=2;
})().catch(e=>{console.error(e);process.exitCode=2});
