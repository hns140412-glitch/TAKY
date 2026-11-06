"""No-network local pilot checks. Does not modify CURRENT or external services."""
import copy
import unittest

from taky_sidebiz_pilot import DEMO, evaluate, scan_adpot_notices


class SideIncomePilotTests(unittest.TestCase):
    def test_demo_is_not_claimed_as_real_income(self):
        out = evaluate(copy.deepcopy(DEMO))
        self.assertEqual(out["status"], "DEMO_ONLY")
        self.assertEqual(out["estimated_approved_value_krw"], 20000)
        self.assertIsNone(out["net_cash_krw"])
        self.assertIs(out["verified_real_income"], False)

    def test_manual_pending_cash_still_unknown(self):
        data = {**DEMO, "mode": "MANUAL"}
        out = evaluate(data)
        self.assertEqual(out["status"], "CASH_NOT_REPORTED")
        self.assertIsNone(out["net_cash_krw"])

    def test_manual_cash_is_never_independently_verified(self):
        data = {**DEMO, "mode": "MANUAL", "cash_received_krw": 20000,
                "ad_spend_krw": 7000, "other_cost_krw": 2000,
                "refunds_krw": 1000, "owner_minutes": 120}
        out = evaluate(data)
        self.assertEqual(out["status"], "CASH_REPORTED_NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(out["known_total_cost_krw"], 10000)
        self.assertEqual(out["net_cash_krw"], 10000)
        self.assertEqual(out["hourly_cash_net_krw"], 5000)
        self.assertFalse(out["verified_real_income"])

    def test_no_approved_leads_means_no_expected_commission(self):
        data = {**DEMO, "approved": 0, "cash_received_krw": 0,
                "ad_spend_krw": 20000, "mode": "MANUAL"}
        out = evaluate(data)
        self.assertEqual(out["estimated_approved_value_krw"], 0)
        self.assertEqual(out["net_cash_krw"], -20000)

    def test_impossible_funnel_rejected(self):
        for changes in ({"approved": 4}, {"applications": 51}, {"clicks": 1001}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, "FUNNEL_COUNT_INCONSISTENT"):
                evaluate({**DEMO, **changes})

    def test_negative_bool_and_cash_overclaim_rejected(self):
        for changes in ({"ad_spend_krw": -1}, {"approved": True}, {"cash_received_krw": 20001}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                evaluate({**DEMO, **changes})

    def test_schema_and_work_id_guard(self):
        for changes in ({"work_id": "INT-001"}, {"schema": "UNTRUSTED"},
                        {"mode": "LIVE"}, {"lane": "UNKNOWN"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                evaluate({**DEMO, **changes})

    def test_micro_app_lane_with_zero_minutes_is_safe(self):
        out = evaluate({**DEMO, "lane": "MICRO_APP", "owner_minutes": 0,
                        "cash_received_krw": 20000, "mode": "MANUAL"})
        self.assertIsNone(out["hourly_cash_net_krw"])
        self.assertEqual(out["net_cash_krw"], 20000)



class AdpotPublicNoticeScanTests(unittest.TestCase):
    SOURCE = ("""
    <table>
    <tr><td>1601</td><td><a href="notice_view.html?code=5365&amp;">[캠페인종료] 하이미디어 모든 CPA 캠페인 종료 안내</a></td><td>2026-11-05</td></tr>
    <tr><td>1600</td><td><a href="notice_view.html?code=5360&amp;">코인원 앱설치 CPA 일 모집수량 변경 안내</a></td><td>2026-11-02</td></tr>
    <tr><td>1599</td><td><a href="notice_view.html?code=5356&amp;">코인원 앱설치 CPA 캠페인 일시중지 안내</a></td><td>2026-10-28</td></tr>
    <tr><td>1598</td><td><a href="notice_view.html?code=5353&amp;">코인원 앱설치 CPA 캠페인 단가 변경 안내</a></td><td>2026-10-26</td></tr>
    <tr><td>1595</td><td><a href="notice_view.html?code=5339&amp;">[신규등록] 코인원 CPA 캠페인 신규등록 안내</a></td><td>2026-10-21</td></tr>
    <tr><td>1588</td><td><a href="notice_view.html?code=5309&amp;">타이어렌탈 넥센타이어 캠페인 할인 혜택 변경 안내</a></td><td>2026-09-30</td></tr>
    <tr><td>1592</td><td><a href="notice_view.html?code=5327&amp;">법정의무교육 캠페인 주말 미운영 안내</a></td><td>2026-10-12</td></tr>
    </table>
    """).encode("utf-8")

    def test_public_notice_stop_and_pause_are_classified(self):
        out = scan_adpot_notices(self.SOURCE)
        risks = {r["notice_id"]: r["risk"] for r in out["notices"]}
        self.assertEqual(risks[1601], "STOP_NOTICE")
        self.assertEqual(risks[1599], "PAUSE_NOTICE")
        self.assertEqual(risks[1592], "PAUSE_NOTICE")
        self.assertEqual(risks[1595], "NEW_OFFER_UNVERIFIED")
        self.assertEqual(risks[1588], "TERMS_CHANGED_RECHECK")

    def test_all_campaigns_remain_unapproved_without_member_terms(self):
        out = scan_adpot_notices(self.SOURCE)
        self.assertIs(out["paid_ads_allowed"], False)
        self.assertEqual(out["member_campaign_status"],
                         "UNKNOWN_NEEDS_CURRENT_CAMPAIGN_TERMS")

    def test_campaign_filter_returns_all_relevant_history(self):
        out = scan_adpot_notices(self.SOURCE, term="코인원")
        self.assertEqual(out["notice_count"], 4)
        self.assertEqual([r["notice_id"] for r in out["notices"]],
                         [1600, 1599, 1598, 1595])
        self.assertEqual(out["notices"][0]["risk"], "TERMS_CHANGED_RECHECK")
        self.assertEqual(out["notices"][1]["risk"], "PAUSE_NOTICE")

    def test_public_notice_urls_are_normalized(self):
        out = scan_adpot_notices(self.SOURCE)
        self.assertTrue(all(r["public_url"].startswith(
            "https://adpot.kr/pc/center/notice_view.html?code=")
            for r in out["notices"]))
        self.assertTrue(out["source_sha256"])

    def test_bad_html_or_unknown_campaign_is_blocked(self):
        for raw, term in ((b"<html>error</html>", ""),
                          (self.SOURCE, "없는 캠페인"),
                          (b"", ""),
                          (self.SOURCE, "x" * 81)):
            with self.subTest(term=term), self.assertRaises(ValueError):
                scan_adpot_notices(raw, term)

    def test_large_or_nonbyte_sources_are_rejected(self):
        for raw in (b"x" * 600001, None, "not bytes"):
            with self.subTest(type=str(type(raw))), self.assertRaises(ValueError):
                scan_adpot_notices(raw)


if __name__ == "__main__":
    unittest.main()
