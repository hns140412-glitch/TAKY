from pathlib import Path
import subprocess, json, os, sys, time
ROOT=Path(__file__).resolve().parents[2]
env=os.environ.copy(); env['PYTHONUTF8']='1'
commands=[]
for f in sorted((ROOT/'ENFORCEMENT').glob('*_test.py')):
    commands.append([sys.executable,'-B',str(f.relative_to(ROOT))])
extra=[
 [sys.executable,'-B','ENFORCEMENT/claude_hook_regression.py'],
 [sys.executable,'-B','ENFORCEMENT/outcome_hook_regression.py'],
 [sys.executable,'-B','ENFORCEMENT/evidence_bridge_regression.py'],
 [sys.executable,'-B','ENFORCEMENT/rule_registry_lint.py'],
 [sys.executable,'-B','ENFORCEMENT/alpha_manifest_validator.py','HANDOFF/TAKY_ALPHA_LOCAL_MANIFEST_2026-10-03.json'],
 [sys.executable,'-B','ENFORCEMENT/handoff_bundle_validator.py','ENFORCEMENT/fixtures/handoff_bundle_pass'],
]
commands.extend(extra)
for base in ['BADGE','SHARED','LEARNING']:
    for f in sorted((ROOT/base).rglob('*.test.js')):
        commands.append(['node',str(f.relative_to(ROOT))])
results=[]; started=time.time()
for argv in commands:
    t=time.time()
    try:
        p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
        results.append({'argv':argv,'exit':p.returncode,'seconds':round(time.time()-t,3),
          'stdout':p.stdout[-3000:],'stderr':p.stderr[-3000:]})
    except subprocess.TimeoutExpired as e:
        results.append({'argv':argv,'exit':'TIMEOUT','seconds':round(time.time()-t,3),
          'stdout':(e.stdout or '')[-3000:] if isinstance(e.stdout,str) else '',
          'stderr':(e.stderr or '')[-3000:] if isinstance(e.stderr,str) else ''})
out=Path(__file__).with_name('full_suite_rerun.json')
out.write_text(json.dumps({'total':len(results),'failures':sum(r['exit']!=0 for r in results),
 'seconds':round(time.time()-started,3),'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
fails=[r for r in results if r['exit']!=0]
print(json.dumps({'total':len(results),'failures':len(fails),
 'seconds':round(time.time()-started,3),
 'failed':[{'argv':r['argv'],'exit':r['exit']} for r in fails]},ensure_ascii=False,indent=2))
