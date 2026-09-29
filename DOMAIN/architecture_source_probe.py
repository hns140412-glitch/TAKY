#!/usr/bin/env python3
"""Read-only bridge from existing TAKY Indexing search projection to ARCHI GROW.

A search hit is NOT source sufficiency and NOT an INDEX_RESULT receipt. The output
is a review packet. Indexing must independently return the evidence/suitability
receipt before the domain growth cycle may route to Mining or method synthesis.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from architecture_growth_cycle import FROZEN_TAGS, PRIORITY, VERSION

BRIDGE_VERSION = 'ARCHIGROW_INDEX_PROBE_V1'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(backlog: dict, index_file: Path, index_module: Path, *, limit: int = 5) -> dict:
    if backlog.get('schema') != VERSION or not isinstance(backlog.get('gaps'), list):
        raise ValueError('BACKLOG_SCHEMA_INVALID')
    if not index_file.is_file() or not index_module.is_file():
        raise FileNotFoundError('REAL_INDEX_PAYLOAD_AND_EXISTING_SEARCH_IMPLEMENTATION_REQUIRED')
    expected_engine = Path(__file__).resolve().parent.parent / 'ENFORCEMENT' / 'data_index_search.py'
    if index_module.resolve() != expected_engine.resolve():
        raise ValueError('UNTRUSTED_INDEX_ENGINE_PATH')
    if not 1 <= limit <= 20:
        raise ValueError('LIMIT_INVALID')
    spec = importlib.util.spec_from_file_location('taky_readonly_index_search', index_module)
    if not spec or not spec.loader:
        raise ValueError('INDEX_ENGINE_LOAD_FAILED')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = module.load_index(index_file)
    if not records:
        raise ValueError('EMPTY_INDEX_NOT_SUFFICIENT_EVIDENCE')
    snapshot = {'index_payload_sha256': sha(index_file), 'engine_sha256': sha(index_module), 'record_count': len(records)}
    results = []
    seen = set()
    for gap in sorted(backlog['gaps'], key=lambda g: (PRIORITY.get(g.get('priority'), 99), str(g.get('gap_id')))):
        gap_id = gap.get('gap_id')
        if gap_id in seen:
            raise ValueError('DUPLICATE_GAP_ID:' + str(gap_id))
        seen.add(gap_id)
        if gap.get('status') == 'HOLD' or FROZEN_TAGS.intersection(set(map(str.upper, gap.get('tags') or []))):
            results.append({'gap_id': gap_id, 'state': 'HOLD_PRESERVED', 'query_executed': False})
            continue
        if gap.get('status') == 'CURRENT_BEST':
            results.append({'gap_id': gap_id, 'state': 'CURRENT_BEST_NO_REQUERY', 'query_executed': False})
            continue
        if gap.get('index_receipt'):
            results.append({'gap_id': gap_id, 'state': 'INDEX_RECEIPT_EXISTS_NO_REQUERY', 'query_executed': False})
            continue
        query = gap.get('question', '').strip()
        if not query:
            raise ValueError('GAP_QUERY_REQUIRED:' + str(gap_id))
        hit = module.search(records, query, filters={}, limit=limit, relation_depth=1)
        results.append({
            'gap_id': gap_id, 'query_executed': True, 'query': query,
            'state': 'INDEX_OWNER_SUITABILITY_REVIEW_REQUIRED',
            'retrieval_mode': hit.get('semantic_mode'), 'candidate_count': hit.get('candidate_count'),
            'candidates': [{k: row.get(k) for k in ('source_id', 'title', 'authority_class', 'current_relation', 'source_ref', 'provenance', 'detail_escalation', 'channels')} for row in hit['results']],
            'owner_review_required': ['source is actually about the gap', 'source revision/currentness', 'project applicability', 'source content supports claim', 'source rights/access'],
            'may_emit_index_result': False,
            'may_request_mining': False,
        })
    return {'schema': BRIDGE_VERSION, 'authority': 'READ_ONLY_INDEX_SEARCH_CANDIDATES_NOT_RECEIPT',
            'snapshot': snapshot, 'results': results, 'index_receipt_generated': False,
            'mining_invoked': False, 'work_os_invoked': False, 'source_or_current_mutated': False}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--backlog', type=Path, required=True)
    ap.add_argument('--index', type=Path, required=True)
    ap.add_argument('--search-engine', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = run(json.loads(args.backlog.read_text(encoding='utf-8')), args.index, args.search_engine)
    value = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(value, encoding='utf-8')
    else:
        print(value, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
