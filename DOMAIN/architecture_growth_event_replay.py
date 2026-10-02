#!/usr/bin/env python3
"""Replay external evidence receipts into an ephemeral ARCHI GROW projection.

The input is append-only event evidence maintained by the rightful source owner.
This script never rewrites input, calls Indexing/Mining, or promotes domain authority.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
from architecture_work_os_proof import preflight
from architecture_growth_cycle import FROZEN_TAGS, assess, make_board

TYPES = {
    'SOURCE_RECEIPT': ('INDEXING', 'source_refs'),
    'INDEX_RESULT': ('INDEXING', 'index_receipt'),
    'METHOD_CANDIDATE': ('ARCHI_GROW', 'method_candidate'),
    'WORK_OS_TRIAL': ('WORK_OS', 'work_os_trial'),
    'WORK_OS_OUTCOME': ('WORK_OS', 'outcome'),
}


def replay(backlog: dict, events: list[dict], *, evidence_root: Path | None = None) -> dict:
    projection = copy.deepcopy(backlog)
    gaps = {g['gap_id']: g for g in projection['gaps']}
    seen: dict[str, str] = {}
    history = []
    for event in events:
        if not isinstance(event, dict) or not all(isinstance(event.get(k), str) and event[k].strip() for k in ('event_id', 'gap_id', 'type', 'receipt_id', 'occurred_at')):
            raise ValueError('EVENT_REQUIRED_FIELDS')
        identity = event['event_id']
        encoded = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        if identity in seen:
            if seen[identity] != encoded:
                raise ValueError('EVENT_ID_CONTENT_CONFLICT:' + identity)
            continue  # replay is idempotent
        seen[identity] = encoded
        gap = gaps.get(event['gap_id'])
        if gap is None:
            raise ValueError('UNKNOWN_GAP:' + event['gap_id'])
        if gap['status'] == 'HOLD' or set(map(str.upper, gap.get('tags', []))).intersection(FROZEN_TAGS):
            raise ValueError('HELD_SCOPE_EVENT_REJECTED:' + event['gap_id'])
        kind = event['type']
        spec = TYPES.get(kind)
        if spec is None or event.get('issuer') != spec[0]:
            raise ValueError('EVENT_OWNER_OR_TYPE_INVALID:' + identity)
        payload = copy.deepcopy(event.get('payload'))
        if not isinstance(payload, dict):
            raise ValueError('EVENT_PAYLOAD_REQUIRED:' + identity)
        if kind == 'SOURCE_RECEIPT':
            required = ('id', 'location', 'revision', 'role')
            if not all(isinstance(payload.get(k), str) and payload[k].strip() for k in required):
                raise ValueError('SOURCE_PROVENANCE_INCOMPLETE:' + identity)
            if payload['id'] in {x['id'] for x in gap.get('source_refs', [])}:
                raise ValueError('SOURCE_DUPLICATE_OR_REVISION_CONFLICT:' + payload['id'])
            gap.setdefault('source_refs', []).append(payload)
        elif kind == 'INDEX_RESULT':
            if gap.get('index_receipt'):
                raise ValueError('INDEX_RESULT_REPLACEMENT_REQUIRES_NEW_GAP_REVISION:' + identity)
            if not isinstance(payload.get('index_payload_sha256'), str) or len(payload['index_payload_sha256']) != 64 or any(c not in '0123456789abcdef' for c in payload['index_payload_sha256'].lower()):
                raise ValueError('INDEX_SNAPSHOT_SHA256_REQUIRED:' + identity)
            if payload.get('sufficient') is False and not (isinstance(payload.get('insufficiency_evidence'), str) and payload['insufficiency_evidence'].strip()):
                raise ValueError('INDEX_INSUFFICIENCY_PROOF_REQUIRED:' + identity)
            if gap.get('index_receipt'):
                raise ValueError('INDEX_RESULT_REPLACEMENT_REQUIRES_NEW_GAP_REVISION:' + identity)
            if payload.get('checked') is not True or not isinstance(payload.get('sufficient'), bool) or payload.get('receipt_id') != event['receipt_id']:
                raise ValueError('INDEX_RECEIPT_INVALID:' + identity)
            if payload['sufficient'] and (not payload.get('sufficiency_evidence') or not payload.get('index_payload_sha256')):
                raise ValueError('INDEX_SUFFICIENCY_PROOF_REQUIRED:' + identity)
            gap['index_receipt'] = payload
        elif kind == 'METHOD_CANDIDATE':
            if assess(gap)['result']['route'] != 'DOMAIN_METHOD_SYNTHESIS':
                raise ValueError('METHOD_OUT_OF_ORDER:' + identity)
            if gap.get('method_candidate'):
                raise ValueError('METHOD_REPLACEMENT_REQUIRES_NEW_GAP_REVISION:' + identity)
            gap['method_candidate'] = payload
        elif kind == 'WORK_OS_TRIAL':
            if assess(gap)['result']['route'] != 'WORK_OS_TRIAL_HANDOFF':
                raise ValueError('TRIAL_OUT_OF_ORDER:' + identity)
            if gap.get('work_os_trial'):
                raise ValueError('TRIAL_REPLACEMENT_REQUIRES_NEW_GAP_REVISION:' + identity)
            if payload.get('receipt_id') != event['receipt_id']:
                raise ValueError('TRIAL_RECEIPT_MISMATCH:' + identity)
            gap['work_os_trial'] = payload
        elif kind == 'WORK_OS_OUTCOME':
            trial = gap.get('work_os_trial')
            if not isinstance(trial, dict) or not trial.get('receipt_id') or trial.get('outcome'):
                raise ValueError('OUTCOME_WITHOUT_OPEN_TRIAL:' + identity)
            if payload.get('receipt_id') != event['receipt_id']:
                raise ValueError('OUTCOME_RECEIPT_MISMATCH:' + identity)
            if payload.get('state') == 'PASS':
                manifest_relative = payload.get('evidence_manifest')
                expected_manifest_sha = payload.get('evidence_manifest_sha256')
                if not evidence_root or not isinstance(manifest_relative, str) or not isinstance(expected_manifest_sha, str):
                    raise ValueError('PASS_PROOF_MANIFEST_REQUIRED:' + identity)
                root = evidence_root.resolve()
                manifest_path = (root / manifest_relative).resolve()
                if not manifest_path.is_relative_to(root) or not manifest_path.is_file():
                    raise ValueError('PASS_PROOF_MANIFEST_PATH_INVALID:' + identity)
                actual_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                if actual_digest != expected_manifest_sha:
                    raise ValueError('PASS_PROOF_MANIFEST_HASH_INVALID:' + identity)
                proof = json.loads(manifest_path.read_text(encoding='utf-8'))
                bound = proof.get('project') or {}
                if proof.get('state') != 'PASS' or bound.get('trial_receipt_id') != trial['receipt_id'] or bound.get('outcome_receipt_id') != event['receipt_id'] or bound.get('project_id') != payload.get('real_project_ref') or bound.get('revision_id') != payload.get('project_revision'):
                    raise ValueError('PASS_PROOF_TRIAL_OUTCOME_BINDING_INVALID:' + identity)
                checked = preflight(proof, root)
                if checked['problems']:
                    raise ValueError('PASS_PROOF_PREFLIGHT_FAILED:' + identity + ':' + ','.join(checked['problems']))
                # Byte-level evidence check is NOT semantic/technical verification or adoption.
                payload = copy.deepcopy(payload)
                payload['proof_preflight'] = 'FILE_HASH_PASS__DOMAIN_REVIEW_PENDING'
                payload['proof_manifest_sha256'] = actual_digest
            trial['outcome'] = payload
        checked = assess(gap)
        if not checked['pass']:
            raise ValueError('REPLAY_PROJECTION_INVALID:' + identity + ':' + ','.join(checked['detected']))
        history.append({'event_id': identity, 'gap_id': gap['gap_id'], 'receipt_id': event['receipt_id'], 'resulting_route': checked['result']['route']})
    return {'board': make_board(projection), 'event_history': history,
            'projection_only': True, 'original_backlog_unchanged': True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('backlog', type=Path)
    ap.add_argument('events', type=Path, help='JSON list or JSONL append-only receipts')
    ap.add_argument('--output', type=Path)
    ap.add_argument('--evidence-root', type=Path, help='Required for PASS outcome evidence; no implicit current directory')
    args = ap.parse_args()
    baseline = json.loads(args.backlog.read_text(encoding='utf-8'))
    raw = args.events.read_text(encoding='utf-8')
    events = json.loads(raw) if raw.lstrip().startswith('[') else [json.loads(x) for x in raw.splitlines() if x.strip()]
    result = replay(baseline, events, evidence_root=args.evidence_root)
    out = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(out, encoding='utf-8')
    else:
        print(out, end='')


if __name__ == '__main__':
    main()
