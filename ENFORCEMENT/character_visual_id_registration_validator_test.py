import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from character_visual_id_registration_validator import validate_template, TEMPLATE

class CharacterVisualIdRegistrationTemplateTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_template_passes(self):
        self.assertEqual(validate_template(self.data), [])

    def test_app_cannot_reinterpret_identity(self):
        d = json.loads(json.dumps(self.data))
        d["gate"]["app_may_reinterpret_identity"] = True
        self.assertTrue(any("must not reinterpret" in e for e in validate_template(d)))

    def test_expressions_remain_variable(self):
        d = json.loads(json.dumps(self.data))
        del d["variable_derivatives"]["expression_states"]
        self.assertTrue(any("expression states" in e for e in validate_template(d)))

    def test_registration_cannot_generate_character_sheet_art(self):
        d = json.loads(json.dumps(self.data))
        d["gate"]["registration_image_generation_forbidden"] = False
        d["gate"]["generated_reference_sheet_is_asset"] = True
        errs = validate_template(d)
        self.assertTrue(any("image generation" in e for e in errs))
        self.assertTrue(any("reference sheet" in e for e in errs))

if __name__ == "__main__":
    unittest.main()
