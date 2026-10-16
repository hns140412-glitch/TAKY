'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('fs');
const router=require('./explorer-crew-learning-voice-route-v1.js');
const base={app_id:'HIDE_SEEK',character_id:'dubi',
 context:{session_id:'s1',task_id:'t1',child_id:'learner-A'}};
function make(type,app='hide-seek',payload={}){return {app,event_id:'event-01',session_id:'s1',task_id:'t1',child_id:'learner-A',type,payload}}
test('Hide native help routes HINT but does not interrupt on return-navigation',()=>{
 const hint=router.route({...base,event:make('HELP_NEEDED')});
 assert.equal(hint.ok,true);assert.equal(hint.event_type,'HINT');assert.equal(hint.autoplay,false);
 const requested=router.route({...base,event:make('HELP_NEEDED','hide-seek',{crew_voice_requested:true})});
 assert.equal(requested.autoplay,true);
 const nav=router.route({...base,event:make('HELP_NEEDED','hide-seek',{crew_voice_requested:true,navigation_pending:true})});
 assert.equal(nav.autoplay,false);
});
test('Snap completed result: independently sourced child authored evidence speaks FEEDBACK',()=>{
 const msg=make('TASK_COMPLETED','snap-pop',{child_authored:true});
 const route=router.route({...base,app_id:'SNAP_POP',event:msg});
 assert.equal(route.ok,true);assert.equal(route.event_type,'FEEDBACK');assert.equal(route.autoplay,true);
 const notProof=router.route({...base,app_id:'SNAP_POP',event:make('TASK_COMPLETED','snap-pop')});
 assert.equal(notProof.autoplay,false);
});
test('Ready task result only after native session-derived completed transition',()=>{
 const context={session_id:'s1',task_id:'t1',child_id:'learner-A'};
 const ok=router.route({...base,app_id:'READY_SET',context,
  event:make('TASK_STATE_CHANGED','ready-set',{next:'COMPLETED',provenance:'SESSION_DERIVED'})});
 assert.equal(ok.ok,true);assert.equal(ok.event_type,'FEEDBACK');
 assert.equal(ok.autoplay,false);
 for(const next of ['DEFERRED','PENDING','BLOCKED']){
  const r=router.route({...base,app_id:'READY_SET',context,event:make('TASK_STATE_CHANGED','ready-set',{next,provenance:'SESSION_DERIVED'})});
  assert.equal(r.ok,false);
 }
});
test('radio request cannot double-play existing Snap ASK button',()=>{
 const r=router.route({...base,app_id:'SNAP_POP',event:make('GUIDE_RADIO_REQUEST','snap-pop',{reason:'home_radio'})});
 assert.equal(r.ok,false);assert.equal(r.status,'NATIVE_RADIO_ALREADY_OWNS_ASK');
});
test('wrong app, missing/foreign task, child, event id never speaks',()=>{
 for(const patch of [{session_id:'s2'},{task_id:'t2'},{child_id:'another'},
 {app:'snap-pop'},{event_id:''}]){
  assert.equal(router.route({...base,event:{...make('HELP_NEEDED'),...patch}}).ok,false,JSON.stringify(patch));
 }
});
test('Snap bridge emits same-tab native learning event and app loads consumer router once',()=>{
 const snap=fs.readFileSync('D:/Git PWA/Snap & Pop/snap-bridge.js','utf8');
 assert.match(snap,/dispatchEvent\(new CustomEvent\('taky-learning-event'/);
 for(const app of ['Ready & Set','Hide & Seek','Snap & Pop']){
  const html=fs.readFileSync('D:/Git PWA/'+app+'/index.html','utf8');
  assert.equal(html.split('explorer-crew-learning-voice-route-v1.js').length,2);
  assert.ok(html.indexOf('explorer-crew-learning-voice-route-v1.js')<
    html.indexOf('explorer-crew-ui-voice-integration-v1.js'));
 }
});
