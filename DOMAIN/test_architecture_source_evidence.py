import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from architecture_source_evidence import packet


class EvidenceTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.idx = {'source_entries': [{'source_id': 'exact-owner-file-id',
                     'title': 'Source', 'source_family': 'ARCHITECTURE_WORK_SOURCE',
                     'source_review_state': 'METADATA_INDEXED', 'authority_level': 'REFERENCE_ONLY'}]}
        self.txt = self.dir / 'source.txt'
        self.txt.write_text('방수 접합부 검토\\n계획 범위 외 사항', encoding='utf-8')

    def test_exact_v26_identity_and_evidence_excerpt(self):
        r = packet(self.idx, 'exact-owner-file-id', self.txt, revision='owner-rev-1', query='방수')
        self.assertTrue(r['query_evidence_found'])
        self.assertEqual(r['excerpts'][0]['paragraph'], 1)
        self.assertFalse(r['project_applicability_verified'])
        self.assertFalse(r['method_adoption_authorized'])
        self.assertEqual(len(r['source_sha256']), 64)

    def test_other_source_id_does_not_inherit_text(self):
        with self.assertRaisesRegex(ValueError, 'SOURCE_ID_MISSING_OR_AMBIGUOUS'):
            packet(self.idx, 'other-id', self.txt, revision='owner-rev-1', query='방수')

    def test_hold_scope_is_blocked(self):
        with self.assertRaisesRegex(ValueError, 'PROTECTED_SCOPE_HOLD'):
            packet(self.idx, 'exact-owner-file-id', self.txt, revision='owner-rev-1', query='방수', scope_tags=['HANNAM'])

    def test_unmatched_query_not_claimed_as_supported(self):
        r = packet(self.idx, 'exact-owner-file-id', self.txt, revision='owner-rev-1', query='주차대수')
        self.assertTrue(r['source_text_retrieved'])
        self.assertFalse(r['query_evidence_found'])

    def test_partial_query_cannot_be_claimed_as_supported(self):
        r = packet(self.idx, 'exact-owner-file-id', self.txt, revision='owner-rev-1', query='방수 주차대수')
        self.assertFalse(r['query_evidence_found'])
        self.assertEqual(r['query_coverage'], 'PARTIAL_ONLY')

    def test_ole_hwp_not_misread_as_text(self):
        old = self.dir / 'old.hwp'
        old.write_bytes(b'old binary')
        with self.assertRaisesRegex(ValueError, 'EXTRACTION_ROUTE_REQUIRED'):
            packet(self.idx, 'exact-owner-file-id', old, revision='owner-rev-1', query='방수')

    def test_xlsm_source_binding_does_not_execute_macros(self):
        archive = self.dir / 'sample.xlsm'
        with zipfile.ZipFile(archive, 'w') as out:
            out.writestr('xl/worksheets/sheet1.xml',
                '<worksheet><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>법규 검토</t></is></c></row></sheetData></worksheet>')
            out.writestr('xl/vbaProject.bin', b'NEVER_RUN')
        r = packet(self.idx, 'exact-owner-file-id', archive, revision='owner-rev-1', query='법규')
        self.assertTrue(r['query_evidence_found'])
        self.assertEqual(r['extraction_method'], 'OOXML_CELLS_NO_FORMULA_EVALUATION')

    def test_hwpx_actual_sections_bind_to_source(self):
        archive = self.dir / 'sample.hwpx'
        with zipfile.ZipFile(archive, 'w') as out:
            out.writestr('Contents/section0.xml',
                         '<h:sec xmlns:h="urn:test"><h:p><h:run><h:t>안전 구조 검토</h:t></h:run></h:p></h:sec>')
        r = packet(self.idx, 'exact-owner-file-id', archive, revision='owner-rev-1', query='구조')
        self.assertEqual(r['extraction_method'], 'HWPX_SECTION_XML')
        self.assertTrue(r['query_evidence_found'])


if __name__ == '__main__':
    unittest.main()
