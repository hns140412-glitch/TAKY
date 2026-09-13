#!/usr/bin/env python3
import json, sys
from pathlib import Path

POLICY = json.loads((Path(__file__).parent / 'execution_policy.json').read_text(encoding='utf-8'))

def gate(record):
    missing = [k for k in POLICY['required_preflight_fields'] if k not in record]
    if missing:
        return {'decision':'BLOCK','failure_class':'PREFLIGHT_FIELD_OMISSION','missing':missing}
    if record['applicable_rules_loaded'] is not True:
        return {'decision':'BLOCK','failure_class':'APPLICABLE_RULES_NOT_LOADED'}
    if record['known_context_checked'] is not True:
        return {'decision':'BLOCK','failure_class':'KNOWN_CONTEXT_OMISSION_RISK'}
    if record['historical_failure_classes_checked'] is not True:
        return {'decision':'BLOCK','failure_class':'HISTORY_NOT_ACTIVATED'}
    if record['role'] == 'ORCHESTRATOR' and record['action_class'] == 'IMPLEMENTATION_WRITE' and record['execution_owner'] != 'TAKY':
        return {'decision':'BLOCK','failure_class':'ROLE_OWNER_VIOLATION'}
    if record['action_class'] == 'VALIDATION_ONLY':
        return {'decision':'PASS','product_progress_advance':False,'note':'VALIDATION_ONLY'}
    return {'decision':'PASS','product_progress_advance':record.get('integrated_user_visible_evidence', False)}

def main():
    if len(sys.argv) != 2:
        print('usage: preflight_gate.py <record.json>', file=sys.stderr); return 2
    record = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result = gate(record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['decision'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
