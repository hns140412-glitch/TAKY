'use strict';
// Watchdog for resource-bounded independent local-browser QA. Windows tree-kill on timeout.
const fs=require('node:fs'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');
const specialist=process.argv.includes('--specialists');
const target=path.join(__dirname,specialist?'family_group_specialist_browser_qa.cjs':'family_group_independent_browser_qa.cjs');
const safe=specialist?'SPECIALISTS':process.argv.includes('--ready-probe')?'READY':process.argv.includes('--all')?'ALL':'SAFE';
const timeoutMs=safe==='READY'?22000:safe==='SPECIALISTS'?22000:safe==='ALL'?46000:30000;
const env={...process.env,
 TAKY_QA_BROWSER_SKIP_READY:safe==='SAFE'?'1':'0',
 TAKY_QA_BROWSER_READY_ONLY:safe==='READY'?'1':'0',
 TAKY_QA_BROWSER_ACTORS:safe==='READY'?'A-P1':undefined,
 TAKY_QA_BROWSER_STEPS:safe==='READY'?'2':'3',
 TAKY_QA_BROWSER_TRACE:'1'};
const started=new Date().toISOString();
let output='',killed=false;
const proc=spawn(process.execPath,[target],{cwd:path.resolve(__dirname,'..'),windowsHide:true,env,stdio:['ignore','pipe','pipe']});
const append=(stream,label)=>stream.on('data',chunk=>{
 const s=String(chunk);output=(output+s).slice(-10000);
 process.stdout.write(s);
});
append(proc.stdout,'stdout');append(proc.stderr,'stderr');
function killTree(pid){
 if(process.platform==='win32')spawnSync('taskkill.exe',['/PID',String(pid),'/T','/F'],{windowsHide:true,timeout:4500,encoding:'utf8'});
 else try{process.kill(pid,'SIGKILL');}catch{}
}
const timer=setTimeout(()=>{killed=true;console.error('TAKY_BROWSER_WATCHDOG_TIMEOUT mode='+safe+' lastLog='+output.slice(-450));killTree(proc.pid);},timeoutMs);
proc.on('error',e=>{clearTimeout(timer);console.error('TAKY_BROWSER_WATCHDOG_SPAWN_ERROR '+e.message);process.exitCode=3;});
proc.on('exit',(code,signal)=>{
 clearTimeout(timer);
 const report={contract:'TAKY_BROWSER_WATCHDOG_V1',mode:safe,startedAt:started,finishedAt:new Date().toISOString(),
  elapsedLimitMs:timeoutMs,pass:!killed&&code===0,exitCode:code,timeout:killed,
  lastProgress:output.split(/\r?\n/).filter(x=>x.startsWith('BOT_STEP ')).slice(-6)};
 const dir=path.resolve(__dirname,'../.local/family-qa/browser');fs.mkdirSync(dir,{recursive:true});
 fs.writeFileSync(path.join(dir,'watchdog-'+safe.toLowerCase()+'.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
 process.exitCode=report.pass?0:1;
});
