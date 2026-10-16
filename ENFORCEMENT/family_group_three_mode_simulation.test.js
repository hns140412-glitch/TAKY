'use strict';
// Simulation-only: verified TAKY family boundaries, two synthetic families, no live accounts.
// Uses the EXISTING identity resolver, HTTP endpoint, and durable-store implementation.
const assert=require('node:assert/strict');
const fsp=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const Session=require('../LEARNING/transport/family-session-http-endpoint.js');
const Data=require('../LEARNING/transport/family-user-data-http-endpoint.js');
const {LocalJsonStrongStore}=require('../LEARNING/transport/local-json-strong-store.js');

const familyA='SIM-FAMILY-A', familyB='SIM-FAMILY-B';
const actors=[
  {id:'parent-a1',mode:'PARENT',family:familyA,members:['parent-a1','parent-a2','learner-a1','learner-a2']},
  {id:'parent-a2',mode:'PARENT',family:familyA,members:['parent-a1','parent-a2','learner-a1','learner-a2']},
  {id:'learner-a1',mode:'LEARNER',family:familyA,members:['learner-a1']},
  {id:'learner-a2',mode:'LEARNER',family:familyA,members:['learner-a2']},
  {id:'parent-b1',mode:'PARENT',family:familyB,members:['parent-b1','learner-b1']},
  {id:'learner-b1',mode:'LEARNER',family:familyB,members:['learner-b1']},
  {id:'admin',mode:'ADMIN',family:null,members:[]}
];
const principals=new Map(actors.map(a=>[
  'sim-verified-'+a.id+'-token', {
    authenticated:true,principal_id:'sim:'+a.id,identity_provider:'SIMULATED_VERIFIED_SESSION',
    families:a.family?[{family_id:a.family,self_member_id:a.id,authorized_member_ids:a.members}]:[]
  }
]));
const bearer=id=>'sim-verified-'+id+'-token';
const headers=id=>({'content-type':'application/json',authorization:'Bearer '+bearer(id)});
const query=(family_id,member_id,record_type,record_id)=>({family_id,member_id,record_type,record_id});
const record=(family_id,member_id,record_type,record_id,source_app,status,payload)=>({
 family_id,member_id,record_type,record_id,source_app,status,payload,
 recorded_at:'2026-10-15T00:00:00.000Z'
});
const check=(response,status,label)=>assert.equal(response.status,status,label+': '+response.body);

(async()=>{
  const root=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-family-sim-'));
  const checks={passed:0,denied:0,conflicts:0};
  try{
    const store=await new LocalJsonStrongStore(root).init();
    const verifyBearerToken=async token=>{
      const p=principals.get(token);
      if(!p)throw new Error('UNAUTHORIZED_TEST_TOKEN');
      return p;
    };
    const session=Session.create({verifyBearerToken});
    const data=Data.create({store,verifyBearerToken});
    const login=id=>session.handle({
      method:'POST',path:Session.ENDPOINT,headers:headers(id),body:'{}'
    });
    const write=(actor,r,etag)=>data.handle({
      method:'POST',path:Data.ENDPOINT,headers:headers(actor),
      body:JSON.stringify({record:r,...(etag?{expected_etag:etag}:{})})
    });
    const read=(actor,q)=>data.handle({
      method:'GET',path:Data.ENDPOINT,headers:headers(actor),query:q
    });
    for(const actor of actors.filter(a=>a.mode!=='ADMIN')){
      const response=await login(actor.id);
      check(response,200,'family login '+actor.id);
      const entry=JSON.parse(response.body).session.families[0];
      assert.equal(entry.family_id,actor.family);
      assert.ok(entry.authorized_member_ids.includes(actor.id));
      checks.passed++;
    }
    check(await login('admin'),403,'global administrator is not family member');checks.denied++;
    check(await read('admin',query(familyA,'learner-a1','ASSIGNMENT','vocab-01')),403,'admin cannot read raw family records');checks.denied++;

    // Parent assigns within their verified family; both parent and learner read same stable record.
    const task=record(familyA,'learner-a1','ASSIGNMENT','vocab-01','Ready & Set','CONFIRMED',
      {title:'12 vocabulary words',app:'Hide & Seek',source:'synthetic'});
    const assigned=await write('parent-a1',task);
    check(assigned,200,'parent assignment');checks.passed++;
    const etag=JSON.parse(assigned.body).etag;
    const learnerTask=await read('learner-a1',query(familyA,'learner-a1','ASSIGNMENT','vocab-01'));
    check(learnerTask,200,'learner sees parent assignment');checks.passed++;
    assert.deepEqual(JSON.parse(learnerTask.body).record.payload,task.payload);

    // Learner's completion is scoped to own member_id, not display name or app-local id.
    const evidence=record(familyA,'learner-a1','EXECUTION_EVENT','hide-01','Hide & Seek','COMPLETED',
      {task_id:'vocab-01',correct:9,questions:12,kind:'synthetic_learning_run'});
    check(await write('learner-a1',evidence),200,'learner completes own session');checks.passed++;
    const parentView=await read('parent-a2',query(familyA,'learner-a1','EXECUTION_EVENT','hide-01'));
    check(parentView,200,'second parent sees same learner outcome');checks.passed++;
    assert.equal(JSON.parse(parentView.body).record.payload.correct,9);
    const play=record(familyA,'learner-a2','LEARNING_ARTIFACT','play-01','Play Camp','COMPLETED',
      {exercise:'hangul sound',correct:4,questions:5,kind:'synthetic'});
    check(await write('learner-a2',play),200,'second learner learns independently');checks.passed++;
    check(await read('parent-a1',query(familyA,'learner-a2','LEARNING_ARTIFACT','play-01')),200,'parent sees second learner');checks.passed++;

    const snap=record(familyB,'learner-b1','SELF_REPORT','snap-01','Snap & Pop','CONFIRMED',
      {kind:'synthetic_exploration',activity:'expression task'});
    check(await write('learner-b1',snap),200,'second family learning record');checks.passed++;
    check(await read('parent-b1',query(familyB,'learner-b1','SELF_REPORT','snap-01')),200,'parent B reads own family');checks.passed++;

    for(const [actor,q,label] of [
      ['learner-a1',query(familyA,'learner-a2','LEARNING_ARTIFACT','play-01'),'sibling A1 cannot see A2'],
      ['learner-a2',query(familyA,'learner-a1','EXECUTION_EVENT','hide-01'),'sibling A2 cannot see A1'],
      ['parent-b1',query(familyA,'learner-a1','ASSIGNMENT','vocab-01'),'cross-family parent B cannot read A'],
      ['parent-a1',query(familyB,'learner-b1','SELF_REPORT','snap-01'),'cross-family parent A cannot read B'],
      ['learner-b1',query(familyA,'learner-a1','ASSIGNMENT','vocab-01'),'cross-family learner cannot read A']
    ]){
      check(await read(actor,q),403,label);checks.denied++;
    }
    check(await write('learner-a1',record(familyA,'learner-a2','EXECUTION_EVENT','spoof-01','Ready & Set','COMPLETED',{result:'spoof'})),403,'learner cannot write sibling');
    checks.denied++;
    check(await write('parent-a1',record(familyB,'learner-b1','ASSIGNMENT','spoof-02','Ready & Set','CONFIRMED',{title:'cross family'})),403,'parent cannot write other family');
    checks.denied++;
    check(await write('admin',task),403,'administrator cannot bypass family permission');
    checks.denied++;

    check(await write('parent-a1',task),409,'no silent overwrite without ETag');
    checks.conflicts++;
    const updated={...task,status:'COMPLETED'};
    check(await write('parent-a1',updated,etag),200,'ETag protects legitimate completion');
    checks.passed++;
    check(await write('parent-a1',task,etag),409,'stale ETag rejected');
    checks.conflicts++;

    // Admin receives only synthetic QA aggregates, never names, assignment text or finance records.
    const report={
      contract:'TAKY_FAMILY_GROUP_3_MODE_SIMULATION_V1',
      environment:'LOCAL_SYNTHETIC_ONLY',
      familyGroups:2,parentActors:3,learnerActors:3,adminActors:1,
      modes:['PARENT','LEARNER','ADMIN'],checks,
      gates:{
        familyIsolation:'PASS',siblingIsolation:'PASS',parentChildLink:'PASS',
        adminRawAccess:'DENIED',optimisticConcurrency:'PASS',
        saveyFinanceAuthority:'SEPARATE_SAVEY_TEST_SUITE',
        productionUI:'NOT_TESTED',realDevice:'NOT_TESTED',liveAccounts:'NOT_USED'
      }
    };
    assert.equal(JSON.stringify(report).includes('12 vocabulary words'),false);
    assert.equal(JSON.stringify(report).includes('learner-a1'),false);
    console.log(JSON.stringify(report));
  }finally{await fsp.rm(root,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
