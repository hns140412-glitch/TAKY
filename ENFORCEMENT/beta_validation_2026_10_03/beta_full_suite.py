from pathlib import Path
import subprocess, json, os, sys, time
ROOT=Path(__file__).resolve().parents[2]
env=os.environ.copy(); env['PYTHONUTF8']='1'
commands=[]
for f in sorted((ROOT/'ENFORCEMENT').glob('*_test.py')):
    commands.append([sys.executable,'-B',str(f.relative_to(ROOT))])
extras=[
 [sys.executable,'-B','ENFORCEMENT/claude_hook_regression.py'],
 [sys.executable,'-B','ENFORCEMENT/outcome_hook_regression.py'],
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
commands.extend(extras)
for base in ['BADGE','SHARED','LEARNING']:
    for f in sorted((ROOT/base).rglob('*.test.js')):
        commands.append(['node',str(f.relative_to(ROOT))])
results=[]; started=time.time()
for argv in commands:
    t=time.time()
    try:
        p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
        results.append({'argv':argv,'exit':p.returncode,'seconds':round(time.time()-t,3),
          'stdout':p.stdout[-2500:],'stderr':p.stderr[-2500:]})
    except subprocess.TimeoutExpired as e:
        results.append({'argv':argv,'exit':'TIMEOUT','seconds':round(time.time()-t,3),
          'stdout':'','stderr':'timeout'})
fails=[r for r in results if r['exit']!=0]
payload={'total':len(results),'failures':len(fails),'seconds':round(time.time()-started,3),'results':results}
Path(__file__).with_name('beta_full_suite.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={'total':len(results),'failures':len(fails),'seconds':payload['seconds'],
 'failed':[{'argv':r['argv'],'exit':r['exit']} for r in fails]}
Path(__file__).with_name('beta_full_suite.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
