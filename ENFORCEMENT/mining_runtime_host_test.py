#!/usr/bin/env python3
import unittest
from mining_runtime_host import execute_provider_requests

class TestMiningRuntimeHost(unittest.TestCase):
    def test_registered_executor_is_actually_invoked(self):
        seen=[]
        def web(req):
            seen.append(req["request_id"])
            return {"results":[{"id":"S1","title":"official source","url":"https://example.test/s1"}]}
        req={"schema":"TAKY_MINING_PROVIDER_REQUEST_V1","request_id":"R1","provider":"WEB","frontier_id":"F1","query":"q"}
        out=execute_provider_requests([req],{"WEB":web})
        self.assertTrue(out["pass"])
        self.assertEqual(seen,["R1"])
        self.assertEqual(out["runtime_results"]["R1"]["state"],"SUCCESS")
        self.assertTrue(out["guards"]["host_invokes_provider_adapter"])

    def test_missing_executor_fails_closed(self):
        req={"request_id":"R2","provider":"GITHUB","frontier_id":"F2","query":"q"}
        out=execute_provider_requests([req],{})
        self.assertFalse(out["pass"])
        self.assertEqual(out["runtime_results"]["R2"]["error"],"PROVIDER_EXECUTOR_NOT_BOUND")

if __name__=="__main__":
    unittest.main()
