#!/usr/bin/env python3
"""Quota+governance integration fixtures: no AI calls or network."""
import unittest
from TAKY_USAGE_BOARD import governed_route_dry_run


def usage():
    return {"checkedAt": "2026-10-15T14:00+09:00", "providers": [
        {"name": name, "fresh": True, "observedAt": "2026-10-15T13:59+09:00",
         "fiveHour": {"usedPercent": 10}, "week": {"usedPercent": 20}}
        for name in ("Codex CLI", "Claude Code")
    ]}


class CombinedRoutingTest(unittest.TestCase):
    def test_auto_recommends_fallback_only_if_governance_allows(self):
        def rule(provider, repo):
            if provider == "Codex":
                return {"status": "HOLD", "reason": "ROUTE_GATE_BLOCKED"}
            return {"status": "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES"}
        result = governed_route_dry_run(usage(), "review", "small", 1,
                                        health_reader=rule)
        self.assertEqual(result["recommended"], "Claude Code")
        self.assertEqual(result["status"], "READY_FOR_SEPARATE_AUTHORIZATION")
        self.assertEqual(result["modelCalls"], 0) if "modelCalls" in result else self.assertEqual(result["inferenceCalls"], 0)

    def test_both_quota_safe_but_governed_hold_is_not_ready(self):
        def hold(provider, repo):
            return {"status": "HOLD", "reason": "UNRESOLVED_GOVERNED_EXECUTION"}
        result = governed_route_dry_run(usage(), "review", "small", 1,
                                        health_reader=hold)
        self.assertIsNone(result["recommended"])
        self.assertEqual(result["status"], "HOLD_NO_QUOTA_AND_GOVERNANCE_SAFE_ROUTE")
        self.assertTrue(all(x["risk"] == "SAFE" for x in result["candidates"]))
        self.assertTrue(all(x["governance"]["status"] == "HOLD" for x in result["candidates"]))

    def test_local_validation_never_reads_governance_or_models(self):
        def must_not_be_called(provider, repo):
            raise AssertionError("Local route should never read external governance")
        result = governed_route_dry_run(usage(), "validation", "small", 1,
                                        health_reader=must_not_be_called)
        self.assertEqual(result["recommended"], "LOCAL_DETERMINISTIC")
        self.assertEqual(result["inferenceCalls"], 0)
        self.assertEqual(result["paidApiCalls"], 0)


if __name__ == "__main__":
    unittest.main()
