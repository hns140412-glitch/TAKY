#!/usr/bin/env python3
import unittest
from mining_claim_relations import relation,analyze
class T(unittest.TestCase):
 def test_same_claim_supports(self):
  a={"subject":"height","predicate":"limit","scope":"zone-a","value":"20m"}; b={**a,"value":"20m"}
  self.assertEqual(relation(a,b),"SUPPORTS")
 def test_opposite_polarity_conflicts(self):
  a={"subject":"use","predicate":"permitted","scope":"zone-a","polarity":"ALLOW"}; b={**a,"polarity":"DENY"}
  self.assertEqual(relation(a,b),"CONTRADICTS")
 def test_different_scope_qualifies_not_conflicts(self):
  a={"subject":"height","predicate":"limit","scope":"zone-a","value":"20m"}; b={"subject":"height","predicate":"limit","scope":"zone-b","value":"30m"}
  self.assertEqual(relation(a,b),"QUALIFIES"); self.assertFalse(analyze([a,b])["conflict"])
 def test_different_subject_unrelated(self):
  self.assertEqual(relation({"subject":"height","predicate":"limit"},{"subject":"parking","predicate":"count"}),"UNRELATED")
 def test_explicit_adapter_relation_wins(self):
  a={"evidence_id":"a","relation_to":{"b":"CONTRADICTS"}}; b={"evidence_id":"b"}
  self.assertEqual(relation(a,b),"CONTRADICTS")
if __name__=="__main__":unittest.main()
