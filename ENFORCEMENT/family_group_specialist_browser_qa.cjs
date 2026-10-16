'use strict';
// Learner bots in separate browser contexts on real Hide/Snap frontends, local fixtures only.
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const work=path.resolve(__dirname,'../..'),out=path.resolve(__dirname,'../.local/family-qa/browser');
fs.mkdirSync(out,{recursive:true});
const scenarios=[
 {id:'A-L1',family:'SIM-A',app:'hide',port:45531,root:path.join(work,'Hide & Seek')},
 {id:'B-L1',family:'SIM-B',app:'snap',port:45532,root:path.join(work,'Snap & Pop')},
 {id:'A-L2',family:'SIM-A',app:'play',port:45533,root:path.join(work,'Play Camp','dist')}
];
function serve(s){
 const formats={html:'text/html',js:'text/javascript',mjs:'text/javascript',css:'text/css',json:'application/json',svg:'image/svg+xml',png:'image/png',jpg:'image/jpeg',mp3:'audio/mpeg',woff2:'font/woff2'};
 return http.createServer((req,res)=>{
   if(req.method!=='GET'){res.writeHead(405);return res.end();}
   let rel;
   try{rel=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname).replace(/^\/+/, '')||'index.html';}
   catch{res.writeHead(400);return res.end();}
   const file=path.resolve(s.root,rel);
   if(!file.startsWith(s.root+path.sep)||rel.split('/').some(n=>n.startsWith('.'))||
       !/\.(?:html|js|mjs|css|json|svg|png|jpe?g|webp|mp3|wav|woff2?|webmanifest|ico)$/.test(rel)||
       !fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
   res.writeHead(200,{'Cache-Control':'no-store','Content-Type':formats[path.extname(file).slice(1)]||'application/octet-stream'});
   fs.createReadStream(file).pipe(res);
 }).listen(s.port,'127.0.0.1');
}
const results=[];let browser;const servers=[];
async function bot(s){
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,serviceWorkers:'block'});
 await context.addInitScript(({id,family})=>{
   sessionStorage.setItem('__TAKY_QA_MEMBER',id);
   sessionStorage.setItem('__TAKY_QA_FAMILY',family);
 },{id:s.id,family:s.family});
 if(s.app==='play')await context.addInitScript(({id,family})=>{
   const profile={
     familyMemberId:id,displayName:'가상 학습자',presentationBand:'EARLY_EXPLORER',interests:[],
     boundary:{explorerId:'explorer-mock',islandId:'island-mock',basecampId:'basecamp-mock',activeCrewIds:['dubi']},
     intro:{stage:'MAIN_ISLAND_READY',selectedCrewIds:['dubi'],visualId:null,visualIdentity:null,packedItemIds:[],
       departureMode:'SAIL',islandName:'모의 섬',basecampName:'모의 캠프'},
     recentExperiences:[],creations:[]
   };
   localStorage.setItem('taky-play-camp-explorer-profile-v1:'+encodeURIComponent(id),JSON.stringify(profile));
   sessionStorage.setItem('play_camp_family_scope_session_v1',family);
 },{id:s.id,family:s.family});
 await context.route('**/*',route=>{
   const url=new URL(route.request().url());
   if(url.hostname!=='127.0.0.1'||url.port!==String(s.port))return route.abort();
   if(url.pathname.startsWith('/api/'))return route.fulfill({status:503,contentType:'application/json',body:'{"ok":false,"reason":"QA_NO_REAL_BACKEND"}'});
   return route.continue();
 });
 const page=await context.newPage(),events=[],errors=[];
 page.on('pageerror',e=>errors.push({source:'pageerror',message:e.message.slice(0,180)}));
 page.on('dialog',d=>d.dismiss());
 try{
  console.log('SPECIALIST_STEP '+s.app+' navigate');
  await page.goto('http://127.0.0.1:'+s.port+'/'+(s.app==='play'?'?child_id='+encodeURIComponent(s.id):''),{waitUntil:'domcontentloaded',timeout:7000});
  if(s.app==='hide'){
   await page.waitForFunction(()=>window.HideTermDecoderV1?.registerCards&&window.HideTermDecoderV1?.open,{timeout:6500});
   const registered=await page.evaluate(()=>{
     window.HideTermDecoderV1.registerCards([{
       id:'qa-apple',term:'apple',meaning:'사과',subject:'ENGLISH',
       components:[{text:'apple',meaning:'사과'}],conceptLinks:['과일']
     }],{replace:true,engineOwned:true,projection:{school_stage:'E5',subject:'ENGLISH',grade_context:{state:'RESOLVED',school_stage:'E5',base_band:'UPPER_ELEMENTARY',effective_band:'UPPER_ELEMENTARY',evidence_step:0}}});
     window.HideTermDecoderV1.open('TRACE');
     return window.HideTermDecoderV1.state;
   });
   events.push({action:'register-and-open-trace',state:registered});
   await page.locator('#termTraceReveal').click({timeout:2500});
   events.push({action:'trace-reveal',status:'PASS'});
   await page.locator('[data-trace-result="SELF_KNOWN"]').click({timeout:2500});
   events.push({action:'trace-answer',status:'PASS'});
  }else if(s.app==='snap'){
   await page.waitForSelector('#landmarks .landmark',{state:'visible',timeout:6500});
   await page.locator('#landmarks .landmark').first().click({timeout:2500});
   await page.waitForFunction(()=>!document.getElementById('selection')?.hidden,{timeout:4500});
   events.push({action:'select-landmark',status:'PASS'});
   await page.locator('#startBtn').click({timeout:2500});
   for(const word of ['처음 발견한 생각','두 번째 탐색 이유','내 표현으로 정리']){
     await page.locator('#answer').fill(word,{timeout:2500});
     await page.locator('#nextBtn').click({timeout:2500});
     events.push({action:'express-and-next',status:'PASS'});
   }
  }else{
    if(await page.locator('.main-island-ready').isVisible())await page.getByRole('button',{name:/수련 캠프 시작/}).click({timeout:2500});
    await page.waitForSelector('.camp-zone-button',{state:'visible',timeout:6500});
    const english=page.locator('.camp-zone-button').filter({hasText:'English'}).first();
    await english.click({timeout:2500});
    events.push({action:'select-english-zone',status:'PASS'});
    await page.waitForSelector('.english-sound-scene',{state:'visible',timeout:6500});
    const stones=page.locator('.phoneme-stone');
    if(await stones.count()<3)throw Error('PLAY_CAMP_PHONEME_STONES_MISSING');
    for(let i=0;i<3;i++)await stones.nth(i).click({timeout:2500});
    events.push({action:'blend-three-sounds',status:'PASS'});
    await page.locator('.english-blend').click({timeout:2500});
    events.push({action:'trigger-blend',status:'PASS'});
  }
  const scope=await page.evaluate(()=>({
    family:sessionStorage.getItem('__TAKY_QA_FAMILY'),member:sessionStorage.getItem('__TAKY_QA_MEMBER')
  }));
  if(scope.family!==s.family||scope.member!==s.id)throw Error('QA_BROWSER_SCOPE_ISOLATION_FAILED');
 }catch(e){errors.push({source:'browser',message:String(e.message).slice(0,350)});}
 if(errors.length){
  try{await page.screenshot({path:path.join(out,'specialist-'+s.app+'-failure.png'),timeout:2500});}catch{}
 }
 await context.close();
 return {actor:s.id,family:s.family,app:s.app,events,errors};
}
(async()=>{
 try{
  for(const s of scenarios){const server=serve(s);await new Promise((resolve,reject)=>{server.once('listening',resolve);server.once('error',reject)});servers.push(server);}
  browser=await chromium.launch({headless:true,channel:'chrome',timeout:15000});
  const rows=await Promise.all(scenarios.map(bot));results.push(...rows);
  const report={contract:'TAKY_FAMILY_SPECIALIST_BROWSER_V1',environment:'LOCAL_MOCK_UI_NO_CANONICAL_WRITE',
   actors:scenarios.length,events:rows.reduce((n,r)=>n+r.events.length,0),errors:rows.flatMap(x=>x.errors.map(e=>({actor:x.actor,...e}))),
   rows,limitations:['NOT_LIVE_LEARNING_ENGINE','NOT_CROSS_APP_HANDOFF','NOT_REAL_DEVICE']};
  fs.writeFileSync(path.join(out,'specialists-latest.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({contract:report.contract,actors:report.actors,events:report.events,errors:report.errors.slice(0,5),report:path.join(out,'specialists-latest.json')}));
  if(report.errors.length)process.exitCode=1;
 }catch(e){console.error('SPECIALIST_BROWSER_FATAL',e.stack);process.exitCode=2;}
 finally{await browser?.close().catch(()=>{});for(const server of servers)await new Promise(r=>server.close(r));}
})();
