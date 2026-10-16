import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {resolve,extname,sep} from 'node:path';
const require=createRequire(import.meta.url);
const sys=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/system-v2.js');
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const memory=new Map(),storage={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)};
const controller=sys.create({app_id:'HIDE_SEEK',storage,replaceUrl:()=>{}});
async function dispatch(id,type,event_id){
 const data={character_id:id,interaction_result:{relation_event:{character_id:id,type,at:new Date().toISOString(),...(event_id?{event_id}:{})}}};
 if(type==='SHARED_ACTIVITY')data.companion_gate={affinity_requirement_met:true,story_unlocked:true};
 return controller.dispatch(data);
}
for(const id of ['dubi','lori']){await dispatch(id,'FIRST_MET');await dispatch(id,'SHARED_ACTIVITY','PROVEN_'+id);}
await dispatch('dubi','MAIN_SELECTED');
const raw=storage.getItem('taky_explorer_crew_canonical_v1');
const directory='D:/Git PWA/Hide & Seek',port=4694;
const server=createServer((req,res)=>{
 let p;
 try{p=resolve(directory,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html'));}
 catch{res.writeHead(400).end();return}
 if(!p.startsWith(resolve(directory)+sep)||!existsSync(p)){res.writeHead(404).end();return}
 const ext=extname(p).toLowerCase(),types={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css','.wav':'audio/wav','.png':'image/png','.svg':'image/svg+xml'};
 res.writeHead(200,{'Content-Type':types[ext]||'application/octet-stream'});createReadStream(p).pipe(res);
});
await new Promise(r=>server.listen(port,'127.0.0.1',r));
const b=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--autoplay-policy=no-user-gesture-required']});
const context=await b.newContext({serviceWorkers:'block',viewport:{width:900,height:800}});
await context.addInitScript(stored=>{localStorage.setItem('taky_explorer_crew_canonical_v1',stored)},raw);
const page=await context.newPage(),report={status:'FAIL',steps:[],errors:[]};
page.on('pageerror',err=>report.errors.push(String(err)));
try{
 await page.goto('http://127.0.0.1:'+port+'/index.html',{waitUntil:'domcontentloaded',timeout:18000});
 await page.waitForFunction(()=>window.TakyCrewSelectionPreviewController?.snapshot?.());
 await page.locator('#takyCrewSelectionLauncher').click();
 await page.locator('[data-taky-id=lori]').click();
 await page.waitForFunction(()=>document.querySelector('[data-taky-status]')?.textContent.includes('재생'),{timeout:12000});
 report.steps.push({stage:'PREVIEW',who:await page.locator('[data-taky-who]').textContent(),
  before_main:await page.evaluate(()=>JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1')).state.relation.main_character_id)});
 const confirm=page.locator('[data-taky-confirm]');
 report.steps.push({stage:'CONFIRM_BUTTON',enabled:await confirm.isEnabled()});
 if(!await confirm.isEnabled())throw Error('COMPANION_GATE_CHECK_BLOCKED_VALID_AVAILABLE_COMPANION');
 await confirm.click();
 await page.waitForFunction(()=>JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1')).state.relation.main_character_id==='lori',{timeout:12000});
 const x=await page.evaluate(()=>JSON.parse(localStorage.getItem('taky_explorer_crew_canonical_v1')).state.relation);
 report.steps.push({stage:'COMMITTED',main:x.main_character_id,dubi:x.members.dubi.relation_state,lori:x.members.lori.relation_state});
 report.status=x.main_character_id==='lori'&&x.members.dubi.relation_state==='COMPANION'&&x.members.lori.relation_state==='MAIN_COMPANION'?'PASS':'FAIL';
}catch(e){report.error=String(e);}
finally{
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_ACTUAL_SELECTION_COMMIT_BROWSER_QA_20261013.json',JSON.stringify(report,null,2));
 console.log(JSON.stringify(report,null,2));
 await context.close().catch(()=>{});await b.close();server.closeAllConnections?.();await new Promise(r=>server.close(r));
}
if(report.status!=='PASS')process.exitCode=2;
