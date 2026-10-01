#!/usr/bin/env python3
import unittest
from mining_provider_execution_loop import choose_providers,build_requests

class T(unittest.TestCase):
 def test_implementation_prefers_github(self):
  p=choose_providers({"preferred_source_classes":["IMPLEMENTATION"]})
  self.assertEqual(p[0],"GITHUB")

 def test_official_prefers_public_data(self):
  p=choose_providers({"prefer":["OFFICIAL"]})
  self.assertEqual(p[0],"PUBLIC_DATA")

 def test_build_requests_bounded(self):
  reqs=build_requests([{"frontier_id":"f","query":"q","prefer":["OFFICIAL"]}],max_providers_per_query=2)
  self.assertEqual(len(reqs),2)
  self.assertEqual(reqs[0]["frontier_id"],"f")

if __name__=="__main__": unittest.main()
