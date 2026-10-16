'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const crypto=require('node:crypto');
const path=require('node:path');
const base=path.resolve(__dirname,'../..');
const apps=['Hide & Seek','Snap & Pop','Ready & Set'];
const client='taky-learning-evidence-client-v1.js';
const auth='taky-family-auth-runtime-v1.js';
const conf='taky-account-auth-config-v1.js';
const account='taky-google-account-auth-v1.js';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const reference=hash(path.join(__dirname,'../SHARED/runtime',client));
let authReference;
for(const name of apps){
 const root=path.join(base,name);
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
 for(const script of [client,auth,conf,account]){
   assert.ok(html.includes(script),name+': bootstrap missing '+script);
   assert.ok(fs.statSync(path.join(root,script)).isFile(),name+': missing file '+script);
 }
 assert.equal(hash(path.join(root,client)),reference,name+': learning client drift');
 const authHash=hash(path.join(root,auth));
 if(authReference)assert.equal(authHash,authReference,name+': auth runtime drift');
 authReference=authHash;
}
console.log('PASS: three-app learning evidence client and auth bootstrap parity');
