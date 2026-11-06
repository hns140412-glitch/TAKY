'use strict';
const assert=require('node:assert/strict');
const A=require('./family-character-asset-http-endpoint.js');
const token='abcdefghijklmnop';
const verify=async t=>{assert.equal(t,token);return{authenticated:true,principal_id:'P1',families:[{family_id:'F1',authorized_member_ids:['M1']}]}};
const uploads=new Map();
const objectStore={
 async createUploadTicket(x){uploads.set('U1',{...x,committed:false});return{upload_id:'U1',upload_url:'https://upload.example.test/U1',expires_at:'2026-09-30T10:05:00Z'}},
 async commitUpload({asset_ref,upload_id,sha256}){const row=uploads.get(upload_id);assert.equal(row.asset_ref,asset_ref);row.committed=true;row.sha256=sha256;return{ok:true,sha256,etag:'E1'}},
 async createReadTicket({asset_ref}){const row=[...uploads.values()].find(x=>x.asset_ref===asset_ref&&x.committed);return row?{read_url:'https://read.example.test/r',expires_at:'2026-09-30T10:05:00Z'}:null}
};
const req=body=>({method:'POST',path:A.ENDPOINT,headers:{'content-type':'application/json',authorization:'Bearer '+token},body:JSON.stringify(body)});
(async()=>{
 const ep=A.create({verifyBearerToken:verify,objectStore});
 const meta={action:'CREATE_UPLOAD',family_id:'F1',member_id:'M1',character_id:'C1',content_type:'image/webp',byte_size:1024,sha256:'a'.repeat(64),asset_version:'v1'};
 let r=await ep.handle(req(meta)),b=JSON.parse(r.body);assert.equal(r.status,200);assert.ok(b.asset_ref.startsWith('taky-character:'));assert.equal(b.upload_id,'U1');
 r=await ep.handle(req({action:'COMMIT_UPLOAD',family_id:'F1',member_id:'M1',character_id:'C1',asset_ref:b.asset_ref,upload_id:'U1',sha256:'a'.repeat(64)}));assert.equal(r.status,200);
 r=await ep.handle(req({action:'RESOLVE_READ',family_id:'F1',member_id:'M1',character_id:'C1',asset_ref:b.asset_ref}));b=JSON.parse(r.body);assert.equal(r.status,200);assert.ok(b.read_url.startsWith('https://read.example.test/'));
 r=await ep.handle(req({...meta,member_id:'OTHER'}));assert.equal(r.status,403);
 // An authorized scope must not be usable to read/commit an asset_ref of ANOTHER family/member/character.
 const victim='taky-character:F2:M9:C1:v1';uploads.set('U9',{asset_ref:victim,committed:true});
 r=await ep.handle(req({action:'RESOLVE_READ',family_id:'F1',member_id:'M1',character_id:'C1',asset_ref:victim}));assert.equal(r.status,403);assert.equal(JSON.parse(r.body).reason,'ASSET_REF_SCOPE_MISMATCH');
 r=await ep.handle(req({action:'COMMIT_UPLOAD',family_id:'F1',member_id:'M1',character_id:'C1',asset_ref:victim,upload_id:'U9',sha256:'a'.repeat(64)}));assert.equal(r.status,403);
 r=await ep.handle(req({action:'RESOLVE_READ',family_id:'F1',member_id:'M1',character_id:'C2',asset_ref:'taky-character:F1:M1:C1:v1'}));assert.equal(r.status,403);
 r=await ep.handle(req({action:'RESOLVE_READ',family_id:'F1',member_id:'M1',character_id:'C1',asset_ref:'taky-character:F1:M10:C1:v1'}));assert.equal(r.status,403);
 console.log('FAMILY_CHARACTER_ASSET_HTTP_PASS: authenticated scope, bounded image upload, commit verification, signed read, asset_ref bound to scope');
})().catch(e=>{console.error(e);process.exit(1)});
