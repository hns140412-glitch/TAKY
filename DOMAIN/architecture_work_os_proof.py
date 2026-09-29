#!/usr/bin/env python3
"""Independent local proof preflight, not a Work OS replacement or approval.

The caller supplies the real Work OS-owned outcome manifest and evidence files.
No manifest claims are accepted if the bytes and revision do not match.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

VERSION = 'ARCHIGROW_WORK_OS_PROOF_PREFLIGHT_V1'


def preflight(manifest: dict, root: Path) -> dict:
    problems = []
    project = manifest.get('project') or {}
    for f in ('project_id', 'revision_id', 'trial_receipt_id', 'outcome_receipt_id'):
        if not isinstance(project.get(f), str) or not project[f].strip():
            problems.append('MISSING_PROJECT_IDENTITY:' + f)
    if manifest.get('source_owner') != 'WORK_OS':
        problems.append('WORK_OS_OWNER_REQUIRED')
    if manifest.get('state') not in ('PASS', 'PARTIAL', 'FAIL'):
        problems.append('OUTCOME_STATE_INVALID')
    evidence = manifest.get('evidence') or []
    if not isinstance(evidence, list):
        problems.append('EVIDENCE_LIST_REQUIRED'); evidence = []
    seen_roles = set()
    checked = []
    allowed_root = root.resolve()
    for e in evidence:
        role = e.get('role') if isinstance(e, dict) else None
        filename = e.get('relative_path') if isinstance(e, dict) else None
        expected = e.get('sha256') if isinstance(e, dict) else None
        if role in seen_roles:
            problems.append('DUPLICATE_EVIDENCE_ROLE:' + str(role))
        seen_roles.add(role)
        if not all(isinstance(s, str) and s.strip() for s in (role, filename, expected)):
            problems.append('EVIDENCE_FIELDS_REQUIRED'); continue
        file = (allowed_root / filename).resolve()
        if not file.is_relative_to(allowed_root):
            problems.append('PATH_ESCAPE:' + role); continue
        if not file.is_file():
            problems.append('FILE_MISSING:' + role); continue
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        if actual != expected.lower():
            problems.append('HASH_MISMATCH:' + role)
        else:
            checked.append({'role': role, 'relative_path': filename, 'sha256': actual})
    if manifest.get('state') == 'PASS':
        required = {'SOURCE_MANIFEST', 'WORK_OS_ARTIFACT', 'INDEPENDENT_QA', 'REGRESSION'}
        for missing in sorted(required - set(x['role'] for x in checked)):
            problems.append('PASS_PROOF_MISSING:' + missing)
        result = manifest.get('comparison') or {}
        if not all(k in result and isinstance(result[k], (int, float)) and not isinstance(result[k], bool) for k in ('baseline', 'observed')):
            problems.append('NUMERIC_BASELINE_OUTCOME_REQUIRED')
        if any(isinstance(result.get(k), (int, float)) and not math.isfinite(result[k]) for k in ('baseline', 'observed')):
            problems.append('NONFINITE_COMPARISON_VALUE')
        if not isinstance(result.get('unit'), str) or not result['unit'].strip():
            problems.append('COMPARISON_UNIT_REQUIRED')
    return {'schema': VERSION, 'decision': 'READY_FOR_INDEPENDENT_DOMAIN_REVIEW' if not problems else 'HOLD_EVIDENCE_INCOMPLETE',
            'problems': problems, 'checked_artifacts': checked, 'automatic_promotion': False,
            'native_or_legal_verification_inferred': False}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--evidence-root', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    result = preflight(json.loads(a.manifest.read_text(encoding='utf-8')), a.evidence_root)
    s = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if a.output: a.output.write_text(s, encoding='utf-8')
    else: print(s, end='')
    return 0 if not result['problems'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
