'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

const ROOT='D:/Git PWA';
const readySrc=fs.readFileSync(ROOT+'/Ready & Set/ready-runtime-v07.js','utf8');
const hideSrc=fs.readFileSync(ROOT+'/Hide & Seek/hide-bridge.js','utf8');
const snapSrc=fs.readFileSync(ROOT+'/Snap & Pop/snap-bridge.js','utf8');

function storage(){
  const m=new Map();
  return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k),dump:()=>Object.fromEntries(m)};
}
function generic(){return {dataset:{},style:{},classList:{add(){},remove(){},toggle(){}},appendChild(){},before(){},addEventListener(){},setAttribute(){},remove(){},closest(){return null},hidden:false,textContent:'',innerHTML:''}}
function sandboxBase(url){
  const u=new URL(url),listeners={},ls=storage(),ss=storage();
  const document={
    readyState:'complete',documentElement:{dataset:{},classList:generic().classList},
    body:{appendChild(){}},head:{appendChild(){}},
    getElementById(){return generic()},querySelector(){return null},querySelectorAll(){return []},
    createElement(){return generic()},addEventListener(n,f){(listeners['doc:'+n]??=[]).push(f)}
  };
  const location={
    href:u.href,origin:u.origin,pathname:u.pathname,search:u.search,hash:u.hash,
    assign(v){const n=new URL(v,this.href);this.href=n.href;this.origin=n.origin;this.pathname=n.pathname;this.search=n.search;this.hash=n.hash}
  };
  const history={replaceState(_a,_b,v){if(v){const n=new URL(v,location.href);location.href=n.href;location.origin=n.origin;location.pathname=n.pathname;location.search=n.search;location.hash=n.hash}}};
  const window={
    window:null,document,location,localStorage:ls,sessionStorage:ss,history,
    addEventListener(n,f){(listeners[n]??=[]).push(f)},
    dispatchEvent(e){for(const f of listeners[e.type]||[])f(e);return true},
    setInterval(){return 0},clearInterval(){},opener:null,parent:null
  };
  window.window=window;
  const sandbox={window,document,location,localStorage:ls,sessionStorage:ss,history,URL,URLSearchParams,Date,JSON,Set,Map,Math,
    structuredClone:global.structuredClone,CustomEvent:class{constructor(type,opt={}){this.type=type;this.detail=opt.detail}},
    Event:class{constructor(type){this.type=type}},MutationObserver:class{observe(){}},Node:{ELEMENT_NODE:1},
    navigator:{},console,setTimeout,clearTimeout,setInterval,clearInterval};
  sandbox.globalThis=sandbox;
  return {sandbox,listeners};
}
function bootReady(){
  const {sandbox,listeners}=sandboxBase('https://ready.test/');
  sandbox.state={activeSession:null,guide:{name:'guide'}};
  sandbox.save=()=>{}; sandbox.completeSession=()=>{}; sandbox.nav=()=>{}; sandbox.toast=()=>{}; sandbox.escapeHtml=x=>String(x);
  sandbox.window.ReadyBaseRuntimeV1={
    selectedPlannerTask:()=>({subject:'English',concept_skill_target:'vocabulary',learning_target_id:'word:apple'}),
    times:()=>({focus:120000}),publishPlannerResult:()=>({})
  };
  sandbox.window.ReadyIdentityV1={get:()=>({userId:'CHILD_A'})};
  vm.createContext(sandbox); vm.runInContext(readySrc,sandbox,{filename:'ready-runtime-v07.js'});
  sandbox.state.activeSession={
    id:'READY-SESSION-1',startAt:100000,targetMs:1500000,targetAt:1600000,
    pausedAt:null,pausedMs:0,issueMs:0,continuity:{intervals:[]},
    selected:['English vocabulary'],tasks:['English vocabulary'],homeworkTaskMap:[]
  };
  const c=sandbox.window.ReadySetRev07.ensure();
  return {sandbox,listeners,contract:c};
}
function bootHide(url){
  const {sandbox}=sandboxBase(url);
  sandbox.S={sharedLearningContext:{},takyLearningOutbox:[],activeSheetId:'S1'};
  sandbox.save=()=>{}; sandbox.sheet=()=>({status:'LEARNING',caseMastery:50}); sandbox.validWords=()=>[1,2];
  sandbox.toast=()=>{}; sandbox.render=()=>{}; sandbox.currentTab='home'; sandbox.viewStack=[];
  vm.createContext(sandbox); vm.runInContext(hideSrc,sandbox,{filename:'hide-bridge.js'});
  return sandbox;
}
function bootSnap(url){
  const {sandbox}=sandboxBase(url);
  sandbox.db=null;sandbox.get=async()=>null;sandbox.set=async()=>{};sandbox.toast=()=>{};
  vm.createContext(sandbox); vm.runInContext(snapSrc,sandbox,{filename:'snap-bridge.js'});
  return sandbox;
}
function sendToReady(ready,event,origin){
  const handlers=ready.listeners.message||[];
  assert(handlers.length>0,'Ready message handler missing');
  for(const h of handlers)h({origin,data:{type:'TAKY_LEARNING_EVENT',event}});
}

const ready=bootReady();
const initial={
  session_id:ready.contract.session_id,
  goal_id:ready.contract.goal_id,
  lap_id:ready.contract.active_lap_id,
  startAt:ready.sandbox.state.activeSession.startAt,
  pausedAt:ready.sandbox.state.activeSession.pausedAt
};

ready.sandbox.window.ReadySetRev07.launchSpecialist('hide-seek');
const hideLaunch=ready.sandbox.location.href;
const hu=new URL(hideLaunch);
assert.equal(hu.hostname,'dainty-froyo-a6e427.netlify.app');
for(const [k,v] of Object.entries({
  session_id:initial.session_id,goal_id:initial.goal_id,lap_id:initial.lap_id,
  child_id:'CHILD_A',subject:'English',concept_skill_target:'vocabulary',learning_target_id:'word:apple',
  continuity_version:'1',state_owner:'ready-set'
}))assert.equal(hu.searchParams.get(k),v,k);
const timer=JSON.parse(hu.searchParams.get('timer_context'));
assert.equal(timer.owner,'ready-set');
assert.equal(timer.startAt,initial.startAt);
assert.equal(ready.contract.tasks[0].laps[0].ended_at,null,'APP_SWITCH must not end lap');
assert.equal(ready.sandbox.state.activeSession.pausedAt,initial.pausedAt,'APP_SWITCH must not pause');

const hide=bootHide(hideLaunch);
const hc=hide.window.HideSeekBridge.context();
assert.equal(hc.session_id,initial.session_id);
assert.equal(hc.lap_id,initial.lap_id);
assert.equal(hc.subject,'English');
assert.equal(hc.concept_skill_target,'vocabulary');
assert.equal(hc.learning_target_id,'word:apple');
const hideEvent=hide.window.HideSeekBridge.emit('TASK_PARTIAL',{caseMastery:55});
sendToReady(ready,hideEvent,hu.origin);
let rc=ready.sandbox.window.ReadySetRev07.contract();
assert.equal(rc.session_id,initial.session_id);
assert.equal(rc.goal_id,initial.goal_id);
assert.equal(rc.tasks[0].state,'PARTIAL');
assert.equal(rc.active_lap_id,initial.lap_id,'PARTIAL specialist result keeps lap open');
assert.equal(rc.active_app,'ready-set');
assert.equal(ready.sandbox.state.activeSession.startAt,initial.startAt);

const beforeDuplicate=rc.events.length;
sendToReady(ready,hideEvent,hu.origin);
rc=ready.sandbox.window.ReadySetRev07.contract();
assert.equal(rc.events.length,beforeDuplicate,'duplicate specialist event must be ignored');

ready.sandbox.window.ReadySetRev07.launchSpecialist('snap-pop');
const snapLaunch=ready.sandbox.location.href;
const su=new URL(snapLaunch);
assert.equal(su.hostname,'cheerful-pothos-d1c3ee.netlify.app');
assert.equal(su.searchParams.get('session_id'),initial.session_id);
assert.equal(su.searchParams.get('lap_id'),initial.lap_id);
assert.equal(su.searchParams.get('subject'),'English');
assert.equal(su.searchParams.get('concept_skill_target'),'vocabulary');
assert.equal(su.searchParams.get('learning_target_id'),'word:apple');
rc=ready.sandbox.window.ReadySetRev07.contract();
assert.equal(rc.active_lap_id,initial.lap_id,'second app switch must reuse current lap');
assert.equal(rc.tasks[0].laps[0].ended_at,null);

const snap=bootSnap(snapLaunch);
const sc=snap.window.SnapPopBridge.context();
assert.equal(sc.session_id,initial.session_id);
assert.equal(sc.lap_id,initial.lap_id);
assert.equal(sc.subject,'English');
assert.equal(sc.concept_skill_target,'vocabulary');
assert.equal(sc.learning_target_id,'word:apple');
const snapEvent=snap.window.SnapPopBridge.emit('TASK_COMPLETED',{child_authored:true,landmark:'idea'});
sendToReady(ready,snapEvent,su.origin);
rc=ready.sandbox.window.ReadySetRev07.contract();
assert.equal(rc.tasks[0].state,'COMPLETED');
assert.equal(rc.active_app,'ready-set');
assert.equal(rc.active_lap_id,null,'COMPLETED specialist result ends lap');
assert.equal(rc.tasks[0].laps[0].end_reason,'SPECIALIST_RESULT');
assert.equal(rc.tasks[0].laps[0].result_state,'COMPLETED');
assert.equal(rc.session_id,initial.session_id);
assert.equal(rc.goal_id,initial.goal_id);
assert.equal(ready.sandbox.state.activeSession.startAt,initial.startAt);
assert.equal(ready.sandbox.state.activeSession.pausedAt,null);
assert(rc.applied_event_ids.includes(hideEvent.event_id));
assert(rc.applied_event_ids.includes(snapEvent.event_id));

console.log('LEARNING_CROSS_APP_CONTINUITY_OWNER_RUNTIME_PASS');
console.log(JSON.stringify({session_preserved:true,goal_preserved:true,lap_preserved_across_switch:true,partial_keeps_lap:true,completed_ends_lap:true,app_switch_not_pause:true,duplicate_result_blocked:true,scope_preserved:true}));
