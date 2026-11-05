// Browser-level evidence for ArchiGrow massing. Uses existing local puppeteer.
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const puppeteer=require('C:/Users/YKH_1507-03/AppData/Local/npm-cache/_npx/4b4c857f6efdfb61/node_modules/puppeteer/lib/puppeteer/puppeteer.js');
const viewer=process.argv[2],out=process.argv[3];
(async()=>{
 const browser=await puppeteer.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
 args:['--disable-extensions','--disable-background-networking','--no-first-run','--disable-dev-shm-usage']});
 const page=await browser.newPage();
 let errors=[];page.on('pageerror',x=>errors.push(String(x)));page.on('console',x=>{if(x.type()==='error')errors.push(x.text())});
 await page.setViewport({width:1440,height:900,deviceScaleFactor:1});
 await page.goto(pathToFileURL(viewer).href,{waitUntil:'load'});
 await page.waitForSelector('#metrics .metric');
 const state=()=>page.evaluate(()=>({
 title:document.querySelector('#strategyName')?.textContent,
 metrics:[...document.querySelectorAll('#metrics .metric')].map(x=>x.textContent.trim()),
 canvas:{width:document.querySelector('canvas').width,height:document.querySelector('canvas').height}
 }));
 const balanced=await state();
 await page.select('#strategy','1');
 const sculptural=await state();
 await page.screenshot({path:path.join(out,'massing_sculptural_browser.png')});
 await page.$eval('#levels',el=>{el.value='12';el.dispatchEvent(new Event('input',{bubbles:true}))});
 const cropped=await state();
 const ok=balanced.title.includes('BALANCED')&&sculptural.title.includes('SCULPTURAL')
   &&balanced.metrics.some(x=>x.includes('6,486'))&&balanced.metrics.some(x=>x.includes('523.1%'))
   &&sculptural.metrics.some(x=>x.includes('6,486'))&&cropped.title.includes('12 FLOOR')
   &&!cropped.metrics.some(x=>x.includes('6,486'))&&cropped.metrics.some(x=>x.includes('42m'))
   &&balanced.canvas.width>1000&&errors.length===0;
 const result={schema:'ARCHIGROW_MASSING_BROWSER_QA_V1',pass:ok,
   balanced,sculptural,cropped,errors,
   claim:'Browser rendered and interacted; synthetic geometry only, no legal verification'};
 fs.writeFileSync(path.join(out,'browser_qa_receipt.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({pass:ok,balanced,sculptural,cropped,errors}));
 await browser.close();
 process.exit(ok?0:2);
})().catch(err=>{console.error(err.stack);process.exit(1)});
