'use strict';
const assert=require('node:assert/strict');
const Transport=require('./siezeall-drive-rest-transport.js');
const Archive=require('./family-user-data-siezeall-archive-publisher.js');
const leaf=Archive.ids.leaf;
const archiveId='u_'+ 'a'.repeat(48);
const metadata=new Map();
let bytes=Buffer.from('{"ciphertext_base64":"encrypted"}');
const folder={id:leaf,parents:[Archive.ids.platform],
 permissions:[{type:'user',role:'owner',emailAddress:'siezeall@gmail.com'}]};
metadata.set(leaf,folder);
let created=0, authCalls=0, httpCalls=0;
function response(status,json=null,raw=null){
 return {ok:status>=200&&status<300,status,json:async()=>json,arrayBuffer:async()=>raw};
}
async function fetchImpl(url,opts){
 httpCalls++;
 assert.equal(opts.headers.Authorization,'Bearer test-google-drive-token-12345');
 assert.equal(opts.redirect,'error');assert.equal(opts.cache,'no-store');
 const u=new URL(url);
 if(u.pathname.endsWith('/'+leaf)&&opts.method==='GET')return response(200,folder);
 if(u.pathname.endsWith('/files')&&opts.method==='GET'){
  assert(u.searchParams.get('q').includes('taky_archive_id'));
  assert(!u.searchParams.get('q').includes('name='));
  const file=[...metadata.values()].find(x=>x?.appProperties?.taky_archive_id===archiveId);
  return response(200,{files:file?[file]:[]});
 }
 if(u.hostname==='www.googleapis.com'&&u.pathname==='/upload/drive/v3/files'&&opts.method==='POST'){
  assert.equal(u.searchParams.get('uploadType'),'multipart');
  assert.match(opts.headers['Content-Type'],/^multipart\/related;/);
  const body=Buffer.from(opts.body);
  assert(body.includes(Buffer.from('taky_scope')));
  assert(body.includes(bytes));
  const match=opts.headers['Content-Type'].match(/boundary=(.+)$/);
  const separator=Buffer.from('\r\n--'+match[1]+'--\r\n');
  assert(body.subarray(body.length-separator.length).equals(separator));
  created++;
  const doc={
   id:'uploaded_12345678901',name:archiveId+'.encrypted.json',mimeType:'application/json',parents:[leaf],
   appProperties:{taky_archive_id:archiveId,taky_scope:'PRIVATE_USER_DATA_BACKUP'},
   permissions:folder.permissions
  };
  metadata.set(doc.id,doc);
  return response(200,doc);
 }
 if(u.pathname.endsWith('/uploaded_12345678901')){
  if(u.searchParams.get('alt')==='media')return response(200,null,bytes);
  return response(200,metadata.get('uploaded_12345678901'));
 }
 return response(404);
}
(async()=>{
 const t=Transport.create({getAccessToken:async()=>{authCalls++;return 'test-google-drive-token-12345'},fetchImpl});
 assert.equal((await t.getMetadata(leaf)).id,leaf);
 assert.equal(await t.findImmutable({folder_id:leaf,archive_id:archiveId}),null);
 const doc=await t.createImmutable({folder_id:leaf,archive_id:archiveId,
  name:archiveId+'.encrypted.json',mime_type:'application/json',bytes});
 assert.equal(doc.appProperties.taky_archive_id,archiveId);
 assert.equal(created,1);
 assert.equal((await t.findImmutable({folder_id:leaf,archive_id:archiveId})).id,doc.id);
 assert(Buffer.from(await t.readFileBytes(doc.id)).equals(bytes));
 assert.equal(authCalls,httpCalls);
 await assert.rejects(()=>t.createImmutable({folder_id:leaf,archive_id:archiveId,
   name:'danger.js',mime_type:'application/javascript',bytes}),/VALIDATION_FAILED/);
 const n=httpCalls;
 await assert.rejects(()=>t.getMetadata('https://drive.google.com/file/ABC'),/FILE_ID_INVALID/);
 assert.equal(httpCalls,n);
 const blocked=Transport.create({getAccessToken:async()=>'' ,fetchImpl});
 await assert.rejects(()=>blocked.getMetadata(leaf),/SERVER_BEARER_UNAVAILABLE/);
 console.log('SIEZEALL_DRIVE_REST_TRANSPORT_PASS',JSON.stringify({
  authorized_server_bearer_only:true,metadata_acl_readback:true,app_properties_lookup:true,
  multipart_encrypted_upload:true,byte_readback:true,unsafe_input_block:true,no_external_network:true
 }));
})().catch(e=>{console.error(e);process.exitCode=1});
