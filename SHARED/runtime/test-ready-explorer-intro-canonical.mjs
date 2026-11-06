import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {extname,resolve,sep} from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const root=resolve('D:/Git PWA/Ready & Set'),port=40984;
const types={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8',
 '.css':'text/css','.wav':'audio/wav','.mp3':'audio/mpeg','.png':'image/png','.svg':'image/svg+xml'};
const server=createServer((req,res)=>{
  let p;try{p=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html'))}
  catch{res.writeHead(400).end();return}
  if(!p.startsWith(root+sep)||!existsSync(p)){res.writeHead(404).end();return}
  res.writeHead(200,{'Content-Type':types[extname(p).toLowerCase()]||'application/octet-stream','Cache-Control':'no-store'});
  createReadStream(p).pipe(res);
});
await new Promise((ok,bad)=>server.once('error',bad).listen(port,'127.0.0.1',ok));
let browser,context;
const report={status:'OPEN',mode:'REAL_READY_APP_BROWSER',steps:[],page_errors:[]};
const record=x=>{const safe=JSON.parse(JSON.stringify(x,(k,v)=>k==='sourcePhoto'&&typeof v==='string'&&v.startsWith('data:')?'[SYNTHETIC_QA_IMAGE]':v));report.steps.push(safe);console.log('STEP',JSON.stringify(safe))};
try{
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
   args:['--autoplay-policy=no-user-gesture-required']});
 context=await browser.newContext({serviceWorkers:'block',viewport:{width:870,height:890}});
 await context.addInitScript(()=>{
  const now=new Date().toISOString();
  const fromMode=!!window.__qaForceMode || new URL(location.href).searchParams.get('qa_full_onboarding')==='1';
  const person={schemaVersion:6,status:fromMode?'UNSET':'CHARACTER_DEFERRED',onboardingStep:fromMode?'MODE':'EXPLORER',
   setupMode:'GUARDIAN_FOR_CHILD',operator:{role:'GUARDIAN',name:'QA'},userId:'QA_FAMILY',
   memberId:'QA_CHILD',legalName:'테스트',nickname:'탐험가',familyRole:'CHILD',
   birthDate:'2015-03-03',schoolStage:'E2',characterSetupState:fromMode?'NOT_STARTED':'DEFERRED_NO_COST',
   explorerId:null,journeyTheme:null,sourcePhoto:'',createdAt:now,updatedAt:now};
  localStorage.setItem('readyset_identity_v1',JSON.stringify(person));
  localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify({state:{relation:{main_character_id:null,members:{}}},updated_at:now}));
 });
 const page=await context.newPage();
 if(process.env.READY_QA_STRIP_APP_BOOT==='1'){
   await page.route('**/*.js*',route=>{
     const pathname=new URL(route.request().url()).pathname;
     const allowed=(process.env.READY_QA_ALLOW_EXTRA||'').split(',').filter(Boolean);
     if(pathname.startsWith('/explorer-crew-voice/')||pathname.includes('/ready-onboarding-identity-v1.js')||
       allowed.some(name=>pathname.includes('/'+name)))return route.continue();
     return route.fulfill({status:200,contentType:'application/javascript',body:'/* isolated Ready boot dependency */'});
   });
 }
 page.setDefaultTimeout(6000);
 page.on('pageerror',e=>report.page_errors.push(String(e)));
 console.log('START_READY');
 const requestPath=process.env.READY_QA_BEGIN_AT_MODE==='1'?'index.html?qa_full_onboarding=1':'index.html';
 await page.goto('http://127.0.0.1:'+port+'/'+requestPath,{waitUntil:'domcontentloaded',timeout:14000});
 if(process.env.READY_QA_BEGIN_AT_MODE==='1'){
   await page.locator('#guardianMode').click({timeout:6000});console.log('MODE_TO_PROFILE');
   await page.locator('#n').fill('테스트');
   await page.locator('#nn').fill('탐험가');
   await page.locator('#bd').fill('2015-03-03');
   await page.locator('#sg').selectOption('E2');
   await page.locator('#f button').click({timeout:6000});console.log('PROFILE_FORM_SUBMITTED');
   await page.waitForFunction(()=>window.ReadyIdentityV1?.get()?.onboardingStep==='PHOTO',null,{timeout:6000});console.log('PHOTO_SCREEN');
   await page.evaluate(async()=>{
     const canvas=document.createElement('canvas');canvas.width=40;canvas.height=40;
     canvas.getContext('2d').fillRect(0,0,40,40);
     const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
     const dt=new DataTransfer();dt.items.add(new File([blob],'qa.png',{type:'image/png'}));
     const el=document.querySelector('#gal');el.files=dt.files;
     el.dispatchEvent(new Event('change',{bubbles:true}));
   });
   await page.waitForFunction(()=>!!document.querySelector('#next')&&!document.querySelector('#next').disabled,null,{timeout:6000});console.log('PHOTO_READY');
   await page.locator('#next').click({timeout:6000});
   await page.waitForFunction(()=>window.ReadyIdentityV1?.get()?.onboardingStep==='CHARACTER',null,{timeout:6000});console.log('CHARACTER_SCREEN');
   await page.waitForFunction(()=>!!document.getElementById('rcDeferCharacter'),null,{timeout:6000});console.log('DEFER_BUTTON_READY');
   await page.locator('#rcDeferCharacter').click({timeout:6000});
   record({phase:'MODE_PROFILE_PHOTO_CHARACTER_DEFERRED',state:await page.evaluate(()=>window.ReadyIdentityV1.get().onboardingStep)});
 }
 await page.waitForFunction(()=>window.ReadyExplorerIntroCanonicalV1?.snapshot()?.state==='EXPLORER',null,{timeout:9000});
 record(await page.evaluate(()=>({phase:'EXPLORER_LOADED',count:document.querySelectorAll('[data-rc-crew]').length,
  state:window.ReadyIdentityV1?.get?.().onboardingStep, signature_count:window.ReadyExplorerIntroCanonicalV1.snapshot().signature_count})));
 // Real pixel click; read bounds and then click.
 async function touch(selector){
  const point=await page.evaluate(sel=>{const a=document.querySelector(sel);if(!a)throw Error('ELEMENT_MISSING:'+sel);
   const r=a.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}},selector);
  await page.mouse.click(point.x,point.y);
 }
 await touch('[data-rc-crew="dubi"]');
 await page.waitForFunction(()=>window.ReadyExplorerIntroEvidence?.last_audio_status==='PLAYING_STARTED',null,{timeout:11000});
 record(await page.evaluate(()=>({phase:'DUBI_AUDIO',event:window.ReadyExplorerIntroCanonicalV1.snapshot(),
  bubble:document.querySelector('[data-rc-quote]')?.textContent,
  actor:document.querySelector('[data-rc-who]')?.textContent})));
 await touch('[data-rc-crew="lori"]');
 await page.waitForFunction(()=>window.ReadyExplorerIntroEvidence?.last_character_id==='lori' &&
    window.ReadyExplorerIntroEvidence?.last_audio_status==='PLAYING_STARTED',null,{timeout:11000});
 record(await page.evaluate(()=>({phase:'LORI_AUDIO',actor:document.querySelector('[data-rc-who]')?.textContent,
  bubble:document.querySelector('[data-rc-quote]')?.textContent,
  key:window.ReadyExplorerIntroEvidence.last_key})));
 if(!(await page.locator('#rcConfirmEncounter').isDisabled()))throw Error('CORE6_FIRST_MEET_GATE_NOT_ENFORCED');
 for(const id of ['ink','nova','take','zero'])await touch('[data-rc-crew="'+id+'"]');
 await touch('[data-rc-crew="lori"]');
 await page.waitForFunction(()=>!document.querySelector('#rcConfirmEncounter')?.disabled,null,{timeout:9000});
 await touch('#rcConfirmEncounter');
 await page.waitForFunction(()=>['THEME','CREW_SELECT'].includes(window.ReadyIdentityV1?.get?.().onboardingStep),null,{timeout:7000});
 if((await page.evaluate(()=>window.ReadyIdentityV1.get().onboardingStep))==='CREW_SELECT'){
   for(const id of ['dubi','ink','nova','take'])await page.locator('[data-rfj-crew="'+id+'"]').click();
   await page.locator('#rfjNext').click();
 }
 await page.waitForFunction(()=>document.querySelector('[data-rc-screen="THEME"]'),null,{timeout:7000});
 record(await page.evaluate(()=>({phase:'THEME',identity:window.ReadyIdentityV1.get(),
  previous_main:JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1')).state.relation.main_character_id})));
 await touch('[data-rc-theme="TODAYS_ISLAND"]');
 await touch('#rcFinish');
 if((await page.evaluate(()=>window.ReadyIdentityV1.get().onboardingStep))==='PACK_BAG'){
   await page.locator('[data-rfj-gear="map"]').click();await page.locator('#rfjNext').click();
   await page.locator('[data-rfj-route="SAIL"]').click();await page.locator('#rfjNext').click();
   await page.locator('[data-rfj-step="ISLAND_FIRST_SIGHT"] #rfjNext').click();
   await page.locator('#rfjIslandName').fill('브라우저섬');await page.locator('#rfjNext').click();
   await page.locator('[data-rfj-step="BASECAMP_DISCOVERY"] #rfjNext').click();
   await page.locator('#rfjBasecampName').fill('브라우저캠프');await page.locator('#rfjNext').click();
   await page.locator('[data-rfj-step="BASECAMP_ARRIVAL"] #rfjNext').click();
 }
 await page.waitForFunction(()=>window.ReadyIdentityV1?.isReady?.(),null,{timeout:9000});
 record(await page.evaluate(()=>({phase:'COMPLETED',profile:window.ReadyIdentityV1.get(),
  main:JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1')).state.relation.main_character_id})));
 const steps=report.steps;
 const a=steps.find(x=>x.phase==='EXPLORER_LOADED');
 const b=steps.find(x=>x.phase==='DUBI_AUDIO');
 const c=steps.find(x=>x.phase==='LORI_AUDIO');
 const d=steps.find(x=>x.phase==='THEME');
 const e=steps.find(x=>x.phase==='COMPLETED');
 report.status=a?.count===6&&a?.signature_count===6&&
  b?.event?.last_key==='MAIN_CREW:dubi:SIGNATURE'&&
  c?.key==='MAIN_CREW:lori:SIGNATURE'&&
  d?.identity?.explorerId==='lori'&&d?.previous_main===null&&
  e?.profile?.journeyTheme==='TODAYS_ISLAND'&&e?.main===null?'PASS_FIRST_ENCOUNTER_TO_READY':'FAIL_ASSERTIONS';
}catch(error){report.error=String(error);report.status='OPEN_BROWSER_ERROR'}
finally{
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/READY_INTRO_CANONICAL_CORE6_BROWSER_QA_20261017.json',
  JSON.stringify(report,null,2));
 console.log('QA',report.status,report.error||'');
 if(context)await Promise.race([context.close().catch(()=>{}),new Promise(r=>setTimeout(r,1500))]);
 if(browser)await Promise.race([browser.close().catch(()=>{}),new Promise(r=>setTimeout(r,1500))]);
 server.closeAllConnections?.();server.close();
}
if(!report.status.startsWith('PASS_'))process.exitCode=2;
