import tempfile
import unittest
import zipfile
from pathlib import Path
from architecture_hwpx_text import extract


class HwpxTextTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'sample.hwpx'

    def test_extracts_paragraphs_without_claiming_source_authority(self):
        xml = ('<h:sec xmlns:h="urn:test">'
               '<h:p><h:run><h:t>설계 </h:t><h:t>검토</h:t></h:run></h:p>'
               '<h:p><h:run><h:t>두 번째 문단</h:t></h:run></h:p>'
               '</h:sec>')
        with zipfile.ZipFile(self.path, 'w') as out:
            out.writestr('Contents/section0.xml', xml)
            out.writestr('Scripts/macro.js', 'untrusted')
        result = extract(self.path)
        self.assertEqual(result['text'], '설계 검토\n두 번째 문단')
        self.assertEqual(result['paragraph_count'], 2)
        self.assertFalse(result['source_content_authority'])

    def test_rejects_missing_sections(self):
        with zipfile.ZipFile(self.path, 'w') as out:
            out.writestr('Contents/not-a-section.xml', '<p/>')
        with self.assertRaisesRegex(ValueError, 'HWPX_SECTION_COUNT_INVALID'):
            extract(self.path)

    def test_rejects_xml_size_over_limit(self):
        with zipfile.ZipFile(self.path, 'w', compression=zipfile.ZIP_DEFLATED) as out:
            out.writestr('Contents/section0.xml', '<root>' + 'x' * (20 * 1024 * 1024) + '</root>')
        with self.assertRaisesRegex(ValueError, 'HWPX_SECTION_XML_LIMIT_EXCEEDED'):
            extract(self.path)


if __name__ == '__main__':
    unittest.main()
