import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,writeFileSync} from 'node:fs';
import {resolve,sep,extname} from 'node:path';
const require=createRequire(import.meta.url),{chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const specs=[
 {app:'HIDE_SEEK',folder:'Hide & Seek',port:4381,child:'dubi',bridge:'HideSeekBridge',type:'HELP_NEEDED',payload:{crew_voice_requested:true},intent:'HINT'},
 {app:'SNAP_POP',folder:'Snap & Pop',port:4382,child:'guide-19',bridge:'SnapPopBridge',type:'TASK_COMPLETED',payload:{child_authored:true},intent:'ACKNOWLEDGE'}
];
const report={status:'FAIL',tests:[]};
let browser;
const servers=[];
function startServer(spec){
 const dir=resolve('D:/Git PWA/'+spec.folder);
 const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.wav':'audio/wav','.png':'image/png','.svg':'image/svg+xml'};
 const server=createServer((req,res)=>{
  let p;try{p=resolve(dir,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html'))}catch{res.writeHead(400).end();return}
  if(!p.startsWith(dir+sep)||!existsSync(p)){res.writeHead(404).end();return}
  res.writeHead(200,{'Content-Type':types[extname(p).toLowerCase()]||'application/octet-stream'});createReadStream(p).pipe(res);
 });
 servers.push(server);
 return new Promise((y,n)=>server.once('error',n).listen(spec.port,'127.0.0.1',()=>y(server)));
}
try{
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
 args:['--autoplay-policy=no-user-gesture-required']});
 for(const spec of specs){
  await startServer(spec);
  const ctx=await browser.newContext({serviceWorkers:'block'});
  const result={app:spec.app,pass:false,errors:[]};
  try{
   await ctx.addInitScript(id=>{
    const relation={main_character_id:id,members:{[id]:{relation_state:'MAIN_COMPANION',affinity:2}}};
    localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify({state:{relation},updated_at:new Date().toISOString()}));
   },spec.child);
   const page=await ctx.newPage();page.on('pageerror',e=>result.errors.push(String(e)));
   const args='?session_id=NATIVE_EVENT_01&task_id=TASK_NATIVE_01&child_id=LEARNER_NATIVE_01&school_stage=E3&school_grade=3';
   await page.goto('http://127.0.0.1:'+spec.port+'/index.html'+args,
     {waitUntil:'domcontentloaded',timeout:16000});
   await page.waitForFunction(()=>window.TakyCrewAudioAppEvidence?.status==='APP_EVENT_CONSUMER_ATTACHED',null,{timeout:12000});
   const info=await page.evaluate(({bridge,type,payload})=>{
    const a=window[bridge];if(!a?.emit)throw Error('NO_NATIVE_EMITTER');
    const event=a.emit(type,payload);return {event,eventContext:a.context()};
   },spec);
   result.native_event=info.event?.type||null;result.context=info.eventContext;
   await page.waitForFunction(()=>window.TakyCrewAudioAppEvidence?.native_learning_events?.some(x=>
    x.status==='PLAYING_STARTED' && x.key?.includes(':')),null,{timeout:12000});
   const state=await page.evaluate(()=>({
    evidence:window.TakyCrewAudioAppEvidence?.native_learning_events,
    last:window.TakyCrewAudioAppEvidence?.last_result
   }));
   result.events=state.evidence;result.last=state.last;
   result.pass=!!state.last?.key?.startsWith('MAIN_CREW:'+spec.child+':'+spec.intent+':')&&
     state.last.status==='PLAYING_STARTED'&&state.evidence.some(x=>x.status==='PLAYING_STARTED');
  }catch(error){result.error=String(error)}
  finally{
   report.tests.push(result);
   await Promise.race([ctx.close().catch(()=>{}),new Promise(r=>setTimeout(r,1000))]);
  }
  console.log('APP_RESULT '+spec.app+' '+(result.pass?'PASS':'FAIL')+' '+String(result.error||''));
  servers.at(-1).closeAllConnections?.();servers.at(-1).close();
 }
 report.status=report.tests.every(x=>x.pass)?'PASS':'FAIL';
}finally{
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_NATIVE_LEARNING_EVENT_AUDIO_QA_20261013.json',JSON.stringify(report,null,2));
 console.log('FINAL '+report.status);
 await Promise.race([browser?.close().catch(()=>{}),new Promise(r=>setTimeout(r,1800))]);
 for(const s of servers){s.closeAllConnections?.();s.close();}
}
if(report.status!=='PASS')process.exitCode=2;
