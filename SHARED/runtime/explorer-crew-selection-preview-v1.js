/* TAKY Companion picker: tap any available card to hear its own signature
  and see the same exact text. Preview never changes relationship. */
(function(root,factory){
 const api=factory();
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else if(root)root.TakyExplorerCrewSelectionPreview=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const CORE6=new Set(['dubi','lori','ink','nova','take','zero']);
 const SELECTABLE=new Set(['COMPANION_AVAILABLE','COMPANION','MAIN_COMPANION']);
 const names=['두비','로리','잉크','노바','테이크','제로','솔라','벨로','모카','니아','키로','피치',
 '민트','토토','루네','포포','마루','보리','린','루미','테스','셀','제이크','비비'];
 const ids=['dubi','lori','ink','nova','take','zero',...Array.from({length:18},(_,i)=>'guide-'+String(i+7).padStart(2,'0'))];
 const LABELS=Object.fromEntries(ids.map((id,i)=>[id,names[i]]));
 const CSS=[
 '.taky-pick-launch{position:fixed;right:12px;bottom:151px;z-index:3100;background:#edf3e9;color:#295d40;border:1px solid #abcbb1;border-radius:24px;padding:10px 13px;font:700 12px system-ui;cursor:pointer}',
 '.taky-pick-shade{position:fixed;inset:0;z-index:21000;display:flex;align-items:center;justify-content:center;background:#172a2788;padding:12px;font-family:system-ui,sans-serif}',
 '.taky-pick-modal{background:#fffdf8;border-radius:20px;width:min(720px,100%);max-height:92dvh;display:flex;flex-direction:column;overflow:hidden;color:#253d31;box-shadow:0 16px 48px #16282155}',
 '.taky-pick-head{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:18px 19px 12px}',
 '.taky-pick-head h2{font-size:20px;margin:0}.taky-pick-head p{margin:7px 0 0;color:#718677;font-size:12px}',
 '.taky-pick-close{border:0;border-radius:50%;width:37px;height:37px;background:#ebf1ea;font-size:24px;cursor:pointer}',
 '.taky-pick-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;padding:8px 16px;max-height:47dvh;overflow:auto}',
 '.taky-pick-card{background:#f5f9f3;border:1px solid #d6e5d9;border-radius:12px;padding:13px 6px;display:flex;flex-direction:column;align-items:center;gap:6px;cursor:pointer;color:#304a3c}',
 '.taky-pick-card[aria-pressed=true]{background:#e0f3e5;border:2px solid #76a88a}.taky-pick-card img{width:76px;height:76px;object-fit:contain;display:block}.taky-pick-card span{font-size:23px}.taky-pick-card b{font-size:14px}.taky-pick-card small{font-size:10px;color:#678675}',
 '.taky-pick-bubble{background:#e9f5e9;border:1px solid #bddcc6;border-radius:15px;margin:10px 16px;padding:14px 17px;min-height:95px;position:relative}',
 '.taky-pick-bubble:before{content:"";position:absolute;top:-8px;left:25px;width:13px;height:13px;background:#e9f5e9;transform:rotate(45deg);border-left:1px solid #bddcc6;border-top:1px solid #bddcc6}',
 '.taky-pick-speaker{font-size:12px;font-weight:800;color:#44765b}.taky-pick-text{font-size:17px;line-height:1.55;margin:7px 0}.taky-pick-status{font-size:11px;color:#597f67}',
 '.taky-pick-bottom{display:flex;gap:10px;justify-content:space-between;align-items:center;padding:0 16px 17px}.taky-pick-note{font-size:11px;color:#63796a;line-height:1.5}',
 '.taky-pick-confirm{background:#437359;color:white;border:0;border-radius:10px;padding:11px 14px;font-size:12px;font-weight:700;white-space:nowrap;cursor:pointer}.taky-pick-confirm:disabled{opacity:.4}',
 '@media(min-width:600px){.taky-pick-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}'
 ].join('\n');
 function create({registry,engine,app_id,doc=typeof document!=='undefined'?document:null,
  readRelation=null,onConfirm=null,allowedIds=null,imageBase='./characters/ui_cutouts/'}={}){
  if(!doc||!registry?.rows||!engine?.play||!engine?.stop)throw Error('PICKER_NEEDS_CANONICAL_AUDIO');
  const signature=new Map(registry.rows.filter(r=>r.kind==='SIGNATURE'&&r.scope==='MAIN_CREW').map(r=>[r.character_id,r]));
  if(signature.size!==24)throw Error('PICKER_NEEDS_24_SIGNATURES');
  const trace={tap_ids:[],play_results:[],commit_results:[]};
  let overlay=null,selected=null,revision=0,launcher=null,previousFocus=null;
  const relation=()=>{try{return readRelation?.()||null}catch{return null}};
  function allowed(){
   if(Array.isArray(allowedIds))return new Set(allowedIds.filter(id=>signature.has(id)));
   const ids=new Set(CORE6),rel=relation();
   for(const [id,member] of Object.entries(rel?.members||{}))
    if(signature.has(id)&&member&&['KNOWN','AFFINITY_BUILDING','COMPANION_AVAILABLE','COMPANION','MAIN_COMPANION'].includes(member.relation_state))ids.add(id);
   return ids;
  }
  const canSelect=id=>!!(relation()?.members?.[id]&&SELECTABLE.has(relation().members[id].relation_state)&&typeof onConfirm==='function');
  function renderSpeech(id,status){
   if(!overlay)return;
   const row=signature.get(id);
   overlay.querySelector('[data-taky-who]').textContent=id?LABELS[id]:'탐험대원';
   overlay.querySelector('[data-taky-speech]').textContent=row?.exact_text||'탐험대원을 터치하면 목소리와 대사가 나와요.';
   overlay.querySelector('[data-taky-status]').textContent=status||'';
   const b=overlay.querySelector('[data-taky-confirm]');
   b.disabled=!id||!canSelect(id);b.textContent=relation()?.main_character_id===id?'이미 주 동행 중':'동행 확정';
   overlay.querySelector('[data-taky-note]').textContent=id&&!canSelect(id)?
    '목소리 미리듣기입니다. 동행 확정은 관계·해금 조건을 충족한 뒤 가능합니다.':
    '터치하면 음성 미리듣기, 동행 확정은 별도입니다.';
  }
  function stop(){revision++;engine.stop()}
  async function preview(id){
   if(!allowed().has(id))return {ok:false,status:'NOT_AVAILABLE'};
   stop();const ticket=revision;selected=id;const row=signature.get(id);
   overlay?.querySelectorAll('[data-taky-id]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.takyId===id?'true':'false'));
   renderSpeech(id,'재생 중...');
   trace.tap_ids.push(id);
   let response;
   try{
    response=await engine.play({app_id,character_id:id,intent:'GREET',locale:'ko-KR',
      dialogue:{source:'APPROVED_BOARD_SIGNATURE',text:row.exact_text}});
   }catch(e){response={ok:false,status:'AUDIO_EXCEPTION',error:String(e)}}
   if(ticket!==revision)return {...response,status:'SUPERSEDED'};
   trace.play_results.push({id,key:response.key||null,status:response.status,mode:response.mode||null});
   renderSpeech(id,response.ok?(response.mode==='APPROVED_MP3'?'확정 녹음 재생':'임시 TTS 재생'):'재생 실패: '+response.status);
   return response;
  }
  async function confirm(){
   if(!selected||!canSelect(selected))return {ok:false,status:'GATE_NOT_MET'};
   let response;try{response=await onConfirm({character_id:selected,app_id})}catch(e){response={ok:false,reason:String(e)}}
   const result=response?.ok&&response?.persisted?{ok:true,status:'MAIN_COMPANION_SAVED'}:
     {ok:false,status:'SELECTION_NOT_PERSISTED',reason:response?.reason||null};
   trace.commit_results.push(result);
   renderSpeech(selected,result.ok?'동행 확정 완료':'동행 확정 미완료');
   return result;
  }
  function close(){stop();overlay?.remove();overlay=null;previousFocus?.focus?.()}
  function open(){
   if(overlay)return overlay;
   previousFocus=doc.activeElement;
   const shade=doc.createElement('div');shade.className='taky-pick-shade';shade.setAttribute('role','presentation');
   const modal=doc.createElement('section');modal.className='taky-pick-modal';modal.setAttribute('role','dialog');
   modal.setAttribute('aria-modal','true');modal.setAttribute('aria-label','동행 탐험대원 선택');
   const head=doc.createElement('header');head.className='taky-pick-head';
   const title=doc.createElement('div');
   const h=doc.createElement('h2');h.textContent='동행 탐험대원 만나보기';
   const d=doc.createElement('p');d.textContent='각 캐릭터를 누르면 인사 음성이 나오고 말풍선이 나타나요.';
   title.append(h,d);
   const x=doc.createElement('button');x.type='button';x.className='taky-pick-close';x.textContent='×';
   x.setAttribute('aria-label','닫기');x.onclick=close;head.append(title,x);
   const list=doc.createElement('div');list.className='taky-pick-grid';
   for(const id of ids.filter(id=>allowed().has(id))){
    const card=doc.createElement('button');card.type='button';card.className='taky-pick-card';
    card.dataset.takyId=id;card.setAttribute('aria-pressed','false');
    const mark=doc.createElement('img');mark.src=imageBase+id+'.png';mark.alt='';mark.loading='lazy';
    mark.onerror=()=>{const fallback=doc.createElement('span');fallback.textContent='✦';mark.replaceWith(fallback)};
    const name=doc.createElement('b');name.textContent=LABELS[id];
    const sub=doc.createElement('small');sub.textContent=signature.get(id).voice_family.startsWith('SP')?'특별 탐험대원':'탐험대원';
    card.append(mark,name,sub);card.addEventListener('click',()=>void preview(id));list.appendChild(card);
   }
   const bubble=doc.createElement('div');bubble.className='taky-pick-bubble';
   for(const [selector,cls] of [['Who','taky-pick-speaker'],['Speech','taky-pick-text'],['Status','taky-pick-status']]){
    const p=doc.createElement('div');p.dataset['taky'+selector]='';p.className=cls;bubble.appendChild(p);
   }
   const foot=doc.createElement('div');foot.className='taky-pick-bottom';
   const note=doc.createElement('div');note.dataset.takyNote='';note.className='taky-pick-note';
   const confirmBtn=doc.createElement('button');confirmBtn.type='button';confirmBtn.className='taky-pick-confirm';
   confirmBtn.dataset.takyConfirm='';confirmBtn.disabled=true;confirmBtn.textContent='동행 확정';
   confirmBtn.onclick=()=>void confirm();foot.append(note,confirmBtn);
   modal.append(head,list,bubble,foot);shade.appendChild(modal);shade.addEventListener('click',e=>{if(e.target===shade)close()});
   overlay=shade;doc.body.appendChild(shade);renderSpeech(null,'');x.focus();return shade;
  }
  function mount(){
   if(!doc.getElementById('takyPickStyle')){const sheet=doc.createElement('style');sheet.id='takyPickStyle';sheet.textContent=CSS;doc.head.appendChild(sheet)}
   launcher=doc.getElementById('takyCrewSelectionLauncher');
   if(!launcher){launcher=doc.createElement('button');launcher.type='button';launcher.id='takyCrewSelectionLauncher';
    launcher.className='taky-pick-launch';launcher.textContent='동행 탐험대원 선택';launcher.onclick=open;doc.body.appendChild(launcher)}
   doc.addEventListener('keydown',e=>{if(!overlay)return;
    if(e.key==='Escape'){e.preventDefault();close()}
    if(e.key==='Tab'){const choices=[...overlay.querySelectorAll('button:not([disabled])')];
      if(!choices.length)return;
      if(e.shiftKey&&doc.activeElement===choices[0]){e.preventDefault();choices.at(-1).focus()}
      else if(!e.shiftKey&&doc.activeElement===choices.at(-1)){e.preventDefault();choices[0].focus()}
    }});
   return launcher;
  }
  return Object.freeze({mount,open,close,preview,confirm,stop,
   snapshot:()=>({opened:!!overlay,selected,visible_ids:[...allowed()],...trace})});
 }
 return Object.freeze({VERSION:'TAKY_CREW_SELECTION_PREVIEW_V1',CORE6,LABELS,create});
});