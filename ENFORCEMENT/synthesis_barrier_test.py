#!/usr/bin/env python3
import unittest
from pathlib import Path

import runtime_orchestrator as ro


class SynthesisBarrierTest(unittest.TestCase):
    def test_runtime_contains_synthesis_barrier_guards(self):
        source = Path(ro.__file__).read_text(encoding="utf-8")
        self.assertIn("SYNTHESIS_EXPECTED_CHILDREN_INVALID", source)
        self.assertIn("SYNTHESIS_CHILD_RESULT_MALFORMED", source)
        self.assertIn("SYNTHESIS_CHILD_RESULTS_INCOMPLETE", source)
        self.assertIn("SYNTHESIS_UNEXPECTED_CHILD_RESULT", source)
        self.assertIn('"synthesis_barrier": synthesis_barrier_result', source)

    def test_structured_result_is_required(self):
        source = Path(ro.__file__).read_text(encoding="utf-8")
        self.assertIn('status != "COMPLETED"', source)
        self.assertIn('not isinstance(structured, dict)', source)
        self.assertIn('"synthesis_ready"', source)


if __name__ == "__main__":
    unittest.main()
