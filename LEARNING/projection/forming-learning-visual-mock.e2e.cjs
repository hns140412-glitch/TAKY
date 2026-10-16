'use strict';
/** Headless REAL Chrome interactions of SHA/authority-bound learning mock. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const ROOT=path.resolve(__dirname,'..','..','..','TAKY_AI_WORKBENCH',
 '01_BACKLOG_AND_ADOPTION','80_EVIDENCE','FORMING_LEARNING_VISUAL_MOCK');
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
const tests=fs.readdirSync(ROOT).filter(x=>/^TAKY_FORMING_LEARNING_VISUAL_MOCK_[a-f0-9]{20}\.json$/.test(x));
if(!tests.length)throw Error('ACTUAL_SOURCE_DRIVEN_MOCK_MISSING');
const proof=JSON.parse(fs.readFileSync(path.join(ROOT,tests.sort().at(-1)),'utf8'));
const html=proof.visual_mock_path;
assert(fs.existsSync(html),'Expected rendered mock HTML missing');
assert.equal(sha(fs.readFileSync(html)),proof.visual_mock_sha256);
let browser;
test.before(async()=>{browser=await chromium.launch({headless:true,channel:'chrome'});});
test.after(async()=>{if(browser)await browser.close();});
async function load(w=1180,h=820){
 const page=await browser.newPage({viewport:{width:w,height:h},deviceScaleFactor:1});
 const external=[];
 page.on('request',req=>{if(!req.url().startsWith('file:'))external.push(req.url());});
 await page.goto('file:///'+html.replace(/\\/g,'/'),{waitUntil:'load'});
 assert.equal(await page.locator('button.case').count(),4);
 assert.equal(await page.locator('body').getAttribute('data-production-released'),'false');
 return {page,external};
}
async function current(page,id,approved){
 await page.locator('button.case[data-case="'+id+'"]').click();
 assert.equal(await page.locator('body').getAttribute('data-current-case'),id);
 assert.equal(await page.locator('body').getAttribute('data-mock-approved'),String(approved));
 assert.equal(await page.locator('body').getAttribute('data-production-released'),'false');
 assert.equal(await page.locator('button.case[aria-pressed="true"]').count(),1);
 const status=await page.locator('#approval-status').innerText();
 return status;
}

test('desktop: default, two signed sources, forged signature hold',async()=>{
 const {page,external}=await load(1280,800);
 try{
  assert.match(await page.locator('#approval-status').innerText(),/HOLD/);
  assert.equal(await page.locator('#pattern-output li').count(),0);
  assert.match(await page.locator('#consumer-outcome').innerText(),/차단/);
  assert.match(await current(page,'ref081',true),/서명 일치/);
  const p081=await page.locator('#pattern-output li').allInnerTexts();
  assert.deepEqual(p081,proof.real_selector_pattern_recommendations.ref081.patterns);
  const screenshotApproved=path.join(ROOT,'TAKY_SIGNED_LEARNING_MOCK_DESKTOP_REF081.png');
  await page.screenshot({path:screenshotApproved,fullPage:true});
  assert.match(await current(page,'ref085',true),/서명 일치/);
  const p085=await page.locator('#pattern-output li').allInnerTexts();
  assert.deepEqual(p085,proof.real_selector_pattern_recommendations.ref085.patterns);
  assert.notDeepEqual(p081,p085);
  assert.match(await current(page,'tampered',false),/변조/);
  assert.equal(await page.locator('#pattern-output li').count(),0);
  assert.match(await page.locator('#consumer-outcome').innerText(),/차단/);
  const screenshotRejected=path.join(ROOT,'TAKY_SIGNED_LEARNING_MOCK_DESKTOP_TAMPER_HOLD.png');
  await page.screenshot({path:screenshotRejected,fullPage:true});
  assert.match(await current(page,'none',false),/HOLD/);
  assert.equal(await page.locator('#pattern-output li').count(),0);
  assert.deepEqual(external,[],'No network/API requests permitted');
  console.log(JSON.stringify({case:'desktop_real_clicks',status:'PASS',source_patterns_diff:true,
    tamper_hold:true,none_hold:true,network_requests:0,
    screenshots:[screenshotApproved,screenshotRejected]}));
 }finally{await page.close();}
});

test('tablet: all four controls visible, no horizontal overflow, source preview works',async()=>{
 const {page,external}=await load(1180,820);
 try{
  const dimensions=await page.evaluate(()=>({
   inner:innerWidth,body:document.body.scrollWidth,
   root:document.documentElement.scrollWidth,
   buttons:[...document.querySelectorAll('button.case')].map(x=>{
    const r=x.getBoundingClientRect();
    return {x:r.x,y:r.y,right:r.right,bottom:r.bottom};
   })
  }));
  assert.equal(dimensions.body,dimensions.inner);
  assert.equal(dimensions.root,dimensions.inner);
  assert.equal(dimensions.buttons.length,4);
  assert(dimensions.buttons.every(x=>x.x>=0&&x.right<=1180&&x.y>=0&&x.bottom<=820));
  await current(page,'ref085',true);
  assert.equal(await page.locator('#pattern-output li').count(),3);
  const screenshot=path.join(ROOT,'TAKY_SIGNED_LEARNING_MOCK_TABLET_REF085.png');
  await page.screenshot({path:screenshot,fullPage:true});
  assert.deepEqual(external,[]);
  console.log(JSON.stringify({case:'tablet_1180_820',status:'PASS',horizontal_overflow:false,
    all_case_controls_visible:true,screenshot}));
 }finally{await page.close();}
});

test('mobile: labels readable, controls responsive and release always false',async()=>{
 const {page,external}=await load(390,844);
 try{
  await current(page,'ref081',true);
  assert.equal(await page.locator('#pattern-output li').count(),2);
  const scroll=await page.evaluate(()=>({
   body:document.body.scrollWidth,root:document.documentElement.scrollWidth,
   inner:innerWidth,card:document.querySelector('.panel').getBoundingClientRect().width,
   title:parseFloat(getComputedStyle(document.querySelector('h1')).fontSize)
  }));
  assert.equal(scroll.body,scroll.inner);
  assert.equal(scroll.root,scroll.inner);
  assert(scroll.card>=300);
  assert(scroll.title>=22);
  await current(page,'tampered',false);
  assert.equal(await page.locator('#pattern-output li').count(),0);
  const screenshot=path.join(ROOT,'TAKY_SIGNED_LEARNING_MOCK_MOBILE_HOLD.png');
  await page.screenshot({path:screenshot,fullPage:true});
  assert.deepEqual(external,[]);
  console.log(JSON.stringify({case:'mobile_390_844',status:'PASS',horizontal_overflow:false,
    title_px:scroll.title,network_requests:0,screenshot}));
 }finally{await page.close();}
});
