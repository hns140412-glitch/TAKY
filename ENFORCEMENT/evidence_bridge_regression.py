#!/usr/bin/env python3
from copy import deepcopy
from pathlib import Path
import json

from preflight_bridge import run

ROOT = Path(__file__).resolve().parents[1]
base = json.loads((ROOT / 'ENFORCEMENT/fixtures/preflight_evidence_pass.json').read_text(encoding='utf-8'))

r = run(base, ROOT)
assert r['pass'] is True, r
assert r['runtime_claim_ceiling'] == 'REPOSITORY_EXECUTABLE_CI_ENFORCED', r
assert r['live_runtime_auto_invocation_verified'] is False, r

bad_hash = deepcopy(base)
bad_hash['applicable_rule_refs'][0]['sha256'] = '0' * 64
r = run(bad_hash, ROOT)
assert r['pass'] is False and any('REPO_FILE_HASH_MISMATCH' in x for x in r['detected']), r

missing_history = deepcopy(base)
missing_history['history_query_refs'] = []
r = run(missing_history, ROOT)
assert r['pass'] is False, r

role_drift = deepcopy(base)
role_drift['action_class'] = 'IMPLEMENTATION_WRITE'
r = run(role_drift, ROOT)
assert r['pass'] is False and 'ROLE_OWNER_VIOLATION' in r['detected'], r

progress_drift = deepcopy(base)
progress_drift['action_class'] = 'VALIDATION_ONLY'
progress_drift['claims_product_progress_advance'] = True
r = run(progress_drift, ROOT)
assert r['pass'] is False and 'VALIDATION_AS_PRODUCT_PROGRESS' in r['detected'], r

runtime_overclaim = deepcopy(base)
runtime_overclaim['claims_runtime_enforced'] = True
r = run(runtime_overclaim, ROOT)
assert r['pass'] is False and 'STATE_CLAIM_MISMATCH' in r['detected'], r

print('PASS evidence-backed preflight bridge regression')
