from pathlib import Path
import json, hashlib, sys, re

ROOT=Path(r'D:\Git PWA\TAKY_ALPHA_20261003')
REVIEW=ROOT/'ALPHA_REVIEW'

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))

fail=[]
notes=[]

input_lock=load(Path('ALPHA_REVIEW/ALPHA_INPUT_LOCK_20261003.json'))
beta=load(Path('ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json'))
approval=load(Path('ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_APPROVAL_20261003.json'))
authority=load(Path('ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json'))
carry=load(Path('ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json'))
validation=load(Path('ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json'))
routing=load(Path('ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json'))
compiled=load(Path('ALPHA/TAKY_ALPHA_RULE_COMPILE_V0_1.json'))
master_registry=load(Path('MASTER/MASTER_FILE_REGISTRY.json'))
rule_registry=load(Path('MASTER/RULE_REGISTRY.json'))
layer_map=load(Path('MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json'))
master_text=(ROOT/'ALPHA/TAKY_ALPHA_MASTER_V0_1.md').read_text(encoding='utf-8')

# V0 approval + frozen input binding
snap=input_lock.get('frozen_beta_snapshot_identity_sha256')
if snap!=approval.get('frozen_beta_snapshot_identity_sha256'):
    fail.append('V0_APPROVAL_SNAPSHOT_MISMATCH')
if approval.get('status')!='APPROVED':
    fail.append('V0_FREEZE_NOT_APPROVED')
apath=ROOT/input_lock.get('freeze_approval_evidence','')
if not apath.exists():
    fail.append('V0_APPROVAL_EVIDENCE_MISSING')
else:
    ah=hashlib.sha256(apath.read_bytes()).hexdigest()
    if ah!=input_lock.get('freeze_approval_sha256'): fail.append('V0_APPROVAL_HASH_MISMATCH')
required_scope={'MARK_EXACT_BETA_SNAPSHOT_FROZEN','START_ALPHA_FROM_FROZEN_BETA_ONLY'}
if not required_scope.issubset(set(approval.get('approval_scope',[]))): fail.append('V0_APPROVAL_SCOPE_INCOMPLETE')
for prohibited in ('PUSH','MERGE','DEPLOY','PAID_API','CANONICAL_ALPHA_PROMOTION'):
    if prohibited not in set(approval.get('not_authorized',[])): fail.append('V0_APPROVAL_BOUNDARY_MISSING:'+prohibited)

# V1 semantic owner exactness + duplicate rejection before indexing
src_rows=master_registry.get('semantic_owners',[])
alpha_rows=authority.get('semantic_owners',[])
src_ns=[r.get('namespace') for r in src_rows]
alpha_ns=[r.get('namespace') for r in alpha_rows]
if len(src_ns)!=len(set(src_ns)): fail.append('V1_SOURCE_DUPLICATE_NAMESPACE')
if len(alpha_ns)!=len(set(alpha_ns)): fail.append('V1_ALPHA_DUPLICATE_NAMESPACE')
if set(src_ns)!=set(alpha_ns): fail.append('V1_NAMESPACE_SET_MISMATCH')
src_by={r['namespace']:r for r in src_rows if r.get('namespace')}
alpha_by={r['namespace']:r for r in alpha_rows if r.get('namespace')}
for ns,row in src_by.items():
    a=alpha_by.get(ns,{})
    for k,v in row.get('paths',{}).items():
        if k in ('owner','current','change_ledger','verification_checkpoint') and a.get(k)!=v:
            fail.append(f'V1_PATH_MISMATCH:{ns}:{k}')

# V2 rule owner-reference compile exactness; no executable-gate overclaim
src_rules=rule_registry.get('rules',[])
cmp_rules=compiled.get('rules',[])
src_ids=[r.get('rule_id') for r in src_rules]
cmp_ids=[r.get('rule_id') for r in cmp_rules]
if len(src_ids)!=len(set(src_ids)): fail.append('V2_SOURCE_DUPLICATE_RULE_ID')
if len(cmp_ids)!=len(set(cmp_ids)): fail.append('V2_ALPHA_DUPLICATE_RULE_ID')
if src_ids!=cmp_ids: fail.append('V2_RULE_ID_ORDER_OR_SET_MISMATCH')
for s,c in zip(src_rules,cmp_rules):
    if any(c.get(k)!=s.get(k) for k in ('rule_id','owner','scope')): fail.append('V2_RULE_ENTRY_MISMATCH:'+str(s.get('rule_id')))
    owner=s.get('owner')
    if owner and not (ROOT/owner).exists(): fail.append('V2_RULE_OWNER_MISSING:'+str(s.get('rule_id')))
if 'Rule Activation / Executable Gate Map' not in json.dumps(validation,ensure_ascii=False):
    fail.append('V2_ACTIVATION_STAGE_NOT_DECLARED')

# V3/V4/V5 boundaries
if 'CURRENT_IS_RESUME_POINTER_NOT_OWNER' not in authority.get('authority_rules',[]): fail.append('V3_CURRENT_BOUNDARY_MISSING')
if 'LIVE_HEAD_CLAIMS_REQUIRE_REQUERY' not in authority.get('authority_rules',[]): fail.append('V4_LIVE_REFRESH_RULE_MISSING')
if authority.get('input',{}).get('source_heads')!=beta.get('source_heads'): fail.append('V5_SOURCE_HEADS_NOT_FROZEN_MATCH')

# V6 exact manifest OPEN + repository HOLD coverage
if carry.get('exact_carry_over_open')!=beta.get('carry_over_open',{}): fail.append('V6_MANIFEST_OPEN_MISMATCH')
if carry.get('exact_contained_open')!=beta.get('freeze_gate',{}).get('contained_open',[]): fail.append('V6_CONTAINED_OPEN_MISMATCH')
expected_hold=[]
shared=layer_map.get('layers',{}).get('SHARED_TECHNICAL_CAPABILITY',{})
if 'HOLD' in str(shared.get('state','')): expected_hold.append('SHARED_TECHNICAL_CAPABILITY')
for i,row in enumerate(layer_map.get('capability_classification',[])):
    if 'HOLD' in str(row.get('state','')): expected_hold.append('CAP:'+str(i))
for i,row in enumerate(layer_map.get('review_findings',[])):
    if row.get('state')=='HOLD': expected_hold.append('GAP:'+str(row.get('gap_id')))
if len(carry.get('repository_hold_constraints',[]))<len(expected_hold): fail.append('V6_REPOSITORY_HOLD_COVERAGE_INCOMPLETE')

# V7 routing integrity / ownership boundaries
nodes=routing.get('nodes',[])
node_ids=[n.get('id') for n in nodes]
if len(node_ids)!=len(set(node_ids)): fail.append('V7_DUPLICATE_ROUTING_NODE')
required={'TAKY','SHARED_TECHNICAL_CAPABILITY','PLATFORM_ADAPTER','WORK_OS','LEARNING_OS','LEARNING_APP_FAMILY','LEARNING_ENGINE','PLANNER','READY_SET','HIDE_SEEK','SNAP_POP'}
if not required.issubset(set(node_ids)): fail.append('V7_REQUIRED_LAYER_MISSING:'+','.join(sorted(required-set(node_ids))))
node_by={n['id']:n for n in nodes if n.get('id')}
planner=node_by.get('PLANNER',{})
if planner.get('owner')=='ready_set' or planner.get('semantic_authority')!='LEARNING_OS': fail.append('V7_PLANNER_AUTHORITY_INVALID')
if not node_by.get('HIDE_SEEK',{}).get('owner_ref'): fail.append('V7_HIDE_OWNER_REF_MISSING')
if not node_by.get('SNAP_POP',{}).get('owner_ref'): fail.append('V7_SNAP_OWNER_REF_MISSING')
for e in routing.get('edges',[]):
    if e.get('from') not in node_by or e.get('to') not in node_by: fail.append('V7_EDGE_UNKNOWN_NODE')

# V8 claim dimensions are non-linear and build IDs distinct from validation IDs
if 'claim_ladder' in validation: fail.append('V8_LINEAR_CLAIM_LADDER_FIELD_PRESENT')
if not validation.get('claim_dimensions'): fail.append('V8_CLAIM_DIMENSIONS_MISSING')
vg=[g.get('id','') for g in validation.get('validation_gates',[])]
if any(x.startswith('A') for x in vg): fail.append('V8_STAGE_VALIDATION_ID_COLLISION')
if 'DOCUMENTED → CODED' in master_text: fail.append('V8_MASTER_LINEAR_CLAIM_ARROW_PRESENT')

# V9 release / hosted boundaries
rb=validation.get('release_boundary',{})
for k in ('push','merge','deploy','paid_api'):
    if rb.get(k)!='HOLD': fail.append('V9_RELEASE_BOUNDARY_NOT_HOLD:'+k)
if not any(x.get('id')=='HOSTED_RUNTIME_INTERCEPTION' for x in carry.get('classes',[])): fail.append('V9_HOSTED_OPEN_MISSING')

result={
  'schema':'TAKY_ALPHA_READONLY_VALIDATION_V0_2',
  'date':'2026-10-03',
  'status':'PASS' if not fail else 'FAIL',
  'failure_count':len(fail),
  'failures':fail,
  'checks':{
    'freeze_approval_bound':not any(x.startswith('V0_') for x in fail),
    'authority_unique_exact':not any(x.startswith('V1_') for x in fail),
    'rule_owner_compile_exact':not any(x.startswith('V2_') for x in fail),
    'manifest_and_repository_open_preserved':not any(x.startswith('V6_') for x in fail),
    'routing_integrity':not any(x.startswith('V7_') for x in fail),
    'claim_dimensions_non_linear':not any(x.startswith('V8_') for x in fail),
    'release_boundaries_hold':not any(x.startswith('V9_') for x in fail)
  },
  'note':'Validator reads source inputs and writes only this validation result; it does not mutate Alpha source structures.'
}
(REVIEW/'ALPHA_READONLY_VALIDATION_20261003.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
sys.exit(0 if not fail else 1)
