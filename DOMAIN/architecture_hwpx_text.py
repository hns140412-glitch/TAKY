#!/usr/bin/env python3
"""Bounded, read-only HWPX text extraction for owner-provided source files.

This is not HWP (OLE) support, an authority receipt, or project approval.
Keeps paragraph boundaries, reads only document section XML, never macros/media.
"""
from __future__ import annotations
import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SECTION = re.compile(r'^Contents/section([0-9]+)\.xml$')
MAX_TOTAL_XML_BYTES = 20 * 1024 * 1024
MAX_SECTIONS = 64


def extract(path: Path) -> dict:
    paragraphs = []
    with zipfile.ZipFile(path) as archive:
        sections = []
        for member in archive.infolist():
            match = SECTION.fullmatch(member.filename)
            if match:
                sections.append((int(match.group(1)), member))
        sections.sort(key=lambda pair: pair[0])
        if not sections or len(sections) > MAX_SECTIONS:
            raise ValueError('HWPX_SECTION_COUNT_INVALID')
        if sum(info.file_size for _, info in sections) > MAX_TOTAL_XML_BYTES:
            raise ValueError('HWPX_SECTION_XML_LIMIT_EXCEEDED')
        for _, info in sections:
            root = ET.fromstring(archive.read(info))
            for para in root.iter():
                if para.tag.rsplit('}', 1)[-1] != 'p':
                    continue
                spans = [node.text for node in para.iter()
                         if node.tag.rsplit('}', 1)[-1] == 't' and node.text]
                if spans:
                    paragraphs.append(''.join(spans))
    if not paragraphs:
        raise ValueError('HWPX_NO_EXTRACTABLE_TEXT')
    return {'format': 'HWPX', 'status': 'TEXT_EXTRACTED_NOT_SEMANTICALLY_VERIFIED',
            'paragraph_count': len(paragraphs), 'text': '\n'.join(paragraphs),
            'source_content_authority': False}


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument('--input', type=Path, required=True)
    cli.add_argument('--output', type=Path)
    args = cli.parse_args()
    payload = json.dumps(extract(args.input), ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(payload, encoding='utf-8')
    else:
        print(payload, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
