import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import voice_explorer_crew_production_preflight as P


class ExplorerCrewVoiceProductionPreflightTest(unittest.TestCase):
    def snapshot(self):
        main=[]
        play=[]
        for cid in P.ALL24:
            for intent in P.INTENTS:
                for v in range(2):
                    main.append({"id":cid,"intent":intent,"variant":v,"text":f"{cid}-{intent}-{v}-main"})
        for cid in P.CORE6:
            for intent in P.INTENTS:
                for v in range(2):
                    play.append({"id":cid,"intent":intent,"variant":v,"text":f"{cid}-{intent}-{v}-play"})
        return {
            "status":P.EXPECTED_MAIN,"play_status":P.EXPECTED_PLAY,
            "play_scope":"COMMON_NEUTRAL_BANK__SCRIPT_LOCKED__RUNTIME_ENABLED",
            "locked":["PLAY_CAMP","MAIN_CREW"],"main":main,"play":play,
            "signatures":{cid:f"sig-{cid}" for cid in P.ALL24},
        }

    def test_locked_scope_routes_and_holds_without_voice_config(self):
        with tempfile.TemporaryDirectory() as td:
            registry=Path(td)/"registry.json"
            registry.write_text('{"assets":[]}',encoding="utf-8")
            out=Path(td)/"out.json"
            with patch.object(P,"REGISTRY",registry), patch.object(P,"OUTPUT",out), patch.object(P,"_node_snapshot",return_value=self.snapshot()), patch.object(P,"_verify_source_lock",return_value={"version":P.EXPECTED_LOCK,"count":35,"bad":[]}):
                r=P.build(Path(td),None)
            self.assertEqual(r["production_lines"]["total_clips"],180)
            self.assertEqual(r["route_summary"],{"CREATE_NEW":180})
            self.assertEqual(r["exact_text_duplicate_count"],0)
            self.assertFalse(r["voice_configuration_ready"])
            self.assertFalse(r["generation_authorized"])
            self.assertEqual(r["status"],"HOLD_PREPRODUCTION_CONFIGURATION")
            self.assertTrue(out.exists())

    def test_source_lock_failure_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            registry=Path(td)/"registry.json"
            registry.write_text('{"assets":[]}',encoding="utf-8")
            with patch.object(P,"REGISTRY",registry), patch.object(P,"_node_snapshot",return_value=self.snapshot()), patch.object(P,"_verify_source_lock",return_value={"version":P.EXPECTED_LOCK,"count":35,"bad":[{"file":"x"}]}):
                with self.assertRaises(RuntimeError):
                    P.build(Path(td),None)


if __name__ == "__main__":
    unittest.main()
