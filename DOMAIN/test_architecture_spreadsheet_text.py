import tempfile
import unittest
import zipfile
from pathlib import Path
from architecture_spreadsheet_text import extract


class SpreadsheetTextTest(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.path = Path(t.name) / 'sample.xlsm'

    def test_shared_and_inline_strings_and_macro_ignored(self):
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr('xl/sharedStrings.xml', '<sst><si><t>법규</t></si></sst>')
            z.writestr('xl/worksheets/sheet1.xml',
                '<worksheet><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c>'
                '<c r="B1" t="inlineStr"><is><t>검토</t></is></c></row></sheetData></worksheet>')
            z.writestr('xl/vbaProject.bin', b'NEVER_EXECUTE')
        result = extract(self.path)
        self.assertIn('A1=법규', result['text'])
        self.assertIn('B1=검토', result['text'])
        self.assertFalse(result['macros_executed'])

    def test_formula_cache_is_not_accepted_as_recalculated(self):
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr('xl/worksheets/sheet1.xml',
                '<worksheet><sheetData><row r="2"><c r="C2"><f>1+1</f><v>2</v></c>'
                '</row></sheetData></worksheet>')
        result = extract(self.path)
        self.assertIn('FORMULA_CACHE_NOT_RECALCULATED', result['warnings'])
        self.assertFalse(result['formula_recalculated'])

    def test_no_sheet_rejected(self):
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr('xl/vbaProject.bin', b'macro')
        with self.assertRaisesRegex(ValueError, 'OOXML_SHEET_COUNT_INVALID'):
            extract(self.path)


if __name__ == '__main__':
    unittest.main()
