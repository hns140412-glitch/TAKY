"""Executable, source-related browser negative-control evidence.
This verifies the *existing local app and test harness*, NOT upstream MCP products.
"""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,hashlib,json,os,time
ROOT=Path(r'D:\Git PWA')
HIDE=ROOT/'Hide & Seek'
BASE=ROOT/'TAKY/LEARNING/evidence/EVERY_AI_BROWSER_METHOD_EXPERIMENT_20261017'
CHECKS=[
 ('positive','tools/code-red-hint-behavior.e2e.cjs',
  'CODE_RED_HINT_BEHAVIOR PASS: 3 hints'),
 ('defect_negative','tools/code-red-hint-negative-control.e2e.cjs',
  'HINT_NEGATIVE_CONTROL_DETECTED'),
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
 if Path(r'D:\Git PWA\TAKY-SOURCE-VAULT\data\site_watch\EVERY_AI_DERIVED_QUARANTINE_20261017.json').is_file():
  raise SystemExit('RETRACTED_DERIVED_LEARNING: source-first revalidation required; historical interpretation must not be regenerated.')
 BASE.mkdir(parents=True,exist_ok=True)
 results=[]
 for name,rel,expected in CHECKS:
  code=HIDE/rel
  started=time.perf_counter()
  proc=subprocess.run(['node',str(code)],cwd=str(HIDE),capture_output=True,
    encoding='utf-8',errors='replace',timeout=65,env={
     **os.environ,'TAKY_QA_SYNTHETIC':'1','TAKY_QA_NETWORK':'MOCK_ONLY'})
  data={'test':name,'command':['node',str(code)],
   'source_test_sha256':sha(code),'runtime_seconds':round(time.perf_counter()-started,2),
   'exit_code':proc.returncode,'stdout':proc.stdout[-3800:],
   'stderr':proc.stderr[-1400:],
   'expected_signal':expected,'signal_seen':expected in (proc.stdout+proc.stderr),
   'actual_app_under_test':str(HIDE/'index.html'),
   'actual_app_hash':sha(HIDE/'index.html'),
   'browser':'headless Google Chrome via installed playwright-core',
   'test_scope':'LOCAL_REAL_APP_SYNTHETIC_SHEET_NOT_PRODUCTION_DATA',
   'upstream_chrome_devtools_mcp_invoked':False}
  data['run_state']='PASS' if proc.returncode==0 and data['signal_seen'] else 'FAIL'
  results.append(data)
 doc={'schema':'TAKY_EVERY_AI_BROWSER_LEARNING_METHOD_RUN_V1',
 'run_at':datetime.now(timezone.utc).isoformat(),
 'source_articles':['https://every-ai-guides.vercel.app/posts/chrome-devtools-mcp',
 'https://every-ai-guides.vercel.app/posts/claude-verify-skills-5'],
 'evaluation':'LOCAL_CHROME_BEHAVIOR_AND_DEFECT_DETECTION',
 'the_article_specific_mcp_not_used':True,
 'not_app_wide_qa':True,
 'cases':results,
 'positive_pass':results[0]['run_state']=='PASS',
 'negative_control_detected':results[1]['run_state']=='PASS',
 'independent_task_validation_scope':'HINT_NO_ANSWER_LEAK_AND_RETRIEVAL_OUTCOME',
 'no_paid_api':True,'no_deploy':True}
 out=BASE/'BROWSER_NEGATIVE_CONTROL_RUN.json'
 out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'state':'PASS' if all(r['run_state']=='PASS' for r in results) else 'FAIL',
  'checks':[{k:r[k] for k in ('test','exit_code','run_state','runtime_seconds')} for r in results],
  'receipt':str(out)},ensure_ascii=True))
 if not all(r['run_state']=='PASS' for r in results):raise SystemExit(1)
if __name__=='__main__':run()
