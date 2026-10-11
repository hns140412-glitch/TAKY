#!/usr/bin/env python3
import unittest
from ai_execution_guard import validate_ai_execution
from ai_reference_projection import build_projection, project_record
from reference_acquisition_adapter import validate_public_url, AcquisitionError

class AILearningQ2LocalExperimentTest(unittest.TestCase):
    def test_separate_guards_validate_before_combination(self):
        adoption={
          "ai_tool_or_connector_adoption_planned":True,
          "ai_adoption_assessment":{
            "capability_gap":"gap","overlap_checked":True,"cost_checked":True,
            "security_checked":True,"upstream_identity_verified":True,
          }}
        cost={"ai_autonomous_cost_exposure":True,"ai_cost_guard":{
          "cost_ceiling":1,"iteration_limit":2,"stop_condition":"stop",
          "approval_required_before_exceeding":True}}
        self.assertEqual(validate_ai_execution(adoption),[])
        self.assertEqual(validate_ai_execution(cost),[])
        combined={**adoption,**cost}
        self.assertEqual(validate_ai_execution(combined),[])

    def test_distinct_reference_sets_do_not_merge_by_topic(self):
        a=project_record({"source_id":"A","title":"Claude agent plugin workflow","source_family":"AI_TOOL"})
        b=project_record({"source_id":"B","title":"Claude agent plugin workflow","source_family":"AI_TOOL"})
        p=build_projection([a,b])
        self.assertEqual(p["source_count"],2)
        self.assertEqual({x["source_id"] for x in p["records"]},{"A","B"})

    def test_public_acquisition_adapter_rejects_private_or_authenticated_paths(self):
        for url in [
            "file:///tmp/secret.txt",
            "http://127.0.0.1/private",
            "https://user:pass@example.com/resource",
        ]:
            with self.assertRaises(AcquisitionError):
                validate_public_url(url)

if __name__=="__main__":
    unittest.main()
