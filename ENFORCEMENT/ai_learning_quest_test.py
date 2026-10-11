#!/usr/bin/env python3
import json, unittest
from pathlib import Path
from ai_learning_quest import build

class AILearningQuestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        cls.p=json.loads((root/"CURRENT/DATA/AI_LEARNING_PROJECTION.json").read_text(encoding="utf-8"))
        cls.q=build(cls.p)

    def test_all_56_classified(self):
        self.assertEqual(self.q["source_learning_count"],56)
        self.assertTrue(self.q["all_classified"])
        self.assertNotIn("UNCLASSIFIED",self.q["states"])

    def test_first_quest_closes_only_tested_adoptions(self):
        self.assertEqual(self.q["states"]["ADOPTED_TESTED_NEW_GUARD"],14)
        self.assertEqual(self.q["states"]["ADOPTED_TESTED_EXISTING"],2)
        q1=next(x for x in self.q["quests"] if x["quest_id"]=="AI-Q1-DETERMINISTIC-GUARDS")
        self.assertEqual(q1["member_count"],16)
        self.assertEqual(q1["state"],"COMPLETE_LOCAL")

    def test_remaining_are_not_auto_promoted(self):
        self.assertEqual(self.q["states"]["ADOPTED_TESTED_Q2"],3)
        self.assertEqual(self.q["states"]["EXPERIMENT_READY"],14)
        self.assertEqual(self.q["states"]["DOMAIN_HANDOFF_READY"],18)
        self.assertEqual(self.q["states"]["REFERENCE_ONLY_VERIFY"],5)

if __name__=="__main__":
    unittest.main()
