'use strict';
// Local Windows Task Scheduler registration for TAKY family QA.
// One-off Node jobs. No resident shell, no push, no deploy, no API.
const {spawnSync}=require('node:child_process');
const path=require('node:path');
const runner=path.resolve(__dirname,'family_group_periodic_qa.cjs');
const program='"'+process.execPath+'"';
const jobs=[
 {name:'TAKY_FAMILY_QA_DAILY',type:'DAILY',time:'20:30',command:program+' "'+runner+'"'},
 {name:'TAKY_FAMILY_QA_WEEKLY_DEEP',type:'WEEKLY',day:'SUN',time:'21:00',command:program+' "'+runner+'" --deep'}
];
const results=[];
for(const job of jobs){
 const args=['/create','/f','/tn',job.name,'/sc',job.type,'/st',job.time];
 if(job.day)args.push('/d',job.day);
 args.push('/tr',job.command);
 const cmd=spawnSync('schtasks.exe',args,{encoding:'utf8',windowsHide:true,timeout:10000});
 const success=cmd.status===0;
 const verify=success?spawnSync('schtasks.exe',['/query','/tn',job.name,'/fo','LIST'],{
   encoding:'utf8',windowsHide:true,timeout:10000
 }):null;
 results.push({task:job.name,success,verified:verify?.status===0,schedule:job.type+' '+(job.day||'EVERYDAY')+' '+job.time,
  failure:success?undefined:String(cmd.stderr||cmd.stdout||cmd.error?.message).slice(0,400)});
}
console.log(JSON.stringify({contract:'TAKY_FAMILY_QA_LOCAL_SCHEDULE_V1',results}));
if(results.some(x=>!x.success||!x.verified))process.exitCode=1;
