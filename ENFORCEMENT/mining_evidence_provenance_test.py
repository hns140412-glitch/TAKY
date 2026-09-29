#!/usr/bin/env python3
"""Evidence provenance must survive provider receipt ingestion without rewriting Index."""
import unittest
from mining_evidence_provenance import enrich_from_index
from mining_core import checkpoint, apply_external_receipts
from mining_run_orchestrator import orchestrate, advance_provider_batch


class EvidenceProvenanceTest(unittest.TestCase):
    def test_exact_duplicate_index_relation_groups_two_publication_surfaces(self):
        rows=[{"source_id":"HTML"},{"source_id":"CATALOG"}]
        relations=[{"type":"EXACT_DUPLICATE_OF","from":"HTML","to":"CATALOG"}]
        evidence=[{"source_id":"HTML","adapter":"PUBLIC_DATA","independent_support_count":2},
                  {"source_id":"CATALOG","adapter":"PUBLIC_DATA","independent_support_count":2}]
        out=enrich_from_index(evidence,rows,relations)
        self.assertEqual(out[0]["canonical_source_id"],out[1]["canonical_source_id"])
        self.assertFalse(out[0]["provenance_group_reviewed"])
        self.assertEqual(out[0]["provenance_match"],"INDEX_EXACT_SOURCE_ID")

    def test_near_duplicate_and_same_family_do_not_assert_canonical_identity(self):
        rows=[{"source_id":"A"},{"source_id":"B"}]
        for typ in ("NEAR_DUPLICATE_OF","SAME_FAMILY_AS","RELATED_TO"):
            out=enrich_from_index([{"source_id":"A"},{"source_id":"B"}],rows,
                                  [{"type":typ,"from":"A","to":"B"}])
            self.assertFalse(any(x.get("provenance_group_reviewed") for x in out))
            self.assertIsNone(out[0].get("canonical_source_id"))
            self.assertIsNone(out[1].get("canonical_source_id"))

    def test_provider_urls_and_unmatched_ids_do_not_fabricate_index_provenance(self):
        rows=[{"source_id":"A","locator":"https://example.gov/a"}]
        out=enrich_from_index([{"source_id":"UNKNOWN","source_url":"https://example.gov/a",
                                "source_identity":"https://example.gov/a","adapter":"WEB"}],rows,[])
        self.assertFalse(out[0]["provenance_group_reviewed"])
        self.assertEqual(out[0]["provenance_match"],"NO_EXACT_INDEX_ID")
        self.assertFalse(out[0].get("canonical_source_id"))

    def test_reviewed_distinct_index_groups_support_two_origins(self):
        rows=[{"source_id":"A","canonical_source_id":"PUBLISHER:A","source_group_reviewed":True},
              {"source_id":"B","canonical_source_id":"PUBLISHER:B","source_group_reviewed":True}]
        out=enrich_from_index([{"source_id":"A","adapter":"WEB"},{"source_id":"B","adapter":"WEB"}],rows,[])
        self.assertTrue(all(x["provenance_group_reviewed"] for x in out))
        self.assertEqual({x["canonical_source_id"] for x in out},{"PUBLISHER:A","PUBLISHER:B"})

    def test_actual_provider_adapter_receipts_preserve_index_group(self):
        rows=[{"source_id":"A"},{"source_id":"B"}]
        relations=[{"type":"EXACT_DUPLICATE_OF","from":"A","to":"B"}]
        task={"goal":"confirm published spec","task_family":"PUBLIC_DATA",
              "required_frontier_ids":["spec"]}
        frontier=[{"id":"spec","question":"official API metadata"}]
        original=checkpoint(task,frontier,[])
        receipts=[{"frontier_id":"spec","query":"official API metadata","adapter":"PUBLIC_DATA",
                   "results":[{"source_id":"A","url":"https://example.gov/info",
                               "source_class":"OFFICIAL","claim":"published",
                               "direct_support":True,"excerpt_ref":"API type","independent_support_count":2},
                              {"source_id":"B","url":"https://example.gov/catalog",
                               "source_class":"OFFICIAL","claim":"published",
                               "direct_support":True,"excerpt_ref":"API type","independent_support_count":2}]}]
        checked=apply_external_receipts(original,receipts,index_rows=rows,index_relations=relations)
        self.assertEqual(checked["external_ingest"]["accepted_evidence"],2)
        self.assertEqual(checked["frontier"][0]["independent_source_identity_count"],1)
        self.assertEqual(checked["frontier"][0]["best_evidence_score"],.925)
        self.assertEqual(checked["evidence"][0]["canonical_source_id"],
                         checked["evidence"][1]["canonical_source_id"])
        self.assertFalse(checked["evidence"][0]["provenance_group_reviewed"])

    def test_full_orchestrator_receipt_uses_index_duplicate_group_without_provider_patch(self):
        task={"task_family":"PUBLIC_DATA","goal":"verify published metadata",
              "unknown":["official API published format"],"max_research_depth":"D1"}
        index=[{"source_id":"HTML"},{"source_id":"CATALOG"}]
        rel=[{"type":"EXACT_DUPLICATE_OF","from":"HTML","to":"CATALOG"}]
        payload={"task":task,"memory":{},"index_rows":index,"index_relations":rel}
        requests=orchestrate(payload)["plan"]["planned_provider_requests"]
        self.assertTrue(requests)
        req=requests[0]
        result=advance_provider_batch(payload,{req["request_id"]:{
            "state":"SUCCESS","response":{"results":[
                {"source_id":"HTML","url":"https://example.gov/spec",
                 "source_class":"OFFICIAL","claim":"metadata","direct_support":True,
                 "excerpt_ref":"format listing","independent_support_count":2},
                {"source_id":"CATALOG","url":"https://example.gov/catalog",
                 "source_class":"OFFICIAL","claim":"metadata","direct_support":True,
                 "excerpt_ref":"format listing","independent_support_count":2}]}
        }})
        self.assertEqual(result["state"],"RECONCILED")
        evidence=result["checkpoint"]["evidence"]
        self.assertEqual(len(evidence),2)
        self.assertEqual(evidence[0]["canonical_source_id"],
                         evidence[1]["canonical_source_id"])
        self.assertEqual(result["checkpoint"]["frontier"][0]["independent_source_identity_count"],1)
        self.assertEqual(result["checkpoint"]["frontier"][0]["best_evidence_score"],.925)
        self.assertTrue(all(x["evidence_origin"]=="PROVIDER_RECEIPT" for x in evidence))

    def test_full_adapter_can_count_two_only_when_index_groups_reviewed(self):
        task={"task_family":"PUBLIC_DATA","goal":"verify independent notices",
              "required_frontier_ids":["notice"]}
        start=checkpoint(task,[{"id":"notice","question":"two notices"}],[])
        rows=[{"source_id":"OFF-A","canonical_source_id":"PUBLISHER:A",
               "source_group_reviewed":True},
              {"source_id":"OFF-B","canonical_source_id":"PUBLISHER:B",
               "source_group_reviewed":True}]
        receipt=[{"frontier_id":"notice","query":"two notices","adapter":"WEB",
                  "results":[{"source_id":"OFF-A","url":"https://a.example/notice",
                              "source_class":"PRIMARY","claim":"statement",
                              "direct_support":True,"independent_support_count":2},
                             {"source_id":"OFF-B","url":"https://b.example/notice",
                              "source_class":"PRIMARY","claim":"statement",
                              "direct_support":True,"independent_support_count":2}]}]
        result=apply_external_receipts(start,receipt,index_rows=rows)
        self.assertEqual(result["frontier"][0]["independent_source_identity_count"],2)
        self.assertEqual(result["frontier"][0]["best_evidence_score"],1.0)
        self.assertTrue(result["frontier"][0]["canonical_grouping_confirmed"])

    def test_provider_cannot_self_certify_reviewed_canonical_groups(self):
        task={"task_family":"PUBLIC_DATA","goal":"verify independent official claims",
              "required_frontier_ids":["proof"]}
        original=checkpoint(task,[{"id":"proof","question":"proof"}],[])
        receipt=[{"frontier_id":"proof","query":"proof","adapter":"WEB","results":[
            {"source_id":"P-A","url":"https://example.org/p",
             "canonical_source_id":"FAKE:PUBLISHER:A","source_group_reviewed":True,
             "source_class":"PRIMARY","claim":"X","direct_support":True,
             "independent_support_count":2},
            {"source_id":"P-B","url":"https://example.net/p",
             "canonical_source_id":"FAKE:PUBLISHER:B","source_group_reviewed":True,
             "source_class":"PRIMARY","claim":"X","direct_support":True,
             "independent_support_count":2}]}]
        result=apply_external_receipts(original,receipt)
        self.assertEqual(result["frontier"][0]["independent_source_identity_count"],1)
        self.assertFalse(result["frontier"][0]["canonical_grouping_confirmed"])
        self.assertTrue(all(not x["provenance_group_reviewed"] for x in result["evidence"]))
        self.assertTrue(all(not x.get("canonical_source_id") for x in result["evidence"]))

    def test_provider_success_with_separate_unreviewed_urls_not_independent(self):
        original=checkpoint({"goal":"review","task_family":"PUBLIC_DATA"},
                            [{"id":"spec","question":"published spec"}],[])
        receipts=[{"frontier_id":"spec","query":"published spec","adapter":"WEB",
                   "results":[{"source_id":"X","url":"https://example.org/a",
                               "source_class":"OFFICIAL","claim":"spec","direct_support":True,
                               "independent_support_count":2},
                              {"source_id":"Y","url":"https://example.net/b",
                               "source_class":"OFFICIAL","claim":"spec","direct_support":True,
                               "independent_support_count":2}]}]
        checked=apply_external_receipts(original,receipts)
        self.assertEqual(checked["frontier"][0]["independent_source_identity_count"],1)
        self.assertEqual(checked["frontier"][0]["best_evidence_score"],.925)


if __name__=="__main__":
    unittest.main()
