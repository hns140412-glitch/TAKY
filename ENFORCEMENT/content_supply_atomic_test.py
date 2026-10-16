import os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from content_supply_atomic import publish_bytes

class AtomicPublishTests(unittest.TestCase):
    def test_publish_and_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"candidate.json"
            self.assertEqual(publish_bytes(p,b'{"ok":true}'),"PUBLISHED")
            self.assertEqual(publish_bytes(p,b'{"ok":true}'),"REUSED")
            self.assertEqual(p.read_bytes(),b'{"ok":true}')
            self.assertFalse(any(x.name.startswith('.taky-supply-') for x in Path(d).iterdir()))
    def test_conflict_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"receipt.json"
            publish_bytes(p,b'old')
            with self.assertRaises(FileExistsError):publish_bytes(p,b'new')
            self.assertEqual(p.read_bytes(),b'old')
    def test_failed_link_creates_no_partial_target(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"receipt.json"
            with patch('content_supply_atomic.os.link',side_effect=OSError('failed')):
                with self.assertRaises(OSError):publish_bytes(p,b'payload')
            self.assertFalse(p.exists())
            self.assertEqual(list(Path(d).iterdir()),[])
if __name__=="__main__":unittest.main()
