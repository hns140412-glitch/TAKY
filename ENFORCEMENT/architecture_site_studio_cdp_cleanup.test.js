// No-Chrome regressions: CDP helper must remove its transient profile on prelaunch/early failure and report it.
const assert=require('node:assert');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const script=path.join(__dirname,'architecture_site_studio_cdp.js');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'taky_cdp_cleanup_test_'));
const run=(chrome,extra={})=>spawnSync(process.execPath,[script,'file:///nonexistent.html'],{encoding:'utf8',timeout:60000,windowsHide:true,
 env:{...process.env,TEMP:root,TMP:root,TMPDIR:root,TAKY_CHROME:chrome,...extra}});
const left=()=>fs.readdirSync(root);
try{
 let r=run(path.join(root,'missing_chrome.exe'));
 assert.notStrictEqual(r.status,0);
 assert.match(r.stderr,/CDP_UI_ERROR Chrome launch failed/);
 assert.deepStrictEqual(left(),[],'prelaunch failure must not leave a profile');
 // browser that exits immediately (node rejects the chrome flags): early failure, no leftovers
 r=run(process.execPath);
 assert.notStrictEqual(r.status,0);
 assert.match(r.stderr,/CDP_UI_ERROR Chrome exited early/);
 assert.deepStrictEqual(left(),[],'early exit must not leave a profile');
 // caller-owned profile is never deleted by the helper
 const own=path.join(root,'caller_owned');fs.mkdirSync(own);
 r=run(path.join(root,'missing_chrome.exe'),{TAKY_CDP_PROFILE:own});
 assert.notStrictEqual(r.status,0);
 assert.ok(fs.existsSync(own),'caller-owned profile must be left to its owner');
 console.log('architecture_site_studio_cdp_cleanup: PASS');
}finally{fs.rmSync(root,{recursive:true,force:true,maxRetries:5,retryDelay:100})}
