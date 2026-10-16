/* TAKY Ready canonical first encounter, phase EXPLORER / THEME.
 * This script does NOT produce or authorize new audio; 24 signatures remain locked.
 * Explorer identity = intro preference only; no falsified central relation affinity.
 */
(function(root){
 'use strict';
 if(root.ReadyExplorerIntroCanonicalV1)return;
 const VERSION='TAKY_READY_CORE6_FIRST_ENCOUNTER_V1';
 const CORE6=['dubi','lori','ink','nova','take','zero'];
 const THEMES=[{id:'TODAYS_ISLAND',title:'오늘의 섬',detail:'오늘의 할 일을 한 걸음씩 발견해 보자'},
  {id:'SKY_ROUTE',title:'하늘길',detail:'한 단계씩 목표로 향하는 탐험'},
  {id:'FOREST_TRAIL',title:'숲길',detail:'작은 단서를 따라 길을 찾는 탐험'}];
 const nameById={dubi:'두비',lori:'로리',ink:'잉크',nova:'노바',take:'테이크',zero:'제로'};
 const identity=()=>root.ReadyIdentityV1?.get?.()||{};
 const getRoot=()=>document.getElementById('readyFirstRun');
 const pick=new Map((root.TakyCrewVoiceRegistry?.rows||[])
   .filter(row=>row.scope==='MAIN_CREW'&&row.kind==='SIGNATURE'&&CORE6.includes(row.character_id))
   .map(row=>[row.character_id,row]));
 let currentId=null,media=null,sequence=0;
 const status={version:VERSION,state:'NOT_LOADED',taps:[],last_audio_status:null,confirmations:0};
 root.ReadyExplorerIntroEvidence=status;
 function engine(){
   if(!media){
     const lib=root.TakyExplorerCrewTtsMockSwitch;
     if(!lib?.create)throw Error('AUDIO_ROUTER_NOT_READY');
     media=lib.create({registry:root.TakyCrewVoiceRegistry,
       approvedAudioManifest:root.TakyCrewApprovedManifest||{clips:[]},
       mockManifest:root.TakyCrewMockManifest});
   }
   return media;
 }
 function ensureStyle(){
  if(document.getElementById('readyExplorerIntroCanonicalStyle'))return;
  const el=document.createElement('style');el.id='readyExplorerIntroCanonicalStyle';
  el.textContent=[
   '.rc-intro{min-height:100dvh;padding:52px 22px 32px;background:linear-gradient(#9bdaef,#f1fcf4 58%,#cceadc);color:#164b4a;box-sizing:border-box;font-family:system-ui,sans-serif}',
   '.rc-intro h1{font-size:clamp(24px,7vw,35px);line-height:1.1;letter-spacing:-.04em;margin:13px 0}',
   '.rc-intro p{font-size:13px;line-height:1.55;margin:8px 0 16px}',
   '.rc-crew-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px;margin-top:19px}',
   '.rc-crew-card{min-width:0;display:flex;flex-direction:column;align-items:center;gap:5px;background:#fffefb;border:2px solid #e1eee5;border-radius:18px;padding:11px 4px;cursor:pointer;color:#255044}',
   '.rc-crew-card[aria-pressed=true]{border-color:#308d75;background:#e1f5e9}',
   '.rc-crew-card img{height:80px;width:100%;object-fit:contain}',
   '.rc-crew-card b{font-size:14px}.rc-crew-card small{font-size:10px;color:#59736b}',
   '.rc-bubble{margin:16px 0;padding:15px;border-radius:16px;background:#f8fffc;border:1px solid #b1dbc2;min-height:75px}',
   '.rc-bubble strong{display:block;font-size:13px}.rc-bubble q{display:block;font-size:16px;margin-top:6px;line-height:1.5}',
   '.rc-bubble small{display:block;font-size:10px;margin-top:7px;opacity:.7}',
   '.rc-actions{display:flex;gap:10px;margin-top:16px}.rc-actions button{flex:1;min-width:0;border-radius:14px;padding:14px;border:0;font-weight:800}',
   '.rc-primary{background:#287e6b;color:#fff}.rc-primary:disabled{opacity:.42}.rc-back{background:#fff;color:#2c6756}',
   '.rc-theme-grid{display:grid;gap:12px;margin:20px 0}.rc-theme-card{padding:18px;text-align:left;border-radius:16px;background:white;border:2px solid #d5e8da;color:#244d41}',
   '.rc-theme-card[aria-pressed=true]{border-color:#318e75;background:#e5f5ea}',
   '.rc-note{font-size:11px;line-height:1.5;color:#5a7469}',
   '@media(min-width:600px){.rc-intro{max-width:800px;margin:auto}.rc-crew-grid{grid-template-columns:repeat(6,minmax(0,1fr))}}'
  ].join('\n');
  document.head.appendChild(el);
 }
 function escape(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));}
 function setSpeech(id,info='선택한 탐험대원의 목소리가 들려요.'){
   const area=getRoot();if(!area)return;
   const row=pick.get(id);
   const label=area.querySelector('[data-rc-who]'),quote=area.querySelector('[data-rc-quote]'),small=area.querySelector('[data-rc-status]');
   if(label)label.textContent=row?nameById[id]:'탐험대원';
   if(quote)quote.textContent=row?.exact_text||'만나고 싶은 탐험대원을 눌러 봐!';
   if(small)small.textContent=info;
   area.querySelectorAll('[data-rc-crew]').forEach(card=>card.setAttribute('aria-pressed',card.dataset.rcCrew===id?'true':'false'));
   const next=area.querySelector('#rcConfirmEncounter');if(next)next.disabled=!id;
 }
 async function preview(id){
   if(!CORE6.includes(id)||!pick.has(id))return {ok:false,status:'CORE6_APPROVED_SOURCE_NOT_FOUND'};
   currentId=id;const nonce=++sequence;
   try{engine().stop();}catch{}
   setSpeech(id,'인사 음성 재생 중…');
   status.taps.push(id);
   let result;
   try{
     result=await engine().play({app_id:'READY_SET',character_id:id,intent:'GREET',
       locale:'ko-KR',dialogue:{source:'APPROVED_BOARD_SIGNATURE',text:pick.get(id).exact_text}});
   }catch(error){result={ok:false,status:'AUDIO_PLAY_EXCEPTION',reason:String(error)}}
   if(nonce!==sequence)return {ok:false,status:'SUPERSEDED'};
   status.last_audio_status=result.status;
   status.last_key=result.key||null;
   status.last_character_id=id;
   setSpeech(id,result.status==='PLAYING_STARTED'?'탐험대원 인사 재생 확인':'음성을 재생하지 못했어요.');
   return result;
 }
 function drawExplorer(el,record){
   status.state='EXPLORER';currentId=CORE6.includes(record.explorerId)?record.explorerId:(CORE6.includes(currentId)?currentId:null);
   el.innerHTML='<div class="rc-intro firstRunSky" data-rc-screen="EXPLORER">'+
     '<span>4 / 5 · FIRST ENCOUNTER</span><h1>오늘 함께 만날 탐험대원은?</h1>'+
     '<p>여섯 탐험대원 중 한 명을 눌러 인사말을 들어 봐. 다시 누르면 또 들을 수 있어.</p>'+
     '<div class="rc-crew-grid">'+CORE6.map(id=>{
       const row=pick.get(id);
       return '<button type="button" class="rc-crew-card" data-rc-crew="'+id+'" aria-pressed="'+(id===currentId?'true':'false')+'">'+
         '<img src="./characters/ui_cutouts/'+id+'.png" alt="'+nameById[id]+'"><b>'+nameById[id]+'</b>'+
         '<small>'+(row?'목소리 듣기':'음원 확인 필요')+'</small></button>';
     }).join('')+'</div>'+
     '<div class="rc-bubble" role="status" aria-live="polite"><strong data-rc-who>탐험대원</strong>'+
     '<q data-rc-quote>만나고 싶은 탐험대원을 눌러 봐!</q>'+
     '<small data-rc-status>터치 시 인사 음성·대사를 함께 확인해요.</small></div>'+
     '<p class="rc-note">첫 만남 선택은 소개 단계입니다. 실제 주 동행 확정과 관계·친밀도는 별도 중앙 엔진 기준을 따릅니다.</p>'+
     '<div class="rc-actions"><button type="button" class="rc-back" id="rcBackCharacter">← 내 캐릭터</button>'+
     '<button type="button" class="rc-primary" id="rcConfirmEncounter" '+(currentId?'':'disabled')+'>이 탐험대원과 출발 준비</button></div></div>';
   el.querySelectorAll('[data-rc-crew]').forEach(card=>card.addEventListener('click',()=>void preview(card.dataset.rcCrew)));
   el.querySelector('#rcBackCharacter').onclick=()=>{
     engine().stop();root.ReadyIdentityV1.patch({onboardingStep:'CHARACTER'});root.ReadyIdentityV1.render();
   };
   el.querySelector('#rcConfirmEncounter').onclick=()=>{
     if(!currentId)return;
     engine().stop();
     root.ReadyIdentityV1.patch({onboardingStep:'THEME',
       explorerId:currentId,explorerName:nameById[currentId],
       introPreferredCrewId:currentId,status:'INTRO_CREW_PREVIEW_SELECTED'});
     status.confirmations++;root.ReadyIdentityV1.render();
   };
   if(currentId)setSpeech(currentId,'다시 터치하면 목소리를 재생해요.');
 }
 function drawTheme(el,record){
   status.state='THEME';const selection=THEMES.find(x=>x.id===record.journeyTheme);
   let selected=selection?.id||null;
   el.innerHTML='<div class="rc-intro firstRunSky" data-rc-screen="THEME">'+
    '<span>5 / 5 · FIRST WORLD</span><h1>첫 탐험의 분위기를 정해 볼까?</h1>'+
    '<p>첫 탐험을 어떻게 시작하고 싶은지 골라 보자.</p>'+
    '<div class="rc-theme-grid">'+THEMES.map(t=>'<button type="button" class="rc-theme-card" data-rc-theme="'+t.id+'" aria-pressed="'+(t.id===selected)+'"><b>'+t.title+'</b><br><small>'+t.detail+'</small></button>').join('')+'</div>'+
    '<p class="rc-note">섬 이름·베이스캠프 이름은 실제 해당 장면에서 별도로 정합니다. 이 단계에서 임의 생성하지 않아요.</p>'+
    '<div class="rc-actions"><button type="button" class="rc-back" id="rcBackCrew">← 탐험대원</button>'+
    '<button type="button" class="rc-primary" id="rcFinish" '+(selected?'':'disabled')+'>Ready & Set 열기</button></div>'+
    '<p class="rc-note" data-rc-error></p></div>';
   el.querySelectorAll('[data-rc-theme]').forEach(b=>b.onclick=()=>{
     selected=b.dataset.rcTheme;
     el.querySelectorAll('[data-rc-theme]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.rcTheme===selected)));
     el.querySelector('#rcFinish').disabled=false;
   });
   el.querySelector('#rcBackCrew').onclick=()=>{
     root.ReadyIdentityV1.patch({onboardingStep:'EXPLORER'});root.ReadyIdentityV1.render();
   };
   el.querySelector('#rcFinish').onclick=()=>{
     if(!selected||!CORE6.includes(record.explorerId))return;
     try{
       const i=root.ReadyIdentityV1.get();
       root.ReadyIdentityV1.complete({
         journeyTheme:selected,explorerId:i.explorerId,explorerName:nameById[i.explorerId],
         teamName:i.teamName||i.nickname+' 탐험대'
       });
       el.remove();document.documentElement.classList.remove('readyFirstRun','identityFirstPaint');
       root.ReadyRoleContextV1?.activateIdentityRole?.({reload:true});
       status.state='COMPLETE';
     }catch(error){
       el.querySelector('[data-rc-error]').textContent='선택을 저장하지 못했어요: '+String(error?.message||error);
       status.state='COMPLETE_BLOCKED';
     }
   };
 }
 function addDeferral(el,record){
   if(record.onboardingStep!=='CHARACTER'||el.querySelector('#rcDeferCharacter'))return;
   if(record.characterVisualId||record.characterSetupState==='DEFERRED_NO_COST')return;
   const section=el.querySelector('.firstRunSky');if(!section)return;
   const button=document.createElement('button');button.type='button';button.id='rcDeferCharacter';button.className='firstRunNext';
   button.textContent='내 캐릭터는 나중에 만들고 탐험대원 만나기';
   button.onclick=()=>{
     root.ReadyIdentityV1.patch({characterSetupState:'DEFERRED_NO_COST',
       onboardingStep:'EXPLORER',status:'CHARACTER_DEFERRED'});
     root.ReadyIdentityV1.render();
   };
   section.appendChild(button);
 }
 function render(el=getRoot()){
   if(!el)return false;
   const api=root.ReadyIdentityV1,record=api?.get?.();
   if(!record||api.isReady?.())return false;
   ensureStyle();
   if(record.onboardingStep==='EXPLORER'){drawExplorer(el,record);return true}
   if(record.onboardingStep==='THEME'){drawTheme(el,record);return true}
   if(record.onboardingStep==='CHARACTER'){addDeferral(el,record);return false}
   return false;
 }
 function init(){
   const existing=root.ReadyIdentityV1;
   if(!existing?.get||!existing?.patch)return;
   // After the existing first-run owner has booted, ensure deferred character action is present.
   render();
   const observer=new MutationObserver(()=>{
     const rec=existing.get(),el=getRoot();
     if(!el||!rec||!['EXPLORER','THEME','CHARACTER'].includes(rec.onboardingStep))return;
     if(rec.onboardingStep==='CHARACTER'){addDeferral(el,rec);return}
     if(el.querySelector('[data-rc-screen]')?.dataset.rcScreen!==rec.onboardingStep)render(el);
   });
   observer.observe(document.documentElement,{childList:true,subtree:true});
   root.addEventListener('pageshow',()=>render());
   root.addEventListener('ready-character-candidate-ready',()=>render());
 }
 root.ReadyExplorerIntroCanonicalV1=Object.freeze({version:VERSION,CORE6:CORE6.slice(),render,preview,
   snapshot:()=>({...status,currentId,signature_count:pick.size})});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof globalThis!=='undefined'?globalThis:this);
