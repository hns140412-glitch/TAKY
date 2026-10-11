import unittest

from voice_asset_reuse_router import VoiceAssetRequest, route_voice_asset, semantic_asset_key


class VoiceAssetReuseRouterTest(unittest.TestCase):
    def req(self):
        key = semantic_asset_key(
            role="PLAY_CAMP_MAKER",
            locale="ko-KR",
            intent="STEP",
            meaning="모서리끼리 딱 만나게 해보자",
        )
        return VoiceAssetRequest(
            semantic_asset_key=key,
            role="PLAY_CAMP_MAKER",
            locale="ko-KR",
            text="모서리끼리 딱 만나게 해보자!",
            intent="STEP",
        )

    def test_locked_guides_to_reuse(self):
        r = self.req()
        d = route_voice_asset(r, [{
            "semantic_asset_key": r.semantic_asset_key,
            "asset_id": "maker_step_001",
            "status": "LOCKED",
        }])
        self.assertEqual(d.route, "REUSE_EXISTING")
        self.assertEqual(d.asset_id, "maker_step_001")

    def test_candidate_guides_to_review(self):
        r = self.req()
        d = route_voice_asset(r, [{
            "semantic_asset_key": r.semantic_asset_key,
            "asset_id": "maker_step_cand",
            "status": "CANDIDATE",
        }])
        self.assertEqual(d.route, "REVIEW_EXISTING_CANDIDATE")

    def test_rejected_guides_to_reasoned_regeneration(self):
        r = self.req()
        d = route_voice_asset(r, [{
            "semantic_asset_key": r.semantic_asset_key,
            "asset_id": "maker_step_bad",
            "status": "REJECTED",
        }])
        self.assertEqual(d.route, "REGENERATE_WITH_REASON")

    def test_missing_guides_to_bounded_create(self):
        d = route_voice_asset(self.req(), [])
        self.assertEqual(d.route, "CREATE_NEW")


if __name__ == "__main__":
    unittest.main()
