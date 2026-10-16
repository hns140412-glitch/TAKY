/* TAKY shared-crew actual UI audio consumer. Does not replace study-guide speech.
  Only routes a verified canonical primary explorer-crew character. */
(function(root){
 'use strict';
 const app=document.currentScript?.dataset?.app||'';
 const apps={HIDE_SEEK:'HIDE_SEEK',SNAP_POP:'SNAP_POP',READY_SET:'READY_SET'};
 if(!apps[app])return;
 const report={app_id:app,status:'INITIALIZING',events:[],last_result:null};
 root.TakyCrewAudioAppEvidence=report;
 const $=id=>document.getElementById(id);
 const roster=new Set((root.TakyCrewVoiceRegistry?.rows||[]).map(r=>r.character_id));
 const styles='font:700 12px/1.3 system-ui;letter-spacing:-.01em;background:#e5f1e8;color:#315e49;border:1px solid #a2c7b1;border-radius:18px;padding:9px 11px;cursor:pointer;';
 function boundId(){
   try{
    if(app==='HIDE_SEEK'||app==='SNAP_POP'){
      const authority=(app==='HIDE_SEEK'?root.HideExplorerCrewAuthorityConsumer:root.SnapExplorerCrewAuthorityConsumer);
      const projection=authority?.snapshot?.(root.localStorage);
      return projection?.status==='BOUND' && roster.has(projection.character_id)?projection.character_id:null;
    }
    // Ready must have a completed real identity and canonical relation. Never bypass first-run onboarding.
    if(root.ReadyIdentityV1?.isReady?.()!==true)return null;
    const raw=root.localStorage?.getItem('taky_explorer_crew_canonical_v1');
    if(!raw)return null;
    const env=JSON.parse(raw),relation=env?.state?.relation||env?.relation;
    const id=relation?.main_character_id;
    return roster.has(id)&&relation?.members && Object.prototype.hasOwnProperty.call(relation.members,id)?id:null;
   }catch{return null;}
 }
 let engine=null,events=null;
 function initVoice(){
   const personality=root.TakyExplorerCrewDialoguePersonality;
   const bridgeLib=root.TakyExplorerCrewTtsMockSwitch;
   const adapterLib=root.TakyExplorerCrewVoiceEventAdapter;
   const ownerLib=root.TakyExplorerCrewContentOwner;
   if(!personality?.resolve||!bridgeLib?.create||!adapterLib?.create||!ownerLib?.create)
    throw new Error('CANONICAL_VOICE_DEPENDENCIES_MISSING');
   engine=bridgeLib.create({
     registry:root.TakyCrewVoiceRegistry,
     approvedAudioManifest:root.TakyCrewApprovedManifest||{clips:[]},
     mockManifest:root.TakyCrewMockManifest
   });
   // MAIN_CREW content is not restricted by the child's school grade.
   // The historical script key is resolved only inside this content-owner adapter.
   events=adapterLib.create({personality:ownerLib.create(personality,{app_id:app}),bridge:engine});
 }
 function readRelation(){
   try{
     const raw=root.localStorage?.getItem('taky_explorer_crew_canonical_v1');
     if(!raw)return null;
     const env=JSON.parse(raw);
     return env?.state?.relation||env?.relation||null;
   }catch{return null}
 }
 async function confirmCanonicalMain({character_id}={}){
   const current=readRelation(),member=current?.members?.[character_id];
   if(!member||!['COMPANION_AVAILABLE','COMPANION','MAIN_COMPANION'].includes(member.relation_state))
     return {ok:false,reason:'RELATION_COMPANION_GATE_NOT_MET'};
   const sys=root.TakyExplorerCrewSystemV2;
   if(!sys?.create)return {ok:false,reason:'CANONICAL_SELECTION_OWNER_UNAVAILABLE'};
   try{
     const controller=sys.create({app_id:app,storage:root.localStorage,
       locationHref:root.location?.href,replaceUrl:()=>{}});
     const now=new Date().toISOString();
     const result=await controller.dispatch({
       character_id,scene_id:'EXPLORER_CREW_SELECT_MAIN',
       interaction_result:{relation_event:{character_id,type:current.main_character_id===character_id?'MAIN_SELECTED':'MAIN_CHANGED',at:now}}
     });
     const saved=readRelation();
     if(saved?.main_character_id!==character_id||saved?.members?.[character_id]?.relation_state!=='MAIN_COMPANION')
       return {ok:false,reason:'CANONICAL_SELECTION_NOT_PERSISTED'};
     const authority=app==='HIDE_SEEK'?root.HideExplorerCrewAuthorityConsumer:
       app==='SNAP_POP'?root.SnapExplorerCrewAuthorityConsumer:null;
     authority?.consumeCanonicalStore?.(root.localStorage);
     report.refresh?.();
     root.dispatchEvent?.(new CustomEvent('taky-crew-main-selected',{detail:{character_id,app_id:app}}));
     return {ok:true,persisted:true,result};
   }catch(error){return {ok:false,reason:String(error?.message||error)}}
 }
 function attachSelectionPreview(){
   const pickerLib=root.TakyExplorerCrewSelectionPreview;
   if(!pickerLib?.create)throw new Error('CREW_SELECTION_PREVIEW_MODULE_MISSING');
   const picker=pickerLib.create({
     registry:root.TakyCrewVoiceRegistry,engine,app_id:app,readRelation,
     imageBase:'./characters/ui_cutouts/',
     onConfirm:root.TakyExplorerCrewSystemV2?.create?confirmCanonicalMain:null
   });
   const launch=picker.mount();
   if(app==='READY_SET'){
     const refreshPicker=()=>{launch.hidden=root.ReadyIdentityV1?.isReady?.()!==true;};
     refreshPicker();
     root.addEventListener('ready-member-profile-local-commit',refreshPicker);
     root.addEventListener('pageshow',refreshPicker);
     root.addEventListener('storage',refreshPicker);
   }
   root.TakyCrewSelectionPreviewController=picker;
   report.selection_preview='MOUNTED';
 }
 async function consume(source,{event_type='ASK',event_id=null}={}){
   const id=boundId();
   if(!id){const r={ok:false,status:'NO_CANONICAL_COMPANION',source};report.last_result=r;return r;}
   const contextResolver=root.TakyExplorerCrewLearnerVoiceContext;
   let confirmedIdentity=null,ready=false;
   if(app==='READY_SET'){
     ready=root.ReadyIdentityV1?.isReady?.()===true;
     confirmedIdentity=ready?root.ReadyIdentityV1?.get?.():null;
   }
   const appBridge=app==='HIDE_SEEK'?root.HideSeekBridge:
     app==='SNAP_POP'?root.SnapPopBridge:null;
   const rawBridge=appBridge?.context?.()||null;
   const appSession=rawBridge&&rawBridge.child_id&&rawBridge.session_id&&rawBridge.task_id?
     {...rawBridge,source:'APP_BOUND_NAVIGATION_CONTEXT'}:null;
   const context=contextResolver?.resolve?.({
     app_id:app,identity:confirmedIdentity,identityReady:ready,
     explicitContext:root.TakyLearningEngineVerifiedContext||appSession
   })||{ok:false,status:'LEARNER_CONTEXT_PROVIDER_UNAVAILABLE'};
   if(!context.ok){
     const result={ok:false,status:context.status,character_id:id,source};
     report.last_result=result;
     return result;
   }
   const actualRelation=readRelation();
   const member=actualRelation?.members?.[id]||null;
   const event={
     app_id:app,character_id:id,event_type,event_id,
     school_stage:context.school_stage,presentation_band:context.presentation_band,
     voice_content_scope:'MAIN_CREW',
     relation_state:member?.relation_state||'MAIN_COMPANION',
     affinity:typeof member?.affinity==='number'?member.affinity:0,
     locale:'ko-KR',source,learner_id:context.learner_id
   };
   let answer;
   try{answer=await events.handle(event);}catch(e){answer={ok:false,status:'CONSUMER_EXCEPTION',reason:String(e)}}
   report.last_result={ok:answer.ok,status:answer.status,key:answer.key||null,
     url:answer.playback?.url||null,mode:answer.playback?.mode||null,
     character_id:id,source};
   report.events.push(report.last_result);
   if(report.events.length>20)report.events.shift();
   const host=app==='SNAP_POP'?$('homeRadio'):$('takyCrewVoiceBtn');
   if(host){
     host.dataset.takyCrewAudioStatus=answer.status;
     host.dataset.takyCrewAudioKey=answer.key||'';
     host.dataset.takyCrewAudioMode=answer.playback?.mode||'';
   }
   return answer;
 }
 function attachNativeLearningEvents(){
   const nativeRouter=root.TakyExplorerCrewLearningVoiceRouteV1;
   if(!nativeRouter?.route)throw Error('NATIVE_LEARNING_EVENT_ROUTE_REQUIRED');
   const nativeSeen=new Set();
   const records=[];
   report.native_learning_events=records;
   root.addEventListener('taky-learning-event',event=>{
     const raw=event?.detail;
     const id=boundId();
     const appBridge=app==='HIDE_SEEK'?root.HideSeekBridge:
       app==='SNAP_POP'?root.SnapPopBridge:null;
     const readyContract=app==='READY_SET'?root.ReadySetRev07?.contract?.():null;
     const context=app==='READY_SET'&&readyContract?{
       session_id:readyContract.session_id,task_id:readyContract.active_task_id,
       child_id:root.ReadyIdentityV1?.get?.()?.userId
     }:appBridge?.context?.()||null;
     const route=nativeRouter.route({app_id:app,event:raw,context,character_id:id});
     const record={id:raw?.event_id||null,event_type:raw?.type||null,
       mapped:route.event_type||null,status:route.status,autoplay:route.autoplay===true};
     if(!route.ok){if(route.status!=='EVENT_HAS_NO_VOICE_INTENT'&&route.status!=='NATIVE_RADIO_ALREADY_OWNS_ASK')records.push(record);return;}
     if(nativeSeen.has(route.event_id)){record.status='EVENT_ALREADY_SEEN';records.push(record);return;}
     nativeSeen.add(route.event_id);if(nativeSeen.size>128)nativeSeen.clear();
     records.push(record);if(records.length>40)records.shift();
     // Do not preempt another lesson voice or native audio player.
     const audioBusy=[...document.querySelectorAll('audio')].some(a=>
       !a.paused&&!a.muted&&a.volume>0);
     if(route.autoplay&&!audioBusy&&!document.hidden){
       void consume('VERIFIED_NATIVE_LEARNING_EVENT',{event_type:route.event_type,event_id:route.event_id})
         .then(result=>{record.status=result.status;record.key=result.key||null;});
     }else{
       const relation=readRelation();
       const contextResolver=root.TakyExplorerCrewLearnerVoiceContext;
       const identity=app==='READY_SET'&&root.ReadyIdentityV1?.isReady?.()?
         root.ReadyIdentityV1.get():null;
       const age=contextResolver?.resolve?.({
         app_id:app,identity,identityReady:!!identity,
         explicitContext:root.TakyLearningEngineVerifiedContext||
           (context?.child_id?{...context,source:'APP_BOUND_NAVIGATION_CONTEXT'}:null)
       });
       if(!age?.ok){record.status='CONTEXT_NOT_READY';return;}
       const data={app_id:app,character_id:route.character_id,
         event_type:route.event_type,event_id:route.event_id,
         relation_state:relation?.members?.[route.character_id]?.relation_state||'MAIN_COMPANION',
         affinity:relation?.members?.[route.character_id]?.affinity||0,
         voice_content_scope:'MAIN_CREW',school_stage:age.school_stage,locale:'ko-KR'};
       void events.handle(data,{play:false}).then(res=>{
         record.status=res.status;record.key=res.key||null;record.played=false;
       }).catch(error=>{record.status='PREPARE_EXCEPTION';record.reason=String(error)});
     }
   });
 }
 function addDedicatedBtn(anchor){
   if($('takyCrewVoiceBtn'))return;
   const button=document.createElement('button');button.type='button';button.id='takyCrewVoiceBtn';
   button.textContent='탐험대원 음성';button.setAttribute('aria-label','동행 탐험대원 목업 음성 듣기');
   button.style.cssText=styles+'position:fixed;right:12px;bottom:96px;z-index:3000;box-shadow:0 3px 12px rgba(0,0,0,.12);';
   button.disabled=!boundId();button.style.display=button.disabled?'none':'';
   button.title='확정된 주 동행 탐험대원이 있을 때 재생';
   button.addEventListener('click',()=>void consume('CREW_VOICE_BUTTON'));
   document.body.appendChild(button);
   function refresh(){button.disabled=!boundId();button.style.display=button.disabled?'none':'';
     button.title=button.disabled?'캐노니컬 주 동행 탐험대원이 아직 연결되지 않았습니다':'확정 주 동행 대사를 듣습니다';}
   root.addEventListener('storage',refresh);
   root.addEventListener('ready-member-profile-local-commit',refresh);
   root.addEventListener('taky-ready-character-runtime',refresh);
   root.addEventListener('pageshow',refresh);
   document.addEventListener('visibilitychange',refresh);
   button.addEventListener('pointerenter',refresh);
   report.refresh=refresh;
 }
 function init(){
  try{
   initVoice();
   if(app==='SNAP_POP'){
     const radio=$('homeRadio');if(!radio)throw Error('HOME_RADIO_MISSING');
     radio.addEventListener('click',()=>{
       if(boundId())void consume('ACTUAL_HOME_RADIO');
     });
   }else if(app==='HIDE_SEEK'){
     addDedicatedBtn($('partnerBar')||$('app'));
   }else if(app==='READY_SET'){
     const home=$('homeView'),main=home?.querySelector('.homeMain');
     addDedicatedBtn(main||home);
   }
   attachSelectionPreview();
   attachNativeLearningEvents();
   report.status='APP_EVENT_CONSUMER_ATTACHED';
  }catch(e){report.status='APP_EVENT_CONSUMER_FAILED';report.error=String(e);}
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
 root.TakyCrewAudioAppPlay=consume;
})(typeof globalThis!=='undefined'?globalThis:this);
