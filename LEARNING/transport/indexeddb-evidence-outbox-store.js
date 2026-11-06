'use strict';
/**
 * Browser-only IndexedDB persistence for the evidence outbox.
 * A single readwrite transaction owns read/version-check/write. Never split
 * CAS across transactions or use localStorage for multi-tab concurrency.
 * Inject indexedDB from the PWA host; no DB opens at module import.
 */
const VERSION='TAKY_INDEXEDDB_EVIDENCE_OUTBOX_STORE_V1';
const DB='taky-central-learning-evidence-outbox-v1',STORE='queue';
function create({indexedDB,dbName=DB}={}){
 if(typeof indexedDB?.open!=='function'||typeof dbName!=='string'||!dbName)
  throw Error('BROWSER_INDEXEDDB_REQUIRED');
 let connection;
 function open(){
  if(connection)return connection;
  connection=new Promise((resolve,reject)=>{
   const req=indexedDB.open(dbName,1);
   req.onupgradeneeded=()=>{
    const db=req.result;
    if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE);
   };
   req.onerror=()=>reject(req.error||Error('OUTBOX_IDB_OPEN_FAILED'));
   req.onsuccess=()=>{
    const db=req.result;
    db.onversionchange=()=>{db.close();connection=null};
    resolve(db);
   };
  }).catch(e=>{connection=null;throw e});
  return connection;
 }
 function transaction(mode,operate){
  return open().then(db=>new Promise((resolve,reject)=>{
   let result,finished=false;
   const tx=db.transaction(STORE,mode),store=tx.objectStore(STORE);
   tx.oncomplete=()=>{finished=true;resolve(result)};
   tx.onerror=()=>{if(!finished)reject(tx.error||Error('OUTBOX_IDB_TX_FAILED'))};
   tx.onabort=()=>{if(!finished)reject(tx.error||Error('OUTBOX_IDB_TX_ABORTED'))};
   try{operate(store,v=>{result=v})}catch(e){tx.abort();reject(e)}
  }));
 }
 return Object.freeze({
  version:VERSION,
  async read(){
   return transaction('readonly',(store,done)=>{
    const req=store.get('state');
    req.onsuccess=()=>{
     const row=req.result||{version:0,data:{entries:[]}};
     done(structuredClone(row));
    };
   });
  },
  async compareAndSwap(expected,next){
   if(!Number.isSafeInteger(expected)||expected<0||
      !Array.isArray(next?.entries))throw Error('OUTBOX_CAS_INPUT_INVALID');
   return transaction('readwrite',(store,done)=>{
    const req=store.get('state');
    req.onsuccess=()=>{
     const old=req.result||{version:0,data:{entries:[]}};
     if(old.version!==expected){done(false);return}
     store.put({version:expected+1,data:structuredClone(next)},'state');
     done(true);
    };
   });
  },
  async close(){
   if(connection){const db=await connection;db.close();connection=null}
  }
 });
}
module.exports=Object.freeze({VERSION,DB,STORE,create});
