#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from learning_mining_closed_loop import run_reference_gap

GAP={
    "gap_id":"G-REF-1",
    "owner":"LEARNING_ENGINE_CORE",
    "gap_type":"REFERENCE_EVIDENCE_REQUIRED",
    "priority":"MEDIUM",
    "scope":{"member_id":"A","subject":"science","concept_skill_target":"climate"},
    "query_terms":["science","climate","official"],
    "existing_source_refs":[],
    "requested_capability":"EXTERNAL_REFERENCE_EVIDENCE",
    "acceptable_source_families":["OFFICIAL_STANDARDS"],
    "acceptable_authority_classes":["OFFICIAL"],
    "required_provenance":["OFFICIAL_SOURCE_REF"],
    "index_check_required":True,
    "resolution_path":"INDEX_THEN_MINING_IF_INSUFFICIENT",
    "mining_request_authorized":False
}

class TestClosedLoop(unittest.TestCase):
    def test_reference_gap_calls_provider_then_index_owner_then_learning(self):
        with tempfile.TemporaryDirectory() as td:
            index=Path(td)/"index.json"
            index.write_text(json.dumps({"sources":[]}),encoding="utf-8")
            calls={"provider":0,"index":0,"learning":0}

            def provider(req):
                calls["provider"]+=1
                return {"results":[{
                    "source_id":"SRC-CLIMATE-1",
                    "url":"https://example.test/climate",
                    "title":"science climate official standard",
                    "source_class":"OFFICIAL",
                    "summary":"official climate reference",
                    "direct_support":True
                }]}

            def index_owner(receipts,route,path):
                calls["index"]+=1
                self.assertTrue(receipts)
                path.write_text(json.dumps({"sources":[{
                    "source_id":"SRC-CLIMATE-1",
                    "title":"science climate official standard",
                    "source_family":"OFFICIAL_STANDARDS",
                    "source_type":"OFFICIAL_CURRICULUM",
                    "authority_class":"OFFICIAL",
                    "keywords":["science","climate","official"],
                    "provenance":["OFFICIAL_SOURCE_REF"]
                }]}),encoding="utf-8")
                return {"pass":True,"indexed_source_ids":["SRC-CLIMATE-1"]}

            def learning_requery(route,rows):
                calls["learning"]+=1
                return {"ok":True,"source_ids":[x.get("source_id") for x in rows]}

            out=run_reference_gap(
                GAP,index_path=index,
                provider_executors={"WEB":provider,"PUBLIC_DATA":provider,"GITHUB":provider},
                index_owner_apply=index_owner,
                learning_requery=learning_requery,
            )
            self.assertTrue(out["pass"])
            self.assertEqual(out["state"],"CLOSED_LOOP_COMPLETE")
            self.assertGreaterEqual(calls["provider"],1)
            self.assertEqual(calls["index"],1)
            self.assertEqual(calls["learning"],1)
            self.assertEqual(out["post_index_route"]["decision"],"INDEX_REQUERY")

    def test_existing_index_skips_mining(self):
        with tempfile.TemporaryDirectory() as td:
            index=Path(td)/"index.json"
            index.write_text(json.dumps({"sources":[{
                "source_id":"SRC-EXISTING","title":"science climate official",
                "source_family":"OFFICIAL_STANDARDS","authority_class":"OFFICIAL",
                "keywords":["science","climate","official"],
                "provenance":["OFFICIAL_SOURCE_REF"]
            }]}),encoding="utf-8")
            calls={"learning":0}
            def learning(route,rows):
                calls["learning"]+=1
                return {"ok":True}
            out=run_reference_gap(
                GAP,index_path=index,provider_executors={},
                index_owner_apply=lambda *args:{"pass":True},
                learning_requery=learning,
            )
            self.assertTrue(out["pass"])
            self.assertEqual(out["state"],"LEARNING_REQUERY_COMPLETE")
            self.assertEqual(calls["learning"],1)

if __name__=="__main__":
    unittest.main()
