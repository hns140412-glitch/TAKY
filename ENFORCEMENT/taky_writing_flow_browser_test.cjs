// TAKY writing UI real Chrome local-only integration; not a design approval.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const assert=require('node:assert/strict');
const {createRequire}=require('node:module');
const ROOT=path.resolve(__dirname,'..','..');
let chromium;
for(const owner of ['TAKY','Play Camp']){
 try{chromium=createRequire(path.join(ROOT,owner,'package.json'))('playwright-core').chromium;if(chromium)break;}
 catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e;}
}
if(!chromium)throw Error('PLAYWRIGHT_ALREADY_INSTALLED_REQUIRED');
const BASE_URL=process.env.TAKY_WRITING_TEST_URL||'http://127.0.0.1:8767/';
const EVIDENCE=process.env.TAKY_WRITING_EVIDENCE_DIR||path.join(ROOT,'TAKY_AI_WORKBENCH','50_INTEGRATION_TEST','TAKY_WRITING_MULTICHANNEL_20261016');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function main(){
 const browser=await chromium.launch({headless:true,channel:'chrome',args:['--no-sandbox']});
 const receipt={schema:'TAKY_WRITING_BROWSER_CANDIDATE_TEST_V1',status:'RUNNING',
   approved_mockup:false,publicly_deployed:false,api_calls:0,desktop:{},mobile:{}};
 try{
  const context=await browser.newContext({viewport:{width:1440,height:900},acceptDownloads:true,locale:'ko-KR'});
  fs.mkdirSync(EVIDENCE,{recursive:true});
  const page=await context.newPage(),errors=[],posts=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',req=>{if(req.url().endsWith('/compose'))posts.push(req.postData()||'')});
  await page.route('**/*',async route=>{
    const u=new URL(route.request().url());
    if(['127.0.0.1','localhost'].includes(u.hostname)&&u.protocol==='http:')await route.continue();
    else if(u.protocol==='blob:'||u.protocol==='data:')await route.continue();
    else await route.abort();
  });
  await page.goto(BASE_URL,{waitUntil:'load'});
  assert.match(await page.title(),/TAKY/);
  const health=await context.request.get(BASE_URL+'health');
  assert.equal(health.status(),200);
  const denied=await context.request.post(BASE_URL+'compose',{
    headers:{'Origin':'https://attacker.invalid','Content-Type':'application/json'},
    data:{input:{title:'외부 요청'},genres:['BLOG']}
  });assert.equal(denied.status(),403);
  await page.locator('#title').fill('가족과 공유할 주말 산책 기록');
  await page.locator('#goal').fill('메모에 기록한 장면만 설명한다.');
  await page.locator('#audience').fill('가족');
  await page.locator('#facts').fill('나무 아래 벤치가 있었다 | USER_NOTE\n사진은 한 장만 골랐다 | USER_NOTE');
  await page.locator('#samples').fill('오늘 사진을 다시 보니 그 순간이 생각나요. 참 좋네요!');
  await page.locator('#takeaway').fill('다음에도 기억을 남겨 보고 싶다.');
  await page.locator('#keywords').fill('가족, 산책');
  assert.equal(await page.locator('#modes input:checked').count(),1);
  await page.locator('#modes input[value="SOCIAL_POST"]').check();
  await page.locator('#generate').click();
  await page.locator('#tabs button').first().waitFor({timeout:7000});
  assert.equal(await page.locator('#tabs button').count(),2);
  assert.match(await page.locator('#status').innerText(),/2종 작성 완료/);
  await page.locator('#togglePreview').click();
  assert.ok(await page.locator('#preview h2').count()>0,'formatted preview headings');
  assert.equal(await page.locator('#draft').isHidden(),true);
  await page.locator('#togglePreview').click();
  assert.equal(await page.locator('#draft').isVisible(),true);
  assert.equal(await page.locator('#modes input[value="OFFICE_REPORT"]').count(),0);
  const workDenied=await context.request.post(BASE_URL+'compose',{
    headers:{'Origin':new URL(BASE_URL).origin,'Content-Type':'application/json'},
    data:{input:{title:'업무 혼입 검증',facts:[{text:'검증',source:'TEST'}]},
          genres:['BLOG','OFFICE_REPORT']}
  });
  assert.equal(workDenied.status(),422);
  assert.match((await workDenied.text()),/INVALID_KIND/);
  await page.locator('#tabs button[data-key="SOCIAL_POST"]').click();
  assert.match(await page.locator('#draft').inputValue(),/#가족/);
  await page.locator('#draft').fill((await page.locator('#draft').inputValue())+'\n작성자 수정 사항');
  await page.locator('#tabs button[data-key="BLOG"]').click();
  await page.locator('#tabs button[data-key="SOCIAL_POST"]').click();
  assert.match(await page.locator('#draft').inputValue(),/작성자 수정 사항/);
  await page.locator('#tabs button[data-key="BLOG"]').click();
  const downloadWait=page.waitForEvent('download');
  await page.locator('#save').click();
  const download=await downloadWait; assert.equal(download.suggestedFilename(),'blog.md');
  const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP+7yF3SgAAAABJRU5ErkJggg==','base64');
  await page.locator('#photos').setInputFiles({name:'test-local.png',mimeType:'image/png',buffer:png});
  await page.locator('#pictures .photo input').fill('벤치 옆 나무가 보이는 사진');
  assert.equal(await page.locator('#pictures .photo').count(),1);
  await page.locator('#insights').fill('사진과 메모를 같이 남기면 다음 기록 때 활용하기 편리하다 | F02,P01');
  await page.locator('#generate').click();
  await page.locator('#tabs button[data-key="BLOG"]').waitFor({state:'visible'});
  await page.waitForFunction(()=>document.querySelector('#metrics').textContent.includes('사진 1장'));
  assert.match(await page.locator('#draft').inputValue(),/벤치 옆 나무가 보이는 사진/);
  assert.match(await page.locator('#draft').inputValue(),/다음 기록 때 활용하기 편리하다/);
  assert.match(await page.locator('#metrics').innerText(),/추가 관점 1개/);
  const unsupported=await context.request.post(BASE_URL+'compose',{
    headers:{'Origin':new URL(BASE_URL).origin,'Content-Type':'application/json'},
    data:{input:{title:'근거 없는 인사이트',facts:[{text:'메모 하나'}],
      insights:[{text:'없는 주장을 추가',evidence_ids:['F99']}]},genres:['BLOG']}
  });
  assert.equal(unsupported.status(),422);
  assert.match(await unsupported.text(),/INSIGHT_UNGROUNDED/);
  assert.ok(posts.every(body=>!body.includes('iVBOR')&&!body.includes('data:image')),'Image pixels not sent');
  assert.equal(errors.length,0,'page errors: '+errors.join(','));
  receipt.desktop={
    tabs:await page.locator('#tabs button').count(),fact_input_count:2,image_count:1,
    user_edit_preserved:true,download_name:download.suggestedFilename(),
    image_payload_sent:false,page_errors:errors,
    viewport_overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),
  };
  assert.equal(receipt.desktop.viewport_overflow,false);
  const desktopFile=path.join(EVIDENCE,'writing_desk_desktop_1440.png');
  await page.locator('#togglePreview').click();
  assert.equal(await page.locator('#preview').isVisible(),true);
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:desktopFile,animations:'disabled'});
  await page.locator('#preview').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(EVIDENCE,'writing_desk_desktop_result_1440.png'),animations:'disabled'});
  receipt.desktop.screenshot=desktopFile;receipt.desktop.sha256=sha(fs.readFileSync(desktopFile));
  await context.close();
  const mobile=await browser.newContext({viewport:{width:390,height:844},locale:'ko-KR'});
  const m=await mobile.newPage();const mobileErrors=[];
  m.on('pageerror',e=>mobileErrors.push(e.message));
  await m.goto(BASE_URL,{waitUntil:'load'});
  await m.locator('#title').fill('모바일 글쓰기 검증');
  await m.locator('#facts').fill('가족 일정표에 주말 항목을 적었다 | MEMO');
  assert.equal(await m.locator('#modes input:checked').count(),1);
  await m.locator('#modes input[value="SOCIAL_POST"]').check();
  await m.locator('#generate').click();
  await m.locator('#tabs button').first().waitFor({timeout:7000});
  assert.equal(await m.locator('#tabs button').count(),2);
  assert.match(await m.locator('#draft').inputValue(),/가족 일정표/);
  const width=await m.evaluate(()=>({inner:innerWidth,scroll:document.documentElement.scrollWidth}));
  assert.ok(width.scroll<=width.inner,'mobile horizontal overflow '+JSON.stringify(width));
  assert.equal(mobileErrors.length,0);
  receipt.mobile={width,tab_count:2,page_errors:mobileErrors};
  const mobileFile=path.join(EVIDENCE,'writing_desk_mobile_390.png');
  await m.locator('#togglePreview').click();
  assert.equal(await m.locator('#preview').isVisible(),true);
  await m.evaluate(()=>window.scrollTo(0,0));
  await m.screenshot({path:mobileFile,animations:'disabled'});
  await m.locator('#preview').scrollIntoViewIfNeeded();
  await m.screenshot({path:path.join(EVIDENCE,'writing_desk_mobile_result_390.png'),animations:'disabled'});
  receipt.mobile.screenshot=mobileFile;receipt.mobile.sha256=sha(fs.readFileSync(mobileFile));
  await mobile.close();
  receipt.status='BROWSER_FUNCTION_AND_LAYOUT_SMOKE_PASS';
  receipt.design_approved=false;receipt.source_data_persisted_by_api=false;
  const receiptPath=path.join(EVIDENCE,'writing_desk_browser_receipt.json');
  fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2));
  console.log(JSON.stringify({status:receipt.status,desktop:receipt.desktop,mobile:receipt.mobile,receipt:receiptPath}));
 }finally{await browser.close();}
}
main().catch(e=>{console.error('BROWSER_TEST_FAILED',e.stack);process.exitCode=2;});
