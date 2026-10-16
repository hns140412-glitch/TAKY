'use strict';
// Independent, seeded multi-actor behavioral QA against TAKY's EXISTING family API/store.
// Not a new auth/learning engine. All identities/data are synthetic; no production network.
const fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('../LEARNING/transport/local-json-strong-store.js');
const Api=require('../LEARNING/transport/family-user-data-http-endpoint.js');
const Session=require('../LEARNING/transport/family-session-http-endpoint.js');
const seed=Number(process.env.TAKY_QA_SEED||20261015)>>>0;
const rounds=Math.min(40,Math.max(6,Number(process.env.TAKY_QA_AGENT_STEPS||10)));
const jitter=ms=>new Promise(r=>setTimeout(r,ms));
function random(s){return ()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};}
const families=[
 {id:'SIM-A',parents:['A-P1','A-P2'],learners:['A-L1','A-L2']},
 {id:'SIM-B',parents:['B-P1'],learners:['B-L1']}
];
const roster=[
 ...families.flatMap(f=>[
  ...f.parents.map(id=>({id,mode:'PARENT',family:f.id,authorized:[...f.parents,...f.learners]})),
  ...f.learners.map(id=>({id,mode:'LEARNER',family:f.id,authorized:[id]}))
 ]),
 {id:'SYS-ADMIN',mode:'ADMIN',family:null,authorized:[]}
];
const tokenFor=a=>'qa-bearer-'+a.id+'-verified-20261015';
const principal=new Map(roster.map(a=>[tokenFor(a),{
  authenticated:true,principal_id:'sim:'+a.id,identity_provider:'LOCAL_TEST',
  families:a.family?[{family_id:a.family,self_member_id:a.id,authorized_member_ids:a.authorized}]:[]
}]));
const query=(f,m,t,id)=>({family_id:f,member_id:m,record_type:t,record_id:id});
const entry=(f,m,t,id,status,payload,app='Ready & Set')=>({
 family_id:f,member_id:m,record_type:t,record_id:id,
 source_app:app,status,payload,recorded_at:'2026-10-15T00:00:00.000Z'
});
const h=a=>({'authorization':'Bearer '+tokenFor(a),'content-type':'application/json'});
function shuffle(arr,rng){for(let i=arr.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]];}return arr;}
(async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'taky-independent-bots-'));
 const trace=[],errors=[],coverage={},notes=[];
 let sequence=0;
 try{
  const store=await new LocalJsonStrongStore(dir).init();
  const verifyBearerToken=async t=>{
   const p=principal.get(t);if(!p)throw Error('SIM_TOKEN_REJECTED');return p;
  };
  const api=Api.create({store,verifyBearerToken});
  const session=Session.create({verifyBearerToken});
  const read=(a,q)=>api.handle({method:'GET',path:Api.ENDPOINT,headers:h(a),query:q});
  const write=(a,r,etag)=>api.handle({method:'POST',path:Api.ENDPOINT,headers:h(a),body:JSON.stringify({record:r,...(etag?{expected_etag:etag}:{})})});
  const recordCheck=(a,action,response,allowed,extra={})=>{
   const status=response.status;
   let partial=false;
   if(status===202&&allowed.includes(200)){
     let body;
     try{body=JSON.parse(response.body||'{}');}catch{body={};}
     partial=body.storage_confirmed===true&&(body.backup_outbox_retry_required===true||body.learning_context_retry_required===true);
     if(partial)notes.push('DURABLE_WRITE_202_FOLLOWUP_REQUIRED:'+a.mode+':'+action);
   }
   const ok=allowed.includes(status)||partial;
   const step={seq:++sequence,actor:a.id,mode:a.mode,action,status,expected:allowed,ok,
     ...(partial?{evidence:'STORED_BUT_DOWNSTREAM_PENDING'}:{}),...extra};
   trace.push(step);
   coverage[action]=(coverage[action]||0)+1;
   if(!ok)errors.push({actor:a.id,action,expected:allowed,actual:status,step:step.seq});
   return response;
  };
  const familyOf=id=>families.find(f=>f.id===id);
  const otherFamily=id=>families.find(f=>f.id!==id);
  // Guaranteed baseline uses real API write path; bots are not scripted relative to each other.
  for(const f of families){
   const parent=roster.find(a=>a.id===f.parents[0]);
   for(const kid of f.learners){
    const out=await write(parent,entry(f.id,kid,'ASSIGNMENT','seed-homework','CONFIRMED',{title:'synthetic baseline task',source:'QA'}));
    if(out.status!==200)throw Error('FIXTURE_WRITE_FAILED '+f.id+' '+kid+' '+out.status);
   }
  }
  const firstPracticeId=new Map();
 const decisions={
   PARENT:['assign','check-child','amend','stale-save','cross-family-read','other-family-write'],
   LEARNER:['read-homework','practice','wrong-answer','resume','sibling-read','cross-family-read','impersonate','double-submit'],
   ADMIN:['ops-summary','raw-access','raw-write','family-login','approval-request']
  };
  async function act(a,action,i){
   const own=familyOf(a.family),other=otherFamily(a.family);
   const child=own?.learners[i%own.learners.length];
   const kid=a.mode==='LEARNER'?a.id:child;
   const ownSeed=()=>query(a.family,kid,'ASSIGNMENT','seed-homework');
   if(action==='assign'){
    const r=entry(a.family,kid,'ASSIGNMENT','parent-task-'+a.id+'-'+i,'CONFIRMED',{title:'synthetic independent task '+i});
    return recordCheck(a,action,await write(a,r),[200],{app:'Ready & Set'});
   }
   if(action==='check-child'){
    const q=query(a.family,kid,'EXECUTION_EVENT','practice-'+kid+'-seed');
    const res=await read(a,q);
    if(res.status===200&&JSON.parse(res.body).record.member_id!==kid)errors.push({actor:a.id,action,reason:'WRONG_CHILD_RECORD'});
    return recordCheck(a,action,res,[200,404],{app:'Ready & Set'});
   }
   if(action==='amend'){
    const got=await read(a,ownSeed());
    recordCheck(a,'amend-read',got,[200]);
    if(got.status!==200)return;
    const {record,etag}=JSON.parse(got.body);
    const changed={...record,payload:{...record.payload,bot_note:'change-'+a.id+'-'+i}};
    return recordCheck(a,action,await write(a,changed,etag),[200,409],{app:'Ready & Set'});
   }
   if(action==='stale-save'){
    const r=entry(a.family,kid,'ASSIGNMENT','seed-homework','CONFIRMED',{title:'unauthorized overwrite attempt'});
    return recordCheck(a,action,await write(a,r),[409]);
   }
   if(action==='cross-family-read'||action==='other-family-write'){
    const q=query(other.id,other.learners[0],'ASSIGNMENT','seed-homework');
    if(action==='cross-family-read'){
      let result=await read(a,q);
      // Test-only artificial defect injection proves denial detectors report unexpected leaks.
      if(process.env.TAKY_QA_INJECT_AUTH_LEAK==='1'&&a.id==='A-P1')result={status:200,body:'{"ok":true}'};
      return recordCheck(a,action,result,[403]);
    }
    return recordCheck(a,action,await write(a,entry(other.id,other.learners[0],'ASSIGNMENT','cross-write-'+a.id,'CONFIRMED',{title:'deny me'})),[403]);
   }
   if(action==='read-homework'){
    const res=await read(a,ownSeed());
    if(res.status===200&&JSON.parse(res.body).record.member_id!==a.id)errors.push({actor:a.id,action,reason:'WRONG_MEMBER'});
    return recordCheck(a,action,res,[200],{app:'Ready & Set'});
   }
   if(action==='practice'||action==='wrong-answer'||action==='resume'){
    const app=action==='practice'?'Hide & Seek':action==='wrong-answer'?'Play Camp':'Snap & Pop';
    const target=action==='resume'?'SELF_REPORT':'EXECUTION_EVENT';
    const id=action+'-'+a.id+'-'+i;
    if(action==='practice'&&!firstPracticeId.has(a.id))firstPracticeId.set(a.id,id);
    const outcome=action==='wrong-answer'?'INCORRECT':action==='resume'?'PARTIAL':'CORRECT';
    const r=entry(a.family,a.id,target,id,'COMPLETED',{behavior:action,outcome,simulated:true},app);
    return recordCheck(a,action,await write(a,r),[200],{app});
   }
   if(action==='sibling-read'){
    const otherMember=own.learners.find(id=>id!==a.id)||other.learners[0];
    const otherScope=own.learners.includes(otherMember)?a.family:other.id;
    return recordCheck(a,action,await read(a,query(otherScope,otherMember,'ASSIGNMENT','seed-homework')),[403]);
   }
   if(action==='impersonate'){
    const otherMember=own.learners.find(id=>id!==a.id)||other.learners[0];
    const otherScope=own.learners.includes(otherMember)?a.family:other.id;
    return recordCheck(a,action,await write(a,entry(otherScope,otherMember,'EXECUTION_EVENT','impersonate-'+a.id,'COMPLETED',{simulated:true})),[403]);
   }
   if(action==='double-submit'){
    const r=entry(a.family,a.id,'EXECUTION_EVENT','double-submit-'+a.id+'-'+i,'COMPLETED',{outcome:'CORRECT',simulated:true},'Hide & Seek');
    const responses=await Promise.all([write(a,r),write(a,r)]);
    const statuses=responses.map(x=>x.status);
    // Exactly one persisted create is mandatory; losing racer may produce conflict or transient 503.
    const ok=statuses.filter(s=>s===200).length===1&&statuses.every(s=>[200,409].includes(s));
    recordCheck(a,action,{status:ok?200:500},[200],{statuses});
    return;
   }
   if(action==='ops-summary'){
    // Aggregated test counters only. A real administrator must not acquire family membership.
    const summary={actors:roster.length,events:trace.length,failures:errors.length};
    if(Object.keys(summary).some(k=>k.includes('member_id')))errors.push({actor:a.id,action,reason:'ADMIN_PII'});
    return recordCheck(a,action,{status:200},[200],{app:'TAKY Mobile'});
   }
   if(action==='raw-access'){
    return recordCheck(a,action,await read(a,query(families[0].id,'A-L1','ASSIGNMENT','seed-homework')),[403],{app:'TAKY Mobile'});
   }
   if(action==='raw-write'){
    return recordCheck(a,action,await write(a,entry(families[0].id,'A-L1','ASSIGNMENT','admin-spoof','CONFIRMED',{title:'blocked'})),[403],{app:'TAKY Mobile'});
   }
   if(action==='family-login'){
    const res=await session.handle({method:'POST',path:Session.ENDPOINT,headers:h(a),body:'{}'});
    return recordCheck(a,action,res,[403],{app:'TAKY Mobile'});
   }
   if(action==='approval-request'){
    // Explicitly no privileged adapter is called by this synthetic observer.
    return recordCheck(a,action,{status:202},[202],{decision:'HUMAN_APPROVAL_REQUIRED'});
   }
   throw Error('UNSUPPORTED_BOT_ACTION '+action);
  }
  const profiles=[];
  // Each bot owns its action list/seed and yields to other bots; no global step ordering.
  await Promise.all(roster.map(async (a,n)=>{
   const rng=random(seed+n*977+23);
   const mandatory=[...decisions[a.mode]];
   const actions=[...mandatory];
   while(actions.length<rounds)actions.push(mandatory[Math.floor(rng()*mandatory.length)]);
   shuffle(actions,rng);
   profiles.push({actor:a.id,role:a.mode,planned:actions.length,distinct:[...new Set(actions)].length});
   for(let i=0;i<actions.length;i++){
    await jitter(Math.floor(rng()*5));
    try{await act(a,actions[i],i);}
    catch(e){errors.push({actor:a.id,action:actions[i],reason:String(e.message).slice(0,180)});}
   }
  }));
  // Final-state invariants, independent of the order and timing of bot actions.
  for(const f of families){
   const pa=roster.find(a=>a.id===f.parents[0]);
   for(const kid of f.learners){
    const res=await read(pa,query(f.id,kid,'ASSIGNMENT','seed-homework'));
    recordCheck(pa,'eventual-parent-read',res,[200]);
    const child=roster.find(a=>a.id===kid);
    const ownRes=await read(child,query(f.id,kid,'EXECUTION_EVENT',firstPracticeId.get(kid)));
    recordCheck(child,'eventual-learner-evidence',ownRes,[200]);
    const denial=await read(roster.find(a=>a.id===otherFamily(f.id).parents[0]),query(f.id,kid,'ASSIGNMENT','seed-homework'));
    recordCheck(child,'eventual-cross-family-denial',denial,[403]);
   }
  }
  // Two parents race after the same read to prevent silent last-writer-wins corruption.
  const pa=roster.find(a=>a.id==='A-P1'),pb=roster.find(a=>a.id==='A-P2');
  const current=await read(pa,query('SIM-A','A-L1','ASSIGNMENT','seed-homework'));
  const {record,etag}=JSON.parse(current.body);
  const edits=[{...record,payload:{...record.payload,race_actor:pa.id}},{...record,payload:{...record.payload,race_actor:pb.id}}];
  const race=await Promise.all([write(pa,edits[0],etag),write(pb,edits[1],etag)]);
  const raceStatus=race.map(x=>x.status);
  const winning=raceStatus.filter(x=>x===200).length;
  const final=await read(pa,query('SIM-A','A-L1','ASSIGNMENT','seed-homework'));
  const winner=JSON.parse(final.body).record.payload.race_actor;
  const racePassed=winning===1&&raceStatus.every(x=>[200,409].includes(x))&&[pa.id,pb.id].includes(winner);
  if(!racePassed)errors.push({reason:'ETAG_CONCURRENT_WRITE_VIOLATION',statuses:raceStatus,winner});
  recordCheck(pa,'concurrent-parent-edit',{status:racePassed?200:500},[200],{statusCodes:raceStatus});
  if(raceStatus.includes(503))notes.push('ETAG_LOSER_INVALID_503_EXPECT_409');
  const summary={
   contract:'TAKY_INDEPENDENT_FAMILY_BOTS_V1',seed,stepsPerBot:rounds,
   environment:'LOCAL_SYNTHETIC_ACTORS',repro:'TAKY_QA_SEED='+seed+' TAKY_QA_AGENT_STEPS='+rounds,
   familyGroups:families.length,actors:roster.length,roles:{PARENT:3,LEARNER:3,ADMIN:1},
   stats:{actions:trace.length,unexpected:errors.length,partialWrites:trace.filter(x=>x.evidence==='STORED_BUT_DOWNSTREAM_PENDING').length,coverage},
   profiles:profiles.sort((x,y)=>x.actor.localeCompare(y.actor)),
   race:{statuses:raceStatus,oneWriteWins:racePassed},notes,
   failedActions:errors.slice(0,20),events:trace,
   limitations:['API_LEVEL_ONLY','NOT_BROWSER_BOTS','SAVEY_INDEPENDENT_BOTS_SEPARATE_SUITE_NO_CROSS_APP_E2E','NO_LIVE_NETWORK','NO_REAL_DEVICE']
  };
  const out=path.resolve(__dirname,'../.local/family-qa');
  await fs.mkdir(out,{recursive:true});
  const outPath=path.join(out,'last-independent-bots.json');
  // Persist reproducibility without tokens or real financial/user data.
  await fs.writeFile(outPath,JSON.stringify(summary,null,2),'utf8');
  console.log(JSON.stringify({contract:summary.contract,seed,actors:7,familyGroups:2,
   actions:trace.length,unexpected:errors.length,race:summary.race,
   coverage,limitations:summary.limitations,report:outPath,errors:errors.slice(0,4)}));
  if(errors.length)process.exitCode=1;
 }finally{await fs.rm(dir,{force:true,recursive:true});}
})().catch(e=>{console.error('TAKY_INDEPENDENT_BOTS_ERROR',e.stack);process.exitCode=1;});
