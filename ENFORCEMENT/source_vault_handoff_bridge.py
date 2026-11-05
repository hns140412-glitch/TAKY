#!/usr/bin/env python3
"""Review a SOURCE VAULT Notion handoff with TAKY's real reference-intake router.

This is a *bounded routing/ingress bridge*, not semantic Mining, raw acquisition,
Indexing, or promotion. All inputs remain local and read-only. The adapter
emits a deterministic, redacted plan receipt without modifying the pending queue.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from reference_intake_router import route

SCHEMA = 'TAKY_SOURCE_VAULT_CENTRAL_ROUTER_BRIDGE_V1'
TRACKING = {'fbclid', 'gclid', 'msclkid', 'mcp_token', 'session_sync_attempted', 'source', 'proxyreferer', 'trackingcode', 'notrackingcode', 'access_token', 'id_token', 'token', 'key', 'api_key', 'apikey', 'signature', 'sig', 'secret', 'password', 'credential', 'session', 'auth', 'authorization', 'expires', 'code'}
REQUIRED = ('INCREMENTAL_QUEUE.json', 'MINING_INBOX_HANDOFF.json', 'INCREMENTAL_SUMMARY.json')

class InputError(ValueError):
    pass


def read_json(path: Path) -> Any:
    if not path.is_file():
        raise InputError(f'REQUIRED_INPUT_MISSING:{path.name}')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def safe_url(value: object) -> str:
    try:
        parsed = urlsplit(str(value or '').strip())
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
            return ''
        items = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                 if not k.lower().startswith(('utm_', 'x-amz-', 'x-goog-')) and k.lower() not in TRACKING]
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(items), ''))
    except (ValueError, TypeError):
        return ''


def _comparison_url(value: object) -> tuple:
    """Compare only sanitized, same-origin URL identity; query presentation order is irrelevant."""
    safe = safe_url(value)
    if not safe:
        return ()
    parsed = urlsplit(safe)
    return (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path,
            tuple(sorted(parse_qsl(parsed.query, keep_blank_values=True))))


def url_conflict_detected(row: dict[str, Any]) -> bool:
    # Never trust a missing/false flag as proof that two separate source locators agree.
    if row.get('url_conflict'):
        return True
    direct = _comparison_url(row.get('url'))
    normalized = _comparison_url(row.get('normalized_url'))
    return bool(direct and normalized and direct != normalized)


def candidate_url(row: dict[str, Any]) -> str:
    # An absent URL may use normalized_url; two materially different locators
    # require source review, not a silent choice (including shortened redirects).
    if url_conflict_detected(row):
        return ''
    return safe_url(row.get('url') or row.get('normalized_url'))


def source_kind(row: dict[str, Any]) -> str:
    if url_conflict_detected(row):
        return 'HOLD_URL_CONFLICT'
    if row.get('record_type') == 'NOTION_CONTAINER':
        return 'NOTION_CHILD_DISCOVERY'
    if row.get('record_type') == 'ATTACHMENT_ONLY':
        return 'NOTION_ATTACHMENT_ACQUISITION'
    if candidate_url(row):
        return 'PUBLIC_URL_CANDIDATE'
    nodes = row.get('material_nodes') or []
    if any(isinstance(x, dict) and x.get('kind') == 'NOTION_CHILD' for x in nodes):
        return 'NOTION_CHILD_DISCOVERY'
    if any(isinstance(x, dict) and x.get('kind') == 'NOTION_ATTACHMENT' for x in nodes):
        return 'NOTION_ATTACHMENT_ACQUISITION'
    if row.get('block_link_candidates'):
        return 'REVIEW_BODY_LINK_CANDIDATES'
    return 'REVIEW_NO_SOURCE_LOCATOR'


def fingerprint(row: dict[str, Any]) -> str:
    folder = str(row.get('block_snapshot_folder') or '')
    # Filename is only a locator hint. It does not verify local bytes or content.
    return PureWindowsPath(folder).name if folder else ''


def build_receipt(report_dir: Path) -> dict[str, Any]:
    q, handoff, summary = [read_json(report_dir / name) for name in REQUIRED]
    if not isinstance(q, list) or not isinstance(handoff, dict) or not isinstance(handoff.get('items'), list) or not isinstance(summary, dict):
        raise InputError('INVALID_INPUT_SHAPE')
    ids = [row.get('notion_page_id') for row in q if isinstance(row, dict)]
    if len(ids) != len(q) or len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        raise InputError('DUPLICATE_OR_INVALID_QUEUE_PAGE_ID')
    handoff_ids = [row.get('notion_page_id') for row in handoff['items'] if isinstance(row, dict)]
    if len(handoff_ids) != len(q) or set(ids) != set(handoff_ids):
        raise InputError('QUEUE_HANDOFF_MISMATCH')
    if summary.get('queue_count') != len(q):
        raise InputError('SUMMARY_COUNT_MISMATCH')
    if summary.get('notion_total') is not None and summary.get('notion_total') != len(q):
        raise InputError('SUMMARY_NOTION_TOTAL_MISMATCH')
    if any(row.get('mining_status') != 'PENDING_NOT_PROMOTED' for row in q):
        raise InputError('QUEUE_CONTAINS_ACK_OR_PROMOTION')

    routes = []
    for row in q:
        kind = source_kind(row)
        page_id = row['notion_page_id']
        normalized = candidate_url(row) if kind == 'PUBLIC_URL_CANDIDATE' else ''
        record = {'intent_text': '신규 참고자료의 원문을 확보하고 기존 자료와 비교 검토하여 활용 후보로 기록',
                  'reference_intake_intent': True, 'has_reference_source': True,
                  'source_id': f'notion:{page_id}', 'source_locator': f'notion:{page_id}',
                  'source_url': normalized, 'domain': 'unspecified'}
        result = route(record)
        if not (result.get('pass') is True and result.get('route_type') == 'REFERENCE_INTAKE_REVIEW'
                and result.get('canonical_promotion_authorized') is False
                and result.get('full_corpus_reindex') is False):
            raise InputError(f'CENTRAL_ROUTER_GUARD_FAILED:{page_id}')
        routes.append({'notion_page_id': page_id, 'kind': kind, 'source_id': record['source_id'],
                       'snapshot_locator_hint': fingerprint(row),
                       'source_url': normalized or None,
                       'source_url_is_verified_current': False,
                       'route_type': result['route_type'], 'next_handoff': result['pipeline'][1],
                       'state': 'ROUTED_NOT_MINED'})
    return {'schema': SCHEMA, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'input_count': len(q), 'queue_sha256': hashlib.sha256((report_dir / REQUIRED[0]).read_bytes()).hexdigest(),
            'handoff_sha256': hashlib.sha256((report_dir / REQUIRED[1]).read_bytes()).hexdigest(),
            'summary_sha256': hashlib.sha256((report_dir / REQUIRED[2]).read_bytes()).hexdigest(),
            'route_counts': dict(Counter(x['kind'] for x in routes)), 'routes': routes,
            'notion_api_called': False, 'network_acquisition': False, 'central_router_executed': True,
            'semantic_mining_executed': False, 'indexing_executed': False,
            'canonical_promotion': False, 'queue_acknowledged': False,
            'original_queue_unchanged': True,
            'next': 'ACQUISITION_RECEIPT_THEN_INDEX_OWNER_REVIEW'}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--reports', required=True, type=Path, help='Existing local SOURCE VAULT reports directory')
    parser.add_argument('--output', type=Path, default=None)
    args = parser.parse_args()
    report_dir = args.reports.resolve()
    original = {n: hashlib.sha256((report_dir / n).read_bytes()).hexdigest() for n in REQUIRED if (report_dir / n).is_file()}
    result = build_receipt(report_dir)
    if {n: hashlib.sha256((report_dir / n).read_bytes()).hexdigest() for n in REQUIRED} != original:
        raise InputError('SOURCE_CHANGED_DURING_ROUTING')
    output = args.output or report_dir / 'SOURCE_VAULT_ROUTER_RECEIPT.json'
    if output.resolve() in {(report_dir / n).resolve() for n in REQUIRED}:
        raise InputError('REFUSE_TO_OVERWRITE_PENDING_INPUT')
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + '.tmp')
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, output)
    print(json.dumps({'result': 'PASS_CENTRAL_ROUTER_ONLY', 'input_count': result['input_count'],
                      'route_counts': result['route_counts'], 'output': str(output),
                      'semantic_mining_executed': False, 'queue_acknowledged': False}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
