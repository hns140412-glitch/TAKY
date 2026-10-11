'use strict';
const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs').promises;
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {LocalCharacterObjectStore}=require('./local-character-object-store.js');
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'taky-char-store-'));let server;
 try{
  const store=await new LocalCharacterObjectStore(root,{publicBaseUrl:'http://127.0.0.1:0'}).init();
  server=http.createServer(async(req,res)=>{if(await store.handleHttp(req,res))return;res.writeHead(404);res.end()});
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
  store.publicBaseUrl='http://127.0.0.1:'+server.address().port;
  const bytes=Buffer.from('character-master-binary');const sha=crypto.createHash('sha256').update(bytes).digest('hex');
  const ticket=await store.createUploadTicket({asset_ref:'taky-character:F1:M1:C1:v1',content_type:'image/webp',byte_size:bytes.length,sha256:sha});
  let resp=await fetch(ticket.upload_url,{method:'PUT',body:bytes});assert.equal(resp.status,204);
  const commit=await store.commitUpload({asset_ref:'taky-character:F1:M1:C1:v1',upload_id:ticket.upload_id,sha256:sha});assert.equal(commit.ok,true);
  const read=await store.createReadTicket({asset_ref:'taky-character:F1:M1:C1:v1'});resp=await fetch(read.read_url);assert.equal(resp.status,200);assert.deepEqual(Buffer.from(await resp.arrayBuffer()),bytes);
  console.log('LOCAL_CHARACTER_OBJECT_STORE_PASS: expiring upload/read tickets, SHA verified commit, private no-store read');
 }finally{if(server)await new Promise(r=>server.close(r));await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exit(1)});
