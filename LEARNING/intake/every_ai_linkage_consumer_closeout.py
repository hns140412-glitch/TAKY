"""End-to-end readback of every._ai source -> mined evidence -> index -> learning
-> real local consumer QA. Durable receipt; no claim of full external app validation.
"""
from pathlib import Path
import hashlib,json,re
ROOT=Path(r'D:\Git PWA\TAKY')
V=ROOT.parent/'TAKY-SOURCE-VAULT'
L=ROOT/'LEARNING/evidence'
P=V/'reports/site_watch/reviews/every_ai_20261017'
def get(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if (ROOT.parent/'TAKY-SOURCE-VAULT/data/site_watch/EVERY_AI_DERIVED_QUARANTINE_20261017.json').exists():
 raise SystemExit('RETRACTED_DERIVED_LEARNING: stale linkage consumer receipt invalid as learning evidence')
src=get(P/'ALL_118_RAW_AUDIT.json')['records']
minep=get(V/'reports/site_watch/SITE_MINING_EVIDENCE_ACTIVE.json')
indexp=get(V/'reports/site_watch/SITE_WATCH_TEXT_INDEX_ACTIVE.json')
queuep=get(V/'data/site_watch/indexing_review/INDEX_OWNER_REVIEW_QUEUE_ACTIVE.json')
mine=get(Path(minep['path']))
index=get(Path(indexp['generation_path']))
queue=get(Path(queuep['generation_path']))
learning=get(L/'EVERY_AI_118_LEARNING_REVIEW_20261017.json')
hyp=get(L/'EVERY_AI_SOURCE_BOUND_METHOD_LEARNING_CANDIDATES_20261017.json')
judged=get(L/'EVERY_AI_METHOD_LEARNING_DECISIONS_20261017.json')
up=get(L/'EVERY_AI_OFFICIAL_SOURCE_CHECK_20261017/OFFICIAL_README_CHECK.json')
browser=get(L/'EVERY_AI_BROWSER_METHOD_EXPERIMENT_20261017/BROWSER_NEGATIVE_CONTROL_RUN.json')
qa_path=ROOT/'.local/family-qa/latest-quick.json';qa=get(qa_path)
prefix='https://every-ai-guides.vercel.app/posts/'
sources={x['url'] for x in src}
m={x['url'] for x in mine['sources'] if x['url'].startswith(prefix)}
i={x['url'] for x in index['entries'] if x['url'].startswith(prefix)}
q={x['source_url'] for x in queue['items'] if x['source_url'].startswith(prefix)}
l={x['url'] for x in learning['rows']}
assert len(sources)==118 and sources==m==i==q==l
assert all(sha(x['raw_path'])==x['sha256'] for x in src)
assert sha(minep['path'])==minep['sha256']
assert sha(indexp['generation_path'])==indexp['generation_sha256']
assert sha(queuep['generation_path'])==queuep['generation_sha256']
assert sum(len(x['units']) for x in mine['sources'] if x['url'].startswith(prefix))==2333
assert hyp['learning_candidate_count']==judged['learning_items_evaluated']==12
assert judged['official_upstream_docs_hash_verified']==4
assert judged['browser_positive_and_negative_valid'] is True
assert judged['existing_quick_qa_consumes_negative_control'] is True
assert judged['canonical_learning_promoted']==0
assert judged['external_tools_installed_or_executed']==0
assert qa['mode']=='quick' and qa['statuses']['failed']==0
assert qa['statuses']['passed']==18 and qa['statuses']['openGaps']==12
checks={x['id']:x['state'] for x in qa['results']}
assert checks['hide-hint-no-answer-browser']=='PASS'
assert checks['hide-hint-negative-control-detection']=='PASS'
assert browser['positive_pass'] and browser['negative_control_detected']
assert all(d['approved_canonical_knowledge'] is False for d in hyp.get('candidates',[]) if 'approved_canonical_knowledge' in d)
out={'schema':'TAKY_EVERY_AI_SOURCE_MINING_INDEX_LEARNING_LOCAL_QA_RECEIPT_V1',
 'scope':'LOCAL_SOURCE_AND_METHOD_EXPERIMENT_NOT_ALL_118_EXTERNAL_EXECUTION',
 'raw_118_hash_verified':True,'mine_118_articles':True,'mined_evidence_units':2333,
 'index_118_articles':True,'owner_review_118_articles':True,
 'learning_evaluation_118_articles':True,'learning_method_dispositions':12,
 'official_readme_hash_verified':4,
 'real_browser_positive_control':True,'real_browser_negative_control':True,
 'qa_quick_checks_passed':18,'qa_quick_failed':0,'qa_unresolved_critical_gaps':12,
 'qa_verdict':qa['verdict'],'qa_run_started_at':qa['startedAt'],
 'qa_full_report_sha256':sha(qa_path),
 'qa_relevant_cases':{k:checks[k] for k in ('hide-hint-no-answer-browser','hide-hint-negative-control-detection')},
 'learning_decision_sha256':sha(L/'EVERY_AI_METHOD_LEARNING_DECISIONS_20261017.json'),
 'canonical_learning_promotion':False,'external_tools_validated':False,
 'api_paid_calls':0,'push_merge_deploy':False}
dest=L/'EVERY_AI_LINKAGE_CONSUMER_RECEIPT_20261017.json'
dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# immutable versioned copy of quick QA evidence, preserving original latest file
orig=qa_path.read_bytes()
backup=L/('EVERY_AI_QUICK_QA_'+sha(qa_path)[:20]+'.json')
if backup.exists():assert backup.read_bytes()==orig
else:backup.write_bytes(orig)
print(json.dumps({'state':'PASS_VERIFIED_CONSUMER_CHAIN','source_count':118,
 'source_units':2333,'method_decisions':12,'quick_qa_passed':18,'quick_qa_critical_gaps':12,
 'browser_positive_and_negative_pass':True,'receipt':str(dest),'pinned_quick_qa':str(backup)},ensure_ascii=True))
