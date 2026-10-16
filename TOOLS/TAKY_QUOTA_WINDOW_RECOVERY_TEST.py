"""Read-only quota window loss and recovery simulation, never queries providers."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import time
import unittest

from TAKY_USAGE_BOARD import claude, governed_route_dry_run


class QuotaRecoveryTests(unittest.TestCase):
    def test_expired_five_hour_gate_holds_until_authenticated_refresh(self):
        now = time.time()
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            status = root / "status.json"
            status.write_text("{}", encoding="utf-8")
            cache = root / "usage.json"
            cache.write_text(json.dumps({
                "cachedUsageUtilization": {
                    "fetchedAtMs": int((now - 90)*1000),
                    "utilization": {
                        "five_hour": {"utilization": 63,
                            "resets_at": dt.datetime.fromtimestamp(
                                now - 30, dt.timezone.utc).isoformat()},
                        "seven_day": {"utilization": 5,
                            "resets_at": dt.datetime.fromtimestamp(
                                now + 86400, dt.timezone.utc).isoformat()},
                    }
                }
            }), encoding="utf-8")
            new_data = root / "oauth.json"
            old = claude(path=status, usage_cache=cache, oauth_snapshot=new_data, now=now)
            self.assertIsNone(old["fiveHour"]["usedPercent"])
            self.assertEqual(old["week"]["usedPercent"], 5)
            self.assertTrue(old["fresh"])
            def health(provider, repo):
                return {"status": ("READY_FOR_EXISTING_COST_AND_APPROVAL_GATES"
                                   if provider == "Claude" else "HOLD"),
                        "signedStateIntegrity": "PASS"}
            base = {"checkedAt": "fixture",
                    "providers": [
                        old, {"name": "Codex CLI", "fresh": True,
                              "fiveHour": {"usedPercent": 46},
                              "week": {"usedPercent": 7}}
                    ]}
            before = governed_route_dry_run(
                base, "review", "small", repo="fixture", health_reader=health)
            self.assertEqual(before["status"], "HOLD_NO_QUOTA_AND_GOVERNANCE_SAFE_ROUTE")
            old_candidate = next(c for c in before["candidates"]
                                 if c["provider"] == "Claude Code")
            self.assertEqual(old_candidate["quotaGateReason"], "QUOTA_WINDOW_UNOBSERVED")
            self.assertEqual(old_candidate["missingQuotaWindows"], ["fiveHour"])

            new_data.write_text(json.dumps({
                "source": "claude_authenticated_usage",
                "capturedAt": dt.datetime.fromtimestamp(
                    now - 15, dt.timezone.utc).isoformat(),
                "five_hour": {"utilization": 0, "resets_at": None},
                "seven_day": {"utilization": 5,
                    "resets_at": dt.datetime.fromtimestamp(
                        now + 86400, dt.timezone.utc).isoformat()}
            }), encoding="utf-8")
            updated = claude(path=status, usage_cache=cache,
                             oauth_snapshot=new_data, now=now)
            self.assertEqual(updated["fiveHour"]["usedPercent"], 0)
            self.assertEqual(updated["rateSource"], "claude_authenticated_usage")
            base["providers"][0] = updated
            after = governed_route_dry_run(
                base, "review", "small", repo="fixture", health_reader=health)
            self.assertEqual(after["status"], "READY_FOR_SEPARATE_AUTHORIZATION")
            self.assertEqual(after["recommended"], "Claude Code")
            claude_row = next(c for c in after["candidates"]
                              if c["provider"] == "Claude Code")
            self.assertEqual(claude_row["quotaGateReason"],
                             "QUOTA_WITHIN_FORECAST_AND_RESERVE")
            self.assertEqual(claude_row["missingQuotaWindows"], [])


if __name__ == "__main__":
    unittest.main()
