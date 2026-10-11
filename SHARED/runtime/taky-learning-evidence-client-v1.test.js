'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

const source=fs.readFileSync(path.join(__dirname,'taky-learning-evidence-client-v1.js'),'utf8');

function makeStorage(){
  const store=new Map();
  return {
    getItem:k=>store.has(k)?store.get(k):null,
    setItem:(k,v)=>store.set(k,String(v)),
    _store:store
  };
}

function boot({search=''}={}){
  const localStorage=makeStorage();
  const sessionStorage=makeStorage();
  const listeners={};
  const fetchCalls=[];
  const location={search};
  const document={
    visibilityState:'visible',
    addEventListener:()=>{}
  };
  const win={
    addEventListener:(n,f)=>{listeners[n]=f},
    fetch:async(url,opts)=>{
      const body=JSON.parse(opts.body);
      fetchCalls.push({url,opts,body});
      return {ok:true,json:async()=>({
        ok:true,
        acknowledgement_kind:'OBSERVATION_INGEST_RECEIPT',
        packet_id:body.packet_id,
        event_id:body.event.event_id,
        storage_confirmed:true
      })};
    },
    TAKY_FAMILY_RUNTIME:{
      apiBaseUrl:'https://central.example.test',
      getToken:async()=> 'validated-bearer-token-001',
      getFamilyId:async()=> 'F1'
    }
  };
  const sandbox={
    console,URL,URLSearchParams,Date,JSON,Set,Object,Array,String,Number,Math,
    localStorage,sessionStorage,location,document,
    setTimeout:()=>0,
    window:win
  };
  Object.assign(win,{window:win,localStorage,sessionStorage,location,document,URL,URLSearchParams});
  vm.createContext(sandbox);
  vm.runInContext(source,sandbox,{filename:'taky-learning-evidence-client-v1.js'});
  return {C:win.TakyLearningEvidenceClientV1,localStorage,sessionStorage,fetchCalls,location,listeners};
}

function scopedEvent(id,extraPayload={}){
  return {
    event_id:id,
    app:'hide-seek',
    type:'RETRIEVAL_ATTEMPT_RESULT',
    at:'2026-10-04T00:00:00.000Z',
    child_id:'CHILD_A',
    payload:{
      learning_scope:{
        subject:'English',
        concept_skill_target:'vocabulary',
        learning_target_id:'word:apple'
      },
      verification_observation:{response_value:'apple'},
      ...extraPayload
    }
  };
}

function unscopedEvent(id){
  return {
    event_id:id,
    app:'hide-seek',
    type:'TASK_COMPLETED',
    at:'2026-10-04T00:00:00.000Z',
    child_id:'CHILD_A',
    payload:{}
  };
}

(async()=>{
  {
    const {C,fetchCalls}=boot();
    const e=scopedEvent('h-proof',{
      verification_candidate:{outcome:1,reference_id:'client:fake'},
      verification_receipt:{authority:'CLIENT_FAKE'},
      verified_outcome:1,
      promotion_authorized:true
    });
    assert.equal(C.enqueue(e).ok,true);
    const queued=C.pending()[0];
    assert.equal(queued.event.payload.verified_outcome,undefined);
    assert.equal(queued.event.payload.verification_candidate,undefined);
    assert.equal(queued.event.payload.verification_receipt,undefined);
    assert.equal(queued.event.payload.promotion_authorized,undefined);
    assert.equal(queued.event.payload.verification_observation.response_value,'apple');

    const result=await C.flush();
    assert.equal(result.ok,true);
    assert.equal(result.acked,1);
    assert.equal(C.pending().length,0);
    assert.equal(fetchCalls.length,1);
    const posted=fetchCalls[0].body;
    assert.equal(posted.context.family_id,'F1');
    assert.equal(posted.context.member_id,'CHILD_A');
    assert.equal(posted.context.subject,'English');
    assert.equal(posted.context.concept_skill_target,'vocabulary');
    assert.equal(posted.event.payload.verification_candidate,undefined);
  }

  {
    const {C,fetchCalls}=boot();
    for(let i=0;i<25;i++)assert.equal(C.enqueue(unscopedEvent('missing-'+i)).ok,true);
    assert.equal(C.enqueue(scopedEvent('scoped-after-missing')).ok,true);
    const result=await C.flush();
    assert.equal(result.acked,1,'scoped row behind missing-scope head must flush');
    assert.equal(fetchCalls.length,1);
    assert.equal(fetchCalls[0].body.event.event_id,'scoped-after-missing');
    assert.equal(C.pending().length,25);
    assert.equal(result.pending_scope,25);
  }

  {
    const {C}=boot();
    for(let i=0;i<120;i++){
      const r=C.enqueue(unscopedEvent('capacity-'+i));
      assert.equal(r.ok,true);
    }
    const oldest=C.pending()[0].event_id;
    const overflow=C.enqueue(unscopedEvent('capacity-overflow'));
    assert.equal(overflow.ok,false);
    assert.equal(overflow.reason,'PENDING_QUEUE_FULL');
    assert.equal(C.pending().length,120);
    assert.equal(C.pending()[0].event_id,oldest,'oldest unacked row must never be silently evicted');
    assert.equal(C.pending().some(x=>x.event_id==='capacity-overflow'),false);
  }

  {
    const {C,fetchCalls}=boot();
    const e=scopedEvent('acked-once');
    C.enqueue(e);
    assert.equal((await C.flush()).acked,1);
    assert.equal(fetchCalls.length,1);
    const again=C.enqueue(e);
    assert.equal(again.ok,true);
    assert.equal(again.acked,true);
    assert.equal(again.duplicate,true);
    assert.equal(C.pending().length,0);
    await C.flush();
    assert.equal(fetchCalls.length,1,'acked event must not be re-posted');
    assert(C.acked().includes('hide-seek:acked-once'));
  }

  {
    const {C}=boot({
      search:'?subject=CurrentSubject&concept_skill_target=current-target&learning_target_id=current-item&child_id=CHILD_A'
    });
    const old=unscopedEvent('old-replay');
    const replay=C.enqueue(old);
    assert.equal(replay.ok,true);
    const held=C.pending()[0];
    assert.equal(held.scope_hint.subject,'');
    assert.equal(held.scope_hint.concept_skill_target,'');
    assert.equal(held.scope_hint.learning_target_id,'');
    assert.equal(held.scope_hint.member_id,'CHILD_A');

    const live=unscopedEvent('live-current');
    const liveResult=C.enqueue(live,{allowAmbientScope:true});
    assert.equal(liveResult.ok,true);
    const liveRow=C.pending().find(x=>x.event_id==='live-current');
    assert.equal(liveRow.scope_hint.subject,'CurrentSubject');
    assert.equal(liveRow.scope_hint.concept_skill_target,'current-target');
    assert.equal(liveRow.scope_hint.learning_target_id,'current-item');
  }

  console.log('TAKY_LEARNING_EVIDENCE_CLIENT_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
