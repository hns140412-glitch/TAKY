import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {resolve,sep,extname} from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const root=resolve('D:/Git PWA/Ready & Set'),port=4991;
const server=createServer((req,res)=>{
 let p;try{p=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html'))}
 catch{res.writeHead(400).end();return}
 if(!p.startsWith(root+sep)||!existsSync(p)){res.writeHead(404).end();return}
 res.writeHead(200,{'Content-Type':{'.html':'text/html','.js':'application/javascript','.wav':'audio/wav','.css':'text/css','.png':'image/png','.svg':'image/svg+xml'}[extname(p).toLowerCase()]||'application/octet-stream'});
 createReadStream(p).pipe(res);
});
await new Promise(r=>server.listen(port,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
 args:['--autoplay-policy=no-user-gesture-required']});
const context=await browser.newContext({serviceWorkers:'block',viewport:{width:900,height:850}});
await context.addInitScript(()=>{
 const now=new Date().toISOString();
 const identity={schemaVersion:6,status:'READY',setupMode:'GUARDIAN_FOR_CHILD',onboardingStep:'DONE',
  operator:{role:'GUARDIAN',name:'QA_PARENT'},userId:'QA_PARENT',memberId:'QA_CHILD',legalName:'테스트',
  nickname:'테스트',familyRole:'CHILD',birthDate:'2015-05-04',schoolStage:'E5',
  characterVisualId:'guide-08',characterSetupState:'CONFIRMED',
  explorerId:'guide-08',explorerName:'벨로',journeyTheme:'CAMP',createdAt:now,updatedAt:now};
 localStorage.setItem('readyset_identity_v1',JSON.stringify(identity));
 localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify({state:{relation:{
  main_character_id:'guide-08',members:{'guide-08':{relation_state:'MAIN_COMPANION',affinity:2}}
 }},updated_at:now}));
 const OriginalAudio=window.Audio;
 window.Audio=function(src){
  const audio=new OriginalAudio(src);
  if(typeof src==='string'&&src.includes('explorer-crew')){
   audio.addEventListener('playing',()=>console.log('TAKY_QA_MEDIA_PLAYING '+src));
   audio.addEventListener('error',()=>console.log('TAKY_QA_MEDIA_ERROR '+src));
  }
  return audio;
 };
});
let report={status:'OPEN',messages:[],profile_ready:false,button_found:false};
const page=await context.newPage();
let resolveMedia;const heard=new Promise(r=>resolveMedia=r);
page.on('console',msg=>{
 const txt=msg.text();
 if(txt.startsWith('TAKY_QA_MEDIA_')){
  report.messages.push(txt);
  if(txt.startsWith('TAKY_QA_MEDIA_PLAYING'))resolveMedia({ok:true,event:txt});
  if(txt.startsWith('TAKY_QA_MEDIA_ERROR'))resolveMedia({ok:false,event:txt});
 }
});
try{
 await page.goto('http://127.0.0.1:'+port+'/index.html',{waitUntil:'domcontentloaded',timeout:14000});
 await page.waitForFunction(()=>window.TakyCrewAudioAppEvidence?.status==='APP_EVENT_CONSUMER_ATTACHED',null,{timeout:10000});
 const before=await page.evaluate(()=>({ready:window.ReadyIdentityV1?.isReady?.(),
  button:!!document.getElementById('takyCrewVoiceBtn'),
  buttonDisabled:document.getElementById('takyCrewVoiceBtn')?.disabled,
  source:window.TakyExplorerCrewLearnerVoiceContext?.resolve?.({app_id:'READY_SET',identityReady:window.ReadyIdentityV1?.isReady?.(),identity:window.ReadyIdentityV1?.get?.()})}));
 report.profile_ready=before.ready;report.button_found=before.button&&!before.buttonDisabled;report.source=before.source;
 if(!before.ready||!report.button_found)throw Error('NO_REAL_READY_IDENTITY_OR_BUTTON');
 await page.evaluate(()=>document.getElementById('takyCrewVoiceBtn').click());
 const outcome=await Promise.race([heard,new Promise(r=>setTimeout(()=>r({ok:false,event:'NODE_SIDE_MEDIA_TIMEOUT'}),11000))]);
 report.status=outcome.ok?'PASS_ACTUAL_READY_MEDIA_PLAYING':'OPEN_MEDIA_NOT_CONFIRMED';report.outcome=outcome;
}catch(e){report.status='OPEN';report.error=String(e);}
finally{
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_READY_MEDIA_INSTRUMENTATION_20261013.json',JSON.stringify(report,null,2));
 console.log(JSON.stringify(report,null,2));
 await Promise.race([context.close().catch(()=>{}),new Promise(r=>setTimeout(r,1000))]);
 await Promise.race([browser.close().catch(()=>{}),new Promise(r=>setTimeout(r,1500))]);
 server.closeAllConnections?.();server.close();
}
if(!report.status.startsWith('PASS'))process.exitCode=2;
