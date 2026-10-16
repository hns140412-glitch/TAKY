/** Bounded Playwright capture. Evidence-only, NEVER approval/PASS on visual design. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const here=path.dirname(fileURLToPath(import.meta.url));
const base=path.dirname(path.dirname(here));
const evidenceRoot=path.join(base,'TAKY_AI_WORKBENCH','01_BACKLOG_AND_ADOPTION','80_EVIDENCE');
// Prefer TAKY's own existing runtime; reuse Play Camp's installed copy only
// when TAKY has none. Never install packages or call a paid service here.
let chromium;
for(const owner of ['TAKY','Play Camp']){
 try{
   const existing=createRequire(pathToFileURL(path.join(base,owner,'package.json')))('playwright-core');
   chromium=existing.chromium;
   if(chromium)break;
 }catch(err){if(err.code!=='MODULE_NOT_FOUND')throw err;}
}
if(!chromium)throw new Error('EXISTING_PLAYWRIGHT_CORE_RUNTIME_REQUIRED');
const sha=b=>createHash('sha256').update(b).digest('hex');
function contained(p,root){const rel=path.relative(root,p);return rel.length>0&&rel!=='..'&&!rel.startsWith('..'+path.sep)&&!path.isAbsolute(rel);}
function isTarget(url){
 const u=new URL(url);
 if (u.protocol==='data:'){assert.ok(url.length<15000&&url.startsWith('data:text/html,'),'bounded HTML fixture only');return true;}
 assert.ok(u.protocol==='http:'&&['127.0.0.1','localhost','[::1]'].includes(u.hostname)&&!u.username&&!u.password,'only local HTTP allowed');
 return false;
}
async function capture(file){
 const configPath=path.resolve(file);
 assert.ok(contained(configPath,evidenceRoot),'Config outside evidence directory');
 const configBytes=await readFile(configPath);assert.ok(configBytes.length<64000);
 const c=JSON.parse(configBytes.toString('utf8'));
 for(const field of ['work_id','screen_id','run_id'])assert.match(c[field],/^[A-Za-z0-9_.:-]{2,96}$/);
 const {width,height}=c.viewport;
 assert.ok(Number.isInteger(width)&&width>=200&&width<=1920&&Number.isInteger(height)&&height>=200&&height<=1920);
 const fixture=isTarget(c.url);
 const steps=c.steps??[];assert.ok(Array.isArray(steps)&&steps.length<=10);
 for(const step of steps){assert.ok(['click','fill','expectText','expectVisible'].includes(step?.action));
   assert.ok(typeof step.selector==='string'&&step.selector.length>0&&step.selector.length<180);
   if(['fill','expectText'].includes(step.action))assert.ok(typeof step.value==='string'&&step.value.length<400);
 }
 const out=path.join(evidenceRoot,'UI_BROWSER_RECEIPTS',c.run_id);
 assert.ok(contained(out,evidenceRoot));await mkdir(out,{recursive:true});
 const receiptPath=path.join(out,'browser_receipt.json');
 try{await stat(receiptPath);throw Error('Existing run_id cannot be overwritten');}catch(e){if(e.code!=='ENOENT')throw e;}
 let browser;let channel;
 try{
   for(const name of ['chrome','msedge'])try{browser=await chromium.launch({headless:true,channel:name});channel=name;break;}catch{}
   assert.ok(browser,'Chrome or Edge not available');
   const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,
      reducedMotion:'reduce',colorScheme:'light',locale:'ko-KR',serviceWorkers:'block'});
   const page=await context.newPage(), errors=[],done=[];
   page.on('pageerror',e=>errors.push(String(e.message).slice(0,200)));
   await page.route('**/*',async route=>{
     const dest=route.request().url();
     const u=new URL(dest);const ok=['data:','blob:'].includes(u.protocol)
       ||(!fixture&&u.origin===new URL(c.url).origin&&u.protocol==='http:');
     if(ok)await route.continue();else await route.abort();
   });
   await page.goto(c.url,{waitUntil:'load',timeout:12000});
   for(const step of steps){
     const el=page.locator(step.selector);
     const observed={action:step.action,selector:step.selector,status:'PASS'};
     if(step.action==='click')await el.click({timeout:3000});
     if(step.action==='fill')await el.fill(step.value,{timeout:3000});
     if(step.action==='expectVisible'){
       await el.waitFor({state:'visible',timeout:3000});
       observed.observed_visibility='visible';
     }
     if(step.action==='expectText'){
       await el.waitFor({state:'visible',timeout:3000});
       let seen='';
       for(let attempt=0;attempt<35;attempt++){
         seen=(await el.textContent())?.trim()??'';
         if(seen===step.value)break;
         await page.waitForTimeout(120);
       }
       assert.equal(seen,step.value,'expected UI text did not settle');
       observed.expected_text=step.value;
       observed.observed_text=seen;
     }
     done.push(observed);
   }
   await page.evaluate(async()=>{await document.fonts.ready});
   const observed=await page.evaluate(()=>({width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth}));
   assert.deepEqual([observed.width,observed.height],[width,height]);
   assert.equal(errors.length,0,'Page JavaScript errors');
   // Accessibility-state evidence complements, but does not replace, pixels.
   const accessibility=await page.locator('body').ariaSnapshot({timeout:3000});
   assert.ok(accessibility&&accessibility.trim().length>0,'empty accessibility state');
   const maxSnapshotChars=32000;
   const a11yText=accessibility.slice(0,maxSnapshotChars);
   const a11yPath=path.join(out,'accessibility_snapshot.txt');
   await writeFile(a11yPath,a11yText,{flag:'wx'});
   const a11yBytes=Buffer.from(a11yText,'utf8');
   const screenshot=path.join(out,'rendered.png');
   await page.screenshot({path:screenshot,fullPage:false,animations:'disabled'});
   const bytes=await readFile(screenshot);
   const receipt={schema:'TAKY_UI_BROWSER_RUNTIME_RECEIPT_V2',
     status:'SCREENSHOT_CAPTURED_NOT_VISUAL_PASS',work_id:c.work_id,screen_id:c.screen_id,run_id:c.run_id,
     timestamp:new Date().toISOString(),config_sha256:sha(configBytes),config_path:configPath,
     viewport:{width,height},observed,target_kind:fixture?'ISOLATED_DATA_FIXTURE':'LOOPBACK_APP',
     browser_channel:channel,steps:done,page_errors:errors,
     rendered_screenshot:{path:screenshot,sha256:sha(bytes),size_bytes:bytes.length},
     accessibility_snapshot:{path:a11yPath,sha256:sha(a11yBytes),
       size_bytes:a11yBytes.length,truncated:accessibility.length>maxSnapshotChars},
     is_approved_design:false,visual_fidelity_tested:false,release_approved:false};
   await writeFile(receiptPath,JSON.stringify(receipt,null,2),{flag:'wx'});
   await context.close();
   console.log(JSON.stringify({receipt:receiptPath,screenshot,steps:done.length,
     status:receipt.status,target_kind:receipt.target_kind}));
   return receipt;
 }finally{if(browser)await browser.close();}
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 capture(process.argv[2]).catch(e=>{console.error('CAPTURE_BLOCKED',e.message);process.exitCode=2;});
}
export {capture,isTarget};
