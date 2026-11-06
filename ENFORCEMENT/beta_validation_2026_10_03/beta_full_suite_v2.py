from pathlib import Path
import subprocess, json, os, sys, time
ROOT=Path(__file__).resolve().parents[2]
env=os.environ.copy(); env['PYTHONUTF8']='1'
runs=[]
for f in sorted((ROOT/'ENFORCEMENT').glob('*_test.py')):
    cwd=ROOT/'ENFORCEMENT' if f.name=='reference_acquisition_runtime_binding_test.py' else ROOT
    argv=[sys.executable,'-B',f.name if cwd.name=='ENFORCEMENT' else str(f.relative_to(ROOT))]
    runs.append((argv,cwd))
extras=[
 [sys.executable,'-B','ENFORCEMENT/evidence_bridge_regression.py'],
 [sys.executable,'-B','ENFORCEMENT/rule_registry_lint.py'],
 [sys.executable,'-B','ENFORCEMENT/beta_owner_rule_consistency_validator.py'],
 [sys.executable,'-B','ENFORCEMENT/beta_resume_authority_consistency_validator.py'],
 [sys.executable,'-B','ENFORCEMENT/beta_claim_boundary_validator.py'],
 [sys.executable,'-B','ENFORCEMENT/semantic_current_resolver.py'],
 [sys.executable,'-B','ENFORCEMENT/handoff_bundle_validator.py','ENFORCEMENT/fixtures/handoff_bundle_pass'],
 [sys.executable,'-B','ENFORCEMENT/taky_gate.py','--replay','ENFORCEMENT/replay_cases_v5.json'],
 [sys.executable,'-B','ENFORCEMENT/taky_gate.py','--replay','ENFORCEMENT/replay_cases_v6.json'],
]
runs.extend((argv,ROOT) for argv in extras)
for base in ['BADGE','SHARED','LEARNING']:
    for f in sorted((ROOT/base).rglob('*.test.js')):
        runs.append((['node',str(f.relative_to(ROOT))],ROOT))
results=[]; started=time.time()
for argv,cwd in runs:
    t=time.time()
    try:
        q=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=120)
        results.append({'argv':argv,'cwd':str(cwd),'exit':q.returncode,'seconds':round(time.time()-t,3),
                        'stdout':q.stdout[-2000:],'stderr':q.stderr[-2000:]})
    except subprocess.TimeoutExpired:
        results.append({'argv':argv,'cwd':str(cwd),'exit':'TIMEOUT','seconds':round(time.time()-t,3),'stdout':'','stderr':'timeout'})
fails=[r for r in results if r['exit']!=0]
summary={'total':len(results),'failures':len(fails),'seconds':round(time.time()-started,3),
         'failed':[{'argv':r['argv'],'cwd':r['cwd'],'exit':r['exit']} for r in fails]}
Path(__file__).with_name('beta_full_suite_v2.json').write_text(json.dumps({'summary':summary,'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
Path(__file__).with_name('beta_full_suite_v2.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
