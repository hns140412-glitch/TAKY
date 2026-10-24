#!/usr/bin/env python3
"""Independent deterministic acceptance tests for Claude's MCP resource sampler."""
import json
import unittest
from unittest.mock import patch
import TAKY_ORCHESTRATION_ADVANCE as target

def proc(name="claude",cpu=1.0,ws=64*1048576,start=10):
    return {"name":name,"cpu":cpu,"ws":ws,"start":start}

class TelemetryTests(unittest.TestCase):
    def observe(self, first, second):
        with patch.object(target,"sample_processes",side_effect=[first,second]),\
             patch.object(target.time,"perf_counter",side_effect=[0.0,0.1,1.1,1.2]),\
             patch.object(target.time,"sleep") as sleeping:
            result=target.run_process_telemetry(timeout=10,interval=1.0)
        sleeping.assert_called_once_with(1.0)
        return result

    def test_steady_process_cpu_delta_and_memory_readout(self):
        r=self.observe({100:proc(cpu=3.0,ws=65*1048576)},
                       {100:proc(cpu=3.2,ws=68*1048576)})
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(len(r["processes"]),1)
        item=r["processes"][0]
        self.assertEqual(item["identity_check"],"START_TIME_MATCHED")
        self.assertEqual(item["cpu_seconds_delta"],0.2)
        self.assertEqual(item["resident_mb"],68.0)
        self.assertFalse(r["cpu_limits_verified"])
        self.assertEqual(r["cpu_budget"],"UNSET_UNVERIFIED")
        self.assertFalse(r["protocol_handshake_verified"])
        self.assertFalse(r["cpu_threshold_applied"])
        self.assertFalse(r["command_lines_collected"])

    def test_pid_reuse_not_misread_as_cpu_delta(self):
        r=self.observe({100:proc(start=12,cpu=2.0)},
                       {100:proc(start=13,cpu=3.0)})
        self.assertEqual(r["churn"]["pid_reuse_excluded"],1)
        self.assertEqual(r["processes"],[])

    def test_unknown_start_time_must_not_be_treated_as_verified_cpu_delta(self):
        r=self.observe({100:proc(start=None,cpu=2.0)},
                       {100:proc(start=None,cpu=12.0)})
        self.assertEqual(r["churn"]["start_time_unverified"],1)
        self.assertEqual(r["processes"][0]["identity_check"],"START_TIME_UNAVAILABLE")
        self.assertIsNone(r["processes"][0]["cpu_seconds_delta"])
        self.assertIsNone(r["processes"][0]["cpu_seconds_per_wall_second"])

    def test_live_observation_scope_expires_without_invalidating_other_work(self):
        from datetime import datetime, timezone, timedelta
        self.assertEqual(target.telemetry_hour_bucket(
            datetime(2026,10,24,13,50,tzinfo=timezone(timedelta(hours=9)))),
            "2026-10-24T04")
        board={"tasks":[{"id":"MCP-002","status":"IMPLEMENTING",
                        "title":"Verify CPU and memory sources"}]}
        with patch.object(target,"sha",return_value="a"*64), patch.object(
                target,"telemetry_hour_bucket",side_effect=[
                    "2026-10-24T04","2026-10-24T05"]):
            old,first=target.evidence_signature(board,"MCP-002")
            new,second=target.evidence_signature(board,"MCP-002")
        self.assertNotEqual(first,second)
        self.assertNotEqual(old["telemetry_observation_utc_hour"],
                            new["telemetry_observation_utc_hour"])

    def test_unavailable_process_probe_is_not_fake_success(self):
        with patch.object(target,"sample_processes",side_effect=ValueError("unavailable")),\
             patch.object(target.time,"perf_counter",return_value=1):
            r=target.run_process_telemetry(timeout=10)
        self.assertEqual(r["status"],"HOLD")
        self.assertFalse(r["cpu_limits_verified"])

if __name__=="__main__":
    unittest.main()
