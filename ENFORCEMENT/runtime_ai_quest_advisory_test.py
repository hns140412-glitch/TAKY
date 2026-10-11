import json
import unittest
from pathlib import Path

from runtime_orchestrator import run

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"ENFORCEMENT"/"fixtures"/"runtime_orchestrator_pass.json"

class RuntimeAIQuestAdvisoryTest(unittest.TestCase):
    def test_open_quest_is_advisory_and_does_not_block(self):
        record=json.loads(FIXTURE.read_text(encoding="utf-8"))
        record["multiple_surfaces_candidate"]=True
        result=run(record,ROOT,None)
        advisory=result.get("ai_open_quest_advisory") or {}
        self.assertTrue(advisory.get("advisory"))
        ids={x["learning_id"] for x in advisory.get("selected") or []}
        self.assertIn("AI-LRN-SURFACE-SELECTION-BY-JOB-DIMENSION",ids)
        self.assertNotIn("AI-LRN-DESIGN-PIPELINE-NOT-PROMPT-ONLY",ids)

    def test_no_match_stays_empty(self):
        record=json.loads(FIXTURE.read_text(encoding="utf-8"))
        result=run(record,ROOT,None)
        advisory=result.get("ai_open_quest_advisory") or {}
        self.assertEqual(advisory.get("selected_count"),0)

if __name__=="__main__":
    unittest.main()
