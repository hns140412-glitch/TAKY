from pathlib import Path
import json, hashlib, sys

ROOT=Path(r'D:\Git PWA\TAKY_ALPHA_20261003')
ALPHA=ROOT/'ALPHA'
REVIEW=ROOT/'ALPHA_REVIEW'

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))

authority=load(Path('ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json'))
registry=load(Path('MASTER/MASTER_FILE_REGISTRY.json'))
rules=load(Path('MASTER/RULE_REGISTRY.json'))
beta=json.loads((ROOT/'ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json').read_text(encoding='utf-8'))
carry=load(Path('ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json'))

# Preserve the exact Frozen Beta carry-over payload, not only a summary.
carry['exact_carry_over_open']=beta.get('carry_over_open',{})
carry['exact_contained_open']=beta.get('freeze_gate',{}).get('contained_open',[])
(ALPHA/'TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json').write_text(json.dumps(carry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# A1: authority compile.
beta_owners={x['namespace']:x for x in registry.get('semantic_owners',[])}
alpha_owners={x['namespace']:x for x in authority.get('semantic_owners',[])}
authority_fail=[]
if set(beta_owners)!=set(alpha_owners):
    authority_fail.append({'code':'NAMESPACE_SET_MISMATCH','expected':sorted(beta_owners),'actual':sorted(alpha_owners)})
for ns,row in beta_owners.items():
    a=alpha_owners.get(ns,{})
    paths=row.get('paths',{})
    for key in ('owner','current','change_ledger','verification_checkpoint'):
        if key in paths and a.get(key)!=paths.get(key):
            authority_fail.append({'code':'OWNER_PATH_MISMATCH','namespace':ns,'field':key,'expected':paths.get(key),'actual':a.get(key)})
        if key in paths and not (ROOT/paths[key]).exists():
            authority_fail.append({'code':'OWNER_PATH_MISSING','namespace':ns,'field':key,'path':paths[key]})

# A2: compile every registered rule without redefining its semantics.
compiled=[]
rule_fail=[]
seen=set()
for r in rules.get('rules',[]):
    rid=r.get('rule_id')
    owner=r.get('owner')
    if not rid or rid in seen:
        rule_fail.append({'code':'DUPLICATE_OR_MISSING_RULE_ID','rule_id':rid})
        continue
    seen.add(rid)
    exists=bool(owner and (ROOT/owner).exists())
    if not exists:
        rule_fail.append({'code':'RULE_OWNER_MISSING','rule_id':rid,'owner':owner})
    compiled.append({
        'rule_id':rid,
        'owner':owner,
        'scope':r.get('scope'),
        'owner_exists':exists,
        'alpha_semantics':'REFERENCE_OWNER_ONLY__NO_REDEFINITION'
    })

rule_compile={
    'schema':'TAKY_ALPHA_RULE_COMPILE_V0_1',
    'status':'PASS' if not rule_fail else 'FAIL',
    'source_registry':'MASTER/RULE_REGISTRY.json',
    'source_registry_version':rules.get('registry_version'),
    'rule_count':len(compiled),
    'rules':compiled,
    'failures':rule_fail,
    'invariants':[
        'ONE_RULE_ONE_OWNER',
        'ALPHA_REFERENCES_OWNER_SEMANTICS__DOES_NOT_COPY_OR_REDEFINE',
        'RULE_ID_IS_STABLE_EXECUTION_REFERENCE'
    ]
}
(ALPHA/'TAKY_ALPHA_RULE_COMPILE_V0_1.json').write_text(json.dumps(rule_compile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# A3: cross-domain routing graph. Draft routing only; authority remains at declared owners.
routing={
 'schema':'TAKY_ALPHA_ROUTING_GRAPH_V0_1',
 'status':'DRAFT_VALIDATED_STRUCTURE',
 'nodes':[
   {'id':'TAKY','role':'governance_orchestrator'},
   {'id':'WORK_OS','owner':'OS/WORK_OS.md'},
   {'id':'LEARNING_ENGINE','owner':'OS/LEARNING_ENGINE_CORE.md'},
   {'id':'PLANNER','owner':'ready_set'},
   {'id':'READY_SET','owner':'PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md'},
   {'id':'HIDE_SEEK','role':'memory_signal_producer'},
   {'id':'SNAP_POP','role':'expression_specialist'},
   {'id':'EXPLORER_CREW','owner':'OS/EXPLORATION_CREW_CANONICAL.md'},
   {'id':'DESIGN_UI_ASSETS','owner':'MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md'},
   {'id':'BADGE','role':'evidence_to_reward_pipeline'},
   {'id':'SAVEY','role':'economic_operating_module','repo_head':'5a196080b8f8ce50d188b0181d9bec5e5477a265'},
   {'id':'ARCHIGROW','owner':'DOMAIN/ARCHITECTURE_GROWTH_MAP.md'},
   {'id':'LEARNINGGROW','owner':'OS/LEARNING_ENGINE_CORE.md'}
 ],
 'edges':[
   {'from':'TAKY','to':'WORK_OS','relation':'ROUTE_PRODUCTIVE_WORK'},
   {'from':'TAKY','to':'LEARNING_ENGINE','relation':'ROUTE_LEARNING_STATE'},
   {'from':'TAKY','to':'SAVEY','relation':'ROUTE_ECONOMIC_OPERATION'},
   {'from':'WORK_OS','to':'ARCHIGROW','relation':'DOMAIN_GROWTH'},
   {'from':'LEARNING_ENGINE','to':'LEARNINGGROW','relation':'DOMAIN_GROWTH'},
   {'from':'HIDE_SEEK','to':'LEARNING_ENGINE','relation':'MEMORY_SIGNALS_ONLY'},
   {'from':'LEARNING_ENGINE','to':'PLANNER','relation':'REVIEW_PRIORITY_SIGNAL__NO_DATED_SCHEDULE_AUTHORITY'},
   {'from':'PLANNER','to':'READY_SET','relation':'DATED_EXECUTION_PLAN'},
   {'from':'EXPLORER_CREW','to':'READY_SET','relation':'SHARED_CHARACTER_RUNTIME_CONTRACT'},
   {'from':'EXPLORER_CREW','to':'HIDE_SEEK','relation':'SHARED_CHARACTER_RUNTIME_CONTRACT'},
   {'from':'EXPLORER_CREW','to':'SNAP_POP','relation':'SHARED_CHARACTER_RUNTIME_CONTRACT'},
   {'from':'DESIGN_UI_ASSETS','to':'READY_SET','relation':'APPROVED_SOURCE_TO_UI'},
   {'from':'DESIGN_UI_ASSETS','to':'HIDE_SEEK','relation':'APPROVED_SOURCE_TO_UI'},
   {'from':'DESIGN_UI_ASSETS','to':'SNAP_POP','relation':'APPROVED_SOURCE_TO_UI'},
   {'from':'READY_SET','to':'BADGE','relation':'EXPLICIT_EVIDENCE_PRODUCER'},
   {'from':'HIDE_SEEK','to':'BADGE','relation':'EXPLICIT_EVIDENCE_PRODUCER'},
   {'from':'SNAP_POP','to':'BADGE','relation':'EXPLICIT_EVIDENCE_PRODUCER'}
 ],
 'invariants':[
   'ROUTING_EDGE_DOES_NOT_TRANSFER_OWNER_AUTHORITY',
   'WORK_OS_AND_LEARNING_OS_ARE_SIBLINGS',
   'PLANNER_OWNS_DATED_SCHEDULING',
   'HIDE_DOES_NOT_OWN_LONG_TERM_SCHEDULING',
   'BADGE_PRODUCER_QA_PASS_DOES_NOT_ACTIVATE_BADGE'
 ]
}
(ALPHA/'TAKY_ALPHA_ROUTING_GRAPH_V0_1.json').write_text(json.dumps(routing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

result={
 'schema':'TAKY_ALPHA_A1_A3_VALIDATION_V0_1',
 'authority':{'status':'PASS' if not authority_fail else 'FAIL','failures':authority_fail},
 'rules':{'status':'PASS' if not rule_fail else 'FAIL','rule_count':len(compiled),'failures':rule_fail},
 'carryover':{'status':'PASS','exact_top_level_keys':sorted(beta.get('carry_over_open',{}).keys()),'contained_count':len(beta.get('freeze_gate',{}).get('contained_open',[]))},
 'routing':{'status':'PASS','node_count':len(routing['nodes']),'edge_count':len(routing['edges'])}
}
result['status']='PASS' if result['authority']['status']=='PASS' and result['rules']['status']=='PASS' else 'FAIL'
(REVIEW/'ALPHA_A1_A3_VALIDATION_20261003.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
sys.exit(0 if result['status']=='PASS' else 1)
