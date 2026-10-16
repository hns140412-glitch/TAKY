'use strict';
/*
 * Explicit server-side composition. Inject an HNS-held SIEZEALL OAuth token
 * provider; never browser credentials or anonymous Drive links.
 * No automatic unbounded polling: an authenticated operator/service runner
 * invokes processRecord only for a concrete durable outbox item.
 */
const Rest=require('./siezeall-drive-rest-transport.js');
const UserData=require('./family-user-data-store.js');
const Queue=require('./family-user-data-archive-outbox.js');
const Publisher=require('./family-user-data-siezeall-archive-publisher.js');
const VERSION='TAKY_FAMILY_USER_DATA_ARCHIVE_SERVICE_V1';
function create({store,getSiezeallAccessToken,fetchImpl,encryptionKey,encryptionKeyId}={}){
 const drive=Rest.create({getAccessToken:getSiezeallAccessToken,fetchImpl});
 const publisher=Publisher.create({store,drive,encryptionKey,keyId:encryptionKeyId});
 return Object.freeze({
  version:VERSION,
  route_id:publisher.route_id,
  verifyRoute:()=>publisher.verifyChain(),
  // Only a verified central record identity is accepted here, not user URL/path.
  processRecord:async({family_id,member_id,record_type,record_id})=>{
   const ref={family_id,member_id,record_type,record_id};
   const key=UserData.keyFor(ref,record_type,record_id);
   if(!key)return{ok:false,reason:'ARCHIVE_RECORD_ID_INVALID'};
   const current=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
   if(!current?.etag||current.data?.family_id!==family_id||current.data?.member_id!==member_id)
    return{ok:false,reason:'ARCHIVE_SOURCE_MISSING'};
   // Repair an outbox write interrupted AFTER central commit. Exact scope and
   // source ETag are re-established from the trusted strong store, not client.
   const pending=await Queue.read(store,current.data);
   if(!pending||pending.data.source_etag!==current.etag){
    const queued=await Queue.queue(store,current.data,current.etag);
    if(!queued.ok)return{ok:false,reason:queued.reason};
   }
   return publisher.publish(ref);
  }
 });
}
module.exports=Object.freeze({VERSION,create});
