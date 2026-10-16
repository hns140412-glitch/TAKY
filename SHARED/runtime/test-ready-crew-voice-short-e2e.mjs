import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {resolve,sep,extname} from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const root=resolve('D:/Git PWA/Ready & Set'),port=4995;
const server=createServer((req,res)=>{
 let file;try{file=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html'))}catch{res.writeHead(400).end();return}
 if(!file.startsWith(root+sep)||!existsSync(file)){res.writeHead(404).end();return}
 res.writeHead(200,{'Content-Type':{'.html':'text/html','.js':'application/javascript','.wav':'audio/wav','.png':'image/png','.css':'text/css'}[extname(file).toLowerCase()]||'application/octet-stream'});
 createReadStream(file).pipe(res);
});
await new Promise(r=>server.listen(port,'127.0.0.1',r));
let browser,ctx,report={status:'OPEN',evidence:null};
const killer=setTimeout(()=>{console.log('READY_E2E_HARD_WATCHDOG');process.exit(4)},19000);
try{
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--autoplay-policy=no-user-gesture-required']});
 ctx=await browser.newContext({serviceWorkers:'block',viewport:{width:900,height:850}});
 await ctx.addInitScript(()=>{
  const now=new Date().toISOString();
  const profile={schemaVersion:6,status:'READY',onboardingStep:'DONE',setupMode:'GUARDIAN_FOR_CHILD',
   operator:{role:'GUARDIAN',name:'QA_PARENT'},userId:'QA_PARENT',memberId:'QA_CHILD',
   legalName:'테스트',nickname:'테스트',familyRole:'CHILD',birthDate:'2015-05-04',
   schoolStage:'E3',characterVisualId:'guide-08',characterSetupState:'CONFIRMED',
   explorerId:'guide-08',explorerName:'벨로',journeyTheme:'CAMP',createdAt:now,updatedAt:now};
  localStorage.setItem('readyset_identity_v1',JSON.stringify(profile));
  localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify({state:{relation:{
   main_character_id:'guide-08',members:{'guide-08':{relation_state:'MAIN_COMPANION',affinity:2}}
  }},updated_at:now}));
 });
 const page=await ctx.newPage();
 const pageErrors=[];page.on('pageerror',e=>pageErrors.push(String(e).slice(0,170)));
 await page.goto('http://127.0.0.1:'+port+'/index.html',{waitUntil:'domcontentloaded',timeout:10000});
 await page.waitForFunction(()=>window.TakyCrewAudioAppEvidence?.status==='APP_EVENT_CONSUMER_ATTACHED',null,{timeout:4500});
 const before=await page.evaluate(()=>({
  ready:window.ReadyIdentityV1?.isReady?.(),status:window.TakyCrewAudioAppEvidence?.status,
  button:document.getElementById('takyCrewVoiceBtn')?.outerHTML.slice(0,120),
  companion:JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1')).state.relation.main_character_id,
  voiceEngine:!!window.TakyExplorerCrewTtsMockSwitch
 }));
 console.log('READY_BEFORE '+JSON.stringify(before));
 if(!before.ready||!before.button||!before.voiceEngine)throw Error('NOT_READY');
 // Schedule a genuine DOM click from inside browser; do not block CDP command on app handler.
 const clickScheduled=await page.evaluate(()=>{setTimeout(()=>{
  const b=document.getElementById('takyCrewVoiceBtn');
  b?.click();
 },20);return true;});
 console.log('READY_CLICK_SCHEDULED '+clickScheduled);
 await new Promise(r=>setTimeout(r,1900));
 const after=await Promise.race([
  page.evaluate(()=>({voice:window.TakyCrewAudioAppEvidence,button:document.getElementById('takyCrewVoiceBtn')?.dataset})),
  new Promise(r=>setTimeout(()=>r({poll_timeout:true}),1700))
 ]);
 report={status:after?.voice?.last_result?.status==='PLAYING_STARTED'?'PASS_ACTUAL_UI_CLICK_MEDIA_PLAYING':'OPEN',
  before,after,errors:pageErrors};
 console.log('READY_RESULT '+JSON.stringify(report).slice(0,2100));
}catch(error){report.error=String(error);console.log('READY_ERROR '+report.error)}
finally{
 clearTimeout(killer);
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_READY_SHORT_UI_E2E_20261013.json',JSON.stringify(report,null,2));
 await Promise.race([ctx?.close().catch(()=>{}),new Promise(r=>setTimeout(r,950))]);
 await Promise.race([browser?.close().catch(()=>{}),new Promise(r=>setTimeout(r,1400))]);
 server.closeAllConnections?.();server.close();
}
if(!report.status.startsWith('PASS'))process.exitCode=2;
