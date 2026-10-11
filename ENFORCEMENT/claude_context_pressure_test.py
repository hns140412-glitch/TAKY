import tempfile
import unittest
from pathlib import Path

from claude_context_pressure import classify_context_pct, guidance_for, read_fresh_state, write_state


class ClaudeContextPressureTest(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(classify_context_pct(39.9), "NORMAL")
        self.assertEqual(classify_context_pct(40), "LIGHT")
        self.assertEqual(classify_context_pct(49.9), "LIGHT")
        self.assertEqual(classify_context_pct(50), "COMPACT")

    def test_guidance_is_shepherding_not_terminal_block(self):
        self.assertIn("CURRENT/owner", guidance_for("LIGHT", 42))
        self.assertIn("Do not assume native auto-compact", guidance_for("COMPACT", 51))
        self.assertIn("real PreCompact/compact-resume", guidance_for("COMPACT", 51))
        self.assertNotIn("deny", guidance_for("COMPACT", 51).lower())

    def test_round_trip_state(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "state.json"
            write_state(44, path=p)
            state = read_fresh_state(path=p)
            self.assertEqual(state["mode"], "LIGHT")
            self.assertEqual(state["used_percentage"], 44.0)


if __name__ == "__main__":
    unittest.main()
