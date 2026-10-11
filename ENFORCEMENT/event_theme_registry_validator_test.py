import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_theme_registry_validator import validate, REGISTRY

class EventThemeRegistryValidatorTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_candidate_registry_passes(self):
        self.assertEqual(validate(self.data), [])

    def test_memorial_cannot_be_celebration(self):
        mutated = json.loads(json.dumps(self.data))
        for e in mutated["events"]:
            if e["id"] == "memorial_day":
                e["tone"] = "CELEBRATION"
        self.assertTrue(any("Memorial Day" in x for x in validate(mutated)))

    def test_layout_must_remain_immutable(self):
        mutated = json.loads(json.dumps(self.data))
        mutated["immutable"].remove("layout")
        self.assertTrue(any("immutable" in x for x in validate(mutated)))

if __name__ == "__main__":
    unittest.main()
