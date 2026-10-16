import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createReadStream,existsSync,readFileSync,writeFileSync} from 'node:fs';
import {extname,resolve,sep} from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const specs=[
 {app_id:'HIDE_SEEK',folder:'Hide & Seek',port:4191,id:'dubi',button:'#takyCrewVoiceBtn'},
 {app_id:'SNAP_POP',folder:'Snap & Pop',port:4192,id:'guide-19',button:'#homeRadio'},
 {app_id:'READY_SET',folder:'Ready & Set',port:4193,id:'guide-08',button:'#takyCrewVoiceBtn'}
];
function serverFor(spec){
 const dir='D:/Git PWA/'+spec.folder,types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
 '.json':'application/json; charset=utf-8','.css':'text/css; charset=utf-8','.wav':'audio/wav',
 '.mp3':'audio/mpeg','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'};
 const server=createServer((req,res)=>{
  let u;try{u=new URL(req.url,'http://localhost')}catch{res.writeHead(400).end();return}
  let decoded;try{decoded=decodeURIComponent(u.pathname)}catch{res.writeHead(400).end();return}
  const f=resolve(dir,'.'+decoded.replace(/\/$/,'/index.html'));
  if(!f.startsWith(resolve(dir)+sep)&&f!==resolve(dir)){res.writeHead(403).end();return}
  if(!existsSync(f)){res.writeHead(404,{'Access-Control-Allow-Origin':'*'}).end();return}
  res.writeHead(200,{'Content-Type':types[extname(f).toLowerCase()]||'application/octet-stream',
   'Cache-Control':'no-store','Access-Control-Allow-Origin':'*'});
  createReadStream(f).pipe(res);
 });
 return new Promise((yes,no)=>server.once('error',no).listen(spec.port,'127.0.0.1',()=>yes(server)));
}
let browser;
const report={status:'FAIL',tests:[],details:[],no_play_camp_changes:true};
try{
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
 args:['--autoplay-policy=no-user-gesture-required']});
 for(const spec of specs.filter(x=>!process.env.TAKY_AUDIO_TEST_APP||x.app_id===process.env.TAKY_AUDIO_TEST_APP)){
  console.log('START_APP '+spec.app_id);
  const server=await serverFor(spec);
  let context=null;
  const result={app_id:spec.app_id,character_id:spec.id,ui_button:spec.button,
   initialized:false,button_ready:false,route_key:null,audio_playing:false,playing_mode:null,
   test_school_stage:process.env.TAKY_AUDIO_TEST_GRADE||'E5',
   url_200:false,page_errors:[],app_warnings:[]};
  try{
   context=await browser.newContext({serviceWorkers:'block',viewport:{width:900,height:800}});
   await context.addInitScript(({app,id})=>{
     const record={state:{relation:{main_character_id:id,members:{[id]:{relation_state:'MAIN_COMPANION',affinity:2}}}},updated_at:new Date().toISOString()};
     localStorage.setItem('taky_explorer_crew_canonical_v1',JSON.stringify(record));
     if(app==='READY_SET'){
       const identity={schemaVersion:6,status:'READY',setupMode:'GUARDIAN_FOR_CHILD',onboardingStep:'DONE',
         operator:{role:'GUARDIAN',name:'QA_PARENT'},userId:'QA_PARENT',memberId:'QA_CHILD',
         legalName:'테스트',nickname:'테스트',familyRole:'CHILD',birthDate:'2015-05-04',
         schoolStage:'E5',characterVisualId:'guide-08',characterSetupState:'CONFIRMED',
         explorerId:'guide-08',explorerName:'벨로',journeyTheme:'CAMP'};
       localStorage.setItem('readyset_identity_v1',JSON.stringify(identity));
     }
   },{app:spec.app_id,id:spec.id});
   const page=await context.newPage();
   page.on('pageerror',e=>result.page_errors.push(String(e)));
   page.on('console',m=>{if(m.type()==='warning'||m.type()==='error')result.app_warnings.push(m.text().slice(0,200))});
   console.log('GOTO_APP '+spec.app_id);
   const stage=process.env.TAKY_AUDIO_TEST_GRADE||'E5';
   const sessionQuery=spec.app_id==='READY_SET'?'':('?session_id=VOICE_QA_01&task_id=VOICE_QA_TASK&child_id=QA_CHILD&school_stage='+encodeURIComponent(stage)+'&school_grade='+encodeURIComponent(stage.replace(/^E/,'')));
   await page.goto('http://127.0.0.1:'+spec.port+'/index.html'+sessionQuery,{waitUntil:'domcontentloaded',timeout:15000});
   console.log('GOTO_DONE '+spec.app_id);
   await page.waitForFunction(()=>window.TakyCrewAudioAppEvidence?.status==='APP_EVENT_CONSUMER_ATTACHED',
      {timeout:10000}).catch(()=>{});
   const details=await page.evaluate(()=>({
      evidence:window.TakyCrewAudioAppEvidence?.status,error:window.TakyCrewAudioAppEvidence?.error,
      hasPersonality:!!window.TakyExplorerCrewDialoguePersonality,
      hasBridge:!!window.TakyExplorerCrewTtsMockSwitch,
      hasEventAdapter:!!window.TakyExplorerCrewVoiceEventAdapter,
      hasRegistry:!!window.TakyCrewVoiceRegistry,
      projection:window.HideExplorerCrewAuthorityConsumer?.snapshot?.(localStorage)?.character_id||
        window.SnapExplorerCrewAuthorityConsumer?.snapshot?.(localStorage)?.character_id||null,
      button:document.getElementById('takyCrewVoiceBtn')?.outerHTML?.slice(0,400)||document.getElementById('homeRadio')?.outerHTML?.slice(0,400)
   }));
   result.init_details=details;
   result.initialized=details.evidence==='APP_EVENT_CONSUMER_ATTACHED';
   console.log('APP_INITIALIZED '+spec.app_id+' '+details.evidence+' '+JSON.stringify(details.error));
   if(!result.initialized)throw Error('APP_VOICE_HOOK_NOT_READY:'+JSON.stringify(details));
   if(spec.app_id==='READY_SET'){
     result.button_ready=await page.evaluate(()=>!!document.getElementById('takyCrewVoiceBtn') && !document.getElementById('takyCrewVoiceBtn').disabled);
   }else{
     await page.waitForFunction(selector=>{const b=document.querySelector(selector);return !!b&&!b.disabled;},spec.button,{timeout:8000});
     result.button_ready=true;
   }
   if(!result.button_ready)throw Error('APP_BUTTON_NOT_READY');
   // Real app UI button event. No direct call to the audio engine.
   console.log('CLICK_APP '+spec.app_id);
   if(spec.app_id==='READY_SET'){
     const before=await page.evaluate(()=>({
       button:document.getElementById('takyCrewVoiceBtn')?.outerHTML||null,
       canonical:localStorage.getItem('taky_explorer_crew_canonical_v1')?.slice(0,300)||null,
       app:document.getElementById('app')?.style.visibility||'',
       status:window.TakyCrewAudioAppEvidence?.status
     }));
     console.log('READY_DIAG '+JSON.stringify(before));
     await page.evaluate(()=>document.getElementById('takyCrewVoiceBtn')?.click());
   }else await page.locator(spec.button).click({force:true,timeout:9000});
   console.log('CLICK_DONE '+spec.app_id);
   await page.waitForFunction(()=>window.TakyCrewAudioAppEvidence?.last_result?.status==='PLAYING_STARTED',
      {timeout:15000}).catch(()=>{});
   const after=await page.evaluate(()=>({
      last:window.TakyCrewAudioAppEvidence?.last_result,
      buttonStatus:document.getElementById(window.TakyCrewAudioAppEvidence?.app_id==='SNAP_POP'?'homeRadio':'takyCrewVoiceBtn')
        ?.dataset.takyCrewAudioStatus
   }));
   result.route_key=after.last?.key||null;
   result.audio_playing=after.last?.status==='PLAYING_STARTED';
   result.playing_mode=after.last?.mode||null;
   result.ui_data_status=after.buttonStatus||null;
   if(after.last?.url){
      const response=await page.request.get('http://127.0.0.1:'+spec.port+'/'+after.last.url.replace(/^\.\//,''));
      result.url_200=response.status()===200;
      result.audio_bytes=(await response.body()).length;
   }
   report.tests.push(result);
  }catch(e){
   result.error=String(e);
   try{
    result.failure_dom=await context.pages()[0].evaluate(()=>({
      buttonExists:!!document.querySelector('#takyCrewVoiceBtn'),
      html:document.querySelector('#takyCrewVoiceBtn')?.outerHTML,
      bodyClass:document.body?.className,appVisibility:document.getElementById('app')?.style.visibility,
      readyBoot:document.documentElement?.dataset.readyBootState,
      canonicalState:localStorage.getItem('taky_explorer_crew_canonical_v1')?.slice(0,180),
      currentEvidence:window.TakyCrewAudioAppEvidence?.status
    }));
   }catch{}
   report.tests.push(result);
  }
  finally{console.log('CLEANING_APP '+spec.app_id);if(context)await context.close().catch(()=>{});server.closeAllConnections?.();await new Promise(r=>server.close(r));console.log('CLEANED_APP '+spec.app_id);}
 }
 report.status=report.tests.every(x=>x.initialized&&x.button_ready&&x.audio_playing&&
  x.playing_mode==='TTS_MOCK'&&x.url_200&&x.route_key?.includes(x.character_id))
  ?(report.tests.length===3?'PASS_THREE_ACTUAL_UI_EVENT_TO_WAV':'PASS_SINGLE_APP_UI_EVENT_TO_WAV'):'FAIL';
}finally{
 if(browser)await browser.close();
 writeFileSync('D:/Git PWA/TAKY/staging/crew_voice_20261012/EXPLORER_CREW_ACTUAL_APP_UI_WAV_SMOKE_20261013'+(process.env.TAKY_AUDIO_TEST_APP?'_'+process.env.TAKY_AUDIO_TEST_APP:'')+'.json',
   JSON.stringify(report,null,2),'utf8');
 console.log(JSON.stringify(report,null,2));
}
if(!report.status.startsWith('PASS_'))process.exitCode=2;
