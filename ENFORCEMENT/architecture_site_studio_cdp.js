const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{spawn,spawnSync}=require('node:child_process');
const chrome=process.env.TAKY_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const [url,widthRaw='1440',heightRaw='1000']=process.argv.slice(2);
if(!url || !/^(file|http):/.test(url)) {console.error('Valid file or loopback URL required');process.exit(2)}
if(url.startsWith('http:') && !/^http:\/\/127\.0\.0\.1(:\d+)?\//.test(url)){console.error('Only loopback HTTP allowed');process.exit(2)}
const width=Number(widthRaw),height=Number(heightRaw);
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
// Transient profile lifecycle: only the exact dir created here is removed, after the child tree exits.
// A caller-supplied TAKY_CDP_PROFILE stays owned (and verified) by that caller.
function killOrphans(profile){
 if(process.platform!=='win32')return;
 spawnSync('powershell',['-NoProfile','-NonInteractive','-Command',"Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($env:TAKY_PROFILE) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],{windowsHide:true,stdio:'ignore',timeout:30000,env:{...process.env,TAKY_PROFILE:profile}});
}
async function teardown(child,exited,profile,owned){
 const problems=[];
 if(child.pid&&child.exitCode===null&&child.signalCode===null){
  if(process.platform==='win32')spawnSync('taskkill',['/F','/T','/PID',String(child.pid)],{windowsHide:true,stdio:'ignore'});else child.kill('SIGKILL');
  await Promise.race([exited,pause(5000)]);
  if(child.exitCode===null&&child.signalCode===null)problems.push('chrome pid '+child.pid+' did not exit within 5s');
 }
 if(!owned)return problems;
 let last='';
 for(let attempt=0;attempt<10&&fs.existsSync(profile);attempt++){
  try{fs.rmSync(profile,{recursive:true,force:true,maxRetries:3,retryDelay:100})}catch(e){last=e.code||'error'}
  if(fs.existsSync(profile)){if(attempt===2)killOrphans(profile);await pause(250)}
 }
 if(fs.existsSync(profile))problems.push('profile '+path.basename(profile)+' still present after retries ('+(last||'unknown')+')');
 return problems;
}
async function main(){
 const owned=!process.env.TAKY_CDP_PROFILE;
 const profile=owned?fs.mkdtempSync(path.join(os.tmpdir(),'taky_chrome_cdp_')):process.env.TAKY_CDP_PROFILE;
 let child={pid:0,exitCode:0,signalCode:null},exited=Promise.resolve(),spawnError;
 let ws;
 try{
  child=spawn(chrome,['--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--no-default-browser-check','--remote-allow-origins=*','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
  exited=new Promise(resolve=>child.once('exit',resolve));child.once('error',e=>{spawnError=e});
  let port; const pf=path.join(profile,'DevToolsActivePort');
  for(let i=0;i<80;i++){if(spawnError)throw Error('Chrome launch failed: '+(spawnError.code||spawnError.message));if(child.exitCode!==null)throw Error('Chrome exited early (code '+child.exitCode+')');if(fs.existsSync(pf)){port=Number(fs.readFileSync(pf,'utf8').split(/\r?\n/)[0]);break}await pause(100)}
  if(!port)throw Error('Chrome DevTools startup timeout');
  const tabs=await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();
  const tab=tabs.find(t=>t.type==='page');if(!tab)throw Error('No browser page');
  ws=new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});
  const pending=new Map();let id=0;
  ws.addEventListener('message',e=>{const v=JSON.parse(e.data);if(v.id&&pending.has(v.id)){const p=pending.get(v.id);pending.delete(v.id);v.error?p.reject(Error(v.error.message)):p.resolve(v.result)}});
  const command=(method,params={})=>new Promise((resolve,reject)=>{
    const k=++id; pending.set(k,{resolve,reject});ws.send(JSON.stringify({id:k,method,params}));setTimeout(()=>{if(pending.has(k)){pending.delete(k);reject(Error(method+' timeout'))}},10000)
  });
  await command('Page.enable');await command('Runtime.enable');
  await command('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<650,screenWidth:width,screenHeight:height});
  await command('Page.navigate',{url});
  const testMode=url.includes('selftest=1');
  let result='';
  for(let i=0;i<50;i++){
    await pause(120);
    const expression=`(()=>{if(${testMode}&&!document.getElementById('selftest-result'))return '';document.querySelectorAll('input[type=radio],input[type=checkbox]').forEach(e=>{if(e.checked)e.setAttribute('checked','checked');else e.removeAttribute('checked')});return document.documentElement.outerHTML})()`;
    const obj=await command('Runtime.evaluate',{expression,returnByValue:true});
    result=obj.result?.value||'';if(result.length>100)break;
  }
  if(!result.includes('site-analysis')&&!result.includes('ARCHI GROW'))throw Error('HTML page failed to render');
  if(testMode&&!result.includes('selftest-result'))throw Error('UI selftest did not finish');
  process.stdout.write(result);
 }finally{
  if(ws)ws.close();
  const problems=await teardown(child,exited,profile,owned);
  if(problems.length){console.error('CDP_PROFILE_LEAK HOLD '+problems.join('; '));process.exitCode=4}
 }
}
main().catch(e=>{console.error('CDP_UI_ERROR '+e.message);process.exitCode=process.exitCode||1});
