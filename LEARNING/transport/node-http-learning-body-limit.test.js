'use strict';
const assert=require('node:assert/strict');
const http=require('node:http');
const Bridge=require('./node-http-learning-bridge.js');
(async()=>{
 const sizes=[];
 const endpoint={handle:async req=>({status:200,headers:{},body:JSON.stringify({ok:true,kind:'evidence',bytes:Buffer.byteLength(req.body||'')})})};
 const userDataEndpoint={handle:async req=>{
  const n=Buffer.byteLength(req.body||'');sizes.push(n);
  return{status:200,headers:{},body:JSON.stringify({ok:true,kind:'family',bytes:n})};
 }};
 const server=http.createServer(Bridge.createHandler({endpoint,userDataEndpoint,allowedOrigins:[]}));
 await new Promise((resolve,reject)=>server.listen(0,'127.0.0.1',err=>err?reject(err):resolve()));
 try{
  const base='http://127.0.0.1:'+server.address().port;
  async function send(path,size){
   const body=JSON.stringify({data:'x'.repeat(size)});
   const res=await fetch(base+path,{method:'POST',headers:{'content-type':'application/json'},body});
   return{status:res.status,data:await res.json()};
  }
  const family=await send('/api/family/user-data',100000);
  assert.equal(family.status,200);
  assert(family.data.bytes>65536&&family.data.bytes<262144);
  const evidence=await send('/api/learning/evidence',100000);
  assert.equal(evidence.status,413);
  const tooLarge=await send('/api/family/user-data',270000);
  assert.equal(tooLarge.status,413);
  assert.deepEqual(sizes.length,1);
  console.log('CENTRAL_HTTP_ROUTE_SPECIFIC_BODY_LIMIT_PASS',JSON.stringify({
   family_over_64k_accepted:true,learning_evidence_limit_preserved:true,
   family_over_256k_rejected:true,external_network:false
  }));
 }finally{await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1});
