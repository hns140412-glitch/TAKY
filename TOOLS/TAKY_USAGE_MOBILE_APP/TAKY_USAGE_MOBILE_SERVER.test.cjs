// Local isolated regression for Apps Script read-only on-demand and offline fallback.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'TAKY_USAGE_MOBILE_SERVER.gs'),'utf8');
const key='a'.repeat(64),baseUrl='https://testbridge.trycloudflare.com';
const cached={schema:'TAKY_USAGE_MOBILE_PROJECTION_V1',exportedAt:new Date(Date.now()-3600000).toISOString(),
  bridge:{baseUrl,accessKey:key},providers:[{name:'Claude Code',fresh:false}]};
const fresh={schema:cached.schema,exportedAt:new Date().toISOString(),providers:[{name:'Claude Code',fresh:true}]};
let fetchCount=0;
const context={DriveApp:{getFileById:()=>({getBlob:()=>({getDataAsString:()=>JSON.stringify(cached)})})},
  UrlFetchApp:{fetch(url,options){
    fetchCount++;
    assert.equal(url,baseUrl+'/api/usage/mobile');
    assert.equal(options.headers['X-TAKY-Usage-Key'],key);
    assert.equal(options.followRedirects,false);
    return{getResponseCode:()=>200,getContentText:()=>JSON.stringify({ok:true,data:fresh,refreshed:true})};
  }}};
vm.runInNewContext(source,context);
const online=context.loadUsage();
assert.equal(online.source,'LIVE_PC');
assert.equal(online.synchronized,true);
assert.equal(online.liveRefresh,true);
assert.equal(fetchCount,1);
assert.equal(Object.hasOwn(online.data,'bridge'),false);
context.UrlFetchApp.fetch=()=>{throw new Error('PC_OFFLINE')};
const offline=context.loadUsage();
assert.equal(offline.source,'CACHED_DRIVE');
assert.equal(offline.pcReachable,false);
assert.equal(offline.synchronized,false);
assert.equal(Object.hasOwn(offline.data,'bridge'),false);
console.log('APP_SCRIPT_ONDEMAND_AND_OFFLINE_PASS');
