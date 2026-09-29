#!/usr/bin/env python3
"""Bind owner-extracted source bytes to existing V26 identity and return bounded excerpts.

Does not fetch private Drive files, certify current law, or promote CURRENT.
Owner supplies exact source_id, source bytes and revision. No folder-name inference.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from architecture_hwpx_text import extract as extract_hwpx

MAX_TEXT_BYTES = 12 * 1024 * 1024
MAX_EXCERPTS = 5
MAX_EXCERPT_CHARS = 480
HOLD_TERMS = {'CTB', 'LISP', 'HANNAM'}


def packet(index_payload: dict, source_id: str, file: Path, *, revision: str, query: str, scope_tags=()) -> dict:
    if HOLD_TERMS.intersection({str(x).upper() for x in scope_tags}):
        raise ValueError('PROTECTED_SCOPE_HOLD')
    entries = index_payload.get('source_entries')
    if not isinstance(entries, list):
        raise ValueError('V26_SOURCE_ENTRIES_REQUIRED')
    matches = [x for x in entries if x.get('source_id') == source_id]
    if len(matches) != 1 or not source_id:
        raise ValueError('SOURCE_ID_MISSING_OR_AMBIGUOUS')
    row = matches[0]
    if row.get('source_family') != 'ARCHITECTURE_WORK_SOURCE':
        raise ValueError('NOT_ARCHITECTURE_SOURCE')
    if not revision or not revision.strip():
        raise ValueError('SOURCE_REVISION_REQUIRED')
    if not query or not query.strip():
        raise ValueError('QUERY_REQUIRED')
    suffix = file.suffix.lower()
    if suffix == '.hwpx':
        extracted = extract_hwpx(file)
        content = extracted['text']
        method = 'HWPX_SECTION_XML'
    elif suffix in ('.txt', '.md'):
        if file.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError('TEXT_BYTES_LIMIT_EXCEEDED')
        content = file.read_text(encoding='utf-8-sig')
        method = 'OWNER_SUPPLIED_TEXT'
    else:
        raise ValueError('EXTRACTION_ROUTE_REQUIRED:' + suffix)
    terms = list(dict.fromkeys(x.lower() for x in re.findall(r'[가-힣]+|[a-zA-Z0-9]+', query) if len(x) >= 2))
    paragraphs = [x.strip() for x in content.splitlines() if x.strip()]
    scored = [(sum(1 for t in terms if t in line.lower()), i, line) for i, line in enumerate(paragraphs)]
    all_terms_present = bool(terms) and all(any(t in line.lower() for line in paragraphs) for t in terms)
    matched = sorted((r for r in scored if r[0]), key=lambda r: (-r[0], r[1]))[:MAX_EXCERPTS]
    if not matched:
        excerpts = []
    else:
        excerpts = [{'paragraph': i + 1, 'text': line[:MAX_EXCERPT_CHARS], 'truncated': len(line) > MAX_EXCERPT_CHARS}
                    for _, i, line in matched]
    return {
        'source_id': source_id, 'title': row.get('title'), 'revision': revision,
        'authority_level': row.get('authority_level'), 'index_review_state': row.get('source_review_state'),
        'source_sha256': hashlib.sha256(file.read_bytes()).hexdigest(), 'extraction_method': method,
        'paragraph_count': len(paragraphs), 'query': query, 'excerpts': excerpts,
        'source_text_retrieved': True, 'query_evidence_found': bool(excerpts) and all_terms_present,
        'query_coverage': 'ALL_TERMS_IN_SOURCE' if all_terms_present else ('PARTIAL_ONLY' if excerpts else 'NO_MATCH'),
        'project_applicability_verified': False, 'legal_currentness_verified': False,
        'method_adoption_authorized': False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', type=Path, required=True)
    ap.add_argument('--source-id', required=True)
    ap.add_argument('--file', type=Path, required=True)
    ap.add_argument('--revision', required=True)
    ap.add_argument('--query', required=True)
    ap.add_argument('--scope-tag', action='append', default=[])
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = packet(json.loads(args.index.read_text(encoding='utf-8-sig')), args.source_id,
                    args.file, revision=args.revision, query=args.query, scope_tags=args.scope_tag)
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
