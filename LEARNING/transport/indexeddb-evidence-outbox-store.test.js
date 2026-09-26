'use strict';
const cryptoProvider=require('node:crypto').webcrypto;
const assert=require('node:assert/strict');
const Adapter=require('./indexeddb-evidence-outbox-store.js');
const Outbox=require('./scoped-evidence-outbox.js');
// Deterministic IndexedDB transaction fixture. Requests fire asynchronously;
// a readwrite transaction serializes get+put, as the browser IDB contract does.
function fakeIDB(){
 const data=new Map();let writeTail=Promise.resolve();
 const db={
  objectStoreNames:{contains:x=>x==='queue'},
  createObjectStore:()=>{},close(){},
  transaction(name,mode){
   assert.equal(name,'queue');
   const tx={oncomplete:null,onerror:null,onabort:null,error:null};
   let pending=0,active=true,ready=Promise.resolve(),release=()=>{};
   if(mode==='readwrite'){
    const prior=writeTail;
    writeTail=new Promise(r=>{release=r});
    ready=prior;
   }
   function finish(){
    if(!active||pending)return;
    queueMicrotask(()=>{if(!active||pending)return;active=false;
     release();tx.oncomplete?.()});
   }
   tx.objectStore=()=>({
    get(key){
     pending++;const req={result:null,onsuccess:null};
     ready.then(()=>queueMicrotask(()=>{
      req.result=structuredClone(data.get(key));req.onsuccess?.();
      pending--;finish();
     }));
     return req;
    },
    put(value,key){
     pending++;ready.then(()=>queueMicrotask(()=>{
      data.set(key,structuredClone(value));pending--;finish();
     }));
    }
   });
   tx.abort=()=>{active=false;release();tx.onabort?.()};
   return tx;
  }
 };
 return {open(name,version){
  assert.equal(version,1);
  const req={result:db,onupgradeneeded:null,onsuccess:null,onerror:null};
  queueMicrotask(()=>{req.onupgradeneeded?.();req.onsuccess?.()});
  return req;
 }};
}
(async()=>{
 const indexedDB=fakeIDB();
 const a=Adapter.create({indexedDB}),b=Adapter.create({indexedDB});
 const start=await a.read();
 assert.equal(start.version,0);
 assert.deepEqual(start.data.entries,[]);
 const [one,two]=await Promise.all([
  a.compareAndSwap(0,{entries:[{key:'first'}]}),
  b.compareAndSwap(0,{entries:[{key:'second'}]})
 ]);
 assert.equal([one,two].filter(Boolean).length,1);
 assert.equal((await a.read()).version,1);
 assert.equal(await b.compareAndSwap(0,{entries:[]}),false);
 // Clear the disposable CAS probe row before testing scoped queue behavior.
 const probe=await a.read();
 assert.equal(await a.compareAndSwap(probe.version,{entries:[]}),true);
 const q=Outbox.create({storage:a,cryptoProvider});
 const p={packet_id:'hide-seek:e1',source_app:'hide-seek',
  context:{family_id:'F',member_id:'A'},
  event:{event_id:'e1',source:'hide-seek'}};
 assert.equal((await q.enqueue(p)).queued,true);
 assert.equal((await q.enqueue(p)).duplicate,true);
 const rows=await Outbox.create({storage:b,cryptoProvider}).list(['F','A','hide-seek']);
 assert.equal(rows.length,1);
 assert.equal(rows[0].status,'PENDING');
 await a.close();await b.close();
 assert.throws(()=>Adapter.create({indexedDB:null}),/BROWSER_INDEXEDDB_REQUIRED/);
 console.log('INDEXEDDB_EVIDENCE_OUTBOX_STORE_PASS: async IDB transaction fixture, competing CAS one winner, cross-instance persistent scoped queue');
})().catch(e=>{console.error(e);process.exitCode=1});
