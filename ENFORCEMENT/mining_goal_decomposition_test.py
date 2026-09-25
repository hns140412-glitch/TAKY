#!/usr/bin/env python3
import unittest
from mining_goal_decomposition import decompose,apply_to_task

class T(unittest.TestCase):
 def test_explicit_requirements_preserved(self):
  d=decompose({"goal":"compare options","requirements":["price","availability"],"critical_requirements":["legal constraint"],"derive_generic_dimensions":False})
  qs={x["question"] for x in d["frontier"]}
  self.assertIn("price",qs); self.assertIn("availability",qs); self.assertIn("legal constraint",qs)

 def test_generic_scaffold_not_domain_fact(self):
  d=decompose({"goal":"build feature"})
  self.assertTrue(any(x["origin"]=="GENERIC_SCAFFOLD" for x in d["frontier"]))
  self.assertTrue(d["guards"]["generic_dimensions_are_not_domain_facts"])

 def test_alternatives_only_when_required(self):
  a=decompose({"goal":"choose approach","alternatives_required":False})
  b=decompose({"goal":"choose approach","alternatives_required":True})
  self.assertEqual(a["alternative_frontier_ids"],[])
  self.assertTrue(b["alternative_frontier_ids"])

 def test_existing_ids_not_overwritten(self):
  t=apply_to_task({"goal":"x","foundation_frontier_ids":["manual_f"]})
  self.assertEqual(t["foundation_frontier_ids"],["manual_f"])
  self.assertIn("goal_decomposition",t)

if __name__=="__main__":unittest.main()
