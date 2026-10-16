'use strict';
// Localhost-only static fixture host for an existing cross-app browser E2E.
// Start via family_group_periodic_qa.cjs only; no external server or provider access.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(String(process.argv[2]||'')),port=Number(process.argv[3]);
if(!fs.existsSync(root)||!fs.statSync(root).isDirectory()||!Number.isInteger(port)||port<1024||port>65535)process.exit(2);
const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.webmanifest':'application/manifest+json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.mp3':'audio/mpeg','.wav':'audio/wav','.woff2':'font/woff2','.wasm':'application/wasm','.ico':'image/x-icon','.txt':'text/plain'};
// GET-only sanitized QA summary, served only when the fixture root is TAKY-MOBILE. Never the raw report.
const qaReport=path.resolve(__dirname,'..','.local','family-qa','latest-deep.json');
const clip=(v,n)=>String(v??'').slice(0,n);
function qaSummary(){
 try{
  const j=JSON.parse(fs.readFileSync(qaReport,'utf8')),s=j.statuses;
  if(!j||j.contract!=='TAKY_FAMILY_PERIODIC_QA_V1'||!s||!Array.isArray(j.gaps))return null;
  const n=v=>Number.isInteger(v)&&v>=0?v:null,statuses={passed:n(s.passed),failed:n(s.failed),blocked:n(s.blocked),openGaps:n(s.openGaps)};
  if(Object.values(statuses).includes(null)||!Number.isFinite(Date.parse(j.finishedAt)))return null;
  const out={contract:clip(j.contract,64),mode:clip(j.mode,16),finishedAt:clip(j.finishedAt,40),productionVerified:j.productionVerified===true,statuses,verdict:clip(j.verdict,64),
   gaps:j.gaps.slice(0,20).map(g=>({id:clip(g?.id,64),priority:clip(g?.priority,8),area:clip(g?.area,32),why:clip(g?.why,200)}))};
  const body=JSON.stringify(out);
  return body.length<=8192?body:null;
 }catch{return null;}
}
http.createServer((req,res)=>{
 if(req.url==='/__taky_qa_summary'){
  const body=req.method==='GET'&&path.basename(root)==='TAKY-MOBILE'?qaSummary():null;
  if(!body){res.writeHead(404,{'Cache-Control':'no-store'});return res.end('not found');}
  res.writeHead(200,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});return res.end(body);
 }
 if(req.url==='/__taky_qa_probe'){res.writeHead(200,{'Content-Type':'text/plain','Cache-Control':'no-store'});return res.end('TAKY_QA_LOCAL_FIXTURE_V1');}
 let name;
 try{name=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname).replace(/^\/+/, '')||'index.html';}
 catch{res.writeHead(400);return res.end('bad path');}
 let file=path.resolve(root,name);
 if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end('forbidden');}
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){
   if(!path.extname(name)) file=path.join(root,'index.html');
   else{res.writeHead(404);return res.end('not found');}
 }
 if(!fs.existsSync(file)){res.writeHead(404);return res.end('not found');}
 res.setHeader('Cache-Control','no-store');
 res.setHeader('Content-Type',(mime[path.extname(file).toLowerCase()]||'application/octet-stream')+(mime[path.extname(file).toLowerCase()]?.startsWith('text/')?'; charset=utf-8':''));
 fs.createReadStream(file).on('error',()=>res.destroy()).pipe(res);
}).listen(port,'127.0.0.1',()=>console.log('TAKY_QA_FIXTURE_READY:'+port));
