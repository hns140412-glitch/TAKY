"""Produce explicitly source-bound LEARNING hypotheses, not mining/index labels.
No canonical promotion or unsupported source-success claims.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,re,sys

ROOT=Path(r'D:\Git PWA\TAKY')
VAULT=ROOT.parent/'TAKY-SOURCE-VAULT'
sys.path.insert(0,str(ROOT/'ENFORCEMENT'))
from ai_reference_projection import build_learning
MINE=VAULT/'reports/site_watch/SITE_MINING_EVIDENCE_ACTIVE.json'
SOURCE=VAULT/'reports/site_watch/reviews/every_ai_20261017/ALL_118_RAW_AUDIT.json'
CURRENT=ROOT/'CURRENT/DATA/AI_LEARNING_PROJECTION.json'
OUT=ROOT/'LEARNING/evidence/EVERY_AI_SOURCE_BOUND_METHOD_LEARNING_CANDIDATES_20261017.json'
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

# These interpretations belong exclusively to LEARNING and require further experiments.
# They are neither facts published by the author nor imported from prior biased grades.
LESSONS=[
('DATA_METRIC_RECALC','claude-insta-analysis','상관',
 'Data-based content recommendations should preserve original rows, recomputable measures, and separation of correlation from causal explanation.',
 'RUN_SOURCE_DATA_RECALCULATION','No input dataset or independent numeric rerun in the source collection'),
('ROLE_PROMPT_NOT_AGENT','claude-secretary-30','커넥터',
 'A list of role prompts connected to apps should not be equated with independently running scheduled agents; verify actual actions and state.',
 'COMPLETE_ACTUAL_ACTION_AND_SCHEDULE_TEST','No independent 24-hour agent log in captured source'),
('MANUAL_TO_ACTUAL_ENFORCEMENT','claude-ai-delegation-loop-4','SKILL.md',
 'A persistent task manual and verification checklist create reusable procedure but do not demonstrate that an executor consumed rules in a real task.',
 'TRACE_READ_EXECUTE_FAIL_RETRY','No externally captured rule-read or failure injection trace'),
('OFFICE_READ_WRITE_ROUNDTRIP','ms-office-free-wordcraft','GridCraft',
 'Compatibility of document, spreadsheet and slide tools must be tested separately with editable files and round-trip changes.',
 'THREE_FORMAT_ROUNDTRIP_TEST','Published availability does not prove formula, font or shape fidelity'),
('REA_SOURCE_BOUND_DIFFERENTIAL','rea-reverse-engineer-anything','REA',
 'Reverse engineering that infers a feature should preserve observed inputs, outputs and traces, followed by differential tests against a separate implementation.',
 'ORIGINAL_VS_REIMPLEMENTATION_TEST','Installation guide is not a proven functional replica'),
('MOTION_PLAYBACK_EVIDENCE','claude-motion-100','HyperFrames',
 'Lists of motion prompts and still examples should be evaluated separately from playable final clips and render reproducibility.',
 'RENDER_SAMPLE_AND_INSPECT_PLAYBACK','Still images do not prove all animations ran'),
('BROWSER_OBSERVED_END_STATE','chrome-devtools-mcp','DevTools',
 'Browser tools can observe elements and console errors, but verification of business behavior requires checking state transitions and persisted results.',
 'INJECT_LOGIC_DEFECT_AND_VERIFY_DETECTION','Tool setup article is not an observed detection benchmark'),
('DESIGN_TOKEN_VS_BEHAVIOR','designlang','designlang',
 'Extracted visual tokens are not a substitute for observed interactions, responsive transitions and underlying data behavior.',
 'COMPARE_VISUAL_AND_FUNCTIONAL_OUTPUTS','Static token extraction alone cannot prove experience equivalence'),
('DESIGN_SKILL_ROLES_SEPARATE','claude-design-skills-5','frontend-design',
 'Aesthetic drafting, component knowledge, motion refinement and accessibility checks target different kinds of quality; compare each against the same output.',
 'FAIR_BASELINE_UI_EVALUATION','Installation of multiple skills is not evidence of improved task success'),
('KOREAN_STYLE_MEANING_DIFF','ai-writing-humanizer-skills','Humanizer',
 'Korean style edits should be evaluated for readability and exact preservation of facts, numbers, entities and citations.',
 'BEFORE_AFTER_FACT_DIFF_AND_READER_TEST','Natural style alone is not accuracy evidence'),
('MODEL_ROUTING_SUCCESS_ADJUSTED_COST','model-routing','모델',
 'Claims of model-routing efficiency require measuring correct results, retries, time and total consumption on comparable tasks.',
 'RUN_BASELINE_WITH_RETRY_COST','No independent task-level cost experiment in this capture'),
('QUALITY_SKILL_TOOL_FAIL_SENSITIVITY','claude-verify-skills-5','Playwright',
 'Different verification tools target different observable failure classes; tool presence and PASS reports should be tested against injected defects.',
 'DEFECT_SEEDED_INDEPENDENT_BENCHMARK','Listing testing tools is not measured bug-finding accuracy')
]
def main():
 if Path(r'D:\Git PWA\TAKY-SOURCE-VAULT\data\site_watch\EVERY_AI_DERIVED_QUARANTINE_20261017.json').is_file():
  raise SystemExit('RETRACTED_DERIVED_LEARNING: source-first revalidation required; historical interpretation must not be regenerated.')
 minepointer=j(MINE)
 mp=Path(minepointer['path'])
 assert sha(mp)==minepointer['sha256']
 mine=j(mp)
 assert mine['semantic_review_complete'] is False
 src=j(SOURCE)['records']
 assert len(src)==118
 byslug={r['url'].split('/posts/')[-1]:r for r in src}
 byurl={r['url']:r for r in mine['sources']}
 base=j(CURRENT)
 assert base.get('authoritative') is False
 current_ids={r['learning_id'] for r in base['learnings']}
 candidate=[]
 project_rows=[]
 issues=[]
 for key,slug,needle,insight,next_test,limit in LESSONS:
  row=byslug.get(slug)
  if not row:issues.append('ARTICLE_MISSING:'+slug);continue
  m=byurl.get(row['url'])
  if not m or sha(Path(row['raw_path']))!=row['sha256'] or m['raw_sha256']!=row['sha256']:
   issues.append('RAW_OR_MINING_IDENTITY:'+slug);continue
  matches=[unit for unit in m['units'] if needle.casefold() in unit['excerpt'].casefold()]
  if not matches:issues.append('QUOTE_NOT_FOUND:'+slug);continue
  unit=matches[0]
  at=unit['excerpt'].casefold().find(needle.casefold())
  start=max(0,at-65);end=min(len(unit['excerpt']),at+len(needle)+130)
  quote=unit['excerpt'][start:end]
  assert needle.casefold() in quote.casefold()
  lid='AI-LRN-EVERY-20261017-'+key
  assert lid not in current_ids
  evidence={
    'source_url':row['url'],'source_sha256':row['sha256'],
    'source_id':m['source_id'],'unit_id':unit['unit_id'],
    'unit_sha256':unit['content_sha256'],
    'anchor':unit['source_anchor'],'exact_quote':quote,
    'source_technical_success_not_verified':True}
  candidate.append({'learning_id':lid,
   'learning_hypothesis':insight,
   'source_grounding':evidence,
   'comparative_disposition':'EVALUATE_IN_LEARNING_NOT_AUTO_ADOPT',
   'next_experiment':next_test,
   'evidence_limitation':limit,
   'canonical_promotion':False})
  project_rows.append({'source_id':m['source_id'],
    'ai_categories':[],
    'learning_eligible':True,
    'learning_candidates':[{'learning_id':lid,'insight':insight}]})
 if issues:raise RuntimeError('LEARNING_GROUNDING_HOLD:'+','.join(issues))
 projection=build_learning(project_rows)
 ids={x['learning_id'] for x in projection['learnings']}
 assert ids=={x['learning_id'] for x in candidate}
 assert all(x['canonical_promotion'] is False and x['state']=='EVIDENCE_CANDIDATE' for x in projection['learnings'])
 assert projection['authoritative'] is False
 doc={'schema':'TAKY_SOURCE_BOUND_LEARNING_METHOD_CANDIDATES_V1',
  'source_registry':'SITE_MINING_EVIDENCE_ACTIVE',
  'learning_owner':'SYSTEM_GROW_REFERENCE_LEARNING_CANDIDATE',
  'source_review_stage':'SOURCE_ANCHORED_UNREVIEWED',
  'independent_method_reproduction_verified':False,
  'machine_generated_utility_decision_authoritative':False,
  'source_count_considered':len(src),'learning_candidate_count':len(candidate),
  'canonical_learning_unchanged':True,
  'model_calls':0,'paid_api_calls':0,
  'candidates':candidate,'existing_projection_compat':projection}
 OUT.parent.mkdir(exist_ok=True,parents=True)
 OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'status':'LEARNING_HYPOTHESES_GROUNDED','source_universe':len(src),
   'new_method_candidacies':len(candidate),'all_raw_and_excerpt_source_bound':True,
   'existing_learning_projection_reused':True,
   'approved_or_deployed':0,'output':str(OUT)},ensure_ascii=True))
if __name__=='__main__':main()
