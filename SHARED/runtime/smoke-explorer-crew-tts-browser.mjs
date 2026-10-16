import {createRequire} from 'module';
import {pathToFileURL} from 'url';
import {writeFileSync} from 'fs';
const require=createRequire(import.meta.url);
const {chromium}=require('D:/Git PWA/Play Camp/node_modules/playwright-core');
const root='D:/Git PWA/TAKY/staging/crew_voice_20261012/mock_tts';
const browser=await chromium.launch({headless:true,
 executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
 args:['--autoplay-policy=no-user-gesture-required']});
const result={status:'FAIL',groups:9,characters:24,expected_audio:264,
 page_errors:[],family_samples:[],direct_audio_tested:0};
try{
 const page=await browser.newPage();
 page.on('pageerror',e=>result.page_errors.push(String(e)));
 await page.goto(pathToFileURL(root+'/index.html').href,{waitUntil:'load'});
 await page.waitForFunction(()=>!!window.TakyVoiceDemoState,{timeout:10000});
 result.initial_list=await page.locator('#list button.line').count();
 result.groups_in_select=await page.locator('#family option').count()-1;
 result.characters_in_select=await page.locator('#character option').count()-1;
 await page.locator('#play').click();
 await page.waitForFunction(()=>document.getElementById('status').textContent.includes('재생 시작'),{timeout:10000});
 result.first_clip_status=await page.locator('#status').textContent();
 await page.locator('#stop').click();
 const groups=['VF01','VF02','VF03','VF04','VF05','VF06','SP01','SP02','SP03'];
 for(const family of groups){
  await page.locator('#family').selectOption(family);
  await page.locator('#play').click();
  const outcome=await page.waitForFunction(()=>{
   const s=document.getElementById('status').textContent;
   if(s.includes('재생 시작')||s.includes('재생 실패'))return s;
   return null;
  },{timeout:13000}).then(h=>h.jsonValue());
  result.family_samples.push({family,status:outcome});
  await page.locator('#stop').click();
 }
 result.direct_audio_tested=await page.evaluate(async()=>{
  let n=0;
  const rows=window.TakyVoiceDemoState.mock.clips;
  for(const item of rows.filter((x,i)=>i%33===0)){
   const a=new Audio(item.url);
   try{
    await new Promise((resolve,reject)=>{
      const timeout=setTimeout(()=>reject(new Error('timeout')),6000);
      a.addEventListener('playing',()=>{clearTimeout(timeout);resolve()},{once:true});
      a.addEventListener('error',()=>{clearTimeout(timeout);reject(new Error('audio_error'))},{once:true});
      a.play().catch(reject);
    });n++;
   }finally{a.pause();a.src='';a.load()}
  }
  return n;
 });
 result.status=result.page_errors.length===0&&result.initial_list===264&&result.groups_in_select===9&&
  result.characters_in_select===24&&result.family_samples.every(x=>x.status.includes('재생 시작'))&&
  result.direct_audio_tested===8?'PASS_BROWSER_WAV_MOCK':'FAIL';
}finally{
 await browser.close();
 writeFileSync(root+'/BROWSER_SMOKE_RESULT.json',JSON.stringify(result,null,2));
 console.log(JSON.stringify(result,null,2));
}
if(result.status!=='PASS_BROWSER_WAV_MOCK')process.exitCode=2;
