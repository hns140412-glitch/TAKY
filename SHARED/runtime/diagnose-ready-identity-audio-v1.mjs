import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {extname,resolve,sep} from 'node:path';
const require=createRequire(import.meta.url),{chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const home='D:/Git PWA/Ready & Set',port=4891;
const server=createServer((req,res)=>{
 let f;try{f=resolve(home,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html'))}
 catch{res.writeHead(400).end();return}
 if(!f.startsWith(resolve(home)+sep)||!existsSync(f)){res.writeHead(404).end();return}
 const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.wav':'audio/wav','.png':'image/png'};
 res.writeHead(200,{'Content-Type':types[extname(f).toLowerCase()]||'application/octet-stream'});
 createReadStream(f).pipe(res);
});
await new Promise(r=>server.listen(port,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
 args:['--autoplay-policy=no-user-gesture-required']});
const ctx=await browser.newContext({serviceWorkers:'block',viewport:{width:900,height:850}});
await ctx.addInitScript(()=>{
 const now=new Date().toISOString();
 const profile={schemaVersion:6,status:'READY',onboardingStep:'DONE',setupMode:'GUARDIAN_FOR_CHILD',
  operator:{role:'GUARDIAN',name:'QA_PARENT'},userId:'QA_PARENT',memberId:'QA_CHILD',
  legalName:'테스트',nickname:'테스트',familyRole:'CHILD',birthDate:'2015-05-04',
  schoolStage:'E5',characterVisualId:'guide-08',characterSetupState:'CONFIRMED',
  explorerId:'guide-08',explorerName:'벨로',journeyTheme:'CAMP',createdAt:now,updatedAt:now};
 localStorage.setItem('readyset_identity_v1',JSON.stringify(profile));
 localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify({state:{relation:{
  main_character_id:'guide-08',members:{'guide-08':{relation_state:'MAIN_COMPANION',affinity:3}}
 }},updated_at:now}));
});
let out={status:'UNKNOWN',profileBefore:null,profileAfter:null,errors:[]};
let page;
try{
 page=await ctx.newPage();
 page.on('pageerror',e=>out.errors.push(String(e).slice(0,250)));
 await page.goto('http://127.0.0.1:'+port+'/index.html',{waitUntil:'domcontentloaded',timeout:18000});
 await page.waitForFunction(()=>!!window.ReadyIdentityV1?.get?.(),null,{timeout:10000});
 await page.waitForFunction(()=>['READY','DEGRADED','ERROR'].includes(document.documentElement.dataset.readyBootState),null,{timeout:15000}).catch(()=>{});
 out=await page.evaluate(()=>({
  readyBootState:document.documentElement.dataset.readyBootState,
  profileBefore:JSON.parse(localStorage.getItem('readyset_identity_v1')||'null'),
  profileAfter:window.ReadyIdentityV1?.get?.(),
  isReady:window.ReadyIdentityV1?.isReady?.(),
  voiceStatus:window.TakyCrewAudioAppEvidence?.status||null,
  choiceStatus:!!window.TakyCrewSelectionPreviewController,
  audioModule:!!window.TakyExplorerCrewLearnerVoiceContext,
  launcher:document.getElementById('takyCrewSelectionLauncher')?.outerHTML.slice(0,250),
  bodyClass:document.body?.className,
  rootClass:document.documentElement?.className,
  readyFirstRun:document.getElementById('readyFirstRun')?.outerHTML.slice(0,140)||null
 }));
 out.status=out.isReady?'PROFILE_READY':'PROFILE_NOT_READY';
}catch(e){out.status='DIAG_ERROR';out.error=String(e)}
finally{
 console.log(JSON.stringify(out,null,2));
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/READY_LEARNER_IDENTITY_AUDIO_DIAG_20261013.json',JSON.stringify(out,null,2));
 await ctx.close().catch(()=>{});await browser.close().catch(()=>{});
 server.closeAllConnections?.();await new Promise(r=>server.close(r));
}
