import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {extname,resolve,sep} from 'node:path';
const require=createRequire(import.meta.url),{chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const base=resolve('D:/Git PWA/Ready & Set'),port=40985;
const scripts=['data-registry','data-mock','data-approved','explorer-crew-dialogue-voice-bridge-v1',
 'explorer-crew-tts-mock-switch-v1','explorer-crew-selection-preview-v1','ready-explorer-intro-canonical-v1'];
const bootstrap="const state={schemaVersion:6,status:'CHARACTER_DEFERRED',onboardingStep:'EXPLORER',"+
"setupMode:'GUARDIAN_FOR_CHILD',userId:'QA_1',memberId:'QA_2',legalName:'모의',"+
"nickname:'탐험가',birthDate:'2015-04-05',schoolStage:'E2',characterSetupState:'DEFERRED_NO_COST',"+
"explorerId:null,journeyTheme:null};"+
"window.ReadyIdentityV1={get(){return {...state}},patch(p){Object.assign(state,p);return {...state}},"+
"isReady(){return state.status==='READY'},complete(p){Object.assign(state,p,{status:'READY',onboardingStep:'DONE'});return {...state}},"+
"render(){window.ReadyExplorerIntroCanonicalV1?.render()}};"+
"window.ReadyRoleContextV1={activateIdentityRole(){}};";
const html='<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body>'+
'<section id="readyFirstRun"></section><script>'+bootstrap+'</script>'+
scripts.map(name=>'<script src="/explorer-crew-voice/'+name+'.js"></script>').join('')+
'</body></html>';
const server=createServer((req,res)=>{
 const u=new URL(req.url,'http://localhost');
 if(u.pathname==='/__intro_isolated.html'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(html);return}
 let p;try{p=resolve(base,'.'+decodeURIComponent(u.pathname).replace(/\/$/,'/index.html'))}catch{res.writeHead(400).end();return}
 if(!p.startsWith(base+sep)||!existsSync(p)){res.writeHead(404).end();return}
 res.writeHead(200,{'Content-Type':{'.js':'application/javascript','.wav':'audio/wav','.png':'image/png'}[extname(p).toLowerCase()]||'application/octet-stream'});
 createReadStream(p).pipe(res);
});
await new Promise(r=>server.listen(port,'127.0.0.1',r));
let browser,context;
const result={status:'FAIL',steps:[],errors:[]};
try{
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--autoplay-policy=no-user-gesture-required']});
 context=await browser.newContext({serviceWorkers:'block',viewport:{width:760,height:850}});
 const page=await context.newPage();
 page.on('pageerror',e=>result.errors.push(String(e)));
 await page.goto('http://127.0.0.1:'+port+'/__intro_isolated.html',{waitUntil:'domcontentloaded',timeout:12000});
 await page.waitForFunction(()=>window.ReadyExplorerIntroEvidence?.state==='EXPLORER',null,{timeout:6000});
 result.steps.push({state:'loaded',count:await page.locator('[data-rc-crew]').count()});
 await page.locator('[data-rc-crew="dubi"]').click({timeout:6000});
 await page.waitForFunction(()=>window.ReadyExplorerIntroEvidence?.last_audio_status==='PLAYING_STARTED',null,{timeout:10000});
 result.steps.push(await page.evaluate(()=>({state:'dubi_playing',key:window.ReadyExplorerIntroEvidence.last_key,popup:document.querySelector('[data-rc-quote]')?.textContent})));
 await page.locator('[data-rc-crew="lori"]').click({timeout:6000});
 await page.waitForFunction(()=>window.ReadyExplorerIntroEvidence?.last_character_id==='lori'&&window.ReadyExplorerIntroEvidence?.last_audio_status==='PLAYING_STARTED',null,{timeout:10000});
 result.steps.push(await page.evaluate(()=>({state:'lori_playing',key:window.ReadyExplorerIntroEvidence.last_key})));
 await page.locator('#rcConfirmEncounter').click();
 await page.waitForFunction(()=>window.ReadyIdentityV1.get().onboardingStep==='THEME',null,{timeout:5000});
 await page.locator('[data-rc-theme="TODAYS_ISLAND"]').click();
 await page.locator('#rcFinish').click();
 result.steps.push(await page.evaluate(()=>({state:'ready',ready:window.ReadyIdentityV1.isReady(),explorer:window.ReadyIdentityV1.get().explorerId,world:window.ReadyIdentityV1.get().journeyTheme})));
 result.status=result.steps[0].count===6&&result.steps[1].key==='MAIN_CREW:dubi:SIGNATURE'&&result.steps[2].key==='MAIN_CREW:lori:SIGNATURE'&&result.steps[3].ready===true?'PASS_ISOLATED_AUDIO_AND_FIRST_RUN':'FAIL_CHECKS';
}catch(e){result.error=String(e)}
finally{
 console.log(JSON.stringify(result,null,2));
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/READY_CORE6_INTRO_ISOLATED_BROWSER_QA_20261013.json',JSON.stringify(result,null,2));
 if(context)await Promise.race([context.close().catch(()=>{}),new Promise(r=>setTimeout(r,1000))]);
 if(browser)await Promise.race([browser.close().catch(()=>{}),new Promise(r=>setTimeout(r,1000))]);
 server.closeAllConnections?.();server.close();
}
if(!result.status.startsWith('PASS_'))process.exitCode=2;
