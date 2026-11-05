"""Capture upstream README bytes to independently check local source claims.
Read-only HTTPS GET, no package installation/model/API charge/CURRENT mutation.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,hashlib,re,datetime,os
ROOT=Path(r'D:\Git PWA\TAKY')
OUT=ROOT/'LEARNING/evidence/EVERY_AI_OFFICIAL_SOURCE_CHECK_20261017'
SOURCES={
 'rea':('morluto','rea'),
 'wordcraft':('storytold','wordcraft'),
 'gridcraft':('storytold','gridcraft'),
 'deckcraft':('storytold','deckcraft'),
}
def h(v):return hashlib.sha256(v).hexdigest()
def collect(k,v):
 org,repo=v
 url=f'https://raw.githubusercontent.com/{org}/{repo}/main/README.md'
 req=Request(url,headers={'User-Agent':'TAKY-public-source-verification/1.0','Accept':'text/plain'})
 with urlopen(req,timeout=18) as r:
  content=r.read(600001)
  final=r.geturl()
 if len(content)>600000 or not content:raise ValueError('RAW_INVALID_SIZE:'+k)
 if not final.startswith('https://raw.githubusercontent.com/'+org+'/'+repo+'/'):
  raise ValueError('UNEXPECTED_REDIRECT:'+final)
 text=content.decode('utf-8')
 path=OUT/(k+'_README_'+h(content)[:16]+'.md')
 if path.exists():
  if path.read_bytes()!=content:raise ValueError('UPSTREAM_SHA_CONFLICT')
 else:path.write_bytes(content)
 signals={
  'alpha':bool(re.search(r'\bin alpha\b|\bAlpha\b|is in alpha',text,re.I)),
  'features_estimated':bool(re.search(r'estimat\w*|readiness|ready for real work',text,re.I)),
  'node_support_22_19':bool(re.search(r'22[.]19',text)),
  'mentions_mcp':bool(re.search(r'\bMCP\b',text)),
 }
 lines=text.splitlines()
 evidence=[]
 for i,line in enumerate(lines):
  if any(s in line.lower() for s in ('in alpha','replacing all','replacing powerpoint','ready for real work','22.19','24.11','mcp server')):
   evidence.append({'line':i+1,'quote':line.strip()[:420]})
 return {'name':k,'url':url,'final_url':final,'sha256':h(content),'bytes':len(content),'local_snapshot':str(path),
  'signals':signals,'literal_matches':evidence[:14],'kind':'OFFICIAL_UPSTREAM_README_NOT_EXECUTED'}
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 got=[];errors=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(collect,k,v):k for k,v in SOURCES.items()}
  for f in as_completed(futures):
   try:got.append(f.result())
   except Exception as e:errors.append({'name':futures[f],'error':type(e).__name__+':'+str(e)[:180]})
 got.sort(key=lambda x:x['name'])
 report={'schema':'TAKY_UPSTREAM_PUBLIC_README_EVIDENCE_V1',
  'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'sources':got,'errors':errors,'verified_readme_count':len(got),
  'no_cli_setup_or_package_install':True,'tool_execution_verified':False,
  'paid_api_calls':0,'model_calls':0}
 out=OUT/'OFFICIAL_README_CHECK.json'
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'state':'UPSTREAM_EVIDENCE_CAPTURED','captured':len(got),'errors':errors,
  'sha':{x['name']:x['sha256'][:16] for x in got},'report':str(out)},ensure_ascii=True))
if __name__=='__main__':main()
