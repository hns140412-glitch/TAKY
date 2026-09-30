(() => {
'use strict';
if (window.TakyGoogleAccountAuthV1) return;

const VERSION='2026.09.30-google-account-auth-v1';
const GIS_SRC='https://accounts.google.com/gsi/client';
let config=null;
let idToken=null;
let initialized=false;
let familySelection=null;

const clean=v=>typeof v==='string'?v.trim():'';

function setState(state,detail=''){
  document.documentElement.dataset.takyAccountAuth=state;
  const status=document.getElementById('takyAccountAuthStatus');
  if(status) status.textContent=detail||({
    UNCONFIGURED:'계정 인증 설정이 필요해요.',
    LOADING:'Google 계정 연결을 준비하고 있어요.',
    SIGN_IN_REQUIRED:'Google 계정으로 로그인해 주세요.',
    VERIFYING:'계정을 확인하고 있어요.',
    FAMILY_REQUIRED:'사용할 가족을 선택해 주세요.',
    AUTHENTICATED:'계정 연결이 완료됐어요.',
    FAILED:'계정 연결을 완료하지 못했어요.'
  }[state]||state);
}

function injectUi(){
  if(document.getElementById('takyAccountAuthHost')) return document.getElementById('takyAccountAuthHost');
  const host=document.createElement('section');
  host.id='takyAccountAuthHost';
  host.hidden=true;
  host.setAttribute('aria-live','polite');
  host.innerHTML='<div class="takyAuthCard"><div class="takyAuthCopy"><b>TAKY 계정 연결</b><span id="takyAccountAuthStatus">Google 계정으로 로그인해 주세요.</span></div><div id="takyGoogleButton"></div><div id="takyFamilyChoices"></div><button type="button" id="takyAccountSignOut" hidden>계정 연결 해제</button></div>';
  const style=document.createElement('style');
  style.textContent='#takyAccountAuthHost{position:fixed;z-index:3500;inset:auto 14px max(14px,env(safe-area-inset-bottom)) 14px;display:flex;justify-content:center;pointer-events:none}#takyAccountAuthHost[hidden]{display:none}.takyAuthCard{pointer-events:auto;width:min(420px,100%);box-sizing:border-box;padding:16px;border-radius:22px;background:rgba(255,255,255,.96);box-shadow:0 18px 50px rgba(18,56,77,.22);font-family:system-ui,-apple-system,sans-serif;color:#173c53}.takyAuthCopy{display:grid;gap:4px;margin-bottom:12px}.takyAuthCopy b{font-size:15px}.takyAuthCopy span{font-size:12px;opacity:.72}#takyGoogleButton{min-height:40px}#takyFamilyChoices{display:grid;gap:8px;margin-top:10px}#takyFamilyChoices button,#takyAccountSignOut{border:0;border-radius:14px;padding:11px 13px;font-weight:800}#takyFamilyChoices button{background:#eaf5ff;color:#154f73}#takyAccountSignOut{margin-top:10px;background:transparent;color:#6c7880;width:100%}';
  document.head.appendChild(style);
  document.body.appendChild(host);
  document.getElementById('takyAccountSignOut')?.addEventListener('click',signOut);
  return host;
}

function show(){const h=injectUi();h.hidden=false}
function hide(){const h=document.getElementById('takyAccountAuthHost');if(h)h.hidden=true}

function validateConfig(next){
  if(!next||typeof next!=='object') throw new Error('TAKY_ACCOUNT_AUTH_CONFIG_REQUIRED');
  const googleClientId=clean(next.googleClientId),apiBaseUrl=clean(next.apiBaseUrl);
  if(!googleClientId||!apiBaseUrl) throw new Error('TAKY_ACCOUNT_AUTH_CONFIG_INCOMPLETE');
  const u=new URL(apiBaseUrl,location.href);
  const local=['localhost','127.0.0.1'].includes(u.hostname);
  if(!local&&u.protocol!=='https:') throw new Error('TAKY_ACCOUNT_AUTH_HTTPS_REQUIRED');
  return {googleClientId,apiBaseUrl:u.href,preferredFamilyId:clean(next.preferredFamilyId)||null};
}

function loadGis(){
  if(window.google?.accounts?.id) return Promise.resolve();
  return new Promise((resolve,reject)=>{
    const existing=document.querySelector('script[data-taky-gis="1"]');
    if(existing){existing.addEventListener('load',resolve,{once:true});existing.addEventListener('error',()=>reject(new Error('GOOGLE_IDENTITY_SCRIPT_FAILED')),{once:true});return}
    const s=document.createElement('script');
    s.src=GIS_SRC;s.async=true;s.defer=true;s.dataset.takyGis='1';
    s.onload=()=>resolve();s.onerror=()=>reject(new Error('GOOGLE_IDENTITY_SCRIPT_FAILED'));
    document.head.appendChild(s);
  });
}

async function fetchSession(token){
  const endpoint=new URL('/api/family/session',config.apiBaseUrl).href;
  const res=await fetch(endpoint,{method:'POST',headers:{'content-type':'application/json','authorization':'Bearer '+token},body:'{}',cache:'no-store'});
  const body=await res.json().catch(()=>({ok:false,reason:'INVALID_FAMILY_SESSION_RESPONSE'}));
  if(!res.ok||body.ok===false) throw Object.assign(new Error(body.reason||('FAMILY_SESSION_HTTP_'+res.status)),{status:res.status,body});
  const families=Array.isArray(body.session?.families)?body.session.families:[];
  if(!families.length) throw new Error('ACTIVE_FAMILY_SESSION_REQUIRED');
  return {session:body.session,families};
}

function renderFamilyChoices(families){
  const root=document.getElementById('takyFamilyChoices');if(!root)return;
  root.innerHTML='';
  for(const f of families){
    const b=document.createElement('button');
    b.type='button';b.textContent='가족 계정 선택 · '+String(f.family_id);
    b.addEventListener('click',()=>void finishAuthentication(f.family_id));
    root.appendChild(b);
  }
}

async function finishAuthentication(preferredFamilyId){
  if(!idToken) throw new Error('GOOGLE_ID_TOKEN_REQUIRED');
  setState('VERIFYING');
  const sessionResult=await fetchSession(idToken);
  const families=sessionResult.families;
  let familyId=clean(preferredFamilyId)||config.preferredFamilyId;
  if(familyId&&!families.some(f=>clean(f.family_id)===familyId)) throw new Error('PREFERRED_FAMILY_NOT_AUTHORIZED');
  if(!familyId&&families.length===1) familyId=clean(families[0].family_id);
  if(!familyId){
    familySelection=sessionResult;
    renderFamilyChoices(families);
    setState('FAMILY_REQUIRED');
    return {state:'FAMILY_REQUIRED',families:families.map(f=>({family_id:f.family_id,self_member_id:f.self_member_id}))};
  }
  const auth=window.TakyFamilyAuthRuntimeV1;
  if(!auth?.registerCentralBearerProvider||!auth?.installFamilyRuntime) throw new Error('TAKY_FAMILY_AUTH_RUNTIME_REQUIRED');
  auth.registerCentralBearerProvider({apiBaseUrl:config.apiBaseUrl,getIdToken:async()=>idToken,preferredFamilyId:familyId});
  const installed=await auth.installFamilyRuntime();
  setState('AUTHENTICATED');
  const signOut=document.getElementById('takyAccountSignOut');if(signOut)signOut.hidden=false;
  setTimeout(hide,700);
  return {state:'AUTHENTICATED',family_id:installed.family_id};
}

async function onCredential(response){
  try{
    idToken=clean(response?.credential);
    if(idToken.length<16) throw new Error('GOOGLE_ID_TOKEN_REQUIRED');
    await finishAuthentication(config.preferredFamilyId);
  }catch(error){
    idToken=null;setState('FAILED',String(error?.message||error));show();
  }
}

async function start(nextConfig=window.TAKY_ACCOUNT_AUTH_CONFIG){
  try{config=validateConfig(nextConfig)}catch(error){setState('UNCONFIGURED');hide();return {state:'UNCONFIGURED',error:String(error?.message||error)}}
  show();
  setState('LOADING');
  await loadGis();
  if(!window.google?.accounts?.id) throw new Error('GOOGLE_IDENTITY_API_UNAVAILABLE');
  if(!initialized){
    window.google.accounts.id.initialize({client_id:config.googleClientId,callback:onCredential,auto_select:false,cancel_on_tap_outside:true});
    initialized=true;
  }
  const target=document.getElementById('takyGoogleButton');
  target.innerHTML='';
  window.google.accounts.id.renderButton(target,{type:'standard',theme:'outline',size:'large',text:'signin_with',shape:'pill',logo_alignment:'left',width:Math.min(360,Math.max(240,target.clientWidth||320))});
  setState('SIGN_IN_REQUIRED');
  return {state:'SIGN_IN_REQUIRED'};
}

function signOut(){
  idToken=null;familySelection=null;
  try{window.google?.accounts?.id?.disableAutoSelect?.()}catch{}
  try{window.TakyFamilyAuthRuntimeV1?.clear?.()}catch{}
  setState(config?'SIGN_IN_REQUIRED':'UNCONFIGURED');
  show();
}

window.TakyGoogleAccountAuthV1={version:VERSION,start,signOut,status:()=>({state:document.documentElement.dataset.takyAccountAuth||'NOT_STARTED',configured:!!config,authenticated:!!idToken})};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>void start(),{once:true});else void start();
})();