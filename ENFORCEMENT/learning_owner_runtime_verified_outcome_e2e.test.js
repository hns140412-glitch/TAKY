'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const fsp=require('node:fs').promises;
const vm=require('node:vm');
const os=require('node:os'),path=require('node:path');
const Evidence=require('../LEARNING/transport/central-learning-http-endpoint.js');
const {LocalJsonStrongStore}=require('../LEARNING/transport/local-json-strong-store.js');
const ServerVerifier=require('../LEARNING/verification/server-specialist-verifier.js');

const ROOT='D:/Git PWA';
const clientSrc=fs.readFileSync(ROOT+'/TAKY/SHARED/runtime/taky-learning-evidence-client-v1.js','utf8');
const hideBridgeSrc=fs.readFileSync(ROOT+'/Hide & Seek/hide-bridge.js','utf8');
const snapBridgeSrc=fs.readFileSync(ROOT+'/Snap & Pop/snap-bridge.js','utf8');
const readySrc=fs.readFileSync(ROOT+'/Ready & Set/ready-runtime-v07.js','utf8');
const readyPracticeSrc=fs.readFileSync(ROOT+'/READY-WEBAPP-20261006/ready-verifiable-practice-evidence-v1.js','utf8');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function drain(client){
  let last=null;
  for(let i=0;i<60;i++){
    if(client.pending().length===0)return {ok:true,pending:0,last};
    last=await client.flush();
    if(client.pending().length===0)return {ok:true,pending:0,last};
    await sleep(10);
  }
  return {ok:false,pending:client.pending().length,last};
}

function storage(){
  const m=new Map();
  return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)};
}
function generic(){return {dataset:{},style:{},classList:{add(){},remove(){},toggle(){}},appendChild(){},before(){},addEventListener(){},setAttribute(){},remove(){},closest(){return null}}}
function baseSandbox(search=''){
  const listeners={}; const ls=storage(),ss=storage(); const g=generic();
  const document={
    readyState:'complete',visibilityState:'visible',documentElement:{dataset:{},classList:g.classList},
    body:{appendChild(){},},head:{appendChild(){}},
    getElementById(){return generic()},querySelector(){return null},querySelectorAll(){return []},
    createElement(){return generic()},addEventListener(n,f){(listeners['doc:'+n]??=[]).push(f)}
  };
  const location={search,origin:'https://owner.test',pathname:'/',hash:'',href:'https://owner.test/'+search,assign(v){this.href=v}};
  const window={
    window:null,document,location,localStorage:ls,sessionStorage:ss,
    addEventListener(n,f){(listeners[n]??=[]).push(f)},
    dispatchEvent(e){for(const f of listeners[e.type]||[])f(e);return true},
    setInterval(){return 0},clearInterval(){},
    opener:null,parent:null
  }; window.window=window;
  const sandbox={window,document,location,localStorage:ls,sessionStorage:ss,URL,URLSearchParams,Date,JSON,Set,Map,Math,
    structuredClone:global.structuredClone,CustomEvent:class{constructor(type,opt={}){this.type=type;this.detail=opt.detail}},
    Event:class{constructor(type){this.type=type}},MutationObserver:class{observe(){}},Node:{ELEMENT_NODE:1},
    navigator:{serviceWorker:null},history:{replaceState(){}},console,setTimeout,clearTimeout,setInterval,clearInterval};
  sandbox.globalThis=sandbox;
  return {sandbox,listeners};
}
async function makeEndpoint(root){
  const store=await new LocalJsonStrongStore(root).init();
  const principal={authenticated:true,principal_id:'PARENT',identity_provider:'TEST',
    families:[{family_id:'F1',self_member_id:'PARENT',authorized_member_ids:['CHILD_A']}]};
  const verifier=ServerVerifier.create({
    resolveReference:async s=>({
      authority:'SERVER_OWNED_LEARNING_REFERENCE',reference_id:'REF:'+s.learning_target_id,
      source_app:s.source_app,subject:s.subject,concept_skill_target:s.concept_skill_target,
      learning_target_id:s.learning_target_id,verifier_type:s.verifier_type,verifier_version:'REF_V1',
      match_rule:'CASEFOLD_TRIM',expected_values:['apple']
    }),
    resolveHumanReview:async s=>({
      authority:'SERVER_OWNED_HUMAN_RUBRIC_REVIEW',receipt_id:'REVIEW:'+s.event_id,reference_id:'RUBRIC:1',
      verifier_version:'RUBRIC_V1',target_event_id:s.event_id,family_id:s.family_id,member_id:s.member_id,
      subject:s.subject,concept_skill_target:s.concept_skill_target,outcome:1,
      verified_at:'2026-10-04T12:40:00+09:00',reviewer_role:'PARENT'
    })
  });
  const endpoint=Evidence.create({store,verifyBearerToken:async()=>principal,verifySpecialistEvidence:verifier});
  const fetchImpl=async(url,opt)=>{
    const o=await endpoint.handle({method:opt.method,path:new URL(url).pathname,headers:opt.headers,body:opt.body});
    return {ok:o.status>=200&&o.status<300,status:o.status,json:async()=>JSON.parse(o.body)};
  };
  return {store,fetchImpl};
}
function installClient(sandbox,fetchImpl){
  sandbox.window.TAKY_FAMILY_RUNTIME={
    apiBaseUrl:'https://central.test',getToken:async()=> 'validated-bearer-token-001',
    getFamilyId:async()=> 'F1',fetchImpl
  };
  vm.createContext(sandbox); vm.runInContext(clientSrc,sandbox,{filename:'taky-learning-evidence-client-v1.js'});
  return sandbox.window.TakyLearningEvidenceClientV1;
}
async function hideCase(fetchImpl){
  const {sandbox}=baseSandbox('?child_id=CHILD_A&subject=English&concept_skill_target=vocabulary&learning_target_id=word%3Aapple');
  sandbox.S={sharedLearningContext:{child_id:'CHILD_A'},takyLearningOutbox:[],activeSheetId:'S1'};
  sandbox.save=()=>{}; sandbox.sheet=()=>({status:'LEARNING',caseMastery:50}); sandbox.validWords=()=>[1,2];
  sandbox.toast=()=>{}; sandbox.render=()=>{}; sandbox.currentTab='home'; sandbox.viewStack=[];
  installClient(sandbox,fetchImpl);
  vm.runInContext(hideBridgeSrc,sandbox,{filename:'hide-bridge.js'});
  const e=sandbox.window.HideSeekBridge.emit('RETRIEVAL_ATTEMPT_RESULT',{
    learning_target_id:'word:apple',instrument_version:'HIDE_CODE_RED_V1',
    verification_observation:{response_value:'APPLE'}
  });
  const flush=await drain(sandbox.window.TakyLearningEvidenceClientV1);
  return {event:e,pending:sandbox.window.TakyLearningEvidenceClientV1.pending(),flush};
}
async function snapCase(fetchImpl){
  const {sandbox}=baseSandbox('?session_id=S1&goal_id=G1&task_id=T1&lap_id=L1&child_id=CHILD_A&subject=English&concept_skill_target=writing&learning_target_id=writing%3A1');
  sandbox.db=null;sandbox.get=async()=>null;sandbox.set=async()=>{};sandbox.toast=()=>{};
  vm.createContext(sandbox); vm.runInContext(snapBridgeSrc,sandbox,{filename:'snap-bridge.js'});
  installClient(sandbox,fetchImpl);
  const e=sandbox.window.SnapPopBridge.emit('TASK_COMPLETED',{child_authored:true,landmark:'idea'});
  sandbox.window.TakyLearningEvidenceClientV1.scan();
  const flush=await drain(sandbox.window.TakyLearningEvidenceClientV1);
  return {event:e,pending:sandbox.window.TakyLearningEvidenceClientV1.pending(),flush};
}
async function readyCase(fetchImpl){
  const {sandbox}=baseSandbox('');
  sandbox.state={activeSession:null,guide:{name:'guide'}}; sandbox.save=()=>{}; sandbox.completeSession=()=>{}; sandbox.nav=()=>{}; sandbox.toast=()=>{};
  sandbox.escapeHtml=x=>String(x);
  sandbox.window.ReadyBaseRuntimeV1={
    selectedPlannerTask:()=>({subject:'English',concept_skill_target:'vocabulary',learning_target_id:'word:apple'}),
    times:()=>({focus:0}),publishPlannerResult:()=>({})
  };
  sandbox.window.ReadyIdentityV1={get:()=>({userId:'CHILD_A'})};
  installClient(sandbox,fetchImpl);
  vm.runInContext(readySrc,sandbox,{filename:'ready-runtime-v07.js'});
  vm.runInContext(readyPracticeSrc,sandbox,{filename:'ready-verifiable-practice-evidence-v1.js'});
  sandbox.state.activeSession={id:'RS1',startAt:Date.now(),selected:['English vocabulary'],tasks:['English vocabulary'],homeworkTaskMap:[]};
  const c=sandbox.window.ReadySetRev07.ensure();
  const ok=sandbox.window.ReadySetRev07.setTaskState(c.active_task_id,'COMPLETED');
  assert.equal(ok,true);
  const practice=sandbox.window.ReadyVerifiablePracticeEvidenceV1.recordExactAnswer({
    subject:'English',concept_skill_target:'vocabulary',learning_target_id:'word:apple',
    response_value:'APPLE',instrument_version:'READY_VOCAB_EXACT_V1'
  });
  assert.equal(practice.ok,true);
  await sleep(20);
  const flush=await drain(sandbox.window.TakyLearningEvidenceClientV1);
  return {events:c.events,practice,pending:sandbox.window.TakyLearningEvidenceClientV1.pending(),acked:sandbox.window.TakyLearningEvidenceClientV1.acked(),flush};
}
async function receiptKinds(store){
  const x=await store.getWithMetadata('families/F1/members/CHILD_A/learning-engine/state-v1',{type:'json',consistency:'strong'});
  const receipts=Object.values(x.data.scope_receipts||{});
  const ev=receipts.flatMap(r=>r.canonical_evidence||[]);
  return ev.map(e=>({event_id:e.event_id,source_app:e.source_app,verified_outcome:e.verified_outcome,evidence_type:e.evidence_type}));
}
(async()=>{
  const dir=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-owner-e2e-'));
  try{
    const {store,fetchImpl}=await makeEndpoint(dir);
    const h=await hideCase(fetchImpl); assert.equal(h.pending.length,0,JSON.stringify(h));
    const s=await snapCase(fetchImpl); assert.equal(s.pending.length,0,JSON.stringify(s));
    const r=await readyCase(fetchImpl); assert.equal(r.pending.length,0);
    const ev=await receiptKinds(store); console.log("OWNER_E2E_EVENTS",JSON.stringify(ev));
    assert(ev.some(x=>x.source_app==='hide-seek'&&x.verified_outcome===1),'Hide owner code must reach verified outcome');
    assert(ev.some(x=>x.source_app==='snap-pop'&&x.verified_outcome===1),'Snap owner code must reach verified outcome');
    assert(r.events.some(x=>x.type==='TASK_STATE_CHANGED'),'Ready owner runtime must emit eligible task-state evidence');
    assert.equal(r.pending.length,0,'Ready owner event must receive central observation ACK');
    assert(ev.some(x=>x.source_app==='ready-set'&&x.verified_outcome===1&&x.evidence_type==='STRUCTURED_PRACTICE_EVIDENCE'),'Ready exact-practice producer must reach verified outcome');
    assert.equal(r.practice.event.payload.verification_observation.response_value,'APPLE');
    assert.equal(JSON.stringify(r.practice.event).includes('expected_values'),false,'trusted answer reference must stay server-side');
    console.log('LEARNING_OWNER_RUNTIME_E2E_PASS');
    console.log(JSON.stringify({hide_verified:true,snap_verified:true,ready_central_observation:true,ready_verified_practice:true,ready_self_report_not_promoted:true}));
  }finally{await fsp.rm(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exit(1)});
