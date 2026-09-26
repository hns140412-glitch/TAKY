'use strict';
const fs=require('node:fs');
const fsp=fs.promises;
const path=require('node:path');
const crypto=require('node:crypto');

const VERSION='TAKY_LOCAL_JSON_STRONG_STORE_V1';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const digest=v=>crypto.createHash('sha256').update(String(v)).digest('hex');

class LocalJsonStrongStore{
  constructor(root,{lock_retry_ms=10,lock_attempts=200}={}){
    this.root=path.resolve(String(root));
    this.lock_retry_ms=Math.max(1,Number(lock_retry_ms)||10);
    this.lock_attempts=Math.max(1,Number(lock_attempts)||200);
  }
  async init(){await fsp.mkdir(this.root,{recursive:true});return this;}
  _paths(key){
    const id=digest(key);
    return {
      data:path.join(this.root,id+'.json'),
      lock:path.join(this.root,id+'.lock')
    };
  }
  async _readCurrent(key){
    const p=this._paths(key).data;
    try{
      const text=await fsp.readFile(p,'utf8');
      const parsed=JSON.parse(text);
      if(parsed.key!==key)throw new Error('LOCAL_STORE_KEY_HASH_COLLISION');
      return {exists:true,data:parsed.data,etag:digest(text)};
    }catch(e){
      if(e&&e.code==='ENOENT')return {exists:false,data:null,etag:null};
      throw e;
    }
  }
  async getWithMetadata(key,opts={}){
    const cur=await this._readCurrent(key);
    if(!cur.exists)return null;
    return {data:cur.data,etag:cur.etag,consistency:'strong',type:opts.type||'json'};
  }
  async _acquire(lock){
    for(let i=0;i<this.lock_attempts;i++){
      try{return await fsp.open(lock,'wx');}
      catch(e){if(!e||e.code!=='EEXIST')throw e; await sleep(this.lock_retry_ms);}
    }
    throw new Error('LOCAL_STORE_LOCK_TIMEOUT');
  }
  async setJSON(key,value,opts={}){
    await this.init();
    const p=this._paths(key);
    const lock=await this._acquire(p.lock);
    try{
      const cur=await this._readCurrent(key);
      if(opts.onlyIfNew&&cur.exists)return {modified:false,etag:cur.etag};
      if(opts.onlyIfMatch&&cur.etag!==opts.onlyIfMatch)return {modified:false,etag:cur.etag};
      const payload=JSON.stringify({store_version:VERSION,key,data:value});
      const tmp=p.data+'.tmp.'+process.pid+'.'+Date.now();
      await fsp.writeFile(tmp,payload,'utf8');
      await fsp.rename(tmp,p.data);
      return {modified:true,etag:digest(payload)};
    }finally{
      await lock.close().catch(()=>{});
      await fsp.unlink(p.lock).catch(()=>{});
    }
  }
}
module.exports=Object.freeze({VERSION,LocalJsonStrongStore});
