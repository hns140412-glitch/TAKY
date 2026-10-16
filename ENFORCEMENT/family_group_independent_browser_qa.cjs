'use strict';
// TAKY QA: independent browser agents on REAL local app UIs. NO production account/API.
const assert=require('node:assert/strict');
const fs=require('node:fs'), path=require('node:path'), http=require('node:http');
const {spawn}=require('node:child_process');
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const work=path.resolve(__dirname,'../..');
const seed=Number(process.env.TAKY_QA_SEED||20261015)>>>0;
const steps=Math.max(2,Math.min(8,Number(process.env.TAKY_QA_BROWSER_STEPS||3)));
const out=path.resolve(__dirname,'../.local/family-qa/browser');
fs.mkdirSync(out,{recursive:true});
const roles=[
 {id:'A-P1',family:'SIM-A',role:'PARENT'},{id:'A-P2',family:'SIM-A',role:'PARENT'},
 {id:'A-L1',family:'SIM-A',role:'LEARNER'},{id:'A-L2',family:'SIM-A',role:'LEARNER'},
 {id:'B-P1',family:'SIM-B',role:'PARENT'},{id:'B-L1',family:'SIM-B',role:'LEARNER'},
 {id:'SYS-ADMIN',family:null,role:'ADMIN'}
];
function rng(s){return()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};}
function shuffle(xs,r){for(let i=xs.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[xs[i],xs[j]]=[xs[j],xs[i]];}return xs;}
const roots=[{root:path.join(work,'Ready & Set'),port:4430},{root:path.join(work,'TAKY-MOBILE'),port:4431}];
const allow=/\.(?:html|js|mjs|css|json|webmanifest|svg|png|jpe?g|webp|gif|woff2?|ttf|ico|mp3|wav|ogg)$/i;
function staticServer(root,port){
 return http.createServer((req,res)=>{
  let url;
  try{url=new URL(req.url,'http://127.0.0.1:'+port);}catch{res.writeHead(400);return res.end();}
  if(req.method!=='GET'){res.writeHead(405);return res.end();}
  const rel=decodeURIComponent(url.pathname).replace(/^\/+/, '')||'index.html';
  if(rel.startsWith('.')||rel.split('/').some(x=>x.startsWith('.')||x==='node_modules')||!allow.test(rel)){
   res.writeHead(404);return res.end();
  }
  const file=path.resolve(root,rel);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){
   res.writeHead(404);return res.end();
  }
  const mime={html:'text/html',js:'text/javascript',mjs:'text/javascript',css:'text/css',json:'application/json',svg:'image/svg+xml',webmanifest:'application/manifest+json',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg',webp:'image/webp',mp3:'audio/mpeg',wav:'audio/wav',ogg:'audio/ogg',woff2:'font/woff2'};
  res.writeHead(200,{'Cache-Control':'no-store','Content-Type':(mime[path.extname(file).slice(1)]||'application/octet-stream')});
  if(/\.(?:js|mjs|css|html)$/.test(file)){try{return res.end(fs.readFileSync(file));}catch{return res.destroy();}}
  fs.createReadStream(file).on('error',()=>res.destroy()).pipe(res);
 }).listen(port,'127.0.0.1');
}
async function serve(){
 const servers=[];
 for(const cfg of roots){
  const srv=staticServer(cfg.root,cfg.port);
  await new Promise((resolve,reject)=>{if(srv.listening)return resolve();srv.once('listening',resolve);srv.once('error',reject);});
  servers.push(srv);
 }
 return servers;
}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function vite(){
 const repo=path.join(work,'SAVEY'),script=path.join(repo,'node_modules/vite/bin/vite.js');
 if(!fs.existsSync(script))throw Error('SAVEY_VITE_NOT_INSTALLED');
 const child=spawn(process.execPath,[script,'--host','127.0.0.1','--port','4432','--strictPort'],{cwd:repo,windowsHide:true,stdio:'ignore',env:{...process.env,NO_COLOR:'1',VITE_STATIC_DEVICE_PREVIEW:'1'}});
 child.on('error',()=>{});
 for(let i=0;i<50;i++){
  if(child.exitCode!==null)throw Error('SAVEY_VITE_EXIT_'+child.exitCode);
  try{const r=await fetch('http://127.0.0.1:4432/');if(r.ok)return child;}catch{}
  await wait(140);
 }
 child.kill();throw Error('SAVEY_VITE_START_TIMEOUT');
}
function seedReady(actor){
 const parent=actor.role==='PARENT';
 return {
  schemaVersion:5,status:'READY',onboardingStep:'DONE',
  setupMode:parent?'GUARDIAN_FOR_CHILD':'SELF',operator:{role:parent?'GUARDIAN':'CHILD'},
  userId:actor.id,memberId:actor.id,legalName:'가상 사용자',nickname:actor.id,
  familyRole:parent?'GUARDIAN':'CHILD',schoolStage:'E5',birthDate:'2015-05-01',
  explorerId:'lumi',explorerName:'루미',journeyTheme:'TODAYS_ISLAND',
  characterSetupState:'DEFERRED_NO_COST',characterVisualId:'crew01',
  source:'SYNTHETIC_QA_ONLY'
 };
}
const result={contract:'TAKY_INDEPENDENT_BROWSER_AGENTS_V1',seed,stepsPerBot:steps,
  startedAt:new Date().toISOString(),actors:roles.length,familyGroups:2,scenarios:[],errors:[],gaps:[],
  limits:['LOCAL_BROWSER_UI_ONLY','SAVEY_DEV_PREVIEW_NOT_FINANCIAL_AUTH','CENTRAL_MULTI_DEVICE_BACKEND_NOT_CONNECTED','REAL_DEVICE_NOT_VERIFIED']};
const filtered=process.env.TAKY_QA_BROWSER_ACTORS?.split(',').filter(Boolean);
const runRoles=filtered?roles.filter(x=>filtered.includes(x.id)):roles;
const verbose=process.env.TAKY_QA_BROWSER_TRACE==='1';
const progress=(a,msg)=>{if(verbose)console.log('BOT_STEP '+a+' '+msg);};
const forbidden=new Set();
const servers=[];let viteChild,browser;
async function screenshot(page,actor,phase){
 const filename=path.join(out,actor.id+'-'+phase+'.png');
 try{await page.screenshot({path:filename,timeout:2800});return filename;}catch{return null;}
}
async function actorBot(actor,n){
 const random=rng(seed+n*1711),trace=[];
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,
   serviceWorkers:'block',reducedMotion:'reduce',locale:'ko-KR'});
 const page=await context.newPage(),issues=[];
 const pendingRequests=new Map();
 page.on('request',r=>pendingRequests.set(r,r.url()));
 page.on('requestfinished',r=>pendingRequests.delete(r));
 page.on('requestfailed',r=>pendingRequests.delete(r));
 page.on('pageerror',e=>issues.push({type:'PAGE_JS',detail:String(e.message).slice(0,240)}));
 if(process.env.TAKY_QA_READY_HANDLER_TRACE==='1'){
  page.on('console',msg=>{if(msg.text().startsWith('QA_NAV_HANDLER_')||msg.text().startsWith('QA_DISPATCH_'))progress(actor.id,msg.text());});
  page.on('framenavigated',frame=>progress(actor.id,'FRAME_NAV_'+frame.url().slice(0,100)));
  page.on('domcontentloaded',()=>progress(actor.id,'DOM_READY'));
  page.on('load',()=>progress(actor.id,'PAGE_LOAD'));
  page.on('crash',()=>progress(actor.id,'PAGE_CRASH'));
  page.on('close',()=>progress(actor.id,'PAGE_CLOSE'));
  await page.addInitScript(()=>{
   const original=EventTarget.prototype.addEventListener;
   const oldDispatch=EventTarget.prototype.dispatchEvent;const types={};
   EventTarget.prototype.dispatchEvent=function(event){
     const t=event?.type||'', n=types[t]=(types[t]||0)+1;
     if(/ready|taky|planner|homework|family/i.test(t) && (n<=3||n===10||n===50||n===100))
       console.log('QA_DISPATCH_'+t+'_'+n);
     return oldDispatch.call(this,event);
   };
   let count=0;
   EventTarget.prototype.addEventListener=function(type,handler,options){
    if(type==='click' && typeof handler==='function'){
      const wrapped=function(event){
        const target=event.target?.closest?.('[data-nav]');
        if(target){
          const id=++count;
          console.log('QA_NAV_HANDLER_ENTER_'+id+'_'+(this===document?'document':this.tagName)+'_'+target.dataset.nav+'_'+String(handler).slice(0,75));
          try{return handler.call(this,event);}
          finally{console.log('QA_NAV_HANDLER_EXIT_'+id);}
        }
        return handler.call(this,event);
      };
      return original.call(this,type,wrapped,options);
    }
    return original.call(this,type,handler,options);
   };
  });
 }

 page.on('dialog',d=>d.dismiss());
 await context.route('**/*',route=>{
  const url=new URL(route.request().url());
  if(url.protocol!=='http:'||url.hostname!=='127.0.0.1'||![4430,4431,4432].includes(Number(url.port))){
   forbidden.add(url.origin);return route.abort();
  }
  if(url.port==='4430'&&url.pathname==='/ready-home-homework-ui-v1.js'&&process.env.TAKY_QA_READY_ISOLATE_UI_MODULE==='1')
    return route.fulfill({status:200,contentType:'text/javascript',body:'/* DIAGNOSTIC ONLY: READY HOMEWORK UI MODULE ISOLATED */'});
  if(url.pathname.startsWith('/api/')||url.pathname.startsWith('/.netlify/functions/')){
   if(url.pathname.endsWith('/canonical'))return route.fulfill({status:401,contentType:'application/json',body:'{"ok":false,"error":"AUTH_REQUIRED"}'});
   if(url.pathname.endsWith('/release-status'))return route.fulfill({status:503,contentType:'application/json',body:'{"ok":false,"error":"LOCAL_QA_NOT_CONNECTED"}'});
   return route.fulfill({status:503,contentType:'application/json',body:'{"ok":false,"error":"LOCAL_QA_API_ISOLATED"}'});
  }
  return route.continue();
 });
 let current='';const recording={actor:actor.id,role:actor.role,family:actor.family,steps:trace,issues};
 try{
  if(actor.role!=='ADMIN'&&process.env.TAKY_QA_BROWSER_SKIP_READY!=='1'){
   await page.addInitScript(identity=>{
     if(location.hostname!=='127.0.0.1'||location.port!=='4430')return;
     if(!localStorage.getItem('__taky_qa_seeded')){
       localStorage.setItem('__taky_qa_seeded','1');
       localStorage.setItem('readyset_identity_v1',JSON.stringify(identity));
       localStorage.setItem('readyset_active_role_v1',identity.operator.role==='GUARDIAN'?'parent':'child');
     }
   },seedReady(actor));
   progress(actor.id,'READY_NAV');
   await page.goto('http://127.0.0.1:4430/?role='+(actor.role==='PARENT'?'parent':'child'),{waitUntil:'domcontentloaded',timeout:6500});
   await page.waitForFunction(()=>!!window.ReadyRoleContextV1,{timeout:5500});
   const actual=await page.evaluate(()=>window.ReadyRoleContextV1.current());
   assert.equal(actual,actor.role==='PARENT'?'parent':'child','WRONG_READY_ROLE');
   const diagnostic=await page.evaluate(()=>({html:document.documentElement.className,appVisible:getComputedStyle(document.querySelector('#app')).visibility,ready:window.ReadyIdentityV1?.isReady?.(),homeVisible:!!document.querySelector('#homeView.active'),firstRunVisible:!!document.querySelector('#readyFirstRun .firstRunSky'),world:!!document.querySelector('#worldStage .worldBoot'),navVisibility:!!document.querySelector('button[data-nav="home"]')?.getClientRects()?.length}));
   progress(actor.id,'READY_DIAG_'+JSON.stringify(diagnostic));
   const loadBefore=await page.evaluate(()=>document.readyState);
   progress(actor.id,'READY_STATE_BEFORE_'+loadBefore);
   if(process.env.TAKY_QA_READY_WAIT_LOAD==='1'){
     try{await page.waitForLoadState('load',{timeout:5500});progress(actor.id,'READY_LOAD_COMPLETE');}
     catch(e){progress(actor.id,'READY_LOAD_TIMEOUT_'+String(e.message).slice(0,100));progress(actor.id,'READY_PENDING_COUNT_'+pendingRequests.size+'_FILES_'+JSON.stringify([...pendingRequests.values()].slice(0,22)));}
   }
   progress(actor.id,'READY_ROLE_PASS');
   trace.push({app:'Ready & Set',action:'role',status:'PASS',actual});
   const readyActions=actor.role==='PARENT'
    ? ['home','calendar','history','settings','home']
    : ['home','mission','calendar','history','home'];
   const picks=process.env.TAKY_QA_READY_TARGETS?process.env.TAKY_QA_READY_TARGETS.split(',').slice(0,steps):shuffle([...readyActions],random).slice(0,steps);
   for(const target of picks){
     progress(actor.id,'READY_STEP_'+target);
     try{
       progress(actor.id,'READY_BUTTON_START_'+target);
       const btn=page.locator('button[data-nav="'+target+'"]:visible').first();
       if(await btn.count()){
         const hit=await btn.evaluate(e=>{
           const r=e.getBoundingClientRect(),cx=Math.round((r.left+r.right)/2),cy=Math.round((r.top+r.bottom)/2);
           const over=document.elementFromPoint(cx,cy),css=getComputedStyle(e);
           return {target:e.outerHTML.slice(0,180),rect:{x:r.x,y:r.y,width:r.width,height:r.height},
             top:over?.outerHTML?.slice(0,220),centerInside:over===e||e.contains(over),
             pointerEvents:css.pointerEvents,opacity:css.opacity,disabled:e.disabled};
         });
         progress(actor.id,'READY_HIT_'+target+'_'+JSON.stringify(hit));
         progress(actor.id,'READY_CLICK_START_'+target);
         if(process.env.TAKY_QA_READY_DOM_ONLY==='1')await btn.evaluate(e=>e.click(),{timeout:1500});
         else await btn.tap({timeout:1500,noWaitAfter:true});
         progress(actor.id,'READY_CLICK_DONE_'+target);
       }
       else await page.evaluate(t=>window.ReadyBaseRuntimeV1?.nav?.(t),target);
       await wait(30+Math.floor(random()*70));
       progress(actor.id,'READY_VIEW_START_'+target);
       const view=await page.evaluate(()=>[...document.querySelectorAll('.view.active')].map(x=>x.id));
       if(!view.length)throw Error('NO_VISIBLE_ACTIVE_READY_VIEW');
       progress(actor.id,'READY_VIEW_DONE_'+target);
       trace.push({app:'Ready & Set',action:'nav-'+target,status:'PASS',view:view[0]});
     }catch(e){issues.push({app:'Ready & Set',action:'nav-'+target,error:String(e.message).slice(0,230)});}
   }
   // Reconnect rehearsal: reload only; do not claim server data restoration.
   progress(actor.id,'READY_RELOAD');
   await page.reload({waitUntil:'domcontentloaded',timeout:6000});
   await page.waitForFunction(()=>!!window.ReadyRoleContextV1,{timeout:4300});
   const reopened=await page.evaluate(()=>({role:window.ReadyRoleContextV1.current(),member:JSON.parse(localStorage.getItem('readyset_identity_v1')||'{}').memberId}));
   if(reopened.member!==actor.id)issues.push({app:'Ready & Set',action:'reconnect',error:'MEMBER_MISMATCH'});
   trace.push({app:'Ready & Set',action:'reload',status:'PASS',memberStable:reopened.member===actor.id});
  }else if(actor.role==='ADMIN'){
   progress(actor.id,'MOBILE_NAV');
   await page.goto('http://127.0.0.1:4431/',{waitUntil:'domcontentloaded',timeout:6500});
   await page.waitForSelector('#operationsList .ops-strip-counts',{timeout:5000});
   const tabs=shuffle(['ops','work','trace','lab','taky'],random).slice(0,steps);
   for(const target of tabs){
    try{
     await page.locator('.nav-btn[data-target="'+target+'"]').click({timeout:2200});
     const visible=await page.locator('.screen[data-screen="'+target+'"]').isVisible();
     if(!visible)throw Error('ADMIN_PANEL_NOT_VISIBLE');
     trace.push({app:'TAKY Mobile',action:'nav-'+target,status:'PASS'});
    }catch(e){issues.push({app:'TAKY Mobile',action:'nav-'+target,error:String(e.message).slice(0,220)});}
   }
   const badge=await page.locator('[data-check="family-backup"]').getAttribute('data-state');
   if(badge==='VERIFIED')issues.push({app:'TAKY Mobile',action:'no-false-green',error:'FAMILY_BACKUP_FALSE_VERIFIED'});
   trace.push({app:'TAKY Mobile',action:'verify-unconnected-backup',status:'PASS',state:badge});
  }
  if(actor.role!=='ADMIN'){
   const preview=actor.role==='PARENT'?'parent':'child';
   progress(actor.id,'SAVEY_NAV');
   await page.goto('http://127.0.0.1:4432/?preview='+preview,{waitUntil:'domcontentloaded',timeout:7500});
   await page.waitForSelector(actor.role==='PARENT'?'.p-screen':'.child-screen',{timeout:6500});
   const choices=actor.role==='PARENT'?['home','record','save','more','home']:['child-home','child-record','child-mission','child-more','child-home'];
   for(const screen of shuffle([...choices],random).slice(0,steps)){
     progress(actor.id,'SAVEY_STEP_'+screen);
     try{
      const selector=actor.role==='PARENT'?'[data-screen="'+screen+'"]':'[data-child-screen="'+screen+'"]';
      const btn=page.locator(selector+':visible').first();
      if(!await btn.count())throw Error('NAV_CONTROL_NOT_VISIBLE');
      await btn.click({timeout:1800});
      const expected=actor.role==='PARENT'
        ? await page.locator('.p-screen[data-id="'+screen+'"]').isVisible()
        : await page.locator('.child-screen[data-child-id="'+screen+'"]').isVisible();
      if(!expected)throw Error('SCREEN_NOT_VISIBLE');
      trace.push({app:'SAVEY',action:'nav-'+screen,status:'PASS',preview:true});
     }catch(e){issues.push({app:'SAVEY',action:'nav-'+screen,error:String(e.message).slice(0,250)});}
   }
   progress(actor.id,'SAVEY_RELOAD');
   await page.reload({waitUntil:'domcontentloaded',timeout:5800});
   await page.waitForSelector(actor.role==='PARENT'?'.p-screen':'.child-screen',{timeout:5500});
   trace.push({app:'SAVEY',action:'reload-preview',status:'PASS'});
  }
 }catch(e){issues.push({actor:actor.id,phase:'bootstrap',error:String(e.message).slice(0,350)});}
 if(issues.length){
  const shot=await screenshot(page,actor,'failure');if(shot)recording.screenshot=shot;
 }
 await context.close();
 return recording;
}
(async()=>{
 try{
  for(const cfg of roots){const srv=staticServer(cfg.root,cfg.port);await new Promise((resolve,reject)=>{srv.once('listening',resolve);srv.once('error',reject)});servers.push(srv);}
  viteChild=await vite();
  browser=await chromium.launch({headless:true,channel:'chrome',timeout:15000});
  const pool=[...runRoles],active=[];
  // Up to three real contexts at once. Each bot picks its own action order.
  for(let i=0;i<Math.min(3,runRoles.length);i++)active.push((async()=>{
   while(pool.length){
    const actor=pool.shift();
    const row=await actorBot(actor,roles.indexOf(actor));
    progress(actor.id,'FINISHED errors='+row.issues.length);
    result.scenarios.push(row);result.errors.push(...row.issues.map(e=>({actor:row.actor,...e})));
   }
  })());
  await Promise.all(active);
  result.scenarios.sort((a,b)=>roles.findIndex(x=>x.id===a.actor)-roles.findIndex(x=>x.id===b.actor));
  result.finishedAt=new Date().toISOString();
  result.stats={actors:result.scenarios.length,uiSteps:result.scenarios.reduce((x,r)=>x+r.steps.length,0),
    errors:result.errors.length,externalOriginsBlocked:forbidden.size};
  const target=path.join(out,'latest.json');fs.writeFileSync(target,JSON.stringify(result,null,2));
  console.log(JSON.stringify({contract:result.contract,seed,stats:result.stats,errors:result.errors.slice(0,10),result:target,limitations:result.limits}));
  if(result.errors.length)process.exitCode=1;
 }catch(e){console.error('TAKY_BROWSER_QA_FATAL',e.stack);process.exitCode=2;}
 finally{
  await browser?.close().catch(()=>{});
  if(viteChild){viteChild.kill();await wait(160);}
  for(const srv of servers)await new Promise(r=>srv.close(r));
 }
})();
