#!/usr/bin/env python3
"""ARCHI GROW domain action routing; no Work OS, Mining or authority duplication.

Reads evidence/gap records; emits proposals and Work OS handoff packets only.
No network, persistence, promotion, project geometry or legal conclusions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

VERSION = 'ARCHIGROW_GROWTH_CYCLE_V1'
PRIORITY = {'P0': 0, 'P1': 1, 'P2': 2}
FROZEN_TAGS = frozenset({'CTB', 'LISP', 'HANNAM'})
STATES = frozenset({'OPEN', 'FRONTIER', 'CURRENT_BEST', 'HOLD'})


def _str(value):
    return value.strip() if isinstance(value, str) else ''


def _route(item, action, owner, next_step, acceptance, *, payload=None, blockers=None):
    return {
        'gap_id': item['gap_id'], 'status': item['status'],
        'priority': item['priority'], 'route': action, 'next_owner': owner,
        'next_action': next_step, 'acceptance_evidence': acceptance,
        'payload': payload or {}, 'blockers': blockers or [],
        'automatic_canonical_promotion': False,
        'automatic_source_or_work_os_mutation': False,
    }


def assess(item):
    """Pure deterministic routing. No input record can authorize its own promotion."""
    if not isinstance(item, dict):
        return {'pass': False, 'detected': ['GAP_OBJECT_REQUIRED']}
    errors = []
    for key in ('gap_id', 'question', 'target_capability'):
        if not _str(item.get(key)):
            errors.append('MISSING:' + key)
    if item.get('domain') != 'ARCHITECTURE' or item.get('owner') != 'ARCHI_GROW':
        errors.append('DOMAIN_OWNER_INVALID')
    if item.get('priority') not in PRIORITY:
        errors.append('PRIORITY_INVALID')
    if item.get('status') not in STATES:
        errors.append('STATUS_INVALID')
    proof = item.get('proof')
    if not isinstance(proof, dict) or not all(_str(proof.get(k)) for k in ('baseline', 'acceptance', 'metric')):
        errors.append('PROOF_CONTRACT_REQUIRED')
    if errors:
        return {'pass': False, 'gap_id': item.get('gap_id'), 'detected': errors}
    tags = set(map(str.upper, item.get('tags') or []))
    if item['status'] == 'HOLD' or tags.intersection(FROZEN_TAGS):
        return {'pass': True, 'result': _route(item, 'HOLD_PRESERVED', 'HUMAN',
            'Do not mine, modify, run tests or route execution without an explicit resume.',
            'Explicit resume instruction referencing this scope.',
            blockers=['USER_HOLD'])}
    if item['status'] == 'CURRENT_BEST':
        if not _str(item.get('approval_receipt_id')):
            return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['UNAPPROVED_CURRENT_BEST']}
        return {'pass': True, 'result': _route(item, 'OBSERVE_CURRENT_BEST', 'ARCHI_GROW',
            'Watch for new contradictory case/outcome evidence without re-promoting.',
            'New evidence or changed conditions justify re-evaluation.')}

    refs = item.get('source_refs') or []
    if not isinstance(refs, list):
        return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['SOURCE_REFS_INVALID']}
    ids = set()
    for ref in refs:
        if not isinstance(ref, dict) or not all(_str(ref.get(k)) for k in ('id', 'location', 'revision', 'role')):
            return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['SOURCE_PROVENANCE_INCOMPLETE']}
        if ref['id'] in ids:
            return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['DUPLICATE_SOURCE_ID']}
        ids.add(ref['id'])

    indexed = item.get('index_receipt') or {}
    if indexed.get('checked') is not True or not _str(indexed.get('receipt_id')):
        return {'pass': True, 'result': _route(item, 'INDEX_QUERY_REQUEST', 'INDEXING',
            'Search existing indexed source/CASE/STRATEGY/FAILURE before asking Mining to collect more.',
            'Dated Indexing receipt with sufficient/insufficient result and source IDs.',
            payload={'query': item['question'], 'known_source_ids': sorted(ids), 'requested_capability': item['target_capability']})}
    if not isinstance(indexed.get('sufficient'), bool):
        return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['INDEX_SUFFICIENCY_MISSING']}
    if indexed['sufficient'] is False:
        digest = indexed.get('index_payload_sha256')
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest.lower()) or not _str(indexed.get('insufficiency_evidence')):
            return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['INDEX_INSUFFICIENCY_PROOF_REQUIRED']}
        return {'pass': True, 'result': _route(item, 'MINING_GAP_REQUEST', 'MINING',
            'Acquire missing source evidence; record official/industry/case authority and date. Never grant rule authority.',
            'Source receipt indexed with provenance and explicit applicability/limitations.',
            payload={'index_receipt_id': indexed['receipt_id'], 'question': item['question'], 'source_refs': sorted(ids)})}
    eligible = set(indexed.get('eligible_source_ids') or [])
    evidence_ids = {ref['id'] for ref in refs if ref.get('role') in ('SOURCE_EVIDENCE', 'PROJECT_SOURCE', 'METHOD_EVIDENCE')}
    if not eligible or not eligible.issubset(evidence_ids):
        return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['INDEX_SOURCE_TRACE_MISMATCH']}
    if not _str(indexed.get('sufficiency_evidence')) or not _str(indexed.get('index_payload_sha256')):
        return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['INDEX_SUFFICIENCY_PROOF_REQUIRED']}

    candidate = item.get('method_candidate') or {}
    if not _str(candidate.get('id')):
        return {'pass': True, 'result': _route(item, 'DOMAIN_METHOD_SYNTHESIS', 'ARCHI_GROW',
            'Compare evidence and propose one localized architectural method with trade-offs, falsification test and scope.',
            'Method ID, applicable conditions, competing method, risk and test contract.',
            payload={'eligible_source_ids': sorted(eligible), 'proof': item['proof']})}
    if not _str(candidate.get('rationale')) or not _str(candidate.get('tradeoff')) or not _str(candidate.get('falsification')):
        return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['METHOD_ARGUMENT_INCOMPLETE']}
    if not set(candidate.get('source_ids') or []).issubset(eligible) or not candidate.get('source_ids'):
        return {'pass': False, 'gap_id': item['gap_id'], 'detected': ['METHOD_SOURCE_TRACE_INVALID']}
    trial = item.get('work_os_trial') or {}
    if not _str(trial.get('receipt_id')):
        return {'pass': True, 'result': _route(item, 'WORK_OS_TRIAL_HANDOFF', 'WORK_OS',
            'Run one bounded real-work experiment without changing canonical rules or frozen scopes.',
            'Work OS artifact, baseline/comparison, error/regression evidence and project/REV identity.',
            payload={'method_id': candidate['id'], 'proof': item['proof'], 'source_ids': candidate['source_ids'],
                     'frozen_tags': sorted(FROZEN_TAGS)})}
    outcome = trial.get('outcome') or {}
    if not _str(outcome.get('receipt_id')) or outcome.get('state') not in ('PASS', 'FAIL', 'PARTIAL'):
        return {'pass': True, 'result': _route(item, 'OUTCOME_RECEIPT_REQUEST', 'WORK_OS',
            'Return traceable outcome versus the declared baseline; do not call a unit-test-only run a real project success.',
            'Outcome receipt, project/revision identity, comparison and failure details.', payload={'trial_receipt_id': trial['receipt_id']})}
    if outcome['state'] != 'PASS':
        return {'pass': True, 'result': _route(item, 'REVISE_METHOD', 'ARCHI_GROW',
            'Classify observed failure/partial result, compare alternatives, and prepare a bounded correction.',
            'New method candidate linked to failure receipt; prior candidate retained.',
            payload={'outcome_receipt_id': outcome['receipt_id'], 'failure_class': outcome.get('failure_class', 'UNCLASSIFIED')})}
    if outcome.get('proof_preflight') != 'FILE_HASH_PASS__DOMAIN_REVIEW_PENDING' or not all(_str(outcome.get(k)) for k in ('real_project_ref', 'project_revision', 'independent_verification_receipt', 'regression_receipt')):
        return {'pass': True, 'result': _route(item, 'REAL_PROOF_GAP', 'WORK_OS',
            'Independently verify a real source-backed project result and regression before domain adoption review.',
            'Real project/REV, independent verification and regression receipt.', blockers=['PASS_CLAIM_NOT_REAL_PROJECT_PROVEN'])}
    return {'pass': True, 'result': _route(item, 'HUMAN_ADOPTION_REVIEW', 'ARCHI_GROW',
        'Review as candidate for existing CURRENT_BEST/FRONTIER owner; never self-promote.',
        'Recorded human approval, applicability, superseded method and rollback conditions.',
        payload={'candidate_id': candidate['id'], 'outcome_receipt_id': outcome['receipt_id'],
                 'independent_verification_receipt': outcome['independent_verification_receipt']})}


def make_board(backlog):
    if backlog.get('schema') != VERSION or not isinstance(backlog.get('gaps'), list):
        raise ValueError('BACKLOG_SCHEMA_INVALID')
    seen = set()
    results = []
    for item in backlog['gaps']:
        result = assess(item)
        if not result['pass']:
            raise ValueError(str(result.get('gap_id')) + ':' + ','.join(result['detected']))
        id_ = item['gap_id']
        if id_ in seen:
            raise ValueError('DUPLICATE_GAP_ID:' + id_)
        seen.add(id_)
        results.append(result['result'])
    results.sort(key=lambda x: (PRIORITY[x['priority']], x['gap_id']))
    active = [x for x in results if x['route'] not in ('HOLD_PRESERVED', 'OBSERVE_CURRENT_BEST')]
    return {
        'schema': VERSION, 'authority': 'ARCHITECTURE_DOMAIN_ACTION_PROPOSAL_ONLY',
        'work_os_execution_owned_by': 'WORK_OS', 'tak_y_governance_owned_by': 'TAKY',
        'next_action': active[0] if active else None, 'items': results,
        'no_automatic_promotion': True, 'no_external_actions_executed': True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('backlog', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    board = make_board(json.loads(args.backlog.read_text(encoding='utf-8')))
    output = json.dumps(board, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
