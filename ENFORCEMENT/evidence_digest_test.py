#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from evidence_digest import canonical_json_sha256

class EvidenceDigestTest(unittest.TestCase):
    def test_line_endings_and_whitespace_do_not_change_digest(self):
        with tempfile.TemporaryDirectory(prefix="taky-digest-") as td:
            a=Path(td)/"a.json"
            b=Path(td)/"b.json"
            a.write_bytes(b'{\n  "b": 2,\n  "a": 1\n}\n')
            b.write_bytes(b'{\r\n"a":1,\r\n"b":2\r\n}\r\n')
            self.assertEqual(canonical_json_sha256(a),canonical_json_sha256(b))

if __name__=="__main__":
    unittest.main()
