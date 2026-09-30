'use strict';
const assert=require('node:assert/strict');
const P=require('./family-character-profile-http-endpoint.js');

function memoryStore(){
  let row=null,seq=0;
  return {
    async getWithMetadata(){return row?{data:structuredClone(row.data),etag:row.etag,consistency:'strong'}:null},
    async setJSON(key,value,opts={}){
      if(opts.onlyIfNew&&row)return {modified:false,etag:row.etag};
      if(opts.onlyIfMatch&&(!row||opts.onlyIfMatch!==row.etag))return {modified:false,etag:row?.etag||null};
      row={key,data:structuredClone(value),etag:'e'+(++seq)};
      return {modified:true,etag:row.etag};
    }
  };
}
const principal={authenticated:true,principal_id:'P1',families:[{family_id:'F1',authorized_member_ids:['M1']}]};
const verify=async token=>{assert.equal(token,'abcdefghijklmnop');return principal};
const request=(action,body={})=>({method:'POST',path:P.ENDPOINT,headers:{'content-type':'application/json',authorization:'Bearer abcdefghijklmnop'},body:JSON.stringify({action,family_id:'F1',member_id:'M1',...body})});

(async()=>{
 const store=memoryStore(),ep=P.create({verifyBearerToken:verify,store});
 let r=await ep.handle(request('GET'));let b=JSON.parse(r.body);assert.equal(r.status,200);assert.equal(b.found,false);
 const projection={member_id:'M1',character_id:'char_M1_v1',identity_version:1,master_asset_ref:'private://characters/M1/v1/master.webp',master_sha256:'a'.repeat(64),asset_version:'gen-v1',derivative_refs:{},status:'CONFIRMED',updated_at:'2026-09-30T10:00:00.000Z'};
 r=await ep.handle(request('PUBLISH',{projection}));b=JSON.parse(r.body);assert.equal(r.status,200);assert.equal(b.published,true);assert.ok(b.etag);
 r=await ep.handle(request('GET'));b=JSON.parse(r.body);assert.equal(b.projection.character_id,'char_M1_v1');assert.equal(b.projection.sourcePhoto,undefined);
 r=await ep.handle(request('PUBLISH',{projection:{...projection,identity_version:0,character_id:'old'}}));assert.equal(r.status,400);
 r=await ep.handle(request('PUBLISH',{projection:{...projection,identity_version:1,character_id:'collision'}}));assert.equal(r.status,409);
 r=await ep.handle({...request('GET'),body:JSON.stringify({action:'GET',family_id:'F1',member_id:'OTHER'})});assert.equal(r.status,403);
 console.log('FAMILY_CHARACTER_PROFILE_HTTP_PASS: authenticated member scope, strong store, no raw photo, monotonic identity version');
})().catch(e=>{console.error(e);process.exit(1)});
