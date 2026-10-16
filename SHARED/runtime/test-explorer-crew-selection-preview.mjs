import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {extname,resolve,sep} from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const specs=[{app:'HIDE_SEEK',dir:'Hide & Seek',port:4291},
 {app:'SNAP_POP',dir:'Snap & Pop',port:4292},
 {app:'READY_SET',dir:'Ready & Set',port:4693}];
const types={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8',
 '.json':'application/json','.css':'text/css','.wav':'audio/wav','.mp3':'audio/mpeg',
 '.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'};
const results=[];
function serve(s){
 const root=resolve('D:/Git PWA/'+s.dir);
 const server=createServer((req,res)=>{
  const uri=new URL(req.url,'http://localhost');
  let p;
  try{p=resolve(root,'.'+decodeURIComponent(uri.pathname).replace(/\/$/,'/index.html'))}
  catch{res.writeHead(400).end();return}
  if(!p.startsWith(root+sep)&&p!==root){res.writeHead(403).end();return}
  if(!existsSync(p)){res.writeHead(404).end();return}
  res.writeHead(200,{'Content-Type':types[extname(p).toLowerCase()]||'application/octet-stream',
   'Cache-Control':'no-store'});
  createReadStream(p).pipe(res);
 });
 return new Promise((resolve,reject)=>server.once('error',reject).listen(s.port,'127.0.0.1',()=>resolve(server)));
}
const browser=await chromium.launch({headless:true,
 executablePath:process.env.TAKY_PICK_BROWSER==='EDGE'?'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe':'C:/Program Files/Google/Chrome/Application/chrome.exe',
 args:['--autoplay-policy=no-user-gesture-required']});
try{
 for(const spec of specs.filter(s=>!process.env.TAKY_PICK_APP||process.env.TAKY_PICK_APP===s.app)){
  const server=await serve(spec);let context;
  const result={app:spec.app,ok:false,events:[],page_errors:[]};
  try{
   context=await browser.newContext({serviceWorkers:'block',viewport:{width:800,height:850}});
   await context.addInitScript(showAll=>{
    localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify({
     state:{relation:{
      main_character_id:'dubi',
      members:{dubi:{relation_state:'MAIN_COMPANION',affinity:1},
       lori:{relation_state:'COMPANION_AVAILABLE',affinity:8},
       'guide-19':{relation_state:'KNOWN',affinity:1}}
     }},updated_at:new Date().toISOString()
    }));
    if(showAll){const raw=JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1'));
      for(let n=7;n<=24;n++){const id='guide-'+String(n).padStart(2,'0');
        raw.state.relation.members[id]={relation_state:'KNOWN',affinity:1};}
      localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify(raw));}
   },process.env.TAKY_PICK_ALL==='1');
   if(spec.app==='READY_SET'){
    await context.addInitScript(()=>{
      const now=new Date().toISOString();
      localStorage.setItem('readyset_identity_v1',JSON.stringify({
       schemaVersion:6,status:'READY',onboardingStep:'DONE',setupMode:'GUARDIAN_FOR_CHILD',
       operator:{role:'GUARDIAN',name:'목업 검증'},userId:'QA_CREW_ONLY',memberId:'QA_CREW_CHILD',
       legalName:'목업 검증',nickname:'테스트 탐험가',familyRole:'CHILD',birthDate:'2015-03-02',
       schoolStage:'E5',characterVisualId:null,characterSetupState:'DEFERRED_NO_COST',
       explorerId:'dubi',explorerName:'두비',journeyTheme:'CAMP',createdAt:now,updatedAt:now
      }));
    });
   }
   const page=await context.newPage();page.setDefaultTimeout(8000);
   page.on('pageerror',e=>result.page_errors.push(String(e)));
   console.log('OPEN_APP '+spec.app);
   await page.goto('http://127.0.0.1:'+spec.port+'/index.html',
     {waitUntil:'domcontentloaded',timeout:18000});
   await page.waitForFunction(()=>window.TakyCrewSelectionPreviewController?.snapshot?.(),{timeout:10000});
   result.mounted=true;
   if(spec.app==='READY_SET'){
    const diag=await page.evaluate(()=>{
     const b=document.getElementById('takyCrewSelectionLauncher');
     return {outer:b?.outerHTML?.slice(0,220),display:getComputedStyle(b).display,
       visibility:getComputedStyle(b).visibility,opacity:getComputedStyle(b).opacity,
       bounds:b?.getBoundingClientRect().toJSON(),bodyDisplay:getComputedStyle(document.body).display,
       parentOverflow:getComputedStyle(document.body).overflow,
       covering:document.elementFromPoint(700,700)?.outerHTML?.slice(0,150)};
    });
    console.log('READY_PICKER_DIAGNOSTIC '+JSON.stringify(diag));
    const box=await page.evaluate(()=>document.getElementById('takyCrewSelectionLauncher')?.getBoundingClientRect().toJSON());
    if(!box)throw Error('PICKER_NOT_VISIBLE');
    await page.mouse.click(box.x+box.width/2,box.y+box.height/2);
   }else await page.locator('#takyCrewSelectionLauncher').click({timeout:6000});
   result.cards=await page.locator('[data-taky-id]').count();
   const fullNames=['두비','로리','잉크','노바','테이크','제로','솔라','벨로','모카','니아','키로','피치','민트','토토','루네','포포','마루','보리','린','루미','테스','셀','제이크','비비'];
   const allIds=['dubi','lori','ink','nova','take','zero',...Array.from({length:18},(_,i)=>'guide-'+String(i+7).padStart(2,'0'))];
   const choices=process.env.TAKY_PICK_ALL==='1'?allIds.map((id,i)=>[id,fullNames[i]]):[['dubi','두비'],['lori','로리'],['guide-19','린'],['dubi','두비']];
   for(const [id,expected] of choices){
    if(spec.app==='READY_SET'){
      const card=await page.evaluate(id=>document.querySelector('[data-taky-id="'+id+'"]')?.getBoundingClientRect().toJSON(),id);
      if(!card)throw Error('CREW_CARD_NOT_VISIBLE:'+id);
      await page.mouse.click(card.x+card.width/2,card.y+card.height/2);
    }else await page.locator('[data-taky-id="'+id+'"]').click({timeout:6000});
    await page.waitForFunction(
      key=>window.TakyCrewSelectionPreviewController?.snapshot?.().play_results?.at(-1)?.id===key,
      id,{timeout:12000});
    const probe=await page.evaluate(()=>{
     const picker=window.TakyCrewSelectionPreviewController.snapshot();
     return {who:document.querySelector('[data-taky-who]')?.textContent,
      text:document.querySelector('[data-taky-speech]')?.textContent,
      status:document.querySelector('[data-taky-status]')?.textContent,
      latest:picker.play_results.at(-1),visible:picker.visible_ids,
      selectionPersisted:JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1')).state.relation.main_character_id}
    });
    result.events.push({id,...probe});
    if(probe.who!==expected||probe.latest?.status!=='PLAYING_STARTED'||
       probe.latest?.key!=='MAIN_CREW:'+id+':SIGNATURE'||
       probe.selectionPersisted!=='dubi')throw Error('INCORRECT_POPUP_SOUND_OR_PREVIEW_CHANGED_RELATION:'+id+':'+JSON.stringify(probe));
   }
   await page.keyboard.press('Escape');
   result.escape_closed=await page.locator('[role=dialog]').count()===0;
   result.ok=result.escape_closed&&result.cards===(process.env.TAKY_PICK_ALL==='1'?24:7)&&result.events.length===choices.length;
  }catch(e){result.error=String(e)}
  finally{results.push(result);if(context)await context.close().catch(()=>{});
   server.closeAllConnections?.();await new Promise(r=>server.close(r))}
  console.log('APP_RESULT '+JSON.stringify({app:spec.app,ok:result.ok,cards:result.cards,error:result.error,
   event_statuses:result.events.map(x=>x.latest?.status),page_errors:result.page_errors.length}));
 }
}finally{await browser.close()}
const passed=results.filter(x=>x.ok).length;
const output={status:passed===results.length?'PASS':'FAIL',tested_apps:results.length,passed,results};
const filename='D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_SELECTION_TAP_QA_20261013'+
 (process.env.TAKY_PICK_APP?'_'+process.env.TAKY_PICK_APP:'')+'.json';
writeFileSync(filename,JSON.stringify(output,null,2));
console.log('QA_STATUS '+output.status+' '+passed+'/'+results.length);
if(output.status!=='PASS')process.exitCode=2;
