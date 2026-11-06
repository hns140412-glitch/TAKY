'use strict';

/**
 * Store conformance probe for an OPERATOR-AUTHORIZED disposable validation
 * namespace only. It does not choose a vendor, run automatically, or certify
 * crash durability, encryption at rest, backup/restore or production costs.
 * One concurrent CAS winner is required; a store with last-write-wins cannot
 * back verified Learning Engine ACKs.
 */
const VERSION='TAKY_CENTRAL_STRONG_STORE_CONFORMANCE_V1';
const validKey=k=>typeof k==='string'&&
 /^validation\/[A-Za-z0-9._-]{8,128}$/.test(k);

async function probe({store,key,parallel=8}={}){
 if(!store||typeof store.getWithMetadata!=='function'||
    typeof store.setJSON!=='function')throw Error('STRONG_STORE_INTERFACE_REQUIRED');
 if(!validKey(key))throw Error('DISPOSABLE_VALIDATION_KEY_REQUIRED');
 if(!Number.isInteger(parallel)||parallel<2||parallel>32)
   throw Error('BOUNDED_PARALLEL_PROBE_REQUIRED');
 const get=()=>store.getWithMetadata(key,{type:'json',consistency:'strong'});
 if(await get())throw Error('VALIDATION_KEY_MUST_BE_NEW');
 const first=await store.setJSON(key,{probe_version:VERSION,revision:0},{onlyIfNew:true});
 if(first?.modified!==true||!first.etag)throw Error('CREATE_ETAG_UNCONFIRMED');
 const read=await get();
 if(!read||read.consistency!=='strong'||read.etag!==first.etag||
    read.data?.probe_version!==VERSION||read.data.revision!==0)
   throw Error('CREATE_READBACK_NOT_STRONG');
 const attempts=await Promise.all(Array.from({length:parallel},(_,i)=>
   store.setJSON(key,{probe_version:VERSION,revision:i+1},
     {onlyIfMatch:first.etag})));
 const winners=attempts.map((r,i)=>({r,i})).filter(x=>x.r?.modified===true);
 if(winners.length!==1||!winners[0].r.etag||
    attempts.some(x=>typeof x?.modified!=='boolean'))
   throw Error('ATOMIC_COMPARE_AND_SWAP_VIOLATED');
 const after=await get();
 if(!after||after.consistency!=='strong'||
    after.etag!==winners[0].r.etag||
    after.data?.revision!==winners[0].i+1)
   throw Error('CAS_WINNER_READBACK_INVALID');
 const stale=await store.setJSON(key,{probe_version:VERSION,revision:999},
   {onlyIfMatch:first.etag});
 const duplicate=await store.setJSON(key,{probe_version:VERSION,revision:999},
   {onlyIfNew:true});
 if(stale?.modified!==false||duplicate?.modified!==false)
   throw Error('STALE_OR_DUPLICATE_WRITE_ACCEPTED');
 const final=await get();
 if(!final||final.etag!==after.etag||
    final.data?.revision!==after.data.revision)
   throw Error('FAILED_WRITE_MUTATED_STATE');
 return Object.freeze({
   ok:true,version:VERSION,parallel_attempts:parallel,cas_winners:1,
   conditional_create:true,strong_readback:true,stale_write_rejected:true,
   final_etag_confirmed:true,operational_certification:false
 });
}
module.exports=Object.freeze({VERSION,probe});
