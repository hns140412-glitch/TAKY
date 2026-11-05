"""Learning decisions from source originals, 4 official upstream READMEs,
and real local Chrome positive/negative evidence. No promotion or paid call.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re,subprocess,shutil
T=Path(r'D:\Git PWA\TAKY')
V=T.parent/'TAKY-SOURCE-VAULT'
P=T/'LEARNING/evidence'
H=P/'EVERY_AI_SOURCE_BOUND_METHOD_LEARNING_CANDIDATES_20261017.json'
B=P/'EVERY_AI_BROWSER_METHOD_EXPERIMENT_20261017/BROWSER_NEGATIVE_CONTROL_RUN.json'
U=P/'EVERY_AI_OFFICIAL_SOURCE_CHECK_20261017/OFFICIAL_README_CHECK.json'
O=V/'reports/site_watch/reviews/every_ai_20261017/ALL_118_RAW_AUDIT.json'
QA=T/'ENFORCEMENT/family_group_periodic_qa.cjs'
DEST=P/'EVERY_AI_METHOD_LEARNING_DECISIONS_20261017.json'
M=DEST.with_suffix('.md')
def get(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_browser(b):
 if [x['test'] for x in b['cases']]!=['positive','defect_negative']:return False
 for x,key in zip(b['cases'],('CODE_RED_HINT_BEHAVIOR PASS: 3 hints','HINT_NEGATIVE_CONTROL_DETECTED')):
  if (x['exit_code']!=0 or x['run_state']!='PASS' or
     not x['signal_seen'] or key not in x['stdout']+x['stderr'] or
     h(x['command'][1])!=x['source_test_sha256'] or
     h(x['actual_app_under_test'])!=x['actual_app_hash']):return False
 return b['the_article_specific_mcp_not_used'] is True
def upstream_map(up):
 x={z['name']:z for z in up['sources']}
 if set(x)!={'rea','wordcraft','gridcraft','deckcraft'} or up['errors']:return None
 for name,s in x.items():
  if h(s['local_snapshot'])!=s['sha256']:return None
  if not s['url'].startswith('https://raw.githubusercontent.com/'):return None
  if name!='rea' and not s['signals']['alpha']:return None
 return x
def source_check(hypotheses):
 a=get(O)['records'];originals={x['url']:x for x in a}
 pointer=get(V/'reports/site_watch/SITE_MINING_EVIDENCE_ACTIVE.json')
 mined=get(Path(pointer['path']))
 ms={x['source_id']:x for x in mined['sources']}
 if h(pointer['path'])!=pointer['sha256']:return False
 for x in hypotheses['candidates']:
  e=x['source_grounding'];src=originals[e['source_url']]
  s=ms[e['source_id']]
  if h(src['raw_path'])!=e['source_sha256'] or s['raw_sha256']!=e['source_sha256']:return False
  unit=next((u for u in s['units'] if u['unit_id']==e['unit_id']),None)
  if unit is None or unit['content_sha256']!=e['unit_sha256'] or e['exact_quote'] not in unit['excerpt']:return False
 return len(a)==118 and len(hypotheses['candidates'])==12

GAPS={
 'DATA_METRIC_RECALC':('HOLD_BASE_DATA_MISSING','Reported 49-post correlations lack a verified input data file for independent recalculation.'),
 'ROLE_PROMPT_NOT_AGENT':('HOLD_EXECUTION_TRACE_MISSING','Thirty suggested workflows are not verified as thirty continuously acting processes.'),
 'MANUAL_TO_ACTUAL_ENFORCEMENT':('HOLD_SKILL_EXECUTION_TRACE_MISSING','A proposed SKILL.md procedure has no controlled proof of use by an executor.'),
 'MOTION_PLAYBACK_EVIDENCE':('HOLD_PLAYABLE_ARTIFACTS_MISSING','Still sample images do not demonstrate 100 playable or reproducible animations.'),
 'DESIGN_TOKEN_VS_BEHAVIOR':('HOLD_DESIGN_BEHAVIOR_BASELINE_MISSING','No matching original/candidate runtime and state transitions are supplied.'),
 'DESIGN_SKILL_ROLES_SEPARATE':('HOLD_CONTROLLED_UI_COMPARISON_MISSING','Five tools are described, not compared with identical UI tasks and success criteria.'),
 'KOREAN_STYLE_MEANING_DIFF':('HOLD_PAIRED_TEXT_VALIDATION_MISSING','No before/after text with fact preservation and reader ratings has been tested.'),
 'MODEL_ROUTING_SUCCESS_ADJUSTED_COST':('HOLD_USAGE_QUALITY_BASELINE_MISSING','No task-matched billing, retries, elapsed time, and correctness comparison is verified.')
}
def decide(name,up,browser,node,quick):
 proof={'local_method_executed':False,'upstream_tool_executed':False}
 if name in ('BROWSER_OBSERVED_END_STATE','QUALITY_SKILL_TOOL_FAIL_SENSITIVITY'):
  if not browser:return 'HOLD_BROWSER_TEST_EVIDENCE_INVALID','Experiment receipt mismatch.',proof
  proof.update(local_method_executed=True,browser_run_sha256=h(B),quick_negative_control_included=quick,qa_sha256=h(QA))
  message='Real local Chrome hint behavior passed; intentional answer leakage detected. NOT an upstream MCP capability test.'
  return ('LOCAL_METHOD_REUSED_IN_QUICK_QA' if quick else 'LOCAL_METHOD_VERIFIED_CONSUMER_NOT_WIRED'),message,proof
 if name=='OFFICE_READ_WRITE_ROUNDTRIP':
  versions={z:up[z]['sha256'] for z in ('wordcraft','gridcraft','deckcraft')}
  proof['upstream_readme_sha256']=versions
  return 'LEARNING_CLAIM_LIMITED_BY_OFFICIAL_ALPHA','Official projects are alpha: maintain per-file fidelity tests, do not infer complete MS Office replacement (estimates ~60% Word, ~50% Excel, ~55% PowerPoint).',proof
 if name=='REA_SOURCE_BOUND_DIFFERENTIAL':
  source=Path(up['rea']['local_snapshot']).read_text(encoding='utf-8')
  if 'Node.js 22.x (>=22.19), 24.x (>=24.11), or 26+' not in source:
   return 'HOLD_OFFICIAL_PREREQ_TEXT_DRIFT','REA Node prerequisite source has changed.',proof
  proof.update(upstream_readme_sha256=up['rea']['sha256'],local_node_version=node,rea_cli_installed=shutil.which('rea') is not None)
  return 'PREREQUISITES_MATCHED_REPRODUCTION_UNTESTED','Original Node requirements match official upstream; local Node version qualifies, but REA is not installed or run.',proof
 if name in GAPS:return GAPS[name][0],GAPS[name][1],proof
 raise ValueError('UNKNOWN_LEARNING_ID:'+name)
def main():
 if Path(r'D:\Git PWA\TAKY-SOURCE-VAULT\data\site_watch\EVERY_AI_DERIVED_QUARANTINE_20261017.json').is_file():
  raise SystemExit('RETRACTED_DERIVED_LEARNING: source-first revalidation required; historical interpretation must not be regenerated.')
 hyp=get(H);browser=get(B);up=upstream_map(get(U))
 assert up is not None and source_check(hyp)
 assert len(hyp['existing_projection_compat']['learnings'])==12
 browse_ok=validate_browser(browser)
 node=subprocess.check_output(['node','--version'],text=True,timeout=5).strip()
 qa=QA.read_text(encoding='utf-8')
 negative_line=[x for x in qa.splitlines() if "item('hide-hint-negative-control-detection'" in x]
 quick=bool(len(negative_line)==1 and "'deep'" not in negative_line[0])
 out=[]
 for candidate in hyp['candidates']:
  name=candidate['learning_id'].split('20261017-',1)[1]
  state,reason,proof=decide(name,up,browse_ok,node,quick)
  out.append({'learning_id':candidate['learning_id'],'learning_hypothesis':candidate['learning_hypothesis'],
   'original_url':candidate['source_grounding']['source_url'],
   'original_raw_sha256':candidate['source_grounding']['source_sha256'],
   'original_unit_sha256':candidate['source_grounding']['unit_sha256'],
   'status':state,'decision_reason':reason,'tested_evidence':proof,
   'required_next_test':candidate['next_experiment'],
   'canonical_learning_promoted':False,'external_tool_installed':False})
 counts=dict(Counter(x['status'] for x in out))
 assert len(out)==12 and sum(counts.values())==12
 result={'schema':'TAKY_EVERY_AI_LOCAL_LEARNING_EVIDENCE_ADJUDICATION_V1',
  'created_at':datetime.now(timezone.utc).isoformat(),
  'original_source_count':118,'learning_items_evaluated':12,
  'browser_positive_and_negative_valid':browse_ok,
  'existing_quick_qa_consumes_negative_control':quick,
  'official_upstream_docs_hash_verified':len(up),
  'tested_local_method_claims':sum(x['tested_evidence']['local_method_executed'] for x in out),
  'external_tools_installed_or_executed':0,'canonical_learning_promoted':0,
  'paid_api_calls':0,'model_calls':0,
  'summary':counts,'decisions':out}
 DEST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# every._ai 러닝 독립 판단 결과',
  '',
  '원문 118편의 전체 기술 검증 완료 보고가 아니라 근거 있는 방법론 12개 판단입니다.',
  '마이닝 적합성 등급을 활용하지 않고 실제 로컬 Chrome 부정 테스트와 공식 README 원문으로 판단합니다.',
  '',
  '원문 118 / 학습 판정 12 / 실제 로컬 브라우저 방법 1건(연관 후보 2건) / 공식 원문 4건',
  '',
  '| 학습 후보 | 상태 | 판단 범위 |','|---|---|---|']
 for x in out:
  lines.append('| '+x['learning_id'].split('20261017-',1)[1]+' | '+x['status']+' | '+x['decision_reason']+' |')
 lines.extend(['','모든 판정은 LEARNING/evidence에서만 유효합니다. 원본 수정, CURRENT 권한 승격, 외부 프로젝트 성공 보고는 없습니다.',
  '','증거: '+str(B),'공식: '+str(U),'원문: '+str(H),'QA 코드: '+str(QA)])
 M.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'state':'LEARNING_DECISIONS_EVIDENCE_BOUND','items':len(out),
  'existing_method_browser_verified':result['tested_local_method_claims'],
  'official_docs':len(up),'quick_qa_wired':quick,
  'states':counts,'report':str(DEST),'human_report':str(M)},ensure_ascii=True))
if __name__=='__main__':main()
