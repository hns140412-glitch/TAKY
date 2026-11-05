#!/usr/bin/env python3
"""Careful local-only patch. Verifies anchors & original backups before mutation."""
from pathlib import Path
import sys
ROOT=Path(r"D:\Git PWA\TAKY-MOBILE")
BAK=Path(r"D:\Git PWA\TAKY_ADMIN_PATCH_BACKUPS\admin-progress-20261018")
def change(s,old,new,tag):
 n=s.count(old)
 if n!=1:raise ValueError(f"ANCHOR_{tag}:{n}")
 return s.replace(old,new,1)
index=(ROOT/"index.html").read_text(encoding="utf8")
index=change(index,'<button id="statusBtn" class="status-chip">RUNTIME MVP</button>','<div class="admin-login-top"><button id="adminLoginBtn" class="status-chip" type="button">관리자 로그인</button><button id="statusBtn" class="status-chip">RUNTIME MVP</button></div>',"LOGIN_HEADER")
for old,new in [
 ('<div class="context-card">','<div class="context-card" data-admin-only hidden>'),
 ('<section id="operationsPanel" class="ops-panel"','<section id="operationsPanel" class="ops-panel" data-admin-only hidden'),
 ('<section class="work-snapshot">','<section class="work-snapshot" data-admin-only hidden>'),
 ('<div class="chat" id="chat">','<div class="chat" id="chat" data-admin-only hidden>'),
 ('<div class="composer-wrap">','<div class="composer-wrap" data-admin-only hidden>'),
 ('<section class="screen" data-screen="work">','<section class="screen" data-screen="work" data-admin-only hidden>'),
 ('<section class="screen" data-screen="lab">','<section class="screen" data-screen="lab" data-admin-only hidden>'),
 ('<section class="screen" data-screen="trace">','<section class="screen" data-screen="trace" data-admin-only hidden>'),
 ('<section class="screen" data-screen="ops"','<section class="screen" data-screen="ops" data-admin-only hidden')]:
 index=change(index,old,new,"SCREEN_"+old[:20])
for key in ("work","lab","trace","ops"):
 index=change(index,f'<button class="nav-btn" data-target="{key}">',f'<button class="nav-btn" data-target="{key}" data-admin-only hidden>',"NAV_"+key)
nav='<button class="nav-btn" data-target="ops" data-admin-only hidden>'
index=change(index,nav,'<button class="nav-btn" data-target="admin" data-admin-only hidden><span>⚙</span><small>관리자</small></button>\n      '+nav,"NAV_ADMIN")
marker='      <section class="screen" data-screen="trace" data-admin-only hidden>'
panel='''      <section class="screen" data-screen="admin" data-admin-only hidden aria-label="관리자 대화 및 진행 관제">
        <div class="section-head"><div><div class="eyebrow">ADMIN · WORKBENCH</div><h2>대화 · 프로젝트 진행 관제</h2></div>
          <button id="adminProgressRefreshBtn" class="small-btn" type="button">새로고침</button></div>
        <p class="ops-boundary">관리자 전용 · 프로젝트/주제/WORK_ID/AI 실행·검증 상태를 원자료와 구분해 표시합니다.</p>
        <div id="adminProgressStatus" role="status"></div><div id="adminProgress" aria-live="polite"></div>
        <button id="adminLogoutBtn" class="small-btn" type="button">관리자 로그아웃</button>
      </section>

'''
index=change(index,marker,panel+marker,"PANEL")
marker='  <input id="resumeFileInput" type="file" accept=".md,text/markdown" hidden />'
modal='''  <div id="adminLoginSheet" class="sheet hidden" role="dialog" aria-modal="true" aria-label="관리자 인증">
    <div id="adminLoginBackdrop" class="sheet-backdrop"></div>
    <div class="sheet-panel auth-panel"><div class="sheet-handle"></div><div class="sheet-title">관리자 인증</div>
      <p>기기 인증과 별개로 관리자 권한을 확인합니다.</p>
      <input id="adminLoginKey" class="auth-input" type="password" autocomplete="off" placeholder="관리자 인증키" />
      <p id="adminLoginError" role="alert"></p>
      <div class="auth-actions"><button id="adminLoginCancelBtn" class="quick" type="button">취소</button>
        <button id="adminLoginSubmitBtn" class="send-btn" type="button">인증</button></div>
    </div>
  </div>
'''
index=change(index,marker,modal+marker,"MODAL")
app=(ROOT/"src/app.js").read_text(encoding="utf8")
app=change(app,"import { deriveOperations, renderOperationsStrip, renderOperationsConsole } from './admin-status.mjs';", "import { deriveOperations, renderOperationsStrip, renderOperationsConsole } from './admin-status.mjs';\nimport { adminSession, adminLogin, adminLogout, readAdminProgress, renderAdminProgress } from './admin-progress.mjs';","IMPORT")
app=change(app,'let cacheKeys = null;','let cacheKeys = null;\nlet adminAuthorized=false;\nconst ADMIN_TARGETS=new Set(["work","lab","trace","ops","admin"]);',"STATE")
app=change(app,'${linked ? `<button class="app-manage" type="button" data-app-work="${app.id}">작업</button>` : \'\'}','${adminAuthorized && linked ? `<button class="app-manage" type="button" data-app-work="${app.id}">작업</button>` : \'\'}',"APP_WORK")
app=change(app,'${app.netlifySite ? `<a class="app-manage" href="https://app.netlify.com/projects/${esc(app.netlifySite)}/deploys" target="_blank" rel="noopener noreferrer">배포 관리</a>` : \'\'}','${adminAuthorized && app.netlifySite ? `<a class="app-manage" href="https://app.netlify.com/projects/${esc(app.netlifySite)}/deploys" target="_blank" rel="noopener noreferrer">배포 관리</a>` : \'\'}',"APP_DEPLOY")
app=change(app,'function activateScreen(target) {\n','function activateScreen(target) {\n  if(ADMIN_TARGETS.has(target)&&!adminAuthorized)return false;\n',"SCREEN_GATE")
functions='''function setAdminAccess(granted){
  adminAuthorized=granted===true;
  document.querySelectorAll('[data-admin-only]').forEach(e=>e.hidden=!adminAuthorized);
  document.getElementById('adminLoginBtn').textContent=adminAuthorized?'관리자 열기':'관리자 로그인';
  if(!adminAuthorized&&document.querySelector('.screen.active[data-admin-only]'))activateScreen('taky');
  renderApps();
}
async function refreshAdminProgress(){
  if(!adminAuthorized)return;
  const status=document.getElementById('adminProgressStatus');
  status.textContent='관리자 관제 확인 중…';
  const value=await readAdminProgress();
  if(value.error==='ADMIN_AUTH_REQUIRED'){setAdminAccess(false);status.textContent='관리자 세션 만료';return}
  status.textContent=value.ok?'워크벤치 기준 · 조회 전용':'조회 제한: '+(value.error||'연결 불가');
  renderAdminProgress(document.getElementById('adminProgress'),value);
}
function bindAdminProgress(){
  const sheet=document.getElementById('adminLoginSheet'),key=document.getElementById('adminLoginKey'),error=document.getElementById('adminLoginError');
  const close=()=>{sheet.classList.add('hidden');key.value='';error.textContent=''};
  document.getElementById('adminLoginBtn').addEventListener('click',()=>{
    if(adminAuthorized){activateScreen('admin');refreshAdminProgress();return}
    sheet.classList.remove('hidden');key.focus();
  });
  document.getElementById('adminLoginBackdrop').addEventListener('click',close);
  document.getElementById('adminLoginCancelBtn').addEventListener('click',close);
  document.getElementById('adminLoginSubmitBtn').addEventListener('click',async()=>{
    if(!key.value.trim()){error.textContent='관리자 인증키를 입력하세요.';return}
    error.textContent='확인 중…';
    const response=await adminLogin(key.value.trim());
    if(!response.authorized){error.textContent='관리자 인증 실패 · '+(response.error||'');return}
    close();setAdminAccess(true);activateScreen('admin');await refreshAdminProgress();
  });
  key.addEventListener('keydown',e=>{if(e.key==='Enter')document.getElementById('adminLoginSubmitBtn').click()});
  document.getElementById('adminProgressRefreshBtn').addEventListener('click',refreshAdminProgress);
  document.getElementById('adminLogoutBtn').addEventListener('click',async()=>{await adminLogout();setAdminAccess(false)});
}
async function checkAdminSession(){const value=await adminSession();setAdminAccess(value.authorized);if(adminAuthorized)await refreshAdminProgress()}

'''
app=change(app,'function bindNavigation() {',functions+'function bindNavigation() {',"ADMIN_HANDLERS")
app=change(app,'  bindResume();\n  createFamilySignin().mount();','  bindResume();\n  bindAdminProgress();\n  await checkAdminSession();\n  createFamilySignin().mount();',"BOOT")
css=(ROOT/"src/styles.css").read_text(encoding="utf8")
css+='''

/* Admin-only UI is never revealed by other screen styles. */
[data-admin-only][hidden]{display:none!important}
.admin-login-top{display:flex;flex-wrap:wrap;gap:6px}
.admin-metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(98px,1fr));gap:8px;margin:14px 0}
.admin-metric{background:#17273c;border:1px solid #51677d;padding:10px;border-radius:10px}
.admin-metric small{display:block}.admin-metric strong{display:block;font-size:22px}
.admin-switch{display:flex;gap:7px;flex-wrap:wrap;margin:15px 0}
.admin-switch button[aria-pressed=true]{background:#23496d;border-color:#82beff}
.admin-search{width:100%;max-width:100%;min-height:42px;padding:10px;border-radius:8px;background:#14283f;color:inherit;border:1px solid #56708e;margin:6px 0}
.admin-progress-results{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:12px 0}
.admin-progress-card{background:#16293e;border:1px solid #3f5571;padding:14px;border-radius:12px;overflow-wrap:anywhere}
.admin-progress-card h3{font-size:15px}.admin-progress-card p{font-size:13px;line-height:1.5}
.admin-progress-card code{font-size:11px;overflow-wrap:anywhere}
.admin-caption{font-size:12px;opacity:.85}.admin-error{color:#f3aaa3}
'''
for name,raw in [('index.html',(ROOT/"index.html").read_text(encoding="utf8")),('app.js',(ROOT/"src/app.js").read_text(encoding="utf8")),('styles.css',(ROOT/"src/styles.css").read_text(encoding="utf8"))]:
 if raw!=(BAK/name).read_text(encoding="utf8"):raise ValueError("ORIGINAL_CHANGED_SINCE_BACKUP:"+name)
if '--check' in sys.argv:
 print("PATCH_ANCHORS_OK_AND_BACKUPS_MATCH");sys.exit(0)
(ROOT/"index.html").write_text(index,encoding="utf8")
(ROOT/"src/app.js").write_text(app,encoding="utf8")
(ROOT/"src/styles.css").write_text(css,encoding="utf8")
print("LOCAL_ADMIN_MENU_PATCH_APPLIED_NOT_DEPLOYED")
