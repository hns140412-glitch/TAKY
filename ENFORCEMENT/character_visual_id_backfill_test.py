import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from character_visual_id_backfill import ROOT, REGISTRY, validate

class CharacterVisualIdBackfillTest(unittest.TestCase):
    def test_backfill_registry_and_cards_pass(self):
        self.assertEqual(validate(), [])

    def test_id24_is_vivi_not_nova(self):
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        v = next(x for x in data["roster"] if x["visual_id"] == "24")
        self.assertEqual(v["display_name_en"], "VIVI")
        self.assertEqual(v["display_name_ko"], "비비")
        self.assertIn("NOVA", v["forbidden_aliases"])

    def test_all_cards_inherit_existing_base_asset(self):
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for item in data["roster"]:
            card = json.loads((ROOT / item["card_path"]).read_text(encoding="utf-8"))
            self.assertEqual(card["runtime"]["base_asset_status"], "INHERITED_EXISTS")
            self.assertEqual(card["authority"]["base_asset_policy"], "INHERIT_EXISTING_APPROVED_ASSET__DO_NOT_REGENERATE")

    def test_all_turnarounds_are_already_bound_and_closed(self):
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertTrue(data["invariants"]["turnaround_24_complete"])
        self.assertEqual(data["invariants"]["turnaround_binding_status"], "CLOSED_APPROVED_BOUND")
        for item in data["roster"]:
            card = json.loads((ROOT / item["card_path"]).read_text(encoding="utf-8"))
            self.assertEqual(card["turnaround_views"]["status"], "APPROVED_BOUND")
            self.assertEqual(card["turnaround_views"]["detail"], "CLOSED__DO_NOT_REBUILD_OR_REBIND")

if __name__ == "__main__":
    unittest.main()
