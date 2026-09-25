#!/usr/bin/env python3
import unittest
from mining_live_execution_loop import next_requests_after_batch

class T(unittest.TestCase):
 def test_success_frontier_does_not_fallback(self):
  req=[{"frontier_id":"f","request_id":"a"}]
  batch={"results":[{"frontier_id":"f","state":"SUCCESS","receipt":{"results":[{"x":1}]}}],"failed_request_ids":[],"empty_request_ids":[]}
  self.assertEqual(next_requests_after_batch(req,batch),[])

 def test_failed_frontier_requests_next_provider(self):
  req=[{"frontier_id":"f","request_id":"a"}]
  batch={"results":[{"frontier_id":"f","state":"FAILED","receipt":{"results":[]}}],"failed_request_ids":["a"],"empty_request_ids":[]}
  n=next_requests_after_batch(req,batch)
  self.assertEqual(n[0]["action"],"TRY_NEXT_PROVIDER")

 def test_empty_frontier_requests_next_provider(self):
  req=[{"frontier_id":"f","request_id":"a"}]
  batch={"results":[{"frontier_id":"f","state":"EMPTY","receipt":{"results":[]}}],"failed_request_ids":[],"empty_request_ids":["a"]}
  self.assertEqual(next_requests_after_batch(req,batch)[0]["frontier_id"],"f")

if __name__=="__main__": unittest.main()
