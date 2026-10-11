#!/usr/bin/env python3
import time, unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from reference_batch_acquisition import acquire_batch

class ReferenceBatchAcquisitionTest(unittest.TestCase):
    def test_one_failure_does_not_block_others(self):
        def fake(url, **kwargs):
            if url.endswith("/bad"):
                raise RuntimeError("boom")
            return {"pass": True, "source_url": url}
        with TemporaryDirectory() as td:
            r=acquire_batch(
              [{"source_id":"A","url":"https://example.com/a"},
               {"source_id":"B","url":"https://example.com/bad"},
               {"source_id":"C","url":"https://example.com/c"}],
              destination_dir=Path(td), acquire_func=fake)
        self.assertTrue(r["pass"])
        self.assertEqual(r["terminal_count"],3)
        self.assertEqual(r["results"][1]["result"]["detected"],["REFERENCE_BATCH_ITEM_EXCEPTION"])

    def test_parallelism_is_bounded_and_effective(self):
        def fake(url, **kwargs):
            time.sleep(0.05)
            return {"pass": True, "source_url": url}
        items=[{"source_id":str(i),"url":f"https://example.com/{i}"} for i in range(8)]
        with TemporaryDirectory() as td:
            start=time.perf_counter()
            baseline=acquire_batch(items,destination_dir=Path(td),workers=1,acquire_func=fake)
            baseline_elapsed=time.perf_counter()-start
            start=time.perf_counter()
            r=acquire_batch(items,destination_dir=Path(td),workers=4,acquire_func=fake)
            elapsed=time.perf_counter()-start
        self.assertTrue(baseline["pass"])
        self.assertTrue(r["pass"])
        self.assertEqual(r["terminal_count"],8)
        # Compare against the same runtime environment instead of a brittle wall-clock constant.
        self.assertLess(elapsed,baseline_elapsed*0.8)

    def test_worker_limit_fails_closed(self):
        with TemporaryDirectory() as td:
            r=acquire_batch([],destination_dir=Path(td),workers=99)
        self.assertFalse(r["pass"])
        self.assertIn("REFERENCE_BATCH_WORKER_LIMIT_INVALID",r["detected"])

if __name__=="__main__":
    unittest.main()
