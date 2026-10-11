import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mobile_design_authority_candidate_validator import validate, REGISTRY

class MobileDesignAuthorityCandidateValidatorTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_candidate_passes(self):
        self.assertEqual(validate(self.data), [])

    def test_external_reference_cannot_be_authority(self):
        d = json.loads(json.dumps(self.data))
        d["external_reference_role"] = "AUTHORITY"
        self.assertTrue(any("external references" in x for x in validate(d)))

    def test_authority_order_is_locked(self):
        d = json.loads(json.dumps(self.data))
        d["authority_order"] = list(reversed(d["authority_order"]))
        self.assertTrue(any("authority order" in x for x in validate(d)))

    def test_only_foundation_has_dedicated_tablet_ui(self):
        d = json.loads(json.dumps(self.data))
        d["device_strategy"]["dedicated_tablet_ui"].append("Hide-Seek")
        self.assertTrue(any("Play Camp only" in x for x in validate(d)))

    def test_play_camp_tablet_is_primary_separate_ui(self):
        d = json.loads(json.dumps(self.data))
        d["apps"]["Play-Camp"]["tablet_ui_authority"] = "RESPONSIVE_MOBILE_DERIVATIVE"
        self.assertTrue(any("tablet-primary separate-UI" in x for x in validate(d)))

    def test_play_camp_base_asset_cannot_be_replaced_by_regeneration(self):
        d = json.loads(json.dumps(self.data))
        d["apps"]["Play-Camp"]["crew_binding_status"] = "REGENERATE_ALL_CREW"
        self.assertTrue(any("base asset must stay inherited" in x for x in validate(d)))

if __name__ == "__main__":
    unittest.main()
