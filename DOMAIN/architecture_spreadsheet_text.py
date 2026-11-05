#!/usr/bin/env python3
"""Read-only text extraction from XLSX/XLSM OOXML cells, never execute macros/formulas.

Owner-provided bytes only. Formula caches may be missing/stale; no calculation authority.
"""
from __future__ import annotations
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

MAX_XML_BYTES = 32 * 1024 * 1024
MAX_SHEETS = 24
MAX_ROWS = 10000
MAX_CELLS = 150000
SHEET_RE = re.compile(r'^xl/worksheets/sheet([0-9]+)\.xml$')


def extract(path: Path) -> dict:
    lines = []
    warnings = set()
    with zipfile.ZipFile(path) as archive:
        sheets = sorted((int(m.group(1)), info) for info in archive.infolist()
                        if (m := SHEET_RE.fullmatch(info.filename)))
        if not sheets or len(sheets) > MAX_SHEETS:
            raise ValueError('OOXML_SHEET_COUNT_INVALID')
        string_file = next((i for i in archive.infolist() if i.filename == 'xl/sharedStrings.xml'), None)
        xml_items = [item for _, item in sheets] + ([string_file] if string_file else [])
        if sum(item.file_size for item in xml_items) > MAX_XML_BYTES:
            raise ValueError('OOXML_XML_BYTES_LIMIT')
        strings = []
        if string_file:
            tree = ET.fromstring(archive.read(string_file))
            for si in tree:
                if si.tag.rsplit('}', 1)[-1] == 'si':
                    strings.append(''.join(t.text or '' for t in si.iter() if t.tag.rsplit('}', 1)[-1] == 't'))
        count = 0
        for sheet_id, info in sheets:
            root = ET.fromstring(archive.read(info))
            rows = [x for x in root.iter() if x.tag.rsplit('}', 1)[-1] == 'row']
            if len(rows) > MAX_ROWS:
                raise ValueError('OOXML_ROW_LIMIT')
            for row in rows:
                cells = []
                for cell in row:
                    if cell.tag.rsplit('}', 1)[-1] != 'c':
                        continue
                    count += 1
                    if count > MAX_CELLS:
                        raise ValueError('OOXML_CELL_LIMIT')
                    cell_type = cell.get('t')
                    value_node = next((n for n in cell if n.tag.rsplit('}', 1)[-1] == 'v'), None)
                    formula = any(n.tag.rsplit('}', 1)[-1] == 'f' for n in cell)
                    if formula:
                        warnings.add('FORMULA_CACHE_NOT_RECALCULATED')
                    if cell_type == 'inlineStr':
                        value = ''.join(n.text or '' for n in cell.iter() if n.tag.rsplit('}', 1)[-1] == 't')
                    elif value_node is None or value_node.text is None:
                        value = ''
                    elif cell_type == 's':
                        idx = int(value_node.text)
                        if idx < 0 or idx >= len(strings):
                            raise ValueError('SHARED_STRING_INDEX_INVALID')
                        value = strings[idx]
                    else:
                        value = value_node.text
                    if value.strip():
                        cells.append(f"{cell.get('r', '?')}={value}")
                if cells:
                    lines.append(f"SHEET_{sheet_id} ROW_{row.get('r','?')} " + ' | '.join(cells))
    if not lines:
        raise ValueError('OOXML_NO_EXTRACTABLE_CELLS')
    return {'format': path.suffix.lower()[1:].upper(), 'status': 'CELL_TEXT_EXTRACTED_NOT_FORMULA_OR_LEGAL_VERIFIED',
            'row_count': len(lines), 'cell_count': count, 'text': '\n'.join(lines),
            'warnings': sorted(warnings), 'macros_executed': False, 'formula_recalculated': False,
            'source_content_authority': False}
