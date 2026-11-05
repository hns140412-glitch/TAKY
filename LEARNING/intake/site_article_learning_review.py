"""Learning-stage evaluation for every._ai source evidence.
Source mining and indexing contain no judgments on practical adoption.
This LEARNING module compares original source observations with existing learning,
chooses evidence-driven follow-up methods, never grants final adoption or CURRENT.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,hashlib,json,re,os,sys
from bs4 import BeautifulSoup
ROOT=Path(r'D:\Git PWA\TAKY')
VAULT=ROOT.parent/'TAKY-SOURCE-VAULT'
sys.path.insert(0,str(VAULT))
from MINE_SITE_EVIDENCE_UNITS_LOCAL import units_html
ORIG=VAULT/'reports/site_watch/reviews/every_ai_20261017/ALL_118_RAW_AUDIT.json'
MINE_PTR=VAULT/'reports/site_watch/SITE_MINING_EVIDENCE_ACTIVE.json'
CURRENT=ROOT/'CURRENT/DATA/AI_LEARNING_PROJECTION.json'
OUT=ROOT/'LEARNING/evidence/EVERY_AI_118_LEARNING_REVIEW_20261017.json'
HOST='https://every-ai-guides.vercel.app/posts/'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t):return re.sub(r'\s+',' ',str(t or '')).strip()
STOP={'ai','claude','code','chatgpt','model','models','tool','tools','agent','agents','plugin','plugins','new','source','data','and','the','with','from','for','not','only','can','use','users','test','testing','web','app','apps','task','tasks','learning','workflow','review','content','design','prompt','prompts'}
def tokens(text):
 return {x.lower() for x in re.findall(r'[A-Za-z][A-Za-z0-9_\-]{2,}',text) if x.lower() not in STOP}
def lexical_neighbors(article,learned):
 t=tokens(article)
 results=[]
 for x in learned:
  s=tokens(str(x.get('insight') or ''))
  common=sorted(t&s)
  if not common:continue
  score=len(common)/max(1,min(len(s),len(t)))
  results.append((score,len(common),str(x.get('learning_id') or ''),common[:8]))
 return [{'learning_id':v,'shared_terms':common,'lexical_fraction':round(score,3),'semantic_equivalence_verified':False} for score,k,v,common in sorted(results,reverse=True)[:3] if k>=1]
def learning_stage_decision(rec,siteunits):
 # Decisions are *learning evaluation work types*, not source quality or adoption scores.
 intro=rec.get('body_intro') or []
 if isinstance(intro,list):intro=' '.join(str(x) for x in intro)
 snippets=' '.join([str(rec['title']),str(intro),str(rec.get('body_full') or '')[:5000]])
 is_command=bool(re.search(r'\b(?:npx|npm install|pip install|git clone|winget install|/plugin\s+install|claude mcp)\b',snippets,re.I))
 actual_reports=[str(c) for c in (rec.get('outcome_claims') or [])
                 if re.match(r'^\s*(?:실제 결과|실험 결과|측정 결과|검증 결과|테스트 결과)\s*[:：]',str(c))]
 metric_re=r'(?:\d+(?:\.\d+)?\s*%|상관(?:계수|관계)|(?:\+|−|-)\s*0\.\d+|절감률|오류율|정확도|성공률)'
 is_number=any(re.search(metric_re,s,re.I) for s in actual_reports)
 media=bool(BeautifulSoup(Path(rec['raw_path']).read_bytes(),'html.parser').select('article.post img'))
 is_report=bool(actual_reports)
 if is_command:
  code='RUNNABLE_TOOL_CLAIM_REPRODUCTION'
  check='실제 설치 대상·버전·라이선스·실행 명령·출력·오류를 공식 소스와 대조하고 격리된 환경에서 재현'
 elif is_report and is_number:
  code='QUANTITATIVE_OR_OUTCOME_CLAIM_RECALCULATION'
  check='원본 데이터·계산식·측정 기간·기초 수치를 확보해 결과를 독립 재계산'
 elif media:
  code='MEDIA_OUTPUT_REVIEW'
  check='본문 이미지가 예제·광고·실제 제작 결과 중 무엇인지 확인하고 재생·편집 가능 여부를 비교'
 elif rec.get('prompts'):
  code='PROMPT_METHOD_BASELINE_COMPARISON'
  check='동일 입력·동일 평가 항목으로 일반 요청문과 글의 단계형 지시문을 실행 비교'
 else:
  code='REFERENCE_OR_EXPLANATION_REVIEW'
  check='원문에서 확인 가능한 사실과 의견을 분리한 뒤 공식 자료와 교차 확인'
 return code,check,{'executable_command_lexical_hit':is_command,'numbers_present':is_number,'author_claim_present':is_report,'html_img_tag_present':media}
def main():
 if Path(r'D:\Git PWA\TAKY-SOURCE-VAULT\data\site_watch\EVERY_AI_DERIVED_QUARANTINE_20261017.json').is_file():
  raise SystemExit('RETRACTED_DERIVED_LEARNING: source-first revalidation required; historical interpretation must not be regenerated.')
 args=argparse.ArgumentParser()
 args.add_argument('--query',default='')
 arg=args.parse_args()
 orig=load(ORIG);records=orig['records']
 assert len(records)==118
 pointer=load(MINE_PTR)
 path=Path(pointer['path']).resolve(strict=True)
 assert path.is_relative_to((VAULT/'reports/site_watch/mining_generations').resolve())
 assert digest(path)==pointer['sha256']
 mined=load(path)
 md={x['url']:x for x in mined['sources'] if x['url'].startswith(HOST)}
 assert len(md)==118
 reference=load(CURRENT)
 assert reference.get('authoritative') is False
 learned=reference.get('learnings') or []
 assert len(learned)>=50
 rows=[]
 for rec in records:
  assert rec['url'] in md and digest(Path(rec['raw_path']))==rec['sha256']
  source=md[rec['url']]
  assert source['raw_sha256']==rec['sha256'] and source['units']
  # Verify source anchor hashes against the miner's text excerpts as a proof of immutable binding.
  units=source['units']
  actual_units,quality=units_html(Path(rec['raw_path']))
  assert len(actual_units)==len(units)
  assert all(a['unit_id']==b['unit_id'] and a['content_sha256']==b['content_sha256'] for a,b in zip(actual_units,units))
  kind,check,observed=learning_stage_decision(rec,units)
  intro=rec.get('body_intro') or []
  if isinstance(intro,list):intro=' '.join(str(x) for x in intro)
  nearby=lexical_neighbors(rec['title']+' '+str(intro)[:350],learned)
  row={
   'source_id':source['source_id'],'url':rec['url'],'title':rec['title'],
   'published':rec['published'],'raw_sha256':rec['sha256'],
   'mining_generation_path':str(path),'evidence_unit_count':len(units),
   'evidence_refs':[{'unit_id':u['unit_id'],'content_sha256':u['content_sha256'],
    'source_anchor':u['source_anchor'],'literal_excerpt':u['excerpt'][:250],
    'review_state':'UNREVIEWED_SOURCE_EXTRACT'} for u in units[:3]],
   'observed_evidence':observed,
   'source_claims_do_not_equal_verified_outcomes':True,
   'existing_learning_lexical_neighbors':nearby,
   'learning_action':kind,'learning_evaluation_requirement':check,
   'learning_decision_state':'INITIAL_COMPARATIVE_TRIAGE_NOT_INDEPENDENT_VALIDATION',
   'semantic_utility_decision':'NOT_DECIDED_BEFORE_VALIDATED_LEARNING_REVIEW',
   'adoption_approved':False,'forming_approved':False,'source_integrity_verified':True}
  rows.append(row)
 report={
  'schema':'TAKY_SITE_SOURCE_LEARNING_COMPARISON_CANDIDATE_V1',
  'status':'LEARNING_STAGE_EVIDENCE_EVALUATION_STARTED',
  'evaluation_boundary':'ONLY_LEARNING_DECIDES_UTILITY_AFTER_SOURCE_AND_OUTCOME_VERIFICATION',
  'source':str(ORIG),'mining_ref':str(path),'original_learning_projection_read_only':str(CURRENT),
  'source_count':len(rows),'evidence_unit_count':sum(r['evidence_unit_count'] for r in rows),
  'evaluation_workload':dict(Counter(x['learning_action'] for x in rows)),
  'learning_quality_authoritatively_validated_count':0,
  'adoption_approved_count':0,'canonical_learning_modified':False,
  'paid_api_calls':0,'model_calls':0,'rows':rows}
 payload=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf8')
 OUT.parent.mkdir(parents=True,exist_ok=True)
 if OUT.exists() and OUT.read_bytes()==payload:pass
 else:
  tmp=OUT.with_name(OUT.name+'.'+str(os.getpid())+'.tmp')
  tmp.write_bytes(payload);os.replace(tmp,OUT)
 assert len(load(OUT)['rows'])==118
 if arg.query:
  matches=[{'source_id':r['source_id'],'title':r['title'],'url':r['url'],
    'learning_action':r['learning_action'],'evidence_refs':r['evidence_refs'][:1]}
    for r in rows if (arg.query.casefold() in (r['title']+' '+r['url']).casefold() if re.search(r'[가-힣]',arg.query) else all(t in set(re.findall(r'[a-z0-9]+',(r['title']+' '+r['url']).casefold())) for t in re.findall(r'[a-z0-9]+',arg.query.casefold())))]
  print(json.dumps({'query':arg.query,'matches':matches[:10]},ensure_ascii=True))
 else:
  print(json.dumps({'status':report['status'],'sources':len(rows),
   'unit_count':report['evidence_unit_count'],'learning_action_workload':report['evaluation_workload'],
   'learning_verified_count':0,'adoption_approved_count':0,'legacy_TAKY_ratings_used':False,
   'out':str(OUT)},ensure_ascii=True))
if __name__=='__main__':main()
