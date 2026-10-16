import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync} from 'node:fs';
import {resolve,extname,sep} from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const root='D:/Git PWA/Ready & Set',port=4693;
const server=createServer((req,res)=>{
 const u=new URL(req.url,'http://localhost');let target;
 try{target=resolve(root,'.'+decodeURIComponent(u.pathname).replace(/\/$/,'/index.html'))}catch{res.writeHead(400).end();return}
 if(!target.startsWith(resolve(root)+sep)||!existsSync(target)){res.writeHead(404).end();return}
 const ext=extname(target).toLowerCase();
 res.writeHead(200,{'Content-Type':{'.js':'application/javascript','.html':'text/html; charset=utf-8','.wav':'audio/wav','.css':'text/css'}[ext]||'application/octet-stream'});
 createReadStream(target).pipe(res);
});
await new Promise(r=>server.listen(port,'127.0.0.1',r));
const b=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--autoplay-policy=no-user-gesture-required']});
const c=await b.newContext({serviceWorkers:'block',viewport:{width:800,height:850}});
await c.addInitScript(()=>{
 const now=new Date().toISOString();
 localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify({state:{relation:{main_character_id:'dubi',members:{dubi:{relation_state:'MAIN_COMPANION'},lori:{relation_state:'COMPANION_AVAILABLE'},'guide-19':{relation_state:'KNOWN'}}}},updated_at:now}));
 localStorage.setItem('readyset_identity_v1',JSON.stringify({schemaVersion:6,status:'READY',onboardingStep:'DONE',setupMode:'GUARDIAN_FOR_CHILD',operator:{role:'GUARDIAN',name:'테스트'},userId:'QA_ONLY',memberId:'QA_CHILD',legalName:'테스트',nickname:'테스트',familyRole:'CHILD',birthDate:'2015-01-01',schoolStage:'E5',characterVisualId:null,characterSetupState:'DEFERRED_NO_COST',explorerId:'dubi',explorerName:'두비',journeyTheme:'CAMP',createdAt:now,updatedAt:now}));
});
const p=await c.newPage();
p.on('pageerror',e=>console.log('PAGE_ERROR',String(e).slice(0,200)));
await p.goto('http://127.0.0.1:'+port+'/index.html',{waitUntil:'domcontentloaded',timeout:13000});
await p.waitForFunction(()=>window.TakyCrewSelectionPreviewController?.snapshot(),{timeout:10000});
console.log('READY_READY',await p.evaluate(()=>window.ReadyIdentityV1?.isReady?.()));
await p.evaluate(()=>window.TakyCrewSelectionPreviewController.open());
console.log('DIALOGUE_OPENED',await p.evaluate(()=>{
 const e=document.querySelector('[data-taky-id=dubi]'),o=document.querySelector('.taky-pick-shade'),b=document.getElementById('takyCrewSelectionLauncher');
 const r=e.getBoundingClientRect();return {cards:document.querySelectorAll('[data-taky-id]').length,
 rect:r.toJSON(),card_display:getComputedStyle(e).display,overlay_z:getComputedStyle(o).zIndex,
 top_at_card:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.outerHTML.slice(0,200),
 launcher_top:document.elementFromPoint(720,675)?.outerHTML.slice(0,150),
 first_run:!!document.querySelector('#readyFirstRun'),first_run_hidden:document.querySelector('#readyFirstRun')?.hidden,
 app_state:window.TakyCrewAudioAppEvidence?.status};
}));
try{
 const point=await p.evaluate(()=>{const r=document.querySelector('[data-taky-id=dubi]').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}});
 console.log('CLICK_COORD',point);
 await p.mouse.click(point.x,point.y);
 console.log('CARD_MOUSE_CLICK_OK');
}catch(e){console.log('CARD_MOUSE_CLICK_FAIL',String(e).slice(0,550));}
await new Promise(r=>setTimeout(r,1800));
console.log('AFTER',await p.evaluate(()=>({selected:window.TakyCrewSelectionPreviewController.snapshot().selected,
 text:document.querySelector('[data-taky-speech]')?.textContent,
 tap_ids:window.TakyCrewSelectionPreviewController.snapshot().tap_ids,
 playing:window.TakyCrewSelectionPreviewController.snapshot().play_results})));
process.exit(0);