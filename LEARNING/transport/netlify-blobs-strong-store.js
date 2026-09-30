'use strict';

const VERSION='TAKY_NETLIFY_BLOBS_STRONG_STORE_V1';
const clean=x=>typeof x==='string'?x.trim():'';

function create({
  getStore,
  store_name='taky-learning-evidence-v1',
  region=null
}={}){
  if(typeof getStore!=='function')throw Error('GET_STORE_REQUIRED');
  if(!clean(store_name))throw Error('STORE_NAME_REQUIRED');
  if(region!==null&&!clean(region))throw Error('REGION_INVALID');

  const args={name:store_name,consistency:'strong'};
  if(region)args.region=region;
  const inner=getStore(args);
  if(!inner||typeof inner.getWithMetadata!=='function'||typeof inner.setJSON!=='function')
    throw Error('NETLIFY_STRONG_STORE_INTERFACE_REQUIRED');

  return Object.freeze({
    version:VERSION,
    store_name,
    region:region||null,
    consistency:'strong',
    async getWithMetadata(key,opts={}){
      const entry=await inner.getWithMetadata(key,{...opts,type:opts.type||'json'});
      if(entry==null)return null;
      if(!entry||typeof entry!=='object'||Array.isArray(entry)||
         typeof entry.etag!=='string'||!entry.etag.trim()||
         !Object.prototype.hasOwnProperty.call(entry,'data'))
        throw Error('NETLIFY_STRONG_READ_METADATA_INVALID');
      return {...entry,consistency:'strong',type:opts.type||'json'};
    },
    async setJSON(key,value,opts={}){
      const result=await inner.setJSON(key,value,opts);
      if(!result||typeof result!=='object'||Array.isArray(result))
        throw Error('NETLIFY_STRONG_WRITE_RESULT_INVALID');
      if(result.modified===true&&
         (typeof result.etag!=='string'||!result.etag.trim()))
        throw Error('NETLIFY_STRONG_WRITE_ETAG_REQUIRED');
      return result;
    }
  });
}

module.exports=Object.freeze({VERSION,create});